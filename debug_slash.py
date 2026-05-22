import requests
import os
from utils.auth import get_access_token
from dotenv import load_dotenv

load_dotenv()

# Try with trailing slash
url = "https://api-dev.callmeooo.com/paisaplan/fileUpload/save/"

token = get_access_token()
headers = {
    "Authorization": f"Bearer {token}",
    "X-Realm": "4healths"
}
params = {"id": "1504094099164225536"}

print(f"Testing URL: {url}")
res = requests.post(url, headers=headers, params=params, verify=False)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")
