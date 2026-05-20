"""Cache Service - High-level caching gateway with automatic RAM fallback and decorators"""
import time
import logging
import asyncio
from functools import wraps
from inspect import iscoroutinefunction
from typing import Optional, Any, Dict

from app.core.redis_client import RedisClient
from app.services.redis_service import RedisService

logger = logging.getLogger("app.cache_service")


class CacheService:
    _memory_cache: Dict[str, dict] = {}

    @classmethod
    async def get_redis(cls) -> Optional[Any]:
        """Backward compatibility for existing code. Returns raw redis client if healthy."""
        is_healthy = await RedisClient.check_health()
        if is_healthy:
            return RedisClient.get_client()
        return None

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.
        Fallback: If Redis is unhealthy/fails, reads from local In-Memory RAM cache.
        """
        is_healthy = await RedisClient.check_health()
        if is_healthy:
            val = await RedisService.get(key)
            if val is not None:
                return val

        # In-Memory RAM Fallback
        if key in cls._memory_cache:
            item = cls._memory_cache[key]
            now = time.time()
            if item["expire_at"] is None or item["expire_at"] > now:
                logger.info(f"Cache HIT (In-Memory RAM Fallback): key='{key}'")
                return item["value"]
            else:
                # Expired
                logger.info(f"Cache EXPIRED (In-Memory RAM Fallback): key='{key}'")
                del cls._memory_cache[key]
        return None

    @classmethod
    async def set(cls, key: str, value: Any, expire: int = 300) -> None:
        """
        Set value in Redis cache with TTL.
        Fallback: If Redis is unhealthy/fails, stores in local In-Memory RAM cache.
        """
        is_healthy = await RedisClient.check_health()
        if is_healthy:
            success = await RedisService.set(key, value, ttl=expire)
            if success:
                return

        # In-Memory RAM Fallback
        now = time.time()
        cls._memory_cache[key] = {
            "value": value,
            "expire_at": now + expire if expire else None
        }
        logger.info(f"Cache SET (In-Memory RAM Fallback): key='{key}', expire={expire}s")

    @classmethod
    async def invalidate(cls, prefix: str) -> None:
        """
        Invalidate cache keys matching a prefix.
        Invalidates both Redis (via pattern `prefix*`) and local In-Memory RAM cache.
        """
        # Invalidate in Redis
        is_healthy = await RedisClient.check_health()
        if is_healthy:
            await RedisService.delete_by_pattern(f"{prefix}*")

        # Invalidate in In-Memory RAM
        keys_to_del = [k for k in cls._memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del cls._memory_cache[k]
        if keys_to_del:
            logger.info(f"Cache INVALIDATED (In-Memory RAM Fallback): prefix='{prefix}' (deleted {len(keys_to_del)} keys)")


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    Works seamlessly on both async and sync functions.
    Usage:
        @cached(ttl=60, key_prefix="dashboard:stats")
        async def get_stats(self):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Compute cache key dynamically based on function arguments
            parts = [key_prefix or f"{func.__module__}:{func.__name__}"]
            # Exclude 'self' or 'cls' from cache key to ensure consistency
            clean_args = args[1:] if args and hasattr(args[0], "__dict__") else args
            if clean_args:
                parts.append(":".join(str(arg) for arg in clean_args))
            if kwargs:
                # Filter out standard dependencies like db session or tenant context
                clean_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ("db", "session", "ctx")
                }
                if clean_kwargs:
                    parts.append(":".join(f"{k}={v}" for k, v in sorted(clean_kwargs.items())))

            cache_key = ":".join(parts)
            
            # Check cache
            cached_val = await CacheService.get(cache_key)
            if cached_val is not None:
                return cached_val
                
            # Perform original computation
            val = await func(*args, **kwargs)
            
            # Cache the non-None result
            if val is not None:
                # Support Pydantic model dump if output is a model
                if hasattr(val, "model_dump"):
                    await CacheService.set(cache_key, val.model_dump(), expire=ttl)
                else:
                    await CacheService.set(cache_key, val, expire=ttl)
            return val
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            parts = [key_prefix or f"{func.__module__}:{func.__name__}"]
            clean_args = args[1:] if args and hasattr(args[0], "__dict__") else args
            if clean_args:
                parts.append(":".join(str(arg) for arg in clean_args))
            if kwargs:
                clean_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ("db", "session", "ctx")
                }
                if clean_kwargs:
                    parts.append(":".join(f"{k}={v}" for k, v in sorted(clean_kwargs.items())))

            cache_key = ":".join(parts)
            
            # Run async CacheService calls in the current thread's loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                # If the loop is already running (e.g. inside an async endpoint calling a sync func)
                # we just call the original function directly to prevent blocking
                return func(*args, **kwargs)
            else:
                cached_val = loop.run_until_complete(CacheService.get(cache_key))
                if cached_val is not None:
                    return cached_val
                
                val = func(*args, **kwargs)
                if val is not None:
                    if hasattr(val, "model_dump"):
                        loop.run_until_complete(CacheService.set(cache_key, val.model_dump(), expire=ttl))
                    else:
                        loop.run_until_complete(CacheService.set(cache_key, val, expire=ttl))
                return val

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper
    return decorator
