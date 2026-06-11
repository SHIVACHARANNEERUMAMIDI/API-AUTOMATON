import requests
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

def get_access_token(username=None, password=None):
    """
    Fetches an access token from Keycloak using password grant type.
    Fails immediately if mandatory environment variables are not configured.
    """
    token_url = os.getenv("TOKEN_URL")
    if not token_url:
        raise ValueError("Mandatory environment variable 'TOKEN_URL' is missing.")
        
    client_id = os.getenv("CLIENT_ID")
    if not client_id:
        raise ValueError("Mandatory environment variable 'CLIENT_ID' is missing.")
        
    grant_type = os.getenv("GRANT_TYPE")
    if not grant_type:
        raise ValueError("Mandatory environment variable 'GRANT_TYPE' is missing.")

    resolved_username = username or os.getenv("AUTH_USERNAME")
    if not resolved_username:
        raise ValueError(
            "Username not provided and default 'AUTH_USERNAME' environment variable is missing."
        )

    resolved_password = password or os.getenv("AUTH_PASSWORD")
    if not resolved_password:
        raise ValueError(
            "Password not provided and default 'AUTH_PASSWORD' environment variable is missing."
        )

    payload = {
        'client_id': client_id,
        'username': resolved_username,
        'password': resolved_password,
        'grant_type': grant_type
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # Disable SSL verification for dev environment
        response = requests.post(token_url, headers=headers, data=payload, verify=False, timeout=30)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        error_msg = f"[AUTH ERROR] Failed to fetch token for {payload['username']}: {e}"
        # We don't use print here anymore. Raise RuntimeError, which will be caught by tests/logger
        raise RuntimeError(error_msg)
