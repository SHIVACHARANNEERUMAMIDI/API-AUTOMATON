import os
import json
import sys
import pytest
# Add current directory to path
sys.path.append(os.getcwd())

from utilities.api_client import API_CLIENT
from underwriter_api.document_actions import upload_document
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.digitization
class TestPolicyDocumentUpload:
    def test_policy_document_upload(self):
        user_name = os.getenv("USER_USERNAME")
        user_pass = os.getenv("USER_PASSWORD")
        client_id = os.getenv("TEST_CLIENT_ID", "919573464433")
        
        # Base file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        automation_root = os.path.dirname(current_dir)
        file_path = os.path.join(automation_root, "Data", "GoDigit Health Insurance 2.pdf")

        print(f"Login as USER ({user_name})...")
        API_CLIENT.set_credentials(user_name, user_pass)
        
        print(f"Uploading as User for Life Insurance...")
        # Load separate JSON payload
        payload_path = os.path.join(automation_root, "Data", "manual_upload_life.json")
        with open(payload_path, "r") as json_f:
            metadata = json.load(json_f)
        
        # Inject client_id from environment
        metadata["clientId"] = client_id
        # Serialize otherInformation as expected by the backend
        metadata["otherInformation"] = json.dumps(metadata["otherInformation"])
        
        data = {
            "documentType": "POLICY_DOCUMENT",
            "metadata": json.dumps(metadata)
        }

        with open(file_path, "rb") as f:
            files = {"file": ("manual_upload_life.pdf", f, "application/pdf")}
            res = API_CLIENT.post_multipart("fileUpload/uploadDocument", files=files, data=data)
        
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        
        assert res.status_code == 200, f"Upload document failed with code {res.status_code}: {res.text}"
        res_json = res.json()
        assert isinstance(res_json, dict), "Expected upload response to be a dictionary object"
        assert res_json.get("requestTypeId") is not None or res_json.get("registrationStatus") is True, f"Missing critical upload fields in response: {res_json}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
