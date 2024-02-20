import decimal
from decimal import Decimal
from typing import Any, List, Iterable, Union, Tuple

from django.db.models import Q

from discounts.models import (
    BulkDiscount,
    CategoryDiscount,
    ComboDiscount,
    Discount,
    DiscountTypeEnum,
    ProductDiscount,
)
from products.models import Product, SellerProduct


def get_discounted_price(discount: Discount, price: Decimal) -> Decimal:
    """
    Получение цены после применения скидки.

    Args:
        discount (Discount): применяемая скидка.
        price (Decimal): оригинальная цена.

    Returns:
        Цена после вычета скидки (Decimal).
    """
    if discount.discount_type == DiscountTypeEnum.PERCENTAGE:
        return round(price * (100 - discount.value) * decimal.Decimal(0.01), 2)
    elif discount.discount_type == DiscountTypeEnum.FIXED_VALUE:
        return max(price - discount.value, discount.MIN_VALUE)
    return discount.value


def __get_sort_params(discount: Discount) -> Tuple[int, int]:
    """ Функция-key для сортировки списка скидок. """
    type_weights = {
        ProductDiscount: 3,
        CategoryDiscount: 2,
        ComboDiscount: 1,
        BulkDiscount: 0,
    }
    return discount.weight, type_weights[type(discount)]


def get_all_discounts_for_products(
        products: Union[
            Product,
            Iterable[Product],
            int,
            Iterable[int],
        ]
) -> List[Any]:
    """
    Получение списка скидок, применимых к продукту/списку продуктов.

    Args:
        products: продукт или список продуктов, для которых нужно найти скидки.

    Returns:
        Список применимых к продукту(ам) скидок.
    """
    if not isinstance(products, Iterable):
        products = (products,)

    discounts = []
    product_discounts = ProductDiscount.current.filter(
        products__in=products,
    )
    discounts.extend(product_discounts)
    category_discounts = CategoryDiscount.current.filter(
        categories__products__in=products
    )
    discounts.extend(category_discounts)
    return discounts


def get_all_discounts_for_single_product(
    product: Union[
        Product,
        int,
    ],
) -> List[Any]:
    """
    Получения списка скидок, применимых к продукту.

    Args:
        product: продукт, для которого нужно найти скидки.

    Returns:
        Список применимых к продукту скидок.
    """
    return get_all_discounts_for_products(product)


def get_priority_discount_for_products(
    products: Union[
        Product,
        Iterable[Product],
        int,
        Iterable[int],
    ],
) -> Any:
    discounts = get_all_discounts_for_products(products)
    if discounts:
        discounts.sort(key=__get_sort_params, reverse=True)
        return discounts[0]


def get_priority_discount_for_single_product(
    product: Union[
        Product,
        int,
    ],
) -> Any:
    """
    Получение наивысшей по приоритету скидки, применимой к продукту.

    Args:
         product: продукт, для которого нужно получить скидку.

    Returns:
        Наивысшая по приоритету скидка, действующая на продукт.
    """
    return get_priority_discount_for_products(product)


def get_discounted_price_for_product(
    product: Union[
        Product,
        int,
    ],
    price: Decimal = None,
) -> Any:
    """
    Получение цены на продукт со скидкой.

    Если изначальная цена не указана, высчитывается скидка от максимальной цены.

    Args:
        product: продукт, на который нужно получить цену.
        price: Изначальная цена продукта.

    Returns:
        Цена после вычета скидки.
    """
    if not isinstance(product, Product):
        product = Product.active.filter(pk=product).first()
        if not product:
            return price

    discount = get_priority_discount_for_single_product(product)
    if not price:
        price = product.max_price

    if discount:
        return get_discounted_price(discount, price)
    return price


def get_combo_discounts_for_products(
    products: Union[
        Iterable[Product],
        Iterable[int],
    ]
) -> Any:
    """
    Получение скидок на наборы, применимых к списку продуктов.

    Args:
        products: Список продуктов, для которых нужно найти скидки.

    Returns:
        Список скидок на наборы, применимых к продуктам.
    """
    combo_discounts = list(ComboDiscount.current.filter(
        Q(set_1__products__in=products) | Q(set_1__categories__products__in=products),
        Q(set_2__products__in=products) | Q(set_2__categories__products__in=products),
    ).order_by('weight').all())
    return combo_discounts


def get_bulk_discount(products: List[Tuple[SellerProduct, int]]) -> Any:
    """
    Получение списка оптовых скидок, применимых к списку продуктов.

    Args:
        products: Список кортежей (SellerProduct, Количество), для которых
                  нужно найти скидки.
    Returns:
        Список скидок, применимых к продуктам.
    """
    unique_amount = len(products)
    total_amount = sum([prod[1] for prod in products])
    total_price = sum([prod[0].price * prod[1] for prod in products])

    discount = BulkDiscount.current.filter(
        Q(product_amount__lte=unique_amount, only_unique=True) | Q(product_amount__lte=total_amount, only_unique=False),
        total_sum__lte=total_price,
    ).order_by('-weight', '-total_sum', '-product_amount').first()
    return discount


