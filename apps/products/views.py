from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


# Category views
class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryDetailView(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category,pk=pk,is_active=True)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# Product views
class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products,many=True,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product,pk=pk,is_active=True)
        serializer = ProductSerializer(product,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)