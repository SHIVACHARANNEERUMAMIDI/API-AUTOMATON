import requests
import os
from utils.auth import get_access_token
from dotenv import load_dotenv

load_dotenv()

# Try with and without /paisaplan
urls = [
    "https://api-dev.callmeooo.com/paisaplan/fileUpload/save",
    "https://api-dev.callmeooo.com/fileUpload/save"
]

token = get_access_token()
headers = {
    "Authorization": f"Bearer {token}",
    "X-Realm": "4healths"
}
params = {"id": "1504094099164225536"}

for url in urls:
    print(f"\nTesting URL: {url}")
    try:
        res = requests.post(url, headers=headers, params=params, verify=False, timeout=5)
        print(f"Status: {res.status_code}")
        print(f"Body: {res.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
