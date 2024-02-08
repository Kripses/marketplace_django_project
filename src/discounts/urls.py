from django.urls import path

from .views import DiscountsListView
from products.views import CatalogView

app_name = "discounts"

urlpatterns = [
    path(
        '<slug:sale>',
        CatalogView.as_view(),
        name='products-on-sale'
    ),
    path('', DiscountsListView.as_view(), name='discounts_list'),
]

