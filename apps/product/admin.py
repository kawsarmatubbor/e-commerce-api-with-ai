from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from .models import Brand, Category, Product, ProductImage


class ProductImageInline(StackedInline):
    model = ProductImage
    fields = ['image', 'alt_text', 'sort_order']
    extra = 1
    ordering = ['sort_order', 'id']


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'description', 'image', 'is_active']


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'description', 'image', 'is_active']


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        'name',
        'sku',
        'category',
        'regular_price',
        'stock_quantity',
        'stock_status',
        'is_active',
    ]
    list_filter = [
        'category',
        'brand',
        'stock_status',
        'is_featured',
        'is_new_arrival',
        'is_active',
        'created_at',
    ]
    search_fields = ['name', 'sku', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['category', 'brand']
    inlines = [ProductImageInline]
    fieldsets = (
        ('Basic information', {
            'fields': (
                'name', 'slug', 'sku', 'category', 'brand',
                'short_description', 'description', 'thumbnail',
            ),
        }),
        ('Pricing', {
            'fields': (
                'regular_price', 'sale_price', 'cost_price', 'tax_percentage',
            ),
        }),
        ('Inventory', {
            'fields': (
                'stock_quantity', 'low_stock_threshold',
                'allow_backorder', 'stock_status',
            ),
        }),
        ('Shipping dimensions', {
            'fields': ('weight', 'length', 'width', 'height'),
        }),
        ('Visibility', {
            'fields': ('is_featured', 'is_new_arrival', 'is_active'),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand')
