"""
API views for the playground app.

Views are thin controllers — they handle:
1. Request parsing and validation (via serializers)
2. Delegating to the service layer
3. Returning HTTP responses

All business logic and Redis operations are in services.py and redis_service.py.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .redis_service import rate_limit_check
from .serializers import (
    CartDeleteSerializer,
    CartItemSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PublishSerializer,
    StreamEventSerializer,
)
from .utils import get_client_ip


# ---------------------------------------------------------------------------
# Rate Limiting Decorator
# ---------------------------------------------------------------------------

def rate_limited(view_func):
    """
    Decorator that applies rate limiting to a view.

    Checks the client IP against the rate limiter in redis_service.
    Returns 429 Too Many Requests if the limit is exceeded.
    """
    def wrapper(request: Request, *args, **kwargs) -> Response:
        client_ip = get_client_ip(request)
        is_allowed, current_count = rate_limit_check(client_ip)

        if not is_allowed:
            return Response(
                {
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests ({current_count}). Try again later.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        response = view_func(request, *args, **kwargs)

        # Add rate limit headers to the response
        response["X-RateLimit-Remaining"] = max(0, 30 - current_count)
        response["X-RateLimit-Count"] = current_count
        return response

    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


# ---------------------------------------------------------------------------
# Product Views
# ---------------------------------------------------------------------------

@api_view(["GET"])
@rate_limited
def product_list(request: Request) -> Response:
    """
    List all products.

    Responses are cached in Redis for 5 minutes.
    GET /api/products/
    """
    data = services.get_product_list()
    return Response(data)


@api_view(["GET"])
@rate_limited
def product_detail(request: Request, product_id: int) -> Response:
    """
    Get a single product by ID.

    Increments the view counter and updates the leaderboard.
    Response is cached in Redis for 5 minutes.
    GET /api/products/{id}/
    """
    # Track this visitor via HyperLogLog
    visitor_id = get_client_ip(request)
    from .redis_service import hyperloglog_add
    hyperloglog_add(visitor_id)

    data = services.get_product_detail(product_id)
    if data is None:
        return Response(
            {"error": f"Product {product_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(data)


# ---------------------------------------------------------------------------
# Shopping Cart Views
# ---------------------------------------------------------------------------

@api_view(["POST", "GET", "DELETE"])
@rate_limited
def cart(request: Request) -> Response:
    """
    Shopping cart endpoint.

    POST /api/cart/   — Add item to cart
    GET  /api/cart/   — Get cart contents (requires ?user_id=)
    DELETE /api/cart/ — Clear cart
    """
    if request.method == "POST":
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.add_to_cart(**serializer.validated_data)
        if "error" in data:
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        return Response(data, status=status.HTTP_201_CREATED)

    if request.method == "GET":
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = services.get_cart(int(user_id))
        return Response(data)

    if request.method == "DELETE":
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.clear_cart(**serializer.validated_data)
        return Response(data)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# ---------------------------------------------------------------------------
# OTP Views
# ---------------------------------------------------------------------------

@api_view(["POST"])
@rate_limited
def otp_request(request: Request) -> Response:
    """
    Generate and send an OTP.

    POST /api/otp/
    Body: {"email": "user@example.com"}
    """
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = services.request_otp(**serializer.validated_data)
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@rate_limited
def login(request: Request) -> Response:
    """
    Verify OTP and log in.

    POST /api/login/
    Body: {"email": "user@example.com", "otp": "123456"}
    """
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = services.verify_otp(**serializer.validated_data)

    if data["authenticated"]:
        return Response(data)

    return Response(data, status=status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Leaderboard View
# ---------------------------------------------------------------------------

@api_view(["GET"])
@rate_limited
def leaderboard(request: Request) -> Response:
    """
    Get the top 10 most-viewed products.

    GET /api/leaderboard/
    """
    data = services.get_leaderboard()
    return Response(data)


# ---------------------------------------------------------------------------
# Pub/Sub View
# ---------------------------------------------------------------------------

@api_view(["POST"])
@rate_limited
def publish(request: Request) -> Response:
    """
    Publish a message to a Redis Pub/Sub channel.

    POST /api/publish/
    Body: {"channel": "notifications", "message": "Hello World"}
    """
    serializer = PublishSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = services.publish_notification(**serializer.validated_data)
    return Response(data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Stream View
# ---------------------------------------------------------------------------

@api_view(["POST"])
@rate_limited
def stream(request: Request) -> Response:
    """
    Add an order event to the Redis Stream.

    POST /api/stream/
    Body: {"order_id": 1, "event": "created", "data": {"total": "99.99"}}
    """
    serializer = StreamEventSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = services.add_order_event(**serializer.validated_data)

    if "error" in data:
        return Response(data, status=status.HTTP_409_CONFLICT)

    return Response(data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Cache Management View
# ---------------------------------------------------------------------------

@api_view(["POST"])
def cache_clear(request: Request) -> Response:
    """
    Clear all cached data.

    POST /api/cache/clear/
    """
    data = services.clear_cache()
    return Response(data)


# ---------------------------------------------------------------------------
# Analytics View
# ---------------------------------------------------------------------------

@api_view(["GET"])
@rate_limited
def analytics(request: Request) -> Response:
    """
    Get aggregated analytics.

    Includes unique visitors (HyperLogLog), daily logins (Bitmap),
    product view counts, and stream event count.

    GET /api/analytics/
    """
    visitor_id = get_client_ip(request)
    data = services.get_analytics(visitor_id=visitor_id)
    return Response(data)
