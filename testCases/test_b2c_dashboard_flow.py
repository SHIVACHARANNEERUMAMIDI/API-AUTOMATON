import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.user_actions import UserActions
from utilities.customLogger import customLogger

logger = customLogger("TestB2CDashboard")

@pytest.mark.b2c
class TestB2CDashboard:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME")
        cls.user_pass = os.getenv("USER_PASSWORD")
        if not cls.user_name or not cls.user_pass:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD) are missing.")
        cls.client_id = cls.user_name
        API_CLIENT.set_credentials(cls.user_name, cls.user_pass)

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_b2c_fetch_personal_policies(self):
        """Fetch personal policies for the B2C client and validate schema structure."""
        logger.info(f"Fetching Personal Policies for Client ID: {self.client_id}...")
        res = UserActions.get_personal_policies(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPersonalPolicies" in data["data"], "Response data missing 'getPersonalPolicies'"
        policies = data["data"]["getPersonalPolicies"].get("policies")
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
        # Business validations: Verify that all returned policies belong to this client
        if policies:
            first_policy = policies[0]
            assert "id" in first_policy, "Policy object missing 'id'"
            assert "insuranceType" in first_policy, "Policy object missing 'insuranceType'"
            logger.info(f"Validated first policy ID: {first_policy.get('id')}")

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_b2c_fetch_portfolio_v2(self):
        """Fetch portfolio details (V2) and validate structural consistency."""
        logger.info(f"Fetching Portfolio V2 for Client ID: {self.client_id}...")
        res = UserActions.get_portfolio_v2(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPortfolioV2" in data["data"], "Response data missing 'getPortfolioV2'"
        
        portfolio = data["data"]["getPortfolioV2"]
        assert isinstance(portfolio, dict), "Expected 'getPortfolioV2' to return a dictionary"
        assert "data" in portfolio, "Portfolio missing 'data' key"
        assert isinstance(portfolio["data"], list), "Expected 'data' field to be a list/array of items"

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_b2c_fetch_all_claims(self):
        """Fetch claims history for the client and validate response shape."""
        logger.info(f"Fetching All Claims for Client ID: {self.client_id}...")
        res = UserActions.get_all_claims_by_client_id(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        claims = res.json()
        assert isinstance(claims, dict), "Expected claims response to be a dictionary"
        assert "claims" in claims, "Claims response missing 'claims' key"
        assert isinstance(claims["claims"], list), "Expected 'claims' field to be a list"
        
        # Business validations: check that all claims returned are for this client ID
        for claim in claims["claims"]:
            assert claim.get("clientId") == self.client_id, f"Claim clientId {claim.get('clientId')} does not match user {self.client_id}"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_risk_score(self):
        """Fetch risk scoring details and validate the response structure."""
        logger.info(f"Fetching Risk Score for Client ID: {self.client_id}...")
        res = UserActions.get_risk_score(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPortfolioV2" in data["data"], "Response data missing 'getPortfolioV2'"
        portfolio = data["data"]["getPortfolioV2"]
        assert "riskScore" in portfolio, "Response missing 'riskScore' in getPortfolioV2"
        assert isinstance(portfolio["riskScore"], dict), "riskScore should be a dictionary"

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_b2c_fetch_user_roles(self):
        """Fetch roles assigned to the currently logged in B2C user."""
        logger.info("Fetching User Roles (MT)...")
        res = UserActions.get_logged_in_user_roles()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        user_info = res.json()
        assert isinstance(user_info, dict), "Expected user info to be returned as a dictionary"
        assert "roles" in user_info, "User info missing 'roles' list"
        roles = user_info["roles"]
        assert isinstance(roles, list), "Expected roles to be a list"
        logger.info(f"Validated user roles list. Size: {len(roles)}")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_tour_details(self):
        """Fetch user-guided tour details for dashboard onboarding."""
        logger.info(f"Fetching Tour Details (MT) for {self.user_name}...")
        res = UserActions.get_tour_details(self.user_name)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        tour = res.json()
        assert isinstance(tour, dict), "Expected tour details to be returned as a dictionary object"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_insurance_type_data(self):
        """Fetch the system active insurance types master details."""
        logger.info("Fetching Insurance Type Data...")
        res = UserActions.get_insurance_type_data()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getInsuranceTypeData" in data["data"], "Response data missing 'getInsuranceTypeData'"
        assert isinstance(data["data"]["getInsuranceTypeData"], list), "Expected list of insurance type data items"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_master_data(self):
        """Fetch master categories lookup values (INSURANCETYPEDATA)."""
        logger.info("Fetching Master Data (INSURANCETYPEDATA)...")
        res = UserActions.get_master_data()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getMasterData" in data["data"], "Response data missing 'getMasterData'"
        master_data = data["data"]["getMasterData"]
        assert isinstance(master_data, dict), "Expected getMasterData to be a dictionary object"
        assert "response" in master_data, "getMasterData missing 'response' field"
        assert isinstance(master_data["response"], list), "Expected list of master data elements"

    @pytest.mark.P2
    @pytest.mark.Regression
    def test_b2c_fetch_rar_tickets(self):
        """Fetch Risk Analysis Report (RAR) tickets for client profile."""
        logger.info("Fetching RAR Tickets...")
        res = UserActions.get_risk_analysis_report_tickets()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "success" in data, "Response missing 'success' key"
        # B2C user should not have admin access
        assert data["success"] is False, "Expected success to be False for B2C user without admin privileges"
        assert "You do not have admin privileges" in data.get("message", ""), "Expected admin privilege error message"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_sales(self):
        """Fetch sales/portfolio performance analytics details."""
        logger.info("Fetching Sales...")
        res = UserActions.get_sales()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert isinstance(data, list), "Expected sales metrics to be a list"
        if data:
            assert "id" in data[0], "Sales item missing 'id'"
            assert "name" in data[0], "Sales item missing 'name'"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_list_chatbot_sessions(self):
        """List active and archived chatbot communication sessions."""
        logger.info("Listing Chatbot Sessions...")
        res = UserActions.list_chatbot_sessions()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        sessions = res.json()
        assert isinstance(sessions, list), "Expected sessions to be a list"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_chatbot_request_count(self):
        """Fetch the client request throttle counts for AI chatbot interactions."""
        logger.info("Getting Chatbot Request Count...")
        res = UserActions.get_chatbot_request_count()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        count_data = res.json()
        assert isinstance(count_data, int), "Expected request count details to be an integer"
        assert count_data >= 0, "Chatbot request count should be non-negative"

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_b2c_fetch_mobile_app_info(self):
        """Fetch the public mobile application configuration and version metadata."""
        logger.info("Fetching Mobile App Info (No Auth Required)...")
        res = UserActions.get_mobile_app_info()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        app_info = res.json()
        assert isinstance(app_info, dict), "Expected app info response to be a dictionary"
        assert "latestVersion" in app_info or "version" in app_info, "latestVersion/version metadata missing from response"
