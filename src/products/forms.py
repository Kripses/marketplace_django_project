from django import forms
from django.core.exceptions import ValidationError

from .models import Category


class FilterForm(forms.Form):
    price = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'range-line',
                'id': 'price',
                'type': 'text',
                'data-type': 'double',
                'data-min': '7',
                'data-max': '50',
                'data-from': '7',
                'data-to': '27',
            },
        ),
        required=False,
    )
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-input form-input_full',
                'id': 'title',
                'type': 'text',
                'placeholder': 'Название',
            },
        ),
        required=False,
    )
    in_stock = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'type': 'checkbox',
            },
        ),
        required=False,
    )


class SearchForm(forms.Form):
    query = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'search-input',
                'id': 'query',
                'name': 'query',
                'type': 'text',
                'placeholder': 'NVIDIA GeForce RTX 3060',
            },
        ),
    )


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        models = Category

    def clean(self):
        cleaned_data = super().clean()
        parent_category = cleaned_data.get('parent_category')
        pk = cleaned_data.get('pk')
        if parent_category:
            if parent_category.pk == pk:
                raise ValidationError(
                    "Can't be a subcategory of itself",
                )
            if parent_category.parent_category:
                raise ValidationError(
                    "%(parent)s is a subcategory and can't be a parent",
                    params={'parent': parent_category},
                )
        return cleaned_data


class ProductsImportForm(forms.Form):
    zip_file = forms.FileField(
        widget=forms.FileInput(
            attrs={'accept': 'application/zip'},
        ),
    )
    email = forms.EmailField(required=False)
