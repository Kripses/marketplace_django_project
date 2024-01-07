from enum import Enum
from typing import Any, Dict

from django.contrib import messages
from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from django.db.models import Count, Max, Min, Sum, QuerySet
from django.core.cache import cache
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, ListView
from django.utils import timezone

from .forms import FilterForm, SearchForm
from .models import Category, Picture, Product, SellerProduct, Tag, Value
from .services.compare_products import (
    add_product_to_compare_list,
    get_compare_list,
    delete_all_compare_products,
    delete_product_to_compare_list,
    get_compare_list,
)
from .utils import Banner, LimitedProduct, TopSellerProduct
from account.models import BrowsingHistory
from catalog.forms import ReviewForm
from catalog.models import Review
from catalog.services import get_reviews_list, add_review, get_count_review
from discounts.models import CategoryDiscount, ComboDiscount, ComboSet, ProductDiscount


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

    QS_KEY = 'catalog_queryset'
    FP_KEY = 'catalog_filter_price'

    def __init__(self):
        super().__init__()
        self.tag = None
        self.categories = None
        self.filter_params = {}
        self.filter_prices = {}
        self.filter_name = None
        self.filter_in_stock = None
        self.search_query = None

    class SortEnum(Enum):
        """ Перечисление параметров сортировки товаров. """
        POP_ASC = '-pop'
        POP_DEC = 'pop'
        PRI_ASC = '-pri'
        PRI_DEC = 'pri'
        REV_ASC = '-rev'
        REV_DEC = 'rev'
        CRE_ASC = '-cre'
        CRE_DEC = 'cre'
        NONE = 'none'

    def get_queryset(self) -> QuerySet:
        """ Получение queryset списка товаров для отображения. """
        products_list = self._get_base_queryset()
        products_list = self._get_filtered_queryset(products_list)
        sort = self._get_selected_sort_type()
        products_list = self._get_sorted_queryset(products_list, sort)

        paginator = Paginator(products_list, 8)
        page_number = self.request.GET.get('p', 1)
        try:
            products = paginator.page(page_number)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        return products

    def _get_base_queryset(self) -> QuerySet:
        """ Получение базового queryset для дальнейшей работы. """
        search_query = self.request.session.get('search_query')
        base_filter = {'seller_count__gt': 0}
        if self.tag or self.categories or search_query:

            if self.tag:
                base_filter['tags'] = self.tag
            if self.categories:
                base_filter['category__in'] = self.categories
            if search_query:
                base_filter['name__icontains'] = search_query

        products_list = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).filter(**base_filter)

        prices = products_list.aggregate(
            min=Min('sellerproduct__price'),
            max=Max('sellerproduct__price'),
        )
        min_pr = prices['min']
        if not min_pr:
            min_pr = 0
        max_pr = prices['max']
        if not max_pr:
            max_pr = 0

        self.filter_prices['min'] = str(min_pr)
        self.filter_prices['max'] = str(max_pr)
        if not self.filter_prices.get('selected_min'):
            self.filter_prices['selected_min'] = str(min_pr)
        if not self.filter_prices.get('selected_max'):
            self.filter_prices['selected_max'] = str(max_pr)
        return products_list

    def _get_filtered_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Получение отфильтрованного queryset.

        Args:
            - queryset: queryset, подлежащий фильтрованию.
        """
        if self.filter_params:
            if 'amount__gt' or 'price__lte' in self.filter_params:
                queryset = queryset.annotate(
                    amount=Sum('sellerproduct__count'),
                    price=Min('sellerproduct__price'),
                ).filter(**self.filter_params)
            else:
                queryset = queryset.filter(**self.filter_params)
        return queryset

    def _get_selected_sort_type(self) -> str:
        """ Получение выбранного типа сортировки из запроса. """
        sort = self.request.GET.get('sort')
        if sort:
            if (sort == self.SortEnum.NONE.value and
                    self.request.session.get('sort')):
                del self.request.session['sort']
            else:
                self.request.session['sort'] = sort
        sort = self.request.session.get('sort')
        if not sort:
            sort = self.SortEnum.NONE.value
        return sort

    def _get_sorted_queryset(self, queryset: QuerySet, sort: str) -> QuerySet:
        """
        Получение отсортированного queryset.

        Args:
            - queryset: queryset, подлежащего сортировке.
            - sort: тип сортировки.
        """
        if sort == self.SortEnum.CRE_ASC.value:
            return queryset.order_by('created_at').all()
        if sort == self.SortEnum.CRE_DEC.value:
            return queryset.order_by('-created_at').all()
        if sort == self.SortEnum.POP_ASC.value:
            return queryset.order_by('-count_sells').all()
        if sort == self.SortEnum.POP_DEC.value:
            return queryset.order_by('count_sells').all()
        if sort == self.SortEnum.PRI_ASC.value:
            return queryset.annotate(
                price=Min('sellerproduct__price')
            ).order_by('-price').all()
        if sort == self.SortEnum.PRI_DEC.value:
            return queryset.annotate(
                price=Min('sellerproduct__price')
            ).order_by('price').all()
        if sort == self.SortEnum.REV_ASC.value:
            return queryset.annotate(
                rev_count=Count('reviews')
            ).order_by('-rev_count').all()
        if sort == self.SortEnum.REV_DEC.value:
            return queryset.annotate(
                rev_count=Count('reviews')
            ).order_by('rev_count').all()

        return queryset.order_by('sort_index').all()

    def get_context_data(self, *, object_list=None, **kwargs) -> Dict[str, Any]:
        """ Получение контекстных данных для ответа. """
        context = super().get_context_data(**kwargs)
        context['sort'] = self.SortEnum
        curr_sort = self.request.session.get('sort')
        if curr_sort:
            context['curr_sort'] = curr_sort
        context['tags'] = Tag.objects.annotate(
            prod_count=Count('products')
        ).order_by('-prod_count').all()[:10]

        widget_attrs = FilterForm.declared_fields['price'].widget.attrs
        widget_attrs['data-min'] = self.filter_prices['min']
        widget_attrs['data-max'] = self.filter_prices['max']
        widget_attrs['data-from'] = self.filter_prices['selected_min']
        widget_attrs['data-to'] = self.filter_prices['selected_max']

        FilterForm.declared_fields['title'].widget.attrs['value'] = (
            self.filter_name
        ) if self.filter_name else ''
        FilterForm.declared_fields['in_stock'].widget.attrs['checked'] = (
            True
        ) if self.filter_in_stock else False

        context['filter_form'] = FilterForm()

        return context

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """ Оброаботка метода GET. """
        self._process_path_params(**kwargs)
        if self.search_query:
            request.session['search_query'] = self.search_query
        elif (
            request.session.get('search_query')
            and not request.GET.get('p')
            and not self.filter_params
        ):
            del request.session['search_query']

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """ Оброаботка метода POST. """
        self._process_path_params(**kwargs)
        filter_form = FilterForm(request.POST)
        search_form = SearchForm(request.POST)
        if filter_form.is_valid():
            cd = filter_form.cleaned_data
            if cd['price']:
                price = cd['price'].split(';')
                self.filter_params['price__gte'] = price[0]
                self.filter_params['price__lte'] = price[1]
                self.filter_prices['selected_min'] = price[0]
                self.filter_prices['selected_max'] = price[1]
            if cd['title']:
                self.filter_params['name__icontains'] = cd['title']
                self.filter_name = cd['title']
            if cd['in_stock']:
                self.filter_params['amount__gt'] = 0
                self.filter_in_stock = True

        if search_form.is_valid():
            self.search_query = search_form.cleaned_data['query']

        return self.get(request, args, kwargs)

    def _process_path_params(self, **kwargs):
        """ Обработка параметров из пути запроса. """
        tag_slug = kwargs.get('tag')
        if tag_slug:
            tag = Tag.objects.filter(slug=tag_slug).first()
            if tag:
                self.tag = tag.pk

        category_slug = kwargs.get('category')
        if category_slug:
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                categories = [category.pk]
                categories.extend(
                    [cat.pk for cat in category.subcategories.all()]
                )
                self.categories = categories


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
            properties_and_values = Value.objects.filter(
                product=product
            ).select_related('property')

            context_data = {
                'product': product,
                'sellers': sellers,
                'images': images,
                'reviews': reviews,
                'properties_and_values': properties_and_values,
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

        add_product_to_compare_list(request)
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
        messages.success(self.request, 'Profile details updated.')
        context = super().get_context_data()

        if not context['object_list']:
            return context

        for product in context.get('object_list'):
            context['properties'] = [
                {
                    'property_name': value.property
                }
                for value in product.product_property_value.select_related('property')
            ]

        for property_name in context['properties']:
            property_name['property_values'] = [
                property_name['property_name'].category_property_value.filter(product=product)
                for product in context.get('object_list')
            ]

        diff_properties = dict()
        for product in context['properties']:
            for product_property in product['product_properties']:
                if diff_properties.get(product_property['property_name']):
                    diff_properties[product_property['property_name']].append(product_property['property_value'])
                else:
                    diff_properties[product_property['property_name']] = [product_property['property_value']]

        context['not_dif_category'] = [
            key for key, value in diff_properties.items() if len(set(value)) == 1 and len(context['properties']) > 1
        ]

        for product in context['properties']:
            product['dif_properties'] = [
                {
                    'property_name': properties['property_name'],
                    'property_value': properties['property_value'],
                }
                for properties in product['product_properties']
                if properties['property_name'] not in context['not_dif_category']
            ]

        for product in context['properties']:
            if len(product['dif_properties']) == len(product['product_properties']) and len(context['properties']) != 1:
                context['diff_category'] = True
            else:
                context['diff_category'] = False
        return context


def delete_all_compare_products_view(request):
    '''функция ajax запроса для доступа к сервису сравнения'''
    delete_all_compare_products(request)
    return HttpResponse()


def delete_product_to_compare_list_view(request, pk):
    '''функция ajax запроса для доступа к сервису сравнения'''
    delete_product_to_compare_list(request, pk)
    return HttpResponse()