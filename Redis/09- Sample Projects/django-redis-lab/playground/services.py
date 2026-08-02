"""
Business logic service layer.

Views call services. Services call redis_service and Django ORM.
This separation keeps views thin and business logic testable.
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.cache import cache

from .models import Product
from .serializers import ProductSerializer
from . import redis_service
from .locks import distributed_lock
from .pubsub import publish_message
from .stream import stream_add_event, stream_read_events, stream_length
from .tasks import send_otp_email
from .utils import generate_otp

logger = logging.getLogger(__name__)

# Cache TTLs
PRODUCT_LIST_CACHE_TTL = 300  # 5 minutes
PRODUCT_DETAIL_CACHE_TTL = 300


# ---------------------------------------------------------------------------
# Product Services
# ---------------------------------------------------------------------------

def get_product_list() -> list[dict[str, Any]]:
    """
    Get all products, with Redis caching.

    Cache key: product_list
    TTL: 300 seconds
    """
    cache_key = "product_list"
    cached = cache.get(cache_key)

    if cached is not None:
        logger.debug("Cache HIT: %s", cache_key)
        return cached

    logger.debug("Cache MISS: %s", cache_key)
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    data = serializer.data
    cache.set(cache_key, data, PRODUCT_LIST_CACHE_TTL)
    return data


def get_product_detail(product_id: int) -> dict[str, Any] | None:
    """
    Get a single product by ID, with Redis caching.

    Also increments the view counter and updates the leaderboard.

    Cache key: product_detail:{id}
    TTL: 300 seconds
    """
    cache_key = f"product_detail:{product_id}"
    cached = cache.get(cache_key)

    if cached is not None:
        logger.debug("Cache HIT: %s", cache_key)
        # Still increment view counter even on cache hit
        _track_product_view(product_id, cached.get("name", "Unknown"))
        return cached

    logger.debug("Cache MISS: %s", cache_key)
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return None

    serializer = ProductSerializer(product)
    data = serializer.data
    cache.set(cache_key, data, PRODUCT_DETAIL_CACHE_TTL)

    _track_product_view(product_id, product.name)
    return data


def _track_product_view(product_id: int, product_name: str) -> None:
    """Increment view counter and update leaderboard."""
    new_count = redis_service.view_counter_increment(product_id)
    redis_service.leaderboard_update(product_id, product_name, new_count)


# ---------------------------------------------------------------------------
# Shopping Cart Services
# ---------------------------------------------------------------------------

def add_to_cart(user_id: int, product_id: int, quantity: int) -> dict[str, Any]:
    """
    Add a product to the user's shopping cart.

    Validates that the product exists before adding to cart.
    """
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return {"error": f"Product {product_id} not found"}

    redis_service.cart_add_item(user_id, product_id, quantity)

    return {
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product.name,
        "quantity_added": quantity,
        "message": "Item added to cart",
    }


def get_cart(user_id: int) -> dict[str, Any]:
    """
    Retrieve the user's shopping cart with product details.

    Enriches the raw Redis data (product_id → quantity) with
    product names and prices from the database.
    """
    raw_cart = redis_service.cart_get(user_id)

    if not raw_cart:
        return {"user_id": user_id, "items": [], "total": 0}

    product_ids = [int(pid) for pid in raw_cart.keys()]
    products = Product.objects.filter(pk__in=product_ids)
    product_map = {p.id: p for p in products}

    items = []
    total = 0
    for pid_str, qty_str in raw_cart.items():
        pid = int(pid_str)
        qty = int(qty_str)
        product = product_map.get(pid)
        if product:
            subtotal = float(product.price) * qty
            total += subtotal
            items.append({
                "product_id": pid,
                "product_name": product.name,
                "price": str(product.price),
                "quantity": qty,
                "subtotal": round(subtotal, 2),
            })

    return {
        "user_id": user_id,
        "items": items,
        "total": round(total, 2),
    }


def clear_cart(user_id: int) -> dict[str, Any]:
    """Clear the user's shopping cart."""
    deleted = redis_service.cart_clear(user_id)
    return {
        "user_id": user_id,
        "cleared": bool(deleted),
        "message": "Cart cleared" if deleted else "Cart was already empty",
    }


