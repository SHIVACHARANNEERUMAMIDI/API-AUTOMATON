import os
import json
import pytest
from utils.api_client import API_CLIENT
from actions.user_actions import rm_callback_request
from dotenv import load_dotenv

load_dotenv()

class TestUserGeneralActionsFlow:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("USER_USERNAME", "919573464433")
        cls.user_pass = os.getenv("USER_PASSWORD", "Anuj@123")

    def test_rm_callback_request_flow(self):
        # --- STEP 0: ENSURE TASK IS CLAIMED BY UNDERWRITER (Requirement for Callback) ---
        uw_name = os.getenv("UW_USERNAME")
        uw_pass = os.getenv("UW_PASSWORD")
        
        print(f"\n[STEP 0] Ensuring task for {self.user_name} is claimed by Underwriter ({uw_name})...")
        API_CLIENT.set_credentials(uw_name, uw_pass)
        
        # Fetch the task for this user
        print(f"Fetching tasks for client ID: {self.user_name}...")
        res_task = API_CLIENT.post_graphql("""
        query getUnderWriterTasks($search: String, $searchType: ClientSearchType, $page: NonNegativeInt!, $size: PositiveInt!) {
          getUnderWriterTasks(search: $search, searchType: $searchType, page: $page, size: $size) {
            content {
              id
              isClaimed
              claimedBy {
                userName
              }
              clientId
            }
          }
        }
        """, {"search": self.user_name, "searchType": "USERNAME", "page": 0, "size": 10})
        
        assert res_task.status_code == 200, f"Failed to query underwriter tasks: {res_task.text}"
        tasks_list = res_task.json().get("data", {}).get("getUnderWriterTasks", {}).get("content", [])
        
        # Find the specific task for this user
        task = next((t for t in tasks_list if t.get("clientId") == self.user_name), None)
        
        if task and not task.get("isClaimed"):
            print(f"Task {task['id']} is unclaimed. Claiming it now...")
            claim_res = API_CLIENT.post_graphql("""
            mutation saveUnderWriterTask($claim: Boolean, $id: String!, $status: UnderWriterTaskStatus) {
              saveUnderWriterTask(claim: $claim, id: $id, status: $status) { id status }
            }
            """, {"claim": True, "id": str(task["id"]), "status": "IN_PROGRESS"})
            assert claim_res.status_code == 200, f"Failed to claim task: {claim_res.text}"
            print("Task claimed successfully.")
        elif task:
            print(f"Task is already claimed by {task['claimedBy']['userName'] if task.get('claimedBy') else 'someone'}.")
        else:
            print("Warning: No task found for this user. The callback might fail.")

        # --- STEP 1: LOGIN AS USER ---
        print(f"\n[STEP 1] Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)
        
        # --- STEP 2: SEND RM CALLBACK REQUEST ---
        print(f"[STEP 2] Sending RM Callback Request...")
        
        name = "Anuj Mankumare"
        email = "anujm0707@gmail.com"
        phone = "9573464433"
        insurance_type = "Motor Insurance - Four-Wheeler"
        
        res = rm_callback_request(name, email, phone, insurance_type)
        assert res.status_code == 200, f"Request failed: {res.text}"
        
        data = res.json().get("data", {}).get("rmCallbackRequest", {})
        print(f"DEBUG: RM Callback Response: {json.dumps(data, indent=2)}")
        
        assert data.get("success") is True or "is pending" in data.get("message", ""), f"Server returned failure: {data.get('message')}"
        print(f"RM Callback Request verified successfully. Message: {data.get('message')}")

        print("\n[FLOW COMPLETE] RM Callback Request Flow Finished Successfully.")
