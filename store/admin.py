from django.contrib import admin
from .models import User, Category, Product, ProductGallery, Cart, CartItem, Address

# 1. Setup the Gallery to show up inside the Product page
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 3 # Shows 3 empty upload boxes by default

# 2. Attach the Gallery to the Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_available')
    inlines = [ProductGalleryInline] # This injects the gallery!

# Register your models
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin) # Use the custom admin
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Address)
# Change your import line at the top to look like this:
from .models import User, Category, Product, ProductGallery, Cart, CartItem, Address, Order, OrderItem

# ... (Keep your existing admin code here) ...

# Add these two lines at the very bottom:
admin.site.register(Order)
admin.site.register(OrderItem)