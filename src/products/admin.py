from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from . import models


@admin.action(description="Archive")
def mark_archived(
        modeladmin: admin.ModelAdmin,
        request: HttpRequest,
        queryset: QuerySet,
):
    queryset.update(archived=True)


@admin.action(description="Un-archive")
def mark_unarchived(
        modeladmin: admin.ModelAdmin,
        request: HttpRequest,
        queryset: QuerySet,
):
    queryset.update(archived=False)


class PictureInline(admin.StackedInline):
    model = models.Picture
    extra = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    actions = [
        mark_archived,
        mark_unarchived
    ]
    # exclude = ['count_sells']
    inlines = [PictureInline]
    list_display = [
        'name',
        'category',
        'sellers_amount',
        'min_price',
        'avg_price',
        'archived',
    ]
    list_filter = ['category', 'archived']
    readonly_fields = ['count_sells']
    search_fields = ['name']

    @admin.display(description='Sellers')
    def sellers_amount(self, obj: models.Product) -> int:
        return 0
        # return len(obj.sellers) if obj.sellers else 0

    @admin.display(description='Min price', empty_value=0)
    def min_price(self, obj: models.Product) -> int:
        return obj.min_price()

    @admin.display(description='Avg price', empty_value=0)
    def avg_price(self, obj: models.Product) -> int:
        return obj.average_price()

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet):
        queryset.update(archived=True)


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_index']
    prepopulated_fields = {
        'slug': ('name',)
    }
    search_fields = ['name']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_index']


@admin.register(models.Seller)
class SellerAdmin(admin.ModelAdmin):
    """SellerAdmin placeholder"""
