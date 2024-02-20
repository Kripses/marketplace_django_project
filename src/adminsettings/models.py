from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    reviews_count = models.PositiveIntegerField(default=10, verbose_name='Количество отзывов')
    products_per_page = models.PositiveIntegerField(default=20, verbose_name='Товаров на странице')
    min_price_for_free_delivery = models.PositiveIntegerField(
        default=2000,
        verbose_name='Минимальная сумма заказа для бесплатной доставки'
    )
    delivery_cost = models.PositiveIntegerField(default=100, verbose_name='Стоимость доставки')
    express_delivery_cost = models.PositiveIntegerField(default=600, verbose_name='Стоимость экспресс доставки')
    discount_percentage = models.PositiveIntegerField(default=0, verbose_name='Скидка на все товары')
    products_images = models.PositiveIntegerField(default=3, verbose_name='Количество изображений в карточке товара')
    amount_products_from_the_seller = models.PositiveIntegerField(default=20,
                                                                  verbose_name="количество товаров от одного продавца")
    top_product_cache_time = models.IntegerField(default=3600,
                                                 verbose_name="время кеширования топ товаров на странице продавца")

    class Meta:
        verbose_name = _('Site settings')
        verbose_name_plural = _('Site settings')
