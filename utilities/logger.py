import os
import json
import datetime

LOG_DIR = "Logs"


def log_api_call(method, url, request_payload=None, response=None, params=None):
    """
    Logs an API call with its request (Before) and response (After).
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Strip query params and sanitize for Windows filenames
    base_endpoint = url.split("/")[-1].split("?")[0] or "api"
    import re
    endpoint_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_endpoint)
    log_file = os.path.join(LOG_DIR, f"{endpoint_name}_{timestamp}.log")
    
    with open(log_file, "w") as f:
        f.write("=== API CALL LOG ===\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Method: {method}\n")
        f.write(f"URL: {url}\n")
        if params:
            f.write(f"Query Params: {json.dumps(params, indent=2)}\n")
        
        f.write("\n--- BEFORE (Request Payload) ---\n")
        if request_payload:
            f.write(json.dumps(request_payload, indent=2))
        else:
            f.write("No payload sent (GET or Multipart)")
        
        f.write("\n\n--- AFTER (Response) ---\n")
        if response is not None:
            f.write(f"Status Code: {response.status_code}\n")
            if response.status_code == 200:
                f.write("[Response Body omitted for successful 200 status]\n")
            else:
                try:
                    f.write(json.dumps(response.json(), indent=2))
                except:
                    f.write(response.text[:1000]) # Fallback to text
        else:
            f.write("No response received.")
    
    print(f"[LOG] API interaction saved to: {log_file}")
