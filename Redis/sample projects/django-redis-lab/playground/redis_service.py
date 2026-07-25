"""
Redis service — the single point of contact for all Redis operations.

Every Redis command in the project goes through this module.
Views and services never call Redis directly; they call functions here.

This separation makes it easy to:
- Mock Redis in tests
- Switch Redis clients
- Add logging/metrics to all Redis operations
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis client singleton
# ---------------------------------------------------------------------------

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """
    Return a shared Redis client instance.

    Uses a module-level singleton so we don't create a new TCP connection
    for every request. The redis-py client is thread-safe.
    """
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # Return str instead of bytes
        )
    return _client


# ---------------------------------------------------------------------------
# Shopping Cart — Redis Hash
# ---------------------------------------------------------------------------

def cart_add_item(user_id: int, product_id: int, quantity: int) -> None:
    """
    Add or update an item in the user's shopping cart.

    Uses HINCRBY to atomically increment the quantity. If the field
    doesn't exist, it's created with the given quantity.

    Key pattern: cart:user:{user_id}
    Field: product_id
    Value: quantity
    """
    r = get_redis_client()
    key = f"cart:user:{user_id}"
    r.hincrby(key, str(product_id), quantity)
    logger.info("Cart updated: user=%s product=%s qty=+%s", user_id, product_id, quantity)


def cart_get(user_id: int) -> dict[str, str]:
    """
    Retrieve all items in a user's cart.

    Returns a dict of {product_id: quantity}.
    """
    r = get_redis_client()
    key = f"cart:user:{user_id}"
    return r.hgetall(key)


def cart_clear(user_id: int) -> int:
    """
    Remove the entire cart for a user.

    Returns 1 if the key was deleted, 0 if it didn't exist.
    """
    r = get_redis_client()
    key = f"cart:user:{user_id}"
    result = r.delete(key)
    logger.info("Cart cleared: user=%s (deleted=%s)", user_id, result)
    return result


# ---------------------------------------------------------------------------
# OTP — String with TTL
# ---------------------------------------------------------------------------

OTP_TTL_SECONDS = 300  # 5 minutes


def otp_store(email: str, otp_code: str) -> None:
    """
    Store an OTP code for the given email with a 300-second TTL.

    Uses SET with EX (expiry in seconds). Redis automatically deletes
    the key after the TTL expires — no cleanup needed.

    Key pattern: otp:{email}
    """
    r = get_redis_client()
    key = f"otp:{email}"
    r.set(key, otp_code, ex=OTP_TTL_SECONDS)
    logger.info("OTP stored: email=%s ttl=%ss", email, OTP_TTL_SECONDS)


def otp_verify(email: str, otp_code: str) -> bool:
    """
    Verify an OTP code and delete it if valid (one-time use).

    Returns True if the OTP matches, False otherwise.
    """
    r = get_redis_client()
    key = f"otp:{email}"
    stored_otp = r.get(key)

    if stored_otp is not None and stored_otp == otp_code:
        r.delete(key)  # OTP consumed — delete immediately
        logger.info("OTP verified: email=%s", email)
        return True

    logger.warning("OTP verification failed: email=%s", email)
    return False


# ---------------------------------------------------------------------------
# Rate Limiter — INCR + EXPIRE
# ---------------------------------------------------------------------------

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # max requests per window


def rate_limit_check(identifier: str) -> tuple[bool, int]:
    """
    Check if the identifier has exceeded the rate limit.

    Uses INCR to atomically increment the counter. On the first request
    in a window, sets EXPIRE to create the sliding window.

    Args:
        identifier: Unique key (e.g., IP address, user ID).

    Returns:
        Tuple of (is_allowed, current_count).
    """
    r = get_redis_client()
    key = f"rate_limit:{identifier}"

    current_count = r.incr(key)

    if current_count == 1:
        # First request in this window — set expiry
        r.expire(key, RATE_LIMIT_WINDOW)

    is_allowed = current_count <= RATE_LIMIT_MAX_REQUESTS
    return is_allowed, current_count


# ---------------------------------------------------------------------------
# Product View Counter — INCR
# ---------------------------------------------------------------------------

def view_counter_increment(product_id: int) -> int:
    """
    Increment the view counter for a product.

    INCR is atomic — safe under concurrent requests.
    Returns the new count.
    """
    r = get_redis_client()
    key = f"product:views:{product_id}"
    count = r.incr(key)
    return count


def view_counter_get(product_id: int) -> int:
    """Get the current view count for a product."""
    r = get_redis_client()
    key = f"product:views:{product_id}"
    count = r.get(key)
    return int(count) if count else 0


# ---------------------------------------------------------------------------
# Leaderboard — Sorted Set
# ---------------------------------------------------------------------------

LEADERBOARD_KEY = "leaderboard:product_views"


def leaderboard_update(product_id: int, product_name: str, score: int) -> None:
    """
    Update a product's score in the leaderboard.

    ZADD with the current view count as the score.
    The member is stored as "product_id:product_name" for display purposes.
    """
    r = get_redis_client()
    member = f"{product_id}:{product_name}"
    r.zadd(LEADERBOARD_KEY, {member: score})


def leaderboard_top(count: int = 10) -> list[dict[str, Any]]:
    """
    Get the top N products by view count.

    ZREVRANGE returns members in descending score order.
    """
    r = get_redis_client()
    results = r.zrevrange(LEADERBOARD_KEY, 0, count - 1, withscores=True)

    leaderboard = []
    for rank, (member, score) in enumerate(results, start=1):
        parts = member.split(":", 1)
        product_id = int(parts[0])
        product_name = parts[1] if len(parts) > 1 else "Unknown"
        leaderboard.append({
            "rank": rank,
            "product_id": product_id,
            "product_name": product_name,
            "views": int(score),
        })

    return leaderboard


# ---------------------------------------------------------------------------
# HyperLogLog — Unique Visitor Count
# ---------------------------------------------------------------------------

HYPERLOGLOG_KEY = "analytics:unique_visitors"


def hyperloglog_add(visitor_id: str) -> int:
    """
    Add a visitor identifier to the HyperLogLog.

    Returns 1 if the internal representation was altered, 0 otherwise.
    The count is approximate (0.81% standard error) but uses ~12 KB
    regardless of the number of unique elements.
    """
    r = get_redis_client()
    return r.pfadd(HYPERLOGLOG_KEY, visitor_id)


def hyperloglog_count() -> int:
    """Return the approximate number of unique visitors."""
    r = get_redis_client()
    return r.pfcount(HYPERLOGLOG_KEY)


# ---------------------------------------------------------------------------
# Bitmap — Daily Login Tracker
# ---------------------------------------------------------------------------


def bitmap_key_today() -> str:
    """Generate a bitmap key for today's date."""
    from datetime import date
    return f"bitmap:daily_login:{date.today().isoformat()}"


