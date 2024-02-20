from typing import Any

from django.db.models import F, QuerySet, Model
from django.views.generic import ListView, DetailView
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from adminsettings.models import SiteSettings
from cart.serializer import CartSerializer, ProductSellerSerializer, CartPostSerializer
from products.models import SellerProduct
from cart.forms import CreateOrderForm
from cart.models import Order, Cart
from cart.services.cart_actions import check_product_amt
from cart.services.order_create import get_total_price, get_fio, get_carts_JSON
from payments.services.payment_service import get_paid


class OrderListView(LoginRequiredMixin, ListView):
    template_name = "cart/order-list.jinja2"
    context_object_name = "orders"

    def get_queryset(self):
        queryset = Order.objects.filter(archived=False, profile=self.request.user.id).order_by('-created_at')
        return queryset


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Класс для просмотра деталей заказа.
    """
    template_name = "cart/order-details.jinja2"
    context_object_name = "order"

    def get_queryset(self):
        queryset = Order.objects.filter(archived=False, profile=self.request.user.id)
        return queryset

    def post(self, request, pk):
        paid_url = get_paid(Order.objects.get(pk=pk))
        return redirect(paid_url)


class CreateOrderView(LoginRequiredMixin, View):
    """
    View-класс для создания заказов.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if user.is_authenticated:
            fio = get_fio(user.last_name, user.first_name, user.username)
            carts = (get_carts_JSON(Cart.objects.filter(profile=user.id)))
            total_price, delivery_price = get_total_price(carts)
            context = {
                'form': CreateOrderForm(initial={"cart": carts, "profile": user.id}),
                'user_fio': fio,
                'user_phone': user.phone,
                'user_email': user.email,
                'total_price': total_price,
                'delivery_price': delivery_price,
                'express': SiteSettings.objects.first().express_delivery_cost,
            }

        else:
            context = {}

        return render(request, 'cart/create_order.jinja2', context=context)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:

        form = CreateOrderForm(request.POST)
        if form.is_valid():
            form.save()
            Cart.objects.filter(profile=request.user.id).delete()
            # if form.cleaned_data['payment_type'] == "Online from a random someone else's account":
            #
            #     return HttpResponse("обработка запроса")
            paid_url = get_paid(Order.objects.filter(profile=request.user.pk).last())
            return redirect(paid_url)
        return self.get(request)


class CartView(ListView):
    '''оотбражение корзины'''
    model = Cart
    template_name = 'cart/cart.jinja2'

    def get_queryset(self) -> QuerySet | list:
        '''получение кверисета корзины'''
        if not self.request.user.is_authenticated:
            cart_list: dict = self.request.session.get('cart')
            if cart_list is None:
                return []
            return [[SellerProduct.objects.get(pk=obj['product_seller']), obj['count']] for obj in cart_list]

        cart = Cart.objects.filter(profile=self.request.user)
        check_product_amt(cart)
        return cart

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        '''формирование контекста корзины'''
        context = super().get_context_data()

        if not self.request.user.is_authenticated:
            context['cart'] = [
                {
                    'product_obj': product_seller[0].product,
                    'pk': product_seller[0].pk,
                    'seller': product_seller[0].pk,
                    'pict': product_seller[0].product.images.first().image.url,
                    'name': product_seller[0].product.name,
                    'price': product_seller[0].price,
                    'count': product_seller[1],
                    'desc': product_seller[0].product.description_short(),
                    'max_product_amt': product_seller[0].count,
                }
                for product_seller in context['object_list']
            ]
        else:
            context['cart'] = [
                {
                    'product_obj': cart_product.product_seller.product,
                    'pk': cart_product.pk,
                    'seller': cart_product.product_seller.pk,
                    'pict': cart_product.product_seller.product.images.first().image.url,
                    'name': cart_product.product_seller.product.name,
                    'price': cart_product.product_seller.price,
                    'count': cart_product.count,
                    'desc': cart_product.product_seller.product.description_short(),
                    'max_product_amt': cart_product.product_seller.count,
                }
                for cart_product in context['object_list']
            ]

        context['total_price'] = sum(map(lambda product: product['price'] * product['count'], context['cart']))
        return context


