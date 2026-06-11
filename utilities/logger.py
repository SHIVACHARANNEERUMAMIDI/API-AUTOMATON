import os
import json
import datetime
import re
import traceback

LOG_DIR = "Logs"


def log_api_call(method, url, request_payload=None, response=None, params=None):
    """
    Logs an API call with its request (Before) and response (After).
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # Strip query params and sanitize for Windows filenames
    base_endpoint = url.split("/")[-1].split("?")[0] or "api"
    endpoint_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_endpoint)
    log_file = os.path.join(LOG_DIR, f"{endpoint_name}_{timestamp}.log")
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== API CALL LOG ===\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n")
        if params:
            f.write(f"Query Params: {json.dumps(params, indent=2)}\n")
        
        f.write("\n--- BEFORE (Request Payload) ---\n")
        if request_payload:
            if isinstance(request_payload, (dict, list)):
                f.write(json.dumps(request_payload, indent=2))
            else:
                f.write(str(request_payload))
        else:
            f.write("No payload sent (GET or Multipart)")
        
        f.write("\n\n--- AFTER (Response) ---\n")
        if response is not None:
            f.write(f"Status Code: {response.status_code}\n")
            if response.status_code in [200, 201]:
                # Log response body only if explicitly requested, or log generic info for successes
                f.write(f"[Response Body omitted for successful {response.status_code} status]\n")
                try:
                    f.write(f"Headers: {json.dumps(dict(response.headers), indent=2)}\n")
                except:
                    pass
            else:
                # Capture failed response bodies
                try:
                    f.write("Response Body:\n")
                    f.write(json.dumps(response.json(), indent=2))
                except:
                    f.write(response.text[:2000]) # Fallback to text
        else:
            f.write("No response received.")
    
    # Avoid print statements, this will be handled via logger.info in api_client.py


def log_api_error(method, url, request_payload=None, exception=None, params=None):
    """
    Logs a failed API call where an exception occurred.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    base_endpoint = url.split("/")[-1].split("?")[0] or "api"
    endpoint_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_endpoint)
    log_file = os.path.join(LOG_DIR, f"{endpoint_name}_{timestamp}_ERROR.log")
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== API CALL ERROR LOG ===\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n")
        if params:
            f.write(f"Query Params: {json.dumps(params, indent=2)}\n")
            
        f.write("\n--- BEFORE (Request Payload) ---\n")
        if request_payload:
            if isinstance(request_payload, (dict, list)):
                f.write(json.dumps(request_payload, indent=2))
            else:
                f.write(str(request_payload))
        else:
            f.write("No payload sent (GET or Multipart)")
            
        f.write("\n\n--- ERROR DETAILS ---\n")
        if exception is not None:
            f.write(f"Exception Type: {type(exception).__name__}\n")
            f.write(f"Exception Message: {str(exception)}\n")
            f.write("Traceback:\n")
            f.write(traceback.format_exc())
        else:
            f.write("Unknown execution failure.")
