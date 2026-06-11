from utilities.api_client import API_CLIENT

class MentalHealthActions:
    @staticmethod
    def get_disc_activities(client_id):
        """
        GET /mentalHealth/activities/getDiscActivitiesByClientId
        Retrieves DISC activities by client ID.
        """
        endpoint = "mentalHealth/activities/getDiscActivitiesByClientId"
        params = {"clientId": client_id}
        return API_CLIENT.get_mt_rest(endpoint, params=params)

    @staticmethod
    def get_activity_session(activity_type="journal_writing", limit=5):
        """
        GET /mentalHealth/activities/getActivitySession
        Retrieves activity session details by type and limit.
        """
        endpoint = "mentalHealth/activities/getActivitySession"
        params = {
            "type": activity_type,
            "limit": limit
        }
        return API_CLIENT.get_mt_rest(endpoint, params=params)

    @staticmethod
    def get_activity_progress(client_id):
        """
        GET /mentalHealth/activities/getActivityProgress
        Retrieves activity progress for a given client ID.
        """
        endpoint = "mentalHealth/activities/getActivityProgress"
        params = {"clientId": client_id}
        return API_CLIENT.get_mt_rest(endpoint, params=params)

    @staticmethod
    def get_all_mental_conditions_by_id(client_id):
        """
        GET /mentalHealth/mental-conditions/getAllMentalConditionsById
        Retrieves all mental conditions logged by client ID.
        """
        endpoint = "mentalHealth/mental-conditions/getAllMentalConditionsById"
        params = {"clientId": client_id}
        return API_CLIENT.get_mt_rest(endpoint, params=params)

    @staticmethod
    def save_mental_conditions(mood, description):
        """
        POST /mentalHealth/mental-conditions/saveMentalConditions
        Saves new mental condition log (mood and description).
        """
        endpoint = "mentalHealth/mental-conditions/saveMentalConditions"
        payload = {
            "mood": mood,
            "description": description
        }
        return API_CLIENT.post_mt_rest(endpoint, data=payload)

    @staticmethod
    def assess_disc_responses(client_id, responses, mood=""):
        """
        POST /mentalHealth/discResponses/assess
        Submits and assesses DISC behavioral assessment responses.
        """
        endpoint = "mentalHealth/discResponses/assess"
        payload = {
            "mood": mood,
            "responses": responses,
            "clientId": client_id
        }
        return API_CLIENT.post_mt_rest(endpoint, data=payload)
