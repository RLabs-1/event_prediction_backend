````README for the **`accounts`** app,
specifically for the **email verification** feature:
---

# Accounts App - Email Verification

This section of the **`accounts`** app handles the email verification functionality. It is responsible for sending verification emails to users when they register and verifying their email when they submit the verification code.

## Features

- **Send Email Verification**: Sends an email to the user with a unique verification link after registration.
- **Verify Email**: Allows the user to verify their email address by submitting a verification code through a POST request.

## How It Works

### 1. **Sending Verification Emails**
   - When a user registers, the `send_verification_email()` function is called automatically.
   - This function generates a signed token for the user's email and creates a verification link.
   - The link is then sent to the user's provided email address.

### 2. **Verifying Email**
   - The user submits the email and verification code (received in the email).
   - The **`verify_email()`** endpoint is called to verify the code and activate the user's account.

## Code Details

### Functions

#### `send_verification_email(user)`
   Sends a verification email to the user.

   - **Arguments**:
     - `user`: The `User` object to which the verification email will be sent.
   - **Process**:
     1. Generates a signed token for the user’s email using Django’s `Signer` class.
     2. Creates a verification URL with the signed token.
     3. Sends the email containing the verification link to the user.

   - **Usage**:
     You can call this function after creating a user or whenever you need to trigger email verification manually.

#### `verify_email_code(email, verification_code)`
   Verifies the email address by checking the provided verification code.

   - **Arguments**:
     - `email`: The email of the user whose verification code is being checked.
     - `verification_code`: The code the user receives to verify their email address.
   - **Process**:
     1. Unsigned the verification code.
     2. Checks if the email matches.
     3. If valid, activates the user's account.
   
   - **Returns**: A success message if verification is successful, or raises an error if the code is invalid.

### Endpoints

#### **POST** `/api/user/verifyEmail/`
   - **Purpose**: Verifies a user's email address using the provided email and verification code.
   - **Request**:
     - **Body**:
       ```json
       {
         "email": "user@example.com",
         "verification_code": "verification_token"
       }
       ```
   - **Response**:
     - Success (200):
       ```json
       {
         "message": "Email successfully verified!"
       }
       ```
     - Error (400):
       ```json
       {
         "error": "Invalid verification code or email mismatch."
       }
       ```

### URL Configuration

In **`accounts/urls.py`**, you should define the URL for email verification:

```python
from django.urls import path
from .views import verify_email, verify_email_token_view

urlpatterns = [
    path('verify-email/', verify_email, name='verify_email'),
    path('verify-email-token/', verify_email_token_view, name='verify_email_token'),
]
```

Make sure this is included in your root `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.urls')),  # Include the accounts URLs
]
```

## How to Use

1. **Triggering Email Verification**:
   - When a user registers, you can call the `send_verification_email()` function as follows:
     ```python
     from accounts.views import send_verification_email
     from django.contrib.auth.models import User

     user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')
     send_verification_email(user)
     ```

2. **Verifying Email**:
   - The user submits the email and verification code using the following API call:
     ```bash
     POST /api/user/verifyEmail/ HTTP/1.1
     Content-Type: application/json

     {
       "email": "newuser@example.com",
       "verification_code": "signed_verification_token"
     }
     ```
   - The response will indicate whether the email verification was successful.

### Configuration

1. **Email Backend**: Ensure that you have an email backend configured in your `settings.py` for sending emails. For development, you can use the console email backend to print emails in the terminal:
   
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Development mode
   DEFAULT_FROM_EMAIL = 'your-email@example.com'  # Replace with your email
   FRONTEND_URL = 'http://127.0.0.1:8000'  # Replace with your frontend URL for verification
   ```

   For production, configure your email backend as needed (e.g., using SMTP with Gmail, SendGrid, etc.).

## Testing

1. **Create a Superuser** to access the admin panel and manually trigger email verification:
   ```bash
   python manage.py createsuperuser
   ```

2. **Test via Django Shell**:
   You can manually test the email verification process from the Django shell:
   ```bash
   python manage.py shell
   ```

   Then, create a user and trigger the email:
   ```python
   from django.contrib.auth.models import User
   from accounts.views import send_verification_email

   user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
   send_verification_email(user)
   ```

3. **Check the terminal** to view the email with the verification link printed out (if you're using the console backend).

## Important Notes

- **Don't forget to review email configurations when deploying to production!**
   - Make sure to configure your SMTP settings for sending emails in production.
   - You might want to use an email service like **SendGrid**, **Mailgun**, or **Amazon SES** for reliable email delivery.

- **Security**: The signed tokens used in the email verification link provide a way to ensure the link is valid. Make sure to configure your Django app to handle token expiration if needed.

