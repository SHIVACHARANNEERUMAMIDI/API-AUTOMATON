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

def get_task_id_for_user(token, target_user):
    page = 0
    while page < 5:
        query = """
        query GetUnderWriterTasks {
          getUnderWriterTasks(page: %d, size: 100) {
            content {
              id
              userDetails {
                userName
              }
            }
          }
        }
        """ % page
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        res = requests.post(PAISAPLAN_BASE_URL, json={"query": query}, headers=headers)
        data = res.json()
        tasks = data.get('data', {}).get('getUnderWriterTasks', {}).get('content', [])
        if not tasks:
            break
        for t in tasks:
            if t.get('userDetails', {}).get('userName') == target_user:
                return t['id']
        page += 1
    return None

def check_and_fix_task_state(token, target_user):
    print(f"Checking state for user {target_user}...")
    
    # Check if task exists and its state
    query = """
    query GetUnderWriterTicketByClientId($clientId: String!) {
      getUnderWriterTicketByClientId(clientId: $clientId) {
        success
        underWriterTask {
          id
          isClaimed
          claimedBy {
            userName
          }
        }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    res = requests.post(PAISAPLAN_BASE_URL, json={"query": query, "variables": {"clientId": target_user}}, headers=headers)
    data = res.json().get('data', {}).get('getUnderWriterTicketByClientId', {})
    task_data = data.get('underWriterTask')
    
    if not task_data:
        print("No task found for user.")
        return False
    
    task_id = task_data.get('id')
    if task_data.get('isClaimed'):
        print(f"Task {task_id} is already claimed by {task_data.get('claimedBy', {}).get('userName')}")
        return True
    
    print(f"Task {task_id} is NOT claimed. Attempting to claim...")
    mutation = """
    mutation SaveUnderWriterTask($claim: Boolean!, $status: UnderWriterTaskStatus!, $id: String!) {
      saveUnderWriterTask(claim: $claim, status: $status, id: $id) {
        id
        isClaimed
      }
    }
    """
    variables = {
        "claim": True,
        "status": "IN_PROGRESS",
        "id": str(task_id)
    }
    res = requests.post(PAISAPLAN_BASE_URL, json={"query": mutation, "variables": variables}, headers=headers)
    result = res.json()
    if 'errors' in result:
        print(f"FAILED to claim: {json.dumps(result['errors'], indent=2)}")
        return False
    
    print("Successfully claimed task.")
    return True

if __name__ == "__main__":
    try:
        print("Authenticating as Underwriter...")
        token = get_token(UW_USERNAME, UW_PASSWORD)
        check_and_fix_task_state(token, "919573464433")
    except Exception as e:
        print(f"Error: {e}")
