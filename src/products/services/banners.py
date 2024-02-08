import datetime
import random

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Min, Q

from products.models import Category, Product


FIXED_KEY = 'index_banners_fixed'
SLIDER_KEY = 'index_banners_slider'
TOP_SELLERS_KEY = 'index_top_sellers'
LIMITED_OFFERS_KEY = 'index_limited_offer'
TIMED_LIMITED_OFFER_KEY = 'index_timed_limited_offer'


class CacheableContextProduct:
    def __init__(self, product: Product):
        self.pk = product.pk
        self.name = product.name
        self.absolute_url = product.get_absolute_url()
        image = product.images.all()[0].image
        self.image_url = settings.MEDIA_URL + str(image) if image else ''


class ProductPreviewCard(CacheableContextProduct):
    def __init__(self, product: Product):
        super().__init__(product)
        self.category = product.category.full_name
        self.price = product.min_price
        self.discounted_price = product.discounted_min_price


class CacheableContextCategory:
    def __init__(self, category: Category):
        self.name = category.name
        self.absolute_url = category.get_absolute_url()


class Banner:
    class SliderProduct(CacheableContextProduct):
        def __init__(self, product: Product):
            super().__init__(product)
            self.description = product.description

    class BannerCategory(CacheableContextCategory):
        def __init__(self, category: Category):
            super().__init__(category)
            sample = category.products.filter(
                archived=False,
            ).annotate(
                min=Min('sellerproduct__price'),
            ).order_by('min').prefetch_related('images').first()
            self.min_price = sample.discounted_min_price
            self.image_url = sample.images.first().image.url

    def __init__(self, fixed_amount=3, slider_amount=3):
        self.fixed = cache.get(FIXED_KEY)

        if not self.fixed:
            categories = Category.objects.annotate(
                    num_products=Count('products', filter=Q(
                        products__archived=False))
                ).filter(is_active=True, num_products__gt=0).all()

            if categories:
                random_categories = random.sample(
                    list(categories),
                    k=fixed_amount,
                )

                self.fixed = [self.BannerCategory(category)
                              for category in random_categories]

                cache.set(FIXED_KEY, self.fixed)

        self.slider = cache.get(SLIDER_KEY)

        if not self.slider:
            products = Product.objects.annotate(
                seller_count=Count('sellerproduct')
            ).filter(
                    archived=False,
                    category__is_active=True,
                    seller_count__gt=0,
                ).prefetch_related('images').all()
            if products:
                random_products = random.sample(
                    list(products),
                    k=slider_amount,
                )

                self.slider = [self.SliderProduct(product)
                               for product in random_products]
                cache.set(SLIDER_KEY, self.slider)


class TopSellerProduct(ProductPreviewCard):
    def __init__(self, product: Product):
        super().__init__(product)

    @staticmethod
    def get_top_sellers(amount=8):
        top_sellers = cache.get(TOP_SELLERS_KEY)

        if not top_sellers:
            products = Product.objects.annotate(
                seller_count=Count('sellerproduct')
            ).filter(
                archived=False,
                category__is_active=True,
                seller_count__gt=0,
            ).order_by(
                '-sort_index',
                '-count_sells',
            ).select_related(
                'category',
            ).prefetch_related('images').all()[:amount]
            top_sellers = [TopSellerProduct(product)
                           for product in products]
            cache.set(TOP_SELLERS_KEY, top_sellers)

        return top_sellers


class LimitedProduct(ProductPreviewCard):
    def __init__(self, product: Product):
        super().__init__(product)

    @staticmethod
    def get_limited_offers(amount=16):
        limited_offers = cache.get(LIMITED_OFFERS_KEY)
        timed_limited_offer = cache.get(TIMED_LIMITED_OFFER_KEY)

        result = {}
        if not limited_offers or not timed_limited_offer:
            products = Product.objects.annotate(
                seller_count=Count('sellerproduct')
            ).filter(
                archived=False,
                category__is_active=True,
                seller_count__gt=0,
                limited=True,
            )
            if timed_limited_offer and not limited_offers:
                products = products.exclude(pk=timed_limited_offer.pk)

            products = products.select_related(
                'category',
            ).prefetch_related('images').all()

            products = list(products)

            if not timed_limited_offer and products:
                product = random.choice(products)
                products.remove(product)
                timed_limited_offer = LimitedProduct(product)
                cache.set(TIMED_LIMITED_OFFER_KEY, timed_limited_offer)

            if products:
                if len(products) > amount:
                    products = random.choices(products, k=amount)
                limited_offers = [LimitedProduct(product)
                                  for product in products]
                now = datetime.datetime.now()
                midnight = datetime.datetime.combine(
                    now + datetime.timedelta(days=1),
                    datetime.time(),
                )
                seconds_until_midnight = (midnight - now).seconds
                cache.set(
                    LIMITED_OFFERS_KEY,
                    limited_offers,
                    timeout=seconds_until_midnight,
                )

        if limited_offers:
            result['regular'] = limited_offers
        if timed_limited_offer:
            today = datetime.date.today()
            end_time = today + datetime.timedelta(days=2)
            timed_limited_offer.end_time = end_time
            result['timed'] = timed_limited_offer
        return result
