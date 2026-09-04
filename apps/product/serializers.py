from rest_framework import serializers

from .models import Brand, Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'image']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'sku',
            'short_description',
            'description',
            'category',
            'brand',
            'regular_price',
            'sale_price',
            'tax_percentage',
            'stock_quantity',
            'allow_backorder',
            'stock_status',
            'weight',
            'length',
            'width',
            'height',
            'is_featured',
            'is_new_arrival',
            'meta_title',
            'meta_description',
            'thumbnail',
            'images',
            'created_at',
            'updated_at',
        ]
