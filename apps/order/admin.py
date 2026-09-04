from django import forms
from django.contrib import admin
from django.db import transaction
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem
from .services import cancel_order


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'


class OrderItemInline(TabularInline):
    model = OrderItem
    fields = [
        'product_name',
        'product_sku',
        'quantity',
        'unit_price',
        'tax_amount',
        'total',
    ]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    form = OrderAdminForm
    list_display = [
        'order_number',
        'customer_name',
        'grand_total',
        'status',
        'payment_status',
        'created_at',
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = [
        'order_number',
        'customer_name',
        'customer_email',
        'customer_phone',
        'user__email',
    ]
    readonly_fields = [
        'order_number',
        'user',
        'subtotal',
        'tax',
        'shipping_cost',
        'discount_amount',
        'grand_total',
        'cancelled_at',
        'created_at',
        'updated_at',
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order', {
            'fields': (
                'order_number', 'user', 'status',
                'payment_status', 'payment_method',
            ),
        }),
        ('Customer and delivery', {
            'fields': (
                'customer_name', 'customer_email', 'customer_phone',
                'shipping_address', 'notes',
            ),
        }),
        ('Totals', {
            'fields': (
                'subtotal', 'tax', 'shipping_cost',
                'discount_amount', 'grand_total',
            ),
        }),
        ('Dates', {
            'fields': ('cancelled_at', 'created_at', 'updated_at'),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            previous = Order.objects.select_for_update().get(pk=obj.pk)
            if (
                obj.status == Order.Status.CANCELLED
                and previous.status != Order.Status.CANCELLED
            ):
                cancel_order(previous)
                obj.cancelled_at = previous.cancelled_at
                obj.payment_status = previous.payment_status
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

