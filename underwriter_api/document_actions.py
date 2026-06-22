import json
from utilities.api_client import API_CLIENT
from utilities.config import Config

class DocumentActions:
    @staticmethod
    def upload_document(file_path, client_id, request_type="SAVEPOLICY", insurance_type="Health Insurance", product_sub_type="General", custom_metadata=None):
        """
        POST /paisaplan/fileUpload/uploadDocument
        Uploads a document with metadata.
        """
        if custom_metadata is not None:
            metadata = custom_metadata
        else:
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
                    "providerId": Config.PROVIDER_ID,
                    "providerName": Config.PROVIDER_NAME
                })
            }

        data = {
            "documentType": "POLICY_DOCUMENT",
            "clientId": client_id,
            "clientType": "RETAIL_INDIVIDUAL",
            "requestType": request_type
        }

        # Serialize metadata in the request body/payload as required by the backend
        if custom_metadata is not None:
            # For custom metadata, make sure we format request body correctly
            data["metadata"] = json.dumps(metadata)

        with open(file_path, "rb") as f:
            files = {
                "file": ("upload.pdf", f, "application/pdf")
            }
            if custom_metadata is None:
                files["metadata"] = (None, json.dumps(metadata), "application/json")

            response = API_CLIENT.post_multipart("fileUpload/uploadDocument", files=files, data=data)

        return response
