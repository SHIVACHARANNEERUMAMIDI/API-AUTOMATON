"""
GraphQL query strings for claim-related operations.
Used by underwriter_api.claim_actions.ClaimActions.
"""

GET_PERSONAL_POLICIES_QUERY = """
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
