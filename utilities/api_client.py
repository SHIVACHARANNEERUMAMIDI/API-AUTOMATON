import requests
import os
import json
import urllib3
from utilities.auth import get_access_token
from utilities.logger import log_api_call


# Disable InsecureRequestWarning for dev environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class APIClient:
    def __init__(self):
        self.paisaplan_base = os.getenv("PAISAPLAN_BASE_URL")
        self.trovity_mt_base = os.getenv("TROVITY_MT_BASE_URL")
        self.token = None
        self.custom_username = None
        self.custom_password = None

    def set_credentials(self, username, password):
        """Override default credentials for a specific test sequence."""
        self.custom_username = username
        self.custom_password = password
        self.token = None

    def _get_headers(self, include_auth=True):
        """Build headers with mandatory X-Realm and Authorization."""
        headers = {
            "X-Realm": os.getenv("KEYCLOAK_REALM_NAME", "4healths"),
            "Accept": "application/json"
        }
        if include_auth:
            if not self.token:
                self.token = get_access_token(self.custom_username, self.custom_password)
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method, url, **kwargs):
        """Centralized request handler with auto-token retrieval."""
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

        print(f"\n[API REQUEST] ---> {method.upper()} {url}")
        response = requests.request(method, url, **kwargs)
        print(f"[API RESPONSE] <--- {response.status_code} {url}")

        # Log the interaction (Before and After)
        log_api_call(
            method=method, 
            url=url, 
            request_payload=kwargs.get("json") or kwargs.get("data"), 
            response=response,
            params=kwargs.get("params")
        )

        if response.status_code >= 400:
            print(f"[ERROR] {method} {url} -> {response.status_code}: {response.text[:500]}")

        return response

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
