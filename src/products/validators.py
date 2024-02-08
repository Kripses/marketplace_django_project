from django.core.exceptions import ValidationError

from . import models


def validate_not_subcategory(value):
    try:
        parent = models.Category.objects.filter(pk=value).get()
        if parent.parent_category:
            raise ValidationError(
                "%(parent)s is a subcategory and can't be a parent",
                params={'parent': parent},
            )
    except models.Category.DoesNotExist:
        raise ValidationError(
            '%Category %(value)s does not exist',
            params={'value': value},
        )
