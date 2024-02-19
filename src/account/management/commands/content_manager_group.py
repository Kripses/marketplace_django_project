from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    Команда для создания группы Content-managers
    """
    PERMISSIONS = [
        "view_profile",
        "add_seller",
        "change_seller",
        "delete_seller",
        "add_category",
        "change_category",
        "delete_category",
        "add_product",
        "change_product",
        "delete_product",
        "add_sellerproduct",
        "change_sellerproduct",
        "delete_sellerproduct",
        "add_picture",
        "change_picture",
        "delete_picture",
        "delete_review",
    ]

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(
            name="Content-managers"
        )

        for codename in self.PERMISSIONS:
            permission, created = Permission.objects.get_or_create(
                codename=codename
            )
            group.permissions.add(permission)

        group.save()
