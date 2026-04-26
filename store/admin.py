from django.contrib import admin
from .models import (
    User, Category, Product, ProductGallery,
    Cart, CartItem, Address, Order, OrderItem
)
from .models import OrderTracking
from django.contrib import admin
from .models import Order, OrderItem, OrderTracking

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # This makes the admin look professional
    list_display = ['id', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'address__full_name']
    list_editable = ['status'] # Change status directly from the list!
    inlines = [OrderItemInline]

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'location', 'created_at']

# 1. Setup the Gallery to show up inside the Product page
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# 2. Custom Product Admin (Removed the problematic 'slug' and 'list_display' fields)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductGalleryInline]
    # We only show 'name' and 'price' to be safe, as these are standard
    list_display = ['name', 'price']

# 3. Setup Order Items to show up inside the Order page
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

# --- Register your models ---

admin.site.register(User)
admin.site.register(Category)

# IMPORTANT: We register Product with our custom ProductAdmin class
admin.site.register(Product, ProductAdmin)

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Address)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)