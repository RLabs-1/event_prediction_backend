import requests

# Base URL of your Django application
BASE_URL = "http://127.0.0.1:8000"

# Test user credentials
TEST_EMAIL = "testuser@example.com"
TEST_NAME = "Test User"
TEST_PASSWORD = "securepassword123"

def register_user():
    """Register a new user."""
    url = f"{BASE_URL}/user/register/"
    data = {
        "email": TEST_EMAIL,
        "name": TEST_NAME,
        "password": TEST_PASSWORD,
    }
    response = requests.post(url, json=data)
    if response.status_code == 201:
        print("User registered successfully!")
        return response.json()  # Returns the user ID
    else:
        print(f"Failed to register user: {response.status_code} - {response.text}")
        return None

def login_user():
    """Log in the user and obtain JWT tokens."""
    url = f"{BASE_URL}/user/login/"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("User logged in successfully!")
        return response.json()  # Returns access and refresh tokens
    else:
        print(f"Failed to log in user: {response.status_code} - {response.text}")
        return None

def access_protected_endpoint(access_token):
    """Access a protected endpoint using the JWT token."""
    url = f"{BASE_URL}/user/current/"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Protected endpoint accessed successfully!")
        print("User data:", response.json())
    else:
        print(f"Failed to access protected endpoint: {response.status_code} - {response.text}")

def refresh_token(refresh_token):
    """Refresh the access token using the refresh token."""
    url = f"{BASE_URL}/user/refresh-token/"
    data = {
        "refresh": refresh_token,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Token refreshed successfully!")
        return response.json()  # Returns the new access token
    else:
        print(f"Failed to refresh token: {response.status_code} - {response.text}")
        return None

def main():
    # Step 1: Register a new user
    print("Registering a new user...")
    register_user()

    # Step 2: Log in the user and obtain JWT tokens
    print("Logging in the user...")
    login_response = login_user()
    if not login_response:
        return

    access_token = login_response.get("access")
    refresh_token = login_response.get("refresh")

    # Step 3: Access a protected endpoint using the access token
    print("Accessing a protected endpoint...")
    access_protected_endpoint(access_token)

    # Step 4: Refresh the access token
    print("Refreshing the access token...")
    refresh_response = refresh_token(refresh_token)
    if refresh_response:
        new_access_token = refresh_response.get("access")
        print("Using the new access token to access the protected endpoint...")
        access_protected_endpoint(new_access_token)

if __name__ == "__main__":
    main()