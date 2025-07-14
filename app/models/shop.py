from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Model, CharField, TextField, DecimalField, BooleanField, DateTimeField, ForeignKey, \
    PositiveIntegerField, PROTECT, CASCADE, PositiveBigIntegerField, OneToOneField, SET_NULL, SmallIntegerField
from django.utils.text import slugify

from app.models.users import User

from app.models.base import TimeBaseModel



class Category(TimeBaseModel):
    name = CharField(max_length=50, unique=True)
    description = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Color(Model):
    name = CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Size(Model):
    SIZE_TYPES = (
        ('CL', 'Clothing'),
        ('SH', 'Shoes'),
        ('AC', 'Accessories'),
    )
    name = CharField(max_length=20)
    size_type = CharField(max_length=2, choices=SIZE_TYPES, default='CL')

    class Meta:
        unique_together = ('name', 'size_type')

    def __str__(self):
        return f"{self.name} ({self.get_size_type_display()})"



class Product(TimeBaseModel):
    name = CharField(max_length=255)
    category = ForeignKey('Category', on_delete=PROTECT)
    seller = ForeignKey(User, on_delete=CASCADE, related_name='products')
    description = TextField()
    discount = SmallIntegerField(default=0)
    is_active = BooleanField(default=True)


    def __str__(self):
        return self.name



class ProductItem(TimeBaseModel):
    product = ForeignKey(Product, on_delete=CASCADE, related_name='variants')
    sku = CharField(max_length=50, unique=True, editable=False)
    stock_quantity = PositiveIntegerField()
    is_available = BooleanField(default=True)
    actual_price = PositiveBigIntegerField()
    color = ForeignKey('Color', on_delete=PROTECT, null=True, blank=True)
    size = ForeignKey('Size', on_delete=PROTECT, null=True, blank=True)

    @property
    def current_price(self):
        return self.actual_price * (self.product.discount)/100


    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):  # noqa
        product_name_slug = slugify(self.product.name, allow_unicode=True)
        color_slug = slugify(self.color.name, allow_unicode=True) if self.color else 'no-color'
        self.sku = f"{product_name_slug}-{color_slug.upper()}"
        while self.__class__.objects.filter(sku=self.sku).exists():
            self.sku += '-1'

        super().save(force_insert, force_update, using, update_fields)


    def __str__(self):
        return f"{self.product.name} - {self.sku}"





class Favorites(TimeBaseModel):
    user = ForeignKey(User, on_delete=CASCADE,
                             related_name='favorites')
    product = ForeignKey(Product, on_delete=CASCADE)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}'s favorite: {self.product}"

