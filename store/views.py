from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail

# Make sure Review is imported!
from .models import User, Product, Category, Cart, CartItem, Address, Order, OrderItem, Review


# --- HELPER FUNCTIONS ---
def is_admin(user):
    return user.is_authenticated and (user.is_store_admin or user.is_superuser)


# --- STOREFRONT VIEWS ---
def home(request):
    products = Product.objects.filter(is_available=True)
    context = {'products': products}
    return render(request, 'store/home.html', context)


def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, is_available=True)
    context = {'products': products, 'category_name': category.name}
    return render(request, 'store/home.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


def search_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_available=True
        )

    context = {
        'products': products,
        'category_name': f"Search results for '{query}'" if query else "Please enter a search term.",
    }
    return render(request, 'store/home.html', context)


@login_required(login_url='/login/')
def submit_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        # Create or update the review
        Review.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating, 'review_text': review_text}
        )

        messages.success(request, 'Thank you! Your review has been submitted.')
        return redirect('product_detail', product_id=product.id)

    return redirect('home')


# --- CART & CHECKOUT VIEWS ---
@login_required(login_url='/login/')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    items = cart.items.all()
    grand_total = sum(item.get_total_price() for item in items)
    addresses = request.user.addresses.all()

    if request.method == 'POST':
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        instructions = request.POST.get('instructions')

        if not address_id:
            messages.error(request, "Please select a delivery address!")
            return redirect('cart')

        selected_address = get_object_or_404(Address, id=address_id)

        # 1. Create the Order FIRST so the variable exists
        order = Order.objects.create(
            user=request.user,
            address=selected_address,
            total_price=grand_total,
            payment_method=payment_method,
            delivery_instructions=instructions
        )

        # 2. Add items to the order
        for item in items:
            purchase_price = item.product.discount_price if item.product.discount_price else item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=purchase_price,
                quantity=item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()

        # 3. Send Email Notification
        subject = f"🎉 New Order Received! #TRX-00{order.id}"
        message = f"""
        Hello Trexio Admin,

        You just received a new order!

        Customer: {request.user.username}
        Total Amount: ₹{grand_total}
        Payment Method: {payment_method}

        Log in to your Admin Dashboard to process this order.
        """

        send_mail(
            subject,
            message,
            'system@trexio.com',
            ['owner@trexio.com'],
            fail_silently=True,  # Changed to True to prevent crashes if email fails locally
        )

        # 4. Empty the cart
        cart.items.all().delete()

        return redirect('order_success', order_id=order.id)

    context = {
        'cart': cart,
        'items': items,
        'grand_total': grand_total,
        'addresses': addresses
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not item_created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, f"{product.name} was added to your cart!")
        return redirect('cart')

    return redirect('home')


# --- ORDER VIEWS ---
@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})


@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})


@login_required(login_url='/login/')
def cancel_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status == 'Pending':
            order.status = 'Cancelled'
            order.save()

            for item in order.items.all():
                item.product.stock += item.quantity
                item.product.save()

            messages.success(request, f"Order #TRX-00{order.id} has been successfully cancelled.")
        else:
            messages.error(request, f"Sorry, you cannot cancel an order that is already {order.status}.")

    return redirect('my_orders')


# --- ADDRESS BOOK VIEW ---
@login_required(login_url='/login/')
def address_book(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone_number')
        street = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone,
            street_address=street,
            city=city,
            state=state,
            postal_code=postal_code,
            is_default=True
        )
        messages.success(request, "Delivery address saved successfully!")
        return redirect('address_book')

    addresses = request.user.addresses.all()
    return render(request, 'store/addresses.html', {'addresses': addresses})


# --- AUTHENTICATION VIEWS ---
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

        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('login')

    return render(request, 'store/register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        p_word = request.POST.get('password')

        user = authenticate(request, username=email, password=p_word)

        if user is not None:
            login(request, user)
            if user.is_store_admin or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# --- ADMIN VIEWS ---
@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
    }
    return render(request, 'store/admin_dashboard.html', context)


@user_passes_test(is_admin, login_url='/login/')
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'store/admin_orders.html', {'orders': orders})


@user_passes_test(is_admin, login_url='/login/')
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        order.status = new_status
        order.save()

        messages.success(request, f"Order #{order.id} has been marked as '{new_status}'.")
    return redirect('admin_orders')


# --- ADMIN VIEWS ---
@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.count()

    # Get the 5 most recent orders for a quick preview
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/admin_dashboard.html', context)
# --- ADMIN PRODUCT MANAGEMENT ---
@user_passes_test(is_admin, login_url='/login/')
def admin_products(request):
    products = Product.objects.all().order_by('-created_date')
    return render(request, 'store/admin_products.html', {'products': products})

@user_passes_test(is_admin, login_url='/login/')
def admin_add_product(request):
    if request.method == 'POST':
        # Get data from the form
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        stock = request.POST.get('stock')
        image = request.FILES.get('image') # Handle file uploads

        category = get_object_or_404(Category, id=category_id)

        # Create the product
        Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            discount_price=discount_price if discount_price else None,
            stock=stock,
            image=image
        )
        messages.success(request, f"Product '{name}' added successfully!")
        return redirect('admin_products')

    categories = Category.objects.all()
    return render(request, 'store/admin_add_product.html', {'categories': categories})


from django.db.models import Sum
from django.db.models.functions import TruncDate


@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.count()

    # Calculate Total Revenue (Money Made)
    total_revenue = Order.objects.exclude(status='Cancelled').aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Get Sales Data for Chart (Last 7 Days)
    sales_data = Order.objects.exclude(status='Cancelled') \
                     .annotate(date=TruncDate('created_at')) \
                     .values('date') \
                     .annotate(daily_revenue=Sum('total_price')) \
                     .order_by('date')[:7]

    # Prepare labels (dates) and data (amounts) for the JavaScript Chart
    chart_labels = [item['date'].strftime('%d %b') for item in sales_data]
    chart_revenue = [float(item['daily_revenue']) for item in sales_data]

    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
    }
    return render(request, 'store/admin_dashboard.html', context)
@user_passes_test(is_admin, login_url='/login/')
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f"Product '{product_name}' was deleted successfully.")
    return redirect('admin_products')