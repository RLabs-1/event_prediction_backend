# accounts/views.py

from django.http import HttpResponse
from .utils import send_verification_email, verify_email_token
from django.contrib.auth.models import User


# View to handle the email verification
def verify_email(request):
    """
    View that handles the email verification process.

    This view receives a token from the URL, verifies it using the
    verify_email_token function, and returns a response indicating
    whether the verification was successful or not.

    Arguments:
    request -- the HTTP request object containing the token.

    Returns:
    A response indicating success or failure of the verification.
    """
    # Retrieve the token from the request's query parameters
    token = request.GET.get('token', '')

    # Verify the token and get the result (success, message)
    success, message = verify_email_token(token)

    # Return an HTTP response with the result message
    return HttpResponse(message)


def register_user(request):
    """
    Register a new user and send them an email verification link.

    Arguments:
    request -- the HTTP request object containing user details.

    Notes for Future Developers: - This view handles user registration and sends an email verification link. - The
    current implementation creates a user with `is_active=False`, meaning they cannot log in until their email is
    verified. - Currently, the view only handles POST requests and expects `username`, `email`, and `password` to be
    provided in the request body. - After the registration process, an email with a verification link is sent to the
    user.

    **Future work**:
    - This is a basic implementation for user registration. Further development is needed to:
      1. Add form validation to ensure the provided data is correct and secure.
      2. Handle edge cases like existing emails, username conflicts, and weak passwords.
      3. Implement additional user registration features such as user profile creation or error handling.
      4. Enhance the process with rate-limiting to prevent abuse.
      5. Ensure appropriate security measures like CSRF protection and secure password handling.

    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Create a new user instance (without activating it)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # User is not active until they verify their email
        user.save()

        # Send the verification email
        send_verification_email(user)

        return HttpResponse("Registration successful. Please check your email to verify your account.")

    return HttpResponse("Invalid request method.")
