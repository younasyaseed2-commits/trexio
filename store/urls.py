from django.urls import path
from . import views

urlpatterns = [
    # Main Store Pages
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Storefront Feature URLs
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Customer Account URLs
    path('addresses/', views.address_book, name='address_book'),
    path('orders/', views.my_orders, name='my_orders'),

    # This is the line that fixes the error!
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    # ... (Keep your existing URLs) ...

    # Admin & Store Management URLs
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
# Customer Account URLs
    path('addresses/', views.address_book, name='address_book'),
    path('orders/', views.my_orders, name='my_orders'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    # Admin Product Management
    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/add/', views.admin_add_product, name='admin_add_product'),
    # Add this line specifically
    path('admin-panel/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    # <-- ADD THIS LINE
]