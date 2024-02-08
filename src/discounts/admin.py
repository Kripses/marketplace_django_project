from django.contrib import admin

from . import models
from .forms import ComboDiscountAdminForm, DiscountAdminForm


class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'weight',
        'start',
        'end',
        'active',
    ]
    list_editable = [
        'weight',
    ]
    prepopulated_fields = {
        'slug': ('name',),
    }
    form = DiscountAdminForm
    radio_fields = {
        'discount_type': admin.HORIZONTAL
    }
    sortable_by = ['name', 'weight', 'start', 'end']


@admin.register(models.ProductDiscount)
class ProductDiscountAdmin(DiscountAdmin):
    raw_id_fields = ['products']
    search_fields = ['name', 'products__name']
    search_help_text = 'Поиск по названию скидки или названию продуктов.'


@admin.register(models.CategoryDiscount)
class CategoryDiscountAdmin(DiscountAdmin):
    raw_id_fields = ['categories']
    search_fields = ['name', 'categories__name']
    search_help_text = 'Поиск по названию скидки или названию категорий.'


@admin.register(models.BulkDiscount)
class BulkCategoryDiscountAdmin(DiscountAdmin):
    search_fields = ['name']
    search_help_text = 'Поиск по названию скидки.'


@admin.register(models.ComboDiscount)
class ComboDiscountAdmin(DiscountAdmin):
    raw_id_fields = ['set_1', 'set_2']
    form = ComboDiscountAdminForm
    search_fields = ['name', 'set_1__name', 'set_2__name']
    search_help_text = 'Поиск по названию скидки или названию наборов.'


@admin.register(models.ComboSet)
class ComboSetAdmin(admin.ModelAdmin):
    raw_id_fields = ['products', 'categories']
    search_fields = ['name', 'products__name', 'categories__name']
    search_help_text = 'Поиск по названию набора или названию товаров/категорий.'

