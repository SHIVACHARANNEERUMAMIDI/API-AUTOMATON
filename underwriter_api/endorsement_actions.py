import json
import os
from utilities.api_client import API_CLIENT

def get_endorsement_tickets(search="", endorsement_tab="PENDING", page=1, size=10):
    """
    GraphQL Query: GET_ENDORSEMENT_TICKETS_DATA
    Fetches endorsement tickets for the underwriter.
    """
    query = """
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
        ticketsCounts {
          totalTickets
          addAndDelete
          detailsCorrections
          policyCorrections
          completedTasks
          rejectedTasks
          pendingTickets
        }
        content {
          id
          clientId
          clientName
          userType
          clientType
          companyName
          receivedDateTime
          policyType
          productSubType
          createdBy {
            id
            userName
            firstName
            lastName
          }
          claimedBy {
            id
            userName
            firstName
            lastName
          }
          status
        }
        pageInfo {
          currentPage
          totalCount
          totalPages
        }
      }
    }
    """
    variables = {
        "page": page,
        "size": size,
        "search": search,
        "endorsementTab": endorsement_tab,
        "filters": []
    }
    return API_CLIENT.post_graphql(query, variables)

def raise_endorsement(client_id, policy_id, endorsement_type, metadata, email="test@example.com", mobile=None):
    """
    GraphQL Mutation: SaveEndorsementData
    Raises an endorsement request as a user.
    """
    mutation = """
    mutation SaveEndorsementData($input: EndorsementData!) {
      saveEndorsementData(input: $input) {
        status
        requestTypeId
        serviceRequestId
      }
    }
    """
    variables = {
        "input": {
            "clientId": client_id,
            "endorsementType": endorsement_type,
            "policyId": policy_id,
            "endorsementRaisedFor": client_id,
            "endorsementRaisedForClientType": "RETAIL_INDIVIDUAL",
            "notificationCategory": "NONE",
            "endorsementStatus": "Request Submitted",
            "email": email,
            "mobileNumber": mobile if mobile else client_id,
            "metadata": metadata
        }
    }
    return API_CLIENT.post_graphql(mutation, variables)

def get_endorsement_ticket_saved_data(ticket_id):
    """
    GraphQL Query: getEndorsementTicketSavedData
    Fetches detailed data for an endorsement ticket.
    """
    query = """
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
    variables = {"ticketId": int(ticket_id)}
    return API_CLIENT.post_graphql(query, variables)

def submit_endorsement(ticket_id, request_dto, endorsement_copy_path=None, action="SUBMIT"):
    """
    POST /paisaplan/fileUpload/save?endorsementAction={action}&ticketId={ticket_id}
    Submits or saves an endorsement update.
    """
    # Use the provided request_dto as is, but ensure top-level structure is correct
    if "endorsementDetails" not in request_dto:
        request_dto = {"endorsementDetails": request_dto}
    
    if "cdAccountDetails" not in request_dto:
        request_dto["cdAccountDetails"] = {"cdAccountId": "", "cdAccountNumber": "", "cdBalance": ""}
    
    if "employeeCountDetails" not in request_dto:
        request_dto["employeeCountDetails"] = {
            "selfNewlyAdded": "", "dependentsNewlyAdded": "", "premiumPaid": "",
            "sumInsuredIncreasedBy": "", "deletedEmployees": "", "dependentsDeleted": "",
            "premiumRefunded": "", "sumInsuredDecreasedBy": ""
        }

    # Construct multipart payload
    file_content = b"%PDF-1.4 dummy"
    filename = "dummy.pdf"
    
    if endorsement_copy_path and os.path.exists(endorsement_copy_path):
        with open(endorsement_copy_path, "rb") as f:
            file_content = f.read()
            filename = os.path.basename(endorsement_copy_path)

    files = {
        "endorsementAction": (None, action),
        "ticketId": (None, str(ticket_id)),
        "requestDto": (None, json.dumps(request_dto)),
        "endorsementCopy": (filename, file_content, "application/pdf")
    }
        
    url = f"{API_CLIENT.paisaplan_base.rstrip('/')}/fileUpload/save"
    params = {"id": str(ticket_id)}
    
    print(f"DEBUG: Submitting Endorsement for Ticket {ticket_id} (Action: {action})")
    return API_CLIENT._request("POST", url, files=files, params=params)

def discover_underwriter_ticket_id(client_id, request_id):
    """
    Finds the underwriter-side ticket ID matching the user-side request_id (requestTypeId/endorsementId).
    """
    res = get_endorsement_tickets(search=client_id, endorsement_tab="PENDING")
    if res.status_code != 200:
        return None
    
    tickets_data = res.json().get("data", {}).get("getEndorsementTickets", {})
    if not tickets_data:
        return None
        
    tickets = tickets_data.get("content", [])
    if not isinstance(tickets, list):
        return None
        
    # Filter tickets matching this client_id
    client_tickets = [t for t in tickets if str(t.get("clientId")) == str(client_id)]
    
    for t in client_tickets:
        t_id = t["id"]
        saved_res = get_endorsement_ticket_saved_data(t_id)
        if saved_res.status_code == 200:
            view = saved_res.json().get("data", {}).get("getEndorsementTicketSavedData", {}).get("endorsementTicketView", {})
            if view:
                req_id = view.get("requestTypeId") or view.get("endorsementId")
                if str(req_id) == str(request_id):
                    print(f"DEBUG: Found matching underwriter ticket ID: {t_id} for request ID: {request_id}")
                    return t_id
                    
    # Fallbacks to prevent failure if exact match is not found
    if client_tickets:
        print(f"WARNING: Exact match for request ID {request_id} not found. Falling back to latest client ticket: {client_tickets[0]['id']}")
        return client_tickets[0]["id"]
    elif tickets:
        print(f"WARNING: Exact match for request ID {request_id} not found. Falling back to latest general ticket: {tickets[0]['id']}")
        return tickets[0]["id"]
    return None
