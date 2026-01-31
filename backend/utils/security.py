"""
Security utilities for Roboto SAI.
Includes password hashing (bcrypt) and input sanitization (bleach).
"""

import logging
from typing import Optional, Dict, Any
import bcrypt
import bleach

logger = logging.getLogger(__name__)

def hash_password(password: str) -> bytes:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): Plain text password.
        
    Returns:
        bytes: Hashed password.
    """
    try:
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError("Failed to hash password")

def verify_password(password: str, hashed: bytes) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password (str): Plain text password to check.
        hashed (bytes): The stored hash.
        
    Returns:
        bool: True if match, False otherwise.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def clean_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS.
    
    Args:
        text (str): Input text.
        
    Returns:
        str: Sanitized text.
    """
    if not text:
        return ""
    try:
        # Allow only safe tags and attributes (empty list = remove all tags)
        return bleach.clean(text, tags=[], strip=True)
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        # Fail safe: return empty string or original if critical
        return ""

def clean_dict_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize strings in a dictionary.
    """
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = clean_input(value)
        elif isinstance(value, dict):
            cleaned[key] = clean_dict_input(value)
        else:
            cleaned[key] = value
    return cleaned
