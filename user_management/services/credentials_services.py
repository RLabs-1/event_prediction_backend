from core.model.credentials_model import Credentials

def create_credentials(access_key, secret_key, storage):
    """Handles creating and saving credentials with encryption."""
    credentials = Credentials(
        access_key=access_key,
        storage=storage
    )
    credentials.set_secret_key(secret_key)  # Encrypt secret_key
    credentials.save()
    return credentials
