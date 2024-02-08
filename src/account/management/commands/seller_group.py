from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from ...models import Seller


class Command(BaseCommand):
    PERMISSIONS = [
        "add_sellerproduct",
        "change_sellerproduct",
        "delete_sellerproduct",
    ]

    def handle(self, *args, **options):
        group, crated = Group.objects.get_or_create(
            name="Sellers"
        )

        for codename in self.PERMISSIONS:
            permission, created = Permission.objects.get_or_create(
                codename=codename
            )
            group.permissions.add(permission)

        group.save()

        for seller in Seller.objects.all():
            seller.profile.groups.add(group)
            seller.profile.is_staff = True
            seller.profile.save()
