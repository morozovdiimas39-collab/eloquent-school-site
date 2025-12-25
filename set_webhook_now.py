#!/usr/bin/env python3
import os
import json
import urllib.request

TOKEN = "8586405236:AAGSeZXHACvWk5u5DNgL95fMzvij-wbVASc"
WEBHOOK_URL = "https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7"

# Set webhook
url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
payload = {
    "url": WEBHOOK_URL,
    "allowed_updates": ["message", "callback_query", "pre_checkout_query", "successful_payment"]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode('utf-8'))
    print(json.dumps(result, indent=2))