# Redis with FastAPI

## Overview

Redis is a core component in many production FastAPI applications. While FastAPI is known for its high performance and asynchronous architecture, Redis complements it by providing an in-memory data store for caching, session-like state management, rate limiting, distributed locking, background task coordination, and real-time features.

A typical FastAPI application communicates with Redis for:

- API response caching
- Database query caching
- Rate limiting
- OTP storage
- Temporary tokens
- Distributed locks
- Background task coordination
- Pub/Sub messaging
- WebSocket message broadcasting
- AI prompt caching
- Feature flags

Redis helps FastAPI applications achieve low latency, reduce database load, and scale horizontally.

---

# Why Use Redis with FastAPI?

Without Redis

```
Client

↓

FastAPI

↓

PostgreSQL

↓

Response
```

Every request queries the database.

---

With Redis

```
Client

↓

FastAPI

↓

Redis

↓

Cache Hit

↓

Response
```

Most requests never reach the database.

---

# Production Architecture

```
                 Client

                    │

                    ▼

              Load Balancer

                    │

                    ▼

                 FastAPI

         ┌─────────┼─────────┐

         ▼         ▼         ▼

      Redis      Celery   PostgreSQL

         │

         ▼

 Cache / Queue / Lock / PubSub
```

Redis becomes a shared infrastructure component.

---

# Installing Packages

Redis client

```bash
pip install redis
```

For asynchronous applications

```bash
pip install redis[hiredis]
```

FastAPI

```bash
pip install fastapi uvicorn
```

---

# Basic Project Structure

```
app/

├── main.py

├── redis_client.py

├── routes/

├── services/

├── models/

├── schemas/

├── config.py

└── requirements.txt
```

Keep Redis configuration centralized.

---

# Creating a Redis Client

```python
import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)
```

Store this in

```
redis_client.py
```

Reuse throughout the application.

---

# Environment Variables

Never hardcode Redis configuration.

Example

```
REDIS_HOST=localhost

REDIS_PORT=6379

REDIS_DB=0
```

Configuration

```python
from os import getenv

REDIS_HOST = getenv("REDIS_HOST")
```

---

# Testing the Connection

```python
redis_client.set(
    "framework",
    "FastAPI"
)

print(
    redis_client.get("framework")
)
```

Output

```
FastAPI
```

---

# Using Redis in FastAPI

Example

```python
from fastapi import FastAPI

from redis_client import redis_client

app = FastAPI()


@app.get("/visits")

def visits():

    count = redis_client.incr("visits")

    return {
        "visits": count
    }
```

Redis acts as a distributed counter.

---

# Caching Database Queries

Without cache

```
Client

↓

FastAPI

↓

Database

↓

Response
```

With cache

```
Client

↓

Redis

↓

Hit?

↓

Return

↓

Else Database

↓

Cache Result
```

---

Example

```python
import json

@app.get("/products")

def get_products():

    cached = redis_client.get("products")

    if cached:

        return json.loads(cached)

    products = fetch_products()

    redis_client.set(
        "products",
        json.dumps(products),
        ex=1800
    )

    return products
```

---

# Caching Individual Objects

```
product:101
```

Example

```python
key = f"product:{product_id}"
```

Instead of

```
products
```

Fine-grained keys reduce cache invalidation complexity.

---

# Cache Invalidation

Suppose

```
Product Updated
```

Workflow

```
Database

↓

Delete Cache

↓

Next Read

↓

Fresh Cache
```

Example

```python
redis_client.delete(
    f"product:{product_id}"
)
```

---

# JSON Serialization

Redis stores strings.

```python
import json

redis_client.set(

    "user:1",

    json.dumps(user),

    ex=600
)
```

Retrieve

```python
user = json.loads(

    redis_client.get("user:1")

)
```

---

# Temporary Tokens

Password reset

```python
redis_client.set(

    token,

    user.id,

    ex=900
)
```

TTL

```
15 Minutes
```

---

# OTP Storage

```
Phone

↓

Redis

↓

OTP

↓

Expire
```

Example

```python
redis_client.set(

    "otp:9999999999",

    "483921",

    ex=300
)
```

---

# API Rate Limiting

```
User

↓

Redis Counter

↓

Allowed?
```

Example

```python
count = redis_client.incr(

    "rate:user:15"

)

if count == 1:

    redis_client.expire(

        "rate:user:15",

        60
    )
```

---

# Feature Flags

Example

```python
redis_client.set(

    "feature:new-ui",

    "enabled"
)
```

Application

```python
if redis_client.get(

    "feature:new-ui"

):
    ...
```

No deployment required.

---

# Distributed Locks

Example

```python
redis_client.set(

    "lock:invoice",

    "1",

    nx=True,

    ex=30
)
```

Useful for

- Payments
- Inventory
- Scheduled jobs

---

# Leaderboards

Redis Sorted Set

```python
redis_client.zadd(

    "leaderboard",

    {

        "alice": 1500

    }
)
```

Top players

```python
redis_client.zrevrange(

    "leaderboard",

    0,

    9,

    withscores=True
)
```

