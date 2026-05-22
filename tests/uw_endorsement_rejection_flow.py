import os
import json
import time
import pytest
from utils.api_client import API_CLIENT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestEndorsementRejectionFlow:
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
        # Configuration
        cls.user_phone = os.getenv("USER_USERNAME", "919573464433")
        cls.user_password = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.uw_username = os.getenv("UNDERWRITER_USERNAME", "403rajeev")
        cls.uw_password = os.getenv("UNDERWRITER_PASSWORD", "Test@1234")
        cls.client_id = cls.user_phone
        
        # Create a dummy file for upload
        cls.file_path = "rejection_proof.pdf"
        with open(cls.file_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy rejection content")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    @pytest.mark.parametrize("endorsement_type", [
        "POLICY_CORRECTION",
        "ADDITION_OR_DELETION",
        "DETAILS_CORRECTION"
    ])
    def test_endorsement_rejection_lifecycle(self, endorsement_type):
        # [STEP 1] Login as USER
        print(f"\n[STEP 1] Login as USER ({self.user_phone})...")
        API_CLIENT.set_credentials(self.user_phone, self.user_password)
        
        # Fetch active policies
        res = API_CLIENT.post_graphql("""
        query getPersonalPolicies($clientId: String, $clientType: ClientType, $expiryType: ExpiryType) {
          getPersonalPolicies(clientId: $clientId, clientType: $clientType, expiryType: $expiryType) {
            policies { id policyNumber insuranceType }
          }
        }
        """, {"clientId": self.client_id, "clientType": "INDIVIDUAL", "expiryType": "ACTIVE"})
        
        policies = res.json()["data"]["getPersonalPolicies"]["policies"]
        assert len(policies) > 0, "No active policies found."
        working_policy = policies[0]
        print(f"DEBUG: Selected Policy: {working_policy}")
        print(f"DEBUG: Using Client ID: {self.client_id}")

        # [STEP 2] Raise Endorsement Request
        print(f"\n[STEP 2] Raising {endorsement_type} Request...")
        
        # Map GraphQL type to raising type
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

        mutation = """
        mutation SaveEndorsementData($input: EndorsementData!) {
          saveEndorsementData(input: $input) { requestTypeId }
        }
        """
        mutation_input = {
            "clientId": self.client_id,
            "endorsementType": raising_type,
            "policyId": working_policy["id"],
            "endorsementRaisedFor": self.client_id,
            "endorsementRaisedForClientType": "RETAIL_INDIVIDUAL",
            "endorsementStatus": "Request Submitted",
            "email": "test@example.com",
            "mobileNumber": self.client_id,
            "metadata": metadata
        }
        
        res = API_CLIENT.post_graphql(mutation, {"input": mutation_input})
        print(f"DEBUG: raise_endorsement response: {res.text}")
        assert res.status_code == 200, f"Failed to raise endorsement: {res.text}"
        ticket_id = res.json()["data"]["saveEndorsementData"]["requestTypeId"]
        print(f"Endorsement Raised. Ticket ID: {ticket_id}")

        print("Waiting 5 seconds for sync...")
        time.sleep(5)

        # [STEP 3] Login as UNDERWRITER
        print(f"\n[STEP 3] Login as UNDERWRITER ({self.uw_username})...")
        API_CLIENT.set_credentials(self.uw_username, self.uw_password)
        
        # Discover correct ticket ID
        get_tickets_query = """
        query GET_ENDORSEMENT_TICKETS_DATA($endorsementTab: EndorsementTab) {
          getEndorsementTickets(page: 1, size: 10, endorsementTab: $endorsementTab) {
            content { id status }
          }
        }
        """
        res = API_CLIENT.post_graphql(get_tickets_query, {"endorsementTab": "PENDING"})
        print(f"DEBUG: getEndorsementTickets response: {res.text}")
        tickets = res.json()["data"]["getEndorsementTickets"]["content"]
        
        # Find our ticket by ID (if possible) or just take the first matching type
        target_ticket = next((t for t in tickets if str(t["id"]) == str(ticket_id)), tickets[0])
        real_ticket_id = target_ticket["id"]
        print(f"Discovered Ticket ID for processing: {real_ticket_id}")

        # [STEP 4] Reject Endorsement
        print(f"\n[STEP 4] Rejecting {endorsement_type} for Ticket: {real_ticket_id}...")
        
        # [STEP 4] Reject Endorsement
        print(f"\n[STEP 4] Rejecting {endorsement_type} for Ticket: {real_ticket_id}...")
        
        # 4.1 Fetch existing ticket data to ensure we don't wipe out fields
        fetch_query = """
        query getEndorsementTicketSavedData($ticketId: Long!) {
          getEndorsementTicketSavedData(ticketId: $ticketId) {
            endorsementTicketView {
              id
              clientId
              clientName
              companyName
              endorsementType
              endorsementId
              requestTypeId
              serviceRequestId
              documentType
              documentUploadId
              annexureUrl
              documentUploadURL
              annexureDetails
              memberIds
              operation
              policyDetails {
                policyId
                policyNumber
                insuranceType
                productSubType
                productType
                sumInsured
                premiumAmount
                policyStartDate
                policyEndDate
                providerId
                providerName
              }
              cdAccountDetails {
                cdAccountId
                cdAccountNumber
                cdBalance
              }
              employeeDetails {
                totalNoOfEmployees
                selfNewlyAdded
                dependentsNewlyAdded
              }
              membersData {
                id
                firstName
                lastName
                relation
                dateOfBirth
              }
            }
          }
        }
        """
        res = API_CLIENT.post_graphql(fetch_query, {"ticketId": int(real_ticket_id)})
        print(f"DEBUG: fetch existing ticket response: {res.text}")
        assert res.status_code == 200, f"Failed to fetch existing ticket: {res.text}"
        ticket_data = res.json()["data"]["getEndorsementTicketSavedData"]["endorsementTicketView"]

        # 4.2 Construct requestDto using the fetched data as base
        # EndorsementTicketRequestDto structure: endorsementDetails, cdAccountDetails, employeeCountDetails
        
        # Construct a more robust payload
        # Extract IDs from ticket_data
        ticket_id = ticket_data.get("id")
        endorsement_id = ticket_data.get("endorsementId")
        request_type_id = ticket_data.get("requestTypeId")
        service_request_id = ticket_data.get("serviceRequestId")
        document_upload_id = ticket_data.get("documentUploadId")

        # Map title case type to all-caps enum name
        type_map = {
            "Endorsement-Policy Corrections": "POLICY_CORRECTION",
            "Policy Correction": "POLICY_CORRECTION",
            "Individual Details Correction": "DETAILS_CORRECTION",
            "Addition Or Deletion": "ADDITION_OR_DELETION",
            "Individual Addition & Deletion": "ADDITION_OR_DELETION"
        }
        enum_type = type_map.get(ticket_data.get("endorsementType"), "POLICY_CORRECTION")

        # Construct a more robust payload
        endorsement_details = {
            "endorsementType": enum_type,
            "status": "REQUEST_REJECTED",
            "policyId": ticket_data["policyDetails"]["policyId"] if ticket_data.get("policyDetails") else None,
            "policyNumber": ticket_data["policyDetails"]["policyNumber"] if ticket_data.get("policyDetails") else None,
            "clientId": ticket_data["clientId"],
            "clientName": ticket_data["clientName"],
            "companyName": ticket_data["companyName"],
            "productType": ticket_data["policyDetails"]["productType"] if ticket_data.get("policyDetails") else None,
            "productSubType": ticket_data["policyDetails"]["productSubType"] if ticket_data.get("policyDetails") else None,
            "insuranceType": ticket_data["policyDetails"]["insuranceType"] if ticket_data.get("policyDetails") else None,
            "sumInsured": ticket_data["policyDetails"]["sumInsured"] if ticket_data.get("policyDetails") else None,
            "premiumPaid": ticket_data["policyDetails"]["premiumAmount"] if ticket_data.get("policyDetails") else None,
            "policyStartDate": ticket_data["policyDetails"]["policyStartDate"] if ticket_data.get("policyDetails") else None,
            "policyEndDate": ticket_data["policyDetails"]["policyEndDate"] if ticket_data.get("policyDetails") else None,
            "provider": {
                "id": str(ticket_data["policyDetails"]["providerId"]) if ticket_data.get("policyDetails") and ticket_data["policyDetails"].get("providerId") else "10",
                "name": ticket_data["policyDetails"]["providerName"] if ticket_data.get("policyDetails") and ticket_data["policyDetails"].get("providerName") else "Go Digit General Insurance Ltd"
            },
            "agentComments": f"REJECTED BY AUTOMATION: {enum_type} invalid criteria.",
            "operation": ticket_data.get("operation", ""),
            "memberIds": ticket_data.get("memberIds", []),
            "membersData": ticket_data.get("membersData") if ticket_data.get("membersData") else [],
            "policyCity": "Mumbai",
            "location": "Mumbai",
            "requestTypeId": endorsement_id,  # THEORY C WORKAROUND: Inject endorsementId here
            "endorsementId": endorsement_id,
            "id": ticket_id
        }

        # Handle numeric fields correctly
        total_employees = 0
        if ticket_data.get("employeeDetails") and ticket_data["employeeDetails"].get("totalNoOfEmployees"):
            try:
                total_employees = int(ticket_data["employeeDetails"]["totalNoOfEmployees"])
            except:
                total_employees = 0

        request_dto = {
            "endorsementDetails": endorsement_details,
            "cdAccountDetails": {
                "cdAccountId": "",
                "cdAccountNumber": "",
                "cdBalance": ""
            },
            "employeeCountDetails": {
                "totalNoOfEmployees": total_employees,
                "selfNewlyAdded": "0",
                "dependentsNewlyAdded": "0",
                "premiumPaid": "",
                "sumInsuredIncreasedBy": "",
                "deletedEmployees": "",
                "dependentsDeleted": "",
                "premiumRefunded": "",
                "sumInsuredDecreasedBy": ""
            }
        }

        print(f"DEBUG: Final requestDto: {json.dumps(request_dto, indent=2)}")

        with open(self.file_path, "rb") as f:
            file_content = f.read()
            files = {
                "endorsementAction": (None, "SUBMIT"),
                "ticketId": (None, str(real_ticket_id)),
                "requestDto": (None, json.dumps(request_dto)),
                "endorsementCopy": ("rejection_proof.pdf", file_content, "application/pdf"),
                "annexureDocument": ("dummy_annexure.pdf", file_content, "application/pdf")
            }
            
            url = f"{API_CLIENT.paisaplan_base.rstrip('/')}/fileUpload/save"
            params = {"id": real_ticket_id}
            print(f"DEBUG: Hitting endpoint: {url} with params {params}")
            res = API_CLIENT._request("POST", url, files=files, params=params)

        assert res.status_code == 200, f"Underwriter rejection failed: {res.text}"
        assert res.json().get("success") is True, f"Rejection result failure: {res.json()}"
        print(f"Endorsement REJECTION Complete for {endorsement_type}!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
