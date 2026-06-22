"""
GraphQL mutation strings for endorsement-related operations.
Used by underwriter_api.endorsement_actions.EndorsementActions.
"""

SAVE_ENDORSEMENT_DATA_MUTATION = """
mutation SaveEndorsementData($input: EndorsementData!) {
  saveEndorsementData(input: $input) {
    status
    requestTypeId
    serviceRequestId
  }
}
"""
