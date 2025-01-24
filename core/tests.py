from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User


class UserSystemTest(TestCase):
    def setUp(self):
        self.register_url = "/api/user/register/"
        self.login_url = "/api/user/login/"
        self.verify_url = "/api/user/verify-email/"
        self.deactivate_url_template = "/api/user/{}/deactivate/"
        self.user_data = {
            "email": "BuffSyndra_JglDiff@gmail.com",
            "password": "StrongPaSsWord123",
            "name": "Walter White"
        }


    def test_user_creation(self):
        response = self.client.post(reverse('user-register'), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())


    def test_user_login(self):
        # First, create a user
        User.objects.create_user(**self.user_data)
        
        # Attempt to log in with correct credentials
        response = self.client.post(reverse('user-login'), {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)



    def test_user_flow_integration(self):
        # Step 1: Create a user
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 2: Extract user from DB and check initial status
        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_verified)  # Ensure user is initially unverified

        #Ensure that initial login attempt fails since the user is unverified
        login_response = self.client.post(self.login_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)
        user.refresh_from_db()

        # This part assumes that the verification code is generated immediately after the initial login attempt
        verification_code = user.verification_code 

        # Step 3: Verify email using the extracted code
        verify_response = self.client.post(self.verify_url, {"code": verification_code})
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # Refresh user instance and check verification status
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        # Step 4: Login with verified credentials
        login_response = self.client.post(self.login_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)

        # Step 5: Deactivate user
        self.assertTrue(user.is_active) # Ensure user is initially active upon creation

        deactivate_url = self.deactivate_url_template.format(user.id)
        deactivate_response = self.client.patch(deactivate_url) #deactivate the user
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertFalse(self.user.is_active) # Ensure is_active is updated

        login_response = self.client.post(self.login_url, {
        "email": self.user_data["email"],
        "password": self.user_data["password"]
        })
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED) # Ensure that after user deactivation, login attempts fail 
        

        

