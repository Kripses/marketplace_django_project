from django.shortcuts import render
from django.http.response import HttpResponse, JsonResponse
from django.views.generic import ListView

from cart.services.cart_actions import (
    add_product_to_cart,
    get_cart_product_amt,
    get_cart_product_list,
    get_total_price,
    remove_product_from_cart,
    get_total_price,
    change_cart_product_amt,
)

from cart.models import Cart


class CartView(ListView):
    model = Cart
    template_name = 'cart/cart.jinja2'

    def get_queryset(self):
        print(get_cart_product_list(self.request.user))
        return get_cart_product_list(self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()

        context['cart'] = [
            {
                'seller': cart_product.product_seller.pk,
                'slug': cart_product.product_name,
                'pict': cart_product.product_seller.product.images.first().image.url,
                'name': cart_product.product_seller.product.name,
                'price': cart_product.product_seller.price,
                'count': cart_product.count,
                'desc': cart_product.product_seller.product.description
            }
            for cart_product in context['object_list']
        ]

        context['total_price'] = get_total_price(self.request.user)
        return context


def add_product_to_cart_view(request, slug, pk):
    add_product_to_cart(request.user, slug, pk)
    return HttpResponse()


def cart_amt_view(request):
    return JsonResponse({'amt': get_cart_product_amt(request.user)})


def remove_product_from_cart_view(request, slug, pk):
    remove_product_from_cart(request.user, slug, pk)
    return HttpResponse(200)


def get_total_price_view(request):
    return JsonResponse({'price': get_total_price(request.user)})


def change_cart_product_amt_view(request, slug, change, pk):
    if change == 2:
        change = -1
    change_cart_product_amt(request.user, slug, change, pk)
    return HttpResponse()
