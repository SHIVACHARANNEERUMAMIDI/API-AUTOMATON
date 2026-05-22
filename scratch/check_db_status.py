import os
import sys
import json
# Add current directory to path
sys.path.append(os.getcwd())

from utils.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

def check_policy_by_id():
    # The policy ID we found in the last successful run
    policy_id = 1494281726984990720 
    uw_username = os.getenv("UW_USERNAME")
    uw_password = os.getenv("UW_PASSWORD")

    print(f"Checking DB Status for Policy ID: {policy_id} using Underwriter: {uw_username}...")
    
    # Login as Underwriter
    API_CLIENT.set_credentials(uw_username, uw_password)
    
    query = """
    query getPolicyDetails($id: String!) {
      getPolicyDetails(id: $id) {
        policy {
          id
          policyNumber
          status
          clientId
          insuranceType
        }
        agentComments
      }
    }
    """
    variables = {"id": str(policy_id)}
    
    res = API_CLIENT.post_graphql(query, variables)
    if res.status_code == 200:
        data = res.json().get("data", {}).get("getPolicyDetails", {})
        policy = data.get("policy")
        if not policy:
            print(f"No policy found for ID: {policy_id}")
            print(f"Full Response: {json.dumps(res.json(), indent=2)}")
        else:
            print(f"Policy Details:")
            print(f" - ID: {policy['id']}")
            print(f" - Status: {policy['status']}")
            print(f" - Client ID: {policy['clientId']}")
            print(f" - Policy #: {policy['policyNumber']}")
            print(f" - Insurance Type: {policy['insuranceType']}")
            print(f" - Agent Comments: {data.get('agentComments')}")
    else:
        print(f"Failed to fetch policy details: {res.text}")

if __name__ == "__main__":
    check_policy_by_id()
