from django.urls import path
from . import views

urlpatterns = [
    # --- Storefront ---
    path('', views.home, name='home'),
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search_view, name='search'),

    # --- Cart & Checkout Flow ---
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    # --- NEW: Manual Payment Route ---
    path('payment/upi/<int:order_id>/', views.manual_payment, name='manual_payment'),

    # --- User Accounts ---
    path('my-orders/', views.my_orders, name='my_orders'),
    path('address-book/', views.address_book, name='address_book'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Admin Dashboard & Fulfillment ---
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('dashboard/print-slip/<int:order_id>/', views.print_order_slip, name='print_slip'),

    # --- Inventory Management ---
    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/products/add/', views.admin_add_product, name='admin_add_product'),
    path('dashboard/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
path('delivery/update/', views.delivery_agent_update, name='delivery_agent_update'),
# Use the trailing slash!
path('delivery/update/', views.delivery_agent_update, name='delivery_agent_update'),
path('order/<int:order_id>/', views.order_detail, name='order_detail'),
]