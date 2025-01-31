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

        # Generate JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.url = reverse('user-update', kwargs={'user_id': self.user.id})

    def test_user_update_success(self):
        data = {
            'email': 'updateduser@example.com',
            'name': 'Updated User',
            'password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        # Check if the user data is updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updateduser@example.com')
        self.assertEqual(self.user.name, 'Updated User')

    def test_user_update_invalid_data(self):
        data = {
            'email': 'invalidemail',
            'name': 'Updated User',
            'password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        # Ensure invalid email raises an error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_update_without_password(self):
        data = {
            'email': 'updateduser@example.com',
            'name': 'Updated User'
        }

        response = self.client.patch(self.url, data, format='json')

        # Ensure the password is not required for an update without changing it
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updateduser@example.com')

    def test_password_update(self):
        data = {
            'email': 'testuser@example.com',
            'name': 'Test User Updated',
            'password': 'newpassword123'
        }

        response = self.client.patch(self.url, data, format='json')

        # Ensure the password is updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()

        # Check if the new password is different from the old one (check hashed passwords)
        self.assertNotEqual(self.user.password, 'newpassword123')
        self.assertTrue(self.user.check_password('newpassword123'))
