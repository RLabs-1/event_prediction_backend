from django.test import TestCase
from user_management.services.services import UserService
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    UserInactiveException,
    InvalidUserOperationException,
)
from user_management.models.models import User
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from unittest.mock import patch
from user_management.services.email_service import EmailService
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse
from user_management.views.views import user_register
import random
import string
from rest_framework.test import APIClient


class UserExceptionTestCase(TestCase):
    def test_user_not_found_exception(self):
        """Test that UserNotFoundException is raised when a user is not found"""
        # Attempt to deactivate a user with a non-existent user ID
        with self.assertRaises(UserNotFoundException):
            UserService.deactivate_user(999)  # Non-existent user ID

    def test_user_already_exists_exception(self):
        """Test that UserAlreadyExistsException is raised when creating a duplicate user"""
        email = "existinguser@example.com"
        password = "password123"

        # Create the first user
        user = User.objects.create_user(email=email, password=password)

        # Try creating another user with the same email, should raise exception
        with self.assertRaises(UserAlreadyExistsException):
            User.objects.create_user(email=email, password=password)

    def test_user_inactive_exception(self):
        """Test that UserInactiveException is raised when attempting to deactivate an already inactive user"""
        email = "inactiveuser@example.com"
        password = "password123"

        # Create the user and deactivate it
        user = User.objects.create_user(email=email, password=password)
        user.is_active = False
        user.save()

        # Attempt to deactivate the already inactive user
        with self.assertRaises(UserInactiveException):
            UserService.deactivate_user(user.id)  # Should raise exception since the user is already inactive

    def test_invalid_user_operation_exception(self):
        """Test that InvalidUserOperationException is raised for invalid user operations"""
        email = "invaliduser@example.com"
        password = "password123"

        # Create the user
        user = User.objects.create_user(email=email, password=password)

        # Manually raise an InvalidUserOperationException for an invalid operation
        with self.assertRaises(InvalidUserOperationException):
            raise InvalidUserOperationException("Invalid user operation test")

    def test_user_activate_already_active(self):
        """Test that no exception is raised when trying to activate an already active user"""
        email = "alreadyactive@example.com"
        password = "password123"

        # Create an active user
        user = User.objects.create_user(email=email, password=password)

        # Ensure the user is active already
        self.assertTrue(user.is_active)

        # No exception should be raised when activating an already active user
        response = UserService.activate_user(user.id)
        self.assertEqual(response['message'], 'User activated successfully')
        self.assertEqual(response['success'], True)

    def test_user_deactivate_already_inactive(self):
        """Test that trying to deactivate an already inactive user raises the right exception"""
        email = "alreadyinactive@example.com"
        password = "password123"

        # Create an inactive user
        user = User.objects.create_user(email=email, password=password)
        user.is_active = False
        user.save()

        # Try deactivating an already inactive user
        with self.assertRaises(UserInactiveException):
            UserService.deactivate_user(user.id)



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

class VerifyEmailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.verify_url = reverse('verify-email')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.user.verification_code = 'ABC123'
        self.user.save()

    def test_verify_email_success(self):
        """Test successful email verification"""
        data = {
            'email': 'test@example.com',
            'verification_code': 'ABC123'
        }
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_verify_email_invalid_code(self):
        """Test email verification with invalid code"""
        data = {
            'email': 'test@example.com',
            'verification_code': 'WRONG123'
        }
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_email_missing_data(self):
        """Test email verification with missing data"""
        # Missing verification code
        data = {'email': 'test@example.com'}
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        data = {'verification_code': 'ABC123'}
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

