"""Service layer for business logic."""

import json
import random
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, CartItem
from app import redis_client
from app.config import settings


class ProductService:
    """Service for product-related operations."""

    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        """
        Create a new product.
        
        Args:
            db: Database session
            product_data: Product data
            
        Returns:
            Product: Created product
        """
        product = Product(**product_data.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        # Invalidate cache
        await redis_client.delete_cache("products:list:*")
        
        return product

    @staticmethod
    async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
        """
        Get product by ID with caching.
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            Optional[Product]: Product or None
        """
        # Try cache first
        cache_key = f"products:detail:{product_id}"
        cached = await redis_client.get_cache(cache_key)
        
        if cached:
            # Return cached data as dict (would need to convert to Product for type safety)
            return cached
        
        # Fetch from database
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if product:
            # Cache the product
            product_dict = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
            await redis_client.set_cache(cache_key, product_dict, ttl=settings.cache_ttl)
            
            # Increment view counter
            await redis_client.increment_counter(f"products:views:{product_id}")
            
            # Update leaderboard
            await redis_client.add_to_sorted_set(
                "products:leaderboard",
                str(product_id),
                float(await redis_client.get_redis().get(f"products:views:{product_id}") or 0)
            )
        
        return product

    @staticmethod
    async def get_products(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None
    ) -> tuple[List[Product], int]:
        """
        Get list of products with caching.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by category
            
        Returns:
            tuple: (List of products, total count)
        """
        # Try cache
        cache_key = f"products:list:{skip}:{limit}:{category or 'all'}"
        cached = await redis_client.get_cache(cache_key)
        
        if cached:
            return cached["products"], cached["total"]
        
        # Build query
        query = select(Product)
        count_query = select(func.count(Product.id))
        
        if category:
            query = query.where(Product.category == category)
            count_query = count_query.where(Product.category == category)
        
        query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())
        
        # Execute queries
        result = await db.execute(query)
        products = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Cache results
        products_dict = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in products
        ]
        
        cache_data = {"products": products_dict, "total": total}
        await redis_client.set_cache(cache_key, cache_data, ttl=settings.cache_ttl)
        
        return list(products), total

    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: int,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update product.
        
        Args:
            db: Database session
            product_id: Product ID
            product_data: Update data
            
        Returns:
            Optional[Product]: Updated product or None
        """
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Update fields
        for field, value in product_data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        
        await db.commit()
        await db.refresh(product)
        
        # Invalidate cache
        await redis_client.delete_cache(f"products:detail:{product_id}")
        await redis_client.delete_cache("products:list:*")
        
        return product

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int) -> bool:
        """
        Delete product.
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            bool: True if deleted
        """
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return False
        
        await db.delete(product)
        await db.commit()
        
        # Invalidate cache
        await redis_client.delete_cache(f"products:detail:{product_id}")
        await redis_client.delete_cache("products:list:*")
        
        return True


class CartService:
    """Service for shopping cart operations using Redis Hash."""

    @staticmethod
    async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int) -> Dict[str, Any]:
        """
        Add product to cart.
        
        Args:
            db: Database session
            user_id: User ID
            product_id: Product ID
            quantity: Quantity to add
            
        Returns:
            dict: Cart data
        """
        # Verify product exists
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise ValueError("Product not found")
        
        if product.stock < quantity:
            raise ValueError("Insufficient stock")
        
        # Store in Redis hash
        cart_key = f"cart:user:{user_id}"
        cart_item = {
            "product_id": product_id,
            "product_name": product.name,
            "price": product.price,
            "quantity": quantity
        }
        
        await redis_client.hash_set(cart_key, str(product_id), json.dumps(cart_item))
        
        return await CartService.get_cart(user_id, db)

    @staticmethod
    async def get_cart(user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Get user's cart.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            dict: Cart data
        """
        cart_key = f"cart:user:{user_id}"
        cart_data = await redis_client.hash_get_all(cart_key)
        
        items = []
        total_price = 0.0
        total_items = 0
        
        for product_id, item_json in cart_data.items():
            item = json.loads(item_json)
            subtotal = item["price"] * item["quantity"]
            
            items.append(CartItem(
                product_id=item["product_id"],
                product_name=item["product_name"],
                price=item["price"],
                quantity=item["quantity"],
                subtotal=subtotal
            ))
            
            total_price += subtotal
            total_items += item["quantity"]
        
        return {
            "user_id": user_id,
            "items": items,
            "total_items": total_items,
            "total_price": round(total_price, 2)
        }

    @staticmethod
    async def remove_from_cart(user_id: int, product_id: int) -> bool:
        """
        Remove product from cart.
        
        Args:
            user_id: User ID
            product_id: Product ID
            
        Returns:
            bool: True if removed
        """
        cart_key = f"cart:user:{user_id}"
        deleted = await redis_client.hash_delete(cart_key, str(product_id))
        return deleted > 0

    @staticmethod
    async def clear_cart(user_id: int) -> bool:
        """
        Clear user's cart.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if cleared
        """
        cart_key = f"cart:user:{user_id}"
        client = await redis_client.get_redis()
        deleted = await client.delete(cart_key)
        return deleted > 0


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    async def generate_otp(phone: str) -> str:
        """
        Generate and store OTP.
        
        Args:
            phone: Phone number
            
        Returns:
            str: Generated OTP
        """
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store in Redis with 5-minute TTL
        otp_key = f"otp:{phone}"
        await redis_client.set_with_expiry(otp_key, otp, 300)
        
        return otp

    @staticmethod
    async def verify_otp(phone: str, otp: str) -> bool:
        """
        Verify OTP.
        
        Args:
            phone: Phone number
            otp: OTP to verify
            
        Returns:
            bool: True if valid
        """
        otp_key = f"otp:{phone}"
        client = await redis_client.get_redis()
        stored_otp = await client.get(otp_key)
        
        if stored_otp and stored_otp == otp:
            # Delete OTP after successful verification
            await client.delete(otp_key)
            return True
        
        return False


class AnalyticsService:
    """Service for analytics operations."""

    @staticmethod
    async def track_visitor(visitor_id: str) -> int:
        """
        Track unique visitor using HyperLogLog.
        
        Args:
            visitor_id: Unique visitor identifier
            
        Returns:
            int: Total unique visitors
        """
        client = await redis_client.get_redis()
        await client.pfadd("analytics:unique_visitors", visitor_id)
        count = await client.pfcount("analytics:unique_visitors")
        return count

    @staticmethod
    async def track_daily_login(user_id: int, date: str) -> bool:
        """
        Track daily login using Bitmap.
        
        Args:
            user_id: User ID
            date: Date in YYYY-MM-DD format
            
        Returns:
            bool: True if set
        """
        bitmap_key = f"analytics:logins:{date}"
        client = await redis_client.get_redis()
        result = await client.setbit(bitmap_key, user_id, 1)
        return result == 0  # Returns 0 if bit was not previously set

    @staticmethod
    async def get_daily_active_users(date: str) -> int:
        """
        Get daily active users count.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            int: Count of active users
        """
        bitmap_key = f"analytics:logins:{date}"
        client = await redis_client.get_redis()
        count = await client.bitcount(bitmap_key)
        return count

    @staticmethod
    async def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top viewed products from leaderboard.
        
        Args:
            limit: Number of products to return
            
        Returns:
            List[dict]: Top products
        """
        results = await redis_client.get_sorted_set_range(
            "products:leaderboard",
            0,
            limit - 1,
            desc=True
        )
        
        return [
            {"product_id": int(product_id), "views": int(views)}
            for product_id, views in results
        ]
