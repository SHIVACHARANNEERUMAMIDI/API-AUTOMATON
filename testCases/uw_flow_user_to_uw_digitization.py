import pytest
import os
import json
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import upload_document
from underwriter_api.policy_actions import create_policy_ticket, verify_policy_ticket, get_policy_digitalization_tickets
from dotenv import load_dotenv

load_dotenv()

class TestUserToUwDigitizationFlow:
    """
    Refined User-to-Underwriter Chained Flow:
    1. User uploads document.
    2. Underwriter fetches the ticket list and searches by clientId.
    3. Underwriter extracts ticket details and submits verification.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_id = os.getenv("TEST_CLIENT_ID", "8309718792")
        self.uw_user = os.getenv("UW_USERNAME")
        self.uw_pass = os.getenv("UW_PASSWORD")
        self.user_name = os.getenv("USER_USERNAME")
        self.user_pass = os.getenv("USER_PASSWORD")
        
        # Paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        self.file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"User uploaded file not found at: {self.file_path}")

    @pytest.mark.parametrize("insurance_type", [
        "Motor Insurance",
        "Health Insurance",
        "Life Insurance",
        "Travel Insurance",
        "Home Insurance"
    ])
    def test_01_user_upload(self, insurance_type):
        # --- STEP 1: USER SIDE (Upload) ---
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and Uploading Document for {insurance_type}...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # Upload Document
        res = upload_document(self.file_path, self.user_id, request_type="SAVEPOLICY")
        assert res.status_code == 200, f"User upload failed: {res.text}"
        print(f"User side: Document Uploaded Successfully for {insurance_type}.")

    @pytest.mark.parametrize("insurance_type", [
        "Motor Insurance",
        "Health Insurance",
        "Life Insurance",
        "Travel Insurance",
        "Home Insurance"
    ])
    def test_02_uw_verify_and_submit(self, insurance_type):
        # --- STEP 2: UNDERWRITER SIDE (Search by Client ID) ---
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user}) and Searching for Ticket with Client ID: {self.user_id}")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        # Search tickets by clientId
        res = get_policy_digitalization_tickets(search=self.user_id)
        assert res.status_code == 200, f"Failed to fetch tickets: {res.text}"
        
        tickets_data = res.json()["data"]["getPolicyDigitalizationTicketsData"]
        assert tickets_data["success"] is True
        
        tickets = tickets_data["content"]
        # Find the specific ticket for this client and insurance type that is still being digitalized
        target_ticket = next((t for t in tickets if t["clientId"] == self.user_id and t.get("insuranceType") == insurance_type), None)
        
        # Fallback to latest ticket for this client if insuranceType doesn't match exactly in search
        if not target_ticket:
             target_ticket = next((t for t in tickets if t["clientId"] == self.user_id), None)

        assert target_ticket is not None, f"No ticket found for clientId: {self.user_id} and type: {insurance_type}"
        
        ticket_id = target_ticket["id"]
        policy_id = target_ticket["policyId"]
        print(f"Found Ticket ID: {ticket_id} | Policy ID: {policy_id} | Client: {target_ticket.get('clientName', 'N/A')}")

        # --- STEP 3: UNDERWRITER SIDE (Verify & Submit) ---
        print(f"\n[STEP 3] Underwriter Submitting Verification for Ticket: {ticket_id}")
        
        # Construct form data using values from the search result and user-provided overrides
        verify_form = {
            "id": ticket_id,
            "decision": "COMPLETED",
            "typeOfPolicy": "NEW",
            "intermediary": "CAR CHASSIS CARRIERS PVT LTD",
            "totalNoOfEmployees": target_ticket.get("totalNoOfEmployees", ""),
            "coverRange": target_ticket.get("coverRange", ""),
            "policyHolderType": target_ticket.get("policyHolderType", "RETAIL_INDIVIDUAL"),
            "clientName": target_ticket.get("clientName", "Shiva Neerumamidi"),
            "policyId": policy_id,
            "policyNumber": target_ticket.get("policyNumber", "D601108267"),
            "thirdPartyPolicyNumber": "",
            "productType": "GENERAL",
            "thirdPartyProvider": None,
            "insuranceType": insurance_type,
            "productSubType": "Four-Wheeler" if "Motor" in insurance_type else "General",
            "sumInsured": "1000000",
            "policyStartDate": "",
            "policyEndDate": "",
            "tpStartDate": "",
            "tpEndDate": "",
            "premiumPaid": "79919",
            "policyInceptionPremium": "79919",
            "previousClaimedAmount": "0",
            "agentComments": "Automated Flow Verification",
            "tpa": "Go Digit General Insurance Ltd",
            "tpaUrl": "",
            "state": "Maharashtra",
            "city": "Mumbai",
            "address": "Mumbai, Mumbai, 400001",
            "branch": "",
            "insuredName": "Prakul Tiwari",
            "vehicleNumber": "1234567",
            "vehicleMakeModel": "12345",
            "paymentType": "ONE_TIME_PAYMENT",
            "installmentDetails": [],
            "isPACovered": True,
            "provider": {"id": "10", "name": "Go Digit General Insurance Ltd"},
            "coverageTypes": "[In-Patient Hospitalization Cover, Day Care Procedures, Pre-Hospitalization, Post-Hospitalization, Road Ambulance, Bariatric Surgery, Psychiatric Illness, Health Check-up, Home (Domiciliary) Hospitalization, Organ Donor Expenses, Emergency Air Ambulance Cover, Worldwide Coverage, Sum Insured Back-up]",
            "individualCoverageTypes": "",
            "clientType": "INDIVIDUAL",
            "clientId": self.user_id,
            "policyMembers": []
        }
        
        res = verify_policy_ticket(verify_form, action="SUBMIT", file_path=self.file_path)
        assert res.status_code == 200, f"Underwriter verification failed: {res.text}"
        
        verify_res = res.json()
        print(f"DEBUG: verifyPolicyTicket Full Response: {json.dumps(verify_res, indent=2)}")
        assert verify_res.get("success") is True, f"Response message: {verify_res.get('message')}"
        print(f"Underwriter side: Policy Verified & Submitted Successfully. Message: {verify_res.get('message')}")
        
        print("\n[FLOW COMPLETE] Refined Chained Flow Finished Successfully.")

if __name__ == "__main__":
    pytest.main([__file__])
