# admin.py
from django.contrib import admin
from .models import Order, OrderItem, CanceledOrderFeedback
from django.db import transaction

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'unit_price', 'quantity']
    can_delete = False

class CanceledOrderFeedbackInline(admin.StackedInline):
    model = CanceledOrderFeedback
    extra = 0
    readonly_fields = ['order', 'reason', 'other_description', 'created_at']
    can_delete = False
    max_num = 1
    min_num = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at', 'has_feedback']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'user__email', 'shipping_full_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline, CanceledOrderFeedbackInline]
    
    def has_feedback(self, obj):
        """Check if order has feedback"""
        return hasattr(obj, 'canceled_feedback')
    has_feedback.boolean = True
    has_feedback.short_description = 'Has Feedback'

@admin.register(CanceledOrderFeedback)
class CanceledOrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'reason', 'created_at', 'has_description']
    list_filter = ['reason', 'created_at']
    search_fields = ['order__id', 'other_description']
    readonly_fields = ['order', 'reason', 'other_description', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_description(self, obj):
        """Check if feedback has description"""
        return bool(obj.other_description)
    has_description.boolean = True
    has_description.short_description = 'Has Description'
    
    def has_add_permission(self, request):
        """Disable adding feedback from admin (only via API)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make feedback read-only in admin"""
        return False

   