def bitmap_mark_login(user_id: int) -> None:
    """
    Mark a user as logged in today.

    Each bit position represents a user ID.
    SETBIT sets the bit at position user_id to 1.
    """
    r = get_redis_client()
    key = bitmap_key_today()
    r.setbit(key, user_id, 1)
    r.expire(key, 86400 * 7)  # Keep for 7 days
    logger.info("Bitmap login marked: user=%s", user_id)


def bitmap_check_login(user_id: int) -> bool:
    """Check if a user has logged in today."""
    r = get_redis_client()
    key = bitmap_key_today()
    return bool(r.getbit(key, user_id))


def bitmap_login_count() -> int:
    """Count total unique logins today."""
    r = get_redis_client()
    key = bitmap_key_today()
    return r.bitcount(key)


# ---------------------------------------------------------------------------
# Cache Invalidation
# ---------------------------------------------------------------------------

def clear_product_cache() -> int:
    """
    Clear all product-related cache keys.

    Uses SCAN to find matching keys without blocking Redis (unlike KEYS).
    Returns the number of keys deleted.
    """
    r = get_redis_client()
    deleted = 0
    cursor = 0

    while True:
        cursor, keys = r.scan(cursor, match="django_redis_lab:*product*", count=100)
        if keys:
            r.delete(*keys)
            deleted += len(keys)
        if cursor == 0:
            break

    logger.info("Cache cleared: %s keys deleted", deleted)
    return deleted


def clear_all_cache() -> None:
    """Flush the entire cache (use with caution)."""
    from django.core.cache import cache
    cache.clear()
    logger.info("All cache cleared")
