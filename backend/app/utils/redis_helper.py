import json
import logging
from typing import Optional, Dict, Any, List
from app.core.redis_client import RedisClient

logger = logging.getLogger("app.redis_helper")


class RedisSessionHelper:
    """Helper to manage active sessions and user session list in Redis cache with fallback mechanism."""

    @staticmethod
    def _get_client():
        try:
            return RedisClient.get_client()
        except Exception as e:
            logger.error(f"Error getting Redis client: {e}")
            return None

    @classmethod
    async def cache_session(cls, session_id: str, data: Dict[str, Any], ttl: int) -> bool:
        """Cache a session object in Redis.

        Key: session:{session_id}
        """
        client = cls._get_client()
        if not client:
            return False
        try:
            key = f"session:{session_id}"
            await client.set(key, json.dumps(data), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache session {session_id} in Redis: {e}")
            return False

    @classmethod
    async def get_cached_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached session from Redis."""
        client = cls._get_client()
        if not client:
            return None
        try:
            key = f"session:{session_id}"
            raw_data = await client.get(key)
            if raw_data:
                return json.loads(raw_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached session {session_id} from Redis: {e}")
            return None

    @classmethod
    async def revoke_cached_session(cls, session_id: str, user_id: str) -> bool:
        """Revoke (delete) a session from Redis cache and remove it from the user's active session list."""
        client = cls._get_client()
        if not client:
            return False
        try:
            session_key = f"session:{session_id}"
            user_key = f"user:{user_id}:sessions"
            
            # Use Redis pipeline to delete both atomically
            async with client.pipeline(transaction=True) as pipe:
                pipe.delete(session_key)
                pipe.srem(user_key, session_id)
                await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to revoke cached session {session_id} from Redis: {e}")
            return False

    @classmethod
    async def add_user_session_to_list(cls, user_id: str, session_id: str) -> bool:
        """Add a session ID to the user's active session list in Redis.

        Key: user:{user_id}:sessions (Set)
        """
        client = cls._get_client()
        if not client:
            return False
        try:
            key = f"user:{user_id}:sessions"
            await client.sadd(key, session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to add session {session_id} to user list in Redis: {e}")
            return False

    @classmethod
    async def get_user_sessions_list(cls, user_id: str) -> List[str]:
        """Get all active session IDs for a user from Redis."""
        client = cls._get_client()
        if not client:
            return []
        try:
            key = f"user:{user_id}:sessions"
            sessions = await client.smembers(key)
            return list(sessions) if sessions else []
        except Exception as e:
            logger.error(f"Failed to get user sessions from Redis: {e}")
            return []

    @classmethod
    async def revoke_all_user_sessions_cached(cls, user_id: str) -> bool:
        """Revoke all cached sessions for a user."""
        client = cls._get_client()
        if not client:
            return False
        try:
            user_key = f"user:{user_id}:sessions"
            session_ids = await client.smembers(user_key)
            if not session_ids:
                return True
                
            async with client.pipeline(transaction=True) as pipe:
                for sid in session_ids:
                    pipe.delete(f"session:{sid}")
                pipe.delete(user_key)
                await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to revoke all cached sessions for user {user_id}: {e}")
            return False
