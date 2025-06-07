import uuid # For UUIDField
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)

    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    national_id = models.CharField(_('national ID'), max_length=10, unique=True, blank=True, null=True)
    address = models.TextField(_('address'), blank=True, null=True)
    postal_code = models.CharField(_('postal code'), max_length=10, blank=True, null=True)
    is_identity_verified = models.BooleanField(_('identity verified'), default=False, help_text=_('Designates whether the user identity has been verified.'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # first_name and last_name are already in AbstractUser

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserPaymentMethod(models.Model):
    user = models.ForeignKey(CustomUser, related_name='payment_methods', on_delete=models.CASCADE)
    card_holder_name = models.CharField(_('card holder name'), max_length=255)
    # In a real application, never store raw card numbers.
    # Store only a part of it (e.g., last 4 digits) or use a payment gateway's tokenization.
    # For this example, we'll store a hashed version for demonstration, though this is NOT PCI compliant.
    # A better approach for card_number_masked or similar would be preferred.
    card_number_last_four = models.CharField(_('card number last four digits'), max_length=4, blank=True) # Storing only last 4
    card_expiry_date = models.CharField(_('card expiry date'), max_length=7, help_text=_('Format: MM/YYYY')) # e.g., 02/2025
    # Storing CVV is NOT recommended and is against PCI DSS compliance.
    # cvv_hashed = models.CharField(max_length=255, blank=True, null=True) # Example if you were to (incorrectly) store it
    is_verified = models.BooleanField(_('payment method verified'), default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - **** **** **** {self.card_number_last_four}"

    class Meta:
        verbose_name = _('user payment method')
        verbose_name_plural = _('user payment methods')
        unique_together = [['user', 'card_number_last_four', 'card_expiry_date']] # Example to prevent duplicate entries of same "masked" card


# Make sure these imports are present if not already at the top of the file
# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.conf import settings # For AUTH_USER_MODEL if needed in a model

class Category(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    slug = models.SlugField(_('slug'), max_length=200, unique=True, help_text=_('Unique URL-friendly identifier for the category.'))
    description = models.TextField(_('description'), blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_('parent category'))
    # Add other fields if necessary, e.g., image for category

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        # To prevent a category from being its own parent, additional validation might be needed in save method.
        # For unique slug, ensure it's enforced.

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, verbose_name=_('category'))
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True, help_text=_('Unique URL-friendly identifier for the product.'))
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_('stock'))
    # Pillow needs to be installed for ImageField to work
    image = models.ImageField(_('image'), upload_to='products/%Y/%m/%d/', blank=True, null=True)
    features = models.JSONField(_('features'), blank=True, null=True, help_text=_('Product-specific features, e.g., {"color": "Red", "size": "L"}'))
    available = models.BooleanField(_('available'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at'] # Default ordering

    def __str__(self):
        return self.name


# Ensure necessary imports are present
from django.conf import settings # For AUTH_USER_MODEL
# from django.db import models
# from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_READY_FOR_SHIPMENT = 'READY_FOR_SHIPMENT'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_READY_FOR_SHIPMENT, _('Ready for Shipment')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_DELIVERED, _('Delivered')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name=_('user'))
    # Consider on_delete=models.SET_NULL for user if orders should be kept even if user is deleted, but adjust related logic.

    billing_address = models.TextField(_('billing address'))
    shipping_address = models.TextField(_('shipping address'))
    # For more structured addresses, consider a separate Address model or using a library like django-address.

    total_paid = models.DecimalField(_('total paid'), max_digits=10, decimal_places=2, default=0.00) # Ensure default is set
    status = models.CharField(
        _('status'),
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    payment_verified = models.BooleanField(_('payment verified'), default=False)
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name=_('order'))
    product = models.ForeignKey('Product', related_name='order_items', on_delete=models.PROTECT, verbose_name=_('product'))
    # Using PROTECT to prevent product deletion if it's part of an order.
    # Consider SET_NULL if products can be removed and order items should reflect that (e.g. product no longer available).
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, help_text=_('Price at the time of order'))
    quantity = models.PositiveIntegerField(_('quantity'), default=1)

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        # unique_together = ('order', 'product') # Ensure a product is not added twice to the same order; sum quantities instead.

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"

    def get_cost(self):
        return self.price * self.quantity


# Cart Model
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_('Cart ID'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        verbose_name=_('user')
    )
    session_key = models.CharField(_('session key'), max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"Cart {self.id} for user {self.user.email}"
        return f"Guest Cart {self.id} (Session: {self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

# CartItem Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_('cart'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items', verbose_name=_('product'))
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    added_at = models.DateTimeField(_('added at'), auto_now_add=True) # Useful for tracking when item was added

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ('cart', 'product') # Prevent duplicate product entries for the same cart; update quantity instead.
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in cart {self.cart.id}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity
