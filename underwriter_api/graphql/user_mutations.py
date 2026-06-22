"""
GraphQL mutation strings for user-related operations.
Used by underwriter_api.user_actions.UserActions.
"""

UPDATE_LOGIN_TIME_MUTATION = """
mutation UpdateLoginTime($userName: String!) {
  updateLoginTime(userName: $userName) {
    loggedInAtLeastOnce
  }
}
"""

SAVE_UNDERWRITER_TASK_MUTATION = """
mutation saveUnderWriterTask($claim: Boolean, $id: String!, $status: UnderWriterTaskStatus) {
  saveUnderWriterTask(claim: $claim, id: $id, status: $status) { id status }
}
"""
