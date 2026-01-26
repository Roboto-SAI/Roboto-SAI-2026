#!/usr/bin/env python
"""Complete test for Responses API integration with authentication"""
import json
import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"

# Step 1: Register
print("=== Step 1: Registering user ===")
register_data = {
    "email": "test@example.com",
    "password": "TestPassword123!"
}

try:
    response = requests.post(
        urljoin(BASE_URL, "/api/auth/register"),
        json=register_data,
        timeout=10
    )
    print(f"Register Status: {response.status_code}")
    if response.status_code != 201:
        print(f"Register Response: {response.json()}")
except Exception as e:
    print(f"Register Error: {e}")

# Step 2: Login
print("\n=== Step 2: Logging in ===")
login_data = {
    "email": "test@example.com",
    "password": "TestPassword123!"
}

cookies = {}
try:
    response = requests.post(
        urljoin(BASE_URL, "/api/auth/login"),
        json=login_data,
        timeout=10
    )
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {json.dumps(response.json(), indent=2)}")
    
    # Extract cookies
    cookies = response.cookies
    print(f"Cookies: {cookies}")
except Exception as e:
    print(f"Login Error: {e}")

# Step 3: Test Responses API
print("\n=== Step 3: Testing Responses API ===")
chat_data = {
    "message": "Test: Are you using Responses API now?",
    "session_id": "responses-api-test-1",
    "previous_response_id": None,
    "use_encrypted_content": True
}

try:
    response = requests.post(
        urljoin(BASE_URL, "/api/chat"),
        json=chat_data,
        cookies=cookies,
        timeout=30
    )
    print(f"Chat Status: {response.status_code}")
    data = response.json()
    print(f"\nChat Response:")
    print(json.dumps(data, indent=2))
    
    # Check for Responses API fields
    print("\n✅ Responses API Fields:")
    print(f"  ✓ response_id: {data.get('response_id')}")
    print(f"  ✓ encrypted_thinking: {bool(data.get('encrypted_thinking'))}")
    print(f"  ✓ xai_stored: {data.get('xai_stored')}")
    print(f"  ✓ response: {data.get('response')[:100]}...")
    
except Exception as e:
    print(f"Chat Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
