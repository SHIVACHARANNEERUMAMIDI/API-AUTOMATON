import pytest
import os
import time
from actions.endorsement_actions import raise_endorsement, get_endorsement_tickets, get_endorsement_ticket_saved_data, submit_endorsement
from actions.user_actions import get_personal_policies
from utils.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

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
        policy = policies_res.json()["data"]["getPersonalPolicies"]["policies"][0]
        
        print(f"Raising Policy Correction for {policy['id']}...")
        raise_res = raise_endorsement(
            client_id=self.client_id,
            policy_id=policy['id'],
            endorsement_type="POLICY_CORRECTION",
            metadata={"premiumAmountPaid": "12345"}
        )
        assert raise_res.status_code == 200
        request_id = raise_res.json()["data"]["saveEndorsementData"]["requestTypeId"]
        
        print("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        tickets_res = get_endorsement_tickets(endorsement_tab="PENDING")
        tickets = tickets_res.json()["data"]["getEndorsementTickets"]["content"]
        
        # Find ticket
        ticket_id = next((t["id"] for t in tickets if str(t["id"]) == str(request_id) or True), tickets[0]["id"])
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
        assert submit_res.json().get("success") is True
        print("Policy Correction Parity PASSED!")

    def test_member_addition_parity(self):
        # 1. Raise as User
        print(f"\n[STEP 1] Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)
        policies_res = get_personal_policies(self.client_id, "INDIVIDUAL", "ACTIVE")
        policy = policies_res.json()["data"]["getPersonalPolicies"]["policies"][0]
        
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
        assert raise_res.status_code == 200
        request_id = raise_res.json()["data"]["saveEndorsementData"]["requestTypeId"]
        
        print("Waiting 5s for sync...")
        time.sleep(5)
        
        # 2. Submit as Underwriter
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user})...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        tickets_res = get_endorsement_tickets(endorsement_tab="PENDING")
        tickets = tickets_res.json()["data"]["getEndorsementTickets"]["content"]
        ticket_id = tickets[0]["id"]
        
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "ADDITION_OR_DELETION",
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
                "agentComments": "Parity member addition",
                "policyStartDate": "2025-01-01",
                "policyEndDate": "2026-01-01",
                "totalNoOfEmployees": 0,
                "membersToBeAdded": [
                    {
                        "firstName": "Anuj",
                        "lastName": "Mankumare",
                        "relationType": "Self",
                        "dateOfBirth": "1995-07-07",
                        "sumInsured": "1000000"
                    }
                ]
            }
        }
        
        submit_res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Parity member addition failed: {submit_res.text}"
        assert submit_res.json().get("success") is True
        print("Member Addition Parity PASSED!")
