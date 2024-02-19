from django.contrib import admin
from django.db.models import QuerySet
from django import forms
from django.http import HttpRequest
from django.urls import path
from modeltranslation.admin import TranslationAdmin

from products import admin_filters, models
from products.views import ProductImportFormView


@admin.action(description="Archive selected products")
def mark_archived(
        modeladmin: admin.ModelAdmin,
        request: HttpRequest,
        queryset: QuerySet,
):
    queryset.update(archived=True)


@admin.action(description="Un-archive selected products")
def mark_unarchived(
        modeladmin: admin.ModelAdmin,
        request: HttpRequest,
        queryset: QuerySet,
):
    queryset.update(archived=False)


class PictureInline(admin.StackedInline):
    model = models.Picture
    extra = 1


@admin.register(models.Value)
class PropertyValueAdmin(TranslationAdmin):

    actions = [
        mark_archived,
        mark_unarchived
    ]
    list_display = [
        'product',
        'property',
        'value',
    ]


@admin.register(models.Property)
class PropertyAdmin(TranslationAdmin):

    actions = [
        mark_archived,
        mark_unarchived
    ]
    list_display = [
        'category',
        'name',
    ]


@admin.register(models.Product)
class ProductAdmin(TranslationAdmin):
    actions = [
        mark_archived,
        mark_unarchived
    ]
    change_list_template = 'admin/product_change_list.html'
    inlines = [PictureInline]
    list_display = [
        'name',
        'category',
        'sellers_amount',
        'min_price',
        'avg_price',
        'avg_disc_price',
        'sort_index',
        'limited',
        'archived',
    ]
    list_filter = [
        'category',
        'limited',
        'archived',
        admin_filters.MinPriceListFilter,
        admin_filters.AvgPriceListFilter,
    ]
    prepopulated_fields = {
        'slug': ('name',),
    }
    readonly_fields = ['count_sells']
    search_fields = ['name']

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path(
                'product_import-products/',
                ProductImportFormView.as_view(),
                name='import_products',
            ),
        ]
        return new_urls + urls

    @admin.display(description='Sellers')
    def sellers_amount(self, obj: models.Product) -> int:
        return obj.sellers.count()

    @admin.display(description='Min price', empty_value=0)
    def min_price(self, obj: models.Product) -> int:
        return obj.min_price

    @admin.display(description='Avg price', empty_value=0)
    def avg_price(self, obj: models.Product) -> int:
        return obj.average_price

    @admin.display(description='Avg disc price', empty_value=0)
    def avg_disc_price(self, obj: models.Product) -> int:
        return obj.discounted_average_price


@admin.register(models.SellerProduct)
class SellerProductAdminModel(admin.ModelAdmin):
    change_list_template = 'admin/product_change_list.html'
    list_display = ['product', 'seller', 'price']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name='Content-managers').exists():
            return queryset
        else:
            return queryset.filter(seller__profile=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not (request.user.is_superuser or request.user.groups.filter(name='Content-managers').exists()):
            form.base_fields['seller'].widget = forms.HiddenInput()
            form.base_fields['seller'].initial = request.user.seller_set.first()
        return form

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path(
                'product_import-products/',
                ProductImportFormView.as_view(),
                name='import_products',
            ),
        ]
        return new_urls + urls


class SubcategoryInline(admin.TabularInline):
    model = models.Category
    extra = 0
    prepopulated_fields = {
        'slug': ('name',),
    }


@admin.register(models.Category)
class CategoryAdmin(TranslationAdmin):
    list_display = [
        'name',
        'slug',
        'parent_category',
        'is_active',
        'sort_index',
    ]
    prepopulated_fields = {
        'slug': ('name',),
    }
    search_fields = ['name']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_index']
    inlines = [SubcategoryInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent_category":
            kwargs["queryset"] = models.Category.objects.filter(
                parent_category=None,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.ProductImportLog)
class ProductImportLogAdmin(admin.ModelAdmin):
    change_list_template = 'admin/product_import_log_change_list.html'
    list_display = [
        'id',
        'status',
        'items_imported',
        'start',
        'end',
        'file_name',
    ]
    readonly_fields = [
        'status',
        'items_imported',
        'start',
        'end',
        'file_name',
        'message_log',
    ]
    list_display_links = ['id', 'status']
