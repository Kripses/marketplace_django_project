from django.contrib import admin

from cart.models import Order, Cart

from . import models


@admin.register(models.Cart)
class PropertyValueAdmin(admin.ModelAdmin):

    list_display = [
        'product_seller',
        'count',
    ]


# class OrderInLine(admin.TabularInline):
#     model = Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = 'profile', 'fio', 'phone', 'email', \
                   'city', 'delivery_address', 'delivery_type', \
                   'payment_type', 'comment', 'archived', 'created_at'
    ordering = 'created_at',
    # inlines = [
    #         OrderInLine,
    #     ]

    # def get_queryset(self, request):
    #     return Order.objects.select_related("cart")
