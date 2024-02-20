import json

from django.http import HttpResponse, HttpRequest

from payments.services.payment_service import get_payment_status

from cart.models import Order


def payment_webhook_view(request: HttpRequest) -> HttpResponse:
    '''вебхук для получения статуса заказа'''
    if request.method == 'GET':
        return HttpResponse(status=404)
    if request.method == 'POST':
        response = json.loads(request.body)

        if response['object']['status'] != 'succeeded':
            return HttpResponse(status=400)

        if response['object']['status'] == 'canceled':
            return HttpResponse(status=200)

        order = Order.objects.get(payment_id=response['object']['id'])
        get_payment_status(order)
        return HttpResponse(status=200)
