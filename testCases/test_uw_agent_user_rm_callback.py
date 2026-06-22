import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.user_actions import UserActions
from utilities.customLogger import customLogger
from utilities.config import Config

logger = customLogger("TestUwAgentUserRmCallback")

@pytest.mark.agent
class TestUwAgentUserRmCallback:
    @classmethod
    def setup_class(cls):
        # RC1: Credentials loaded from .env via Config (no hardcoded values)
        cls.user_name = Config.UW_AGENT_USERNAME
        cls.user_pass = Config.UW_AGENT_PASSWORD
        cls.uw_name = Config.UW_USERNAME
        cls.uw_pass = Config.UW_PASSWORD

        if not cls.user_name or not cls.user_pass or not cls.uw_name or not cls.uw_pass:
            raise ValueError(
                "Mandatory environment variables (UW_AGENT_USERNAME, UW_AGENT_PASSWORD, "
                "UW_USERNAME, UW_PASSWORD) are missing."
            )

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_rm_callback_request_flow(self):
        # --- STEP 0: ENSURE TASK IS CLAIMED BY UNDERWRITER ---
        logger.info(f"Ensuring task for {self.user_name} is claimed by Underwriter ({self.uw_name})...")
        API_CLIENT.set_credentials(self.uw_name, self.uw_pass)

        logger.info(f"Fetching tasks for client ID: {self.user_name}...")
        res_task = UserActions.get_underwriter_tasks(self.user_name, search_type="USERNAME")

        assert res_task.status_code == 200, f"Failed to query underwriter tasks: {res_task.text}"
        tasks_list = res_task.json().get("data", {}).get("getUnderWriterTasks", {}).get("content", [])

        # Find the specific task for this user
        task = next((t for t in tasks_list if t.get("clientId") == self.user_name), None)

        if task and not task.get("isClaimed"):
            logger.info(f"Task {task['id']} is unclaimed. Claiming it now...")
            claim_res = UserActions.claim_underwriter_task(task["id"], claim=True, status="IN_PROGRESS")
            assert claim_res.status_code == 200, f"Failed to claim task: {claim_res.text}"
            logger.info("Task claimed successfully.")
        elif task:
            logger.info(f"Task is already claimed by {task['claimedBy']['userName'] if task.get('claimedBy') else 'someone'}.")
        else:
            logger.warning("Warning: No task found for this user. The callback might fail.")

        # --- STEP 1: LOGIN AS USER ---
        logger.info(f"Login as USER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        # --- STEP 2: SEND RM CALLBACK REQUEST ---
        logger.info("Sending RM Callback Request...")

        # RC1: Test data loaded from data/test_users.json via Config (no hardcoded values)
        name = Config.USER_FULL_NAME
        email = Config.USER_EMAIL
        phone = Config.USER_PHONE
        insurance_type = Config.USER_INSURANCE_TYPE

        res = UserActions.rm_callback_request(name, email, phone, insurance_type)
        assert res.status_code == 200, f"Request failed: {res.text}"

        json_resp = res.json()
        data = json_resp.get("data", {}).get("rmCallbackRequest") or {}

        logger.info(f"RM Callback Response: {json.dumps(json_resp, indent=2)}")

        # Business validations
        assert data.get("success") is True or "is pending" in data.get("message", ""), \
            f"Server returned failure. Full response: {json_resp}"
        logger.info(f"RM Callback Request verified successfully. Message: {data.get('message')}")
        logger.info("RM Callback Request Flow Finished Successfully.")
