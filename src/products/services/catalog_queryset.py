from enum import Enum
from typing import Any, Dict

from django.db.models import QuerySet, Count, Min, Max, Sum, BooleanField, ExpressionWrapper, Q
from django.http import HttpRequest

from ..forms import FilterForm, SearchForm
from ..models import Product, Tag, Category
from discounts.models import CategoryDiscount, ComboDiscount, ProductDiscount


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


class CatalogQuerySetProcessor:
    def __init__(self):
        self.tag = None
        self.categories = None
        self.products = None
        self.filter_params = {}
        self.filter_prices = {}
        self.filter_name = ''
        self.filter_in_stock = None
        self.search_query = None
        self.after_post = None

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        products_list = self.__get_base_queryset(request)
        products_list = self.__get_filtered_queryset(products_list)
        sort = self.__get_selected_sort_type(request)
        products_list = self.__get_sorted_queryset(products_list, sort)

        return products_list

    def __get_base_queryset(self, request) -> QuerySet:
        """ Получение базового queryset для дальнейшей работы. """
        search_query = request.session.get('search_query')

        base_filter = {}
        if self.tag or self.categories or self.products or search_query:
            if self.tag:
                base_filter['tags'] = self.tag
            if self.categories:
                base_filter['category__in'] = self.categories
            if self.products:
                base_filter['pk__in'] = self.products
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
        selected_min_pr = self.filter_prices.get('selected_min')

        if not selected_min_pr:
            self.filter_prices['selected_min'] = str(min_pr)
        elif selected_min_pr == str(round(min_pr, 2)) and self.filter_params.get('price__gte'):
            del self.filter_params['price__gte']
        selected_max_pr = self.filter_prices.get('selected_max')
        if not selected_max_pr:
            self.filter_prices['selected_max'] = str(max_pr)
        elif selected_max_pr == str(round(max_pr, 2)) and self.filter_params.get('price__lte'):
            del self.filter_params['price__lte']

        return products_list

    def __get_filtered_queryset(self, queryset: QuerySet) -> QuerySet:
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

    @staticmethod
    def __get_selected_sort_type(request: HttpRequest) -> str:
        """ Получение выбранного типа сортировки из запроса. """
        sort = request.GET.get('sort')
        if sort:
            if ((sort == SortEnum.NONE.value or
                 sort not in SortEnum._value2member_map_.values()) and
                    request.session.get('sort')):
                del request.session['sort']
            else:
                request.session['sort'] = sort
        sort = request.session.get('sort')
        if not sort:
            sort = SortEnum.NONE.value
        return sort

    @staticmethod
    def __get_sorted_queryset(queryset: QuerySet, sort: str) -> QuerySet:
        """
        Получение отсортированного queryset.

        Args:
            - queryset: queryset, подлежащего сортировке.
            - sort: тип сортировки.
        """
        annotate_params = {
            'in_stock': ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            )
        }
        sort_params = ['-in_stock']
        if sort == SortEnum.CRE_ASC.value:
            sort_params.append('created_at')

        if sort == SortEnum.CRE_DEC.value:
            sort_params.append('-created_at')

        if sort == SortEnum.POP_ASC.value:
            sort_params.append('-count_sells')

        if sort == SortEnum.POP_DEC.value:
            sort_params.append('count_sells')

        if sort == SortEnum.PRI_ASC.value:
            annotate_params['price'] = Min('sellerproduct__price')
            sort_params.append('-price')

        if sort == SortEnum.PRI_DEC.value:
            annotate_params['price'] = Min('sellerproduct__price')
            sort_params.append('price')

        if sort == SortEnum.REV_ASC.value:
            annotate_params['rev_count'] = Count('reviews')
            sort_params.append('-rev_count')

        if sort == SortEnum.REV_DEC.value:
            annotate_params['rev_count'] = Count('reviews')
            sort_params.append('rev_count')

        sort_params.append('sort_index')
        return queryset.annotate(
            **annotate_params,
        ).order_by(*sort_params).all()

    def get_context_data(
            self,
            context: Dict[str, Any],
            request: HttpRequest,
    ) -> Dict[str, Any]:
        context['sort'] = SortEnum
        curr_sort = request.session.get('sort')
        if curr_sort:
            context['curr_sort'] = curr_sort
        context['tags'] = Tag.objects.annotate(
            prod_count=Count('products')
        ).order_by('-prod_count').all()[:10]

        form = FilterForm()

        widget_attrs = form.fields['price'].widget.attrs
        widget_attrs['data-min'] = self.filter_prices['min']
        widget_attrs['data-max'] = self.filter_prices['max']
        widget_attrs['data-from'] = self.filter_prices['selected_min']
        widget_attrs['data-to'] = self.filter_prices['selected_max']
        form.fields['title'].widget.attrs['value'] = (
            self.filter_name
        ) if self.filter_name else ''
        form.fields['in_stock'].widget.attrs['checked'] = (
            True
        ) if self.filter_in_stock else False

        context['filter_form'] = form

        return context

    def process_get_params(self, request: HttpRequest, **kwargs,):
        self.__process_path_params(**kwargs)
        change_page = request.GET.get('p')
        if not change_page and not self.after_post:
            self.__clean_session_filter(request)
            self.__clean_session_search(request)

        self.filter_in_stock = request.session.get('filter_in_stock')
        self.filter_params = request.session.get('filter_params', {})
        self.filter_name = request.session.get('filter_name')
        self.filter_prices = request.session.get('filter_prices', {})
        self.search_query = request.session.get('search_query')

    def process_post_params(self, request: HttpRequest, **kwargs):
        self.__process_path_params(**kwargs)
        filter_form = FilterForm(request.POST)
        search_form = SearchForm(request.POST)
        self.__clean_session_filter(request)
        if filter_form.is_valid():
            cd = filter_form.cleaned_data
            filter_params = {}
            filter_prices = {}
            if cd['price']:
                price = cd['price'].split(';')
                filter_params['price__gte'] = price[0]
                filter_params['price__lte'] = price[1]
                filter_prices['selected_min'] = price[0]
                filter_prices['selected_max'] = price[1]
            if cd['title']:
                filter_params['name__icontains'] = cd['title']
                request.session['filter_name'] = cd['title']
            if cd['in_stock']:
                filter_params['amount__gt'] = 0
                filter_params['seller_count__gt'] = 0
                request.session['filter_in_stock'] = True

            if filter_params:
                request.session['filter_params'] = filter_params
            if filter_prices:
                request.session['filter_prices'] = filter_prices
        if request.POST.get('query') is not None and request.POST.get('query').strip() == '':
            self.__clean_session_search(request)
        if search_form.is_valid():
            request.session['search_query'] = search_form.cleaned_data['query']

        self.after_post = True

    def __process_path_params(self, **kwargs):
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

        discount_slug = kwargs.get('sale')
        if discount_slug:
            self.__process_discount_slug(discount_slug)

    def __process_discount_slug(self, discount_slug: str):
        product_discount = ProductDiscount.current.filter(
                slug=discount_slug,
            ).prefetch_related('products').first()

        category_discount = CategoryDiscount.current.filter(
                slug=discount_slug,
            ).prefetch_related('categories').first()

        combo_discount = ComboDiscount.current.filter(
            slug=discount_slug,
        ).prefetch_related('set_1', 'set_2').first()

        products = []
        categories = []

        if product_discount:
            products = list(
                product_discount.products.values_list('pk', flat=True).all(),
            )

        if category_discount:
            categories = list(
                category_discount.categories.values_list('pk', flat=True).all(),
            )

        if combo_discount:
            products.extend(
                list(
                    combo_discount.set_1.products.values_list(
                        'pk',
                        flat=True,
                    ).all(),
                ),
            )
            products.extend(
                list(
                    combo_discount.set_2.products.values_list(
                        'pk',
                        flat=True,
                    ).all(),
                ),
            )
            categories.extend(
                list(
                    combo_discount.set_1.categories.values_list(
                        'pk',
                        flat=True,
                    ).all(),
                ),
            )
            categories.extend(
                list(
                    combo_discount.set_2.categories.values_list(
                        'pk',
                        flat=True,
                    ).all(),
                ),
            )

        if products:
            self.products = products
        if categories:
            self.categories = categories

    @staticmethod
    def __clean_session_filter(request):
        if request.session.get('filter_in_stock'):
            del request.session['filter_in_stock']
        if request.session.get('filter_params'):
            del request.session['filter_params']
        if request.session.get('filter_prices'):
            del request.session['filter_prices']
        if request.session.get('filter_name'):
            del request.session['filter_name']

    @staticmethod
    def __clean_session_search(request):
        if request.session.get('search_query'):
            del request.session['search_query']












