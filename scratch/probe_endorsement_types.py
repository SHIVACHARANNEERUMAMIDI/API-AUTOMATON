import os
from utils.api_client import API_CLIENT
from actions.endorsement_actions import raise_endorsement
from dotenv import load_dotenv

load_dotenv()

def probe_types():
    client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
    user_name = os.getenv("USER_USERNAME", "919573464433")
    user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
    
    API_CLIENT.set_credentials(user_name, user_pass)
    
    # Try a few variants
    types_to_try = [
        "IND_POLICY_MEMBER_ADD_DELETE",
        "INDIVIDUAL_ADDITION_DELETION",
        "ADDITION_OR_DELETION",
        "Individual Addition & Deletion",
        "POLICY_CORRECTION",
        "Policy Correction"
    ]
    
    policy_id = "1503370801215324160" # Use a known ID
    metadata = {"action": "add", "firstName": "Probe"}
    
    for t in types_to_try:
        print(f"Trying type: '{t}'...")
        res = raise_endorsement(client_id, policy_id, t, metadata)
        res_json = res.json()
        if "errors" in res_json:
            msg = res_json["errors"][0]["message"]
            print(f"  Result: FAILED - {msg}")
        else:
            print(f"  Result: SUCCESS! ID: {res_json['data']['saveEndorsementData']['requestTypeId']}")

if __name__ == "__main__":
    probe_types()
