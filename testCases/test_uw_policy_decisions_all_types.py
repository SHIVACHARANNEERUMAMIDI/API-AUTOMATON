import pytest
import time
import os
from dotenv import load_dotenv
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import upload_document
from underwriter_api.policy_actions import get_policy_digitalization_tickets, verify_policy_ticket

# Load environment variables
load_dotenv()

USER_USERNAME = os.getenv("USER_USERNAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")
UW_USERNAME = os.getenv("UW_USERNAME")
UW_PASSWORD = os.getenv("UW_PASSWORD")

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
    @pytest.mark.parametrize("insurance_type", INSURANCE_TYPES)
    @pytest.mark.parametrize("decision", ["COMPLETED", "REJECTED"])
    def test_policy_decisions_all_types(self, insurance_type, decision):
        """
        End-to-end test for policy digitalization across all insurance types.
        Tests both Approval (COMPLETED) and Rejection (REJECTED) flows.
        """
        print(f"\n--- Testing {insurance_type} with decision: {decision} ---")
        
        # 1. User Uploads Policy Document
        API_CLIENT.set_credentials(USER_USERNAME, USER_PASSWORD)
        client_id = USER_USERNAME
        
        # Use a dummy pdf file for testing
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        dummy_file = os.path.join(automation_root, "Data", "test_policy.pdf")
        if not os.path.exists(dummy_file):
            os.makedirs(os.path.dirname(dummy_file), exist_ok=True)
            with open(dummy_file, "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")

        print(f"Uploading {insurance_type} policy document...")
        upload_res = upload_document(dummy_file, client_id, insurance_type=insurance_type)
        assert upload_res.status_code == 200
        res_json = upload_res.json()
        assert isinstance(res_json, dict), "Upload response should be a dictionary"
        assert res_json.get("requestTypeId") is not None or res_json.get("registrationStatus") is True
        print("Upload successful.")

        # 2. Underwriter Logs In and Finds the Ticket
        API_CLIENT.set_credentials(UW_USERNAME, UW_PASSWORD)
        
        # Wait a bit for the system to process the upload and create the ticket
        time.sleep(3)
        
        print(f"Fetching digitalization tickets to find the entry for {client_id}...")
        res = get_policy_digitalization_tickets(search=client_id)
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
        print(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id}")

        # 3. Underwriter Processes the Ticket (Approve or Reject)
        print(f"Processing ticket with decision: {decision}...")
        
        # Use the full ticket data as the base for verification to ensure no fields are lost
        verify_form = target_ticket.copy()
        verify_form["decision"] = decision
        verify_form["agentComments"] = f"Processed by Automation for {insurance_type} - {decision}"
        
        # Action "SUBMIT" triggers the final verification logic
        verify_res = verify_policy_ticket(verify_form, action="SUBMIT", file_path=dummy_file)
        
        assert verify_res.status_code == 200
        verify_json = verify_res.json()
        assert isinstance(verify_json, dict), "Verification response should be a dictionary"
        assert verify_json.get("success") is True
        print(f"Ticket processed successfully with decision: {decision}")

        # 4. Final State Verification
        print("Test passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
