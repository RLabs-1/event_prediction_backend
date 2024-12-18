# accounts/services.py

from django.core.signing import Signer, BadSignature
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

signer = Signer()


class RegistrationService:
    @staticmethod
    def verify_email_code(email, verification_code):
        """
        Verifies the email verification code (token).

        Arguments:
        email -- The email of the user.
        verification_code -- The token that the user provides for email verification.

        Returns:
        A success or error message.
        """
        try:
            # Unsigned the verification code (token) to retrieve the user's email
            unsiged_email = signer.unsign(verification_code)

            # Check if the email matches
            if unsiged_email != email:
                raise ValidationError("Invalid verification code or email mismatch.")

            # Retrieve the user associated with the email
            user = User.objects.get(email=email)

            # Activate the user account
            user.is_active = True
            user.save()

            return "Email successfully verified!"

        except BadSignature:
            raise ValidationError("Invalid or expired verification code.")
        except User.DoesNotExist:
            raise ValidationError("User not found.")
