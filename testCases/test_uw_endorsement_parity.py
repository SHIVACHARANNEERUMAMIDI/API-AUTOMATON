import pytest
import os
import time
from underwriter_api.endorsement_actions import EndorsementActions
from underwriter_api.user_actions import UserActions
from utilities.api_client import API_CLIENT
from utilities.customLogger import customLogger
from utilities.config import Config

logger = customLogger("TestEndorsementParity")

@pytest.mark.endorsement
class TestEndorsementParity:
    @classmethod
    def setup_class(cls):
        cls.user_phone = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD")
        cls.client_id = cls.user_phone
        
        if not cls.user_phone or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UNDERWRITER_USERNAME, UNDERWRITER_PASSWORD) are missing.")
            
        cls.dummy_pdf = "parity_test.pdf"
        with open(cls.dummy_pdf, "wb") as f:
            f.write(b"%PDF-1.4 parity content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.dummy_pdf):
            os.remove(cls.dummy_pdf)

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_policy_correction_parity(self):
        # 1. Raise as User
        logger.info(f"Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)
        policies_res = UserActions.get_personal_policies(self.client_id, "INDIVIDUAL", "ACTIVE")
        assert policies_res.status_code == 200, f"Failed to fetch policies: {policies_res.text}"
        res_json = policies_res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
        policy = next((p for p in policies if p.get("insuranceType") == "Health Insurance"), None)
        if not policy:
            policy = next((p for p in policies if p.get("insuranceType") == "Life Insurance"), None)
        if not policy:
            policy = policies[0]
        assert "id" in policy, "Policy missing 'id'"
        
        logger.info(f"Raising Policy Correction for {policy['id']}...")
        raise_res = EndorsementActions.raise_endorsement(
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
        
        logger.info("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        logger.info(f"Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        ticket_id = EndorsementActions.discover_underwriter_ticket_id(self.client_id, request_id)
        assert ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {request_id}"
        logger.info(f"Processing Ticket: {ticket_id}")
        
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "policyNumber": policy.get("policyNumber"),
                "clientId": self.client_id,
                "clientName": Config.USER_FULL_NAME,  # RC1: sourced from data/test_users.json
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
        
        submit_res = EndorsementActions.submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Parity submission failed: {submit_res.text}"
        submit_json = submit_res.json()
        assert isinstance(submit_json, dict), "Expected submit result to be a dictionary"
        assert submit_json.get("success") is True, f"Parity submission success was not True: {submit_json}"
        logger.info("Policy Correction Parity PASSED!")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_member_addition_parity(self):
        # 1. Raise as User
        logger.info(f"Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)
        policies_res = UserActions.get_personal_policies(self.client_id, "INDIVIDUAL", "ACTIVE")
        assert policies_res.status_code == 200, f"Failed to fetch policies: {policies_res.text}"
        res_json = policies_res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
        policy = next((p for p in policies if p.get("insuranceType") == "Health Insurance"), None)
        if not policy:
            policy = next((p for p in policies if p.get("insuranceType") == "Life Insurance"), None)
        if not policy:
            policy = policies[0]
        assert "id" in policy, "Policy missing 'id'"
        
        logger.info(f"Raising Member Addition for {policy['id']}...")
        metadata = {
            "empId": self.client_id,
            "firstName": "Parity", "lastName": "User", 
            "relationType": "SPOUSE", "dateOfBirth": "01-01-1995", 
            "sumInsured": "100000", "action": "add"
        }
        raise_res = EndorsementActions.raise_endorsement(
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
        
        logger.info("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        logger.info(f"Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        ticket_id = EndorsementActions.discover_underwriter_ticket_id(self.client_id, request_id)
        assert ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {request_id}"
        logger.info(f"Processing Ticket: {ticket_id}")
        
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "clientId": self.client_id,
                "agentComments": "Parity member addition"
            }
        }
        
        submit_res = EndorsementActions.submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Parity member addition failed: {submit_res.text}"
        submit_json = submit_res.json()
        assert isinstance(submit_json, dict), "Expected submit result to be a dictionary"
        assert submit_json.get("success") is True, f"Parity member addition success was not True: {submit_json}"
        logger.info("Member Addition Parity PASSED!")
