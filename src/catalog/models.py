from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from account.models import Profile
from products.models import Product


class Review(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    text = models.TextField(max_length=1000, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'review'
        verbose_name_plural = 'reviews'


@receiver(post_save, sender=Review)
def clear_review_cache(sender, instance, **kwargs):
    """
    Очистка кеша при добавлении отзыва
    """
    product = instance.product
    cache_key = f'product_details_{product.pk}'
    cache.delete(cache_key)
