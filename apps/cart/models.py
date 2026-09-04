from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.product.models import Product


MONEY_PLACES = Decimal('0.01')


def money(value):
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return money(sum(
            (item.subtotal for item in self.items.all()),
            Decimal('0'),
        ))

    @property
    def tax(self):
        return money(sum(
            (item.tax_amount for item in self.items.all()),
            Decimal('0'),
        ))

    @property
    def grand_total(self):
        return money(self.subtotal + self.tax)

    def __str__(self):
        return f'Cart for {self.user.email}'


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_product_per_cart',
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name='cart_item_quantity_gte_1',
            ),
        ]

    @property
    def unit_price(self):
        return (
            self.product.sale_price
            if self.product.sale_price is not None
            else self.product.regular_price
        )

    @property
    def subtotal(self):
        return money(self.unit_price * self.quantity)

    @property
    def tax_amount(self):
        return money(
            self.subtotal * self.product.tax_percentage / Decimal('100')
        )

    @property
    def total(self):
        return money(self.subtotal + self.tax_amount)

    def __str__(self):
        return f'{self.product} × {self.quantity}'

