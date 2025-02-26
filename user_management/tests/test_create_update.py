from core.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken


class RegistrationViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('user-register')  # The URL for registration

    def test_user_registration_success(self):
        data = {
            'email': 'testuser@example.com',
            'name': 'Test User',
            'password': 'password123'
        }

        response = self.client.post(self.url, data, format='json')

        # Check if the user is created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'testuser@example.com')

    def test_user_registration_missing_email(self):
        data = {
            'name': 'Test User',
            'password': 'password123'
        }

        response = self.client.post(self.url, data, format='json')

        # Ensure an error is raised for missing email
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_missing_password(self):
        data = {
            'email': 'testuser@example.com',
            'name': 'Test User'
        }

        response = self.client.post(self.url, data, format='json')

        # Ensure an error is raised for missing password
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)



class UserUpdateViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            name='Test User'
        )

        # Authenticate using force_authenticate
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user-update', kwargs={'user_id': self.user.id})

    def test_user_update_success(self):
        data = {
            'name': 'Updated User'
        }

        response = self.client.patch(self.url, data, format='json')

        # Check if the user data is updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated User')

    def test_user_update_without_password(self):
        data = {
            'name': 'Updated User'
        }

        response = self.client.patch(self.url, data, format='json')

        # Ensure the password is not required for an update without changing it
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated User')

    def test_password_update_success(self):
        data = {
            'current_password': 'password123',
            'new_password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        # Ensure the password is updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_update_wrong_current_password(self):
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_update_missing_current_password(self):
        data = {
            'new_password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
        self.assertEqual(response.data['current_password'][0], 'Current password is required to set new password')