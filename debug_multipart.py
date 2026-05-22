import requests
import os
import json
from utils.auth import get_access_token
from dotenv import load_dotenv

load_dotenv()

url = "https://api-dev.callmeooo.com/paisaplan/fileUpload/save"
token = get_access_token()
headers = {
    "Authorization": f"Bearer {token}",
    "X-Realm": "4healths"
}
params = {"id": "1504094099164225536"}

# Minimal multipart data
data = {
    "endorsementAction": "SUBMIT",
    "ticketId": "1504094099164225536",
    "requestDto": json.dumps({"endorsementDetails": {"status": "PENDING"}})
}
files = {
    "endorsementCopy": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")
}

print(f"Testing Multipart POST to URL: {url}")
res = requests.post(url, headers=headers, params=params, data=data, files=files, verify=False)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")