# ---------------------------------------------------------------------------
# OTP Services
# ---------------------------------------------------------------------------

def request_otp(email: str) -> dict[str, str]:
    """
    Generate, store, and send an OTP for the given email.

    The OTP is stored in Redis with a 300-second TTL.
    A Celery task is dispatched to simulate sending the email.
    """
    otp_code = generate_otp()
    redis_service.otp_store(email, otp_code)

    # Dispatch background email task via Celery
    send_otp_email.delay(email, otp_code)

    return {
        "email": email,
        "message": "OTP sent to your email (check Celery worker logs)",
        "otp_for_testing": otp_code,  # Exposed for testing only
    }


def verify_otp(email: str, otp_code: str) -> dict[str, Any]:
    """
    Verify an OTP and simulate login.

    If valid, marks the user as logged in using the bitmap tracker.
    """
    is_valid = redis_service.otp_verify(email, otp_code)

    if is_valid:
        # Simulate login — use a hash of email as user_id for bitmap
        user_id = abs(hash(email)) % 100000
        redis_service.bitmap_mark_login(user_id)
        return {
            "email": email,
            "authenticated": True,
            "message": "Login successful",
        }

    return {
        "email": email,
        "authenticated": False,
        "message": "Invalid or expired OTP",
    }


# ---------------------------------------------------------------------------
# Leaderboard Service
# ---------------------------------------------------------------------------

def get_leaderboard() -> list[dict[str, Any]]:
    """Get the top 10 most-viewed products."""
    return redis_service.leaderboard_top(count=10)


# ---------------------------------------------------------------------------
# Pub/Sub Service
# ---------------------------------------------------------------------------

def publish_notification(channel: str, message: str) -> dict[str, Any]:
    """Publish a message to a Redis Pub/Sub channel."""
    receivers = publish_message(channel, message)
    return {
        "channel": channel,
        "message": message,
        "receivers": receivers,
    }


# ---------------------------------------------------------------------------
# Stream Service
# ---------------------------------------------------------------------------

def add_order_event(
    order_id: int,
    event: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Add an order event to the Redis Stream.

    Uses a distributed lock to simulate critical section protection.
    """
    with distributed_lock(f"order:{order_id}") as token:
        if token is None:
            return {
                "error": "Could not acquire lock. Another process is updating this order.",
            }

        entry_id = stream_add_event(order_id, event, data)

    return {
        "entry_id": entry_id,
        "order_id": order_id,
        "event": event,
        "data": data or {},
        "message": "Event added to stream",
    }


# ---------------------------------------------------------------------------
# Analytics Service
# ---------------------------------------------------------------------------

def get_analytics(visitor_id: str | None = None) -> dict[str, Any]:
    """
    Aggregate analytics data from various Redis sources.

    Includes: unique visitors (HyperLogLog), daily logins (Bitmap),
    view counts, and stream length.
    """
    # Track this visitor if an ID is provided
    if visitor_id:
        redis_service.hyperloglog_add(visitor_id)

    # Gather product view counts
    products = Product.objects.all()[:10]
    view_counts = {}
    for product in products:
        count = redis_service.view_counter_get(product.id)
        if count > 0:
            view_counts[product.name] = count

    return {
        "unique_visitors": redis_service.hyperloglog_count(),
        "daily_logins_today": redis_service.bitmap_login_count(),
        "product_view_counts": view_counts,
        "order_stream_length": stream_length(),
    }


# ---------------------------------------------------------------------------
# Cache Management Service
# ---------------------------------------------------------------------------

def clear_cache() -> dict[str, str]:
    """Clear all cached product data."""
    redis_service.clear_all_cache()
    return {"message": "All cache cleared"}
