import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.claim_actions import get_personal_policies, raise_claim, get_all_claims, update_claim_status
from dotenv import load_dotenv
from utilities.state_manager import STATE_FILE


load_dotenv()

class TestUserToUwClaimsFlow:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UW_USERNAME")
        cls.uw_pass = os.getenv("UW_PASSWORD")
        
        # Files for claim
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.doc_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        
        if not os.path.exists(cls.doc_path):
            raise FileNotFoundError(f"Test document not found: {cls.doc_path}")

    def test_01_user_raise_claim(self):
        # --- STEP 1: USER FETCH POLICIES ---
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        res = get_personal_policies(self.client_id)
        assert res.status_code == 200
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        
        assert len(policies) > 0, "No active policies found for the user to raise a claim!"
        
        # Pick the Motor Insurance policy we just activated (or the first one)
        target_policy = None
        for p in policies:
            if p.get("insuranceType") == "Motor Insurance":
                target_policy = p
                break
        
        if not target_policy:
            target_policy = policies[0]
            
        print(f"Found Target Policy ID: {target_policy['id']} | Policy #: {target_policy.get('policyNumber')}")
        
        # --- STEP 2: USER RAISE CLAIM ---
        print(f"\n[STEP 2] Raising Claim for Policy: {target_policy['id']}...")
        
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
        
        res = raise_claim(claim_dto, files)
        assert res.status_code == 200, f"Failed to raise claim: {res.text}"
        print(f"DEBUG: Raise Claim Response: {json.dumps(res.json(), indent=2)}")
        print("Claim Raised Successfully.")
        
        # Save state for UW test to use if needed (optional tracking)
        with open(STATE_FILE, "w") as f:
            json.dump({"last_claim_policy_id": str(target_policy['id'])}, f)

    def test_02_uw_approve_claim(self):
        # --- STEP 3: UNDERWRITER FETCH CLAIMS ---
        print(f"\n[STEP 3] Login as UNDERWRITER ({self.uw_user}) and searching for new claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        res = get_all_claims()
        assert res.status_code == 200
        
        all_claims = res.json()
        claims_list = all_claims if isinstance(all_claims, list) else all_claims.get("content", [])
        
        # Try to read policy_id from state file, otherwise just find any pending claim for the user
        target_policy_id = None
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                target_policy_id = state.get("last_claim_policy_id")

        found_claim = None
        for c in claims_list:
            # We look for a claim that belongs to the user and is not yet approved
            if c.get("clientId") == self.client_id and c.get("status") != "APPROVED":
                if target_policy_id and c.get("policyId") != target_policy_id:
                    continue
                found_claim = c
                break
        
        assert found_claim is not None, f"No pending claim found in underwriter list for client {self.client_id}"
        claim_id = found_claim['id']
        print(f"Found Claim ID: {claim_id} | Status: {found_claim.get('status')}")
        
        # --- STEP 4: UNDERWRITER UPDATE CLAIM STATUS (APPROVE) ---
        print(f"\n[STEP 4] Approving Claim: {claim_id}...")
        
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
        
        res = update_claim_status(claim_id, status_dto)
        assert res.status_code == 200, f"Failed to update claim status: {res.text}"
        print(f"Claim {claim_id} Approved Successfully.")
        
        print("\n[FLOW COMPLETE] User to Underwriter Claims Flow Finished Successfully.")
