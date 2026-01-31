"""Rate limiting utilities for FastAPI endpoints."""

import os
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

SESSION_COOKIE_NAME = "roboto_session"


def get_rate_limit_key(request: Request) -> str:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return f"session:{session_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["100/minute", "1000/hour"],
    storage_uri=os.getenv("REDIS_URL"),
    enabled=(os.getenv("RATE_LIMITING_ENABLED", "true").strip().lower() == "true"),
)

__all__ = [
    "limiter",
    "RateLimitExceeded",
    "_rate_limit_exceeded_handler",
    "get_rate_limit_key",
]
