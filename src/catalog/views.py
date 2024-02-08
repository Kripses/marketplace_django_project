from django.shortcuts import render

from django.http import HttpRequest

from .forms import ReviewForm
from .services import add_review, get_count_review, get_reviews_list


def add_to_comparison(request, product_id):
    # добавить продукт для сравнения
    return None

def remove_from_comparison(request, product_id):
    # удалить продукт из сравнения
    return None

def comparison_list(request):
    # список сравниваемых продуктов
    return None

def comparison_count(request):
    # количество товаров в списке сравнения
    return None