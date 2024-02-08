from typing import List, Any

from discounts.models import (
    BulkDiscount,
    CategoryDiscount,
    ComboDiscount,
    ProductDiscount
)


def get_all_current_discounts() -> List[Any]:
    discounts = []

    discounts.extend(ProductDiscount.current.all())

    discounts.extend(CategoryDiscount.current.all())

    discounts.extend(BulkDiscount.current.all())

    discounts.extend(ComboDiscount.current.all())

    discounts.sort(key=lambda x: x.end)

    return discounts
