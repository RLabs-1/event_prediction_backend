# user_management/exceptions/custom_exceptions.py

class UserException(Exception):
    """Base exception class for User model-related errors."""
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

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

class UserValidationError(UserException):
    """Exception raised for validation errors."""
    def __init__(self, message="Invalid user data provided"):
        super().__init__(message, code='validation_error')

class UserAuthenticationError(UserException):
    """Exception raised for authentication failures."""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, code='auth_error')

class UserPermissionError(UserException):
    """Exception raised for permission-related issues."""
    def __init__(self, message="Permission denied"):
        super().__init__(message, code='permission_error')

class UserNotVerifiedError(UserException):
    """Exception raised when unverified user attempts restricted actions."""
    def __init__(self, message="User email not verified"):
        super().__init__(message, code='not_verified')

class UserStateError(UserException):
    """Exception raised for invalid state transitions."""
    def __init__(self, message="Invalid user state"):
        super().__init__(message, code='state_error')
