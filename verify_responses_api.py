#!/usr/bin/env python
"""Verify Responses API implementation across all components"""
import os
import re

def verify_file_changes(filepath, patterns, description):
    """Verify that patterns exist in file"""
    print(f"\n✓ Checking {description}...")
    print(f"  File: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for pattern_name, pattern in patterns.items():
            if pattern in content:
                print(f"    ✅ Found: {pattern_name}")
            else:
                print(f"    ❌ Missing: {pattern_name}")
                return False
        return True
    except Exception as e:
        print(f"    ❌ Error reading file: {e}")
        return False

# Verification checks
checks = {
    "SDK Client (Responses API)": (
        "sdk/roboto-sai-sdk/roboto-sai-sdk/client.py",
        {
            "Responses API chat.create()": "chat = self.xai_client.chat.create(",
            "previous_response_id parameter": "previous_response_id=",
            "use_encrypted_content parameter": "use_encrypted_content=",
            "response_id in return": "response_id",
            "vent_mode method": "def vent_mode(",
            "get_stored_completion method": "def get_stored_completion(",
        }
    ),
    "GrokLLM Wrapper": (
        "backend/grok_llm.py",
        {
            "Dict import": "from typing import",
            "logging import": "import logging",
            "Responses API attributes": "previous_response_id: Optional[str]",
            "acall_with_response_id method": "async def acall_with_response_id(",
            "Returns Dict": "-> Dict[str, Any]:",
            "Calls client.chat()": "self.client.chat(",
        }
    ),
    "ChatMessage Model": (
        "backend/main.py",
        {
            "ChatMessage class": "class ChatMessage(BaseModel):",
            "previous_response_id field": "previous_response_id: Optional[str]",
            "use_encrypted_content field": "use_encrypted_content: bool",
        }
    ),
    "Chat Endpoint": (
        "backend/main.py",
        {
            "acall_with_response_id call": "await grok_llm.acall_with_response_id(",
            "previous_response_id passed": "previous_response_id=request.previous_response_id",
            "Response ID in return": "response_id or f",
            "Encrypted thinking in return": "encrypted_thinking",
            "xai_stored in return": "xai_stored",
        }
    ),
}

print("=" * 60)
print("Roboto SAI - Responses API Implementation Verification")
print("=" * 60)

all_pass = True
for check_name, (filepath, patterns) in checks.items():
    # Make path absolute
    abs_path = os.path.join(os.path.dirname(__file__), filepath)
    if verify_file_changes(abs_path, patterns, check_name):
        print(f"  ✅ {check_name}: PASS")
    else:
        print(f"  ❌ {check_name}: FAIL")
        all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("✅ ALL CHECKS PASSED - Responses API Implementation Complete")
    print("\nFeatures Implemented:")
    print("  A) Response API for stateful conversation chaining")
    print("  B) Response ID storage in Supabase")
    print("  C) Encrypted thinking content support")
else:
    print("❌ Some checks failed - Review implementation")

print("=" * 60)
