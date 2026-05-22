import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

PAISAPLAN_BASE_URL = os.getenv("PAISAPLAN_BASE_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
UW_USERNAME = os.getenv("UW_USERNAME")
UW_PASSWORD = os.getenv("UW_PASSWORD")
CLIENT_ID = os.getenv("CLIENT_ID")
GRANT_TYPE = os.getenv("GRANT_TYPE")

def get_token(username, password):
    payload = {
        'grant_type': GRANT_TYPE,
        'client_id': CLIENT_ID,
        'username': username,
        'password': password
    }
    res = requests.post(TOKEN_URL, data=payload)
    res.raise_for_status()
    return res.json()['access_token']

def claim_task(token, task_id):
    query = """
    mutation SaveUnderWriterTask($claim: Boolean!, $status: UnderWriterTaskStatus!, $id: String!) {
      saveUnderWriterTask(claim: $claim, status: $status, id: $id) {
        id
        isClaimed
        claimedBy {
          userName
        }
      }
    }
    """
    variables = {
        "claim": True,
        "status": "IN_PROGRESS",
        "id": str(task_id)
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    res = requests.post(PAISAPLAN_BASE_URL, json={"query": query, "variables": variables}, headers=headers)
    return res.json()

if __name__ == "__main__":
    try:
        print("Authenticating as Underwriter...")
        token = get_token(UW_USERNAME, UW_PASSWORD)
        
        # Task ID for user 919573464433
        # Based on previous find, it was 1483747949001724000
        task_id = 1483747949001724000 
        
        print(f"Attempting to claim task {task_id}...")
        result = claim_task(token, task_id)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
