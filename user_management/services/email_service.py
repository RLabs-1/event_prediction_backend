from django.core.mail import send_mail
from django.conf import settings
import logging
import random
import string

# Set up logger
logger = logging.getLogger('user_management')

class EmailService:

    @staticmethod
    def generate_verification_code(length=6):
        """Generate a random verification code"""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def send_email(email):
        """
        Send welcome email with verification code to newly registered user
        """
        try:
            # Generate verification code
            verification_code = EmailService.generate_verification_code()
            
            subject = "Welcome to Event Prediction System - Email Verification"
            message = f"""
            Welcome to Event Prediction System!
            
            Thank you for registering. To complete your registration and activate your account, 
            please use the following verification code:
            
            Verification Code: {verification_code}
            
            This code will expire in 1 hour.
            
            If you did not register for an account, please ignore this email.
            
            Best regards,
            Event Prediction Team
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent successfully to {email}")
            return verification_code
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            raise Exception(f"Failed to send welcome email: {str(e)}")

    @staticmethod
    def send_password_reset_email(email, verification_code):
        """
        Send password reset email with verification code
        """
        subject = 'Password Reset Request'
        message = f"""
        You have requested to reset your password.
        
        Your verification code is: {verification_code}
        
        This code will expire in 15 minutes.
        
        If you did not request this password reset, please ignore this email.
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise Exception("Failed to send password reset email")
