import pytest
import os
import time
from underwriter_api.endorsement_actions import raise_endorsement, get_endorsement_tickets, get_endorsement_ticket_saved_data, submit_endorsement, discover_underwriter_ticket_id
from underwriter_api.user_actions import get_personal_policies
from utilities.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.endorsement
class TestEndorsementParity:
    @classmethod
    def setup_class(cls):
        cls.user_phone = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD", "Test@1234")
        cls.client_id = cls.user_phone
        cls.dummy_pdf = "parity_test.pdf"
        with open(cls.dummy_pdf, "wb") as f:
            f.write(b"%PDF-1.4 parity content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.dummy_pdf):
            os.remove(cls.dummy_pdf)

    def test_policy_correction_parity(self):
        # 1. Raise as User
        print(f"\n[STEP 1] Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)
        policies_res = get_personal_policies(self.client_id, "INDIVIDUAL", "ACTIVE")
        assert policies_res.status_code == 200, f"Failed to fetch policies: {policies_res.text}"
        res_json = policies_res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        # Prioritize Health Insurance, then Life Insurance, then fallback to first active policy
        policy = next((p for p in policies if p.get("insuranceType") == "Health Insurance"), None)
        if not policy:
            policy = next((p for p in policies if p.get("insuranceType") == "Life Insurance"), None)
        if not policy:
            policy = policies[0]
        assert "id" in policy, "Policy missing 'id'"
        
        print(f"Raising Policy Correction for {policy['id']}...")
        raise_res = raise_endorsement(
            client_id=self.client_id,
            policy_id=policy['id'],
            endorsement_type="POLICY_CORRECTION",
            metadata={"premiumAmountPaid": "12345"}
        )
        assert raise_res.status_code == 200, f"Failed to raise endorsement: {raise_res.text}"
        raise_json = raise_res.json()
        assert "data" in raise_json, "Response missing 'data' key"
        assert "saveEndorsementData" in raise_json["data"], "Response missing 'saveEndorsementData'"
        save_data = raise_json["data"]["saveEndorsementData"]
        assert isinstance(save_data, dict), "Expected saveEndorsementData to be a dictionary"
        request_id = save_data["requestTypeId"]
        assert request_id is not None, "saveEndorsementData missing 'requestTypeId'"
        
        print("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        # Discover correct underwriter-side ticket ID using robust lookup
        ticket_id = discover_underwriter_ticket_id(self.client_id, request_id)
        assert ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {request_id}"
        print(f"Processing Ticket: {ticket_id}")
        
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "policyNumber": policy.get("policyNumber"),
                "clientId": self.client_id,
                "clientName": "Anuj Mankumare",
                "companyName": self.client_id,
                "insuranceType": policy['insuranceType'],
                "productType": "GENERAL",
                "sumInsured": "1000000",
                "premiumPaid": "10000",
                "provider": {"id": "10", "name": "Go Digit General Insurance Ltd"},
                "agentComments": "Parity test approval",
                "policyStartDate": "2025-01-01",
                "policyEndDate": "2026-01-01",
                "totalNoOfEmployees": 0
            }
        }
        
        submit_res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Parity submission failed: {submit_res.text}"
        submit_json = submit_res.json()
        assert isinstance(submit_json, dict), "Expected submit result to be a dictionary"
        assert submit_json.get("success") is True, f"Parity submission success was not True: {submit_json}"
        print("Policy Correction Parity PASSED!")

    def test_member_addition_parity(self):
        # 1. Raise as User
        print(f"\n[STEP 1] Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)
        policies_res = get_personal_policies(self.client_id, "INDIVIDUAL", "ACTIVE")
        assert policies_res.status_code == 200, f"Failed to fetch policies: {policies_res.text}"
        res_json = policies_res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        # Prioritize Health Insurance, then Life Insurance, then fallback to first active policy
        policy = next((p for p in policies if p.get("insuranceType") == "Health Insurance"), None)
        if not policy:
            policy = next((p for p in policies if p.get("insuranceType") == "Life Insurance"), None)
        if not policy:
            policy = policies[0]
        assert "id" in policy, "Policy missing 'id'"
        
        print(f"Raising Member Addition for {policy['id']}...")
        metadata = {
            "empId": self.client_id,
            "firstName": "Parity", "lastName": "User", 
            "relationType": "SPOUSE", "dateOfBirth": "01-01-1995", 
            "sumInsured": "100000", "action": "add"
        }
        raise_res = raise_endorsement(
            client_id=self.client_id,
            policy_id=policy['id'],
            endorsement_type="IND_POLICY_MEMBER_ADD/DELETE",
            metadata=metadata
        )
        assert raise_res.status_code == 200, f"Failed to raise endorsement: {raise_res.text}"
        raise_json = raise_res.json()
        assert "data" in raise_json, "Response missing 'data' key"
        assert "saveEndorsementData" in raise_json["data"], "Response missing 'saveEndorsementData'"
        save_data = raise_json["data"]["saveEndorsementData"]
        assert isinstance(save_data, dict), "Expected saveEndorsementData to be a dictionary"
        request_id = save_data["requestTypeId"]
        assert request_id is not None, "saveEndorsementData missing 'requestTypeId'"
        
        print("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        # Discover correct underwriter-side ticket ID using robust lookup
        ticket_id = discover_underwriter_ticket_id(self.client_id, request_id)
        assert ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {request_id}"
        print(f"Processing Ticket: {ticket_id}")
        
        # Submit as Underwriter using simplified requestDto
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "clientId": self.client_id,
                "agentComments": "Parity member addition"
            }
        }
        
        submit_res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Parity member addition failed: {submit_res.text}"
        submit_json = submit_res.json()
        assert isinstance(submit_json, dict), "Expected submit result to be a dictionary"
        assert submit_json.get("success") is True, f"Parity member addition success was not True: {submit_json}"
        print("Member Addition Parity PASSED!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
