from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from user_management.services.email_service import EmailService
from unittest.mock import patch
import string
from core.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


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


class UserLoginViewTest(TestCase):

    def setUp(self):
        """
        Set up a user for testing the login functionality.
        """
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123"
        )
        self.login_url = "/api/user/login/"

    def test_user_login_success(self):
        """
        Test the user login with correct credentials.
        """
        # Define the login payload
        payload = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }

        # Send the POST request to the login endpoint
        response = self.client.post(self.login_url, payload, format="json")

        # Assert the response status code and content
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_invalid_credentials(self):
        """
        Test login with invalid credentials (wrong password).
        """
        payload = {
            "email": "testuser@example.com",
            "password": "wrongpassword"
        }

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"error": "Invalid credentials."})

    def test_user_login_missing_fields(self):
        """
        Test login with missing email or password.
        """
        # Test missing email
        payload = {"password": "testpassword123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Email and password are required."})

        # Test missing password
        payload = {"email": "testuser@example.com"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Email and password are required."})

    def test_user_login_non_existent_user(self):
        """
        Test login with a non-existent user.
        """
        payload = {
            "email": "nonexistentuser@example.com",
            "password": "testpassword123"
        }

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"error": "Invalid credentials."})

class UserRegisterViewTestCase(TestCase):

    @patch('user_management.services.EmailService.send_email')  # Mocking the send_email method
    def test_user_register_success(self, mock_send_email):
        # Mocking send_email to not actually send an email
        mock_send_email.return_value = None
        response = self.client.post(reverse('user_register'))
        
        # Check the response content
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"message": "User registered and email sent successfully!"}
        )

        # Check that send_email was called once
        mock_send_email.assert_called_once_with("raneem.dz34@gmail.com")

    @patch('user_management.services.EmailService.send_email')  # Mocking the send_email method
    def test_user_register_failure(self, mock_send_email):
        # Simulate a failure in send_email
        mock_send_email.side_effect = Exception("Email sending failed")
        response = self.client.post(reverse('user_register'))
        
        # Check that the status code is 500 when email sending fails
        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error": "Failed to send email: Email sending failed"}
        )
        
class EmailServiceTestCase(TestCase):
    
    def test_generate_verification_code(self):
        email_service = EmailService()
        
        # Test the default length (6 characters)
        code = email_service.generate_verification_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(all(c in string.ascii_letters + string.digits for c in code))

        # Test with a custom length
        code = email_service.generate_verification_code(8)
        self.assertEqual(len(code), 8)

    @patch('user_management.services.email_service.send_mail')  # Mocking the send_mail method
    def test_send_email(self, mock_send_mail):
        email_service = EmailService()
        recipient_email = "test@example.com"
        
        # Call the send_email method
        email_service.send_email(recipient_email)
        
        # Check that send_mail was called once
        mock_send_mail.assert_called_once_with(
            subject="Welcome to Our Platform!",
            message=patch('user_management.services.email_service.EmailService.send_email.__code__'),
            from_email="eventprediction.backend@gmail.com",
            recipient_list=[recipient_email],
            fail_silently=False
        )
        
        # Ensure that the email content includes the verification code placeholder
        args, kwargs = mock_send_mail.call_args
        message = args[1]
        self.assertIn("Verification Code:", message)

