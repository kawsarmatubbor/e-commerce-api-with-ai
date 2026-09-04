from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.helpers import error, success

from apps.product.models import Product

from .models import Cart, CartItem
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from .services import get_quantity_error


def get_serialized_cart(user):
    cart = Cart.objects.prefetch_related('items__product').get(user=user)
    return CartSerializer(cart).data


def touch_cart(cart):
    cart.save(update_fields=['updated_at'])


class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        Cart.objects.get_or_create(user=request.user)
        return success(
            status_code=200,
            message='Cart retrieved successfully',
            data=get_serialized_cart(request.user),
        )


class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return error(
                status_code=400,
                message='Invalid data',
                errors=serializer.errors,
            )

        with transaction.atomic():
            product = Product.objects.select_for_update().get(
                pk=serializer.validated_data['product'].pk
            )
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart = Cart.objects.select_for_update().get(pk=cart.pk)
            cart_item = CartItem.objects.select_for_update().filter(
                cart=cart,
                product=product,
            ).first()

            quantity = serializer.validated_data['quantity']
            new_quantity = quantity + (cart_item.quantity if cart_item else 0)
            quantity_error = get_quantity_error(product, new_quantity)
            if quantity_error:
                return error(
                    status_code=400,
                    message='Unable to add product to cart',
                    errors={'quantity': [quantity_error]},
                )

            created = cart_item is None
            if created:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=new_quantity,
                )
            else:
                cart_item.quantity = new_quantity
                cart_item.save(update_fields=['quantity', 'updated_at'])
            touch_cart(cart)

        return success(
            status_code=201 if created else 200,
            message='Product added to cart successfully',
            data=get_serialized_cart(request.user),
        )


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return error(
                status_code=400,
                message='Invalid data',
                errors=serializer.errors,
            )

        with transaction.atomic():
            try:
                cart_item = CartItem.objects.select_for_update().select_related(
                    'cart',
                    'product',
                ).get(pk=item_id, cart__user=request.user)
            except CartItem.DoesNotExist:
                return error(status_code=404, message='Cart item not found')

            product = Product.objects.select_for_update().get(
                pk=cart_item.product_id
            )
            quantity = serializer.validated_data['quantity']
            quantity_error = get_quantity_error(product, quantity)
            if quantity_error:
                return error(
                    status_code=400,
                    message='Unable to update cart item',
                    errors={'quantity': [quantity_error]},
                )

            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity', 'updated_at'])
            touch_cart(cart_item.cart)

        return success(
            status_code=200,
            message='Cart item updated successfully',
            data=get_serialized_cart(request.user),
        )

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.select_related('cart').get(
                pk=item_id,
                cart__user=request.user,
            )
        except CartItem.DoesNotExist:
            return error(status_code=404, message='Cart item not found')

        cart = cart_item.cart
        cart_item.delete()
        touch_cart(cart)
        return success(
            status_code=200,
            message='Cart item removed successfully',
            data=get_serialized_cart(request.user),
        )


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        touch_cart(cart)
        return success(
            status_code=200,
            message='Cart cleared successfully',
            data=get_serialized_cart(request.user),
        )

