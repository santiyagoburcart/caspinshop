from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import CustomUser, UserPaymentMethod, Category, Product, Order, OrderItem
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserPaymentMethodSerializer,
    CategorySerializer, ProductSerializer, OrderSerializer
)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] # Anyone can register

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all() # Required for RetrieveUpdateAPIView
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensures users can only view/update their own profile
        return self.request.user

class UserPaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = UserPaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(available=True).select_related('category').order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-created_at')
        return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items__product').order_by('-created_at')

    # perform_create is handled by the serializer context now
    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user) # User is set in serializer via context

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_as_shipped(self, request, pk=None):
        order = self.get_object()
        if order.status == Order.STATUS_PROCESSING or order.status == Order.STATUS_READY_FOR_SHIPMENT:
            order.status = Order.STATUS_SHIPPED
            order.save()
            return Response({'status': 'order marked as shipped'})
        else:
            return Response({'error': 'Order cannot be marked as shipped in its current state.'}, status=status.HTTP_400_BAD_REQUEST)
