from django.contrib.auth.views import LoginView
from django.urls import path
from .views import (
    HistoryOrderView,
    ProfileUpdateView,
    RegisterView,
    SellerDetailView,
    UserAccountView,
    UserBrowsingHistoryView,
    UserEmailView,
    UserLoginView,
    UserLogoutView,
    # password_change,
    # ChangePasswordView,
)

app_name = 'account'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('e-mail/', UserEmailView.as_view(), name='e-mail'),
    path(
        "seller/<int:pk>/",
        SellerDetailView.as_view(),
        name="seller_details",
    ),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('historyorder/', HistoryOrderView.as_view(), name='historyorder'),
    path(
        'browsing-history',
        UserBrowsingHistoryView.as_view(),
        name='browsing_history',
    ),
    path('account/', UserAccountView.as_view(), name='account'),
    # path('password_change/', password_change, name='password_change'),
    # path('password_change/', ChangePasswordView.as_view(),
    #      name='password_change'),
]