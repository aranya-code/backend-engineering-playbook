"""
Distributed lock implementation using Redis SET NX EX.

A distributed lock ensures that only one process can execute a critical
section at a time, even across multiple servers.

SET key value NX EX timeout
- NX: Only set if key does Not eXist (acquire lock)
- EX: Set an EXpiry in seconds (auto-release if holder crashes)
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Generator

from .redis_service import get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TIMEOUT = 10  # seconds
DEFAULT_ACQUIRE_TIMEOUT = 5  # seconds
RETRY_INTERVAL = 0.1  # seconds between acquisition attempts


def acquire_lock(
    lock_name: str,
    timeout: int = DEFAULT_LOCK_TIMEOUT,
    acquire_timeout: int = DEFAULT_ACQUIRE_TIMEOUT,
) -> str | None:
    """
    Attempt to acquire a distributed lock.

    Args:
        lock_name: Unique name for the lock.
        timeout: Lock expiry in seconds (auto-release safety).
        acquire_timeout: Max time to wait for lock acquisition.

    Returns:
        Lock token (UUID) if acquired, None if acquisition timed out.
    """
    r = get_redis_client()
    key = f"lock:{lock_name}"
    token = str(uuid.uuid4())
    end_time = time.time() + acquire_timeout

    while time.time() < end_time:
        acquired = r.set(key, token, nx=True, ex=timeout)
        if acquired:
            logger.info("Lock acquired: name=%s token=%s", lock_name, token[:8])
            return token
        time.sleep(RETRY_INTERVAL)

    logger.warning("Lock acquisition timed out: name=%s", lock_name)
    return None


def release_lock(lock_name: str, token: str) -> bool:
    """
    Release a distributed lock.

    Only releases the lock if the token matches (prevents releasing
    a lock held by another process).

    Uses a Lua script to make the check-and-delete atomic.

    Args:
        lock_name: The lock name used during acquisition.
        token: The token returned by acquire_lock().

    Returns:
        True if the lock was released, False if it was already expired
        or held by another process.
    """
    r = get_redis_client()
    key = f"lock:{lock_name}"

    # Lua script ensures atomic check-and-delete
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    result = r.eval(lua_script, 1, key, token)

    if result:
        logger.info("Lock released: name=%s token=%s", lock_name, token[:8])
        return True

    logger.warning("Lock release failed (token mismatch or expired): name=%s", lock_name)
    return False


@contextmanager
def distributed_lock(
    lock_name: str,
    timeout: int = DEFAULT_LOCK_TIMEOUT,
    acquire_timeout: int = DEFAULT_ACQUIRE_TIMEOUT,
) -> Generator[str | None, None, None]:
    """
    Context manager for distributed locking.

    Usage:
        with distributed_lock("process-payment") as token:
            if token:
                # Critical section — only one process at a time
                process_payment()
            else:
                raise Exception("Could not acquire lock")
    """
    token = acquire_lock(lock_name, timeout, acquire_timeout)
    try:
        yield token
    finally:
        if token:
            release_lock(lock_name, token)
