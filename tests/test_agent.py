#!/usr/bin/env python3
import json
import requests

url = "http://127.0.0.1:1234/v1/chat/completions"
payload = {
    "model": "local-model",
    "messages": [{"role": "user", "content": "Respond with: {\"test\": true}"}],
    "temperature": 0.7,
    "max_tokens": 100,
}

print("[1] Sending request...")
try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"[2] Got status {response.status_code}")
    data = response.json()
    print(f"[3] Response: {data['choices'][0]['message']['content']}")
except Exception as e:
    print(f"[!] Error: {e}")
