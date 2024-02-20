from django.http import HttpRequest

session_key: str = 'compare_list_key_slug'
max_list_amt: int = 4


def delete_product_to_compare_list(request: HttpRequest, slug: str) -> None:
    '''убирает товар из списка сравнения'''
    compare_list = request.session.get(session_key, [])
    compare_list.remove(slug)
    request.session[session_key] = compare_list
    return


def get_compare_list(request: HttpRequest, product_amt: int = max_list_amt) -> list[str]:
    '''
    Возвращает список товаров из списка сравнения
    (по умолчанию первые 4 товара)
    '''
    return request.session.get(session_key, [])[:product_amt]


def get_compare_list_amt(request: HttpRequest) -> int:
    '''возвращает количество товаров в списке сравнения'''
    return len(get_compare_list(request))


def add_product_to_compare_list(request: HttpRequest, slug: str) -> None:
    '''добавляет товар в список сравнения'''
    compare_list = request.session.get(session_key, [])
    if slug in compare_list or get_compare_list_amt(request) == max_list_amt:
        return
    compare_list.append(slug)
    request.session[session_key] = compare_list
    return


def delete_all_compare_products(request: HttpRequest) -> None:
    '''удаляет все товары из сравнения'''
    request.session[session_key] = []
    return
