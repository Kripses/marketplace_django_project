from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Profile, Seller

# admin.site.register(Profile, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'address', 'archived')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'address')
    fieldsets = (
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'address', 'archived')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )


class SellerInLine(admin.TabularInline):
    model = Seller.products.through


@admin.action(description="Archive seller")
def mark_archived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=True)


@admin.action(description="Unarchive seller")
def mark_unarchived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=False)


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    actions = [
        mark_archived,
        mark_unarchived,
    ]
    inlines = [
        SellerInLine,
    ]
    list_display = 'id', 'user_verbose', 'description'
    list_display_links = 'id', 'user_verbose'
    ordering = 'pk',
    search_fields = 'user_verbose',

    def get_queryset(self, request):
        return Seller.objects.select_related("profile")

    def user_verbose(self, obj: Seller) -> str:
        return obj.name
