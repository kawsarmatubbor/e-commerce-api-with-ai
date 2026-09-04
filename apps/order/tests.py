from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.product.models import Category, Product
from apps.user.models import User

from .models import Order


class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='customer@example.com',
            password='test-password',
            is_active=True,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='test-password',
            is_active=True,
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Wireless Headphones',
            sku='HEADPHONE-001',
            category=self.category,
            regular_price=Decimal('100.00'),
            sale_price=Decimal('80.00'),
            tax_percentage=Decimal('10.00'),
            stock_quantity=5,
            stock_status=Product.StockStatus.IN_STOCK,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )
        self.client.force_authenticate(self.user)

    def checkout(self):
        return self.client.post(
            reverse('order-checkout'),
            {
                'customer_name': 'Test Customer',
                'customer_phone': '+8801700000000',
                'shipping_address': 'Dhaka, Bangladesh',
                'payment_method': Order.PaymentMethod.CASH_ON_DELIVERY,
            },
            format='json',
        )

    def test_checkout_creates_snapshots_reduces_stock_and_clears_cart(self):
        response = self.checkout()

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get()
        order_item = order.items.get()
        self.product.refresh_from_db()
        self.assertTrue(order.order_number.startswith('ORD-'))
        self.assertEqual(order.grand_total, Decimal('176.00'))
        self.assertEqual(order_item.product_name, 'Wireless Headphones')
        self.assertEqual(order_item.unit_price, Decimal('80.00'))
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertFalse(self.cart.items.exists())

    def test_checkout_revalidates_current_stock(self):
        self.product.stock_quantity = 1
        self.product.save(update_fields=['stock_quantity'])

        response = self.checkout()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(self.cart.items.exists())

    def test_order_list_and_detail_are_scoped_to_the_user(self):
        checkout_response = self.checkout()
        order_number = checkout_response.data['data']['order_number']
        Order.objects.create(
            user=self.other_user,
            customer_name='Other',
            customer_email=self.other_user.email,
            customer_phone='123',
            shipping_address='Other address',
            subtotal=Decimal('10.00'),
            grand_total=Decimal('10.00'),
        )

        list_response = self.client.get(reverse('order-list'))
        detail_response = self.client.get(
            reverse('order-detail', args=[order_number])
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data['data']), 1)
        self.assertEqual(detail_response.status_code, 200)

    def test_cancelling_order_restores_stock(self):
        checkout_response = self.checkout()
        order_number = checkout_response.data['data']['order_number']

        response = self.client.post(
            reverse('order-cancel', args=[order_number])
        )

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        order = Order.objects.get(order_number=order_number)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock_quantity, 5)

    def test_shipped_order_cannot_be_cancelled(self):
        checkout_response = self.checkout()
        order = Order.objects.get(
            order_number=checkout_response.data['data']['order_number']
        )
        order.status = Order.Status.SHIPPED
        order.save(update_fields=['status'])

        response = self.client.post(
            reverse('order-cancel', args=[order.order_number])
        )

        self.assertEqual(response.status_code, 400)

    def test_checkout_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.checkout()

        self.assertEqual(response.status_code, 401)

