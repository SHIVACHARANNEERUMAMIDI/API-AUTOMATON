"""
GraphQL mutation strings for policy-related operations.
Used by underwriter_api.policy_actions.PolicyActions.
"""

DELETE_POLICY_MUTATION = """
mutation ($policyId: String!, $reason: String!) {
  deletePolicy(policyId: $policyId, reason: $reason) {
    message
    success
  }
}
"""
