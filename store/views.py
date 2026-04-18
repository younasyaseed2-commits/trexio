"""
TREXIO E-COMMERCE CORE ENGINE - VERSION 2.2
-------------------------------------------------------------------------------
Updates: Integrated 'Packed' status logic, Enhanced Agent Security,
         Optimized Single Order View, and Automated Status Transitions.
-------------------------------------------------------------------------------
"""
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate

# Database Model Imports
from .models import (
    User, Product, Category, Cart, CartItem,
    Address, Order, OrderItem, Review, OrderTracking
)

# -----------------------------------------------------------------------------
# 1. SECURITY & PERMISSIONS HELPERS
# -----------------------------------------------------------------------------

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_agent(user):
    # Expanded to allow staff or specific store admins in Vatakara/Kuttiadi
    return user.is_authenticated and (user.is_staff or getattr(user, 'is_store_admin', False))

# -----------------------------------------------------------------------------
# 2. AUTHENTICATION MODULE
# -----------------------------------------------------------------------------

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        p_word = request.POST.get('password')
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register')
        user = User.objects.create_user(username=email, email=email, password=p_word)
        user.phone_number = phone
        user.is_customer = True
        user.save()
        messages.success(request, "Registration successful! Please sign in.")
        return redirect('login')
    return render(request, 'store/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        p_word = request.POST.get('password')
        user = authenticate(request, username=email, password=p_word)
        if user is not None:
            login(request, user)
            # Redirect staff to dashboard, agents to scanner, others home
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('home')
        messages.error(request, "Invalid credentials. Please try again.")
    return render(request, 'store/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been safely logged out.")
    return redirect('home')

# -----------------------------------------------------------------------------
# 3. STOREFRONT & DISCOVERY
# -----------------------------------------------------------------------------

def home(request):
    products = Product.objects.filter(is_available=True).order_by('-id')
    return render(request, 'store/home.html', {'products': products})

def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, is_available=True)
    return render(request, 'store/home.html', {'products': products, 'category_name': category.name})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

# -----------------------------------------------------------------------------
# 4. CART & ORDERING
# -----------------------------------------------------------------------------

@login_required(login_url='/login/')
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
    items = cart.items.all()
    grand_total = sum(item.get_total_price() for item in items)

    if request.method == 'POST':
        address_id = request.POST.get('address')
        if not address_id:
            messages.error(request, "A delivery address is required.")
            return redirect('cart')

        order = Order.objects.create(
            user=request.user,
            address=get_object_or_404(Address, id=address_id),
            total_price=grand_total,
            payment_method=request.POST.get('payment_method'),
            status='Pending' # Default status
        )

        for item in items:
            OrderItem.objects.create(
                order=order, product=item.product,
                price=item.product.discount_price or item.product.price,
                quantity=item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()

        if order.payment_method in ['Online', 'UPI']:
            return redirect('manual_payment', order_id=order.id)
        return redirect('order_success', order_id=order.id)

    return render(request, 'store/cart.html', {
        'cart': cart, 'items': items,
        'grand_total': grand_total,
        'addresses': request.user.addresses.all()
    })

# -----------------------------------------------------------------------------
# 5. DELIVERY AGENT MODULE (SMART LOGISTICS)
# -----------------------------------------------------------------------------

@user_passes_test(is_agent, login_url='/login/')
def delivery_agent_update(request):
    order_id = request.GET.get('order_id')
    order = None

    if order_id:
        order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST' and order:
        action = request.POST.get('action')
        loc = request.POST.get('current_location')

        if action == 'update_location':
            # AUTO-STATUS LOGIC:
            # If agent marks as 'Warehouse', order is 'Packed'
            # If agent marks as 'Hub' or 'Out for delivery', order is 'Shipped'
            if loc == "Warehouse":
                order.status = 'Packed'
            else:
                order.status = 'Shipped'

            order.save()

            OrderTracking.objects.create(
                order=order,
                location=loc,
                message=f"Status: {order.status} - Location: {loc}"
            )
            messages.success(request, f"Trexio Tracking Updated: {loc}")

        elif action == 'deliver':
            order.status = 'Delivered'
            order.is_paid = True
            order.save()
            OrderTracking.objects.create(order=order, location="Customer", message="Package Delivered")
            messages.success(request, f"Order #TRX-{order.id} Delivered!")
            return redirect('delivery_agent_update')

    return render(request, 'store/delivery_update.html', {'order': order})

# -----------------------------------------------------------------------------
# 6. CUSTOMER PORTAL & TRACKING
# -----------------------------------------------------------------------------

@login_required(login_url='/login/')
def my_orders(request):
    # Returns all orders for the 'See all' view
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})

@login_required(login_url='/login/')
def order_detail(request, order_id):
    # Returns ONLY ONE specific order for the Amazon-style tracking view
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/orders.html', {'orders': [order], 'is_single_view': True})

@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

# -----------------------------------------------------------------------------
# 7. ADMIN & INVENTORY MANAGEMENT
# -----------------------------------------------------------------------------

@user_passes_test(is_admin)
def admin_dashboard(request):
    active_orders = Order.objects.exclude(status='Cancelled')
    total_rev = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    context = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': total_rev,
        'recent_orders': Order.objects.all().order_by('-created_at')[:8],
    }
    return render(request, 'store/admin_dashboard.html', context)

@user_passes_test(is_admin)
def admin_orders(request):
    return render(request, 'store/admin_orders.html', {'orders': Order.objects.all().order_by('-created_at')})

@user_passes_test(is_admin)
def admin_products(request):
    return render(request, 'store/admin_products.html', {'products': Product.objects.all().order_by('-id')})

# END OF TREXIO CORE ENGINE V2.2