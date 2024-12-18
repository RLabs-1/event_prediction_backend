from django.test import TestCase

# Create your tests here.
# accounts/tests.py

# Unit tests for the accounts app functionality such as user registration and email verification.
# Ensure that the email verification process works correctly by testing the token generation and validation.

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.mail import outbox
from .utils import send_verification_email


class UserRegistrationTest(TestCase):
    def test_registration_sends_email(self):
        """
        Test that a registration request sends a verification email.
        """
        user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')
        send_verification_email(user)  # Simulate sending verification email

        # Check if the email was sent
        self.assertEqual(len(outbox), 1)
        self.assertIn("Verify Your Email", outbox[0].subject)
        self.assertIn("Click the link to verify your email", outbox[0].body)

    def test_verify_email(self):
        """
        Test that the email verification process works correctly.
        """
        user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')
        send_verification_email(user)
        token = outbox[0].body.split('=')[-1]  # Extract token from the email body
        success, message = verify_email_token(token)

        self.assertTrue(success)
        self.assertEqual(message, "Email successfully verified!")
