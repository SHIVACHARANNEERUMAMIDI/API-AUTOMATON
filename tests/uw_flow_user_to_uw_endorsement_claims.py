import os
import json
import pytest
import time
from utils.api_client import API_CLIENT
from actions.claim_actions import update_claim_status
from dotenv import load_dotenv

load_dotenv()

class TestUserToUwEndorsementClaimsFlow:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UW_USERNAME")
        cls.uw_pass = os.getenv("UW_PASSWORD")
        
        # Base file path for dummy documents
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "data", "GoDigit Health Insurance 2.pdf")

    def test_01_user_raise_endorsement_claim(self):
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and fetching active policies...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # GraphQL Query: getPersonalPolicies
        query = """
        {
          getPersonalPolicies(
            clientId: "919573464433"
            clientType: INDIVIDUAL
            expiryType: ACTIVE
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
        res = API_CLIENT.post_graphql(query)
        assert res.status_code == 200, f"Failed to fetch policies: {res.text}"
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        assert len(policies) > 0, "No active policies found for the user."
        
        target_policy = policies[0]
        policy_id = target_policy['id']
        insurance_type = target_policy.get('insuranceType', 'Health Insurance')
        product_sub_type = target_policy.get('productSubType', 'General')
        print(f"Target Policy ID: {policy_id} | Type: {insurance_type}")

        # [STEP 2] Raise Claim (Endorsement)
        print(f"[STEP 2] Raising Claim for Policy ID: {policy_id}...")
        
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
        
        files = {}
        document_types = [
            "claimForm", "policyCopy", "medicalCertificate", "dischargeSummary", 
            "consolidatedBill", "breakUpBill", "cashReceipts", "investigationReports", "bankDetailsOfPayee"
        ]
        
        with open(self.file_path, "rb") as f:
            file_content = f.read()
            for doc_type in document_types:
                files[doc_type] = (f"{doc_type}.pdf", file_content, "application/pdf")
            
            # type and dto are @RequestPart in IndividualClaimsController
            files["type"] = (None, "Submit", "application/json")
            files["dto"] = (None, json.dumps(dto), "application/json")
            
            res = API_CLIENT.post_multipart("claims", files=files, data={})
        
        assert res.status_code == 200, f"Claim submission failed: {res.text}"
        print("Claim Submitted Successfully.")

    def test_02_uw_approve_endorsement_claim(self):
        # [STEP 3] Login as UNDERWRITER and Search for the Claim
        print(f"\n[STEP 3] Login as UNDERWRITER ({self.uw_user}) and searching for claim...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        # Get All Claims
        res = API_CLIENT.get_rest("claims/getAllClaims", params={"page": 0, "size": 10})
        assert res.status_code == 200, f"Failed to fetch claims: {res.text}"
        all_claims = res.json().get("content", [])
        
        # Filter claims for our client that are not yet APPROVED
        target_claim = next((claim for claim in all_claims if claim.get("clientId") == self.client_id and claim.get("status") != "APPROVED"), None)
        
        # Fallback to latest claim if none are pending
        if not target_claim:
             target_claim = next((claim for claim in all_claims if claim.get("clientId") == self.client_id), None)

        assert target_claim is not None, f"Could not find a claim for client {self.client_id}"
        claim_id = target_claim['id']
        print(f"Found Claim ID: {claim_id} | Status: {target_claim.get('status')}")

        # [STEP 4] Underwriter Approve Claim
        print(f"\n[STEP 4] Approving Claim ID: {claim_id}...")
        
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
        
        # Hit statusUpdate endpoint
        endpoint = f"claims/{claim_id}/statusUpdate"
        res = API_CLIENT._request("PUT", f"{API_CLIENT.paisaplan_base.rstrip('/')}/{endpoint}", json=status_payload)
        
        assert res.status_code == 200, f"Claim approval failed: {res.text}"
        print(f"Claim {claim_id} Approved Successfully.")
        
        # [VERIFY] Final check
        print("\n[VERIFY] Checking final status of the claim...")
        res = API_CLIENT.get_rest("claims/getAllClaims", params={"page": 0, "size": 10})
        all_claims_final = res.json().get("content", [])
        updated_claim = next((c for c in all_claims_final if c['id'] == claim_id), None)
        assert updated_claim['status'] == "APPROVED", f"Status mismatch! Expected APPROVED but got {updated_claim['status']}"
        print(f"Verification Successful: Claim {claim_id} is now APPROVED.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
