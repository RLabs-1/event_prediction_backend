from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .services import RegistrationService
from django.core.exceptions import ValidationError
import json
from .utils import verify_email_token, send_verification_email


# View to handle email verification via a POST request
@csrf_exempt
@require_POST
def verify_email(request):
    """
    Endpoint to verify the user's email address using the provided verification code.

    Arguments:
    request -- HTTP POST request containing 'email' and 'verification_code'.

    Returns:
    JsonResponse -- Success or error message.
    """
    try:
        # Parse JSON body for email and verification_code
        data = json.loads(request.body)
        email = data.get('email')
        verification_code = data.get('verification_code')

        # Ensure both email and verification code are provided
        if not email or not verification_code:
            return JsonResponse({"error": "Email and verification code are required."}, status=400)

        # Use RegistrationService to verify the email and verification code
        message = RegistrationService.verify_email_code(email, verification_code)

        return JsonResponse({"message": message}, status=200)

    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Existing view to handle the email verification process (using token)
def verify_email_token_view(request):
    """
    View that handles the email verification process via a token link.

    This view receives a token from the URL, verifies it using the
    verify_email_token function, and returns a response indicating
    whether the verification was successful or not.
    """
    token = request.GET.get('token', '')

    # Verify the token and get the result (success, message)
    success, message = verify_email_token(token)

    # Return a JSON response indicating success or failure
    if success:
        return JsonResponse({"message": message}, status=200)
    else:
        return JsonResponse({"error": message}, status=400)


@csrf_exempt
@require_POST
def register_user(request):
    """
    Register a new user and send them an email verification link.

    Arguments:
    request -- the HTTP request object containing user details.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Handle missing fields or invalid data
        if not username or not email or not password:
            return JsonResponse({"error": "Missing required fields."}, status=400)

        # Create a new user instance (without activating it)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # User is not active until they verify their email
        user.save()

        # Send the verification email
        send_verification_email(user)

        return JsonResponse({"message": "Registration successful. Please check your email to verify your account."},
                            status=201)

    return JsonResponse({"error": "Invalid request method."}, status=405)  # Method Not Allowed
