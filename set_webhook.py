import json
import urllib.request
import os

# Get token from environment
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN environment variable not set")
    exit(1)

# API endpoint
url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"

# Payload
payload = {
    "url": "https://functions.yandexcloud.net/d4eb3ckc7i9h81v7gcre",
    "allowed_updates": ["message", "callback_query", "pre_checkout_query"]
}

# Convert to JSON bytes
data = json.dumps(payload).encode('utf-8')

# Create request
req = urllib.request.Request(
    url,
    data=data,
    headers={'Content-Type': 'application/json'}
)

# Make request
try:
    with urllib.request.urlopen(req) as response:
        response_data = response.read().decode('utf-8')
        result = json.loads(response_data)
        
        print("=== TELEGRAM API RESPONSE ===")
        print(json.dumps(result, indent=2))
        
        if result.get('ok'):
            print("\n✓ Webhook set successfully!")
        else:
            print("\n✗ Webhook setup failed!")
            
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
