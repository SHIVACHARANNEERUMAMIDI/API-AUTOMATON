import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import DocumentActions
from utilities.customLogger import customLogger

logger = customLogger("TestPolicyDocumentUpload")

@pytest.mark.digitization
class TestPolicyDocumentUpload:
    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_policy_document_upload(self):
        user_name = os.getenv("USER_USERNAME")
        user_pass = os.getenv("USER_PASSWORD")
        client_id = os.getenv("TEST_CLIENT_ID")
        
        if not user_name or not user_pass or not client_id:
            raise ValueError("Mandatory environment variables (USER_USERNAME, USER_PASSWORD, TEST_CLIENT_ID) are missing.")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Policy PDF file not found at: {file_path}")

        logger.info(f"Login as USER ({user_name})...")
        API_CLIENT.set_credentials(user_name, user_pass)
        
        logger.info("Uploading as User for Life Insurance...")
        payload_path = os.path.join(automation_root, "Data", "manual_upload_life.json")
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"Payload JSON file not found at: {payload_path}")
            
        with open(payload_path, "r") as json_f:
            metadata = json.load(json_f)
        
        metadata["clientId"] = client_id
        metadata["otherInformation"] = json.dumps(metadata["otherInformation"])
        
        res = DocumentActions.upload_document(
            file_path=file_path,
            client_id=client_id,
            request_type="SAVEPOLICY",
            custom_metadata=metadata
        )
        
        logger.info(f"Status Code: {res.status_code}")
        
        assert res.status_code == 200, f"Upload document failed with code {res.status_code}: {res.text}"
        res_json = res.json()
        assert isinstance(res_json, dict), "Expected upload response to be a dictionary object"
        
        # Business validations
        assert res_json.get("requestTypeId") is not None or res_json.get("registrationStatus") is True, f"Missing critical upload fields in response: {res_json}"
        if res_json.get("requestTypeId"):
            logger.info(f"Document upload successfully verified. Ticket ID: {res_json.get('requestTypeId')}")
