from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify
from ckeditor.fields import RichTextField


def generate_unique_slug(model, value, instance_id=None):
    base_slug = slugify(value) or model._meta.model_name
    slug = base_slug
    counter = 1

    queryset = model.objects.exclude(pk=instance_id)
    while queryset.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1

    return slug


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = RichTextField(blank=True)
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = RichTextField(blank=True)
    image = models.ImageField(
        upload_to='brands/',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Brand, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    class StockStatus(models.TextChoices):
        IN_STOCK = 'in_stock', 'In stock'
        OUT_OF_STOCK = 'out_of_stock', 'Out of stock'
        PREORDER = 'preorder', 'Preorder'

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    short_description = models.TextField(blank=True)
    description = RichTextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name='products',
        blank=True,
        null=True,
    )

    regular_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100')),
        ],
    )

    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    allow_backorder = models.BooleanField(default=False)
    stock_status = models.CharField(
        max_length=20,
        choices=StockStatus.choices,
        default=StockStatus.OUT_OF_STOCK,
    )

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
    )

    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to='products/thumbnails/',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(sale_price__isnull=True) | Q(sale_price__lte=F('regular_price')),
                name='product_sale_price_lte_regular_price',
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.sale_price is not None
            and self.regular_price is not None
            and self.sale_price > self.regular_price
        ):
            errors['sale_price'] = 'Sale price cannot be greater than regular price.'

        if (
            self.stock_quantity == 0
            and self.stock_status == self.StockStatus.IN_STOCK
            and not self.allow_backorder
        ):
            errors['stock_status'] = (
                'A product with no stock cannot be marked as in stock unless '
                'backorders are allowed.'
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Product, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.alt_text or f'Image for {self.product}'
