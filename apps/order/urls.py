from django.urls import path

from .views import CheckoutView, OrderCancelView, OrderDetailView, OrderListView


urlpatterns = [
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/checkout/', CheckoutView.as_view(), name='order-checkout'),
    path(
        'orders/<str:order_number>/',
        OrderDetailView.as_view(),
        name='order-detail',
    ),
    path(
        'orders/<str:order_number>/cancel/',
        OrderCancelView.as_view(),
        name='order-cancel',
    ),
]

