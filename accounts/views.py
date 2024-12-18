from django.contrib.auth.models import User
from django.http import HttpResponse
from django.core.signing import Signer, BadSignature
from django.core.mail import send_mail
from django.conf import settings

signer = Signer()  # Used to generate and verify signed tokens.

# Function to send verification email
def send_verification_email(user):
    token = signer.sign(user.email)  # Create a signed token
    verification_link = f"{settings.FRONTEND_URL}/verify-email/?token={token}"  # Verification link
    send_mail(
        "Verify Your Email",  # Email subject
        f"Click the link to verify your email: {verification_link}",  # Email body
        settings.DEFAULT_FROM_EMAIL,  # From email
        [user.email],  # Recipient email
    )

# Function to verify email when the user clicks the link
def verify_email(request):
    token = request.GET.get('token', '')
    try:
        # Unsigned the token and get the email
        email = signer.unsign(token)
        user = User.objects.get(email=email)
        user.is_active = True  # Activate the user account
        user.save()
        return HttpResponse("Email successfully verified!")  # Success message
    except (BadSignature, User.DoesNotExist):
        return HttpResponse("Invalid or expired verification link.")  # Error message
