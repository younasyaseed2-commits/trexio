from .models import Category, Cart


def menu_categories(request):
    categories = Category.objects.all()
    return {'menu_categories': categories}


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        # Find the active cart for the logged-in user
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        if cart:
            # Add up the quantity of all items in the cart
            count = sum(item.quantity for item in cart.items.all())

    return {'cart_count': count}