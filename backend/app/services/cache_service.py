import json
import logging
import asyncio
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("app.cache")


class CacheService:
    _redis: Optional[aioredis.Redis] = None
    _memory_cache: dict = {}
    _initialized: bool = False

    @classmethod
    async def get_redis(cls) -> Optional[aioredis.Redis]:
        # Retry connection if previously failed or not initialized
        if cls._redis is None:
            try:
                # Reload settings REDIS_URL dynamically
                from app.core.config import Settings
                current_settings = Settings()
                url = current_settings.REDIS_URL

                if url and "upstash.io" in url and "mat_khau_cua_ban" not in url:
                    cls._redis = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=3.0)
                    await cls._redis.ping()
                    logger.info("Connected to Upstash Redis Cloud successfully!")
                elif url and "localhost" in url:
                    cls._redis = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=1.0)
                    await cls._redis.ping()
                    logger.info("Connected to Local Redis successfully!")
                else:
                    cls._redis = None
            except Exception as e:
                logger.warning(f"Redis connection failed, using In-Memory RAM Cache: {e}")
                cls._redis = None
            finally:
                cls._initialized = True
        return cls._redis

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                val = await redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis get error for {key}: {e}")

        if key in cls._memory_cache:
            item = cls._memory_cache[key]
            if item["expire_at"] is None or item["expire_at"] > asyncio.get_event_loop().time():
                return item["value"]
            else:
                del cls._memory_cache[key]
        return None

    @classmethod
    async def set(cls, key: str, value: Any, expire: int = 300):
        val_str = json.dumps(value, default=str)
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                await redis_client.set(key, val_str, ex=expire)
                return
            except Exception as e:
                logger.warning(f"Redis set error for {key}: {e}")

        cls._memory_cache[key] = {
            "value": value,
            "expire_at": asyncio.get_event_loop().time() + expire if expire else None
        }

    @classmethod
    async def invalidate(cls, prefix: str):
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys(f"{prefix}*")
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis invalidate error: {e}")

        keys_to_del = [k for k in cls._memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del cls._memory_cache[k]
