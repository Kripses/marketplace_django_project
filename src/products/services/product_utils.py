from decimal import Decimal

from django.db.models import Avg, Max, Min


def get_average_price(product: 'Product') -> Decimal:
    """ Средняя цены продукта. """
    avg_price = product.sellers.aggregate(
        avg=Avg('sellerproduct__price')
    ).get('avg')
    return round(avg_price, 2) if avg_price else 0.00


def discounted_average_price(product: 'Product') -> Decimal:
    """ Средняя цены продукта со скидкой. """
    from discounts.services.discount_utils import get_discounted_price_for_product
    avg_price = get_average_price(product)

    return round(get_discounted_price_for_product(product, avg_price), 2)


def get_min_price(product: 'Product') -> Decimal:
    """ Минимальная цена продукта. """
    min_price = product.sellers.aggregate(
        min=Min('sellerproduct__price')
    ).get('min')
    return round(min_price, 2) if min_price else 0.00


def get_discounted_min_price(product: 'Product') -> Decimal:
    """ Минимальная цены продукта со скидкой. """
    from discounts.services.discount_utils import get_discounted_price_for_product
    min_price = get_min_price(product)

    return round(get_discounted_price_for_product(product, min_price), 2)


def get_max_price(product: 'Product') -> Decimal:
    """ Максимальнаяцена продукта. """
    min_price = product.sellers.aggregate(
        max=Max('sellerproduct__price')
    ).get('max')
    return round(min_price, 2) if min_price else 0.00
