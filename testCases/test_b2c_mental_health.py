import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.mental_health_actions import (
    get_disc_activities,
    get_activity_session,
    get_activity_progress,
    get_all_mental_conditions_by_id,
    save_mental_conditions,
    assess_disc_responses
)
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.b2c
class TestMentalHealthFlow:
    @classmethod
    def setup_class(cls):
        # Load standard user credentials from .env to establish authentication context
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.client_id = os.getenv("TEST_CLIENT_ID", "8309718792")

    def test_get_disc_activities(self):
        """Verify retrieving DISC activities for a client ID."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        print(f"[STEP 2] Fetching DISC activities for client {self.client_id}...")
        res = get_disc_activities(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch DISC activities: {res.text}"
        data = res.json()
        print(f"DEBUG: DISC Activities Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of activities"
        if data:
            first_activity = data[0]
            assert "id" in first_activity, "Activity missing 'id' field"
            assert "name" in first_activity, "Activity missing 'name' field"
            assert "type" in first_activity, "Activity missing 'type' field"
            assert "score" in first_activity, "Activity missing 'score' field"
        print("Successfully validated DISC activities.")

    def test_get_activity_session(self):
        """Verify retrieving activity session details."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        print("[STEP 2] Fetching activity session (type=journal_writing, limit=5)...")
        res = get_activity_session("journal_writing", 5)
        
        assert res.status_code == 200, f"Failed to fetch activity session: {res.text}"
        data = res.json()
        print(f"DEBUG: Activity Session Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of sessions"
        if data:
            first_session = data[0]
            assert "id" in first_session, "Session missing 'id' field"
            assert "activityId" in first_session, "Session missing 'activityId' field"
            assert "status" in first_session, "Session missing 'status' field"
            assert "type" in first_session, "Session missing 'type' field"
        print("Successfully validated activity session details.")

    def test_get_activity_progress(self):
        """Verify retrieving activity progress details."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        print(f"[STEP 2] Fetching activity progress for client {self.client_id}...")
        res = get_activity_progress(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch activity progress: {res.text}"
        data = res.json()
        print(f"DEBUG: Activity Progress Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, dict), "Response should be a JSON dictionary of progress info"
        assert "totalCompleted" in data, "Progress missing 'totalCompleted' field"
        assert "totalSuggested" in data, "Progress missing 'totalSuggested' field"
        assert "completedActivities" in data, "Progress missing 'completedActivities' field"
        assert isinstance(data["completedActivities"], list), "Expected 'completedActivities' to be a list"
        print("Successfully validated activity progress details.")

    def test_get_all_mental_conditions_by_id(self):
        """Verify retrieving all logged mental conditions for a client ID."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        print(f"[STEP 2] Fetching logged mental conditions for client {self.client_id}...")
        res = get_all_mental_conditions_by_id(self.client_id)
        
        assert res.status_code == 200, f"Failed to fetch mental conditions: {res.text}"
        data = res.json()
        print(f"DEBUG: Mental Conditions Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a JSON list of mental conditions"
        if data:
            first_condition = data[0]
            assert "id" in first_condition, "Condition missing 'id' field"
            assert "clientId" in first_condition, "Condition missing 'clientId' field"
            assert "mood" in first_condition, "Condition missing 'mood' field"
            assert "description" in first_condition, "Condition missing 'description' field"
        print("Successfully validated mental conditions.")

    def test_save_mental_conditions(self):
        """Verify saving mental conditions (mood and description)."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        print("[STEP 2] Saving mental conditions (mood=2, description='Feeling okay')...")
        res = save_mental_conditions(2, "Feeling okay")
        assert res.status_code in [200, 201], f"Failed to save mental conditions: {res.text}"
        data = res.json()
        print(f"DEBUG: Save Mental Conditions Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, dict), "Response should be a JSON dictionary"
        assert data.get("mood") == 2, "Saved mood value mismatch"
        assert data.get("description") == "Feeling okay", "Saved description mismatch"
        print("Successfully saved mental conditions.")

    def test_assess_disc_responses(self):
        """Verify assessing DISC responses."""
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        responses = ["I"] * 10
        print(f"[STEP 2] Assessing DISC responses for client {self.client_id}...")
        res = assess_disc_responses(self.client_id, responses, mood="")
        assert res.status_code in [200, 201], f"Failed to assess DISC responses: {res.text}"
        data = res.json()
        print(f"DEBUG: Assess DISC Responses Response: {json.dumps(data, indent=2)}")
        assert isinstance(data, list), "Response should be a list of results"
        assert len(data) > 0, "Assessment result list should not be empty"
        print("Successfully assessed DISC responses.")

        print("\n[FLOW COMPLETE] Mental Health API Automation Flow Finished Successfully.")

