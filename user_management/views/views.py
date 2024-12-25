from django.http import JsonResponse
from ..services.email_service import EmailService
from django.shortcuts import render

def user_register(request):

    user_email = "raneem.dz34@gmail.com"  #We should use the registered email

    #Sending welcome email
    email_service = EmailService()
    try:
        email_service.send_email(user_email)
        return JsonResponse({"message": "User registered and email sent successfully!"})
    except Exception as e:
        return JsonResponse({"error": f"Failed to send email: {str(e)}"}, status=500)


