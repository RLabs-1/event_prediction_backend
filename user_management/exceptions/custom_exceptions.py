# user_management/exceptions/custom_exceptions.py

class UserException(Exception):
    """Base exception class for User model-related errors."""
    pass

class UserNotFoundException(UserException):
    """Exception raised when a user is not found."""
    def __init__(self, message="User not found"):
        super().__init__(message)

class UserAlreadyExistsException(UserException):
    """Exception raised when a user with the same email already exists."""
    def __init__(self, message="User with this email already exists"):
        super().__init__(message)

class UserInactiveException(UserException):
    """Exception raised when attempting to operate on an inactive user."""
    def __init__(self, message="The user is inactive"):
        super().__init__(message)

class InvalidUserOperationException(UserException):
    """Exception raised for invalid user operations."""
    def __init__(self, message="Invalid operation on user"):
        super().__init__(message)
