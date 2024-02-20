from abc import ABC
import datetime
import random
from typing import Dict, List

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Min, Q

from products.models import Category, Product


FIXED_KEY = 'index_banners_fixed'
SLIDER_KEY = 'index_banners_slider'
TOP_SELLERS_KEY = 'index_top_sellers'
LIMITED_OFFERS_KEY = 'index_limited_offer'
TIMED_LIMITED_OFFER_KEY = 'index_timed_limited_offer'


class CacheableContextProduct(ABC):
    """
        Базовый DTO с информацией о продукте.

        Пригодный для кэширования.
    """
    def __init__(self, product: Product):
        self.pk = product.pk
        self.name = product.name
        self.absolute_url = product.get_absolute_url()
        image = product.images.all()[0].image
        self.image_url = settings.MEDIA_URL + str(image) if image else ''


class ProductPreviewCard(CacheableContextProduct):
    """ DTO с информацией о продукте для preview карточки. """
    def __init__(self, product: Product):
        super().__init__(product)
        self.category = product.category.full_name
        self.price = product.min_price
        self.discounted_price = product.discounted_min_price


class CacheableContextCategory:
    """
        Базовый DTO с информацией о категории продукта.

        Пригодный для кэширования.
    """
    def __init__(self, category: Category):
        self.name = category.name
        self.absolute_url = category.get_absolute_url()


class Banner:
    """
        Класс, содержащий баннеры для главной страницы.

        Баннеры-слайдеры товаров и баннеры категорий.
    """
    class SliderProduct(CacheableContextProduct):
        """ DTO с информаций о товаре для баннера-слайдера. """
        def __init__(self, product: Product):
            super().__init__(product)
            self.description = product.description

    class BannerCategory(CacheableContextCategory):
        """ DTO с информацией о категории для баннера. """
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
    """ DTO с информацией о товаре для preview карточки популярного товара. """
    def __init__(self, product: Product):
        super().__init__(product)

    @staticmethod
    def get_top_sellers(amount : int = 8) -> List['TopSellerProduct']:
        """ Получение списка preview карточек популярных товаров. """
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
    """ DTO с информацией о товаре для карточки лимитированного товара. """
    def __init__(self, product: Product):
        super().__init__(product)

    @staticmethod
    def get_limited_offers(
            amount: int = 16,
    ) -> Dict[str, List['LimitedProduct']]:
        """ Получение карточек лимитированных товаров. """
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
                end_time = LimitedProduct._get_limited_offer_end_time()
                seconds_until_end_time = (end_time - datetime.datetime.now()).seconds
                cache.set(
                    LIMITED_OFFERS_KEY,
                    limited_offers,
                    timeout=seconds_until_end_time,
                )

        if limited_offers:
            result['regular'] = limited_offers
        if timed_limited_offer:
            end_time = LimitedProduct._get_limited_offer_end_time()
            timed_limited_offer.end_time = end_time
            result['timed'] = timed_limited_offer
        return result

    @staticmethod
    def _get_limited_offer_end_time() -> datetime.datetime:
        """ Получение времени окончания действия временного баннера. """
        today = datetime.datetime.now(datetime.timezone.utc).today()
        return (
                datetime.datetime(today.year, today.month, today.day) +
                datetime.timedelta(days=1)
        )


def clear_banner_cache() -> None:
    """ Функция для очистки кэша баннеров """
    cache.delete(FIXED_KEY)
    cache.delete(SLIDER_KEY)
    cache.delete(TOP_SELLERS_KEY)
    cache.delete(LIMITED_OFFERS_KEY)
    cache.delete(TIMED_LIMITED_OFFER_KEY)
