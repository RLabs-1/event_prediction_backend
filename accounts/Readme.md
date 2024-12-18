README for the **`accounts`** app,
specifically for the **email verification** feature:
---

# Accounts App - Email Verification

This section of the **`accounts`** app handles email verification functionality. It is responsible for sending verification emails to users when they register and verifying their email when they click the verification link.

## Features

- **Send Email Verification**: Sends an email to the user with a unique verification link.
- **Verify Email**: Allows the user to verify their email address by clicking on the link in the email.

## How It Works

### 1. **Sending Verification Emails**
   - When a user registers or when you want to trigger email verification manually, the `send_verification_email()` function is called.
   - This function creates a signed token for the user's email and generates a verification link.
   - The link is then sent via email to the user's provided email address.

### 2. **Verifying Email**
   - The user receives an email with a verification link that includes a token.
   - When the user clicks the link, the `verify_email()` view is triggered.
   - The token is unsign to retrieve the email address, and the user’s status is updated to "active," confirming their email address.

## Code Details

### Functions

#### `send_verification_email(user)`
   Sends a verification email to the user.

   - **Arguments**:
     - `user`: The `User` object to which the verification email is to be sent.
   - **Process**:
     1. Generates a signed token for the user’s email using the `Signer` class.
     2. Creates a verification URL with the signed token.
     3. Sends the email with the verification link to the user.

   - **Usage**:
     Call this function after creating a user or when you need to trigger email verification manually.

#### `verify_email(request)`
   Handles the verification process when the user clicks the email verification link.

   - **Arguments**:
     - `request`: The HTTP request containing the signed token as a query parameter (`token`).
   - **Process**:
     1. Extracts the token from the query parameters.
     2. Unsings the token to retrieve the user's email.
     3. If the email exists, updates the user's account to be active (`user.is_active = True`).
     4. If the token is invalid or expired, an error message is shown.

   - **URL**:
     The URL for email verification is defined in `accounts/urls.py` as:
     ```
     /accounts/verify-email/?token=<signed_token>
     ```

## How to Use

1. **Triggering Email Verification**:
   - When a user registers, you can call the `send_verification_email()` function like so:
     ```python
     from accounts.views import send_verification_email
     from django.contrib.auth.models import User

     user = User.objects.create_user(username='newuser', email='newuser@example.com', password='password123')
     send_verification_email(user)
     ```

2. **Verifying Email**:
   - After the user clicks the verification link in the email, the `verify_email()` view will be called automatically by the URL configured in `accounts/urls.py`.

### URL Configuration

In **`accounts/urls.py`**, you should define the URL for email verification:

```python
from django.urls import path
from .views import verify_email

urlpatterns = [
    path('verify-email/', verify_email, name='verify_email'),
]
```

Make sure this is included in the root `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.urls')),  # Include the accounts URLs
]
```

## Configuration

1. **Email Backend**: Ensure that you have an email backend configured in your `settings.py` for sending emails. For development, you can use the console email backend to print emails in the terminal.

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
   - Make sure you configure your SMTP settings for sending emails in production.
   - You might want to use an email service like **SendGrid**, **Mailgun**, or **Amazon SES** for reliable email delivery.

- **Security**: The signed tokens used in the email verification link provide a way to ensure the link is valid. Make sure to configure your Django app to handle token expiration if needed.

