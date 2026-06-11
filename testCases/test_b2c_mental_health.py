import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.mental_health_actions import MentalHealthActions
from utilities.customLogger import customLogger

logger = customLogger("TestB2CMentalHealth")

@pytest.mark.b2c
class TestB2CMentalHealth:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        cls.client_id = os.getenv("TEST_CLIENT_ID")
        if not cls.user_name or not cls.user_pass or not cls.client_id:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, TEST_CLIENT_ID) are missing.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_disc_activities(self):
        """Verify retrieving DISC activities for a client ID."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info(f"Fetching DISC activities for client {self.client_id}...")
        res = MentalHealthActions.get_disc_activities(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch DISC activities: {res.text}"
        data = res.json()
        logger.info(f"DISC Activities Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of activities"
        
        if data:
            first_activity = data[0]
            assert "id" in first_activity, "Activity missing 'id' field"
            assert "name" in first_activity, "Activity missing 'name' field"
            assert "type" in first_activity, "Activity missing 'type' field"
            assert "score" in first_activity, "Activity missing 'score' field"
        logger.info("Successfully validated DISC activities.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_activity_session(self):
        """Verify retrieving activity session details."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info("Fetching activity session (type=journal_writing, limit=5)...")
        res = MentalHealthActions.get_activity_session("journal_writing", 5)
        
        assert res.status_code == 200, f"Failed to fetch activity session: {res.text}"
        data = res.json()
        logger.info(f"Activity Session Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of sessions"
        
        if data:
            first_session = data[0]
            assert "id" in first_session, "Session missing 'id' field"
            assert "activityId" in first_session, "Session missing 'activityId' field"
            assert "status" in first_session, "Session missing 'status' field"
            assert "type" in first_session, "Session missing 'type' field"
        logger.info("Successfully validated activity session details.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_activity_progress(self):
        """Verify retrieving activity progress details."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info(f"Fetching activity progress for client {self.client_id}...")
        res = MentalHealthActions.get_activity_progress(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch activity progress: {res.text}"
        data = res.json()
        logger.info(f"Activity Progress Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, dict), "Response should be a JSON dictionary of progress info"
        assert "totalCompleted" in data, "Progress missing 'totalCompleted' field"
        assert "totalSuggested" in data, "Progress missing 'totalSuggested' field"
        assert "completedActivities" in data, "Progress missing 'completedActivities' field"
        assert isinstance(data["completedActivities"], list), "Expected 'completedActivities' to be a list"
        logger.info("Successfully validated activity progress details.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_all_mental_conditions_by_id(self):
        """Verify retrieving all logged mental conditions for a client ID."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info(f"Fetching logged mental conditions for client {self.client_id}...")
        res = MentalHealthActions.get_all_mental_conditions_by_id(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch mental conditions: {res.text}"
        data = res.json()
        logger.info(f"Mental Conditions Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of mental conditions"
        
        # Business validations: Verify that all mental conditions returned belong to this client ID
        if data:
            first_condition = data[0]
            assert "id" in first_condition, "Condition missing 'id' field"
            assert first_condition.get("clientId") == self.client_id, "Condition clientId mismatch"
            assert "mood" in first_condition, "Condition missing 'mood' field"
            assert "description" in first_condition, "Condition missing 'description' field"
        logger.info("Successfully validated mental conditions.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_save_mental_conditions(self):
        """Verify saving mental conditions (mood and description)."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info("Saving mental conditions (mood=2, description='Feeling okay')...")
        res = MentalHealthActions.save_mental_conditions(2, "Feeling okay")
        assert res.status_code in [200, 201], f"Failed to save mental conditions: {res.text}"
        data = res.json()
        logger.info(f"Save Mental Conditions Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, dict), "Response should be a JSON dictionary"
        
        # Business validations
        assert data.get("mood") == 2, "Saved mood value mismatch"
        assert data.get("description") == "Feeling okay", "Saved description mismatch"
        logger.info("Successfully saved mental conditions.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_assess_disc_responses(self):
        """Verify assessing DISC responses."""
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        responses = ["I"] * 10
        logger.info(f"Assessing DISC responses for client {self.client_id}...")
        res = MentalHealthActions.assess_disc_responses(self.client_id, responses, mood="")
        assert res.status_code in [200, 201], f"Failed to assess DISC responses: {res.text}"
        data = res.json()
        logger.info(f"Assess DISC Responses Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a list of results"
        assert len(data) > 0, "Assessment result list should not be empty"
        logger.info("Successfully assessed DISC responses.")
