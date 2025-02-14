from django.test import TestCase
from django.core.exceptions import ValidationError
from user_management.exceptions.custom_exceptions import *
from core.models import User

class UserExceptionTests(TestCase):
    def setUp(self):
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }

    def test_user_validation_error(self):
        """Test validation error when creating user with invalid data"""
        with self.assertRaises(UserValidationError):
            User.objects.create_user(email='', password='test123')

    def test_user_state_error(self):
        """Test state transitions"""
        user = User.objects.create_user(**self.valid_user_data)
        user.is_active = False
        user.save()

        with self.assertRaises(UserStateError):
            user.deactivate()  # Should raise error as already inactive

    def test_user_not_verified_error(self):
        """Test operations requiring verification"""
        user = User.objects.create_user(**self.valid_user_data)
        user.is_verified = False
        user.save()

        with self.assertRaises(UserNotVerifiedError):
            user.activate()  # Should raise error as not verified 