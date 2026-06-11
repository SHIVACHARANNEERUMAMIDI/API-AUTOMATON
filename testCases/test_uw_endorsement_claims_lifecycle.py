import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.claim_actions import ClaimActions
from utilities.customLogger import customLogger

logger = customLogger("TestEndorsementClaimsLifecycle")

@pytest.mark.endorsement
class TestEndorsementClaimsLifecycle:
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
        cls.file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        if not os.path.exists(cls.file_path):
            raise FileNotFoundError(f"Mock document not found at: {cls.file_path}")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_user_raise_endorsement_claim(self):
        logger.info(f"Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        res = ClaimActions.get_personal_policies(self.client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE")
        assert res.status_code == 200, f"Failed to fetch policies: {res.text}"
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        assert len(policies) > 0, "No active policies found for the user."
        
        target_policy = policies[0]
        policy_id = target_policy['id']
        insurance_type = target_policy.get('insuranceType', 'Health Insurance')
        product_sub_type = target_policy.get('productSubType', 'General')
        logger.info(f"Target Policy ID: {policy_id} | Type: {insurance_type}")

        # [STEP 2] Raise Claim (Endorsement)
        logger.info(f"Raising Claim for Policy ID: {policy_id}...")
        
        dto = {
            "clientId": self.client_id,
            "policyId": policy_id,
            "policyType": insurance_type,
            "policySubType": product_sub_type,
            "documents": [
                {"checklistName": "Duly filled and signed Claim form", "required": True, "documentType": "claimForm"},
                {"checklistName": "Insurance Card or Policy Copy", "required": True, "documentType": "policyCopy"},
                {"checklistName": "Medical Certificate signed by the doctor", "required": True, "documentType": "medicalCertificate"},
                {"checklistName": "Original discharge summary", "required": True, "documentType": "dischargeSummary"},
                {"checklistName": "Original consolidated final bill", "required": True, "documentType": "consolidatedBill"},
                {"checklistName": "Break ups required for the submitted final bill", "required": True, "documentType": "breakUpBill"},
                {"checklistName": "Cash paid receipts of hospital/pharmacy/lab", "required": True, "documentType": "cashReceipts"},
                {"checklistName": "Supportive investigation reports", "required": True, "documentType": "investigationReports"},
                {"checklistName": "Bank details of payee name with printed", "required": True, "documentType": "bankDetailsOfPayee"}
            ]
        }
        
        document_types = [
            "claimForm", "policyCopy", "medicalCertificate", "dischargeSummary", 
            "consolidatedBill", "breakUpBill", "cashReceipts", "investigationReports", "bankDetailsOfPayee"
        ]
        
        claim_files = {doc_type: self.file_path for doc_type in document_types}
        res = ClaimActions.raise_claim(dto, claim_files)
        
        assert res.status_code == 200, f"Claim submission failed: {res.text}"
        claim_data = res.json()
        assert isinstance(claim_data, dict), "Expected claim response to be a dictionary object"
        assert "id" in claim_data, "Claim response missing 'id' key"
        assert "status" in claim_data, "Claim response missing 'status' key"
        logger.info(f"Claim Submitted Successfully. Claim ID: {claim_data['id']}")

        # Save claim ID to state for UW processing
        state_path = os.path.join(os.path.dirname(self.file_path), "Logs", "last_endorsement_claim_state.json")
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump({"last_endorsement_claim_id": str(claim_data['id'])}, f)

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_uw_approve_endorsement_claim(self):
        # [STEP 3] Login as UNDERWRITER and Search for the Claim
        logger.info(f"Login as UNDERWRITER ({self.uw_user}) and searching for claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        res = ClaimActions.get_all_claims(page=0, size=10)
        assert res.status_code == 200, f"Failed to fetch claims: {res.text}"
        all_claims = res.json().get("content", [])
        
        state_path = os.path.join(os.path.dirname(self.file_path), "Logs", "last_endorsement_claim_state.json")
        target_claim_id = None
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                state = json.load(f)
                target_claim_id = state.get("last_endorsement_claim_id")

        target_claim = None
        for claim in all_claims:
            if target_claim_id and str(claim.get("id")) == target_claim_id:
                target_claim = claim
                break
            elif claim.get("clientId") == self.client_id and claim.get("status") != "APPROVED":
                target_claim = claim
                break
        
        if not target_claim:
             target_claim = next((claim for claim in all_claims if claim.get("clientId") == self.client_id), None)

        assert target_claim is not None, f"Could not find a claim for client {self.client_id} (Claim ID: {target_claim_id})"
        claim_id = target_claim['id']
        logger.info(f"Found Claim ID: {claim_id} | Status: {target_claim.get('status')}")

        # [STEP 4] Underwriter Approve Claim
        logger.info(f"Approving Claim ID: {claim_id}...")
        
        status_payload = {
            "status": "APPROVED",
            "claimRequestedAmount": 1,
            "claimSettledAmount": 1,
            "claimSettledDate": "2026-05-11T00:00:00.000Z",
            "claimType": "1",
            "description": "Approved via automation",
            "comments": "Endorsement claim verified",
            "claimQueryList": [
                {
                    "raisedBy": "Rajeev Singh",
                    "raisedAt": "2026-05-11T06:43:45.712Z",
                    "message": ""
                }
            ]
        }
        
        res = ClaimActions.update_claim_status(claim_id, status_payload)
        assert res.status_code == 200, f"Claim approval failed: {res.text}"
        logger.info(f"Claim {claim_id} Approved Successfully.")
        
        # [VERIFY] Final check - Business validation
        logger.info("Checking final status of the claim...")
        res = ClaimActions.get_all_claims(page=0, size=10)
        all_claims_final = res.json().get("content", [])
        updated_claim = next((c for c in all_claims_final if c['id'] == claim_id), None)
        assert updated_claim is not None, f"Could not find claim {claim_id} in final check"
        assert updated_claim['status'] == "APPROVED", f"Status mismatch! Expected APPROVED but got {updated_claim['status']}"
        logger.info(f"Verification Successful: Claim {claim_id} is now APPROVED.")
