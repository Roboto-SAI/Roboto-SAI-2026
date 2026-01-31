"""
Unit tests for security utilities.
"""
import pytest
import sys
import os

# Add backend to path so we can import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.security import hash_password, verify_password, clean_input, clean_dict_input

def test_hash_password():
    password = "securepassword123"
    hashed = hash_password(password)
    assert hashed != password.encode('utf-8')
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_clean_input():
    unsafe = "<script>alert('xss')</script>Hello"
    safe = clean_input(unsafe)
    assert "<script>" not in safe
    assert "Hello" in safe
    
    # Verify basic text remains
    assert clean_input("Normal text") == "Normal text"

def test_clean_dict_input():
    data = {
        "name": "<b>Bold</b>",
        "nested": {
            "comment": "<img src=x onerror=alert(1)>"
        },
        "number": 123
    }
    cleaned = clean_dict_input(data)
    
    assert "<b>" not in cleaned["name"]
    assert "Bold" in cleaned["name"]
    assert "<img" not in cleaned["nested"]["comment"]
    assert cleaned["number"] == 123
