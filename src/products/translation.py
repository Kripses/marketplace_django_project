from modeltranslation.translator import register, TranslationOptions

from products.models import Product, Category, Property, Value


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', )


@register(Property)
class PropertyTranslationOptions(TranslationOptions):
    fields = ('name', )


@register(Value)
class ValueTranslationOptions(TranslationOptions):
    fields = ('value', )
