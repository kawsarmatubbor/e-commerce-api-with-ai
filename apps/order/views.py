from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.helpers import error, success

from apps.cart.models import Cart

from .models import Order
from .serializers import CheckoutSerializer, OrderSerializer
from .services import CheckoutError, cancel_order, create_order_from_cart


def order_queryset():
    return Order.objects.select_related('user').prefetch_related('items')


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error(
                status_code=400,
                message='Invalid checkout data',
                errors=serializer.errors,
            )

        with transaction.atomic():
            try:
                cart = Cart.objects.select_for_update().get(user=request.user)
                order = create_order_from_cart(
                    request.user,
                    cart,
                    serializer.validated_data,
                )
            except Cart.DoesNotExist:
                return error(status_code=400, message='Your cart is empty.')
            except CheckoutError as checkout_error:
                return error(status_code=400, message=str(checkout_error))

        order = order_queryset().get(pk=order.pk)
        return success(
            status_code=201,
            message='Order placed successfully',
            data=OrderSerializer(order).data,
        )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = order_queryset().filter(user=request.user)
        return success(
            status_code=200,
            message='Orders retrieved successfully',
            data=OrderSerializer(orders, many=True).data,
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = order_queryset().get(
                order_number=order_number,
                user=request.user,
            )
        except Order.DoesNotExist:
            return error(status_code=404, message='Order not found')

        return success(
            status_code=200,
            message='Order retrieved successfully',
            data=OrderSerializer(order).data,
        )


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        with transaction.atomic():
            try:
                order = order_queryset().select_for_update().get(
                    order_number=order_number,
                    user=request.user,
                )
            except Order.DoesNotExist:
                return error(status_code=404, message='Order not found')

            try:
                cancel_order(order)
            except CheckoutError as checkout_error:
                return error(status_code=400, message=str(checkout_error))

        order = order_queryset().get(pk=order.pk)
        return success(
            status_code=200,
            message='Order cancelled successfully',
            data=OrderSerializer(order).data,
        )

