import pytest
import os
import json
import time
from utilities.api_client import API_CLIENT
from underwriter_api.policy_actions import PolicyActions
from underwriter_api.endorsement_actions import EndorsementActions
from utilities.customLogger import customLogger
from utilities.config import Config

logger = customLogger("TestEndorsementTicketsLifecycle")

@pytest.mark.endorsement
class TestEndorsementTicketsLifecycle:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID")
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.uw_user = os.getenv("UW_USERNAME")
        cls.uw_pass = os.getenv("UW_PASSWORD")
        
        if not cls.client_id or not cls.user_name or not cls.user_pass or not cls.uw_user or not cls.uw_pass:
            raise ValueError("Mandatory environment variables (TEST_CLIENT_ID, USER_USERNAME, USER_PASSWORD, UW_USERNAME, UW_PASSWORD) are missing.")
        
        # Base file path for dummy documents
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        cls.state_file_path = os.path.join(automation_root, "Logs", "last_endorsement_state.json")
        
        if not os.path.exists(cls.file_path):
            os.makedirs(os.path.dirname(cls.file_path), exist_ok=True)
            with open(cls.file_path, "wb") as f:
                f.write(b"%PDF-1.4\n%dummy pdf")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_user_raise_endorsement(self):
        # [STEP 1] Raise Endorsement as USER
        logger.info(f"Login as USER ({self.user_name}) and raising endorsement request...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # GraphQL Query: getPersonalPolicies
        res_policies = PolicyActions.get_personal_policies(self.client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE")
        policies = res_policies.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        assert len(policies) > 0, "No active policies found to raise endorsement."
        
        res_data = None
        ticket_id = None
        working_policy = None
 
        for policy in policies:
            policy_id = policy['id']
            logger.info(f"Trying Policy ID: {policy_id} ({policy['insuranceType']})...")
            
            metadata = {
                "policyStartDate": "2026-05-11",
                "premiumAmountPaid": "79919",
                "insuranceName": policy["insuranceType"],
                "others": "Automated Endorsement Flow Test"
            }
            
            res = EndorsementActions.raise_endorsement(
                client_id=self.client_id,
                policy_id=policy_id,
                endorsement_type="POLICY_CORRECTION",
                metadata=metadata,
                email="test@example.com"
            )
            res_json = res.json()
            
            if "errors" not in res_json and res_json.get("data", {}).get("saveEndorsementData"):
                res_data = res_json["data"]["saveEndorsementData"]
                ticket_id = res_data["requestTypeId"]
                working_policy = policy
                logger.info(f"Success with Policy ID: {policy_id}. Ticket ID: {ticket_id}")
                break
            else:
                error_msg = res_json.get("errors", [{"message": "Unknown error"}])[0]["message"]
                logger.warning(f"Failed with Policy ID {policy_id}: {error_msg}")
 
        assert ticket_id is not None, "Could not find any policy eligible for endorsement."
        assert res_data["status"] == "Uploaded Successfully"
        assert "requestTypeId" in res_data, "Response missing 'requestTypeId'"
        assert "serviceRequestId" in res_data, "Response missing 'serviceRequestId'"
        logger.info(f"Endorsement Request Raised Successfully. Ticket ID: {ticket_id}")
        
        # Save state for UW test to use
        with open(self.state_file_path, "w") as f:
            json.dump({
                "ticket_id": ticket_id,
                "policy_id": working_policy['id'],
                "policy_number": working_policy.get('policyNumber', 'D601108267'),
                "insurance_type": working_policy['insuranceType']
            }, f)

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_uw_process_endorsement(self):
        # [STEP 2] Fetch Pending Tickets to get the correct Ticket ID for processing
        logger.info(f"Login as UNDERWRITER ({self.uw_user}) and fetching correct Ticket ID...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        res = EndorsementActions.get_endorsement_tickets(search=self.client_id, endorsement_tab="PENDING")
        assert res.status_code == 200, f"Failed to fetch tickets: {res.text}"
        res_json = res.json()
        assert "data" in res_json, "Response missing 'data' key"
        assert "getEndorsementTickets" in res_json["data"], "Response missing 'getEndorsementTickets'"
        tickets_data = res_json["data"]["getEndorsementTickets"]
        assert tickets_data.get("success") is True, "getEndorsementTickets success key is False"
        tickets = tickets_data["content"]
        assert isinstance(tickets, list), "Expected 'content' field to be a list"
        
        # Try to match with saved state if available
        working_policy = None
        if os.path.exists(self.state_file_path):
            with open(self.state_file_path, "r") as f:
                working_policy = json.load(f)

        target_ticket = None
        if tickets:
            if working_policy:
                if working_policy.get("ticket_id"):
                    target_ticket = next((t for t in tickets if str(t["id"]) == str(working_policy["ticket_id"])), None)
                if not target_ticket:
                    target_ticket = tickets[0]
            else:
                target_ticket = tickets[0]
            
            real_ticket_id = target_ticket["id"]
            logger.info(f"Discovered correct Ticket ID for processing: {real_ticket_id}")
        else:
            pytest.fail("Underwriter has no pending tickets for this client.")

        # [STEP 3] Process Endorsement as UNDERWRITER
        logger.info(f"Processing ticket: {real_ticket_id}...")
        ticket_id = real_ticket_id
        
        if not working_policy:
            working_policy = {
                "policy_id": "UNKNOWN",
                "policy_number": "D601108267",
                "insurance_type": "Health Insurance"
            }
        
        request_dto = {
            "cdAccountDetails": {"cdAccountId": "", "cdAccountNumber": "", "cdBalance": ""},
            "employeeCountDetails": {
                "selfNewlyAdded": "", "dependentsNewlyAdded": "", "premiumPaid": "",
                "sumInsuredIncreasedBy": "", "deletedEmployees": "", "dependentsDeleted": "",
                "premiumRefunded": "", "sumInsuredDecreasedBy": ""
            },
            "endorsementDetails": {
                "endorsementType": "POLICY_CORRECTION",
                "status": "REQUEST_SUBMITTED",
                "operation": "",
                "typeOfPolicy": "NEW",
                "intermediary": "AUTOMATION TEST",
                "coverRange": "",
                "policyHolderType": "RETAIL_INDIVIDUAL",
                "clientName": Config.USER_FULL_NAME,  # RC1: sourced from data/test_users.json
                "companyName": self.client_id,
                "clientId": self.client_id,
                "policyId": working_policy['policy_id'],
                "policyNumber": working_policy['policy_number'],
                "productType": "GENERAL",
                "insuranceType": working_policy['insurance_type'],
                "productSubType": "General",
                "sumInsured": "1000000",
                "premiumPaid": "79919",
                "policyInceptionPremium": "79919",
                "policyStartDate": "2026-05-11",
                "policyEndDate": "2026-05-31",
                "tpStartDate": "",
                "tpEndDate": "",
                "thirdPartyProvider": None,
                "thirdPartyPolicyNumber": "",
                "previousClaimedAmount": 0,
                "agentComments": "Processed via Automation",
                "tpa": "",
                "policyState": "",
                "policyCity": "",
                "branch": "",
                "policyAddress": "",
                "insuredName": Config.USER_FULL_NAME,  # RC1: sourced from data/test_users.json
                "vehicleNumber": "",
                "vehicleMakeModel": "",
                "noOfPermanentEmployees": "0",
                "noOfContractEmployees": "0",
                "totalNoOfEmployees": 0,
                "noOfEmployeesCovered": "0",
                "noOfLivesCovered": "0",
                "definitionOfFamily": "",
                "avgFamilySize": "0",
                "paymentType": "ONE_TIME_PAYMENT",
                "installmentDetails": [],
                "cc": "",
                "gvw": "",
                "seatingCapacity": "",
                "vehicleIdv": "",
                "fuelType": "",
                "ncbPercentage": "",
                "engineNumber": "",
                "chassisNumber": "",
                "yearOfManufacture": "",
                "isPACovered": True,
                "provider": {"id": "10", "name": "Go Digit General Insurance Ltd"},
                "coverageTypes": "",
                "individualCoverageTypes": "",
                "membersData": None,
                "membersToBeAdded": None,
                "membersToBeDeleted": None
            }
        }

        res = EndorsementActions.submit_endorsement(
            ticket_id=ticket_id,
            request_dto=request_dto,
            endorsement_copy_path=self.file_path,
            action="SUBMIT"
        )
            
        assert res.status_code == 200, f"Underwriter submission failed: {res.text}"
        res_json = res.json()
        assert res_json.get("success") is True, f"Submission failed: {res_json.get('message')}"
        logger.info(f"Endorsement Ticket {ticket_id} Processed Successfully.")
