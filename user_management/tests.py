from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

class UserLoginViewTest(APITestCase):

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