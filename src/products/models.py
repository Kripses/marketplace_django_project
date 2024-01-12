from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import product_utils
from .validators import validate_not_subcategory


class Tag(models.Model):
    """
    Модель тега продуктов.

    name - Наименование тега;
    slug - Слаг тега.
    """
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.SlugField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:products-by-tag', args=[self.slug])


class ActiveProductsManager(models.Manager):
    """ Менеджер активных(не архивированных) продуктов. """
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Product(models.Model):
    """
    Модель продукта.

    category - связь с категорией, к которой относится товар;
    name - наименование товара;
    slug - слаг товара;
    description - описание товара;
    created_at - дата/время создания записи;
    count_sells - количество проданных единиц товара;
    archived - флаг архивирования (мягкого удаления) товара;
    sort_index - индекс сортировки товара;
    limited - флаг ограниченного количества товара.
    """
    category = models.ForeignKey(
        "Category",
        related_name='products',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200, null=False, blank=False)
    slug = models.SlugField(max_length=200, unique=True, null=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    count_sells = models.IntegerField(default=0)
    archived = models.BooleanField(default=False)
    sort_index = models.IntegerField(default=0)
    limited = models.BooleanField(default=False)

    tags = models.ManyToManyField(
        'Tag',
        related_name='products',
        blank=True
    )

    objects = models.Manager()
    active = ActiveProductsManager()

    class Meta:
        ordering = ['sort_index', 'name']
        indexes = [
            models.Index(fields=['name', 'slug']),
        ]

    def get_absolute_url(self) -> str:
        """ Получение абсолютной ссылки на продукт. """
        return reverse('products:product_details', kwargs={'slug': self.slug})

    @property
    def average_price(self) -> Decimal:
        """ Средняя цена продукта. """
        return product_utils.get_average_price(self)

    @property
    def discounted_average_price(self) -> Decimal:
        """ Средняя цены продукта со скидкой. """
        return product_utils.discounted_average_price(self)

    @property
    def min_price(self) -> Decimal:
        """ Минимальная цена продукта. """
        return product_utils.get_min_price(self)

    @property
    def discounted_min_price(self) -> Decimal:
        """ Минимальная цены продукта со скидкой. """
        return product_utils.get_discounted_min_price(self)

    def __str__(self):
        return f'{self.name}'


@receiver(post_save, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """
    Очистка кеша модели Product при изменении товара в БД.
    """
    cache_key = f'product_details_{instance.pk}'
    cache.delete(cache_key)


def product_images_directory_path(
        instance: "ProductImage",
        filename: str
) -> str:
    """Сгенерировать путь для сохранения изображения продукта."""
    return "products/images/product_{pk}/{filename}".format(
        pk=instance.product.pk,
        filename=filename,
    )


def category_images_directory_path(
        instance: "Category",
        filename: str
) -> str:
    """Сгенерировать путь для сохранения изображения."""
    return "categories/images/category_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


def category_icons_directory_path(
        instance: "Category",
        filename: str
) -> str:
    """Сгенерировать путь для сохранения иконки."""
    return "categories/icons/category_{pk}/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class Picture(models.Model):
    """
    Модель изображения продукта.

    product - связь с продуктом, к которому относится изображение;
    image - файл изображения.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to=product_images_directory_path)


class SellerProduct(models.Model):
    """
    Модель для описпания связи между товарами и продавцами,
    а также количества товаров и цены у каждого продавца в наличии.

    product - связь с продуктами;
    seller - связь с продавцами;
    count - количество товаров в наличии;
    price - цена товара у данного продавца.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )
    seller = models.ForeignKey(
        'account.Seller',
        on_delete=models.CASCADE,
    )
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['seller', 'product']

    def __str__(self):
        return f'{self.product} by {self.seller.name}'


class Category(models.Model):
    """
    Модель категорий товаров.

    name - наименование категории;
    slug - слаг категории;
    is_active - флаг активности (мягкого удаления) категории;
    parent_category - связь с родительской категорией;
    icon - иконка категории;
    sort_index - индекс сортировки категории.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    parent_category = models.ForeignKey(
        'self',
        related_name='subcategories',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        validators=[validate_not_subcategory],
    )
    image = models.ImageField(
        upload_to=category_images_directory_path,
        null=True,
        blank=True,
    )
    icon = models.FileField(
        upload_to=category_icons_directory_path,
        null=True,
        blank=True,
    )
    sort_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_index', 'name']
        indexes = [
            models.Index(fields=['name', 'slug']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        """ Полное наименование категории. """
        if not self.parent_category:
            return self.name

        return f'{self.parent_category.name} / {self.name}'

    def get_absolute_url(self) -> str:
        """ Получение абсолютной ссылки на категорию. """
        return reverse('products:products-by-category', args=[self.slug])


class Property(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_property'
    )
    name = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = 'property'
        verbose_name_plural = 'properties'

    def __str__(self):
        return str(self.name)


class Value(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_property_value'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='category_property_value'
    )
    value = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.value)

