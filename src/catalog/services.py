from django.utils.translation import ngettext

from account.models import Profile
from catalog.models import Review
from products.models import Product


def get_reviews_list(pk: int):
    """
    Сервис получения списка отзывов на товар.

    Args:
        pk (int): уникальный код товара.
    """
    return Review.objects.filter(product=pk)


def add_review(*args, **kwargs):
    """
    Сервис добавления отзывов к товару.

    Returns:
        context: параметны для отрисовки шаблона, содержит:
            - review_template: название шаблона добавления отзыва к товару для имрорта в шаблон страницы товара;
            - form: форма для добавления отзыва.
    """

    Review.objects.create(
        text=kwargs['text'],
        author=Profile.objects.get(pk=kwargs['user_id']),
        product=Product.objects.get(slug=kwargs['slug']),
    )

    context = {
        'review_template': 'catalog/review.jinja2',
    }
    return context


def get_count_review(pk: int) -> tuple:
    """
    Функция для определения количества отзывов на товар.

    Args:
        pk (int): уникальный код товара.

    return:
        result (tuple) - количество отзывов на товар.
    """
    count_review = len(Review.objects.filter(product=pk))
    review = ngettext(
        "review",
        "reviews",
        count_review
    )
    return count_review, f'{count_review} {review}'
