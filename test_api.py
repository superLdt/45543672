import requests
import json

url = "http://127.0.0.1:5000/api/dispatch/tasks/T2024001/confirm-with-vehicle"
payload = {
    "manifest_number": "MN2024001",
    "dispatch_number": "DP2024001",
    "license_plate": "京A12345",
    "carriage_number": "1",
    "actual_volume": 45.5,
    "volume_photo_url": "http://example.com/photo.jpg"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")