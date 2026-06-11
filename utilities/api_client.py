import requests
import os
import json
import urllib3
from dotenv import load_dotenv
from utilities.auth import get_access_token
from utilities.logger import log_api_call, log_api_error
from utilities.customLogger import customLogger

load_dotenv()


# Disable InsecureRequestWarning for dev environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class APIClient:
    def __init__(self):
        self.logger = customLogger("APIClient")
        self.paisaplan_base = os.getenv("PAISAPLAN_BASE_URL")
        self.trovity_mt_base = os.getenv("TROVITY_MT_BASE_URL")
        self.token = None
        self.custom_username = None
        self.custom_password = None

    def set_credentials(self, username, password):
        """Override default credentials for a specific test sequence."""
        self.logger.info(f"Setting override credentials for user: {username}")
        self.custom_username = username
        self.custom_password = password
        self.token = None

    def _get_headers(self, include_auth=True):
        """Build headers with mandatory X-Realm and Authorization."""
        realm = os.getenv("KEYCLOAK_REALM_NAME")
        if not realm:
            raise ValueError("Mandatory environment variable 'KEYCLOAK_REALM_NAME' is missing.")
            
        headers = {
            "X-Realm": realm,
            "Accept": "application/json"
        }
        if include_auth:
            if not self.token:
                self.token = get_access_token(self.custom_username, self.custom_password)
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method, url, **kwargs):
        """Centralized request handler with auto-token retrieval and robust logging."""
        headers = self._get_headers(include_auth=kwargs.pop("_include_auth", True))
        
        # Merge caller headers
        caller_headers = kwargs.pop("headers", None) or {}
        headers.update(caller_headers)

        # Default Content-Type for JSON POST
        if method.upper() == "POST" and "Content-Type" not in headers and "files" not in kwargs:
            headers["Content-Type"] = "application/json"

        kwargs["headers"] = headers
        kwargs["verify"] = False
        kwargs.setdefault("timeout", 60)

        self.logger.info(f"API REQUEST ---> {method.upper()} {url}")
        
        request_payload = kwargs.get("json") or kwargs.get("data")
        params = kwargs.get("params")
        
        try:
            response = requests.request(method, url, **kwargs)
            self.logger.info(f"API RESPONSE <--- {response.status_code} {url}")
            
            # Log the interaction (Before and After)
            log_api_call(
                method=method, 
                url=url, 
                request_payload=request_payload, 
                response=response,
                params=params
            )
            
            if response.status_code >= 400:
                self.logger.error(
                    f"API ERROR RESPONSE - {method} {url} -> {response.status_code}: {response.text[:1000]}"
                )
                
            return response
            
        except Exception as e:
            self.logger.error(f"HTTP REQUEST EXCEPTION - {method} {url}: {str(e)}")
            # Log failure details and exception
            log_api_error(
                method=method,
                url=url,
                request_payload=request_payload,
                exception=e,
                params=params
            )
            raise e

    def post_graphql(self, query, variables=None):
        url = self.paisaplan_base
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        return self._request("POST", url, json=payload)

    def post_multipart(self, endpoint, files=None, data=None, params=None):
        url = f"{self.paisaplan_base.rstrip('/')}/{endpoint.lstrip('/')}"
        return self._request("POST", url, files=files or {}, data=data, params=params)

    def post_rest(self, endpoint, data=None, **kwargs):
        url = f"{self.paisaplan_base.rstrip('/')}/{endpoint.lstrip('/')}"
        return self._request("POST", url, json=data, **kwargs)

    def get_rest(self, endpoint, params=None, **kwargs):
        url = f"{self.paisaplan_base.rstrip('/')}/{endpoint.lstrip('/')}"
        return self._request("GET", url, params=params, **kwargs)

    def get_mt_rest(self, endpoint, params=None, **kwargs):
        url = f"{self.trovity_mt_base.rstrip('/')}/{endpoint.lstrip('/')}"
        return self._request("GET", url, params=params, **kwargs)

    def post_mt_rest(self, endpoint, data=None, **kwargs):
        url = f"{self.trovity_mt_base.rstrip('/')}/{endpoint.lstrip('/')}"
        return self._request("POST", url, json=data, **kwargs)

API_CLIENT = APIClient()
