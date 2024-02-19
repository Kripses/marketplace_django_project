from django.contrib import admin

from cart.models import Order, Cart


@admin.register(Cart)
class PropertyValueAdmin(admin.ModelAdmin):

    list_display = [
        'product_seller',
        'count',
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = 'profile', 'fio', 'phone', 'email', \
                   'city', 'delivery_address', 'delivery_type', \
                   'payment_type', 'comment', 'archived', 'created_at'
    ordering = 'created_at',

    def __str__(self):
        return f"Заказ № {self.id}"
