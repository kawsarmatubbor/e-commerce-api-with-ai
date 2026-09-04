from rest_framework import serializers

from .models import Order, OrderItem


class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=30)
    shipping_address = serializers.CharField()
    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices,
        default=Order.PaymentMethod.CASH_ON_DELIVERY,
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_name',
            'product_sku',
            'quantity',
            'unit_price',
            'tax_percentage',
            'subtotal',
            'tax_amount',
            'total',
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'payment_status',
            'payment_method',
            'customer_name',
            'customer_email',
            'customer_phone',
            'shipping_address',
            'notes',
            'items',
            'subtotal',
            'tax',
            'shipping_cost',
            'discount_amount',
            'grand_total',
            'cancelled_at',
            'created_at',
            'updated_at',
        ]

