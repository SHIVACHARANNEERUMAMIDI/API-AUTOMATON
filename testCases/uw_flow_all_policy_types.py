import os
import json
import time
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import upload_document
from underwriter_api.policy_actions import get_policy_digitalization_tickets, verify_policy_ticket, create_policy_ticket
from dotenv import load_dotenv

load_dotenv()

class TestAllPolicyTypesDigitization:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UW_USERNAME")
        cls.uw_pass = os.getenv("UW_PASSWORD")
        
        # Base file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")

    @pytest.mark.parametrize("insurance_type, product_sub_type", [
        ("Motor Insurance", "Four-Wheeler"),
        ("Health Insurance", "Individual"),
        ("Term Life Insurance", "Term Life"),
        ("Travel Insurance", "International"),
        ("Home Insurance", "Structure and Contents"),
        ("Marine Insurance", "Cargo")
    ])
    def test_digitization_flow_per_type(self, insurance_type, product_sub_type):
        print(f"\n[START] Testing Flow for: {insurance_type} | {product_sub_type}")
        
        # --- STEP 1: USER UPLOAD ---
        print(f"Step 1: Uploading as User for {insurance_type}...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # We need to pass the specific insurance type in metadata if possible
        # Actually, our upload_document action has it hardcoded to 'Term Life Insurance'
        # I will modify the action to take these as parameters
        
        res = self.upload_with_metadata(insurance_type, product_sub_type)
        assert res.status_code == 200, f"Upload failed for {insurance_type}: {res.text}"
        print(f"Upload Successful for {insurance_type}")
        
        # Wait for backend processing (AI extraction etc)
        print("Waiting 5 seconds for backend processing...")
        time.sleep(5)
        
        # Step 2: Search for the ticket
        print(f"Step 2: Searching as Underwriter for {insurance_type} ticket...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        target_ticket = None
        for attempt in range(3):
            res = get_policy_digitalization_tickets(search=self.client_id, policy_type=insurance_type)
            assert res.status_code == 200
            tickets = res.json().get("data", {}).get("getPolicyDigitalizationTicketsData", {}).get("content", [])
            
            # Find the latest ticket for this client and insurance type
            if tickets:
                target_ticket = tickets[0]
                break
            
            # Debug: print all tickets without policy_type filter to see what's happening
            debug_res = get_policy_digitalization_tickets(search=self.client_id)
            all_tickets = debug_res.json().get("data", {}).get("getPolicyDigitalizationTicketsData", {}).get("content", [])
            print(f"DEBUG: All tickets for client: {[t.get('insuranceType') for t in all_tickets]}")
            
            print(f"Ticket not found for {insurance_type}, retrying in 5s (Attempt {attempt+1}/3)...")
            time.sleep(5)
        
        assert target_ticket is not None, f"No {insurance_type} ticket found for client {self.client_id}"
        
        ticket_id = target_ticket['id']
        policy_id = target_ticket['policyId']
        print(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id}")
        
        # --- STEP 3: UNDERWRITER VERIFY/SUBMIT ---
        print(f"Step 3: Verifying Ticket: {ticket_id} as {insurance_type}...")
        
        verify_form = target_ticket.copy()
        # Override with our specific type for this test iteration
        verify_form.update({
            "decision": "COMPLETED",
            "insuranceType": insurance_type,
            "productSubType": product_sub_type,
            "status": "COMPLETED",
            "agentComments": f"Verified {insurance_type} via automation"
        })
        
        # Cleanup internal graphql fields
        verify_form.pop("__typename", None)
        
        res = verify_policy_ticket(verify_form)
        assert res.status_code == 200, f"Verification failed for {insurance_type}: {res.text}"
        print(f"Successfully Digitized: {insurance_type}")
        
        # Wait between iterations to avoid overloading AI service
        print("Cooling down for 3 seconds...")
        time.sleep(3)

    def upload_with_metadata(self, insurance_type, product_sub_type):
        """Custom upload helper using /paisaplan/policy/create-ticket."""
        form_data = {
            "clientId": self.client_id,
            "insuranceType": insurance_type,
            "productSubType": product_sub_type,
            "clientType": "INDIVIDUAL",
            "productType": "GENERAL",
            "status": "PENDING"
        }
        # Call the dedicated create-ticket endpoint
        return create_policy_ticket(form_data, is_ticket_required="true", file_path=self.file_path)
