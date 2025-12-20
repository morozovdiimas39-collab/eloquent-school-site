import json
import urllib.request

url = "https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4"
data = {
    "action": "auto_assign_basic_words",
    "student_id": 7515380522,
    "count": 15
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print("Status Code:", response.status)
        print("Response:")
        print(result)
except Exception as e:
    print("Error:", str(e))
