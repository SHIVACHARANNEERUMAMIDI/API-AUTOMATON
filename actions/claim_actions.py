import json
import os
from utils.api_client import API_CLIENT

def get_personal_policies(client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE"):
    """Fetch personal policies for a user via GraphQL."""
    query = """
    query getPersonalPolicies($clientId: String, $clientType: ClientType, $expiryType: ExpiryType) {
      getPersonalPolicies(
        clientId: $clientId
        clientType: $clientType
        expiryType: $expiryType
        year: ""
        insuranceType: ""
        insuranceSubType: ""
      ) {
        totalPolicies
        policies {
          id
          policyNumber
          status
          clientId
          insuranceType
          productSubType
        }
      }
    }
    """
    variables = {
        "clientId": client_id,
        "clientType": client_type,
        "expiryType": expiry_type
    }
    return API_CLIENT.post_graphql(query, variables)

def raise_claim(dto, files, action_type="Submit"):
    """
    Raise a claim for a policy.
    dto: dict containing clientId, policyId, policyType, documents list etc.
    files: dict of {form_field_name: file_path}
    """
    # Prepare files for requests
    multipart_files = {}
    opened_files = []
    try:
        for field, path in files.items():
            f = open(path, "rb")
            opened_files.append(f)
            multipart_files[field] = (os.path.basename(path), f, "application/pdf")
        
        # type and dto are @RequestPart in IndividualClaimsController
        multipart_files["type"] = (None, action_type, "application/json")
        multipart_files["dto"] = (None, json.dumps(dto), "application/json")
        
        return API_CLIENT.post_multipart("claims", files=multipart_files, data={})
    finally:
        # We can't close here if we want API_CLIENT to use them?
        # Actually API_CLIENT.post_multipart is synchronous, so it's fine.
        for f in opened_files:
            f.close()

def get_all_claims(page=0, size=10):
    """Fetch all claims for underwriter via REST."""
    return API_CLIENT.get_rest(f"claims/getAllClaims?page={page}&size={size}")

def update_claim_status(claim_id, status_dto):
    """Update claim status (APPROVED/REJECTED etc.) via REST PUT."""
    url = f"claims/{claim_id}/statusUpdate"
    # Note: API_CLIENT doesn't have a put_rest, I'll use _request
    return API_CLIENT._request("PUT", f"{API_CLIENT.paisaplan_base.rstrip('/')}/{url.lstrip('/')}", json=status_dto)
