from django.contrib import admin, messages
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import path

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'reviews_count',
        'products_per_page',
        'min_price_for_free_delivery',
        'delivery_cost',
        'express_delivery_cost',
        'discount_percentage',
        'products_images',
        'amount_products_from_the_seller'
    ]
    change_list_template = 'admin/cache-reset.html'

    def reset_cache_action(self, request):
        cache.clear()
        self.message_user(request, "Кеш успешно сброшен.", messages.SUCCESS)
        return redirect("..")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reset_cache/', self.reset_cache_action, name='reset_cache'),
        ]
        return custom_urls + urls
