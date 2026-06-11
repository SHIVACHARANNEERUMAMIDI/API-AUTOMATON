import os
import json
import pytest
import time
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import DocumentActions
from underwriter_api.policy_actions import PolicyActions
from utilities.customLogger import customLogger

logger = customLogger("TestPolicyDigitizationRejection")

@pytest.mark.digitization
class TestPolicyDigitizationRejection:
    """
    Test suite for the End-to-End Underwriter Policy Digitalization REJECTION flow.
    Workflow:
    1. Login as USER and upload a policy document (creates a digitalization ticket).
    2. Login as UNDERWRITER and find the ticket.
    3. Underwriter REJECTS the digitalization request.
    """

    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("USER_USERNAME")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UNDERWRITER_USERNAME")
        cls.uw_pass = os.getenv("UNDERWRITER_PASSWORD")
        
        if not cls.client_id or not cls.user_name or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, UNDERWRITER_USERNAME, UNDERWRITER_PASSWORD) are missing.")
        
        # Base file path for dummy documents
        cls.file_path = "digitalization_rejection_doc.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy digitalization rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_digitalization_rejection_lifecycle(self):
        # [STEP 1] Login as USER and Upload Document
        logger.info(f"Login as USER ({self.user_name}) and uploading policy document...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # Upload Document triggers ticket creation
        res = DocumentActions.upload_document(self.file_path, self.client_id, request_type="SAVEPOLICY")
        assert res.status_code == 200, f"User upload failed: {res.text}"
        logger.info("User side: Document Uploaded Successfully (Ticket Created).")

        # [STEP 2] Login as UNDERWRITER and Search for the Ticket
        logger.info(f"Login as UNDERWRITER ({self.uw_user}) and searching for ticket...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        # Search tickets by clientId
        res = PolicyActions.get_policy_digitalization_tickets(search=self.client_id)
        assert res.status_code == 200, f"Failed to fetch tickets: {res.text}"
        
        tickets_data = res.json()["data"]["getPolicyDigitalizationTicketsData"]
        assert tickets_data["success"] is True
        
        tickets = tickets_data["content"]
        # Find the specific ticket for this client (latest one)
        target_ticket = next((t for t in tickets if t["clientId"] == self.client_id), None)
        assert target_ticket is not None, f"No ticket found for clientId: {self.client_id}"
        
        ticket_id = target_ticket["id"]
        policy_id = target_ticket["policyId"]
        logger.info(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id}")

        # [STEP 3] Underwriter REJECT Digitalization Request
        logger.info(f"Rejecting Digitalization for Ticket: {ticket_id}...")
        
        # Construct form data for REJECTION
        verify_form = {
            "id": ticket_id,
            "decision": "REJECTED",
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
        
        res = PolicyActions.verify_policy_ticket(verify_form, action="SUBMIT", file_path=self.file_path)
        assert res.status_code == 200, f"Underwriter rejection failed: {res.text}"
        
        verify_res = res.json()
        logger.info(f"Server Response: {verify_res}")
        assert verify_res.get("success") is True, f"Response message: {verify_res.get('message')}"
        logger.info(f"Underwriter side: Policy REJECTED Successfully. Message: {verify_res.get('message')}")
        
        # [VERIFY] Check ticket status in the list - Business validation
        logger.info("Checking ticket status in digitalization queue...")
        res = PolicyActions.get_policy_digitalization_tickets(search=self.client_id)
        updated_tickets = res.json()["data"]["getPolicyDigitalizationTicketsData"]["content"]
        updated_ticket = next((t for t in updated_tickets if t["id"] == ticket_id), None)
        
        if updated_ticket:
            logger.info(f"Ticket {ticket_id} status is now: {updated_ticket.get('status')}")
            assert updated_ticket.get("status") == "REJECTED"
            logger.info("Verification Successful!")
