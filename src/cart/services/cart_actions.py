from django.core.exceptions import ValidationError

from cart.models import Cart
from products.models import SellerProduct


def merge_cart_products(user, cart_list_session):
    # TODO: добавить докстринг для чего этот сервис
    if cart_list_session is None:
        return
    for product_session in cart_list_session:
        product, created = Cart.objects.get_or_create(
            profile=user,
            product_seller__pk=product_session['product_seller'],
            defaults={
                'product_seller': SellerProduct.objects.get(pk=product_session['product_seller']),
                'count': product_session['count'],
                'profile': user,
            }
        )
        if not created:
            try:
                product.clean(product.count + product_session['count'])
                product.count += product_session['count']
                product.save()
            except ValidationError:
                product.count = product.product_seller.count
                product.save()


def clear_cart(profile):
    Cart.objects.filter(profile=profile).delete()


def check_product_amt(cart):
    # TODO: добавить докстринг для чего этот сервис
    cart.filter(product_seller__count=0).delete()
    new_counts = map(
        lambda product:
        product.product_seller.count if product.count > product.product_seller.count else product.count,
        cart
    )
    for product, new_count in zip(cart, new_counts):
        product.count = new_count
    Cart.objects.bulk_update(cart, ["count"])
