from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product, SellerProduct


@receiver(post_save, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """
    Очистка кеша модели Product при изменении товара в БД.
    """
    cache_key = f'product_details_{instance.pk}'
    cache.delete(cache_key)


@receiver(post_save, sender=SellerProduct)
def clear_sellerproduct_cache(sender, instance, **kwargs):
    """
    Очистка кеша при добавлении/изменении товара продавцом
    """
    product = instance.product
    cache_key = f'product_details_{product.pk}'
    cache.delete(cache_key)
