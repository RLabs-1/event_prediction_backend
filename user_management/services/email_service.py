from django.core.mail import send_mail
from django.conf import settings
import logging
import random
import string

# Set up logger
logger = logging.getLogger('user_management')

class EmailService:

    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))

    def send_email(self, recipient_email):
        """Send verification code email"""
        try:
            verification_code = self.generate_verification_code()
            print(f"Generated code: {verification_code}")  # Debug print
            
            subject = "Password Reset Verification Code"
            message = f"""
            Your verification code is: {verification_code}
            
            Please use this code to reset your password.
            This code will expire in 1 hour.
            """
            
            print(f"Attempting to send email to: {recipient_email}")  # Debug print
            print(f"Using sender email: {settings.EMAIL_HOST_USER}")  # Debug print
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            print("Email sent successfully!")  # Debug print
            return verification_code
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # Debug print
            raise Exception(f"Failed to send email: {str(e)}")

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

    @staticmethod
    def send_email(email):
        """
        Send verification email
        """
        # Your existing send_email implementation
        pass