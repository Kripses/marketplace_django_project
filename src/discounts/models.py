from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from products.models import Category, Product


class CurrentDiscountsManager(models.Manager):
    """ Менеджер актуальных скидок. """
    def get_queryset(self):
        return super().get_queryset().filter(active=True, end__gte=now())


def discount_images_directory_path(
        instance: "Category",
        filename: str
) -> str:
    """Сгенерировать путь для сохранения изображения."""
    return "discounts/images/category_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class DiscountTypeEnum(models.TextChoices):
    """ Перечисление типов скидки. """
    PERCENTAGE = 'PRCNT', 'Percentage'
    FIXED_VALUE = 'FXVAL', 'Fixed value'
    SET_PRICE = 'PRC', 'Set price'


class Discount(models.Model):
    """ Базовая модель скидки. """
    MIN_VALUE = 0.01

    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField()
    active = models.BooleanField(default=True)
    weight = models.IntegerField(default=0)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(max_length=100)

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountTypeEnum.choices,
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)

    image = models.ImageField(
        upload_to=discount_images_directory_path,
        null=True,
        blank=True,
    )

    objects = models.Manager()
    current = CurrentDiscountsManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['slug'])
        ]

    def get_absolute_url(self):
        return reverse(
            'discounts:products-on-sale',
            kwargs={'sale': self.slug},
        )

    def __str__(self):
        return self.name


class ProductDiscount(Discount):
    """ Модель скидки на продукт. """
    products = models.ManyToManyField(
        Product,
        related_name='product_discounts',
    )

    class Meta:
        verbose_name = _('Product discount')
        verbose_name_plural = _('Product discounts')


class CategoryDiscount(Discount):
    """ Модель скидки на котегорию. """
    categories = models.ManyToManyField(
        Category,
        related_name='category_discounts',
    )

    class Meta:
        verbose_name = _('Category discount')
        verbose_name_plural = _('Category discounts')


class BulkDiscount(Discount):
    """ Модель оптовой скидки. """
    product_amount = models.PositiveIntegerField()
    total_sum = models.DecimalField(max_digits=10, decimal_places=2)
    only_unique = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Bulk discount')
        verbose_name_plural = _('Bulk discounts')

    def get_absolute_url(self):
        return reverse('products:catalog')


class ComboSet(models.Model):
    """ Модель списка товаров для набора. """
    name = models.CharField(max_length=50, null=True, blank=True)
    products = models.ManyToManyField(
        Product,
        related_name='combo_discounts',
        blank=True,
    )
    categories = models.ManyToManyField(
        Category,
        related_name='combo_discounts',
        blank=True,
    )

    class Meta:
        verbose_name = _('Combo set')
        verbose_name_plural = _('Combo sets')

    def __str__(self):
        return f'Combo set {self.name}' if self.name else f'Combo set #{self.pk}'


class ComboDiscount(Discount):
    """ Модель скидки на набор товаров. """
    set_1 = models.ForeignKey(
        ComboSet,
        on_delete=models.CASCADE,
        related_name='discounts_1',
    )
    set_2 = models.ForeignKey(
        ComboSet,
        on_delete=models.CASCADE,
        related_name='discounts_2',
    )

    class Meta:
        verbose_name = _('Combo discount')
        verbose_name_plural = _('Combo discounts')
