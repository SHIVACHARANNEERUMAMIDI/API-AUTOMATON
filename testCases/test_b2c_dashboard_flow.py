import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.user_actions import (
    get_personal_policies, 
    get_portfolio_v2, 
    get_all_claims_by_client_id, 
    get_risk_score,
    get_logged_in_user_roles,
    get_insurance_type_data,
    get_master_data,
    get_risk_analysis_report_tickets,
    get_sales,
    get_mobile_app_info,
    list_chatbot_sessions,
    get_chatbot_request_count,
    get_tour_details
)
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.b2c
class TestB2CDashboardFlow:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME", "9542994704")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.client_id = cls.user_name # Assuming username is the clientId for B2C
        API_CLIENT.set_credentials(cls.user_name, cls.user_pass)

    def test_b2c_fetch_personal_policies(self):
        """Fetch personal policies for the B2C client and validate schema structure."""
        print(f"\nFetching Personal Policies for Client ID: {self.client_id}...")
        res = get_personal_policies(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPersonalPolicies" in data["data"], "Response data missing 'getPersonalPolicies'"
        policies = data["data"]["getPersonalPolicies"].get("policies")
        assert isinstance(policies, list), "Expected 'policies' to be a list"
        
        if policies:
            first_policy = policies[0]
            assert "id" in first_policy, "Policy object missing 'id'"
            assert "insuranceType" in first_policy, "Policy object missing 'insuranceType'"
            print(f"Validated first policy ID: {first_policy.get('id')}")

    def test_b2c_fetch_portfolio_v2(self):
        """Fetch portfolio details (V2) and validate structural consistency."""
        print(f"\nFetching Portfolio V2 for Client ID: {self.client_id}...")
        res = get_portfolio_v2(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPortfolioV2" in data["data"], "Response data missing 'getPortfolioV2'"
        
        portfolio = data["data"]["getPortfolioV2"]
        assert isinstance(portfolio, dict), "Expected 'getPortfolioV2' to return a dictionary"
        assert "data" in portfolio, "Portfolio missing 'data' key"
        assert isinstance(portfolio["data"], list), "Expected 'data' field to be a list/array of items"

    def test_b2c_fetch_all_claims(self):
        """Fetch claims history for the client and validate response shape."""
        print(f"\nFetching All Claims for Client ID: {self.client_id}...")
        res = get_all_claims_by_client_id(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        claims = res.json()
        assert isinstance(claims, dict), "Expected claims response to be a dictionary"
        assert "claims" in claims, "Claims response missing 'claims' key"
        assert isinstance(claims["claims"], list), "Expected 'claims' field to be a list"

    def test_b2c_fetch_risk_score(self):
        """Fetch risk scoring details and validate the response structure."""
        print(f"\nFetching Risk Score for Client ID: {self.client_id}...")
        res = get_risk_score(self.client_id)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getPortfolioV2" in data["data"], "Response data missing 'getPortfolioV2'"
        portfolio = data["data"]["getPortfolioV2"]
        assert "riskScore" in portfolio, "Response missing 'riskScore' in getPortfolioV2"
        assert isinstance(portfolio["riskScore"], dict), "riskScore should be a dictionary"

    def test_b2c_fetch_user_roles(self):
        """Fetch roles assigned to the currently logged in B2C user."""
        print(f"\nFetching User Roles (MT)...")
        res = get_logged_in_user_roles()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        user_info = res.json()
        assert isinstance(user_info, dict), "Expected user info to be returned as a dictionary"
        assert "roles" in user_info, "User info missing 'roles' list"
        roles = user_info["roles"]
        assert isinstance(roles, list), "Expected roles to be a list"
        print(f"Validated user roles list. Size: {len(roles)}")

    def test_b2c_fetch_tour_details(self):
        """Fetch user-guided tour details for dashboard onboarding."""
        print(f"\nFetching Tour Details (MT) for {self.user_name}...")
        res = get_tour_details(self.user_name)
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        tour = res.json()
        assert isinstance(tour, dict), "Expected tour details to be returned as a dictionary object"

    def test_b2c_fetch_insurance_type_data(self):
        """Fetch the system active insurance types master details."""
        print(f"\nFetching Insurance Type Data...")
        res = get_insurance_type_data()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getInsuranceTypeData" in data["data"], "Response data missing 'getInsuranceTypeData'"
        assert isinstance(data["data"]["getInsuranceTypeData"], list), "Expected list of insurance type data items"

    def test_b2c_fetch_master_data(self):
        """Fetch master categories lookup values (INSURANCETYPEDATA)."""
        print(f"\nFetching Master Data (INSURANCETYPEDATA)...")
        res = get_master_data()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "data" in data, "Response body missing 'data' key"
        assert "getMasterData" in data["data"], "Response data missing 'getMasterData'"
        master_data = data["data"]["getMasterData"]
        assert isinstance(master_data, dict), "Expected getMasterData to be a dictionary object"
        assert "response" in master_data, "getMasterData missing 'response' field"
        assert isinstance(master_data["response"], list), "Expected list of master data elements"

    def test_b2c_fetch_rar_tickets(self):
        """Fetch Risk Analysis Report (RAR) tickets for client profile."""
        print(f"\nFetching RAR Tickets...")
        res = get_risk_analysis_report_tickets()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert "success" in data, "Response missing 'success' key"
        assert data["success"] is False, "Expected success to be False for B2C user without admin privileges"
        assert "You do not have admin privileges" in data.get("message", ""), "Expected admin privilege error message"

    def test_b2c_fetch_sales(self):
        """Fetch sales/portfolio performance analytics details."""
        print(f"\nFetching Sales...")
        res = get_sales()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        data = res.json()
        assert isinstance(data, list), "Expected sales metrics to be a list"
        if data:
            assert "id" in data[0], "Sales item missing 'id'"
            assert "name" in data[0], "Sales item missing 'name'"

    def test_b2c_list_chatbot_sessions(self):
        """List active and archived chatbot communication sessions."""
        print(f"\nListing Chatbot Sessions...")
        res = list_chatbot_sessions()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        sessions = res.json()
        assert isinstance(sessions, list), "Expected sessions to be a list"

    def test_b2c_fetch_chatbot_request_count(self):
        """Fetch the client request throttle counts for AI chatbot interactions."""
        print(f"\nGetting Chatbot Request Count...")
        res = get_chatbot_request_count()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        count_data = res.json()
        assert isinstance(count_data, int), "Expected request count details to be an integer"
        assert count_data >= 0, "Chatbot request count should be non-negative"

    def test_b2c_fetch_mobile_app_info(self):
        """Fetch the public mobile application configuration and version metadata."""
        print(f"\nFetching Mobile App Info (No Auth Required)...")
        res = get_mobile_app_info()
        assert res.status_code == 200, f"Expected status code 200 but got {res.status_code}"
        
        app_info = res.json()
        assert isinstance(app_info, dict), "Expected app info response to be a dictionary"
        assert "latestVersion" in app_info or "version" in app_info, "latestVersion/version metadata missing from response"
