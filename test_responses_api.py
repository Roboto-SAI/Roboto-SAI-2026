#!/usr/bin/env python
"""Test Responses API integration"""
import json
import requests

url = "http://localhost:5000/api/chat"

# Test with Responses API parameters
payload = {
    "message": "Test: Are you using Responses API now?",
    "session_id": "responses-api-test-1",
    "previous_response_id": None,
    "use_encrypted_content": True
}

headers = {
    "Content-Type": "application/json"
}

print("Testing Responses API integration...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    
    data = response.json()
    print(f"\nResponse:")
    print(json.dumps(data, indent=2))
    
    # Check for Responses API fields
    print("\n✓ Responses API Fields:")
    print(f"  - response_id: {data.get('response_id')}")
    print(f"  - encrypted_thinking: {data.get('encrypted_thinking')}")
    print(f"  - xai_stored: {data.get('xai_stored')}")
    
except Exception as e:
    print(f"Error: {e}")
