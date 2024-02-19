import os
from yookassa import Configuration, Payment
import uuid

from django.urls import reverse

from cart.services.cart_actions import clear_cart
from cart.models import Order
from products.models import SellerProduct


Configuration.account_id = os.getenv("SHOP_ID", "")
Configuration.secret_key = os.getenv("SECRET_KEY", "")


def get_paid(order):
    return_url = reverse('cart:order_detail', args=(order.pk,))
    payment = Payment.create({
        "amount": {
            "value": str(order.total_price),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f'https://45.153.69.124{return_url}'
        },
        "capture": True,
        "test": True,
    }, uuid.uuid4())
    order.payment_id = payment.id
    order.save()
    return payment.confirmation.confirmation_url


def change_seller_product_count(cart):
    for product_seller, count in map(
            lambda prod: (
                    prod['seller'],
                    prod['count'],
            ),
            cart.values()):
        seller = SellerProduct.objects.get(pk=product_seller)
        seller.count -= count
        seller.save()

        seller.product.count_sells += count
        seller.product.save()


def get_payment_status(order):
    change_seller_product_count(order.cart)
    if order == Order.objects.filter(profile=order.profile, archived=False).last():
        clear_cart(order.profile)
    order.status = True
    order.save()
