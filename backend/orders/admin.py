# admin.py
from django.contrib import admin
from .models import Order, OrderItem
from django.db import transaction

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

   