from django import forms

from django.core.exceptions import ValidationError

from . import models


class DiscountAdminForm(forms.ModelForm):
    class Meta:
        models = models.Discount

    def clean(self):
        cleaned_data = super().clean()
        msg = None
        discount_type = cleaned_data.get('discount_type')
        value = cleaned_data.get('value')
        min_value = models.Discount.MIN_VALUE
        if discount_type and value:
            if discount_type == models.DiscountTypeEnum.PERCENTAGE:
                if not 1 <= value <= 100:
                    msg = 'Discount value must be from 1 to 100 %'
            elif value < min_value:
                if discount_type == models.DiscountTypeEnum.FIXED_VALUE:
                    msg = f'Discount value can\'t be less than {min_value}'
                else:
                    msg = f'New price can\'t be less that {min_value}'
            if msg:
                raise ValidationError({'value': msg})

        return cleaned_data


class ComboDiscountAdminForm(DiscountAdminForm):
    class Meta:
        models = models.ComboDiscount

    def clean(self):
        cleaned_data = super().clean()
        set_1 = cleaned_data.get('set_1')
        set_2 = cleaned_data.get('set_2')

        if (set_1 and set_2) and (set_1 == set_2):
            msg = 'Sets 1 and 2 can\'t be thee same set'
            raise ValidationError({'set_1': msg})

        return cleaned_data
