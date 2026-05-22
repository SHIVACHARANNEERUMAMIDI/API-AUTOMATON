import json
from utils.api_client import API_CLIENT

def upload_document(file_path, client_id, request_type="SAVEPOLICY", insurance_type="Health Insurance", product_sub_type="General"):
    """
    POST /paisaplan/fileUpload/uploadDocument
    Uploads a document with metadata.
    """
    # Map insurance type to valid ProductType enum (GENERAL or LIFE)
    product_type_enum = "LIFE" if insurance_type == "Life Insurance" else "GENERAL"
    
    metadata = {
        "clientId": client_id,
        "clientType": "RETAIL_INDIVIDUAL",
        "requestType": request_type,
        "otherInformation": json.dumps({
            "insuranceType": insurance_type,
            "productType": product_type_enum,
            "productSubType": product_sub_type,
            "providerId": "123",
            "providerName": "AutoTestProvider"
        })
    }
    
    data = {
        "documentType": "POLICY_DOCUMENT",
        "clientId": client_id,
        "clientType": "RETAIL_INDIVIDUAL",
        "requestType": request_type
    }
    
    with open(file_path, "rb") as f:
        files = {
            "file": ("upload.pdf", f, "application/pdf"),
            "metadata": (None, json.dumps(metadata), "application/json")
        }
        response = API_CLIENT.post_multipart("fileUpload/uploadDocument", files=files, data=data)
    
    return response
