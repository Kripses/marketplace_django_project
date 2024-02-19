from django.db.models import Min, Sum, Count, BooleanField, ExpressionWrapper, \
    Q
from django.test import RequestFactory, TestCase

from products.models import Product
from products.services.catalog_queryset import CatalogQuerySetProcessor, SortEnum


class CatalogQuerysetTest(TestCase):
    fixtures = [
        'fixtures/account_fixture.json',
        'fixtures/category_fixture.json',
        'fixtures/products_fixture.json',
        'fixtures/sellers_fixture.json',
        'fixtures/seller_product_fixture.json',
    ]

    def setUp(self):
        self.qs_processor = CatalogQuerySetProcessor()
        self.factory = RequestFactory()

    def test_get_base_queryset(self):
        request = self.factory.get('/catalog/')
        request.session = {}
        qs = self.qs_processor._CatalogQuerySetProcessor__get_base_queryset(request)
        target_qs = Product.active.all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_base_queryset_for_category(self):
        request = self.factory.get('/catalog/')
        request.session = {}
        categories = [2]
        self.qs_processor.categories = categories
        qs = self.qs_processor._CatalogQuerySetProcessor__get_base_queryset(request)
        target_qs = Product.active.filter(category__in=categories).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_base_queryset_for_pk(self):
        request = self.factory.get('/catalog/')
        request.session = {}
        pks = [1, 2, 3]
        self.qs_processor.products = pks
        qs = self.qs_processor._CatalogQuerySetProcessor__get_base_queryset(request)
        target_qs = Product.active.filter(pk__in=pks).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_base_queryset_for_search(self):
        request = self.factory.get('/catalog/')
        search = 'samsung'
        request.session = {'search_query': search}
        qs = self.qs_processor._CatalogQuerySetProcessor__get_base_queryset(request)
        target_qs = Product.active.filter(name__icontains=search).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_filtered_queryset_no_filter(self):
        base_qs = Product.active.all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_filtered_queryset(base_qs)
        self.assertQuerySetEqual(qs, base_qs, ordered=False)

    def test_get_filtered_queryset_price(self):
        base_qs = Product.active.all()
        min_pr = 100
        max_pr = 1000
        self.qs_processor.filter_params = {
            'price__gte': min_pr,
            'price__lte': max_pr,
        }
        qs = self.qs_processor._CatalogQuerySetProcessor__get_filtered_queryset(base_qs)
        target_qs = base_qs.annotate(
                    price=Min('sellerproduct__price'),
                ).filter(price__gte=min_pr, price__lte=max_pr).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_filtered_queryset_title(self):
        base_qs = Product.active.all()
        title = 'samsung'
        self.qs_processor.filter_params = {
            'name__icontains': title
        }
        qs = self.qs_processor._CatalogQuerySetProcessor__get_filtered_queryset(base_qs)
        target_qs = base_qs.filter(name__icontains=title).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_filtered_queryset_in_stock(self):
        base_qs = Product.active.annotate(
                    amount=Sum('sellerproduct__count'),
                    seller_count=Count('sellerproduct'),
                ).all()
        self.qs_processor.filter_params = {
            'amount__gt': 0,
            'seller_count__gt': 0,
        }
        qs = self.qs_processor._CatalogQuerySetProcessor__get_filtered_queryset(base_qs)
        target_qs = base_qs.filter(amount__gte=0, seller_count__gt=0).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_sort_type_none(self):
        request = self.factory.get('/catalog/')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.NONE.value)

    def test_get_sort_type_none_with_pre_existing(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.NONE.value}')
        request.session = {'sort': SortEnum.CRE_ASC.value}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.NONE.value)
        self.assertEqual(request.session.get('sort'), None)

    def test_get_sort_type_wrong_value(self):
        request = self.factory.get('/catalog/?sort=qwer')
        request.session = {'sort': SortEnum.CRE_ASC.value}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(
            request)
        self.assertEqual(sort, SortEnum.NONE.value)
        self.assertEqual(request.session.get('sort'), None)

    def test_get_sort_type_price_ascending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.PRI_ASC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.PRI_ASC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.PRI_ASC.value)

    def test_get_sort_type_price_descending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.PRI_DEC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.PRI_DEC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.PRI_DEC.value)

    def test_get_sort_type_popularity_ascending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.POP_ASC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.POP_ASC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.POP_ASC.value)

    def test_get_sort_type_popularity_descending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.POP_DEC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.POP_DEC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.POP_DEC.value)

    def test_get_sort_type_reviews_ascending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.REV_ASC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.REV_ASC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.REV_ASC.value)

    def test_get_sort_type_reviews_descending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.REV_DEC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.REV_DEC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.REV_DEC.value)

    def test_get_sort_type_created_ascending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.CRE_ASC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.CRE_ASC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.CRE_ASC.value)

    def test_get_sort_type_created_descending(self):
        request = self.factory.get(f'/catalog/?sort={SortEnum.CRE_DEC.value}')
        request.session = {}
        sort = self.qs_processor._CatalogQuerySetProcessor__get_selected_sort_type(request)
        self.assertEqual(sort, SortEnum.CRE_DEC.value)
        self.assertEqual(request.session.get('sort'), SortEnum.CRE_DEC.value)

    def test_get_sorted_queryset_price(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.PRI_ASC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
            price=Min('sellerproduct__price'),
        ).order_by('-price', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_created(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.CRE_ASC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
        ).order_by('created_at', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_popularity(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.POP_ASC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
        ).order_by('-count_sells', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_reviews(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.REV_ASC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
            rev_count=Count('reviews'),
        ).order_by('-rev_count', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_price_desc(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.PRI_DEC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
            price=Min('sellerproduct__price'),
        ).order_by('price', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_created_desc(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.CRE_DEC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
        ).order_by('-created_at', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_popularity_desc(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.POP_DEC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
        ).order_by('count_sells', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_sorted_queryset_reviews_desc(self):
        base_qs = Product.active.annotate(
            seller_count=Count('sellerproduct'),
        ).all()
        qs = self.qs_processor._CatalogQuerySetProcessor__get_sorted_queryset(base_qs, SortEnum.REV_DEC.value)
        target_qs = base_qs.annotate(
            in_stock=ExpressionWrapper(
                Q(seller_count__gt=0),
                output_field=BooleanField()
            ),
            rev_count=Count('reviews'),
        ).order_by('rev_count', 'in_stock')
        self.assertQuerysetEqual(qs, target_qs)

    def test_get_queryset(self):
        request = self.factory.get('/catalog/')
        request.session = {}
        qs = self.qs_processor.get_queryset(request)
        target_qs = Product.active.all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_queryset_search(self):
        search = 'samsung'
        request = self.factory.post('/catalog/', {'query': search})
        request.session = {}
        self.qs_processor.process_post_params(request)
        self.qs_processor.process_get_params(request)
        qs = self.qs_processor.get_queryset(request)
        target_qs = Product.active.filter(name__icontains=search).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_queryset_clean_after_search(self):
        request = self.factory.get('/catalog/')
        request.session = {'search_query': 'samsung'}
        self.qs_processor.process_get_params(request)
        qs = self.qs_processor.get_queryset(request)
        target_qs = Product.active.all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)

    def test_get_queryset_pagination_after_search(self):
        search = 'samsung'
        request = self.factory.get('/catalog/?p=2')
        request.session = {'search_query': search}
        self.qs_processor.process_get_params(request)
        qs = self.qs_processor.get_queryset(request)
        target_qs = Product.active.filter(name__icontains=search).all()
        self.assertQuerySetEqual(qs, target_qs, ordered=False)