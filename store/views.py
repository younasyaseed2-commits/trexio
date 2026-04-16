"""
TREXIO E-COMMERCE CORE ENGINE - VERSION 2.1
-------------------------------------------------------------------------------
Owner: Younis K. | Location: Vatakara, Kerala
System: Django 6.0.3 | Project: Trexio E-Commerce Solutions
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
    return user.is_authenticated and (user.is_staff or user.is_store_admin)

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
            return redirect('admin_dashboard' if user.is_staff else 'home')
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

def search_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query),
        is_available=True
    ) if query else Product.objects.none()
    return render(request, 'store/home.html', {'products': products, 'category_name': f"Search: '{query}'"})

# -----------------------------------------------------------------------------
# 4. CART & MANUAL UPI GATEWAY
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
            user=request.user, address=get_object_or_404(Address, id=address_id),
            total_price=grand_total, payment_method=request.POST.get('payment_method'),
            delivery_instructions=request.POST.get('instructions')
        )
        for item in items:
            OrderItem.objects.create(order=order, product=item.product,
                                    price=item.product.discount_price or item.product.price,
                                    quantity=item.quantity)
            item.product.stock -= item.quantity
            item.product.save()
        cart.items.all().delete()
        if order.payment_method in ['Online', 'UPI']:
            return redirect('manual_payment', order_id=order.id)
        return redirect('order_success', order_id=order.id)
    return render(request, 'store/cart.html', {'cart': cart, 'items': items, 'grand_total': grand_total, 'addresses': request.user.addresses.all()})

@login_required(login_url='/login/')
def manual_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        order.transaction_id = request.POST.get('utr')
        order.payment_screenshot = request.FILES.get('screenshot')
        order.save()
        messages.success(request, "Proof submitted! We will verify shortly.")
        return redirect('order_success', order_id=order.id)
    return render(request, 'store/pay_upi.html', {'order': order})

@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
            item.save()
        messages.success(request, f"Added {product.name} to cart.")
    return redirect('cart')

# -----------------------------------------------------------------------------
# 5. ADMIN FULFILLMENT & LOGISTICS
# -----------------------------------------------------------------------------

@user_passes_test(is_admin)
def admin_dashboard(request):
    active_orders = Order.objects.exclude(status='Cancelled')
    total_rev = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    context = {
        'total_products': Product.objects.count(), 'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(), 'total_revenue': total_rev,
        'recent_orders': Order.objects.all().order_by('-created_at')[:8],
    }
    return render(request, 'store/admin_dashboard.html', context)

@user_passes_test(is_admin)
def admin_orders(request):
    return render(request, 'store/admin_orders.html', {'orders': Order.objects.all().order_by('-created_at')})

@user_passes_test(is_admin)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status == 'Cancelled' and order.status != 'Cancelled':
            for item in order.items.all():
                item.product.stock += item.quantity
                item.product.save()
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
    return redirect('admin_orders')

@user_passes_test(is_admin)
def print_order_slip(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin_order_slip.html', {'order': order})

# -----------------------------------------------------------------------------
# 6. DELIVERY AGENT MODULE (SECURE QR SCAN)
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
            # If the order was just 'Pending', move it to 'Shipped' automatically
            if order.status == 'Pending':
                order.status = 'Shipped'
                order.save()

            OrderTracking.objects.create(
                order=order,
                location=loc,
                message=f"Arrived at {loc}"
            )
            messages.success(request, f"Tracking updated for {loc}")

        elif action == 'deliver':
            order.status = 'Delivered'
            order.is_paid = True
            order.save()
            OrderTracking.objects.create(order=order, location="Customer", message="Delivered")
            messages.success(request, "Order marked as Delivered!")
            return redirect('delivery_agent_update')

    return render(request, 'store/delivery_update.html', {'order': order})
# -----------------------------------------------------------------------------
# 7. CUSTOMER PORTAL
# -----------------------------------------------------------------------------

@login_required(login_url='/login/')
def order_success(request, order_id):
    return render(request, 'store/order_success.html', {'order': get_object_or_404(Order, id=order_id, user=request.user)})

@login_required(login_url='/login/')
def my_orders(request):
    return render(request, 'store/orders.html', {'orders': Order.objects.filter(user=request.user).order_by('-created_at')})

@login_required(login_url='/login/')
def cancel_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status == 'Pending':
            for item in order.items.all():
                item.product.stock += item.quantity
                item.product.save()
            order.status = 'Cancelled'
            order.save()
            messages.success(request, "Order cancelled.")
    return redirect('my_orders')

@login_required(login_url='/login/')
def address_book(request):
    if request.method == 'POST':
        Address.objects.create(user=request.user, full_name=request.POST.get('full_name'),
            phone_number=request.POST.get('phone_number'), street_address=request.POST.get('street_address'),
            city=request.POST.get('city'), state=request.POST.get('state'), postal_code=request.POST.get('postal_code'))
        messages.success(request, "Address added.")
        return redirect('address_book')
    return render(request, 'store/addresses.html', {'addresses': request.user.addresses.all()})

# -----------------------------------------------------------------------------
# 8. INVENTORY CRUD (STAFF ONLY)
# -----------------------------------------------------------------------------

@user_passes_test(is_admin)
def admin_products(request):
    return render(request, 'store/admin_products.html', {'products': Product.objects.all().order_by('-id')})

@user_passes_test(is_admin)
def admin_add_product(request):
    if request.method == 'POST':
        Product.objects.create(name=request.POST.get('name'),
            category=get_object_or_404(Category, id=request.POST.get('category')),
            description=request.POST.get('description'), price=request.POST.get('price'),
            stock=request.POST.get('stock'), image=request.FILES.get('image'))
        return redirect('admin_products')
    return render(request, 'store/admin_add_product.html', {'categories': Category.objects.all()})

@user_passes_test(is_admin)
def admin_delete_product(request, product_id):
    get_object_or_404(Product, id=product_id).delete()
    return redirect('admin_products')


@login_required(login_url='/login/')
def order_detail(request, order_id):
    # This ensures a customer can ONLY see their own order
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # We pass it as a list [order] so we can reuse the same HTML tracker logic
    return render(request, 'store/order_detail.html', {'order': order})
# END OF TREXIO CORE ENGINE V2.1
# .............................................................................
# .............................................................................
# .............................................................................