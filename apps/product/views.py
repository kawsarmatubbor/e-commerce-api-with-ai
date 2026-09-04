from django.db.models import Q
from rest_framework.views import APIView

from utils.helpers import error, success

from .models import Brand, Category, Product
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return success(
            status_code=200,
            message='Categories retrieved successfully',
            data=serializer.data,
        )


class BrandListView(APIView):
    def get(self, request):
        brands = Brand.objects.filter(is_active=True)
        serializer = BrandSerializer(brands, many=True)
        return success(
            status_code=200,
            message='Brands retrieved successfully',
            data=serializer.data,
        )


class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related(
            'category',
            'brand',
        ).prefetch_related('images')

        category = request.query_params.get('category')
        brand = request.query_params.get('brand')
        search = request.query_params.get('search')

        if category:
            products = products.filter(category__slug=category)
        if brand:
            products = products.filter(brand__slug=brand)
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        if request.query_params.get('featured') == 'true':
            products = products.filter(is_featured=True)
        if request.query_params.get('new_arrival') == 'true':
            products = products.filter(is_new_arrival=True)

        serializer = ProductSerializer(products, many=True)
        return success(
            status_code=200,
            message='Products retrieved successfully',
            data=serializer.data,
        )


class ProductDetailView(APIView):
    def get(self, request, slug):
        try:
            product = Product.objects.select_related(
                'category',
                'brand',
            ).prefetch_related('images').get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return error(status_code=404, message='Product not found')

        serializer = ProductSerializer(product)
        return success(
            status_code=200,
            message='Product retrieved successfully',
            data=serializer.data,
        )

