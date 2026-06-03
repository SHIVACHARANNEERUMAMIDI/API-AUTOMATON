import os
import json
import pytest
import time
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import upload_document
from underwriter_api.policy_actions import verify_policy_ticket, get_policy_digitalization_tickets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.mark.digitization
class TestPolicyDigitalizationRejectionFlow:
    """
    Test suite for the End-to-End Underwriter Policy Digitalization REJECTION flow.
    Workflow:
    1. Login as USER and upload a policy document (creates a digitalization ticket).
    2. Login as UNDERWRITER and find the ticket.
    3. Underwriter REJECTS the digitalization request.
    """

    @classmethod
    def setup_class(cls):
        # Configuration
        cls.client_id = os.getenv("USER_USERNAME", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD", "Test@1234")
        
        # Base file path for dummy documents
        cls.file_path = "digitalization_rejection_doc.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy digitalization rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    def test_digitalization_rejection_lifecycle(self):
        # [STEP 1] Login as USER and Upload Document
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and uploading policy document...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # Upload Document triggers ticket creation
        res = upload_document(self.file_path, self.client_id, request_type="SAVEPOLICY")
        assert res.status_code == 200, f"User upload failed: {res.text}"
        print("User side: Document Uploaded Successfully (Ticket Created).")

        # [STEP 2] Login as UNDERWRITER and Search for the Ticket
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user}) and searching for ticket...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        # Search tickets by clientId
        res = get_policy_digitalization_tickets(search=self.client_id)
        assert res.status_code == 200, f"Failed to fetch tickets: {res.text}"
        
        tickets_data = res.json()["data"]["getPolicyDigitalizationTicketsData"]
        assert tickets_data["success"] is True
        
        tickets = tickets_data["content"]
        # Find the specific ticket for this client (latest one)
        target_ticket = next((t for t in tickets if t["clientId"] == self.client_id), None)
        assert target_ticket is not None, f"No ticket found for clientId: {self.client_id}"
        
        ticket_id = target_ticket["id"]
        policy_id = target_ticket["policyId"]
        print(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id}")

        # [STEP 3] Underwriter REJECT Digitalization Request
        print(f"\n[STEP 3] Rejecting Digitalization for Ticket: {ticket_id}...")
        
        # Construct form data for REJECTION
        verify_form = {
            "id": ticket_id,
            "decision": "REJECTED", # KEY CHANGE: REJECTED instead of COMPLETED
            "typeOfPolicy": "NEW",
            "policyId": policy_id,
            "policyNumber": target_ticket.get("policyNumber", "D601108267"),
            "insuranceType": "Motor Insurance",
            "productSubType": "Four-Wheeler",
            "agentComments": "REJECTED BY AUTOMATION: Image quality too low, text unreadable.", 
            "clientId": self.client_id,
            "clientType": "INDIVIDUAL",
            "policyMembers": []
        }
        
        # verify_policy_ticket handles the multipart request to verifyPolicyTicket mutation/REST
        res = verify_policy_ticket(verify_form, action="SUBMIT", file_path=self.file_path)
        assert res.status_code == 200, f"Underwriter rejection failed: {res.text}"
        
        verify_res = res.json()
        print(f"Server Response: {verify_res}")
        assert verify_res.get("success") is True, f"Response message: {verify_res.get('message')}"
        print(f"Underwriter side: Policy REJECTED Successfully. Message: {verify_res.get('message')}")
        
        # [VERIFY] Check ticket status in the list
        print("\n[VERIFY] Checking ticket status in digitalization queue...")
        res = get_policy_digitalization_tickets(search=self.client_id)
        updated_tickets = res.json()["data"]["getPolicyDigitalizationTicketsData"]["content"]
        updated_ticket = next((t for t in updated_tickets if t["id"] == ticket_id), None)
        
        # If it's rejected, it might still show in the list with status REJECTED
        # Note: Depending on UI filters, it might move to a different 'REJECTED' tab.
        if updated_ticket:
            print(f"Ticket {ticket_id} status is now: {updated_ticket.get('status')}")
            # The backend sets TaskStatus.REJECTED which usually maps to "REJECTED" in response
            assert updated_ticket.get("status") == "REJECTED"
            print("Verification Successful!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
