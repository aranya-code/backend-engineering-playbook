"""Distributed locking implementation using Redis."""

import asyncio
import uuid
from typing import Optional
from contextlib import asynccontextmanager

from app import redis_client
from app.utils import CacheKeyBuilder


class DistributedLock:
    """Distributed lock implementation using Redis SET NX EX."""

    def __init__(self, resource: str, ttl: int = 10, retry_delay: float = 0.1):
        """
        Initialize distributed lock.
        
        Args:
            resource: Resource identifier to lock
            ttl: Lock timeout in seconds
            retry_delay: Delay between retry attempts
        """
        self.resource = resource
        self.ttl = ttl
        self.retry_delay = retry_delay
        self.lock_key = CacheKeyBuilder.lock(resource)
        self.lock_value = str(uuid.uuid4())
        self.acquired = False

    async def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire the lock.
        
        Args:
            blocking: If True, wait until lock is acquired
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            bool: True if lock acquired
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Try to acquire lock
            self.acquired = await redis_client.acquire_lock(
                self.lock_key,
                self.lock_value,
                self.ttl
            )
            
            if self.acquired:
                return True
            
            if not blocking:
                return False
            
            # Check timeout
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    return False
            
            # Wait before retry
            await asyncio.sleep(self.retry_delay)

    async def release(self) -> bool:
        """
        Release the lock.
        
        Returns:
            bool: True if lock released
        """
        if not self.acquired:
            return False
        
        released = await redis_client.release_lock(self.lock_key, self.lock_value)
        if released:
            self.acquired = False
        return released

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.release()


@asynccontextmanager
async def distributed_lock(resource: str, ttl: int = 10, timeout: Optional[float] = None):
    """
    Context manager for distributed lock.
    
    Args:
        resource: Resource identifier to lock
        ttl: Lock timeout in seconds
        timeout: Maximum time to wait for lock acquisition
        
    Yields:
        DistributedLock: Lock instance
        
    Example:
        async with distributed_lock("my_resource") as lock:
            # Critical section
            pass
    """
    lock = DistributedLock(resource, ttl=ttl)
    acquired = await lock.acquire(blocking=True, timeout=timeout)
    
    if not acquired:
        raise TimeoutError(f"Could not acquire lock for {resource}")
    
    try:
        yield lock
    finally:
        await lock.release()


async def with_lock(resource: str, ttl: int = 10):
    """
    Decorator for functions that need distributed locking.
    
    Args:
        resource: Resource identifier to lock
        ttl: Lock timeout in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with distributed_lock(resource, ttl=ttl):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