---

# Pub/Sub Example

Publisher

```python
redis_client.publish(

    "notifications",

    "Order Created"
)
```

Subscriber

```python
pubsub = redis_client.pubsub()

pubsub.subscribe(
    "notifications"
)
```

Useful for

- Notifications
- Real-time updates
- Chat systems

---

# WebSocket Architecture

```
Client

↓

FastAPI WebSocket

↓

Redis Pub/Sub

↓

Other FastAPI Instances
```

Enables horizontal scaling.

---

# AI Prompt Caching

```
Prompt

↓

Redis

↓

Cached Response

↓

LLM
```

Repeated prompts avoid expensive inference.

---

# Shared State

Multiple FastAPI instances

```
App1

↓

Redis

↑

App2

↑

App3
```

All instances share

- Counters
- Sessions
- Locks
- Cache
- Rate limits

---

# High Availability

```
             FastAPI

      ┌────────┼────────┐

      ▼        ▼        ▼

    App1     App2     App3

      │        │        │

      └────────┼────────┘

               ▼

        Redis Sentinel

               ▼

      Primary + Replicas
```

---

# Monitoring

Useful commands

```
INFO

INFO stats

INFO memory

CLIENT LIST

SLOWLOG GET
```

Monitor

- Hit ratio
- Latency
- Memory
- Connections
- Evictions

---

# Common Production Use Cases

Redis is commonly used with FastAPI for:

- Query caching
- Response caching
- API rate limiting
- OTP storage
- Password reset tokens
- Feature flags
- Distributed locks
- WebSocket Pub/Sub
- Leaderboards
- AI prompt caching
- Temporary state
- Background jobs

---

# Common Mistakes

## Creating a Redis Client Per Request

Bad

```python
@app.get("/")

def home():

    client = redis.Redis(...)
```

Create one shared client instead.

---

## Forgetting TTL

Temporary data

- OTP
- Password reset
- Verification tokens

should always expire automatically.

---

## Caching Large Objects

Avoid caching huge query results.

Prefer

- IDs
- Lightweight DTOs
- Serialized dictionaries

---

## Hardcoding Redis Configuration

Bad

```python
host="localhost"
```

Use environment variables.

---

## No Fallback

If Redis fails

```
Application

↓

Crash
```

Always implement graceful degradation.

---

# Best Practices

- Create a single reusable Redis client during application startup.
- Use environment variables for all Redis configuration.
- Cache only expensive or frequently requested data.
- Apply TTLs to all temporary keys.
- Use descriptive key names and namespaces.
- Monitor Redis latency, memory usage, and hit ratio.
- Design fallback logic when Redis becomes unavailable.
- Keep cache entries small to improve serialization and network performance.

---

# Performance Considerations

| Feature | Benefit |
|----------|----------|
| Query Cache | Fewer database queries |
| Counters | Atomic operations |
| OTP Storage | Automatic expiration |
| Rate Limiting | Protects APIs |
| Distributed Locks | Prevents duplicate work |
| Pub/Sub | Real-time communication |
| Leaderboards | Extremely fast ranking |

---

# Production Considerations

For production deployments:

- Use Redis with connection pooling rather than creating new connections for each request.
- Deploy Redis with Sentinel or Cluster for high availability.
- Protect Redis with authentication, TLS, and private networking.
- Separate cache, queues, and application state using logical databases or key prefixes.
- Monitor hit ratio, latency, memory fragmentation, and connection counts.
- Design cache invalidation carefully to avoid stale data.
- Test Redis failover scenarios to ensure the application continues functioning during outages.

---

# Django vs FastAPI Redis Integration

| Feature | Django | FastAPI |
|----------|---------|----------|
| Built-in Cache Framework | ✅ Yes | ❌ No |
| Session Management | Built-in | Custom Implementation |
| Async Support | Limited | Native |
| Redis Client | django-redis / redis-py | redis-py |
| Response Caching | Built-in Options | Third-Party or Custom |
| Pub/Sub | Supported | Excellent |
| WebSocket Integration | Limited | Excellent |
| Background Tasks | Celery | Celery / BackgroundTasks |

---

# Summary

Redis is a critical infrastructure component for production FastAPI applications, providing high-speed caching, distributed counters, rate limiting, temporary storage, Pub/Sub messaging, and background coordination. By centralizing Redis configuration, reusing connections, applying TTLs appropriately, and implementing graceful failure handling, FastAPI applications can scale efficiently while maintaining low latency and high availability.

---

# Key Takeaways

- Redis significantly improves FastAPI performance by reducing database load.
- Create a single reusable Redis client instead of opening connections per request.
- Use Redis for caching, counters, OTPs, feature flags, distributed locks, and Pub/Sub.
- Cache individual objects with descriptive key names for easier invalidation.
- Apply TTLs to temporary data.
- Monitor Redis performance continuously in production.
- Use Sentinel or Cluster for high availability.
- Design FastAPI applications to continue operating even if Redis becomes temporarily unavailable.