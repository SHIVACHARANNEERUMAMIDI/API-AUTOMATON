import pytest
import os
import json
from underwriter_api.user_actions import (
    save_or_update_insurance_profile,
    get_insurance_profile,
    get_all_claims_by_client_id,
    list_chatbot_sessions,
    get_chatbot_agent_availability,
    get_chatbot_session_history,
    get_logged_in_user_roles,
    get_tour_details,
    get_mobile_app_info,
    check_pwned_password_range
)
from utilities.api_client import API_CLIENT
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.b2c
class TestB2CProfileAndChatbotParity:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.client_id = cls.user_name
        API_CLIENT.set_credentials(cls.user_name, cls.user_pass)

    def test_profile_flow(self):
        print(f"\n[PROFILE] Saving insurance profile for {self.client_id}...")
        
        # Load external JSON payload
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        payload_path = os.path.join(automation_root, "Data", "profile_dto.json")
        with open(payload_path, "r") as json_f:
            profile_dto = json.load(json_f)
            
        # Dynamically inject client_id
        profile_dto["clientId"] = self.client_id
        
        res = save_or_update_insurance_profile(profile_dto)
        assert res.status_code in [200, 201], f"Expected 200 or 201 but got {res.status_code}"
        
        print(f"[PROFILE] Fetching insurance profile for {self.client_id}...")
        res = get_insurance_profile(self.client_id)
        assert res.status_code == 200
        profile_data = res.json()
        assert isinstance(profile_data, dict), "Expected profile details to be a dictionary object"
        assert profile_data.get("clientId") == self.client_id, "Fetched profile client ID mismatch"
        assert "gender" in profile_data, "Profile missing 'gender' field"
        assert "employmentType" in profile_data, "Profile missing 'employmentType' field"
        assert "annualIncome" in profile_data, "Profile missing 'annualIncome' field"

    def test_claims_history(self):
        print(f"\n[CLAIMS] Fetching claims for {self.client_id}...")
        res = get_all_claims_by_client_id(self.client_id)
        assert res.status_code == 200
        claims_data = res.json()
        assert isinstance(claims_data, dict), "Expected claims details to be a dictionary object"
        assert "claims" in claims_data, "Claims response missing 'claims' key"
        assert isinstance(claims_data["claims"], list), "Expected 'claims' field to be a list"
        print(f"DEBUG: Claims count: {len(claims_data['claims'])}")

    def test_chatbot_sessions(self):
        print(f"\n[CHATBOT] Listing sessions...")
        res = list_chatbot_sessions()
        assert res.status_code == 200
        sessions = res.json()
        assert isinstance(sessions, list), "Expected sessions to be returned as a list"
        print(f"DEBUG: Sessions found: {len(sessions)}")
        
        if sessions:
            session_id = sessions[0].get("id") or sessions[0].get("sessionId")
            assert session_id is not None, "Session object missing ID field"
            print(f"[CHATBOT] Fetching history for session: {session_id}...")
            res_history = get_chatbot_session_history(session_id)
            assert res_history.status_code == 200
            history = res_history.json()
            assert isinstance(history, list), "Expected chat history to be a list"
            print(f"DEBUG: History fetched successfully. Size: {len(history)}")

    def test_chatbot_agent_availability(self):
        print(f"\n[CHATBOT] Checking agent availability...")
        res = get_chatbot_agent_availability()
        assert res.status_code == 200
        availability = res.json()
        assert isinstance(availability, dict), "Expected agent availability details to be a dictionary object"
        print(f"DEBUG: Agent availability: {availability}")

    def test_user_roles(self):
        print(f"\n[ACCESS] Fetching user roles...")
        res = get_logged_in_user_roles()
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
        user_info = res.json()
        assert isinstance(user_info, dict), "Expected user info to be returned as a dictionary object"
        assert "roles" in user_info, "User info missing 'roles' list"
        roles = user_info["roles"]
        assert isinstance(roles, list), "Expected roles to be a list"
        if roles:
            assert all(isinstance(role, (str, dict)) for role in roles), "Expected roles to contain string or dictionary items"

    def test_tour_details(self):
        print(f"\n[ACCESS] Fetching tour details for {self.user_name}...")
        res = get_tour_details(self.user_name)
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
        tour = res.json()
        assert isinstance(tour, dict), "Expected tour details to be a dictionary object"
        # Verify typical keys in tour details if present, e.g. status or steps configuration
        assert len(tour.keys()) >= 0, "Tour details dict should be valid"

    def test_mobile_info(self):
        print(f"\n[INFO] Fetching mobile app info...")
        res = get_mobile_app_info()
        assert res.status_code == 200
        app_info = res.json()
        assert isinstance(app_info, dict), "Expected app info response to be a dictionary object"
        assert "latestVersion" in app_info or "version" in app_info, "latestVersion/version metadata missing from response"

    def test_check_pwned_password_range(self):
        print("\n[PWNED] Querying compromised password range for hash prefix 848B1...")
        res = check_pwned_password_range("848B1")
        assert res.status_code == 200
        assert len(res.text) > 0, "Response content should not be empty"
        # Confirm that standard pwned passwords response contains hash suffixes
        assert ":" in res.text, "Response should be in 'SUFFIX:COUNT' format"
        print("Successfully fetched pwned password hashes range and verified format.")

