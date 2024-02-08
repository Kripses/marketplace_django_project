from django.contrib import admin

from catalog.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = 'id', 'author', 'text', 'created_at'
    list_display_links = 'id', 'author'
    ordering = 'pk',
