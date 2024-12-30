"""Cache utilities."""

import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional
from uuid import UUID
from loguru import logger
from pydantic import BaseModel

from redis import asyncio as aioredis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff


class ModelEncoder(json.JSONEncoder):
    """Custom JSON encoder for models and special types."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


class RedisCache:
    """Redis cache implementation."""

    _instance = None

    def __init__(self, url: Optional[str] = None):
        """Initialize Redis connection."""
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        retry = Retry(ExponentialBackoff(), 3)
        self.redis = aioredis.from_url(
            self.url,
            decode_responses=True,
            retry=retry,
            retry_on_timeout=True,
            socket_keepalive=True
        )

    @classmethod
    def get_instance(cls) -> "RedisCache":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache hit for {key}")
                return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            await self._reconnect()
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        try:
            # Handle lists of Pydantic models
            if isinstance(value, list) and value and isinstance(value[0], BaseModel):
                value = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in value
                ]

            await self.redis.setex(key, ttl, json.dumps(value, cls=ModelEncoder))
            logger.debug(f"Cache set for {key}")
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            await self._reconnect()

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache deleted for {key}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            await self._reconnect()

    async def _reconnect(self) -> None:
        """Attempt to reconnect to Redis."""
        try:
            await self.redis.close()
            retry = Retry(ExponentialBackoff(), 3)
            self.redis = aioredis.from_url(
                self.url,
                decode_responses=True,
                retry=retry,
                retry_on_timeout=True,
                socket_keepalive=True
            )
        except Exception as e:
            logger.error(f"Redis reconnection error: {e}")


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key = []
    # Handle special types in args
    for arg in args:
        if isinstance(arg, (UUID, BaseModel)):
            key.append(str(arg))
        elif hasattr(arg, '__class__'):
            # Use class name for class instances instead of str representation
            key.append(arg.__class__.__name__)
        else:
            key.append(str(arg))

    # Handle special types in kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (UUID, BaseModel)):
            key.append(f"{k}:{str(v)}")
        elif hasattr(v, '__class__'):
            # Use class name for class instances instead of str representation
            key.append(f"{k}:{v.__class__.__name__}")
        else:
            key.append(f"{k}:{v}")

    return ":".join(key)


def cache_result(ttl: int = 300):
    """Decorator to cache function results in Redis."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = RedisCache.get_instance()
            key = cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache first
            if result := await cache.get(key):
                return result

            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator
