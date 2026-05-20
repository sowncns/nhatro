import uuid
import asyncio
import logging
from typing import Optional
from app.core.redis_client import RedisClient

logger = logging.getLogger("app.lock_helper")


class RedisDistributedLock:
    """Redis Distributed Lock context manager to prevent race conditions across multiple server instances.

    Key format: lock:user:{user_id}
    """

    def __init__(
        self,
        lock_key: str,
        expire_seconds: int = 10,
        acquire_timeout: float = 5.0,
        retry_interval: float = 0.1,
    ):
        """Args:

            lock_key: The Redis key for the lock (e.g. "lock:user:123").
            expire_seconds: Auto-expiration of the lock in seconds (prevents
              deadlocks if the client crashes).
            acquire_timeout: Maximum time in seconds to wait to acquire the lock
              before raising an error.
            retry_interval: Time to sleep in seconds between lock attempts.
        """
        self.lock_key = lock_key
        self.expire_seconds = expire_seconds
        self.acquire_timeout = acquire_timeout
        self.retry_interval = retry_interval
        self.token = str(uuid.uuid4())
        self.redis = None
        self.acquired = False

    async def acquire(self) -> bool:
        """Attempt to acquire the lock within the acquire_timeout limit."""
        try:
            self.redis = RedisClient.get_client()
        except Exception as e:
            logger.error(f"Failed to get Redis client for lock: {e}")
            # If Redis is unavailable, fallback: assume lock acquired to let DB row locking handle it.
            logger.warning("Redis offline. Proceeding without distributed lock (will rely on DB row locking).")
            self.acquired = True
            return True

        if not self.redis:
            # Fallback
            self.acquired = True
            return True

        end_time = asyncio.get_event_loop().time() + self.acquire_timeout
        while asyncio.get_event_loop().time() < end_time:
            try:
                # SET key value NX EX expire_seconds
                success = await self.redis.set(
                    self.lock_key,
                    self.token,
                    nx=True,
                    ex=self.expire_seconds
                )
                if success:
                    self.acquired = True
                    return True
            except Exception as e:
                logger.error(f"Error trying to acquire Redis lock: {e}")
                # Fallback on Redis exception
                self.acquired = True
                return True
                
            await asyncio.sleep(self.retry_interval)

        logger.warning(f"Timeout acquiring lock: {self.lock_key}")
        return False

    async def release(self) -> bool:
        """Release the lock safely using Lua script to verify ownership."""
        if not self.acquired or not self.redis:
            return False

        # If Redis is offline/fallback was triggered
        try:
            await self.redis.ping()
        except Exception:
            return False

        # Lua script ensures atomic check-and-delete
        lua_release = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            result = await self.redis.eval(lua_release, 1, self.lock_key, self.token)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to release Redis lock {self.lock_key}: {e}")
            return False

    async def __aenter__(self):
        success = await self.acquire()
        if not success:
            raise TimeoutError(f"Could not acquire lock for key {self.lock_key} within {self.acquire_timeout}s")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
