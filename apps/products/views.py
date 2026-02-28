from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Category
from .serializers import CategorySerializer


# Category views
class CategoryView(APIView):
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryDetailView(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category,pk=pk,is_active=True)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)