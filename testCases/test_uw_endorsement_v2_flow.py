import pytest
import json
import time
import os
from utilities.api_client import API_CLIENT
from dotenv import load_dotenv
from utilities.state_manager import save_state, get_state
from underwriter_api.endorsement_actions import submit_endorsement, discover_underwriter_ticket_id

load_dotenv()

@pytest.mark.endorsement
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
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "Data", "endorsement_result.pdf")
        
        if not os.path.exists(cls.file_path):
            os.makedirs(os.path.dirname(cls.file_path), exist_ok=True)
            with open(cls.file_path, "wb") as f:
                f.write(b"%PDF-1.4 test content")

    def test_user_raises_endorsement_request(self):
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
        assert res.status_code == 200, f"Failed to get personal policies: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data'"
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
        assert "insuranceType" in policy, "Policy missing 'insuranceType'"
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
        assert res.status_code == 200, f"Failed to raise endorsement: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data'"
        assert "saveEndorsementData" in res_json["data"], "Response missing 'saveEndorsementData'"
        save_data = res_json["data"]["saveEndorsementData"]
        assert isinstance(save_data, dict), "Expected saveEndorsementData to be a dict"
        ticket_id = save_data["requestTypeId"]
        assert ticket_id is not None, "saveEndorsementData missing 'requestTypeId'"
        
        # SAVE STATE
        save_state("ticketId", ticket_id)
        print(f"Endorsement Raised. Saved Ticket ID to state: {ticket_id}")

    def test_underwriter_processes_endorsement(self):
        """UNDERWRITER processes the ticket (Can be run independently)."""
        ticket_id = get_state("ticketId")
        policy_id = get_state("policyId")
        insurance_type = get_state("insuranceType")

        if not ticket_id:
            pytest.fail("No ticketId found in state. Run Step 1 first or provide one manually.")

        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user}) for Ticket: {ticket_id}...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)

        # Discover correct underwriter-side ticket ID
        real_ticket_id = discover_underwriter_ticket_id(self.client_id, ticket_id)
        assert real_ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {ticket_id}"

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
            ticket_id=real_ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.file_path
        )

        assert res.status_code == 200, f"Underwriter submission failed: {res.text}"
        res_json = res.json()
        assert isinstance(res_json, dict), "Expected submission response to be a dictionary"
        assert res_json.get("success") is True, f"Submission success was not True: {res_json}"
        print(f"Endorsement Lifecycle Complete for Ticket {ticket_id}!")

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