class CartApiViewSet(ModelViewSet):
    '''api для работы с корзиной'''
    def get_serializer_class(self) -> Any:
        '''выбор класса сериализации'''
        if not self.request.user.is_authenticated:
            return ProductSellerSerializer

        if self.request.method == 'POST' or self.request.method == 'PUT':
            return CartPostSerializer
        return CartSerializer

    def get_queryset(self) -> QuerySet | list:
        '''формирование кверисета корзины в api'''
        if not self.request.user.is_authenticated:
            cart_list = self.request.session.get('cart')
            if cart_list is None:
                return []
            return [SellerProduct.objects.get(pk=obj['product_seller']) for obj in cart_list]

        return Cart.objects.filter(profile=self.request.user)

    def get_object(self) -> Cart | SellerProduct:
        '''получение объекта корзины'''
        if not self.request.user.is_authenticated:
            return SellerProduct.objects.get(pk=self.kwargs['pk'])

        return Cart.objects.filter(profile=self.request.user).get(pk=self.kwargs['pk'])

    def list(self, request: HttpRequest, *args, **kwargs) -> Response:
        '''получение списка корзины'''
        if not request.user.is_authenticated:
            cart_list = request.session.get('cart')
            if cart_list is None:
                return Response({'length': 0})
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            for item, cart_product in zip(serializer.data, cart_list):
                item['cart_count'] = cart_product['count']
            return Response(serializer.data)

        return super().list(request)

    def destroy(self, request: HttpRequest, *args, **kwargs) -> Response:
        '''удаление товара из корзины'''
        if not request.user.is_authenticated:
            cart_list = request.session.get('cart')
            for product in cart_list:
                if int(kwargs['pk']) == product['product_seller']:
                    cart_list.remove(product)
                    request.session['cart'] = cart_list
                    return Response(200)
            return Response(400)

        return super().destroy(request)

    def create(self, request: HttpRequest, *args, **kwargs) -> Response:
        '''добавление товара в корзину'''
        if not request.user.is_authenticated:
            cart_list = request.session.get('cart')
            if cart_list is None:
                request.session['cart'] = [request.data]
                return Response(200)
            for product in cart_list:
                if request.data['product_seller'] == product['product_seller']:
                    try:
                        if product['count'] + 1 > SellerProduct.objects.get(pk=request.data['product_seller']).count:
                            raise ValidationError("Can't be more than total")
                        product['count'] += 1
                        request.session['cart'] = cart_list
                    except ValidationError:
                        return Response(400)
                    return Response(200)
            cart_list.append(request.data)
            request.session['cart'] = cart_list
            return Response(200)

        cart_product = Cart.objects.filter(
            profile=request.user,
            product_seller=request.data['product_seller']
        )
        if cart_product:
            try:
                cart_product[0].clean()
                cart_product.update(count=F('count') + 1)
            except ValidationError("Can't be more than total"):
                pass
            return Response(request.data)
        request.data['profile'] = request.user.pk
        return super().create(request)

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> Response:
        '''изменение кол-ва товара корзины'''
        if not request.user.is_authenticated:
            cart_list = request.session.get('cart')
            for product in cart_list:
                if int(kwargs['pk']) == product['product_seller']:
                    try:
                        if request.data['count'] > self.get_object().count:
                            raise ValidationError("Can't be more than total")
                        product['count'] = request.data['count']
                        request.session['cart'] = cart_list
                    except ValidationError:
                        pass
                    return Response({'price': self.get_object().price, 'count': product['count']})

        try:
            self.get_object().clean(request.data['count'])
            return super().partial_update(request)
        except ValidationError:
            return Response(
                {'product_seller':
                    {
                        'price': self.get_object().product_seller.price
                    },
                 'count': request.data['count'] - 1
                 }
            )


class SellerApiViewSet(ModelViewSet):
    '''api для работы с корзиной при неавторизированном пользователе'''
    queryset = SellerProduct.objects.filter(count__gt=0).order_by('price')
    serializer_class = ProductSellerSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['product', 'seller']
