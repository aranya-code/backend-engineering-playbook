"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db
from app.redis_client import get_redis


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in get_db():
        yield session


async def get_redis_client() -> redis.Redis:
    """
    Dependency to get Redis client.
    
    Returns:
        redis.Redis: Redis client
    """
    return await get_redis()


async def get_current_user_id(
    x_user_id: int = Header(..., description="User ID from authentication")
) -> int:
    """
    Dependency to get current user ID from header.
    
    Args:
        x_user_id: User ID from X-User-Id header
        
    Returns:
        int: User ID
        
    Raises:
        HTTPException: If user ID is invalid
    """
    if x_user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return x_user_id


async def get_optional_user_id(
    x_user_id: int = Header(None, description="Optional User ID")
) -> int:
    """
    Dependency to get optional user ID from header.
    
    Args:
        x_user_id: Optional user ID from X-User-Id header
        
    Returns:
        int: User ID or default value
    """
    return x_user_id if x_user_id else 1
