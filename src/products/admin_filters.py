from enum import Enum

from django.contrib import admin
from django.db.models import Avg, Min, Count


class Prices(Enum):
    FIFTY = '< $50'
    ONE_HUNDRED = '< $100'
    ONE_THOUSAND = '< $1,000'
    FIVE_THOUSAND = '< $5,000'
    TEN_THOUSAND = '< $10,000'


lookups = [
    (Prices.FIFTY, Prices.FIFTY.value),
    (Prices.ONE_HUNDRED, Prices.ONE_HUNDRED.value),
    (Prices.ONE_THOUSAND, Prices.ONE_THOUSAND.value),
    (Prices.FIVE_THOUSAND, Prices.FIVE_THOUSAND.value),
    (Prices.TEN_THOUSAND, Prices.TEN_THOUSAND.value),
]


class MinPriceListFilter(admin.SimpleListFilter):
    title = 'Min price'
    parameter_name = 'min_price'

    def lookups(self, request, model_admin):
        return lookups

    def queryset(self, request, queryset):
        qs = queryset.annotate(
                min=Min('sellerproduct__price')
            )

        if self.value() == str(Prices.FIFTY):
            return qs.filter(min__lte=50)
        if self.value() == str(Prices.ONE_HUNDRED):
            return qs.filter(min__lte=100)
        if self.value() == str(Prices.ONE_THOUSAND):
            return qs.filter(min__lte=1000)
        if self.value() == str(Prices.FIVE_THOUSAND):
            return qs.filter(min__lte=5000)
        if self.value() == str(Prices.TEN_THOUSAND):
            return qs.filter(min__lte=10000)


class AvgPriceListFilter(admin.SimpleListFilter):
    title = 'Avg price'
    parameter_name = 'avg_price'

    def lookups(self, request, model_admin):
        return lookups

    def queryset(self, request, queryset):
        qs = queryset.annotate(
                avg=Avg('sellerproduct__price')
            )

        if self.value() == str(Prices.FIFTY):
            return qs.filter(avg__lte=50)
        if self.value() == str(Prices.ONE_HUNDRED):
            return qs.filter(avg__lte=100)
        if self.value() == str(Prices.ONE_THOUSAND):
            return qs.filter(avg__lte=1000)
        if self.value() == str(Prices.FIVE_THOUSAND):
            return qs.filter(avg__lte=5000)
        if self.value() == str(Prices.TEN_THOUSAND):
            return qs.filter(avg__lte=10000)
