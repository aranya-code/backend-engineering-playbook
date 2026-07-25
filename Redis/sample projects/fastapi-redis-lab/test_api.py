"""Test script to verify all API endpoints."""

import requests
import time
from typing import Dict, Any
import json


BASE_URL = "http://localhost:8000"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test name."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing: {name}{Colors.RESET}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")


def test_health_check():
    """Test health check endpoints."""
    print_test("Health Check")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print_success("Root endpoint OK")
    else:
        print_error(f"Root endpoint failed: {response.status_code}")
    
    # Test app health
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print_success("App health check OK")
    else:
        print_error(f"App health check failed: {response.status_code}")
    
    # Test Redis health
    response = requests.get(f"{BASE_URL}/redis/health")
    if response.status_code == 200:
        print_success("Redis health check OK")
    else:
        print_error(f"Redis health check failed: {response.status_code}")
        print_info("Make sure Redis is running!")


def test_products():
    """Test product endpoints."""
    print_test("Products API")
    
    # Create product
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 50,
        "category": "Test"
    }
    
    response = requests.post(f"{BASE_URL}/products", json=product_data)
    if response.status_code == 201:
        product = response.json()
        product_id = product["id"]
        print_success(f"Product created: ID={product_id}")
    else:
        print_error(f"Failed to create product: {response.status_code}")
        return None
    
    # Get product list (should be cached)
    response = requests.get(f"{BASE_URL}/products")
    if response.status_code == 200:
        products = response.json()
        print_success(f"Retrieved {len(products['products'])} products (cached)")
    else:
        print_error(f"Failed to get products: {response.status_code}")
    
    # Get product detail (should increment view counter)
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    if response.status_code == 200:
        print_success(f"Retrieved product detail (view counter incremented)")
    else:
        print_error(f"Failed to get product detail: {response.status_code}")
    
    # Update product
    update_data = {"price": 79.99}
    response = requests.put(f"{BASE_URL}/products/{product_id}", json=update_data)
    if response.status_code == 200:
        print_success("Product updated (cache invalidated)")
    else:
        print_error(f"Failed to update product: {response.status_code}")
    
    return product_id


def test_cart(product_id: int):
    """Test shopping cart endpoints."""
    print_test("Shopping Cart API")
    
    headers = {"X-User-Id": "1"}
    
    # Add to cart
    cart_data = {
        "product_id": product_id,
        "quantity": 3
    }
    
    response = requests.post(f"{BASE_URL}/cart", json=cart_data, headers=headers)
    if response.status_code == 201:
        cart = response.json()
        print_success(f"Added to cart: {cart['total_items']} items")
    else:
        print_error(f"Failed to add to cart: {response.status_code}")
    
    # Get cart
    response = requests.get(f"{BASE_URL}/cart", headers=headers)
    if response.status_code == 200:
        cart = response.json()
        print_success(f"Retrieved cart: ${cart['total_price']:.2f}")
    else:
        print_error(f"Failed to get cart: {response.status_code}")
    
    # Clear cart
    response = requests.delete(f"{BASE_URL}/cart", headers=headers)
    if response.status_code == 200:
        print_success("Cart cleared")
    else:
        print_error(f"Failed to clear cart: {response.status_code}")


def test_auth():
    """Test authentication endpoints."""
    print_test("Authentication API")
    
    phone = "+1234567890"
    
    # Request OTP
    response = requests.post(f"{BASE_URL}/auth/otp", json={"phone": phone})
    if response.status_code == 200:
        result = response.json()
        print_success("OTP requested (stored in Redis with 5-min TTL)")
        
        # Extract OTP from demo response
        message = result.get("message", "")
        if "Demo OTP:" in message:
            otp = message.split("Demo OTP:")[1].strip()
            print_info(f"Demo OTP: {otp}")
            
            # Test login
            time.sleep(1)  # Small delay
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"phone": phone, "otp": otp}
            )
            if response.status_code == 200:
                print_success("Login successful (OTP verified and deleted)")
            else:
                print_error(f"Login failed: {response.status_code}")
    else:
        print_error(f"Failed to request OTP: {response.status_code}")


