"""Fingerprint utilities for deduplication."""

from __future__ import annotations

import hashlib
from typing import Any


def generate_fingerprint(user_input: Any, roboto_response: Any) -> str:
    """Generate a stable fingerprint for a conversation pair."""
    normalized = f"{str(user_input).strip()}::{str(roboto_response).strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
