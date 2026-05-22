import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from utils.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

def test_login():
    username = os.getenv("USER_USERNAME")
    password = os.getenv("USER_PASSWORD")
    print(f"Testing login for {username}...")
    try:
        API_CLIENT.set_credentials(username, password)
        headers = API_CLIENT._get_headers(include_auth=True)
        token = headers.get("Authorization", "")
        if token:
            print(f"Token obtained successfully: {token[:20]}...")
        else:
            print("Login FAILED: No token in headers")
    except Exception as e:
        print(f"Login FAILED: {str(e)}")

if __name__ == "__main__":
    test_login()
