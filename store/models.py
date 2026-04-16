from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# -----------------------------------------------------------------------------
# 1. USER MODEL
# -----------------------------------------------------------------------------

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_store_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='store_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='store_user_permissions',
        blank=True
    )

# -----------------------------------------------------------------------------
# 2. INVENTORY MODELS
# -----------------------------------------------------------------------------

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.all()
        return sum(review.rating for review in reviews) / len(reviews) if reviews else 0

    def review_count(self):
        return self.reviews.count()

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')

    class Meta:
        verbose_name_plural = "Product Galleries"

# -----------------------------------------------------------------------------
# 3. SHOPPING CART MODELS
# -----------------------------------------------------------------------------

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def get_total_price(self):
        price = self.product.discount_price if self.product.discount_price else self.product.price
        return price * self.quantity

# -----------------------------------------------------------------------------
# 4. ORDER & PAYMENT MODELS
# -----------------------------------------------------------------------------

class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.city}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    delivery_instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Tracks status changes

    # Payment Tracking
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

# -----------------------------------------------------------------------------
# 5. TRACKING & REVIEWS
# -----------------------------------------------------------------------------

class OrderTracking(models.Model):
    order = models.ForeignKey(Order, related_name='tracking_history', on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order.id} - {self.location}"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"