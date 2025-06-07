from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction # For atomic operations like order creation
from .models import CustomUser, UserPaymentMethod, Category, Product, Order, OrderItem, Cart, CartItem

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'password', 'password2')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        # Remove password2 from attrs as it's not part of the User model
        attrs.pop('password2')
        return attrs

    def create(self, validated_data):
        # validated_data already has password2 removed by the validate method
        # phone_number is optional in model, so get() is appropriate
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number')
            # password is not passed directly to create_user
        )
        user.set_password(validated_data['password']) # Set password correctly
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'national_id', 'address', 'postal_code', 'is_identity_verified')
        read_only_fields = ('email', 'id', 'is_identity_verified') # Email typically not changed, identity verified by admin

# UserPaymentMethod Serializer (Basic)
class UserPaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPaymentMethod
        fields = ('id', 'card_holder_name', 'card_number_last_four', 'card_expiry_date', 'is_verified')
        read_only_fields = ('is_verified',) # Verified by admin

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'parent')

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True) # Nested serializer for read-only category details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, allow_null=True
    ) # For writing category by ID

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'stock', 'image', 'features', 'available', 'category', 'category_id', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'category')

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True) # Renamed to avoid conflict if 'product' is also writable
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, help_text="Price at the time of order")

    class Meta:
        model = OrderItem
        fields = ('id', 'product_id', 'product_detail', 'quantity', 'price') # product_id for write, product_detail for read

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user_detail = UserProfileSerializer(source='user', read_only=True) # Renamed for clarity

    class Meta:
        model = Order
        fields = ('id', 'user_detail', 'items', 'total_paid', 'status', 'billing_address', 'shipping_address', 'payment_verified', 'transaction_id', 'created_at', 'updated_at')
        read_only_fields = ('user_detail', 'total_paid', 'status', 'payment_verified', 'transaction_id', 'created_at', 'updated_at')

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        billing_address = validated_data.get('billing_address', user.address or "N/A")
        shipping_address = validated_data.get('shipping_address', user.address or "N/A")

        # Create order instance first without items
        order = Order.objects.create(user=user, billing_address=billing_address, shipping_address=shipping_address,
                                     status=Order.STATUS_PENDING) # Explicitly set status, other fields have defaults or are read-only here

        total_order_price = 0
        order_items_to_create = []

        for item_data in items_data:
            product_instance = item_data['product'] # This is the Product instance from product_id
            quantity = item_data['quantity']

            if product_instance.stock < quantity:
                raise serializers.ValidationError(f"Not enough stock for {product_instance.name}. Available: {product_instance.stock}")

            order_items_to_create.append(OrderItem(
                order=order,
                product=product_instance,
                price=product_instance.price,
                quantity=quantity
            ))
            total_order_price += (product_instance.price * quantity)

            product_instance.stock -= quantity
            # Defer saving product_instance until all items are validated to avoid partial stock updates on error

        # Bulk create order items
        OrderItem.objects.bulk_create(order_items_to_create)

        # Save all product stock changes
        for item_data in items_data:
            item_data['product'].save(update_fields=['stock'])

        order.total_paid = total_order_price
        order.save() # Save the final order details
        return order


# --- Cart and CartItem Serializers ---

class ProductLiteSerializer(serializers.ModelSerializer):
    """A lightweight product serializer for use in cart items."""
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'image')

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductLiteSerializer(source='product', read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True) # Removed redundant source

    class Meta:
        model = CartItem
        fields = ('id', 'product_id', 'product_detail', 'quantity', 'subtotal', 'added_at')
        read_only_fields = ('id', 'added_at')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be a positive integer."))
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    total_items = serializers.IntegerField(read_only=True) # Removed redundant source
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True) # Removed redundant source

    class Meta:
        model = Cart
        fields = (
            'id',
            'user',
            'user_email',
            'session_key',
            'items',
            'total_items',
            'total_price',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'id',
            'user',
            'session_key',
            'total_items',
            'total_price',
            'created_at',
            'updated_at'
        )
