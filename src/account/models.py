from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from products.models import Product, SellerProduct


class Profile(AbstractUser):
    registered_at = models.DateTimeField(auto_now_add=True)
    agreement_accept = models.BooleanField(default=False)
    phone = models.CharField(max_length=14, unique=True, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    cart = models.IntegerField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    # Заменяем поле имени пользователя на электронную почту для аутентификации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # 'username' требуется по умолчанию


class BrowsingHistory(models.Model):
    """
    Модель истории просмотра товаров пользователем
    """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self) -> str:
        """
        Получение абсолютной ссылки на продукт.
        """
        return reverse('products:product_details', kwargs={'slug': self.product.slug})


class Seller(models.Model):
    """
    Модель для описания продавцов.

    name - название продавца;
    description - описание продавца;
    products - список продавакмых товаров;
    profile - связь с моделью профиля пользователя;
    archived - архивирование страницы продавца для мягкого удаления.
    """
    name = models.CharField(max_length=30)
    description = models.TextField()
    products = models.ManyToManyField(
        Product,
        through=SellerProduct,
        through_fields=('seller', 'product'),
        related_name='sellers',
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name}"
