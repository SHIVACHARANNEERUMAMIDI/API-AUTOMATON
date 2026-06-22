"""
GraphQL query strings for user-related operations.
Used by underwriter_api.user_actions.UserActions.
"""

RM_CALLBACK_QUERY = """
query RmCallbackRequest($name: String!, $email: String!, $phone: String!, $insuranceType: String!) {
  rmCallbackRequest(
    rmCallBackRequest: {
      customerName: $name,
      customerEmailId: $email,
      customerMobileNo: $phone,
      insuranceType: $insuranceType
    }
  ) {
    success
    message
  }
}
"""

GET_PERSONAL_POLICIES_QUERY = """
{
  getPersonalPolicies(
    clientId: "%s"
    clientType: %s
    expiryType: %s
    year: "%s"
    insuranceType: "%s"
    insuranceSubType: "%s"
  ) {
    totalPolicies
    totalPremiumAmount
    activePolicies
    policies {
      id
      policyNumber
      status
      companyName
      insuranceType
      productSubType
      issuedOn
      expiresOn
    }
  }
}
"""

GET_PORTFOLIO_V2_QUERY = """
{
  getPortfolioV2(clientId: "%s", clientType: %s) {
    ctc
    overallSuggestions {
      insuranceName
      riskLevel
    }
    data {
      insuranceMainName
      company {
        sumAssured
        premium
      }
      personal {
        sumAssured
        premium
      }
    }
  }
}
"""

GET_RISK_SCORE_QUERY = """
query getPortfolioV2($clientId: String!, $clientType: ClientType!) {
  getPortfolioV2(clientId: $clientId, clientType: $clientType) {
    riskScore {
      healthInsurance { score }
      lifeInsurance { score }
    }
  }
}
"""

GET_EXPIRED_POLICIES_YEAR_LIMIT_QUERY = """
{
  getExpiredPoliciesYearLimit(clientId: "%s") {
    success
    message
    data {
      expiredPolicyYearLimitMin
      expiredPolicyYearLimitHigh
    }
  }
}
"""

GET_CHILD_AND_PARENT_COMPANY_DETAILS_QUERY = """
query GetChildAndParentCompanyDetails($clientId: String!) {
  getChildAndParentCompanyDetails(clientId: $clientId) {
    parentCompanyDetails {
      id
      clientId
      companyName
    }
    childCompanyDetailsList {
      id
      clientId
      companyName
    }
  }
}
"""

GET_INSURANCE_TYPE_DATA_QUERY = """
query GetInsuranceTypeData($clientType: PolicyHolderType) {
  getInsuranceTypeData(clientType: $clientType) {
    id
    productType
    insuranceType
    subType
    category
  }
}
"""

GET_MASTER_DATA_QUERY = """
query GetMasterData($input: [MasterDataType]!) {
  getMasterData(input: $input) {
    response {
      dataType
      data
    }
  }
}
"""

GET_UNDERWRITER_TASKS_QUERY = """
query getUnderWriterTasks($search: String, $searchType: ClientSearchType, $page: NonNegativeInt!, $size: PositiveInt!) {
  getUnderWriterTasks(search: $search, searchType: $searchType, page: $page, size: $size) {
    content {
      id
      isClaimed
      claimedBy {
        userName
      }
      clientId
    }
  }
}
"""
