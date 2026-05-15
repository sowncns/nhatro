import asyncio
from app.services.cache_service import CacheService

async def clear_cache():
    # Invalidate common prefixes
    prefixes = ["contracts:", "rooms:", "tenants:", "dashboard:", "boarding_houses:"]
    for p in prefixes:
        print(f"Invalidating {p}...")
        await CacheService.invalidate(p)
    print("Cache cleared!")

if __name__ == "__main__":
    asyncio.run(clear_cache())
