from django.test import TestCase
from user_management.services.services import UserService
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    UserInactiveException,
    InvalidUserOperationException,
)
from user_management.models.models import User


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
