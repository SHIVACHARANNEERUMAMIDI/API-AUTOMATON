import requests
import os
from dotenv import load_dotenv

# Load environment variables from Configurations/.env file
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), "Configurations", ".env")
load_dotenv(dotenv_path=env_path)


def get_access_token(username=None, password=None):
    """
    Fetches an access token from Keycloak using password grant type.
    Defaults to the Underwriter credentials in .env if none provided.
    """
    url = os.getenv("TOKEN_URL")
    payload = {
        'client_id': os.getenv("CLIENT_ID"),
        'username': username or os.getenv("AUTH_USERNAME"),
        'password': password or os.getenv("AUTH_PASSWORD"),
        'grant_type': os.getenv("GRANT_TYPE")
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # Disable SSL verification for dev environment
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        error_msg = f"[AUTH ERROR] Failed to fetch token for {payload['username']}: {e}"
        print(error_msg)
        raise RuntimeError(error_msg)
