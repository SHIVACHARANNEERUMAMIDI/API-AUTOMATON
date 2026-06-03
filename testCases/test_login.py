import os
import sys
import pytest
# Add current directory to path
sys.path.append(os.getcwd())

from utilities.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.login
class TestLogin:
    def test_login(self):
        username = os.getenv("USER_USERNAME")
        password = os.getenv("USER_PASSWORD")
        print(f"Testing login for {username}...")
        API_CLIENT.set_credentials(username, password)
        headers = API_CLIENT._get_headers(include_auth=True)
        token = headers.get("Authorization", "")
        assert token, "Login FAILED: No Authorization token in headers"
        assert token.startswith("Bearer "), "Token should start with Bearer prefix"
        print(f"Token obtained successfully: {token[:20]}...")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
