import os
import json
import pytest
from utils.api_client import API_CLIENT
from actions.user_actions import (
    get_personal_policies, 
    get_portfolio_v2, 
    get_all_claims_by_client_id, 
    get_risk_score,
    get_expired_policies_year_limit,
    get_child_and_parent_company_details,
    get_smart_advisory_tips,
    update_login_time,
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

class TestB2CUserFlow:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME", "9542994704")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")
        cls.client_id = cls.user_name # Assuming username is the clientId for B2C

    def test_b2c_dashboard_flow(self):
        # --- STEP 1: LOGIN AS USER ---
        print(f"\n[STEP 1] Login as B2C USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # --- STEP 2: GET PERSONAL POLICIES ---
        print(f"[STEP 2] Fetching Personal Policies for Client ID: {self.client_id}...")
        res = get_personal_policies(self.client_id)
        assert res.status_code == 200
        
        # --- STEP 3: GET PORTFOLIO V2 ---
        print(f"[STEP 3] Fetching Portfolio V2 for Client ID: {self.client_id}...")
        res = get_portfolio_v2(self.client_id)
        assert res.status_code == 200
        
        # --- STEP 4: GET ALL CLAIMS ---
        print(f"[STEP 4] Fetching All Claims for Client ID: {self.client_id}...")
        res = get_all_claims_by_client_id(self.client_id)
        assert res.status_code == 200

        # --- STEP 5: GET RISK SCORE ---
        print(f"[STEP 5] Fetching Risk Score for Client ID: {self.client_id}...")
        res = get_risk_score(self.client_id)
        assert res.status_code == 200

        # --- STEP 6: GET USER ROLES (MT) ---
        print(f"[STEP 6] Fetching User Roles (MT)...")
        res = get_logged_in_user_roles()
        assert res.status_code == 200
        print(f"DEBUG: User Roles found: {len(res.json()) if isinstance(res.json(), list) else 'N/A'}")

        # --- STEP 7: GET TOUR DETAILS (MT) ---
        print(f"[STEP 7] Fetching Tour Details (MT) for {self.user_name}...")
        res = get_tour_details(self.user_name)
        assert res.status_code == 200

        # --- STEP 8: GET INSURANCE TYPE DATA ---
        print(f"[STEP 8] Fetching Insurance Type Data...")
        res = get_insurance_type_data()
        assert res.status_code == 200
        
        # --- STEP 9: GET MASTER DATA ---
        print(f"[STEP 9] Fetching Master Data (INSURANCETYPEDATA)...")
        res = get_master_data()
        assert res.status_code == 200

        # --- STEP 10: GET RAR TICKETS ---
        print(f"[STEP 10] Fetching RAR Tickets...")
        res = get_risk_analysis_report_tickets()
        assert res.status_code == 200
        
        # --- STEP 11: GET SALES ---
        print(f"[STEP 11] Fetching Sales...")
        res = get_sales()
        assert res.status_code == 200

        # --- STEP 12: GET CHATBOT SESSIONS ---
        print(f"[STEP 12] Listing Chatbot Sessions...")
        res = list_chatbot_sessions()
        assert res.status_code == 200
        
        # --- STEP 13: GET CHATBOT REQUEST COUNT ---
        print(f"[STEP 13] Getting Chatbot Request Count...")
        res = get_chatbot_request_count()
        assert res.status_code == 200

        # --- STEP 14: GET MOBILE APP INFO ---
        print(f"[STEP 14] Fetching Mobile App Info (No Auth Required)...")
        res = get_mobile_app_info()
        assert res.status_code == 200

        print("\n[FLOW COMPLETE] Full B2C Dashboard Flow Finished Successfully.")
