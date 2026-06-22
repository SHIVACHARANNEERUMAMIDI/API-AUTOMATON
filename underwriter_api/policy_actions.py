import json
from utilities.api_client import API_CLIENT
from underwriter_api.graphql.policy_queries import (
    GET_PERSONAL_POLICIES_QUERY,
    GET_POLICY_DIGITALIZATION_TICKETS_QUERY,
)
from underwriter_api.graphql.policy_mutations import DELETE_POLICY_MUTATION

class PolicyActions:
    @staticmethod
    def get_personal_policies(client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE"):
        """
        GraphQL Query: getPersonalPolicies
        """
        variables = {
            "clientId": client_id,
            "clientType": client_type,
            "expiryType": expiry_type
        }
        return API_CLIENT.post_graphql(GET_PERSONAL_POLICIES_QUERY, variables=variables)

    @staticmethod
    def create_policy_ticket(form_data, is_ticket_required=True, file_path=None):
        """
        POST /paisaplan/policy/create-ticket
        Creates a policy digitalization ticket.

        :param is_ticket_required: Python boolean. Converted to lowercase string at the
                                   multipart form boundary to satisfy the API contract.
        """
        data = {
            "form": json.dumps(form_data),
            "isTicketRequired": str(is_ticket_required).lower()
        }

        if file_path:
            with open(file_path, "rb") as f:
                files = {"policyDocument": ("policy.pdf", f, "application/pdf")}
                return API_CLIENT.post_multipart("policy/create-ticket", files=files, data=data)
        else:
            return API_CLIENT.post_multipart("policy/create-ticket", data=data)

    @staticmethod
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

    @staticmethod
    def delete_policy(policy_id, reason):
        """
        GraphQL Mutation: deletePolicy
        """
        variables = {"policyId": policy_id, "reason": reason}
        return API_CLIENT.post_graphql(DELETE_POLICY_MUTATION, variables=variables)

    @staticmethod
    def get_policy_digitalization_tickets(page=1, size=10, search="", policy_type=None):
        """
        GraphQL Query: getPolicyDigitalizationTicketsData
        """
        variables = {
            "page": page,
            "size": size,
            "sort": "DESC",
            "search": search,
            "policyType": policy_type,
            "policyDigitalizationTabs": "ALL"
        }
        return API_CLIENT.post_graphql(GET_POLICY_DIGITALIZATION_TICKETS_QUERY, variables=variables)
