import pytest
import os
import json
import time
from utils.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

class TestUserToUwEndorsementTicketsFlow:
    @classmethod
    def setup_class(cls):
        cls.client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_user = os.getenv("UW_USERNAME", "403rajeev")
        cls.uw_pass = os.getenv("UW_PASSWORD", "Test@1234")
        
        # Base file path for dummy documents
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        cls.file_path = os.path.join(automation_root, "data", "GoDigit Health Insurance 2.pdf")
        
        if not os.path.exists(cls.file_path):
            os.makedirs(os.path.dirname(cls.file_path), exist_ok=True)
            with open(cls.file_path, "wb") as f:
                f.write(b"%PDF-1.4\n%dummy pdf")

    def test_01_user_raise_endorsement(self):
        # [STEP 1] Raise Endorsement as USER
        print(f"\n[STEP 1] Login as USER ({self.user_name}) and raising endorsement request...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # GraphQL Mutation: SaveEndorsementData
        mutation = """
        mutation SaveEndorsementData($input: EndorsementData!) {
          saveEndorsementData(input: $input) {
            status
            requestTypeId
            serviceRequestId
          }
        }
        """
        
        # GraphQL Query: getPersonalPolicies
        query_policies = """
        {
          getPersonalPolicies(
            clientId: "919573464433"
            clientType: INDIVIDUAL
            expiryType: ACTIVE
          ) {
            policies { id policyNumber insuranceType }
          }
        }
        """
        res_policies = API_CLIENT.post_graphql(query_policies)
        policies = res_policies.json().get("data", {}).get("getPersonalPolicies", {}).get("policies", [])
        assert len(policies) > 0, "No active policies found to raise endorsement."
        
        res_data = None
        ticket_id = None
        working_policy = None

        for policy in policies:
            policy_id = policy['id']
            print(f"Trying Policy ID: {policy_id} ({policy['insuranceType']})...")
            
            variables = {
                "input": {
                    "clientId": self.client_id,
                    "endorsementType": "POLICY_CORRECTION",
                    "policyId": policy_id,
                    "endorsementRaisedFor": self.client_id,
                    "endorsementRaisedForClientType": "RETAIL_INDIVIDUAL",
                    "notificationCategory": "NONE",
                    "endorsementStatus": "Request Submitted",
                    "email": "test@example.com",
                    "mobileNumber": self.client_id,
                    "metadata": {
                        "policyStartDate": "2026-05-11",
                        "premiumAmountPaid": "79919",
                        "insuranceName": policy["insuranceType"],
                        "others": "Automated Endorsement Flow Test"
                    }
                }
            }
            
            res = API_CLIENT.post_graphql(mutation, variables=variables)
            res_json = res.json()
            
            if "errors" not in res_json and res_json.get("data", {}).get("saveEndorsementData"):
                res_data = res_json["data"]["saveEndorsementData"]
                ticket_id = res_data["requestTypeId"]
                working_policy = policy
                print(f"Success with Policy ID: {policy_id}. Ticket ID: {ticket_id}")
                break
            else:
                error_msg = res_json.get("errors", [{"message": "Unknown error"}])[0]["message"]
                print(f"Failed with Policy ID {policy_id}: {error_msg}")

        assert ticket_id is not None, "Could not find any policy eligible for endorsement."
        assert res_data["status"] == "Uploaded Successfully"
        print(f"Endorsement Request Raised Successfully. Ticket ID: {ticket_id}")
        
        # Save state for UW test to use
        with open("last_endorsement_state.json", "w") as f:
            json.dump({
                "ticket_id": ticket_id,
                "policy_id": working_policy['id'],
                "policy_number": working_policy.get('policyNumber', 'D601108267'),
                "insurance_type": working_policy['insuranceType']
            }, f)

    def test_02_uw_process_endorsement(self):
        # [STEP 2] Fetch Pending Tickets to get the correct Ticket ID for processing
        print(f"\n[STEP 2] Login as UNDERWRITER ({self.uw_user}) and fetching correct Ticket ID...")
        API_CLIENT.set_credentials(self.uw_user, self.uw_pass)
        
        get_tickets_query = """
        query GET_ENDORSEMENT_TICKETS_DATA($page: Int, $size: Int, $filters: [EndorsementTicketFilter], $search: String, $endorsementTab: EndorsementTab) {
          getEndorsementTickets(
            page: $page
            size: $size
            filters: $filters
            search: $search
            endorsementTab: $endorsementTab
          ) {
            success
            message
            content {
              id
              status
              clientId
              clientName
              companyName
            }
          }
        }
        """
        ticket_vars = {
            "page": 1,
            "size": 10,
            "search": self.client_id,
            "endorsementTab": "PENDING",
            "filters": []
        }
        res = API_CLIENT.post_graphql(get_tickets_query, ticket_vars)
        assert res.status_code == 200, f"Failed to fetch tickets: {res.text}"
        res_json = res.json()
        tickets = res_json["data"]["getEndorsementTickets"]["content"]
        
        # Try to match with saved state if available
        working_policy = None
        if os.path.exists("last_endorsement_state.json"):
            with open("last_endorsement_state.json", "r") as f:
                working_policy = json.load(f)

        target_ticket = None
        if tickets:
            if working_policy:
                # 1. Try exact Ticket ID match if available from state
                if working_policy.get("ticket_id"):
                    target_ticket = next((t for t in tickets if str(t["id"]) == str(working_policy["ticket_id"])), None)
                
                # 2. Fallback to picking the latest ticket if no ID match (since list is usually sorted by newest)
                if not target_ticket:
                    target_ticket = tickets[0]
            else:
                target_ticket = tickets[0]
            
            real_ticket_id = target_ticket["id"]
            print(f"Discovered correct Ticket ID for processing: {real_ticket_id}")
        else:
            pytest.fail("Underwriter has no pending tickets for this client.")

        # [STEP 3] Process Endorsement as UNDERWRITER
        print(f"\n[STEP 3] Processing ticket: {real_ticket_id}...")
        ticket_id = real_ticket_id
        
        # Fetch working policy info from ticket if not in state
        if not working_policy:
            working_policy = {
                "policy_id": "UNKNOWN",
                "policy_number": "D601108267",
                "insurance_type": "Health Insurance"
            }

        # The multipart POST endpoint for saving/submitting underwriter processing
        endpoint = "fileUpload/save"
        params = {"id": ticket_id}
        
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
                "clientName": "Anuj Mankumare",
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
                "insuredName": "Anuj Mankumare",
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

        url = f"{API_CLIENT.paisaplan_base.rstrip('/')}/{endpoint.lstrip('/')}"
        files = {
            "endorsementAction": (None, "SUBMIT"),
            "ticketId": (None, str(ticket_id)),
            "requestDto": (None, json.dumps(request_dto)),
            "endorsementCopy": ("endorsement_result.pdf", open(self.file_path, "rb"), "application/pdf")
        }
        res = API_CLIENT._request("POST", url, files=files, params=params)
        assert res.status_code == 200, f"Underwriter submission failed: {res.text}"
        res_json = res.json()
        assert res_json.get("success") is True, f"Submission failed: {res_json.get('message')}"
        print(f"Endorsement Ticket {ticket_id} Processed Successfully.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
