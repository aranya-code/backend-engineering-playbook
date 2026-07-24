# Async Redis

## Overview

One of FastAPI's biggest strengths is its **asynchronous execution model**. Unlike traditional synchronous web frameworks, FastAPI can process thousands of concurrent requests without blocking worker threads.

To fully leverage this capability, Redis operations should also be asynchronous.

Using a synchronous Redis client inside an asynchronous FastAPI application blocks the event loop, reducing concurrency and increasing latency.

Production FastAPI applications should use the **async Redis client** provided by `redis-py`.

---

# Why Async Redis?

Consider an API request.

Without async

```
Request

↓

FastAPI

↓

Redis

↓

Wait...

↓

Database

↓

Response
```

While Redis is processing, the worker cannot perform other tasks.

---

With async

```
Request

↓

FastAPI

↓

await Redis

↓

Event Loop

↓

Handle Other Requests

↓

Redis Response

↓

Continue
```

The worker remains productive.

---

# Synchronous vs Asynchronous

## Synchronous

```
Request A

↓

Redis

↓

Finished

↓

Request B

↓

Redis

↓

Finished
```

Each request waits for the previous one.

---

## Asynchronous

```
Request A

↓

await Redis

↓

Request B

↓

await Redis

↓

Request C

↓

await Redis

↓

Responses Returned
```

Multiple requests are handled concurrently.

---

# FastAPI Event Loop

```
          Request 1

               │

               ▼

          await Redis

               │

               ▼

        Event Loop Switches

               │

        ┌──────┼──────┐

        ▼      ▼      ▼

   Request2 Request3 Request4

               │

               ▼

      Redis Response Ready

               │

               ▼

Continue Processing
```

This is the foundation of FastAPI scalability.

---

# Installing Async Redis

```bash
pip install redis[hiredis]
```

The modern `redis-py` package supports both synchronous and asynchronous APIs.

---

# Importing Async Redis

Instead of

```python
import redis
```

Use

```python
from redis.asyncio import Redis
```

---

# Creating an Async Client

```python
from redis.asyncio import Redis

redis_client = Redis(

    host="localhost",

    port=6379,

    db=0,

    decode_responses=True
)
```

---

# Project Structure

```
app/

├── main.py

├── redis_client.py

├── routes/

├── services/

└── config.py
```

Example

```
redis_client.py
```

```python
from redis.asyncio import Redis

redis_client = Redis(

    host="localhost",

    port=6379,

    decode_responses=True
)
```

---

# Testing the Connection

```python
await redis_client.set(

    "framework",

    "FastAPI"
)

value = await redis_client.get(

    "framework"
)
```

Output

```
FastAPI
```

---

# Using Async Redis in FastAPI

```python
from fastapi import FastAPI

from redis_client import redis_client

app = FastAPI()


@app.get("/")

async def home():

    visits = await redis_client.incr(

        "homepage"

    )

    return {

        "visits": visits

    }
```

Notice

```
async

await
```

throughout the code.

---

# Reading Data

```python
value = await redis_client.get(

    "user:15"
)
```

---

# Writing Data

```python
await redis_client.set(

    "user:15",

    "Alice"
)
```

---

# Deleting Data

```python
await redis_client.delete(

    "user:15"
)
```

---

# Expiring Keys

```python
await redis_client.set(

    "otp",

    "483921",

    ex=300
)
```

Expires automatically.

---

# Working with JSON

Store

```python
import json

await redis_client.set(

    "product:1",

    json.dumps(product)
)
```

Retrieve

```python
product = json.loads(

    await redis_client.get(

        "product:1"
    )
)
```

---

# Async Cache-Aside Pattern

```
Request

↓

Redis

↓

Hit?

├── Yes

│ Return

│

└── No

↓

Database

↓

Redis

↓

Return
```

Example

```python
@app.get("/products")

async def products():

    cached = await redis_client.get(

        "products"
    )

    if cached:

        return json.loads(cached)

    data = await fetch_products()

    await redis_client.set(

        "products",

        json.dumps(data),

        ex=1800
    )

    return data
```

---

# Async Counters

```python
count = await redis_client.incr(

    "page_views"
)
```

Useful for

- Views
- Downloads
- API usage
- Likes

---

# Async Lists

Push

```python
await redis_client.lpush(

    "jobs",

    "task1"
)
```

Retrieve

```python
await redis_client.rpop(

    "jobs"
)
```

---

# Async Sets

```python
await redis_client.sadd(

    "online_users",

    "alice"
)
```

Retrieve

```python
await redis_client.smembers(

    "online_users"
)
```

---

# Async Sorted Sets

Leaderboard

```python
await redis_client.zadd(

    "leaderboard",

    {

        "alice": 500

    }
)
```

Top players

```python
await redis_client.zrevrange(

    "leaderboard",

    0,

    9,

    withscores=True
)
```

---

# Async Pub/Sub

Publisher

```python
await redis_client.publish(

    "orders",

    "created"
)
```

Subscriber

