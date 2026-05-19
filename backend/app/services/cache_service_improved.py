"""Improved Cache Service with Redis and fallback to in-memory cache"""
import json
import logging
import asyncio
from typing import Optional, Any, Callable, List
from functools import wraps
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("app.cache")


class ImprovedCacheService:
    """
    Enhanced cache service with:
    - Redis primary cache
    - In-memory fallback
    - Cache decorators
    - Batch operations
    - Cache warming
    """

    _redis: Optional[aioredis.Redis] = None
    _memory_cache: dict = {}
    _initialized: bool = False

    @classmethod
    async def initialize(cls):
        """Initialize Redis connection"""
        if cls._initialized:
            return

        try:
            if settings.REDIS_URL:
                cls._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=3.0,
                    socket_keepalive=True,
                    health_check_interval=30,
                )
                await cls._redis.ping()
                logger.info("✅ Connected to Redis successfully!")
            else:
                logger.warning("⚠️ REDIS_URL not configured, using in-memory cache only")
                cls._redis = None
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed, using in-memory cache: {e}")
            cls._redis = None
        finally:
            cls._initialized = True

    @classmethod
    async def get_redis(cls) -> Optional[aioredis.Redis]:
        """Get Redis client, initialize if needed"""
        if not cls._initialized:
            await cls.initialize()
        return cls._redis

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache"""
        redis_client = await cls.get_redis()

        # Try Redis first
        if redis_client:
            try:
                val = await redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis get error for {key}: {e}")

        # Fallback to memory cache
        if key in cls._memory_cache:
            item = cls._memory_cache[key]
            if item["expire_at"] is None or item["expire_at"] > asyncio.get_event_loop().time():
                return item["value"]
            else:
                del cls._memory_cache[key]

        return None

    @classmethod
    async def set(cls, key: str, value: Any, expire: int = 300):
        """Set value in cache with expiration"""
        val_str = json.dumps(value, default=str)
        redis_client = await cls.get_redis()

        # Try Redis first
        if redis_client:
            try:
                await redis_client.set(key, val_str, ex=expire)
                return
            except Exception as e:
                logger.warning(f"Redis set error for {key}: {e}")

        # Fallback to memory cache
        cls._memory_cache[key] = {
            "value": value,
            "expire_at": asyncio.get_event_loop().time() + expire if expire else None,
        }

    @classmethod
    async def delete(cls, key: str):
        """Delete specific key"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error for {key}: {e}")

        if key in cls._memory_cache:
            del cls._memory_cache[key]

    @classmethod
    async def invalidate(cls, prefix: str):
        """Invalidate all keys with given prefix"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                keys = await redis_client.keys(f"{prefix}*")
                if keys:
                    await redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis keys with prefix: {prefix}")
            except Exception as e:
                logger.warning(f"Redis invalidate error: {e}")

        # Memory cache
        keys_to_del = [k for k in cls._memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del cls._memory_cache[k]

        if keys_to_del:
            logger.info(f"Invalidated {len(keys_to_del)} memory cache keys with prefix: {prefix}")

    @classmethod
    async def get_many(cls, keys: List[str]) -> dict:
        """Get multiple keys at once"""
        redis_client = await cls.get_redis()
        result = {}

        if redis_client:
            try:
                values = await redis_client.mget(keys)
                for key, val in zip(keys, values):
                    if val:
                        result[key] = json.loads(val)
                return result
            except Exception as e:
                logger.warning(f"Redis mget error: {e}")

        # Fallback to memory cache
        for key in keys:
            val = await cls.get(key)
            if val is not None:
                result[key] = val

        return result

    @classmethod
    async def set_many(cls, items: dict, expire: int = 300):
        """Set multiple keys at once"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                pipe = redis_client.pipeline()
                for key, value in items.items():
                    val_str = json.dumps(value, default=str)
                    pipe.set(key, val_str, ex=expire)
                await pipe.execute()
                return
            except Exception as e:
                logger.warning(f"Redis mset error: {e}")

        # Fallback to memory cache
        for key, value in items.items():
            await cls.set(key, value, expire)

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if key exists"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                return await redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists error: {e}")

        return key in cls._memory_cache

    @classmethod
    async def increment(cls, key: str, amount: int = 1) -> int:
        """Increment counter"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                return await redis_client.incrby(key, amount)
            except Exception as e:
                logger.warning(f"Redis incr error: {e}")

        # Memory cache fallback
        if key not in cls._memory_cache:
            cls._memory_cache[key] = {"value": 0, "expire_at": None}

        cls._memory_cache[key]["value"] += amount
        return cls._memory_cache[key]["value"]

    @classmethod
    async def get_stats(cls) -> dict:
        """Get cache statistics"""
        redis_client = await cls.get_redis()
        stats = {
            "redis_connected": redis_client is not None,
            "memory_cache_size": len(cls._memory_cache),
        }

        if redis_client:
            try:
                info = await redis_client.info("stats")
                stats["redis_keys"] = info.get("db0", {}).get("keys", 0)
                stats["redis_hits"] = info.get("keyspace_hits", 0)
                stats["redis_misses"] = info.get("keyspace_misses", 0)
            except Exception as e:
                logger.warning(f"Redis stats error: {e}")

        return stats

    @classmethod
    async def clear_all(cls):
        """Clear all cache (use with caution!)"""
        redis_client = await cls.get_redis()

        if redis_client:
            try:
                await redis_client.flushdb()
                logger.warning("⚠️ Redis cache cleared!")
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        cls._memory_cache.clear()
        logger.warning("⚠️ Memory cache cleared!")


def cached(
    key_prefix: str,
    expire: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results

    Usage:
        @cached(key_prefix="user", expire=600)
        async def get_user(user_id: str):
            return await db.get(user_id)

        @cached(key_prefix="stats", key_builder=lambda org_id, date: f"stats:{org_id}:{date}")
        async def get_stats(org_id: str, date: str):
            return calculate_stats(org_id, date)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{args_str}:{kwargs_str}"

            # Try to get from cache
            cached_value = await ImprovedCacheService.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await ImprovedCacheService.set(cache_key, result, expire)

            return result

        return wrapper

    return decorator


def invalidate_cache(*prefixes: str):
    """
    Decorator to invalidate cache after function execution

    Usage:
        @invalidate_cache("user", "stats")
        async def update_user(user_id: str, data: dict):
            return await db.update(user_id, data)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            for prefix in prefixes:
                await ImprovedCacheService.invalidate(prefix)

            return result

        return wrapper

    return decorator
