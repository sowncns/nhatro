"""Redis Client Singleton - NhaTro Manager"""
import logging
from typing import Optional
import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from app.core.config import settings

logger = logging.getLogger("app.redis")


class RedisClient:
    _instance: Optional["RedisClient"] = None
    _client: Optional[aioredis.Redis] = None
    _pool: Optional[aioredis.ConnectionPool] = None
    _is_healthy: bool = False

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_client(cls) -> Optional[aioredis.Redis]:
        """Get the Redis client singleton. Automatically initializes if not done yet."""
        if cls._client is None:
            cls.initialize()
        return cls._client

    @classmethod
    def initialize(cls) -> None:
        """Initialize the Redis client and connection pool using settings.REDIS_URL."""
        url = settings.REDIS_URL
        if not url:
            logger.warning("REDIS_URL is not set. Redis is disabled.")
            cls._client = None
            cls._pool = None
            cls._is_healthy = False
            return

        try:
            logger.info("Initializing Redis connection pool...")
            # We configure socket timeouts to prevent hanging during redis cloud outages
            cls._pool = aioredis.ConnectionPool.from_url(
                url,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
                retry_on_timeout=True,
                max_connections=50,
            )
            cls._client = aioredis.Redis(connection_pool=cls._pool)
            cls._is_healthy = False  # Will verify on ping
            logger.info("Redis client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}", exc_info=True)
            cls._client = None
            cls._pool = None
            cls._is_healthy = False

    @classmethod
    async def check_health(cls) -> bool:
        """Perform a ping to verify Redis server connection health."""
        if cls._client is None:
            cls.initialize()
            if cls._client is None:
                return False

        try:
            # Send a ping to check health
            await cls._client.ping()
            if not cls._is_healthy:
                logger.info("Redis connection established successfully (Health: OK).")
                cls._is_healthy = True
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            if cls._is_healthy or cls._is_healthy is None:
                logger.error(f"Redis health check failed. Redis server is offline: {e}")
            cls._is_healthy = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Redis health check: {e}")
            cls._is_healthy = False
            return False

    @classmethod
    async def close(cls) -> None:
        """Gracefully close Redis connections and pool."""
        if cls._client:
            logger.info("Closing Redis client...")
            try:
                await cls._client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
            cls._client = None

        if cls._pool:
            logger.info("Disconnecting Redis connection pool...")
            try:
                await cls._pool.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting Redis pool: {e}")
            cls._pool = None

        cls._is_healthy = False
        logger.info("Redis connection closed completely.")
