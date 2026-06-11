import pytest
import os
import json
from underwriter_api.user_actions import UserActions
from utilities.api_client import API_CLIENT
from utilities.customLogger import customLogger

logger = customLogger("TestB2CProfileAndChatbotParity")

@pytest.mark.b2c
class TestB2CProfileAndChatbotParity:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        if not cls.user_name or not cls.user_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD) are missing.")
        cls.client_id = cls.user_name
        API_CLIENT.set_credentials(cls.user_name, cls.user_pass)

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_profile_flow(self):
        logger.info(f"Saving insurance profile for {self.client_id}...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        payload_path = os.path.join(automation_root, "Data", "profile_dto.json")
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"Profile payload DTO not found at: {payload_path}")
            
        with open(payload_path, "r") as json_f:
            profile_dto = json.load(json_f)
            
        profile_dto["clientId"] = self.client_id
        
        res = UserActions.save_or_update_insurance_profile(profile_dto)
        assert res.status_code in [200, 201], f"Expected 200 or 201 but got {res.status_code}"
        
        logger.info(f"Fetching insurance profile for {self.client_id}...")
        res = UserActions.get_insurance_profile(self.client_id)
        assert res.status_code == 200
        profile_data = res.json()
        assert isinstance(profile_data, dict), "Expected profile details to be a dictionary object"
        
        # Business validation
        assert profile_data.get("clientId") == self.client_id, "Fetched profile client ID mismatch"
        assert "gender" in profile_data, "Profile missing 'gender' field"
        assert "employmentType" in profile_data, "Profile missing 'employmentType' field"
        assert "annualIncome" in profile_data, "Profile missing 'annualIncome' field"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_claims_history(self):
        logger.info(f"Fetching claims for {self.client_id}...")
        res = UserActions.get_all_claims_by_client_id(self.client_id)
        assert res.status_code == 200
        claims_data = res.json()
        assert isinstance(claims_data, dict), "Expected claims details to be a dictionary object"
        assert "claims" in claims_data, "Claims response missing 'claims' key"
        assert isinstance(claims_data["claims"], list), "Expected 'claims' field to be a list"
        
        # Business validations: Verify claims belong to client
        for claim in claims_data["claims"]:
            assert claim.get("clientId") == self.client_id, "Claim client ID mismatch"
        logger.info(f"Claims count: {len(claims_data['claims'])}")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_chatbot_sessions(self):
        logger.info("Listing sessions...")
        res = UserActions.list_chatbot_sessions()
        assert res.status_code == 200
        sessions = res.json()
        assert isinstance(sessions, list), "Expected sessions to be returned as a list"
        logger.info(f"Sessions found: {len(sessions)}")
        
        if sessions:
            session_id = sessions[0].get("id") or sessions[0].get("sessionId")
            assert session_id is not None, "Session object missing ID field"
            logger.info(f"Fetching history for session: {session_id}...")
            res_history = UserActions.get_chatbot_session_history(session_id)
            assert res_history.status_code == 200
            history = res_history.json()
            assert isinstance(history, list), "Expected chat history to be a list"
            logger.info(f"History fetched successfully. Size: {len(history)}")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_chatbot_agent_availability(self):
        logger.info("Checking agent availability...")
        res = UserActions.get_chatbot_agent_availability()
        assert res.status_code == 200
        availability = res.json()
        assert isinstance(availability, dict), "Expected agent availability details to be a dictionary object"
        logger.info(f"Agent availability: {availability}")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_user_roles(self):
        logger.info("Fetching user roles...")
        res = UserActions.get_logged_in_user_roles()
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
        user_info = res.json()
        assert isinstance(user_info, dict), "Expected user info to be returned as a dictionary object"
        assert "roles" in user_info, "User info missing 'roles' list"
        roles = user_info["roles"]
        assert isinstance(roles, list), "Expected roles to be a list"
        if roles:
            assert all(isinstance(role, (str, dict)) for role in roles), "Expected roles to contain string or dictionary items"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_tour_details(self):
        logger.info(f"Fetching tour details for {self.user_name}...")
        res = UserActions.get_tour_details(self.user_name)
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
        tour = res.json()
        assert isinstance(tour, dict), "Expected tour details to be a dictionary object"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_mobile_info(self):
        logger.info("Fetching mobile app info...")
        res = UserActions.get_mobile_app_info()
        assert res.status_code == 200
        app_info = res.json()
        assert isinstance(app_info, dict), "Expected app info response to be a dictionary object"
        assert "latestVersion" in app_info or "version" in app_info, "latestVersion/version metadata missing from response"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_check_pwned_password_range(self):
        logger.info("Querying compromised password range for hash prefix 848B1...")
        res = UserActions.check_pwned_password_range("848B1")
        assert res.status_code == 200
        assert len(res.text) > 0, "Response content should not be empty"
        assert ":" in res.text, "Response should be in 'SUFFIX:COUNT' format"
        logger.info("Successfully fetched pwned password hashes range and verified format.")
