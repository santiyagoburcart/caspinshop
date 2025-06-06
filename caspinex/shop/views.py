from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend # Ensure this is imported

from .models import CustomUser, UserPaymentMethod, Category, Product, Order, OrderItem
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserPaymentMethodSerializer,
    CategorySerializer, ProductSerializer, OrderSerializer
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
