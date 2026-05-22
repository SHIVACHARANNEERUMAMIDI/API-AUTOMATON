import os
import json
import pytest
import time
from utils.api_client import API_CLIENT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestClaimRejectionFlow:
    """
    Test suite for the End-to-End Underwriter Claim REJECTION flow.
    Workflow:
    1. Login as USER.
    2. Raise a claim for an active policy.
    3. Login as UNDERWRITER.
    4. Find the claim.
    5. Reject the claim.
    """

    @classmethod
    def setup_class(cls):
        # Configuration
        cls.client_id = os.getenv("USER_USERNAME", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD", "Test@1234")
        
        # Use a dummy file for claim documents
        cls.file_path = "claim_rejection_doc.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy claim rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    def test_claim_rejection_lifecycle(self):
        # [STEP 1] Login as USER and Fetch Policies
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        get_policies_query = """
        query getPersonalPolicies($clientId: String, $clientType: ClientType, $expiryType: ExpiryType, $year: String, $insuranceType: String, $insuranceSubType: String) {
          getPersonalPolicies(
            clientId: $clientId
            clientType: $clientType
            expiryType: $expiryType
            year: $year
            insuranceType: $insuranceType
            insuranceSubType: $insuranceSubType
          ) {
            policies {
              id
              policyNumber
              insuranceType
              productSubType
            }
          }
        }
        """
        variables = {
            "clientId": self.client_id,
            "clientType": "INDIVIDUAL",
            "expiryType": "ACTIVE",
            "year": "",
            "insuranceType": "",
            "insuranceSubType": ""
        }
        res = API_CLIENT.post_graphql(get_policies_query, variables)
        assert res.status_code == 200, f"Failed to fetch policies: {res.text}"
        policies = res.json()["data"]["getPersonalPolicies"]["policies"]
        assert len(policies) > 0, "No active policies found for user."
        
        target_policy = policies[0]
        policy_id = target_policy['id']
        print(f"Target Policy ID: {policy_id} | Type: {target_policy['insuranceType']}")

        # [STEP 2] Raise Claim
        print(f"[STEP 2] Raising Claim for Policy ID: {policy_id}...")
        
        dto = {
            "clientId": self.client_id,
            "policyId": policy_id,
            "policyType": target_policy['insuranceType'],
            "policySubType": target_policy.get('productSubType', 'General'),
            "documents": [
                {"checklistName": "Duly filled and signed Claim form", "required": True, "documentType": "claimForm"}
            ],
            "comments": "Automated Claim for Rejection Test",
            "description": "This claim will be rejected by automation."
        }
        
        with open(self.file_path, "rb") as f:
            file_content = f.read()
            files = {
                "claimForm": ("claimForm.pdf", file_content, "application/pdf"),
                "type": (None, "Submit", "application/json"),
                "dto": (None, json.dumps(dto), "application/json")
            }
            res = API_CLIENT.post_multipart("claims", files=files, data={})
        
        assert res.status_code == 200, f"Claim submission failed: {res.text}"
        print("Claim Submitted Successfully.")
        
        # [STEP 3] Login as UNDERWRITER and Search for the Claim
        print(f"\n[STEP 3] Login as UNDERWRITER ({self.uw_user}) and searching for claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        # Get All Claims
        res = API_CLIENT.get_rest("claims/getAllClaims", params={"page": 0, "size": 10})
        assert res.status_code == 200, f"Failed to fetch claims: {res.text}"
        all_claims = res.json().get("content", [])
        
        # Find our claim (latest one for our client)
        target_claim = next((c for c in all_claims if c.get("clientId") == self.client_id), None)
        assert target_claim is not None, f"Could not find a claim for client {self.client_id}"
        
        claim_id = target_claim['id']
        print(f"Found Claim ID: {claim_id} | Current Status: {target_claim.get('status')}")

        # [STEP 4] Underwriter REJECT Claim
        print(f"\n[STEP 4] Rejecting Claim ID: {claim_id}...")
        
        status_payload = {
            "status": "REJECTED", # KEY CHANGE: REJECTED instead of APPROVED
            "comments": "REJECTED BY AUTOMATION: Duplicate claim request detected.",
            "description": "Automated rejection for test purposes.",
            "clientId": self.client_id
        }
        
        endpoint = f"claims/{claim_id}/statusUpdate"
        # We use _request with PUT as seen in the core app service logic
        res = API_CLIENT._request("PUT", f"{API_CLIENT.paisaplan_base.rstrip('/')}/{endpoint}", json=status_payload)
        
        assert res.status_code == 200, f"Claim rejection failed: {res.text}"
        res_json = res.json()
        print(f"Server Response: {res_json}")
        print(f"Claim {claim_id} REJECTED Successfully.")
        
        # [VERIFY] Final check
        print("\n[VERIFY] Checking final status of the claim...")
        res = API_CLIENT.get_rest("claims/getAllClaims", params={"page": 0, "size": 10})
        all_claims_final = res.json().get("content", [])
        updated_claim = next((c for c in all_claims_final if c['id'] == claim_id), None)
        assert updated_claim['status'] == "REJECTED", f"Status mismatch! Expected REJECTED but got {updated_claim['status']}"
        print(f"Verification Successful: Claim {claim_id} is now REJECTED.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
