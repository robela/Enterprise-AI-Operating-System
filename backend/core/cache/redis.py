"""Redis cache client and helpers."""
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

from backend.core.config.settings import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


async def init_redis() -> None:
    global _redis
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        _redis = client
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — cache disabled for this session", exc)
        _redis = None


async def close_redis() -> None:
    if _redis:
        await _redis.aclose()


def get_redis() -> Redis | None:
    return _redis


async def cache_get(key: str) -> str | None:
    if _redis is None:
        return None
    return await _redis.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    if _redis is None:
        return
    await _redis.setex(key, ttl, str(value))


async def cache_delete(key: str) -> None:
    if _redis is None:
        return
    await _redis.delete(key)


async def cache_get_json(key: str) -> dict | None:
    import json
    raw = await cache_get(key)
    return json.loads(raw) if raw else None


async def cache_set_json(key: str, value: dict, ttl: int = 300) -> None:
    import json
    await cache_set(key, json.dumps(value), ttl)