import os
import json
import pytest
import time
from utilities.api_client import API_CLIENT
from underwriter_api.claim_actions import ClaimActions
from utilities.customLogger import customLogger

logger = customLogger("TestClaimRejection")

@pytest.mark.claims
class TestClaimRejection:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("USER_USERNAME")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD")
        
        if not cls.client_id or not cls.user_name or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UNDERWRITER_USERNAME, UNDERWRITER_PASSWORD) are missing.")
        
        cls.file_path = "claim_rejection_doc.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy claim rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_claim_rejection_lifecycle(self):
        # [STEP 1] Login as USER and Fetch Policies
        logger.info(f"Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        res = ClaimActions.get_personal_policies(self.client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE")
        assert res.status_code == 200, f"Failed to fetch policies: {res.text}"
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        assert len(policies) > 0, "No active policies found for user."
        
        target_policy = policies[0]
        policy_id = target_policy['id']
        logger.info(f"Target Policy ID: {policy_id} | Type: {target_policy['insuranceType']}")

        # [STEP 2] Raise Claim
        logger.info(f"Raising Claim for Policy ID: {policy_id}...")
        
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
        
        files = {
            "claimForm": self.file_path
        }
        
        res = ClaimActions.raise_claim(dto, files)
        assert res.status_code == 200, f"Claim submission failed: {res.text}"
        logger.info("Claim Submitted Successfully.")
        
        # [STEP 3] Login as UNDERWRITER and Search for the Claim
        logger.info(f"Login as UNDERWRITER ({self.uw_user}) and searching for claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        res = ClaimActions.get_all_claims(page=0, size=10)
        assert res.status_code == 200, f"Failed to fetch claims: {res.text}"
        all_claims = res.json().get("content", [])
        
        target_claim = next((c for c in all_claims if c.get("clientId") == self.client_id), None)
        assert target_claim is not None, f"Could not find a claim for client {self.client_id}"
        
        claim_id = target_claim['id']
        logger.info(f"Found Claim ID: {claim_id} | Current Status: {target_claim.get('status')}")

        # [STEP 4] Underwriter REJECT Claim
        logger.info(f"Rejecting Claim ID: {claim_id}...")
        
        status_payload = {
            "status": "REJECTED",
            "comments": "REJECTED BY AUTOMATION: Duplicate claim request detected.",
            "description": "Automated rejection for test purposes.",
            "clientId": self.client_id
        }
        
        res = ClaimActions.update_claim_status(claim_id, status_payload)
        assert res.status_code == 200, f"Claim rejection failed: {res.text}"
        res_json = res.json()
        logger.info(f"Server Response: {res_json}")
        logger.info(f"Claim {claim_id} REJECTED Successfully.")
        
        # [VERIFY] Final check - Business validation
        logger.info("Checking final status of the claim...")
        res = ClaimActions.get_all_claims(page=0, size=10)
        all_claims_final = res.json().get("content", [])
        updated_claim = next((c for c in all_claims_final if c['id'] == claim_id), None)
        assert updated_claim is not None, f"Could not find claim {claim_id} in final check"
        assert updated_claim['status'] == "REJECTED", f"Status mismatch! Expected REJECTED but got {updated_claim['status']}"
        logger.info(f"Verification Successful: Claim {claim_id} is now REJECTED.")
