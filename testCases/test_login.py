import os
import pytest
from utilities.api_client import API_CLIENT
from utilities.customLogger import customLogger

logger = customLogger("TestLogin")

@pytest.mark.login
class TestLogin:
    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_login(self):
        username = os.getenv("USER_USERNAME")
        password = os.getenv("USER_PASSWORD")
        if not username or not password:
            raise ValueError("Mandatory environment variables USER_USERNAME or USER_PASSWORD are missing.")
            
        logger.info(f"Testing login for {username}...")
        API_CLIENT.set_credentials(username, password)
        headers = API_CLIENT._get_headers(include_auth=True)
        token = headers.get("Authorization", "")
        
        # Business validations
        assert token, "Login FAILED: No Authorization token in headers"
        assert token.startswith("Bearer "), "Token should start with Bearer prefix"
        logger.info(f"Token obtained successfully and verified: {token[:30]}...")
