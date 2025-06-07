from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'shop' # Define the application namespace
from .views import (
    UserRegistrationView, UserProfileView, UserPaymentMethodViewSet,
    CategoryViewSet, ProductViewSet, OrderViewSet, CartViewSet # Added CartViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payment-methods', UserPaymentMethodViewSet, basename='paymentmethod')
router.register(r'cart', CartViewSet, basename='cart') # Register CartViewSet

urlpatterns = [
    # User management
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain-pair'), # JWT Login
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'), # JWT Refresh
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # API routes from router
    path('', include(router.urls)), # This includes all registered viewsets
]