```python
pubsub = redis_client.pubsub()

await pubsub.subscribe(

    "orders"
)
```

---

# Background Consumer

Example

```python
async for message in pubsub.listen():

    print(message)
```

Useful for

- Notifications
- WebSockets
- Event processing

---

# Pipelines

Without pipeline

```
SET

↓

GET

↓

EXPIRE
```

Three network round trips.

---

With pipeline

```
Pipeline

↓

SET

GET

EXPIRE

↓

Single Network Trip
```

Example

```python
async with redis_client.pipeline() as pipe:

    pipe.set("a", 1)

    pipe.set("b", 2)

    pipe.set("c", 3)

    await pipe.execute()
```

---

# Transactions

```python
async with redis_client.pipeline(

    transaction=True

) as pipe:

    pipe.set("balance", 100)

    pipe.incr("counter")

    await pipe.execute()
```

Commands execute atomically.

---

# Connection Lifecycle

FastAPI supports startup and shutdown events.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):

    yield

    await redis_client.close()
```

Always close connections gracefully.

---

# Error Handling

Example

```python
from redis.exceptions import RedisError

try:

    value = await redis_client.get("x")

except RedisError:

    value = None
```

Fallback gracefully.

---

# Timeouts

```python
Redis(

    socket_timeout=5,

    socket_connect_timeout=5
)
```

Avoid hanging requests.

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

Monitor

```
Latency

Memory

Connections

Blocked Clients

Slowlog

Hit Ratio
```

Useful commands

```
INFO

SLOWLOG GET

CLIENT LIST
```

---

# Common Production Use Cases

Async Redis is commonly used for:

- Response caching
- Query caching
- API rate limiting
- OTP storage
- Distributed locks
- Session storage
- Feature flags
- Leaderboards
- Real-time notifications
- Pub/Sub messaging
- AI prompt caching
- Background job coordination

---

# Common Mistakes

## Using Synchronous Redis in Async Code

Bad

```python
import redis

client = redis.Redis(...)
```

This blocks the event loop.

Always use

```python
from redis.asyncio import Redis
```

---

## Forgetting await

Bad

```python
redis_client.get("x")
```

Correct

```python
await redis_client.get("x")
```

---

## Creating Multiple Clients

Bad

```python
@app.get("/")

async def home():

    Redis(...)
```

Create one shared client during application startup.

---

## Not Closing Connections

Open connections accumulate over time.

Always close Redis during application shutdown.

---

## No Timeout

Network failures may block requests indefinitely.

Configure socket timeouts.

---

# Best Practices

- Use `redis.asyncio.Redis` for all FastAPI applications.
- Create a single shared Redis client during application startup.
- Always use `await` for Redis operations.
- Batch commands using pipelines where appropriate.
- Configure connection and socket timeouts.
- Close Redis connections during application shutdown.
- Handle Redis failures gracefully with fallback logic.
- Monitor latency, memory usage, connection counts, and slow commands.

---

# Performance Considerations

| Feature | Benefit |
|----------|----------|
| Async I/O | High concurrency |
| Await | Non-blocking execution |
| Pipelines | Fewer network round trips |
| Pub/Sub | Real-time communication |
| Atomic Operations | Safe concurrent updates |
| Connection Reuse | Lower overhead |

---

# Production Considerations

For production deployments:

- Use the asynchronous Redis client (`redis.asyncio`) with FastAPI.
- Deploy Redis behind Sentinel or Cluster for high availability.
- Configure connection pooling to reduce connection overhead.
- Use pipelines for batches of related Redis commands.
- Set socket timeouts to prevent stalled requests.
- Monitor event loop latency alongside Redis metrics.
- Design graceful fallbacks so temporary Redis outages do not take down the API.

---

# Async Redis vs Sync Redis

| Feature | Sync Redis | Async Redis |
|----------|------------|-------------|
| Event Loop | Blocks | Non-blocking |
| FastAPI Compatibility | Poor | Excellent |
| High Concurrency | Limited | Excellent |
| Throughput | Moderate | High |
| Recommended for FastAPI | ❌ No | ✅ Yes |

---

# Summary

FastAPI achieves its performance through asynchronous request handling, and Redis integration should follow the same model. Using `redis.asyncio` allows Redis operations to execute without blocking the event loop, enabling the application to handle thousands of concurrent requests efficiently. Combined with connection reuse, pipelines, proper timeout configuration, and graceful error handling, asynchronous Redis is the foundation of scalable, production-grade FastAPI services.

---

# Key Takeaways

- Use `redis.asyncio.Redis` instead of the synchronous Redis client in FastAPI.
- Always `await` Redis operations to avoid blocking the event loop.
- Reuse a single Redis client rather than creating connections per request.
- Use pipelines to reduce network round trips.
- Configure timeouts and close connections during application shutdown.
- Handle Redis failures gracefully with fallback mechanisms.
- Monitor Redis performance and event loop health together.
- Async Redis is essential for building highly concurrent FastAPI applications.