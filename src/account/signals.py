from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from account.models import Seller


@receiver(post_save, sender=Seller)
def add_seller_to_stuff_group(sender, instance, created, **kwargs):
    """
    Сигнал для добавления новых продавцов в группу Sellers
    и присвоения им статуса is_stuff
    """
    if created:
        seller_group, created = Group.objects.get_or_create(name='Sellers')
        instance.profile.groups.add(seller_group)
        instance.profile.is_staff = True
        instance.profile.save()
