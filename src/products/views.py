from typing import Any, Dict

from django.contrib import messages
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.db.models import QuerySet
from django.core.cache import cache
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, ListView
from django.utils import timezone

from catalog.forms import ReviewForm
from catalog.services import get_reviews_list, add_review, get_count_review

from .models import Picture, Product, SellerProduct
from .services.catalog_queryset import CatalogQuerySetProcessor
from .services.compare_products import (
    add_product_to_compare_list,
    delete_all_compare_products,
    delete_product_to_compare_list,
    get_compare_list_amt,
    get_compare_list,
)
from .utils import Banner, LimitedProduct, TopSellerProduct
from account.models import BrowsingHistory
from catalog.forms import ReviewForm
from catalog.models import Review
from catalog.services import get_reviews_list, add_review, get_count_review


class IndexView(TemplateView):
    """ View главной страницы сайта. """
    template_name = 'index.jinja2'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """ Получение контекстных данных для ответа. """
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner()
        context['top_sellers'] = TopSellerProduct.get_top_sellers()
        context['limited_offers'] = LimitedProduct.get_limited_offers()

        return context


class CatalogView(ListView):
    """ View каталога товаров. """
    template_name = 'catalog/catalog.jinja2'
    model = Product
    context_object_name = 'products'

    def __init__(self):
        super().__init__()
        self.queryset_processor = CatalogQuerySetProcessor()

    def get_queryset(self) -> QuerySet:
        """ Получение queryset списка товаров для отображения. """

        products_list = self.queryset_processor.get_queryset(self.request)

        paginator = Paginator(products_list, 8)
        page_number = self.request.GET.get('p', 1)

        try:
            products = paginator.page(page_number)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        return products

    def get_context_data(self, *, object_list=None, **kwargs) -> Dict[str, Any]:
        """ Получение контекстных данных для ответа. """
        context = super().get_context_data(**kwargs)
        context = self.queryset_processor.get_context_data(
            context,
            self.request,
        )

        return context

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """ Оброаботка метода GET. """

        self.queryset_processor.process_get_params(request, **kwargs)

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """ Оброаботка метода POST. """

        self.queryset_processor.process_post_params(request, **kwargs)

        return self.get(request, args, kwargs)


class ProductDetailsView(DetailView):
    template_name = "products/product-details.jinja2"
    queryset = Product.objects.prefetch_related("images")
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.user.is_authenticated:
            browsing_history, created = BrowsingHistory.objects.get_or_create(
                profile=request.user, product=self.object
            )

            if not created:
                browsing_history.timestamp = timezone.now()
                browsing_history.save()

        context_data = self.get_context_data()

        return self.render_to_response(context_data)

    def get_context_data(self, **kwargs):
        """
        Получение контекстных данных для представления деталей продукта.
        """
        cache_key = f'product_details_{self.object.pk}'
        context_data = cache.get(cache_key)

        if context_data is None:
            product = self.object
            sellers = SellerProduct.objects.filter(
                product=product,
            ).select_related('seller')
            images = Picture.objects.filter(product=product)
            reviews = Review.objects.filter(
                product=product,
            ).order_by('-created_at')

            context_data = {
                'product': product,
                'sellers': sellers,
                'images': images,
                'reviews': reviews,
                'reviews_list': get_reviews_list(product.pk),
                'get_count_review': get_count_review(product.pk)
            }

            cache.set(cache_key, context_data, 60 * 60 * 24)

        return context_data

    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST)

        if form.is_valid():
            add_review(post=request.POST, user_id=request.user.id, pk=kwargs['pk'])

            return redirect('products:product_details', pk=kwargs['pk'])

        return HttpResponseRedirect(
            reverse('products:product_details',
                    kwargs={'pk': kwargs.get('pk')}
                    )
        )


class ProductsCompareView(ListView):
    template_name = 'products/compare/compare.jinja2'

    def get_queryset(self):
        return [
            product[0] for product in [
                Product.objects.filter(slug=slug).select_related('category').prefetch_related("images")
                for slug in get_compare_list(self.request)
            ]
        ]

    def get_context_data(self, *, object_list=None, **kwargs):
        # messages.success(self.request, 'Profile details updated.')
        context = super().get_context_data()

        if not context['object_list']:
            return context

        context['properties'] = [
            {
                'pk': product.pk,
                'product': product,
                'price': product.min_price,
                'img': product.images.first().image.url,
                'slug': product.slug,
                'property': [
                    {
                        'property_name': value.property,
                        'property_value': value.value,
                    }
                    for value in product.product_property_value.select_related('property')
                ]
            }
            for product in context['object_list']
        ]

        diff_properties = dict()
        for product in context['properties']:
            for product_property in product['property']:
                if diff_properties.get(product_property['property_name']):
                    diff_properties[product_property['property_name']].append(product_property['property_value'])
                else:
                    diff_properties[product_property['property_name']] = [product_property['property_value']]
        for key, value in diff_properties.items():
            print(len(set(map(lambda elem: elem.lower(), value))) == 1, len(context['properties']) > 1)
        context['not_dif_category'] = [
            key for key, value in diff_properties.items()
            if len(set(map(lambda elem: elem.lower(), value))) == 1
            and
            len(context['properties']) > 1
        ]
        print(context['not_dif_category'])

        for product in context['properties']:
            product['dif_properties'] = [
                {
                    'property_name': properties['property_name'],
                    'property_value': properties['property_value'],
                }
                for properties in product['property']
                if properties['property_name'] not in context['not_dif_category']
            ]

        for product in context['properties']:
            if (len(product['dif_properties']) == len(product['property']) or len(product['dif_properties']) == 0) \
                    and \
                    len(context['properties']) != 1:
                product['diff_category'] = True
                context['diff_category'] = True
            else:
                product['diff_category'] = False

        return context


def delete_all_compare_products_view(request):
    '''функция ajax запроса для доступа к сервису сравнения'''
    if request.method == 'DELETE':
        delete_all_compare_products(request)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def delete_product_to_compare_list_view(request, slug):
    '''функция ajax запроса для доступа к сервису сравнения'''
    if request.method == 'DELETE':
        delete_product_to_compare_list(request, slug)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def add_product_to_compare_list_view(request, slug):
    if request.method == 'POST':
        add_product_to_compare_list(request, slug)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def get_compare_list_amt_view(request):
    if request.method == 'GET':
        return HttpResponse(get_compare_list_amt(request))
    return HttpResponse('Нет доступа')
