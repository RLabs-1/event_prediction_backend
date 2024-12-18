# utils.py
from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature
from django.conf import settings
from django.contrib.auth.models import User

# The signer is used to create and verify signed tokens for email verification
signer = Signer()


def send_verification_email(user):
    """
    Sends a verification email to the user.

    Arguments:
    user -- the user object to whom the verification email will be sent.
    """
    # Create a signed token using the user's email
    token = signer.sign(user.email)

    # Construct the verification link using the frontend URL and token
    verification_link = f"{settings.FRONTEND_URL}/verify-email/?token={token}"

    # Send the email with the verification link
    send_mail(
        "Verify Your Email",  # Subject of the email
        f"Click the link to verify your email: {verification_link}",  # Body of the email
        settings.DEFAULT_FROM_EMAIL,  # Sender's email
        [user.email],  # Recipient's email
    )


def verify_email_token(token):
    """
    Verifies the email verification token.

    Arguments:
    token -- the signed token received from the verification link.

    Returns:
    A tuple (success, message), where:
    - success: True if the token is valid, False if it's not.
    - message: A success or error message.
    """
    try:
        # Unsigned the token to retrieve the user's email
        email = signer.unsign(token)

        # Retrieve the user associated with the email
        user = User.objects.get(email=email)

        # Activate the user account (set is_active to True)
        user.is_active = True
        user.save()

        # Return a success message
        return True, "Email successfully verified!"

    except (BadSignature, User.DoesNotExist):
        # Return an error message if the token is invalid or user does not exist
        return False, "Invalid or expired verification link."
