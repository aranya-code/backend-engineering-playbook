"""Redis client configuration and helper functions."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        redis.Redis: Redis client
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=settings.redis_decode_responses,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# Helper functions for common Redis operations

async def set_cache(key: str, value: Any, ttl: int = settings.cache_ttl) -> bool:
    """
    Set value in Redis cache with TTL.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds
        
    Returns:
        bool: True if successful
    """
    client = await get_redis()
    serialized_value = json.dumps(value)
    return await client.setex(key, ttl, serialized_value)


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Optional[Any]: Cached value or None
    """
    client = await get_redis()
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def delete_cache(pattern: str) -> int:
    """
    Delete keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "products:*")
        
    Returns:
        int: Number of keys deleted
    """
    client = await get_redis()
    keys = []
    async for key in client.scan_iter(match=pattern):
        keys.append(key)
    
    if keys:
        return await client.delete(*keys)
    return 0


async def increment_counter(key: str, amount: int = 1) -> int:
    """
    Increment a counter in Redis.
    
    Args:
        key: Counter key
        amount: Amount to increment by
        
    Returns:
        int: New counter value
    """
    client = await get_redis()
    return await client.incrby(key, amount)


async def set_with_expiry(key: str, value: str, seconds: int) -> bool:
    """
    Set a key with expiry time.
    
    Args:
        key: Redis key
        value: Value to set
        seconds: Expiry time in seconds
        
    Returns:
        bool: True if successful
    """
    client = await get_redis()
    return await client.setex(key, seconds, value)


async def acquire_lock(lock_key: str, lock_value: str, ttl: int = 10) -> bool:
    """
    Acquire a distributed lock using Redis.
    
    Args:
        lock_key: Lock identifier
        lock_value: Unique value for this lock acquisition
        ttl: Lock timeout in seconds
        
    Returns:
        bool: True if lock acquired
    """
    client = await get_redis()
    return await client.set(lock_key, lock_value, nx=True, ex=ttl)


async def release_lock(lock_key: str, lock_value: str) -> bool:
    """
    Release a distributed lock.
    
    Args:
        lock_key: Lock identifier
        lock_value: Value used when acquiring lock
        
    Returns:
        bool: True if lock released
    """
    client = await get_redis()
    
    # Lua script to ensure we only delete our own lock
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    
    result = await client.eval(lua_script, 1, lock_key, lock_value)
    return bool(result)


async def add_to_sorted_set(key: str, member: str, score: float) -> int:
    """
    Add member to sorted set with score.
    
    Args:
        key: Sorted set key
        member: Member to add
        score: Score for ranking
        
    Returns:
        int: Number of elements added
    """
    client = await get_redis()
    return await client.zadd(key, {member: score})


async def get_sorted_set_range(key: str, start: int = 0, end: int = -1, desc: bool = True) -> list:
    """
    Get range from sorted set.
    
    Args:
        key: Sorted set key
        start: Start index
        end: End index (-1 for all)
        desc: If True, return in descending order
        
    Returns:
        list: List of (member, score) tuples
    """
    client = await get_redis()
    if desc:
        return await client.zrevrange(key, start, end, withscores=True)
    return await client.zrange(key, start, end, withscores=True)


async def hash_set(key: str, field: str, value: str) -> int:
    """
    Set field in hash.
    
    Args:
        key: Hash key
        field: Field name
        value: Field value
        
    Returns:
        int: 1 if new field, 0 if updated
    """
    client = await get_redis()
    return await client.hset(key, field, value)


async def hash_get_all(key: str) -> dict:
    """
    Get all fields from hash.
    
    Args:
        key: Hash key
        
    Returns:
        dict: All fields and values
    """
    client = await get_redis()
    return await client.hgetall(key)


async def hash_delete(key: str, *fields: str) -> int:
    """
    Delete fields from hash.
    
    Args:
        key: Hash key
        fields: Field names to delete
        
    Returns:
        int: Number of fields deleted
    """
    client = await get_redis()
    if fields:
        return await client.hdel(key, *fields)
    return 0
