from django.test import TestCase


class CatalogPageTest(TestCase):
    fixtures = [
        'fixtures/profile_fixture.json',
        'fixtures/category_fixture.json',
        'fixtures/products_fixture.json',
        'fixtures/sellers_fixture.json',
        'fixtures/seller_product_fixture.json',
    ]

    def test_catalog(self):
        response = self.client.get('/catalog/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 8)
        self.assertEqual(response.context_data['products'].paginator.count, 17)

    def test_catalog_pagination(self):
        response = self.client.get('/catalog/?p=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 1)
        self.assertEqual(response.context_data['products'].paginator.count, 17)

    def test_catalog_name_filter(self):
        response = self.client.post('/catalog/', {'title': 'samsung'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 5)
        self.assertEqual(response.context_data['products'].paginator.count, 5)

    def test_catalog_price_filter(self):
        response = self.client.post('/catalog/', {'price': '100;1000'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 8)
        self.assertEqual(response.context_data['products'].paginator.count, 10)

    def test_catalog_price_filter_with_pagination(self):
        self.client.post('/catalog/', {'price': '100;1000'})
        response = self.client.get('/catalog/?p=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 2)
        self.assertEqual(response.context_data['products'].paginator.count, 10)

    def test_catalog_header_search(self):
        response = self.client.post('/catalog/', {'query': 'samsung'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['products']), 5)
        self.assertEqual(response.context_data['products'].paginator.count, 5)