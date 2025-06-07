from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from caspinex.shop.models import Product, Category, Cart, CartItem # Corrected import path
from decimal import Decimal

User = get_user_model()

class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='testpassword123', first_name='Test', last_name='User')

        self.category = Category.objects.create(name='تست الکترونیک', slug='test-electronics-cart') # Unique slug
        self.product1 = Product.objects.create(
            name='محصول تست ۱ کارت', slug='product-test-1-cart', category=self.category,
            price=Decimal('100.00'), stock=10, available=True
        )
        self.product2 = Product.objects.create(
            name='محصول تست ۲ کارت', slug='product-test-2-cart', category=self.category,
            price=Decimal('200.00'), stock=5, available=True
        )
        self.product_unavailable = Product.objects.create(
            name='محصول ناموجود کارت', slug='product-unavailable-cart', category=self.category,
            price=Decimal('50.00'), stock=0, available=False
        )

        # URLs for cart actions. Basename for cart router is 'cart'. Actions are methods in CartViewSet.
        self.cart_url = reverse('shop:cart-retrieve-cart') # Corrected: action is retrieve_cart (url_path='mine')
        self.add_item_url = reverse('shop:cart-add-item')   # Correct: action is add_item
        self.clear_cart_url = reverse('shop:cart-clear-cart') # Corrected: action is clear_cart (url_path='clear')
        # update_item_quantity and remove_item URLs need item_pk, constructed in tests using correct action names.

        self.guest_client = APIClient()
        self.auth_client = APIClient()

    def _login_user(self):
        # Assuming 'token-obtain-pair' is the name for simplejwt's TokenObtainPairView in shop:urls
        # If shop:urls is included with namespace 'shop', then 'shop:token-obtain-pair' might be incorrect
        # if token-obtain-pair is not part of that router.
        # Let's assume it's directly under shop's urlpatterns.
        login_url = reverse('shop:token-obtain-pair')
        response = self.auth_client.post(login_url, {'email': 'testuser@example.com', 'password': 'testpassword123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Login failed: {response.data}")
        token = response.data.get('access')
        self.auth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- Guest Cart Tests ---
    def test_guest_can_get_cart(self):
        response = self.guest_client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('id' in response.data)
        self.assertEqual(response.data['items'], [])

    def test_guest_add_item_to_cart(self):
        response = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_detail']['id'], self.product1.id)
        self.assertEqual(response.data['items'][0]['quantity'], 2)
        self.assertEqual(Decimal(response.data['total_price']), Decimal('200.00'))

    def test_guest_add_unavailable_product_fails(self):
        response = self.guest_client.post(self.add_item_url, {'product_id': self.product_unavailable.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_add_item_insufficient_stock_fails(self):
        response = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': self.product1.stock + 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_guest_update_item_quantity(self):
        add_response = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        self.assertEqual(add_response.status_code, status.HTTP_200_OK)
        item_id = add_response.data['items'][0]['id']

        update_url = reverse('shop:cart-update-item-quantity', kwargs={'item_pk': item_id})
        response = self.guest_client.patch(update_url, {'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['quantity'], 3)
        self.assertEqual(Decimal(response.data['total_price']), Decimal('300.00'))

    def test_guest_update_item_to_zero_removes_item(self):
        add_response = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        item_id = add_response.data['items'][0]['id']
        update_url = reverse('shop:cart-update-item-quantity', kwargs={'item_pk': item_id})
        response = self.guest_client.patch(update_url, {'quantity': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_guest_remove_item_from_cart(self):
        add_response = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        item_id = add_response.data['items'][0]['id']
        remove_url = reverse('shop:cart-remove-item', kwargs={'item_pk': item_id})
        response = self.guest_client.delete(remove_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_guest_clear_cart(self):
        self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        self.guest_client.post(self.add_item_url, {'product_id': self.product2.id, 'quantity': 2}, format='json')
        response = self.guest_client.post(self.clear_cart_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(Decimal(response.data['total_price']), Decimal('0.00'))

    # --- Authenticated User Cart Tests ---
    def test_auth_user_can_get_cart(self):
        self._login_user()
        response = self.auth_client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('id' in response.data)
        self.assertEqual(response.data['user'], self.user.id)

    def test_auth_user_add_item_to_cart(self):
        self._login_user()
        response = self.auth_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_detail']['id'], self.product1.id)

    def test_guest_cart_merges_after_login(self):
        # 1. Guest adds items
        add1_resp = self.guest_client.post(self.add_item_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        guest_cart_id = add1_resp.data['id']

        # Ensure session is saved for guest_client
        self.guest_client.session.save()

        # 2. User logs in with a separate client, but we need to simulate session persistence.
        # APITestCase clients manage their own sessions. To test merge, the logged-in user's session
        # needs to know about the guest_cart_id.
        # We will use a single client that acts as guest, then logs in.

        # The guest_client already has the session with cart_id after adding items.
        # Now, we will use this same client to log in.

        # Log in using the guest_client instance, which will then become an authenticated client.
        login_url = reverse('shop:token-obtain-pair')
        login_response = self.guest_client.post(login_url, {'email': 'testuser@example.com', 'password': 'testpassword123'}, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login failed: {login_response.data}")
        token = login_response.data.get('access')
        self.guest_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') # Authenticate the client

        # 3. Authenticated user (using the now authenticated guest_client) accesses their cart.
        # The get_cart method in CartViewSet should handle merging the session cart (identified by session['cart_id'])
        # with the user's cart.

        # Add another item as authenticated user to ensure their cart is active and potentially trigger merge/creation.
        self.guest_client.post(self.add_item_url, {'product_id': self.product2.id, 'quantity': 2}, format='json')

        response = self.guest_client.get(self.cart_url) # Access cart after login and adding another item
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that items from guest cart (product1) and new item (product2) are present
        final_items = response.data['items']
        self.assertEqual(len(final_items), 2, "Cart items did not merge correctly or new item not added.")

        item1_found = any(item['product_detail']['id'] == self.product1.id and item['quantity'] == 1 for item in final_items)
        item2_found = any(item['product_detail']['id'] == self.product2.id and item['quantity'] == 2 for item in final_items)
        self.assertTrue(item1_found, "Item from guest cart (product1) not found after merge.")
        self.assertTrue(item2_found, "Item added after login (product2) not found.")

        # Verify the guest cart (by ID) is deleted or disassociated
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(id=guest_cart_id, user__isnull=True)
