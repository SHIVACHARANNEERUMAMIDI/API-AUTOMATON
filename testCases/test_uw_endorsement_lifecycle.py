import pytest
import os
from utilities.api_client import API_CLIENT
from underwriter_api.policy_actions import PolicyActions
from underwriter_api.endorsement_actions import EndorsementActions
from utilities.customLogger import customLogger
from utilities.state_manager import save_state, get_state

logger = customLogger("TestEndorsementLifecycle")

@pytest.mark.endorsement
class TestEndorsementLifecycle:
    """
    Modular Endorsement Flow.
    Steps are independent but share ticketId via last_state.json.
    """

    @classmethod
    def setup_class(cls):
        cls.user_phone = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD")
        cls.client_id = cls.user_phone
        
        if not cls.user_phone or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UNDERWRITER_USERNAME, UNDERWRITER_PASSWORD) are missing.")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "Data", "endorsement_result.pdf")
        
        if not os.path.exists(cls.file_path):
            os.makedirs(os.path.dirname(cls.file_path), exist_ok=True)
            with open(cls.file_path, "wb") as f:
                f.write(b"%PDF-1.4 test content")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_user_raises_endorsement_request(self):
        """USER login and fetch policies, then raise endorsement."""
        logger.info(f"Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_pass)

        # 1. Fetch Policies
        res = PolicyActions.get_personal_policies(self.client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE")
        assert res.status_code == 200, f"Failed to get personal policies: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data'"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
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
        metadata = {"premiumAmountPaid": "111111111"}
        res = EndorsementActions.raise_endorsement(
            client_id=self.client_id,
            policy_id=policy["id"],
            endorsement_type="POLICY_CORRECTION",
            metadata=metadata,
            email="automation@test.com"
        )
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
        logger.info(f"Endorsement Raised. Saved Ticket ID to state: {ticket_id}")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_underwriter_processes_endorsement(self):
        """UNDERWRITER processes the ticket (Can be run independently)."""
        ticket_id = get_state("ticketId")
        policy_id = get_state("policyId")
        insurance_type = get_state("insuranceType")

        if not ticket_id:
            pytest.fail("No ticketId found in state. Run Step 1 first or provide one manually.")

        logger.info(f"Login as UNDERWRITER ({self.uw_user}) for Ticket: {ticket_id}...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)

        # Discover correct underwriter-side ticket ID
        real_ticket_id = EndorsementActions.discover_underwriter_ticket_id(self.client_id, ticket_id)
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

        # Submit using our stabilized action class
        res = EndorsementActions.submit_endorsement(
            ticket_id=real_ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.file_path
        )

        assert res.status_code == 200, f"Underwriter submission failed: {res.text}"
        res_json = res.json()
        assert isinstance(res_json, dict), "Expected submission response to be a dictionary"
        assert res_json.get("success") is True, f"Submission success was not True: {res_json}"
        logger.info(f"Endorsement Lifecycle Complete for Ticket {ticket_id}!")
