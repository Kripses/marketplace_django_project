from django.test import TestCase
from django.urls import reverse

from account.models import Profile
from catalog.models import Review
from products.models import Category, Product


class ProductDetailsViewTestCase(TestCase):

    def setUp(self) -> None:
        self.user = Profile.objects.create_user(
            username="admin",
            email="admin@example.com",
            password='123'
        )
        self.client.login(email="admin@example.com", password='123')
        Category.objects.create(name="some category")
        Product.objects.create(
            category=Category.objects.first(),
            name="some product",
            slug="some_product"
        )

    def tearDown(self) -> None:
        self.client.logout()
        Profile.objects.filter(username='admin').delete()
        Category.objects.filter(name="some category").delete()
        Product.objects.filter(name="some product").delete()
        Review.objects.all().delete()

    def test_product_details_view_add_review(self):
        self.client.post(
            reverse("products:product_details", kwargs={"slug": Product.objects.first().slug}),
            {
                "text": 'text',
                "user_id": Profile.objects.first().id,
                "slug": Product.objects.first().slug
            }
        )
        self.assertTrue(Review.objects.filter(text="text").exists())
