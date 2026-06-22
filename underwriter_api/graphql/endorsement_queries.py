"""
GraphQL query strings for endorsement-related operations.
Used by underwriter_api.endorsement_actions.EndorsementActions.
"""

GET_ENDORSEMENT_TICKETS_QUERY = """
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

GET_ENDORSEMENT_TICKET_SAVED_DATA_QUERY = """
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