def test_analytics():
    """Test analytics endpoints."""
    print_test("Analytics API")
    
    headers = {"X-User-Id": "1"}
    
    # Get leaderboard
    response = requests.get(f"{BASE_URL}/analytics/leaderboard")
    if response.status_code == 200:
        leaderboard = response.json()
        print_success(f"Leaderboard: {leaderboard['total']} top products")
    else:
        print_error(f"Failed to get leaderboard: {response.status_code}")
    
    # Get analytics
    response = requests.get(f"{BASE_URL}/analytics", headers=headers)
    if response.status_code == 200:
        analytics = response.json()
        print_success(f"Analytics: {analytics['unique_visitors']} unique visitors")
        print_info(f"Daily active users: {analytics['daily_active_users']}")
    else:
        print_error(f"Failed to get analytics: {response.status_code}")


def test_redis_features():
    """Test Redis feature demonstrations."""
    print_test("Redis Features")
    
    # Test Pub/Sub
    message_data = {
        "channel": "test",
        "message": "Hello from test script!"
    }
    response = requests.post(f"{BASE_URL}/redis/publish", json=message_data)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pub/Sub: Published to {result['subscribers']} subscribers")
    else:
        print_error(f"Pub/Sub failed: {response.status_code}")
    
    # Test Streams
    event_data = {
        "event_type": "test.event",
        "data": {"key": "value", "timestamp": int(time.time())}
    }
    response = requests.post(f"{BASE_URL}/redis/stream", json=event_data)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Stream: Event added with ID {result['event_id']}")
    else:
        print_error(f"Stream failed: {response.status_code}")
    
    # Test distributed lock
    response = requests.post(f"{BASE_URL}/redis/lock/demo?resource=test_resource")
    if response.status_code == 200:
        print_success("Distributed lock: Acquired and released successfully")
    else:
        print_error(f"Distributed lock failed: {response.status_code}")
    
    # Test Redis stats
    response = requests.get(f"{BASE_URL}/redis/stats")
    if response.status_code == 200:
        stats = response.json()
        print_success(f"Redis stats: version {stats.get('redis_version', 'unknown')}")
        print_info(f"Memory used: {stats.get('used_memory_human', 'unknown')}")
    else:
        print_error(f"Redis stats failed: {response.status_code}")


def test_celery():
    """Test Celery background tasks."""
    print_test("Celery Background Tasks")
    
    # Test welcome email
    response = requests.post(
        f"{BASE_URL}/redis/celery/welcome-email",
        params={"email": "test@example.com", "user_name": "Test User"}
    )
    if response.status_code == 200:
        result = response.json()
        print_success("Celery: Welcome email task queued")
        print_info(result["message"])
    else:
        print_error(f"Celery task failed: {response.status_code}")
        print_info("Make sure Celery worker is running!")


def test_cache_operations():
    """Test cache operations."""
    print_test("Cache Operations")
    
    # Clear product cache
    response = requests.post(f"{BASE_URL}/redis/cache/clear?pattern=products:*")
    if response.status_code == 200:
        result = response.json()
        print_success(f"Cache cleared: {result['keys_deleted']} keys deleted")
    else:
        print_error(f"Cache clear failed: {response.status_code}")


def run_all_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}FastAPI Redis Lab - API Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    
    try:
        # Check if server is running
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
        except requests.exceptions.ConnectionError:
            print_error("\nServer is not running!")
            print_info("Start the server with: uvicorn app.main:app --reload")
            return
        
        # Run tests
        test_health_check()
        product_id = test_products()
        
        if product_id:
            test_cart(product_id)
        
        test_auth()
        test_analytics()
        test_redis_features()
        test_celery()
        test_cache_operations()
        
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}All tests completed!{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
        
        print_info("Check Redis data with:")
        print("  redis-cli")
        print("  KEYS *")
        print("  GET products:detail:1")
        print("  HGETALL cart:user:1")
        print("  ZRANGE products:leaderboard 0 -1 WITHSCORES")
        
    except Exception as e:
        print_error(f"\nTest suite failed with error: {e}")


if __name__ == "__main__":
    run_all_tests()
