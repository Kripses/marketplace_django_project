from django.urls import path
from .views import get_admin_settings

urlpatterns = [
    path('get_admin_settings', get_admin_settings, name='get_admin_settings'),
]
