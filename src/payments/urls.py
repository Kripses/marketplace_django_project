from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from payments.views import payment_webhook_view

app_name = "payments"

urlpatterns = [
    path('notification_url/', csrf_exempt(payment_webhook_view), name='payment_webhook')
]
