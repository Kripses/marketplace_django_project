import decimal

from django.test import TestCase

from discounts.services import discount_utils
from discounts.models import CategoryDiscount, ComboDiscount, BulkDiscount, ProductDiscount
from products.models import Product


class DiscountUtilsTest(TestCase):
    fixtures = [
        'fixtures/profile_fixture.json',
        'fixtures/category_fixture.json',
        'fixtures/products_fixture.json',
        'fixtures/sellers_fixture.json',
        'fixtures/seller_product_fixture.json',
        'fixtures/discounts_fixture.json',
    ]

    def test_get_discounted_price_percent(self):
        discount = ProductDiscount.objects.filter(pk=1).first()
        product = discount.products.first()
        price = product.sellerproduct_set.first().price
        result = discount_utils.get_discounted_price(discount, price)
        expected_price = round(
            price * (100 - discount.value) * decimal.Decimal(0.01),
            2,
        )
        self.assertEqual(result, expected_price)

    def test_get_discounted_price_fixed_value(self):
        discount = ProductDiscount.objects.filter(pk=2).first()
        product = discount.products.first()
        price = product.sellerproduct_set.first().price
        result = discount_utils.get_discounted_price(discount, price)
        expected_price = max(price - discount.value, discount.MIN_VALUE)
        self.assertEqual(result, expected_price)

    def test_get_discount_for_single_product(self):
        product = Product.active.filter(pk=3).first()
        discounts = [
            ProductDiscount.current.filter(pk=1).first(),
        ]
        result = discount_utils.get_all_discounts_for_single_product(product)
        self.assertEqual(result, discounts)

    def test_get_discounts_for_products(self):
        products = list(Product.active.filter(pk__in=[3, 7]).all())
        discounts = list(ProductDiscount.current.filter(pk__in=[1, 4]).all())
        discounts.append(CategoryDiscount.current.filter(pk=1).first())
        result = discount_utils.get_all_discounts_for_products(products)
        self.assertEqual(result, discounts)

    def test_get_priority_discount_for_product(self):
        product = Product.active.filter(pk=7).first()
        expected_discount = ProductDiscount.current.filter(pk=4).first()
        result = discount_utils.get_priority_discount_for_single_product(product)
        self.assertEqual(result, expected_discount)

    def test_get_discounted_price_for_product(self):
        product = Product.active.filter(pk=7).first()
        discount = ProductDiscount.current.filter(pk=4).first()
        price = product.sellerproduct_set.first().price
        result = discount_utils.get_discounted_price_for_product(product, price)
        expected_price = max(price - discount.value, discount.MIN_VALUE)
        self.assertEqual(result, expected_price)

    def test_get_combo_discounts_for_products(self):
        products = list(Product.active.filter(pk__in=[3, 5]))
        expected_discounts = [ComboDiscount.current.filter(pk=1).first()]
        result = discount_utils.get_combo_discounts_for_products(products)
        self.assertEqual(result, expected_discounts)

    def test_get_bulk_discount_not_unique(self):
        product = Product.active.filter(pk=16).first()
        # price = product.sellerproduct_set.first().price
        amount = 6
        product_data = [(product.sellerproduct_set.first(), amount)]
        result = discount_utils.get_bulk_discount(product_data)
        expected_discount = BulkDiscount.current.filter(pk=1).first()
        self.assertEqual(result, expected_discount)

    def test_get_bulk_discount_unique(self):
        products = Product.active.filter(pk__in=[14, 15, 16]).all()
        products_data = [
            (prod.sellerproduct_set.first(), 1)
            for prod in products
        ]
        result = discount_utils.get_bulk_discount(products_data)
        expected_discount = BulkDiscount.current.filter(pk=2).first()
        self.assertEqual(result, expected_discount)

    def test_calculate_discount_prices_one_product_overlapping_discounts(self):
        product = Product.active.filter(pk=7).first()
        seller_product = product.sellerproduct_set.first()
        discount = ProductDiscount.current.filter(pk=4).first()
        amount = 1
        expected_price = max(seller_product.price - discount.value, discount.MIN_VALUE)
        product_data = [(seller_product, amount)]
        expected_data = [(seller_product, expected_price, amount, True)]
        result = discount_utils.calculate_discounted_prices(product_data)
        self.assertEqual(result, expected_data)

    def test_calculate_discount_prices_one_product_bulk(self):
        product = Product.active.filter(pk=5).first()
        seller_product = product.sellerproduct_set.first()
        discount = BulkDiscount.current.filter(pk=1).first()
        amount = 2
        expected_price = round(
            seller_product.price * (100 - discount.value) * decimal.Decimal(0.01),
            2,
        )
        product_data = [(seller_product, amount)]
        expected_data = [(seller_product, expected_price, amount, True)]
        result = discount_utils.calculate_discounted_prices(product_data)
        self.assertEqual(result, expected_data)

    def test_calculate_discount_prices_combo(self):
        products = Product.active.filter(pk__in=[3, 5])
        discount = ComboDiscount.current.filter(pk=1).first()
        products_data = [
            (prod.sellerproduct_set.first(), 1)
            for prod in products
        ]
        expected_data = [
            (
                prod[0],
                round(
                    prod[0].price * (100 - discount.value) * decimal.Decimal(0.01),
                    2,
                ),
                prod[1],
                True,
            )
            for prod in products_data
        ]
        result = discount_utils.calculate_discounted_prices(products_data)
        self.assertEqual(set(result), set(expected_data))

    def test_calculate_discount_prices_mixed_cart(self):
        combo_products = Product.active.filter(pk__in=[3, 5])
        combo_discount = ComboDiscount.current.filter(pk=1).first()
        products_data = [
            (prod.sellerproduct_set.first(), 1)
            for prod in combo_products
        ]
        expected_data = [
            (
                prod[0],
                round(
                    prod[0].price * (100 - combo_discount.value) * decimal.Decimal(0.01),
                    2,
                ),
                prod[1],
                True,
            )
            for prod in products_data
        ]
        single_discount = ProductDiscount.objects.filter(pk=4).first()
        single_product = single_discount.products.first()
        single_product_data = (
            single_product.sellerproduct_set.first(),
            1,
        )
        products_data.append(single_product_data)
        expected_data.append((
            single_product_data[0],
            max(
                single_product_data[0].price - single_discount.value,
                single_discount.MIN_VALUE,
            ),
            single_product_data[1],
            True,
        ))
        no_discount_product = Product.objects.filter(pk=17).first()
        no_discount_product_data = (
            no_discount_product.sellerproduct_set.first(),
            1,
        )
        products_data.append(no_discount_product_data)
        expected_data.append((
            no_discount_product_data[0],
            no_discount_product_data[0].price,
            no_discount_product_data[1],
            False,
        ))
        result = discount_utils.calculate_discounted_prices(products_data)
        self.assertEqual(set(result), set(expected_data))
