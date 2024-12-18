from django.test import TestCase
from django.contrib.auth.models import User
from django.core.mail import outbox
from django.urls import reverse
import json

from accounts.utils import send_verification_email, verify_email_token


class UserRegistrationTest(TestCase):
    def test_registration_sends_email(self):
        """
        Test that a registration request sends a verification email.
        """
        # Create a new user (simulate registration)
        user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')

        # Send the verification email manually as it would be done in the registration view
        send_verification_email(user)

        # Check that the email was sent
        self.assertEqual(len(outbox), 1)  # Ensure only one email was sent
        self.assertIn("Verify Your Email", outbox[0].subject)  # Check subject line
        self.assertIn("Click the link to verify your email",
                      outbox[0].body)  # Check body contains the verification link

    def test_verify_email(self):
        """
        Test that the email verification process works correctly.
        """
        user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')

        # Send the verification email
        send_verification_email(user)

        # Extract the token from the email body
        token = outbox[0].body.split('=')[-1]  # Get the token from the verification link

        # Verify the token using the utility function
        success, message = verify_email_token(token)

        # Check that the token verification was successful
        self.assertTrue(success)
        self.assertEqual(message, "Email successfully verified!")

    def test_verify_email_post_endpoint(self):
        """
        Test the email verification POST endpoint.
        """
        user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')

        # Send the verification email
        send_verification_email(user)

        # Extract the token from the email
        token = outbox[0].body.split('=')[-1]  # Get the token from the verification link

        # The verification code is the token in this case
        verification_code = token

        # Now simulate submitting the email and verification code via the POST endpoint
        url = reverse('verify_email')  # Use the POST endpoint URL
        response = self.client.post(url, json.dumps({
            'email': 'newuser@example.com',
            'verification_code': verification_code
        }), content_type='application/json')

        # Assert that the verification was successful
        self.assertEqual(response.status_code, 200)  # Ensure the view returns a 200 status code
        self.assertContains(response, "Email successfully verified!")  # Check for success message in response

    def test_verify_email_post_missing_fields(self):
        """
        Test that the email verification POST endpoint returns an error when fields are missing.
        """
        url = reverse('verify_email')  # Use the POST endpoint URL

        # Missing email and verification_code in request
        response = self.client.post(url, json.dumps({}), content_type='application/json')

        # Assert that the response contains the error message
        self.assertEqual(response.status_code, 400)  # Bad Request for missing fields
        self.assertContains(response, "Email and verification code are required.")  # Check for error message
