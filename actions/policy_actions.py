import json
from utils.api_client import API_CLIENT

def get_personal_policies(client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE"):
    """
    GraphQL Query: getPersonalPolicies
    """
    query = """
    query getPersonalPolicies($clientId: String, $clientType: ClientType, $expiryType: ExpiryType) {
      getPersonalPolicies(
        clientId: $clientId
        clientType: $clientType
        expiryType: $expiryType
      ) {
        policies {
          id
          policyNumber
          insuranceType
          productSubType
          issuedOn
          expiresOn
          otherInformation {
            insuredName
            city
            state
            address
          }
          provider {
            id
            name
          }
        }
      }
    }
    """
    variables = {
        "clientId": client_id,
        "clientType": client_type,
        "expiryType": expiry_type
    }
    return API_CLIENT.post_graphql(query, variables=variables)

def create_policy_ticket(form_data, is_ticket_required="true", file_path=None):
    """
    POST /paisaplan/policy/create-ticket
    Creates a policy digitalization ticket.
    """
    data = {
        "form": json.dumps(form_data),
        "isTicketRequired": is_ticket_required
    }
    
    if file_path:
        with open(file_path, "rb") as f:
            files = {"policyDocument": ("policy.pdf", f, "application/pdf")}
            return API_CLIENT.post_multipart("policy/create-ticket", files=files, data=data)
    else:
        return API_CLIENT.post_multipart("policy/create-ticket", data=data)

def verify_policy_ticket(form_data, action="SAVE", file_path=None):
    """
    POST /paisaplan/policy/verifyPolicyTicket
    Underwriter verification of a policy ticket.
    """
    data = {
        "policyDigitalizationForm": json.dumps(form_data),
        "addPolicyAction": action
    }
    
    if file_path:
        with open(file_path, "rb") as f:
            files = {"policyDocument": ("policy.pdf", f, "application/pdf")}
            return API_CLIENT.post_multipart("policy/verifyPolicyTicket", files=files, data=data)
    else:
        # Use an empty byte string as a placeholder to force multipart encoding
        files = {"policyDocument": ("empty.pdf", b"", "application/pdf")}
        return API_CLIENT.post_multipart("policy/verifyPolicyTicket", files=files, data=data)

def delete_policy(policy_id, reason):
    """
    GraphQL Mutation: deletePolicy
    """
    query = """
    mutation ($policyId: String!, $reason: String!) {
      deletePolicy(policyId: $policyId, reason: $reason) {
        message
        success
      }
    }
    """
    variables = {"policyId": policy_id, "reason": reason}
    return API_CLIENT.post_graphql(query, variables=variables)

def get_policy_digitalization_tickets(page=1, size=10, search="", policy_type=None):
    """
    GraphQL Query: getPolicyDigitalizationTicketsData
    """
    query = """
    query ($page: NonNegativeInt!, $size: PositiveInt!, $sort: String, $sortField: String, $search: String, $policyType: String, $rmAssigned: String, $claimedBy: String, $taskStatus: TaskStatus, $policyDigitalizationTabs: PolicyDigitalizationTabs) {
      getPolicyDigitalizationTicketsData(
        page: $page
        size: $size
        sort: $sort
        sortField: $sortField
        search: $search
        policyType: $policyType
        rmAssigned: $rmAssigned
        claimedBy: $claimedBy
        taskStatus: $taskStatus
        policyDigitalizationTabs: $policyDigitalizationTabs
      ) {
        success
        message
        content {
          id
          status
          clientId
          clientName
          clientType
          policyId
          policyNumber
          productType
          productSubType
          insuredName
          insuranceType
          sumInsured
          policyStartDate
          policyEndDate
          premiumPaid
          previousClaimedAmount
          coverageTypes
          individualCoverageTypes
          agentComments
          tpa
          tpaUrl
          location
          branch
          policyUploadedMethod
          vehicleNumber
          vehicleMakeModel
          engineNumber
          chassisNumber
          yearOfManufacture
          cc
          individualSumInsured
          vehicleIdv
          seatingCapacity
          fuelType
          provider {
            id
            name
          }
        }
      }
    }
    """
    variables = {
        "page": page,
        "size": size,
        "sort": "DESC",
        "search": search,
        "policyType": policy_type,
        "policyDigitalizationTabs": "ALL"
    }
    return API_CLIENT.post_graphql(query, variables=variables)
