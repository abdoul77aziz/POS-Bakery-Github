from django.contrib import admin
from .models import Order, OrderLine

class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'created_at', 'total_amount', 'payment_mode')
    list_filter = ('payment_mode', 'created_at')
    inlines = [OrderLineInline]
    