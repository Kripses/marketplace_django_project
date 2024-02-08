import logging

import phonenumbers as phonenumbers
from django import forms

from .models import Order
# import phonenumbers


class CreateOrderForm(forms.ModelForm):
    cart = forms.JSONField(widget=forms.Textarea(attrs={'hidden': True}))
    profile = forms.CharField(widget=forms.Textarea(attrs={'hidden': True}))
    phone = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = Order
        fields = (
            'profile',
            'fio',
            'cart',
            'phone',
            'email',
            'city',
            'delivery_address',
            'delivery_type',
            'payment_type',
            'comment',
            'status',
            'total_price',
        )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        z = phonenumbers.parse(phone, "SG")
        if not phonenumbers.is_valid_number(z):
            raise forms.ValidationError("Number not in successful format")
        return z.national_number
