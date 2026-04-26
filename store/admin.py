from django.contrib import admin
from .models import (
    User, Category, Product, ProductGallery,
    Cart, CartItem, Address, Order, OrderItem, OrderTracking
)

# 1. INLINES (Used inside other pages)
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# 2. CUSTOM ADMIN CLASSES
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'is_available']
    list_editable = ['price', 'stock', 'is_available']
    inlines = [ProductGalleryInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'address__full_name']
    list_editable = ['status']
    inlines = [OrderItemInline]

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'location', 'created_at']
    list_filter = ['created_at']

# 3. SIMPLE REGISTRATIONS
# Note: Do NOT manually register Order, Product, or OrderTracking here
# because we used @admin.register above.
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Address)
admin.site.register(OrderItem)