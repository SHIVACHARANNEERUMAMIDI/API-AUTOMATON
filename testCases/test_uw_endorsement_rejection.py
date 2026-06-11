import os
import json
import time
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.endorsement_actions import EndorsementActions
from underwriter_api.policy_actions import PolicyActions
from utilities.customLogger import customLogger

logger = customLogger("TestEndorsementRejection")

@pytest.mark.endorsement
class TestEndorsementRejection:
    """
    Test suite for the End-to-End Underwriter Endorsement REJECTION flow.
    Workflow:
    1. Login as USER.
    2. Raise an endorsement request (POLICY_CORRECTION).
    3. Login as UNDERWRITER.
    4. Find the newly created ticket.
    5. Reject the endorsement request.
    """

    @classmethod
    def setup_class(cls):
        cls.user_phone = os.getenv("USER_USERNAME")
        cls.user_password = os.getenv("USER_PASSWORD")
        cls.uw_username = os.getenv("UNDERWRITER_USERNAME")
        cls.uw_password = os.getenv("UNDERWRITER_PASSWORD")
        cls.client_id = cls.user_phone
        
        if not cls.user_phone or not cls.user_password or not cls.uw_username or not cls.uw_password:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UNDERWRITER_USERNAME, UNDERWRITER_PASSWORD) are missing.")
        
        cls.file_path = "rejection_proof.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    @pytest.mark.P1
    @pytest.mark.Regression
    @pytest.mark.parametrize("endorsement_type", [
        "POLICY_CORRECTION",
        "ADDITION_OR_DELETION",
        "DETAILS_CORRECTION"
    ])
    def test_endorsement_rejection_lifecycle(self, endorsement_type):
        # [STEP 1] Login as USER
        logger.info(f"Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_password)
        
        # Fetch active policies
        res = PolicyActions.get_personal_policies(self.client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE")
        assert res.status_code == 200, f"Failed to fetch active policies: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getPersonalPolicies" in res_json["data"], "Response missing 'getPersonalPolicies'"
        policies = res_json["data"]["getPersonalPolicies"]["policies"]
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
        working_policy = next((p for p in policies if p.get("insuranceType") == "Health Insurance"), None)
        if not working_policy:
            working_policy = next((p for p in policies if p.get("insuranceType") == "Life Insurance"), None)
        if not working_policy:
            working_policy = policies[0]
        assert "id" in working_policy, "Policy object missing 'id'"

        # [STEP 2] Raise Endorsement Request
        logger.info(f"Raising {endorsement_type} Request...")
        
        raising_type = {
            "POLICY_CORRECTION": "POLICY_CORRECTION",
            "ADDITION_OR_DELETION": "IND_POLICY_MEMBER_ADD/DELETE",
            "DETAILS_CORRECTION": "IND_POLICY_MEMBER_DETAILS_CORRECTION"
        }[endorsement_type]

        metadata = {
            "POLICY_CORRECTION": {"premiumAmountPaid": "99999"},
            "ADDITION_OR_DELETION": {
                "empId": self.client_id,
                "firstName": "RejectMe", "lastName": "Test", 
                "relationType": "SPOUSE", "dateOfBirth": "01-01-1995", 
                "sumInsured": "100000", "action": "add"
            },
            "DETAILS_CORRECTION": {
                "MEMBER_EMPLOYEE_ID": self.client_id,
                "firstName": "John", "lastName": "Doe",
                "existingError": "Wrong Name", "newModification": "Correct Name",
                "action": "Update"
            }
        }[endorsement_type]
        
        res = EndorsementActions.raise_endorsement(
            client_id=self.client_id,
            policy_id=working_policy["id"],
            endorsement_type=raising_type,
            metadata=metadata,
            email="test@example.com"
        )
        assert res.status_code == 200, f"Failed to raise endorsement: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "saveEndorsementData" in res_json["data"], "Response missing 'saveEndorsementData'"
        save_data = res_json["data"]["saveEndorsementData"]
        assert isinstance(save_data, dict), "Expected saveEndorsementData to be a dictionary"
        ticket_id = save_data["requestTypeId"]
        assert ticket_id is not None, "saveEndorsementData missing 'requestTypeId'"
        logger.info(f"Endorsement Raised. Ticket ID: {ticket_id}")

        logger.info("Waiting 5 seconds for sync...")
        time.sleep(5)

        # [STEP 3] Login as UNDERWRITER
        logger.info(f"Login as UNDERWRITER ({self.uw_username})...")
        API_CLIENT.set_credentials(self.uw_username, self.uw_password)
        
        # Discover correct underwriter-side ticket ID using robust lookup
        real_ticket_id = EndorsementActions.discover_underwriter_ticket_id(self.client_id, ticket_id)
        assert real_ticket_id is not None, f"Could not discover underwriter-side ticket ID for request ID {ticket_id}"
        logger.info(f"Discovered Ticket ID for processing: {real_ticket_id}")

        # [STEP 4] Reject Endorsement
        logger.info(f"Rejecting {endorsement_type} for Ticket: {real_ticket_id}...")
        request_dto = {
            "endorsementDetails": {
                "endorsementType": endorsement_type,
                "status": "REQUEST_REJECTED",
                "policyId": working_policy["id"],
                "clientId": self.client_id,
                "agentComments": f"REJECTED BY AUTOMATION: {endorsement_type} invalid criteria."
            }
        }

        res = EndorsementActions.submit_endorsement(
            ticket_id=real_ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.file_path,
            action="SUBMIT"
        )

        assert res.status_code == 200, f"Underwriter rejection failed: {res.text}"
        assert res.json().get("success") is True, f"Rejection result failure: {res.json()}"
        logger.info(f"Endorsement REJECTION Complete for {endorsement_type}!")
