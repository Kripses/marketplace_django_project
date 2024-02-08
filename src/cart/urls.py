from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CartView,
    CartApiViewSet,
    SellerApiViewSet,
    CreateOrderView,
    OrderListView,
    OrderDetailView,
)

app_name = "cart"

router = DefaultRouter()
router.register(r'cart', CartApiViewSet, basename='cart_api')
router.register(r'product-seller', SellerApiViewSet, basename='product_seller_api')

urlpatterns = [
    path('', CartView.as_view(), name='cart_view'),
    path('api/', include(router.urls)),
    path('order_list/', OrderListView.as_view(), name='order_list'),
    path('order_detail/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('create_order/', CreateOrderView.as_view(), name='create_order'),
]

