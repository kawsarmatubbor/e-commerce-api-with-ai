from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.product.models import Category, Product
from apps.user.models import User

from .models import CartItem


class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='customer@example.com',
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
        self.client.force_authenticate(self.user)

    def add_product(self, quantity=1):
        return self.client.post(
            reverse('cart-item-create'),
            {'product_id': self.product.pk, 'quantity': quantity},
            format='json',
        )

    def test_cart_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('cart-detail'))

        self.assertEqual(response.status_code, 401)

    def test_get_cart_creates_an_empty_cart(self):
        response = self.client.get(reverse('cart-detail'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['items'], [])
        self.assertEqual(response.data['data']['grand_total'], '0.00')

    def test_add_product_calculates_totals(self):
        response = self.add_product(quantity=2)

        self.assertEqual(response.status_code, 201)
        data = response.data['data']
        self.assertEqual(data['total_quantity'], 2)
        self.assertEqual(data['subtotal'], '160.00')
        self.assertEqual(data['tax'], '16.00')
        self.assertEqual(data['grand_total'], '176.00')

    def test_adding_the_same_product_merges_quantity(self):
        self.add_product(quantity=1)

        response = self.add_product(quantity=2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(response.data['data']['items'][0]['quantity'], 3)

    def test_stock_limit_is_enforced(self):
        response = self.add_product(quantity=6)

        self.assertEqual(response.status_code, 400)
        self.assertIn('quantity', response.data['errors'])

    def test_backorders_can_exceed_stock(self):
        self.product.allow_backorder = True
        self.product.stock_status = Product.StockStatus.PREORDER
        self.product.save(update_fields=['allow_backorder', 'stock_status'])

        response = self.add_product(quantity=10)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['total_quantity'], 10)

    def test_update_remove_and_clear_cart_items(self):
        add_response = self.add_product(quantity=1)
        item_id = add_response.data['data']['items'][0]['id']

        update_response = self.client.patch(
            reverse('cart-item-detail', args=[item_id]),
            {'quantity': 3},
            format='json',
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data['data']['total_quantity'], 3)

        remove_response = self.client.delete(
            reverse('cart-item-detail', args=[item_id])
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual(remove_response.data['data']['items'], [])

        self.add_product(quantity=1)
        clear_response = self.client.delete(reverse('cart-clear'))
        self.assertEqual(clear_response.status_code, 200)
        self.assertEqual(clear_response.data['data']['items'], [])

