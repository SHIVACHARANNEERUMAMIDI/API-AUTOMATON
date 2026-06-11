import pytest
import time
import os
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import DocumentActions
from underwriter_api.policy_actions import PolicyActions
from utilities.customLogger import customLogger

logger = customLogger("TestPolicyDecisionsAllTypes")

# Comprehensive list of insurance types found in the codebase
INSURANCE_TYPES = [
    "Motor Insurance",
    "Health Insurance",
    "Life Insurance",
    "Travel Insurance",
    "Home Insurance",
    "Accidental Insurance",
    "Group Health Insurance",
    "Group Term Insurance",
    "Group Accidental Insurance",
    "Fire Insurance",
    "Engineering Insurance",
    "Liability Insurance",
    "Marine Insurance",
    "Miscellaneous"
]

@pytest.mark.digitization
class TestPolicyDecisionsAllTypes:
    @classmethod
    def setup_class(cls):
        cls.user_username = os.getenv("USER_USERNAME")
        cls.user_password = os.getenv("USER_PASSWORD")
        cls.uw_username = os.getenv("UW_USERNAME")
        cls.uw_password = os.getenv("UW_PASSWORD")
        
        if not cls.user_username or not cls.user_password or not cls.uw_username or not cls.uw_password:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UW_USERNAME, UW_PASSWORD) are missing.")

    @pytest.mark.P1
    @pytest.mark.Regression
    @pytest.mark.parametrize("insurance_type", INSURANCE_TYPES)
    @pytest.mark.parametrize("decision", ["COMPLETED", "REJECTED"])
    def test_policy_decisions_all_types(self, insurance_type, decision):
        """
        End-to-end test for policy digitalization across all insurance types.
        Tests both Approval (COMPLETED) and Rejection (REJECTED) flows.
        """
        logger.info(f"--- Testing {insurance_type} with decision: {decision} ---")
        
        # 1. User Uploads Policy Document
        API_CLIENT.set_credentials(self.user_username, self.user_password)
        client_id = self.user_username
        
        # Use a dummy pdf file for testing
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        dummy_file = os.path.join(automation_root, "Data", "test_policy.pdf")
        if not os.path.exists(dummy_file):
            os.makedirs(os.path.dirname(dummy_file), exist_ok=True)
            with open(dummy_file, "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")

        logger.info(f"Uploading {insurance_type} policy document...")
        upload_res = DocumentActions.upload_document(dummy_file, client_id, insurance_type=insurance_type)
        assert upload_res.status_code == 200
        res_json = upload_res.json()
        assert isinstance(res_json, dict), "Upload response should be a dictionary"
        assert res_json.get("requestTypeId") is not None or res_json.get("registrationStatus") is True
        logger.info("Upload successful.")

        # 2. Underwriter Logs In and Finds the Ticket
        API_CLIENT.set_credentials(self.uw_username, self.uw_password)
        
        # Wait a bit for the system to process the upload and create the ticket
        time.sleep(3)
        
        logger.info(f"Fetching digitalization tickets to find the entry for {client_id}...")
        res = PolicyActions.get_policy_digitalization_tickets(search=client_id)
        assert res.status_code == 200
        
        res_data = res.json()
        assert "data" in res_data, "Response missing 'data'"
        assert "getPolicyDigitalizationTicketsData" in res_data["data"], "Response missing 'getPolicyDigitalizationTicketsData'"
        tickets_data = res_data["data"]["getPolicyDigitalizationTicketsData"]
        assert tickets_data["success"] is True
        tickets = tickets_data["content"]
        assert isinstance(tickets, list), "Expected 'content' to be a list of tickets"
        
        # Find the specific ticket for this client (latest one with this insurance type)
        target_ticket = next((t for t in tickets if t["clientId"] == client_id and t["insuranceType"] == insurance_type), None)
        
        # Fallback if insurance type name is slightly different
        if not target_ticket:
             target_ticket = next((t for t in tickets if t["clientId"] == client_id), None)

        assert target_ticket is not None, f"No ticket found for clientId: {client_id}"
        assert "id" in target_ticket, "Ticket missing 'id'"
        assert "policyId" in target_ticket, "Ticket missing 'policyId'"
        
        ticket_id = target_ticket["id"]
        policy_id = target_ticket["policyId"]
        logger.info(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id}")

        # 3. Underwriter Processes the Ticket (Approve or Reject)
        logger.info(f"Processing ticket with decision: {decision}...")
        
        verify_form = target_ticket.copy()
        verify_form["decision"] = decision
        verify_form["agentComments"] = f"Processed by Automation for {insurance_type} - {decision}"
        
        # Action "SUBMIT" triggers the final verification logic
        verify_res = PolicyActions.verify_policy_ticket(verify_form, action="SUBMIT", file_path=dummy_file)
        
        assert verify_res.status_code == 200
        verify_json = verify_res.json()
        assert isinstance(verify_json, dict), "Verification response should be a dictionary"
        
        # Business validation
        assert verify_json.get("success") is True
        logger.info(f"Ticket processed successfully with decision: {decision}")
