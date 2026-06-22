"""
GraphQL query strings for policy-related operations.
Used by underwriter_api.policy_actions.PolicyActions.
"""

GET_PERSONAL_POLICIES_QUERY = """
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

GET_POLICY_DIGITALIZATION_TICKETS_QUERY = """
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
