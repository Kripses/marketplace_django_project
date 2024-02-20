from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetView
from django.urls import path, reverse_lazy
from account.views import (
    HistoryOrderView,
    ProfileUpdateView,
    RegisterView,
    SellerDetailView,
    UserAccountView,
    UserBrowsingHistoryView,
    UserLoginView,
    UserLogoutView,
)

app_name = 'account'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('password-reset/',
         PasswordResetView.as_view(
            template_name="registration/password_reset_form.jinja2",
            email_template_name="registration/password_reset_email.jinja2",
            success_url=reverse_lazy('account:password_reset_done')
         ), name='password_reset'),
    path('password-reset/done/',
         PasswordResetDoneView.as_view(template_name="registration/password_reset_done.jinja2"), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.jinja2",
            success_url=reverse_lazy('account:login')
         ), name='password_reset_confirm'),
    path('password-reset/complite/', PasswordResetCompleteView.as_view(), name='password_reset_confirm'),
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
]
