# Redis Patterns & Implementation Guide

This document explains each Redis pattern used in the FastAPI Redis Lab project.

## Table of Contents

1. [Caching Pattern](#1-caching-pattern)
2. [Shopping Cart with Hash](#2-shopping-cart-with-hash)
3. [OTP with TTL](#3-otp-with-ttl)
4. [Rate Limiting](#4-rate-limiting)
5. [View Counter](#5-view-counter)
6. [Leaderboard with Sorted Set](#6-leaderboard-with-sorted-set)
7. [Pub/Sub Messaging](#7-pubsub-messaging)
8. [Event Sourcing with Streams](#8-event-sourcing-with-streams)
9. [Distributed Locking](#9-distributed-locking)
10. [Celery Task Queue](#10-celery-task-queue)
11. [Unique Visitors with HyperLogLog](#11-unique-visitors-with-hyperloglog)
12. [Daily Active Users with Bitmap](#12-daily-active-users-with-bitmap)

---

## 1. Caching Pattern

### Pattern: Cache-Aside (Lazy Loading)

**Use Case**: Product catalog caching

**How It Works**:
1. Check cache first
2. If miss, fetch from database
3. Store in cache for next request
4. Set TTL (Time To Live)

**Implementation**:
```python
# File: app/services.py - ProductService.get_product()

async def get_product(db: AsyncSession, product_id: int):
    # Try cache first
    cache_key = f"products:detail:{product_id}"
    cached = await redis_client.get_cache(cache_key)
    
    if cached:
        return cached  # Cache hit
    
    # Cache miss - fetch from database
    product = await db.fetch_product(product_id)
    
    if product:
        # Store in cache with TTL
        await redis_client.set_cache(cache_key, product_dict, ttl=300)
    
    return product
```

**Redis Commands**:
- `SET key value EX 300` - Set with expiry
- `GET key` - Retrieve value

**Key Pattern**: `products:detail:{id}`, `products:list:{skip}:{limit}:{category}`

**Cache Invalidation**:
```python
# On update/delete
await redis_client.delete_cache(f"products:detail:{product_id}")
await redis_client.delete_cache("products:list:*")
```

---

## 2. Shopping Cart with Hash

### Pattern: Redis Hash for Structured Data

**Use Case**: User shopping cart

**Why Hash?**:
- Store multiple items under one key
- Efficient field-level operations
- Better than separate keys for each item

**Implementation**:
```python
# File: app/services.py - CartService

# Store cart
cart_key = f"cart:user:{user_id}"
cart_item = {
    "product_id": product_id,
    "product_name": product.name,
    "price": product.price,
    "quantity": quantity
}
await redis_client.hash_set(cart_key, str(product_id), json.dumps(cart_item))

# Retrieve cart
cart_data = await redis_client.hash_get_all(cart_key)
```

**Redis Commands**:
- `HSET cart:user:1 product_1 '{"quantity":2}'`
- `HGETALL cart:user:1`
- `HDEL cart:user:1 product_1`

**Key Pattern**: `cart:user:{user_id}`

**Benefits**:
- Atomic operations
- Efficient updates
- Single key for all items

---

## 3. OTP with TTL

### Pattern: Time-Limited Data

**Use Case**: One-Time Password authentication

**Implementation**:
```python
# File: app/services.py - AuthService

async def generate_otp(phone: str) -> str:
    otp = str(random.randint(100000, 999999))
    otp_key = f"otp:{phone}"
    
    # Store with 5-minute TTL
    await redis_client.set_with_expiry(otp_key, otp, 300)
    return otp

async def verify_otp(phone: str, otp: str) -> bool:
    otp_key = f"otp:{phone}"
    stored_otp = await client.get(otp_key)
    
    if stored_otp and stored_otp == otp:
        # Delete after successful verification
        await client.delete(otp_key)
        return True
    return False
```

**Redis Commands**:
- `SETEX otp:+1234567890 300 "123456"`
- `GET otp:+1234567890`
- `TTL otp:+1234567890` - Check remaining time
- `DEL otp:+1234567890`

**Key Pattern**: `otp:{phone_number}`

**Benefits**:
- Automatic expiration
- No manual cleanup needed
- Secure (single-use)

---

## 4. Rate Limiting

### Pattern: Token Bucket with INCR + EXPIRE

**Use Case**: Prevent API abuse

**Implementation**:
```python
# File: app/utils.py - check_rate_limit()

async def check_rate_limit(identifier: str) -> bool:
    rate_limit_key = f"rate_limit:{identifier}"
    client = await redis_client.get_redis()
    
    current = await client.get(rate_limit_key)
    
    if current is None:
        # First request - set counter with expiry
        await client.setex(rate_limit_key, window_seconds, 1)
        return True
    
    if int(current) >= max_requests:
        raise HTTPException(429, "Rate limit exceeded")
    
    # Increment counter
    await client.incr(rate_limit_key)
    return True
```

**Redis Commands**:
- `SETEX rate_limit:ip_address 60 1`
- `INCR rate_limit:ip_address`
- `TTL rate_limit:ip_address`

**Key Pattern**: `rate_limit:{identifier}` (IP, user_id, API key)

**Configuration**:
- Max requests: 10
- Window: 60 seconds

---

## 5. View Counter

### Pattern: Atomic Increment

**Use Case**: Product view tracking

**Implementation**:
```python
# File: app/services.py - ProductService.get_product()

# Increment view counter
await redis_client.increment_counter(f"products:views:{product_id}")

# Update leaderboard
views = await client.get(f"products:views:{product_id}")
await redis_client.add_to_sorted_set(
    "products:leaderboard",
    str(product_id),
    float(views)
)
```

**Redis Commands**:
- `INCR products:views:1`
- `GET products:views:1`
- `INCRBY products:views:1 5` - Increment by amount

**Key Pattern**: `products:views:{product_id}`

**Benefits**:
- Atomic operation
- Fast increment
- No race conditions

---

## 6. Leaderboard with Sorted Set

### Pattern: Ranked Data Structure

**Use Case**: Top viewed products

**Implementation**:
```python
# File: app/services.py - AnalyticsService

# Add to leaderboard
await redis_client.add_to_sorted_set(
    "products:leaderboard",
    str(product_id),
    float(view_count)
)

# Get top 10
results = await redis_client.get_sorted_set_range(
    "products:leaderboard",
    0,
    9,
    desc=True
)
```

**Redis Commands**:
- `ZADD products:leaderboard 150 "1"` - Add with score
- `ZINCRBY products:leaderboard 1 "1"` - Increment score
- `ZREVRANGE products:leaderboard 0 9 WITHSCORES` - Top 10
- `ZRANK products:leaderboard "1"` - Get rank

**Key Pattern**: `products:leaderboard`

**Benefits**:
- Automatic sorting
- Fast range queries
- Efficient updates

---

## 7. Pub/Sub Messaging

### Pattern: Real-Time Event Broadcasting

**Use Case**: Notifications, real-time updates

**Implementation**:
```python
# File: app/pubsub.py

# Publisher
async def publish(channel: str, message: dict) -> int:
    client = await get_redis()
    message_json = json.dumps(message)
    return await client.publish(channel, message_json)

# Subscriber
async def subscribe(channel: str, callback: Callable):
    client = await get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            await callback(data)
```

**Redis Commands**:
- `PUBLISH notifications "message"` - Send message
- `SUBSCRIBE notifications` - Listen to channel
- `PSUBSCRIBE order.*` - Pattern subscribe

**Channels**: `notifications`, `orders`, `analytics`

**Benefits**:
- Real-time delivery
- Multiple subscribers
- Fire-and-forget

**Limitation**: Messages not persisted

---

## 8. Event Sourcing with Streams

### Pattern: Append-Only Event Log

**Use Case**: Order events, audit log

**Implementation**:
```python
# File: app/stream.py

# Add event
async def add_event(event_type: str, data: dict) -> str:
    client = await get_redis()
    stream_data = {
        "event_type": event_type,
        "timestamp": str(int(time.time() * 1000)),
        **{k: str(v) for k, v in data.items()}
    }
    event_id = await client.xadd(stream_key, stream_data)
    return event_id

# Read events
async def read_events(count: int = 10) -> list:
    client = await get_redis()
    results = await client.xrange(stream_key, "-", "+", count=count)
    return results
```

**Redis Commands**:
- `XADD orders:events * event_type order.created order_id 123`
- `XRANGE orders:events - + COUNT 10`
- `XREAD COUNT 10 STREAMS orders:events 0`
- `XLEN orders:events`

**Key Pattern**: `orders:events`, `notifications:events`

**Benefits**:
- Persistent messages
- Consumer groups
- Replay capability
- Ordered delivery

---

## 9. Distributed Locking

### Pattern: SET NX EX (Set if Not Exists with Expiry)

**Use Case**: Prevent race conditions

**Implementation**:
```python
# File: app/locks.py

async def acquire_lock(lock_key: str, lock_value: str, ttl: int) -> bool:
    client = await get_redis()
    return await client.set(lock_key, lock_value, nx=True, ex=ttl)

async def release_lock(lock_key: str, lock_value: str) -> bool:
    # Lua script ensures we only delete our own lock
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    return await client.eval(lua_script, 1, lock_key, lock_value)
```

**Redis Commands**:
- `SET lock:resource "unique_value" NX EX 10`
- `GET lock:resource`
- `DEL lock:resource` (via Lua script)

**Usage**:
```python
async with distributed_lock("inventory_update", ttl=10):
    # Critical section
    # Only one process can execute this at a time
    await update_inventory()
```

**Key Pattern**: `lock:{resource_name}`

**Benefits**:
- Mutual exclusion
- Automatic timeout
- Safe release (Lua script)

---

## 10. Celery Task Queue

### Pattern: Redis as Message Broker

**Use Case**: Background email, payment processing

**Implementation**:
```python
# File: app/tasks.py

@celery_app.task(name="send_welcome_email")
def send_welcome_email(email: str, user_name: str) -> dict:
    time.sleep(2)  # Simulate work
    return {
        "status": "success",
        "email": email,
        "message": "Email sent"
    }

# Queue task
task = send_welcome_email.delay("user@example.com", "John")
```

**Redis Structure**:
- **Broker** (DB 1): Task queue
- **Backend** (DB 2): Result storage

**Queues**: `celery`, `emails`, `payments`, `reports`

**Benefits**:
- Async processing
- Retry mechanism
- Task scheduling
- Result tracking

---

## 11. Unique Visitors with HyperLogLog

### Pattern: Cardinality Estimation

**Use Case**: Count unique visitors efficiently

**Why HyperLogLog?**:
- Uses only 12KB per key
- 0.81% error rate
- Handles billions of unique values

**Implementation**:
```python
# File: app/services.py - AnalyticsService

async def track_visitor(visitor_id: str) -> int:
    client = await get_redis()
    await client.pfadd("analytics:unique_visitors", visitor_id)
    count = await client.pfcount("analytics:unique_visitors")
    return count
```

**Redis Commands**:
- `PFADD analytics:unique_visitors "user_1" "user_2"`
- `PFCOUNT analytics:unique_visitors`
- `PFMERGE dest_key source_key1 source_key2`

**Key Pattern**: `analytics:unique_visitors`

**Memory**: ~12KB regardless of visitor count

---

## 12. Daily Active Users with Bitmap

### Pattern: Boolean Flags

**Use Case**: Track daily logins efficiently

**Why Bitmap?**:
- 1 bit per user
- Extremely memory efficient
- Fast bitwise operations

**Implementation**:
```python
# File: app/services.py - AnalyticsService

async def track_daily_login(user_id: int, date: str) -> bool:
    bitmap_key = f"analytics:logins:{date}"
    client = await get_redis()
    # Set bit at position user_id to 1
    result = await client.setbit(bitmap_key, user_id, 1)
    return result == 0

async def get_daily_active_users(date: str) -> int:
    bitmap_key = f"analytics:logins:{date}"
    client = await get_redis()
    # Count all bits set to 1
    count = await client.bitcount(bitmap_key)
    return count
```

**Redis Commands**:
- `SETBIT analytics:logins:2024-01-15 123 1`
- `GETBIT analytics:logins:2024-01-15 123`
- `BITCOUNT analytics:logins:2024-01-15`
- `BITOP AND result key1 key2` - Common logins

**Key Pattern**: `analytics:logins:{YYYY-MM-DD}`

**Memory**: ~125KB for 1 million users

**Benefits**:
- Ultra-low memory
- Fast operations
- Bitwise analytics

---

## Best Practices

### Key Naming Convention

```
{domain}:{entity}:{identifier}:{field}
```

Examples:
- `products:detail:123`
- `cart:user:456`
- `lock:inventory:product_123`
- `analytics:logins:2024-01-15`

### TTL Strategy

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Cache | 5-30 min | Balance freshness vs load |
| OTP | 5 min | Security |
| Rate limit | 60 sec | Window size |
| Session | 24 hours | User experience |
| Lock | 10 sec | Prevent deadlock |

### Memory Management

- Set `maxmemory` policy: `allkeys-lru`
- Use appropriate data structures
- Set TTL on temporary data
- Monitor memory usage

### Error Handling

```python
try:
    await redis_client.get(key)
except redis.ConnectionError:
    # Fallback to database
    logger.error("Redis connection failed")
except redis.TimeoutError:
    # Retry or skip cache
    logger.warning("Redis timeout")
```

---

## Performance Comparison

| Pattern | Operation | Time Complexity |
|---------|-----------|-----------------|
| String | GET/SET | O(1) |
| Hash | HGET/HSET | O(1) |
| Sorted Set | ZADD | O(log N) |
| Sorted Set | ZRANGE | O(log N + M) |
| HyperLogLog | PFADD | O(1) |
| Bitmap | SETBIT | O(1) |
| Stream | XADD | O(1) |

---

## Testing Redis Patterns

### Check Cache

```bash
redis-cli
GET products:detail:1
```

### Check Cart

```bash
HGETALL cart:user:1
```

### Check Leaderboard

```bash
ZREVRANGE products:leaderboard 0 9 WITHSCORES
```

### Check Unique Visitors

```bash
PFCOUNT analytics:unique_visitors
```

### Check Daily Logins

```bash
BITCOUNT analytics:logins:2024-01-15
```

### Monitor Commands

```bash
redis-cli MONITOR
```

---

## Resources

- [Redis Documentation](https://redis.io/docs/)
- [Redis Commands Reference](https://redis.io/commands/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

---

**Happy Caching! 🚀**
