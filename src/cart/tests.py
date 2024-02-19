from django.test import TestCase
from django.urls import reverse

from account.models import Profile
from adminsettings.models import SiteSettings
from cart.models import Order


class CreateOrderViewTestCase(TestCase):
    def setUp(self) -> None:
        SiteSettings.objects.create()
        self.user = Profile.objects.create_user(
            username="admin",
            email="admin@example.com",
            password='123'
        )
        self.client.login(email="admin@example.com", password='123')

    def tearDown(self) -> None:
        self.client.logout()
        Profile.objects.filter(username='admin').delete()

    def test_create_order_view(self):
        responce = self.client.post(
            reverse("cart:create_order"),
            {
                "profile": Profile.objects.first().id,
                "fio": "Иванов Иван",
                "phone": "+79998887766",
                "email": "admin@example.com",
                "cart": {
                    "16": {
                        "image": "SAMSUNG.webp",
                        "name": "SSD",
                        "slug": "ssd",
                        "description": "SSD Samsung",
                        "price": 199.0,
                        "count": 1,
                        "seller": "Mvideo"
                    },
                },
                "city": "Moskow",
                "delivery_address": "Kutuzova 14",
                "delivery_type": "Обычная доставка",
                "payment_type": "Онлайн картой",
                "comment": "Тестовый заказ",
                "total_price": "999.00",
                "payment_id": "1",
            },
        )

        self.assertEqual(responce.status_code, 302)
        self.assertTrue(
            Order.objects.filter(phone="9998887766").exists()
        )
