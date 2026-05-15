import asyncio
import redis.asyncio as aioredis

async def clear_cache():
    url = "redis://localhost:6379/0" # Local redis
    try:
        r = aioredis.from_url(url)
        await r.flushdb()
        print("Local Redis cache cleared")
    except Exception as e:
        print(f"Local Redis failed: {e}")

    # Also try Upstash if configured
    try:
        from app.core.config import settings
        url = settings.REDIS_URL
        if url and "upstash.io" in url:
            r = aioredis.from_url(url)
            await r.flushdb()
            print("Upstash Redis cache cleared")
    except Exception as e:
        print(f"Upstash failed: {e}")

if __name__ == "__main__":
    asyncio.run(clear_cache())
