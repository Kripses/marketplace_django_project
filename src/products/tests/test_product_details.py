from django.test import TestCase
from django.urls import reverse

from products.models import Product, Category
from account.models import Profile, BrowsingHistory


class ProductDetailsViewTest(TestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(
            username="user",
            email="user@test",
            password='password'
        )
        self.client.login(email="user@test", password='password')
        self.category = Category.objects.create(name='Test category')
        self.product_slug = 'product_slug'
        self.product = Product.objects.create(
            category=self.category,
            name='Test product name',
            description='Test description',
            slug=self.product_slug
        )
        self.url = reverse('products:product_details', kwargs={'slug': self.product_slug})

    def tearDown(self) -> None:
        self.client.logout()
        Profile.objects.filter(username='user').delete()
        Category.objects.filter(name="Test category").delete()
        Product.objects.filter(name="Test product name").delete()

    def test_product_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.product.description)

    def test_product_model_fields(self):
        self.assertEqual(self.product.name, 'Test product name')
        self.assertEqual(self.product.description, 'Test description')
        self.assertEqual(self.product.category, self.category)

    def test_add_to_browsing_history(self):
        self.assertEqual(BrowsingHistory.objects.filter(profile=self.user).count(), 0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BrowsingHistory.objects.filter(profile=self.user).count(), 1)
