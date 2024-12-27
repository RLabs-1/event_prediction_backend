from django.test import TestCase
from unittest.mock import patch
from user_management.services.email_service import EmailService
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse
from user_management.views.views import user_register
import random
import string

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
