import pytest
import os
import json
import time
from utils.api_client import API_CLIENT
from actions.endorsement_actions import raise_endorsement, get_endorsement_tickets, submit_endorsement
from actions.policy_actions import get_personal_policies
from dotenv import load_dotenv

load_dotenv()

class TestEndorsementVariants:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UW_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UW_PASSWORD", "Test@1234")
        
        # Ensure a dummy PDF exists for uploads
        cls.dummy_pdf = "endorsement_proof.pdf"
        with open(cls.dummy_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%dummy pdf content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.dummy_pdf):
            os.remove(cls.dummy_pdf)

    def _get_working_policy(self):
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        res = get_personal_policies(self.client_id)
        policies = res.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        if not policies:
            pytest.fail("No active policies found for the user.")
        return policies[0]

    def test_add_member_endorsement_flow(self):
        """
        Flow: User raises 'IND_POLICY_MEMBER_ADD_DELETE' (Add Member) -> Underwriter approves.
        """
        policy = self._get_working_policy()
        print(f"\n[STEP 1] Raising Member Addition Endorsement for Policy {policy['id']}...")
        
        metadata = {
            "firstName": "John",
            "lastName": "Doe",
            "relationType": "SPOUSE",
            "dateOfBirth": "01-01-1990",
            "sumInsured": "500000",
            "action": "add"
        }
        
        res = raise_endorsement(
            client_id=self.client_id,
            policy_id=policy['id'],
            endorsement_type="IND_POLICY_MEMBER_ADD/DELETE",
            metadata=metadata
        )
        
        res_json = res.json()
        assert "errors" not in res_json, f"Failed to raise endorsement: {res_json}"
        request_id = res_json["data"]["saveEndorsementData"]["requestTypeId"]
        print(f"Endorsement Request Raised. ID: {request_id}")

        print("Waiting 5s for sync...")
        time.sleep(5)

        # [STEP 2] Underwriter processes the ticket
        print(f"[STEP 2] Underwriter ({self.uw_user}) processing ticket...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        tickets_res = get_endorsement_tickets(endorsement_tab="PENDING")
        tickets = tickets_res.json()["data"]["getEndorsementTickets"]["content"]
        
        # Discover the real ticket ID
        ticket = tickets[0] # Assuming the latest is ours
        ticket_id = ticket["id"]
        print(f"Discovered Ticket ID: {ticket_id}")

        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "clientId": self.client_id,
                "agentComments": "Testing with POLICY_CORRECTION"
            }
        }

        submit_res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Submission failed: {submit_res.text}"
        print(f"Member Addition Endorsement Successful: {submit_res.json()}")

    def test_member_details_correction_flow(self):
        """
        Flow: User raises 'IND_POLICY_MEMBER_DETAILS_CORRECTION' -> Underwriter approves.
        """
        policy = self._get_working_policy()
        print(f"\n[STEP 1] Raising Member Details Correction for Policy {policy['id']}...")
        
        metadata = {
            "firstName": "John",
            "lastName": "Doe",
            "existingError": "Wrong DOB",
            "newModification": "Corrected DOB 1990-05-05",
            "action": "Update"
        }
        
        res = raise_endorsement(
            client_id=self.client_id,
            policy_id=policy['id'],
            endorsement_type="IND_POLICY_MEMBER_DETAILS_CORRECTION",
            metadata=metadata
        )
        
        res_json = res.json()
        assert "errors" not in res_json, f"Failed to raise endorsement: {res_json}"
        request_id = res_json["data"]["saveEndorsementData"]["requestTypeId"]
        print(f"Correction Request Raised. ID: {request_id}")

        print("Waiting 5s for sync...")
        time.sleep(5)

        # [STEP 2] Underwriter processes the ticket
        print(f"[STEP 2] Underwriter processing ticket...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        tickets_res = get_endorsement_tickets(endorsement_tab="PENDING")
        ticket_id = tickets_res.json()["data"]["getEndorsementTickets"]["content"][0]["id"]
        
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "DETAILS_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "policyId": policy['id'],
                "clientId": self.client_id,
                "insuranceType": policy['insuranceType'],
                "agentComments": "Details correction approved by automation"
            }
        }

        submit_res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.dummy_pdf
        )
        
        assert submit_res.status_code == 200, f"Submission failed: {submit_res.text}"
        print(f"Member Details Correction Successful: {submit_res.json()}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
