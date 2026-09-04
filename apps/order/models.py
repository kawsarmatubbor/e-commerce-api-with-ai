from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.cart.models import money
from apps.product.models import Product


def generate_order_number():
    while True:
        order_number = f'ORD-{uuid4().hex[:12].upper()}'
        if not Order.objects.filter(order_number=order_number).exists():
            return order_number


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = 'cash_on_delivery', 'Cash on delivery'
        BANK_TRANSFER = 'bank_transfer', 'Bank transfer'

    ALLOWED_STATUS_TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.PROCESSING, Status.CANCELLED},
        Status.PROCESSING: {Status.SHIPPED},
        Status.SHIPPED: {Status.DELIVERED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    order_number = models.CharField(max_length=30, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH_ON_DELIVERY,
    )

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=20, decimal_places=2)
    tax = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    shipping_cost = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0'),
    )
    discount_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0'),
    )
    grand_total = models.DecimalField(max_digits=20, decimal_places=2)

    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if not self.pk:
            return

        previous_status = type(self).objects.filter(pk=self.pk).values_list(
            'status',
            flat=True,
        ).first()
        if not previous_status or previous_status == self.status:
            return

        allowed_statuses = self.ALLOWED_STATUS_TRANSITIONS.get(
            previous_status,
            set(),
        )
        if self.status not in allowed_statuses:
            raise ValidationError({
                'status': (
                    f'Order status cannot change from {previous_status} '
                    f'to {self.status}.'
                )
            })

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name='order_items',
        blank=True,
        null=True,
    )
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    subtotal = models.DecimalField(max_digits=20, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=20, decimal_places=2)
    total = models.DecimalField(max_digits=20, decimal_places=2)
    stock_deducted_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    @classmethod
    def from_product(cls, order, product, quantity, stock_deducted_quantity):
        unit_price = (
            product.sale_price
            if product.sale_price is not None
            else product.regular_price
        )
        subtotal = money(unit_price * quantity)
        tax_amount = money(
            subtotal * product.tax_percentage / Decimal('100')
        )
        return cls(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            quantity=quantity,
            unit_price=unit_price,
            tax_percentage=product.tax_percentage,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=money(subtotal + tax_amount),
            stock_deducted_quantity=stock_deducted_quantity,
        )

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

