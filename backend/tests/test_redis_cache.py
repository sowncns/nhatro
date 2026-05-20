"""Automated test suite for Redis caching system, distributed locks, rate limiting, and fallback mechanics."""
import asyncio
import logging
import time
from typing import Dict, Any

from app.core.redis_client import RedisClient
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService, cached
from app.services.invalidate_helper import InvalidateHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_redis")


@cached(ttl=5, key_prefix="test:decorator")
async def calculate_square(x: int) -> Dict[str, Any]:
    logger.info(f"Computing square for {x} (Cache MISS)...")
    return {"input": x, "square": x * x, "timestamp": time.time()}


async def run_tests():
    logger.info("==================================================")
    logger.info("STARTING REDIS CACHE TEST SUITE")
    logger.info("==================================================")

    # ─── 1. Initialize Redis Client ──────────────────────────────
    logger.info("\n--- Test 1: Redis Client Initialization & Health Check ---")
    RedisClient.initialize()
    is_healthy = await RedisClient.check_health()
    logger.info(f"Redis Health Status: {'CONNECTED' if is_healthy else 'OFFLINE'}")
    assert is_healthy is True, "Redis should be online for this test suite"

    # ─── 2. Redis Service CRUD Operations ────────────────────────
    logger.info("\n--- Test 2: Redis Service CRUD operations ---")
    test_key = "test:crud:key1"
    test_value = {"status": "success", "data": [1, 2, 3], "nested": {"ok": True}}
    
    # Clean up before testing
    await RedisService.delete(test_key)
    
    # Test GET before set (should be None)
    val = await RedisService.get(test_key)
    assert val is None, f"Expected None, got {val}"
    logger.info("GET on missing key: OK (returned None)")

    # Test SET
    success = await RedisService.set(test_key, test_value, ttl=10)
    assert success is True, "SET should succeed"
    logger.info("SET key: OK")

    # Test GET after set (should match)
    val = await RedisService.get(test_key)
    assert val == test_value, f"Expected {test_value}, got {val}"
    logger.info("GET key: OK (correctly deserialized nested dict)")

    # Test EXISTS
    exists = await RedisService.exists(test_key)
    assert exists is True, "Key should exist"
    logger.info("EXISTS check: OK")

    # Test DELETE
    deleted = await RedisService.delete(test_key)
    assert deleted is True, "DELETE should succeed"
    logger.info("DELETE key: OK")

    # Test EXISTS after delete
    exists = await RedisService.exists(test_key)
    assert exists is False, "Key should no longer exist"
    logger.info("EXISTS after delete: OK")

    # ─── 3. Invalidation & Pattern Deletion ──────────────────────
    logger.info("\n--- Test 3: Pattern-based Cache Invalidation ---")
    keys_to_set = {
        "test:pattern:room1": "value1",
        "test:pattern:room2": "value2",
        "test:pattern:other": "value3"
    }
    for k, v in keys_to_set.items():
        await RedisService.set(k, v, ttl=20)

    # Invalidate by pattern
    deleted_count = await RedisService.delete_by_pattern("test:pattern:room*")
    logger.info(f"Pattern invalidation deleted {deleted_count} keys")
    assert deleted_count == 2, f"Expected 2 keys deleted, got {deleted_count}"

    assert await RedisService.get("test:pattern:room1") is None
    assert await RedisService.get("test:pattern:room2") is None
    assert await RedisService.get("test:pattern:other") == "value3"
    logger.info("Pattern invalidation: OK (correctly deleted matching keys and preserved others)")
    await RedisService.delete("test:pattern:other")

    # ─── 4. RAM Fallback Mechanism ──────────────────────────────
    logger.info("\n--- Test 4: RAM Fallback when Redis is offline ---")
    # Simulate Redis offline by patching health check and client
    original_client = RedisClient._client
    original_healthy = RedisClient._is_healthy
    
    try:
        # Force offline state
        RedisClient._client = None
        RedisClient._is_healthy = False
        
        fallback_key = "test:fallback:key1"
        fallback_val = {"ram": "fallback", "active": True}
        
        # Test CacheService SET (should fallback to RAM)
        await CacheService.set(fallback_key, fallback_val, expire=5)
        logger.info("SET under simulated offline Redis: OK (saved in RAM)")
        
        # Test CacheService GET (should read from RAM)
        val = await CacheService.get(fallback_key)
        assert val == fallback_val, f"Expected fallback value, got {val}"
        logger.info("GET under simulated offline Redis: OK (retrieved from RAM)")
        
        # Test expiration in RAM
        logger.info("Waiting 6 seconds for RAM cache expiration...")
        await asyncio.sleep(6)
        val_expired = await CacheService.get(fallback_key)
        assert val_expired is None, "Value should have expired in RAM"
        logger.info("RAM cache expiration check: OK")
        
    finally:
        # Restore Redis client
        RedisClient._client = original_client
        RedisClient._is_healthy = original_healthy

    # ─── 5. Distributed Locks ────────────────────────────────────
    logger.info("\n--- Test 5: Distributed Lock ---")
    lock_key = "test:lock:crit_section"
    
    # Try acquiring lock
    async with RedisService.distributed_lock(lock_key, ttl=5) as acquired1:
        assert acquired1 is True, "Should acquire lock successfully"
        logger.info("Acquired distributed lock: OK")
        
        # Attempt to acquire lock again concurrently (should fail)
        async with RedisService.distributed_lock(lock_key, ttl=5) as acquired2:
            assert acquired2 is False, "Concurrently acquiring locked key should fail"
            logger.info("Concurrent lock attempt blocked: OK")

    # Lock is automatically released, try acquiring again
    async with RedisService.distributed_lock(lock_key, ttl=5) as acquired3:
        assert acquired3 is True, "Lock should be re-acquired after release"
        logger.info("Re-acquired distributed lock after automatic context manager release: OK")

    # ─── 6. Rate Limiting ────────────────────────────────────────
    logger.info("\n--- Test 6: Rate Limiting ---")
    rate_key = "test:rate:client1"
    await RedisService.delete(rate_key)
    
    # Test allowed requests
    for i in range(5):
        allowed = await RedisService.rate_limit(rate_key, limit=5, window=10)
        assert allowed is True, f"Request {i+1} should be allowed"
    logger.info("First 5 requests within limit: OK (allowed)")

    # 6th request should be blocked
    blocked = await RedisService.rate_limit(rate_key, limit=5, window=10)
    assert blocked is False, "6th request should exceed limit and be blocked"
    logger.info("6th request: OK (blocked correctly)")

    # ─── 7. Caching Decorator ────────────────────────────────────
    logger.info("\n--- Test 7: Caching Decorator `@cached` ---")
    # Clean up decorator cache keys
    await CacheService.invalidate("test:decorator")
    
    # First call (Cache miss, triggers computation)
    res1 = await calculate_square(10)
    logger.info(f"Result 1: {res1}")
    
    # Second call (Cache hit, immediate return)
    res2 = await calculate_square(10)
    logger.info(f"Result 2: {res2}")
    
    assert res1["square"] == 100
    assert res1["timestamp"] == res2["timestamp"], "Timestamps must match, indicating cache hit"
    logger.info("Decorator caching: OK (cached return value)")

    # ─── 8. Invalidation Helpers ─────────────────────────────────
    logger.info("\n--- Test 8: Invalidation Helpers ---")
    org_id = "test_org"
    
    # Seed list and details
    await CacheService.set(f"rooms:list:{org_id}:page:1", ["room1", "room2"])
    await CacheService.set(f"rooms:detail:{org_id}:room123", {"id": "room123", "name": "Room 123"})
    await CacheService.set(f"dashboard:stats:{org_id}", {"total": 10})
    
    # Trigger room invalidation helper
    await InvalidateHelper.invalidate_room(org_id, "room123")
    
    # Check that they are deleted
    assert await CacheService.get(f"rooms:list:{org_id}:page:1") is None
    assert await CacheService.get(f"rooms:detail:{org_id}:room123") is None
    assert await CacheService.get(f"dashboard:stats:{org_id}") is None
    logger.info("Invalidation helper for Room: OK (all dependencies wiped successfully)")

    logger.info("\n==================================================")
    logger.info("ALL TESTS COMPLETED SUCCESSFULLY! 100% CORRECT")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
