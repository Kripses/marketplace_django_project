from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q

from .forms import SearchForm
from .models import Category
from .services.banners import CacheableContextCategory
from discounts.models import Discount

CATEGORIES_KEY = 'header_menu_categories'


class MenuCategory(CacheableContextCategory):
    def __init__(self, category: Category):
        super().__init__(category)
        self.icon_url = settings.MEDIA_URL + str(
            category.icon,
        ) if category.icon else ''
        self.subcategories = [MenuCategory(subcategory)
                              for subcategory
                              in category.subcategories.filter(
                                  is_active=True
                              ).all()]


def get_active_discounts_count():
    count = 0
    for subclass in Discount.__subclasses__():
        query = subclass.objects.aggregate(
            active_count=Count(
                'active',
                filter=Q(active=True)
            )
        )
        count += query['active_count']
    return count


def header_menu(request):
    menu_categories = cache.get(CATEGORIES_KEY)

    if not menu_categories:
        active_categories = Category.objects.filter(
            is_active=True,
            parent_category=None,
        ).prefetch_related(
            'subcategories',
        ).all()
        menu_categories = [MenuCategory(category)
                           for category in active_categories]

        cache.set(CATEGORIES_KEY, menu_categories)

    active_discounts = get_active_discounts_count()

    return {
        'categories': menu_categories,
        'search_form': SearchForm(),
        'active_discounts': active_discounts,
    }
