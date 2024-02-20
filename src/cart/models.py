from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from products.models import SellerProduct

from account.models import Profile


class Cart(models.Model):
    product_seller = models.ForeignKey(SellerProduct, on_delete=models.CASCADE, null=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='cart_profile')
    count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def clean(self, product_amt=0):
        if (product_amt > self.product_seller.count) \
                or ((self.count + 1 > self.product_seller.count) and (product_amt == 0)):
            raise ValidationError(
                    "Can't be more than total",
                )


class Order(models.Model):
    """
    Модель для описания заказа покупателя.

    profile - id пользователя;
    fio - фамилия, имя и отчество покупателя;
    phone - телефон покупателя;
    email - адрес электронной почты покупателя;
    cart - перечень товаров в заказе;
    delivery_address - адрес доставки;
    delivery_type - способ доставки;
    payment_type - способ оплаты;
    comment - коментарий к заказу;
    archived - метка для мягкого удаления;
    created_at - дата и время создания заказа;
    status - статус заказа;
    total_price - итоговая стоимость заказа;
    """
    profile = models.CharField(max_length=4, null=False, blank=False)
    fio = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(null=False, blank=False)
    cart = models.JSONField(null=False, blank=False)
    city = models.CharField(max_length=255, null=False, blank=False)
    delivery_address = models.CharField(max_length=255, null=False, blank=False)
    delivery_type = models.CharField(default='обычная доставка', max_length=20)
    payment_type = models.CharField(max_length=40)
    comment = models.TextField(null=False, blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.SlugField(max_length=200, unique=True, null=True)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
