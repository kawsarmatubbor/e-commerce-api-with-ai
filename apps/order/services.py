from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.cart.models import money
from apps.cart.services import get_quantity_error
from apps.product.models import Product

from .models import Order, OrderItem


class CheckoutError(Exception):
    pass


def create_order_from_cart(user, cart, checkout_data):
    cart_items = list(cart.items.select_related('product'))
    if not cart_items:
        raise CheckoutError('Your cart is empty.')

    products = {
        product.pk: product
        for product in Product.objects.select_for_update().filter(
            pk__in=[item.product_id for item in cart_items]
        )
    }

    prepared_items = []
    subtotal = Decimal('0')
    tax = Decimal('0')

    for cart_item in cart_items:
        product = products.get(cart_item.product_id)
        if not product:
            raise CheckoutError(
                f'{cart_item.product.name} is no longer available.'
            )

        quantity_error = get_quantity_error(product, cart_item.quantity)
        if quantity_error:
            raise CheckoutError(f'{product.name}: {quantity_error}')

        deducted_quantity = min(product.stock_quantity, cart_item.quantity)
        product.stock_quantity -= deducted_quantity
        if product.stock_quantity == 0:
            product.stock_status = (
                Product.StockStatus.PREORDER
                if product.allow_backorder
                else Product.StockStatus.OUT_OF_STOCK
            )
        product.save(update_fields=['stock_quantity', 'stock_status', 'updated_at'])

        prepared_items.append((product, cart_item.quantity, deducted_quantity))
        unit_price = (
            product.sale_price
            if product.sale_price is not None
            else product.regular_price
        )
        item_subtotal = money(unit_price * cart_item.quantity)
        item_tax = money(
            item_subtotal * product.tax_percentage / Decimal('100')
        )
        subtotal += item_subtotal
        tax += item_tax

    subtotal = money(subtotal)
    tax = money(tax)
    shipping_cost = Decimal('0')
    discount_amount = Decimal('0')
    grand_total = money(subtotal + tax + shipping_cost - discount_amount)

    order = Order.objects.create(
        user=user,
        customer_name=checkout_data['customer_name'],
        customer_email=checkout_data.get('customer_email') or user.email,
        customer_phone=checkout_data['customer_phone'],
        shipping_address=checkout_data['shipping_address'],
        payment_method=checkout_data['payment_method'],
        notes=checkout_data.get('notes', ''),
        subtotal=subtotal,
        tax=tax,
        shipping_cost=shipping_cost,
        discount_amount=discount_amount,
        grand_total=grand_total,
    )
    OrderItem.objects.bulk_create([
        OrderItem.from_product(order, product, quantity, deducted_quantity)
        for product, quantity, deducted_quantity in prepared_items
    ])
    cart.items.all().delete()
    cart.save(update_fields=['updated_at'])
    return order


def cancel_order(order):
    if order.status not in {Order.Status.PENDING, Order.Status.CONFIRMED}:
        raise CheckoutError('This order can no longer be cancelled.')

    order_items = list(order.items.all())
    product_ids = [
        item.product_id
        for item in order_items
        if item.product_id and item.stock_deducted_quantity
    ]
    products = {
        product.pk: product
        for product in Product.objects.select_for_update().filter(pk__in=product_ids)
    }

    for item in order_items:
        product = products.get(item.product_id)
        if not product or not item.stock_deducted_quantity:
            continue
        product.stock_quantity += item.stock_deducted_quantity
        if product.stock_quantity > 0:
            product.stock_status = Product.StockStatus.IN_STOCK
        product.save(update_fields=['stock_quantity', 'stock_status', 'updated_at'])

    order.status = Order.Status.CANCELLED
    order.cancelled_at = timezone.now()
    if order.payment_status == Order.PaymentStatus.PAID:
        order.payment_status = Order.PaymentStatus.REFUNDED
    order.save(update_fields=[
        'status',
        'payment_status',
        'cancelled_at',
        'updated_at',
    ])
    return order

