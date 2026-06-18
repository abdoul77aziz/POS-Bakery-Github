from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'selling_price', 'stock_quantity', 'low_stock_threshold', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    