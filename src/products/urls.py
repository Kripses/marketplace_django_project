from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (
    CatalogView,
    ProductDetailsView,
    ProductsCompareView,
    delete_all_compare_products_view,
    delete_product_to_compare_list_view,
    get_compare_list_amt_view,
    add_product_to_compare_list_view,
)

app_name = "products"

routers = DefaultRouter()

urlpatterns = [
    # path("products/", ProductsListView, name="products_list"),
    # path("<str:slug>/", ProductDetailsView.as_view(), name="product_details"),
    path('compare/', ProductsCompareView.as_view(), name='product_compare'),
    path('compare/delete_all/', delete_all_compare_products_view, name='delete_all_compare_products'),
    path('compare/delete/<str:slug>/', delete_product_to_compare_list_view, name='delete_product_to_compare_list'),
    path('compare/amt/', get_compare_list_amt_view, name='compare_amt'),
    path('compare/add/<str:slug>/', add_product_to_compare_list_view, name='add_product_to compare_list'),
    path('api/', include(routers.urls)),
    path('t/<slug:tag>', CatalogView.as_view(), name='products-by-tag'),
    path(
        'category/<slug:category>',
        CatalogView.as_view(),
        name='products-by-category'
    ),
    path(
        'sale/<slug:sale>',
        CatalogView.as_view(),
        name='products-on-sale'
    ),
    path("<slug:slug>/", ProductDetailsView.as_view(), name="product_details"),
    path('', CatalogView.as_view(), name='catalog'),
]

