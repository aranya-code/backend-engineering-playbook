"""Analytics endpoints using Redis data structures."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db_session, get_optional_user_id
from app.schemas import LeaderboardResponse, LeaderboardItem, AnalyticsResponse
from app.services import AnalyticsService
from app.models import Product

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=50, description="Number of products to return"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get top viewed products leaderboard.
    
    Uses Redis Sorted Set to maintain product view rankings.
    """
    # Get leaderboard from Redis
    top_products = await AnalyticsService.get_leaderboard(limit)
    
    # Fetch product names from database
    product_ids = [item["product_id"] for item in top_products]
    
    if product_ids:
        result = await db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products = {p.id: p.name for p in result.scalars().all()}
    else:
        products = {}
    
    # Combine data
    leaderboard_items = [
        LeaderboardItem(
            product_id=item["product_id"],
            product_name=products.get(item["product_id"], f"Product {item['product_id']}"),
            views=item["views"]
        )
        for item in top_products
    ]
    
    return LeaderboardResponse(
        top_products=leaderboard_items,
        total=len(leaderboard_items)
    )


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: int = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive analytics.
    
    Combines multiple Redis data structures:
    - HyperLogLog for unique visitors
    - Bitmap for daily active users
    - Sorted Set for top products
    """
    # Track this visitor
    visitor_id = f"user:{user_id}"
    unique_visitors = await AnalyticsService.track_visitor(visitor_id)
    
    # Track daily login
    today = datetime.utcnow().strftime("%Y-%m-%d")
    await AnalyticsService.track_daily_login(user_id, today)
    daily_active_users = await AnalyticsService.get_daily_active_users(today)
    
    # Get leaderboard
    top_products_data = await AnalyticsService.get_leaderboard(10)
    
    # Fetch product names
    product_ids = [item["product_id"] for item in top_products_data]
    if product_ids:
        result = await db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products = {p.id: p.name for p in result.scalars().all()}
    else:
        products = {}
    
    # Build leaderboard items
    top_products = [
        LeaderboardItem(
            product_id=item["product_id"],
            product_name=products.get(item["product_id"], f"Product {item['product_id']}"),
            views=item["views"]
        )
        for item in top_products_data
    ]
    
    # Calculate total views
    total_views = sum(item.views for item in top_products)
    
    return AnalyticsResponse(
        unique_visitors=unique_visitors,
        total_views=total_views,
        daily_active_users=daily_active_users,
        top_products=top_products
    )
