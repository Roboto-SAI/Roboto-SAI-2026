"""Redis client utilities for caching."""

import json
import logging
import os
from typing import Any, Optional

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional dependency
    redis = None

logger = logging.getLogger(__name__)

_redis_client: Optional[Any] = None


async def get_redis_client() -> Optional[Any]:
    """Get or create async Redis client."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url or redis is None:
        return None

    try:
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        await _redis_client.ping()
        logger.info("Redis connected")
    except Exception as exc:
        logger.warning(f"Redis connection failed: {exc}")
        _redis_client = None

    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis_client()
    if client is None:
        return None
    try:
        value = await client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:
        logger.warning(f"Cache get error: {exc}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    client = await get_redis_client()
    if client is None:
        return False
    try:
        payload = json.dumps(value, default=str)
        await client.setex(key, ttl, payload)
        return True
    except Exception as exc:
        logger.warning(f"Cache set error: {exc}")
        return False


async def cache_delete(key: str) -> bool:
    client = await get_redis_client()
    if client is None:
        return False
    try:
        await client.delete(key)
        return True
    except Exception as exc:
        logger.warning(f"Cache delete error: {exc}")
        return False
