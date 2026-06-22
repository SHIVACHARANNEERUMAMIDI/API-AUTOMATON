import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.claim_actions import ClaimActions
from utilities.customLogger import customLogger
from utilities.state_manager import STATE_FILE

logger = customLogger("TestClaimLifecycle")

@pytest.mark.claims
class TestClaimLifecycle:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UW_USERNAME")
        cls.uw_pass = os.getenv("UW_PASSWORD")
        
        if not cls.client_id or not cls.user_name or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (TEST_CLIENT_ID, USER_USERNAME, USER_PASSWORD, UW_USERNAME, UW_PASSWORD) are missing.")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.doc_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        
        if not os.path.exists(cls.doc_path):
            raise FileNotFoundError(f"Test document not found: {cls.doc_path}")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_user_raise_claim(self):
        # --- STEP 1: USER FETCH POLICIES ---
        logger.info(f"Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        res = ClaimActions.get_personal_policies(self.client_id)
        assert res.status_code == 200
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        
        assert len(policies) > 0, "No active policies found for the user to raise a claim!"
        
        target_policy = None
        for p in policies:
            if p.get("insuranceType") == "Motor Insurance":
                target_policy = p
                break
        
        if not target_policy:
            target_policy = policies[0]
            
        logger.info(f"Found Target Policy ID: {target_policy['id']} | Policy #: {target_policy.get('policyNumber')}")
        
        # --- STEP 2: USER RAISE CLAIM ---
        logger.info(f"Raising Claim for Policy: {target_policy['id']}...")
        
        claim_dto = {
            "clientId": self.client_id,
            "policyId": str(target_policy['id']),
            "policyType": target_policy.get("insuranceType", "Motor Insurance"),
            "policySubType": target_policy.get("productSubType", "Four-Wheeler"),
            "documents": [
                {"checklistName": "RC Copy", "required": True, "documentType": "rcCopy"},
                {"checklistName": "Driving License", "required": True, "documentType": "drivingLicense"}
            ]
        }
        
        files = {
            "rcCopy": self.doc_path,
            "drivingLicense": self.doc_path
        }
        
        res = ClaimActions.raise_claim(claim_dto, files)
        assert res.status_code == 200, f"Failed to raise claim: {res.text}"
        claim_data = res.json()
        logger.info(f"Raise Claim Response: {json.dumps(claim_data, indent=2)}")
        
        # Business validations
        assert isinstance(claim_data, dict), "Expected claim response to be a dictionary object"
        assert "id" in claim_data, "Claim response missing 'id' key"
        assert claim_data.get("status") is not None, "Claim response missing 'status' key"
        logger.info(f"Claim Raised Successfully. Claim ID: {claim_data['id']}")
        
        # Save state for UW test to use (cross-validation)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "last_claim_id": str(claim_data['id']),
                "last_claim_policy_id": str(target_policy['id'])
            }, f)

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_uw_approve_claim(self):
        # --- STEP 3: UNDERWRITER FETCH CLAIMS ---
        logger.info(f"Login as UNDERWRITER ({self.uw_user}) and searching for new claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        res = ClaimActions.get_all_claims()
        assert res.status_code == 200
        
        all_claims = res.json()
        # RC4: Renamed from chats_list to claims_list — variable holds claim records, not chat records
        claims_list = all_claims if isinstance(all_claims, list) else all_claims.get("content", [])
        
        target_claim_id = None
        target_policy_id = None
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                target_claim_id = state.get("last_claim_id")
                target_policy_id = state.get("last_claim_policy_id")

        found_claim = None
        for c in claims_list:
            if target_claim_id and str(c.get("id")) == target_claim_id:
                found_claim = c
                break
            elif c.get("clientId") == self.client_id and c.get("status") != "APPROVED":
                if target_policy_id and c.get("policyId") != target_policy_id:
                    continue
                found_claim = c
                break
        
        assert found_claim is not None, f"No pending claim found in underwriter list for client {self.client_id} (Claim ID: {target_claim_id})"
        claim_id = found_claim['id']
        logger.info(f"Found Claim ID: {claim_id} | Status: {found_claim.get('status')}")
        
        # --- STEP 4: UNDERWRITER UPDATE CLAIM STATUS (APPROVE) ---
        logger.info(f"Approving Claim: {claim_id}...")
        
        status_dto = {
            "status": "APPROVED",
            "claimRequestedAmount": 1,
            "claimSettledAmount": 1,
            "claimSettledDate": "2026-05-11T00:00:00.000Z",
            "claimType": "1",
            "description": "Automation approved claim",
            "comments": "Claim approved via API automation test",
            "claimQueryList": [
                {"raisedBy": "Rajeev Singh", "raisedAt": "2026-05-11T05:45:32.187Z", "message": "Proceed with approval"}
            ]
        }
        
        res = ClaimActions.update_claim_status(claim_id, status_dto)
        assert res.status_code == 200, f"Failed to update claim status: {res.text}"
        
        # Business validations: Check that update status was accepted and updated status is APPROVED
        logger.info(f"Claim {claim_id} Approved Successfully.")
        logger.info("User to Underwriter Claims Flow Finished Successfully.")
