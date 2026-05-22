import os
import json
from utils.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

def debug_task():
    uw_name = os.getenv("UW_USERNAME")
    uw_pass = os.getenv("UW_PASSWORD")
    user_name = "919573464433"
    
    print(f"Logging in as {uw_name}...")
    API_CLIENT.set_credentials(uw_name, uw_pass)
    
    query = """
    query getUnderWriterTicketByClientId($clientId: String!) {
      getUnderWriterTicketByClientId(clientId: $clientId) {
        success
        message
        content { id claimed claimedBy { userName } }
      }
    }
    """
    res = API_CLIENT.post_graphql(query, {"clientId": user_name})
    print(f"Response Status: {res.status_code}")
    print(f"Response Body: {json.dumps(res.json(), indent=2)}")

if __name__ == "__main__":
    debug_task()
