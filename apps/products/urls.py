from django.urls import path
from .views import(
    CategoryListView, 
    CategoryDetailView,
    ProductListView,
    ProductDetailView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('products/', ProductListView.as_view(), name='products'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
