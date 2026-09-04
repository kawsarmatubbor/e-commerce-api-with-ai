from rest_framework import serializers

from apps.product.models import Product

from .models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'sku',
            'thumbnail',
            'regular_price',
            'sale_price',
            'tax_percentage',
            'stock_quantity',
            'stock_status',
            'allow_backorder',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )
    tax_amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )
    total = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'quantity',
            'unit_price',
            'subtotal',
            'tax_amount',
            'total',
            'created_at',
            'updated_at',
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )
    tax = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )
    grand_total = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'total_quantity',
            'subtotal',
            'tax',
            'grand_total',
            'created_at',
            'updated_at',
        ]


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

