from typing import Any, Dict

from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.utils import timezone

from .forms import ProductsImportForm
from .models import Product
from .services.catalog_queryset import CatalogQuerySetProcessor
from .services.compare_products import (
    add_product_to_compare_list,
    delete_all_compare_products,
    delete_product_to_compare_list,
    get_compare_list_amt,
    get_compare_list,
)
from .services.banners import Banner, LimitedProduct, TopSellerProduct, clear_banner_cache
from .tasks import import_products
from account.models import BrowsingHistory
from catalog.forms import ReviewForm
from catalog.services import add_review, get_count_review
from .context_processors import clear_category_cache


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
    """
    View детальной страницы товара
    """
    model = Product
    template_name = "products/product-details.jinja2"
    context_object_name = "product"

    def get_queryset(self) -> QuerySet:
        """
        Метод для получения queryset товара.
        Если данные не найдены в кэше, они извлекаются из базы данных и кэшируются на 24 часа.
        """
        slug = self.kwargs.get('slug')
        cache_key = f'product_details_{slug}'
        queryset = cache.get(cache_key)

        if queryset is None:
            queryset = Product.objects.prefetch_related(
                'images',
                'sellerproduct__seller',
                'product_property_value__property'
            )
            cache.set(cache_key, queryset, 60 * 60 * 24)

        return queryset

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Метод для получения контекстных данных, передаваемых в шаблон.
        Включает изображения товара, связанные товары от продавца, свойства товара, отзывы и количество отзывов.
        """
        context_data = super().get_context_data(**kwargs)

        context_data['images'] = self.object.images.all()
        context_data['seller_products'] = self.object.sellerproduct.all()
        context_data['properties'] = self.object.product_property_value.all()
        context_data['reviews'] = self.object.reviews.all()
        context_data['get_count_review'] = get_count_review(self.object.pk)

        return context_data

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        Метод обработки GET-запроса.
        Если пользователь аутентифицирован, создается запись о просмотре товара в истории просмотров.
        """
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

    def post(self, request, *args, **kwargs) -> HttpResponseRedirect:
        form = ReviewForm(request.POST)

        if form.is_valid():
            add_review(text=request.POST['text'], user_id=request.user.id, slug=kwargs['slug'])

            return redirect('products:product_details', slug=kwargs['slug'])

        return HttpResponseRedirect(
            reverse('products:product_details',
                    kwargs={'slug': kwargs.get('slug')}
                    )
        )


class ProductsCompareView(ListView):
    template_name = 'products/compare/compare.jinja2'

    def get_queryset(self) -> list[Product]:
        '''Фомирует кверисет для страницы сравнения'''
        return [
            product[0] for product in [
                Product.objects.filter(slug=slug).select_related('category').prefetch_related("images")
                for slug in get_compare_list(self.request)
            ]
        ]

    def get_context_data(self, *, object_list=None, **kwargs) -> dict[Any]:
        '''Фомирует контекст для страницы сравнения'''
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
        context['not_dif_category'] = [
            key for key, value in diff_properties.items()
            if len(set(map(lambda elem: elem.lower(), value))) == 1
            and
            len(context['properties']) > 1
            and
            len(list(map(lambda elem: elem.lower(), value))) != 1
        ]

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


def delete_all_compare_products_view(request: HttpRequest) -> HttpResponse:
    '''функция ajax запроса для удаления всех товаров из сравнения'''
    if request.method == 'DELETE':
        delete_all_compare_products(request)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def delete_product_to_compare_list_view(request: HttpRequest, slug: str) -> HttpResponse:
    '''функция ajax запроса для удаления одного товара из сравнения'''
    if request.method == 'DELETE':
        delete_product_to_compare_list(request, slug)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def add_product_to_compare_list_view(request: HttpRequest, slug: str) -> HttpResponse:
    '''функция ajax запроса для добавления одного товара в сравнение'''
    if request.method == 'POST':
        add_product_to_compare_list(request, slug)
        return HttpResponse()
    return HttpResponse('Нет доступа')


def get_compare_list_amt_view(request: HttpRequest) -> HttpResponse:
    '''функция ajax запроса для получения количества товаров в сравнении'''
    if request.method == 'GET':
        return HttpResponse(get_compare_list_amt(request))
    return HttpResponse('Нет доступа')


class ProductImportFormView(PermissionRequiredMixin, FormView):
    """ View страницы импорта товаров. """
    template_name = 'admin/product_import_form.html'
    form_class = ProductsImportForm
    success_url = '..'
    permission_required = [
        "products.add_product",
        "products.add_seller_product",
    ]

    def form_valid(self, form):
        task = import_products.delay(
            form.files['zip_file'].read(),
            self.request.user.pk,
            form.cleaned_data['email'],
        )

        self.request.session['import_task'] = task.id
        messages.add_message(
            self.request,
            messages.INFO,
            "Import task added to queue")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = self.request.session.get('import_task')
        if task_id:
            task = AsyncResult(task_id)
            if task.successful() or task.failed():
                del self.request.session['import_task']
            else:
                context['status'] = task.status
        return context


def reset_banners_cache(request) -> HttpResponse:
    """
    AJAX функция для сброса кэша при смене языка
    """
    if request.method == 'POST':
        clear_banner_cache()
        clear_category_cache()
        return HttpResponse()
    return HttpResponse('Нет доступа')
