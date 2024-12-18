# accounts/utils.py

from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import BadSignature
from django.contrib.auth.models import User
from django.core.signing import Signer

signer = Signer()
"""The Signer class in Django is part of the django.core.signing module, and it is used to create "signed" data. This 
means that the data is securely encoded with a cryptographic signature that can later be verified to ensure its 
integrity and authenticity """


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


def verify_email_token(verification_code, email):
    """
    Verifies the email verification token.

    Arguments:
    verification_code -- The code provided by the user to verify the email.
    email -- The user's email address.

    Returns:
    A tuple (success, message), where:
    - success: True if the code matches, False if it's invalid or expired.
    - message: A success or error message.
    """
    try:
        # Unsigned the verification code (token) to retrieve the user's email
        unsiged_email = signer.unsign(verification_code)

        # Check if the email matches
        if unsiged_email != email:
            return False, "Invalid verification code or email mismatch."

        # Retrieve the user associated with the email
        user = User.objects.get(email=email)

        # Activate the user account
        user.is_active = True
        user.save()

        return True, "Email successfully verified!"

    except BadSignature:
        return False, "Invalid or expired verification code."
    except User.DoesNotExist:
        return False, "User not found."
