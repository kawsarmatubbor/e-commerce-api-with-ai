from rest_framework import serializers
from .models import Category, Product

# Category serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "description"]

# Product serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "category", "title", "description", "price", "discount_price", "stock", "sku", "image"]