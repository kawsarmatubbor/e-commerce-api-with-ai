from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from ckeditor.fields import RichTextField

from apps.product.models import Brand, Category, Product, ProductImage


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
        self.brand = Brand.objects.create(name='Acme')

    def make_product(self, **overrides):
        data = {
            'name': 'Wireless Headphones',
            'sku': 'HEADPHONE-001',
            'category': self.category,
            'brand': self.brand,
            'regular_price': Decimal('100.00'),
            'stock_quantity': 10,
            'stock_status': Product.StockStatus.IN_STOCK,
        }
        data.update(overrides)
        return Product(**data)

    def test_slug_is_generated_and_made_unique(self):
        first = self.make_product()
        first.save()
        second = self.make_product(sku='HEADPHONE-002')
        second.save()

        self.assertEqual(first.slug, 'wireless-headphones')
        self.assertEqual(second.slug, 'wireless-headphones-1')

    def test_category_and_brand_content_fields_are_optional(self):
        for model in (Category, Brand):
            with self.subTest(model=model.__name__):
                self.assertTrue(model._meta.get_field('description').blank)
                self.assertTrue(model._meta.get_field('image').blank)
                self.assertIsInstance(
                    model._meta.get_field('description'),
                    RichTextField,
                )

    def test_only_main_product_description_uses_ckeditor(self):
        self.assertIsInstance(
            Product._meta.get_field('description'),
            RichTextField,
        )
        self.assertNotIsInstance(
            Product._meta.get_field('short_description'),
            RichTextField,
        )
        self.assertNotIsInstance(
            Product._meta.get_field('meta_description'),
            RichTextField,
        )

    def test_sale_price_cannot_exceed_regular_price(self):
        product = self.make_product(sale_price=Decimal('101.00'))

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn('sale_price', context.exception.message_dict)

    def test_zero_stock_cannot_be_in_stock_without_backorders(self):
        product = self.make_product(
            stock_quantity=0,
            stock_status=Product.StockStatus.IN_STOCK,
            allow_backorder=False,
        )

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn('stock_status', context.exception.message_dict)


class ProductAPITests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
        self.brand = Brand.objects.create(name='Acme')
        self.product = Product.objects.create(
            name='Wireless Headphones',
            sku='HEADPHONE-001',
            category=self.category,
            brand=self.brand,
            regular_price=Decimal('100.00'),
            cost_price=Decimal('60.00'),
            stock_quantity=10,
            stock_status=Product.StockStatus.IN_STOCK,
            is_featured=True,
        )
        ProductImage.objects.create(
            product=self.product,
            image='products/images/headphones.jpg',
            alt_text='Wireless headphones',
        )
        Product.objects.create(
            name='Hidden Product',
            sku='HIDDEN-001',
            category=self.category,
            regular_price=Decimal('50.00'),
            is_active=False,
        )

    def test_product_list_returns_active_products_and_hides_cost_price(self):
        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, 200)
        products = response.json()['data']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['slug'], self.product.slug)
        self.assertNotIn('cost_price', products[0])
        self.assertEqual(len(products[0]['images']), 1)

    def test_product_list_can_be_filtered(self):
        response = self.client.get(
            reverse('product-list'),
            {'category': self.category.slug, 'featured': 'true'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']), 1)

    def test_category_and_brand_api_include_content_fields(self):
        category_response = self.client.get(reverse('category-list'))
        brand_response = self.client.get(reverse('brand-list'))

        self.assertEqual(category_response.status_code, 200)
        self.assertEqual(brand_response.status_code, 200)
        self.assertIn('description', category_response.json()['data'][0])
        self.assertIn('image', category_response.json()['data'][0])
        self.assertIn('description', brand_response.json()['data'][0])
        self.assertIn('image', brand_response.json()['data'][0])

    def test_inactive_product_detail_returns_not_found(self):
        hidden_product = Product.objects.get(sku='HIDDEN-001')

        response = self.client.get(
            reverse('product-detail', args=[hidden_product.slug])
        )

        self.assertEqual(response.status_code, 404)
