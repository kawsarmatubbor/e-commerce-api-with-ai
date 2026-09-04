from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'tax_amount']
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = [
        'user_email',
        'total_quantity',
        'subtotal',
        'grand_total',
        'updated_at',
    ]
    search_fields = ['user__email']
    readonly_fields = ['user', 'created_at', 'updated_at']
    fields = readonly_fields
    inlines = [CartItemInline]

    @admin.display(description='User', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related(
            'items__product'
        )

