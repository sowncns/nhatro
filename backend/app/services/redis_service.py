"""Redis Service - Core Redis operations, distributed locks, and rate limiting"""
import json
import logging
from typing import Optional, Any, List
from contextlib import asynccontextmanager
from app.core.redis_client import RedisClient

logger = logging.getLogger("app.redis_service")


class RedisService:
    @staticmethod
    def _serialize(value: Any) -> str:
        """Helper to serialize complex Python objects into JSON strings."""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, default=str)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return str(value)

    @staticmethod
    def _deserialize(value: str) -> Any:
        """Helper to deserialize JSON strings back into Python objects."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If it's not a JSON string, return raw value
            return value

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from Redis. Safely falls back to None on Redis failures."""
        client = RedisClient.get_client()
        if client is None:
            return None

        try:
            val = await client.get(key)
            if val is not None:
                logger.info(f"Cache HIT: key='{key}'")
                return cls._deserialize(val)
            logger.info(f"Cache MISS: key='{key}'")
            return None
        except Exception as e:
            logger.error(f"Redis GET error (key={key}): {e}")
            return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl: Optional[int] = 300) -> bool:
        """Set value in Redis with a TTL. Safely falls back to False on Redis failures."""
        client = RedisClient.get_client()
        if client is None:
            return False

        try:
            serialized_val = cls._serialize(value)
            if ttl:
                await client.set(key, serialized_val, ex=ttl)
            else:
                await client.set(key, serialized_val)
            logger.info(f"Cache SET: key='{key}', ttl={ttl}")
            return True
        except Exception as e:
            logger.error(f"Redis SET error (key={key}): {e}")
            return False

    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete key from Redis. Safely falls back to False on Redis failures."""
        client = RedisClient.get_client()
        if client is None:
            return False

        try:
            deleted = await client.delete(key)
            if deleted:
                logger.info(f"Cache DEL: key='{key}'")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Redis DELETE error (key={key}): {e}")
            return False

    @classmethod
    async def delete_by_pattern(cls, pattern: str) -> int:
        """Delete keys matching a glob pattern (e.g. 'rooms:list:*'). Safely falls back to 0."""
        client = RedisClient.get_client()
        if client is None:
            return 0

        try:
            # We fetch all matching keys using async keys
            # (In production, SCAN is preferred, but for smaller lists KEYS is safe. Let's use scan_iter)
            keys: List[str] = []
            async for k in client.scan_iter(match=pattern):
                keys.append(k)

            if keys:
                await client.delete(*keys)
                logger.info(f"Cache INVALIDATED by pattern: '{pattern}' (deleted {len(keys)} keys)")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE PATTERN error (pattern={pattern}): {e}")
            return 0

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if a key exists in Redis. Safely falls back to False on Redis failures."""
        client = RedisClient.get_client()
        if client is None:
            return False

        try:
            count = await client.exists(key)
            return count > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error (key={key}): {e}")
            return False

    @classmethod
    @asynccontextmanager
    async def distributed_lock(cls, lock_key: str, ttl: int = 10):
        """
        Context manager for distributed locking.
        Usage:
            async with RedisService.distributed_lock("my_lock", ttl=5) as acquired:
                if acquired:
                    # Do critical work
        """
        client = RedisClient.get_client()
        acquired = False
        if client is None:
            # Redis not connected
            yield False
            return

        try:
            # NX=True sets the key only if it does not exist
            acquired = await client.set(lock_key, "1", ex=ttl, nx=True)
            if acquired:
                logger.info(f"Acquired distributed lock: '{lock_key}'")
            yield bool(acquired)
        except Exception as e:
            logger.error(f"Redis distributed lock error (lock_key={lock_key}): {e}")
            yield False
        finally:
            if acquired:
                try:
                    await client.delete(lock_key)
                    logger.info(f"Released distributed lock: '{lock_key}'")
                except Exception as e:
                    logger.error(f"Failed to release distributed lock (lock_key={lock_key}): {e}")

    @classmethod
    async def rate_limit(cls, key: str, limit: int, window: int) -> bool:
        """
        Pipeline-based sliding/fixed window rate limiting.
        Returns True if request is allowed, False if limit is exceeded.
        """
        client = RedisClient.get_client()
        if client is None:
            return True  # Bypass rate limiting if Redis is unavailable

        try:
            async with client.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                await pipe.expire(key, window, nx=True)
                results = await pipe.execute()
                current_count = results[0]
                if current_count > limit:
                    logger.warning(f"Rate limit exceeded for key='{key}' ({current_count}/{limit})")
                    return False
                return True
        except Exception as e:
            logger.error(f"Redis rate_limit error (key={key}): {e}")
            return True  # Bypass on Redis failure
