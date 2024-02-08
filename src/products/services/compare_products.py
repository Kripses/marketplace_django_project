from django.http import HttpRequest

from django.core.cache import cache

from ..models import Product


session_key = 'compare_list_key_slug'
max_list_amt = 4


def delete_product_to_compare_list(request, slug):
    '''убирает товар из списка сравнения'''
    compare_list = request.session.get(session_key, [])
    compare_list.remove(slug)
    request.session[session_key] = compare_list
    return


def get_compare_list(request, product_amt=max_list_amt):
    '''
    Возвращает список товаров из списка сравнения
    (по умолчанию первые 4 товара)
    '''
    return request.session.get(session_key, [])[:product_amt]


def get_compare_list_amt(request):
    '''возвращает количество товаров в списке сравнения'''
    return len(get_compare_list(request))


def add_product_to_compare_list(request, slug):
    '''добавляет товар в список сравнения'''
    compare_list = request.session.get(session_key, [])
    if slug in compare_list or get_compare_list_amt(request) == max_list_amt:
        return
    compare_list.append(slug)
    request.session[session_key] = compare_list
    return


def delete_all_compare_products(request):
    request.session[session_key] = []
    return
