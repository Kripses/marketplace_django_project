from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from products.models import Product, SellerProduct


class Profile(AbstractUser):
    """
    Модель для описания пользователей.

    registered_at - дата регистрации
    agreement_accept - пользовательское соглашение
    phone - телефон
    avatar - фото пользователя
    address - адрес проживаиния (доставки)
    cart - корзина пользователя
    archived - архивирование страницы продавца для мягкого удаления
    email - адрес электронной почты (используется для входа)
    """
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

    class Meta:
        verbose_name = _('Seller')
        verbose_name_plural = _('Sellers')

    def __str__(self) -> str:
        return f"{self.name}"
