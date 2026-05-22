import pytest
import json
import time
import os
from utils.api_client import API_CLIENT
from dotenv import load_dotenv
from utils.state_manager import save_state, get_state
from actions.endorsement_actions import submit_endorsement

load_dotenv()

class TestEndorsementV2Flow:
    """
    Modular Endorsement Flow.
    Steps are independent but share ticketId via last_state.json.
    """

    @classmethod
    def setup_class(cls):
        cls.user_phone = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD", "Test@1234")
        cls.client_id = cls.user_phone
        cls.file_path = "endorsement_result.pdf"
        if not os.path.exists(cls.file_path):
            with open(cls.file_path, "wb") as f:
                f.write(b"%PDF-1.4 test content")

    def test_step1_user_raises_request(self):
        """USER login and fetch policies, then raise endorsement."""
        print(f"\n[STEP 1] Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)

        # 1. Fetch Policies
        get_policies_query = """
        query getPersonalPolicies($clientId: String, $clientType: ClientType) {
          getPersonalPolicies(clientId: $clientId, clientType: $clientType, expiryType: ACTIVE) {
            policies { id insuranceType issuedOn }
          }
        }
        """
        res = API_CLIENT.post_graphql(get_policies_query, {"clientId": self.client_id, "clientType": "INDIVIDUAL"})
        policies = res.json()["data"]["getPersonalPolicies"]["policies"]
        policy = policies[0]
        save_state("policyId", policy["id"])
        save_state("insuranceType", policy["insuranceType"])

        # 2. Raise Endorsement
        mutation = """
        mutation SaveEndorsementData($input: EndorsementData!) {
          saveEndorsementData(input: $input) { requestTypeId }
        }
        """
        mutation_input = {
            "clientId": self.client_id,
            "endorsementType": "POLICY_CORRECTION",
            "policyId": policy["id"],
            "endorsementRaisedFor": self.client_id,
            "endorsementRaisedForClientType": "RETAIL_INDIVIDUAL",
            "endorsementStatus": "Request Submitted",
            "email": "automation@test.com",
            "mobileNumber": self.user_phone,
            "metadata": {"premiumAmountPaid": "111111111"}
        }
        res = API_CLIENT.post_graphql(mutation, {"input": mutation_input})
        ticket_id = res.json()["data"]["saveEndorsementData"]["requestTypeId"]
        
        # SAVE STATE
        save_state("ticketId", ticket_id)
        print(f"Endorsement Raised. Saved Ticket ID to state: {ticket_id}")

    def test_step2_underwriter_processes(self):
        """UNDERWRITER processes the ticket (Can be run independently)."""
        ticket_id = get_state("ticketId")
        policy_id = get_state("policyId")
        insurance_type = get_state("insuranceType")

        if not ticket_id:
            pytest.fail("No ticketId found in state. Run Step 1 first or provide one manually.")

        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user}) for Ticket: {ticket_id}...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)

        # Build DTO
        request_dto = {
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "clientId": self.client_id,
                "policyId": policy_id,
                "insuranceType": insurance_type,
                "agentComments": "Processed via Modular Automation",
                "totalNoOfEmployees": 0
            }
        }

        # Submit using our stabilized action
        res = submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.file_path
        )

        assert res.status_code == 200, f"Underwriter submission failed: {res.text}"
        print(f"Endorsement Lifecycle Complete for Ticket {ticket_id}!")

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
