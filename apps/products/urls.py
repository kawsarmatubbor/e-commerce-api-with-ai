from django.urls import path
from .views import CategoryView, CategoryDetailView

urlpatterns = [
    path('categories/', CategoryView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]
