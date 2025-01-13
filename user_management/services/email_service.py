from django.core.mail import send_mail
from django.conf import settings
import logging
import random
import string

# Set up logger
logger = logging.getLogger()

class EmailService:

    def generate_verification_code(self, length=6):
        #Generating a random verification code.

        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(length))
        return code

    def send_email(self, recipient_email: str):
        # Sends a welcome email to the registered user, including a random/unique verification code.

        try:
            subject = "Welcome to Our Platform!"      #the sent email subject.
            verification_code = self.generate_verification_code() #Creating a unique random verification code using generate_verification_code() func.

            #the sent email message:
            message = f"""
            Welcome to our platform!

            We are excited to have you on board. To complete your registration, please use the following verification code:

            Verification Code: {verification_code}

            Please enter this code on the verification page to activate your account.

            Best regards,
            The Team
            """

            #sending the email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient_email],
                fail_silently=False,
            )

            logger.info(f"Email sent successfully to {recipient_email} with subject: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}. Error: {str(e)}")
            raise e