def calculate_discounted_prices(
    products: List[Tuple[SellerProduct, int]]
) -> List[Tuple[SellerProduct, Decimal, int, bool]]:
    """
    # TOP
    Вычисление цен со скидками для продуктов.

    Предназначается для вычисления цен на список товаров в корзине.

    Args:
        products: Список кортежей с информацией о продуктах.
                  (SellerProduct, Количество)

    Returns:
        Список кортежей с информацией о товарах после применения скидок.
        (SellerProduct, Цена со скидкой, Количество, Применена ли скидка)
    """
    product_discounts = get_all_discounts_for_products(
        [product[0].product for product in products],
    )
    combo_discounts = get_combo_discounts_for_products(
        [product[0].product for product in products],
    )
    bulk_discount = get_bulk_discount(products)

    discounts = [*product_discounts, *combo_discounts]
    if bulk_discount:
        discounts.append(bulk_discount)

    if discounts:
        discounts.sort(key=__get_sort_params, reverse=True)

    if bulk_discount and discounts[0] is bulk_discount:
        return _process_multiproduct_discount(products, bulk_discount)

    if bulk_discount:
        discounts.remove(bulk_discount)

    return _process_discounts(products, discounts)


def _process_discounts(
    products: List[Tuple[SellerProduct, int]],
    discounts: List[Union[
        'ProductDiscount',
        'ComboDiscount',
        'CategoryDiscount',
    ]],
) -> List[Tuple[SellerProduct, Decimal, int, bool]]:
    """
    Обработка списка товаров с применением скидок.

    Args:
        products: Список кортежей с информацией о продуктах.
                  (SellerProduct, Количество)
        discounts: Список скидок для применения к продуктам.
    Returns:
        Список кортежей с информацией о товарах после применения скидок.
        (SellerProduct, Цена со скидкой, Количество, Применена ли скидка)
    """
    result = []
    for discount in discounts:
        if isinstance(discount, ComboDiscount):
            processed = _process_combo_discount(products, discount)
        else:
            processed = _process_individual_discount(products, discount)
        if processed:
            result.extend(processed)
        if not products:
            break

    if products:
        result.extend(
            (product[0], product[0].price, product[1], False)
            for product in products
        )

    return result


def _process_combo_discount(
    products: List[Tuple[SellerProduct, int]],
    discount: 'ComboDiscount',
) -> List[Tuple[SellerProduct, Decimal, int, bool]]:
    """
    Обработка списка товаров с применением скидок на наборы продуктов.

    Args:
        products: Список кортежей с информацией о продуктах.
                  (SellerProduct, Количество)
        discounts: Список скидок на наборы для применения к продуктам.
    Returns:
        Список кортежей с информацией о товарах после применения скидок.
        (SellerProduct, Цена со скидкой, Количество, Применена ли скидка)
    """
    def filter_set1(product: Tuple[SellerProduct, int]):
        product = product[0].product
        return (
            product in discount.set_1.products.all() or
            product.category in discount.set_1.categories.all()
        )

    def filter_set2(product: Tuple[SellerProduct, int]):
        product = product[0].product
        return (
            product in discount.set_2.products.all() or
            product.category in discount.set_2.categories.all()
        )

    result = []

    products_1 = list(filter(filter_set1, products))
    remaining_products = list(set(products)-set(products_1))
    products_2 = list(filter(filter_set2, remaining_products))

    if products_1 and products_2:
        products_1.extend(products_2)
        processed_products = _process_multiproduct_discount(
            products_1,
            discount,
        )
        for prod in products_1:
            products.remove(prod)
        result.extend(processed_products)

    return result


def _process_individual_discount(
    products: List[Tuple[SellerProduct, int]],
    discount: Union['ProductDiscount', 'CategoryDiscount'],
) -> List[Tuple[SellerProduct, Decimal, int, bool]]:
    """
    Обработка списка товаров с применением скидок на отдельные товары.

    Args:
        products: Список кортежей с информацией о продуктах.
                  (SellerProduct, Количество)
        discounts: Список скидок для применения к продуктам.
    Returns:
        Список кортежей с информацией о товарах после применения скидок.
        (SellerProduct, Цена со скидкой, Количество, Применена ли скидка)
    """
    def filter_product(product: Tuple[SellerProduct, int]):
        product = product[0].product
        if isinstance(discount, CategoryDiscount):
            return product.category in discount.categories.all()
        else:
            return product in discount.products.all()

    viable_products = list(filter(filter_product, products))

    result = []
    for prod in viable_products:
        product, amount = prod
        discounted_price = get_discounted_price(discount, product.price)
        processed_product = (product, discounted_price, amount, True)
        result.append(processed_product)
        products.remove(prod)

    return result


def _process_multiproduct_discount(
    products: List[Tuple[SellerProduct, int]],
    discount: Union[BulkDiscount, ComboDiscount],
) -> List[Tuple[SellerProduct, Decimal, int, bool]]:
    """
    Обработка списка товаров с применением одной скидки ко всему списку.

    Args:
        products: Список кортежей с информацией о продуктах.
                  (SellerProduct, Количество)
        discount: Скидок для применения к продуктам.
    Returns:
        Список кортежей с информацией о товарах после применения скидок.
        (SellerProduct, Цена со скидкой, Количество, Применена ли скидка)

    """
    result = []

    total_price = sum([product[0].price*product[1] for product in products])

    for product in products:
        product, amount = product

        if discount.discount_type == DiscountTypeEnum.PERCENTAGE:
            discounted_price = round(
                product.price * (100 - discount.value) * decimal.Decimal(0.01), 2
            )
        else:
            proportion = product.price / total_price
            if discount.discount_type == DiscountTypeEnum.FIXED_VALUE:
                discounted_price = round(
                    max(
                        product.price - (discount.value * proportion),
                        discount.MIN_VALUE,
                    ),
                    2,
                )
            else:
                discounted_price = round(
                    discount.value * proportion,
                    2,
                )
        processed_product = (product, discounted_price, amount, True)
        result.append(processed_product)

    return result
