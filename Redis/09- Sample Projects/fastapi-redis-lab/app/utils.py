"""Utility functions and middleware."""

import time
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request
from app import redis_client
from app.config import settings


async def check_rate_limit(identifier: str) -> bool:
    """
    Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (e.g., IP address, user ID)
        
    Returns:
        bool: True if within limit
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    rate_limit_key = f"rate_limit:{identifier}"
    client = await redis_client.get_redis()
    
    # Get current count
    current = await client.get(rate_limit_key)
    
    if current is None:
        # First request, set counter with expiry
        await client.setex(rate_limit_key, settings.rate_limit_window, 1)
        return True
    
    current_count = int(current)
    
    if current_count >= settings.rate_limit_requests:
        # Get TTL to inform user when they can try again
        ttl = await client.ttl(rate_limit_key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {ttl} seconds."
        )
    
    # Increment counter
    await client.incr(rate_limit_key)
    return True


def rate_limit(identifier_func: Callable[[Request], str]):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        identifier_func: Function to extract identifier from request
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = kwargs.get("request") or args[0]
            identifier = identifier_func(request)
            await check_rate_limit(identifier)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: FastAPI request
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded IP first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return request.client.host if request.client else "unknown"


async def generate_request_id() -> str:
    """
    Generate unique request ID.
    
    Returns:
        str: Unique request ID
    """
    timestamp = int(time.time() * 1000)
    client = await redis_client.get_redis()
    counter = await client.incr("request_id_counter")
    return f"{timestamp}-{counter}"


class CacheKeyBuilder:
    """Helper class for building consistent cache keys."""
    
    @staticmethod
    def product_list(skip: int, limit: int, category: str = None) -> str:
        """Build cache key for product list."""
        return f"products:list:{skip}:{limit}:{category or 'all'}"
    
    @staticmethod
    def product_detail(product_id: int) -> str:
        """Build cache key for product detail."""
        return f"products:detail:{product_id}"
    
    @staticmethod
    def cart(user_id: int) -> str:
        """Build cache key for cart."""
        return f"cart:user:{user_id}"
    
    @staticmethod
    def otp(phone: str) -> str:
        """Build cache key for OTP."""
        return f"otp:{phone}"
    
    @staticmethod
    def rate_limit(identifier: str) -> str:
        """Build cache key for rate limit."""
        return f"rate_limit:{identifier}"
    
    @staticmethod
    def session(session_id: str) -> str:
        """Build cache key for session."""
        return f"session:{session_id}"
    
    @staticmethod
    def lock(resource: str) -> str:
        """Build cache key for distributed lock."""
        return f"lock:{resource}"
