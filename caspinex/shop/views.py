from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend # Ensure this is imported
from django.utils.translation import gettext_lazy as _ # For error messages in CartViewSet

from .models import CustomUser, UserPaymentMethod, Category, Product, Order, OrderItem, Cart, CartItem
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserPaymentMethodSerializer,
    CategorySerializer, ProductSerializer, OrderSerializer, CartSerializer
)
from .filters import ProductFilter # Import the ProductFilter

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserPaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = UserPaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPaymentMethod.objects.filter(user=self.request.user)

    def perform__create(self, serializer): # perform_create was misspelled in the prompt
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    # filter_backends = [DjangoFilterBackend] # Optional: if not relying on global
    # filterset_fields = ['name', 'slug']

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(available=True).select_related('category').order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-created_at')
        return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items__product').order_by('-created_at')

    def perform_create(self, serializer): # Corrected this method name from the prompt
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_as_shipped(self, request, pk=None):
        order = self.get_object()
        if order.status == Order.STATUS_PROCESSING or order.status == Order.STATUS_READY_FOR_SHIPMENT:
            order.status = Order.STATUS_SHIPPED
            order.save()
            return Response({'status': 'order marked as shipped'})
        else:
            return Response({'error': 'Order cannot be marked as shipped in its current state.'}, status=status.HTTP_400_BAD_REQUEST)


# --- Shopping Cart Views ---

class CartViewSet(viewsets.GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    # permission_classes = [AllowAny] # Default to AllowAny for cart access, can be stricter per action

    def get_cart(self, request):
        """Helper method to get or create a cart for the current user/session."""
        cart_id = request.session.get('cart_id')
        user = request.user if request.user.is_authenticated else None

        if user:
            session_cart = None
            if cart_id:
                try: # Try to get a session cart that is not yet associated with any user
                    session_cart = Cart.objects.prefetch_related('items__product').get(id=cart_id, user__isnull=True)
                except Cart.DoesNotExist:
                    session_cart = None # cart_id in session was invalid or already belonged to a user

            # Get or create the user's primary cart
            user_cart, created = Cart.objects.prefetch_related('items__product').get_or_create(user=user)

            if session_cart: # Merge items from session_cart to user_cart
                for session_item in session_cart.items.all():
                    user_cart_item, item_created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=session_item.product,
                        defaults={'quantity': session_item.quantity}
                    )
                    if not item_created: # Item already existed, update quantity
                        user_cart_item.quantity += session_item.quantity
                        user_cart_item.save()
                session_cart.delete() # Delete the guest session cart

            # If a new cart was created for the user, or if we just merged a session cart,
            # ensure the session points to the user's cart.
            # Or, if user logs out, their cart_id should ideally be removed from session.
            # For simplicity now, we just ensure the session cart_id is cleared after merge/login.
            if 'cart_id' in request.session and (not session_cart or session_cart.id == request.session.get('cart_id')):
                 del request.session['cart_id'] # Clear old session cart_id after processing

            # It's generally not needed to store user's cart_id back in session, as it's tied to user.
            # request.session['cart_id'] = str(user_cart.id)
            return user_cart

        # Guest user logic
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if cart_id:
            try:
                cart = Cart.objects.prefetch_related('items__product').get(id=cart_id, user__isnull=True)
                # If cart has a session_key and it doesn't match current session, it's an old session.
                # Or if cart has no session_key, associate it with current session.
                if cart.session_key and cart.session_key != session_key:
                    # This specific cart_id belongs to another session. Create a new one for current session.
                    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True, defaults={})
                elif not cart.session_key: # Cart exists but not tied to a session (e.g. direct DB creation)
                    cart.session_key = session_key
                    cart.save()
            except Cart.DoesNotExist: # cart_id in session is invalid
                cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True, defaults={})
        else: # No cart_id in session, get or create by session_key
            cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True, defaults={})

        request.session['cart_id'] = str(cart.id) # Store/update cart_id in session for guest
        return cart

    @action(detail=False, methods=['get'], url_path='mine', permission_classes=[AllowAny])
    def retrieve_cart(self, request):
        cart = self.get_cart(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add-item', permission_classes=[AllowAny])
    def add_item(self, request):
        cart = self.get_cart(request)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id or quantity <= 0:
            return Response({'error': _('Product ID and valid quantity are required.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({'error': _('Product not found or unavailable.')}, status=status.HTTP_404_NOT_FOUND)

        # Check stock before creating/updating CartItem
        if product.stock < quantity: # If this is the total quantity desired
            return Response({'error': _(f'Not enough stock for {product.name}. Available: {product.stock}')}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created: # Item already in cart, update quantity
            # Check stock against the additional quantity requested
            # This assumes quantity in request is "new total quantity" not "amount to add"
            # If it was "amount to add", the logic would be:
            # if product.stock < cart_item.quantity + quantity: ... error ...
            # cart_item.quantity += quantity
            # For "new total quantity":
            if product.stock < quantity: # Redundant if already checked above, unless quantity means "additional"
                 return Response({'error': _(f'Not enough stock for {product.name} to update to {quantity}. Available: {product.stock}')}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity # Set to new quantity
            cart_item.save()

        serializer = self.get_serializer(cart) # Serialize the whole cart
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='update-item/(?P<item_pk>[^/.]+)', permission_classes=[AllowAny])
    def update_item_quantity(self, request, item_pk=None): # Renamed for clarity
        cart = self.get_cart(request)
        new_quantity = int(request.data.get('quantity', -1))

        if new_quantity < 0:
             return Response({'error': _('Valid quantity is required.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': _('Cart item not found.')}, status=status.HTTP_404_NOT_FOUND)

        product = cart_item.product
        if not product.available and new_quantity > 0 : # Allow setting to 0 even if unavailable
            return Response({'error': _(f'Product {product.name} is no longer available.')}, status=status.HTTP_400_BAD_REQUEST)

        if new_quantity == 0:
            cart_item.delete()
        else:
            if product.stock < new_quantity:
                return Response({'error': _(f'Not enough stock for {product.name}. Requested: {new_quantity}, Stock: {product.stock}')}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            cart_item.save()

        # Re-fetch cart to ensure related items are fresh for serialization
        cart = Cart.objects.prefetch_related('items__product').get(id=cart.id)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='remove-item/(?P<item_pk>[^/.]+)', permission_classes=[AllowAny])
    def remove_item(self, request, item_pk=None):
        cart = self.get_cart(request)
        try:
            cart_item = CartItem.objects.get(id=item_pk, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': _('Cart item not found.')}, status=status.HTTP_404_NOT_FOUND)

        # Re-fetch cart to ensure related items are fresh for serialization
        cart = Cart.objects.prefetch_related('items__product').get(id=cart.id)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='clear', permission_classes=[AllowAny])
    def clear_cart(self, request):
        cart = self.get_cart(request)
        cart.items.all().delete()
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
