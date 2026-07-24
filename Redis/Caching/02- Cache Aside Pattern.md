# Cache Aside Pattern

## Overview

The **Cache Aside Pattern** (also known as **Lazy Loading**) is the most widely used caching strategy in modern backend systems.

In this pattern, the **application is responsible for managing the cache**. It first attempts to retrieve data from Redis. If the data is not found (a cache miss), the application fetches it from the database, stores it in Redis, and returns it to the client.

This pattern provides a good balance between simplicity, scalability, and performance, making it the default caching strategy for many large-scale applications.

It is used extensively by companies such as:

- Amazon
- Netflix
- Facebook
- Uber
- Airbnb
- Spotify
- LinkedIn

---

# How Cache Aside Works

```
                 Client
                    │
                    ▼
             Application Server
                    │
            Check Redis Cache
          ┌─────────┴─────────┐
          ▼                   ▼
     Cache Hit           Cache Miss
          │                   │
          ▼                   ▼
  Return Cached Data    Query Database
                              │
                              ▼
                      Store in Redis
                              │
                              ▼
                      Return Response
```

---

# Step-by-Step Workflow

### Step 1

Client requests data.

```
GET /users/1001
```

↓

Application receives the request.

---

### Step 2

Application checks Redis.

```
GET user:1001
```

---

### Step 3A — Cache Hit

```
Redis

↓

User Found

↓

Return Response
```

The database is never accessed.

---

### Step 3B — Cache Miss

```
Redis

↓

Not Found

↓

Database Query
```

Application queries the database.

---

### Step 4

Database returns data.

```
User

↓

John

↓

Developer

↓

London
```

---

### Step 5

Application stores the result in Redis.

```
SET user:1001

...

EX 3600
```

TTL = 1 hour.

---

### Step 6

Application returns the response to the client.

Future requests are served directly from Redis.

---

# Complete Flow

```
              Request

                 │

                 ▼

          Check Redis Cache

        ┌────────┴─────────┐

        ▼                  ▼

   Cache Hit          Cache Miss

        │                  │

        ▼                  ▼

 Return Response     Query Database

                           │

                           ▼

                    Store in Redis

                           │

                           ▼

                    Return Response
```

---

# Python Example (Pseudo Code)

```python
def get_user(user_id):
    key = f"user:{user_id}"

    user = redis.get(key)

    if user:
        return user

    user = database.get_user(user_id)

    redis.set(
        key,
        user,
        ex=3600
    )

    return user
```

The application completely controls cache behavior.

---

# Django Example

```python
from django.core.cache import cache

def get_user(user_id):

    key = f"user:{user_id}"

    user = cache.get(key)

    if user:
        return user

    user = User.objects.get(id=user_id)

    cache.set(
        key,
        user,
        timeout=3600
    )

    return user
```

---

# FastAPI Example

```python
@app.get("/users/{id}")
async def get_user(id: int):

    key = f"user:{id}"

    user = redis.get(key)

    if user:
        return user

    user = db.get_user(id)

    redis.set(
        key,
        user,
        ex=3600
    )

    return user
```

---

# Read Workflow

```
User Request

↓

Redis

↓

Hit?

├── Yes

│      ↓

│   Return Data

│

└── No

       ↓

Database

       ↓

Redis

       ↓

User
```

---

# Write Workflow

Updating data is slightly more complicated.

```
Update User

↓

Database

↓

Delete Redis Key

↓

Next Read Reloads Cache
```

This prevents stale cache entries.

---

# Cache Invalidation

Suppose a user changes their email.

```
Old Cache

↓

john@example.com
```

Database Update

```
john_new@example.com
```

Delete Cache

```
DEL user:1001
```

Next request

```
Database

↓

Redis Updated
```

---

# Cache Population

Cache entries are only created when needed.

```
Application

↓

First Request

↓

Database

↓

Redis

↓

Future Requests
```

This is why Cache Aside is also called **Lazy Loading**.

---

# Advantages

## Simple Implementation

No special Redis features are required.

Application controls everything.

---

## Reduced Database Load

```
100,000 Requests

↓

95,000 Redis

↓

5,000 Database
```

---

## Easy Cache Invalidation

Delete the cache whenever data changes.

```
Update

↓

Database

↓

Delete Cache
```

---

## Excellent Scalability

Works well for:

- Microservices
- REST APIs
- GraphQL
- Mobile APIs
- Distributed systems

---

# Disadvantages

## First Request is Slow

```
Cache Miss

↓

Database

↓

Redis

↓

Response
```

The initial request experiences higher latency.

---

## Stale Data

If cache isn't invalidated:

```
Database Updated

↓

Redis Still Old

↓

Incorrect Response
```

---

## Cache Stampede

If many requests arrive after expiration:

```
1000 Users

↓

Cache Miss

↓

1000 Database Queries
```

A later chapter explores this problem in detail.

---

## Duplicate Cache Population

Multiple servers may simultaneously load identical data.

```
Server A

↓

Database

Server B

↓

Database

Server C

↓

Database
```

This creates unnecessary database load.

---

# Cache Aside Lifecycle

```
Database

↓

Application

↓

Redis

↓

TTL

↓

Expiration

↓

Database Again
```

---

# Best TTL Values

| Data Type | Suggested TTL |
|------------|--------------:|
| Product Catalog | 1–6 hours |
| User Profile | 30–60 minutes |
| Configuration | 24 hours |
| Dashboard Data | 1–5 minutes |
| Search Results | 5–15 minutes |
| Session Data | 15–60 minutes |

TTL depends on how frequently the underlying data changes.

---

# Real-World Example

### Product Details API

Without cache

```
Client

↓

API

↓

Database
```

Every request queries the database.

---

With Cache Aside

```
Client

↓

API

↓

Redis

↓

Hit?

↓

Yes

↓

Response
```

The database is queried only when necessary.

---

# Suitable Use Cases

Cache Aside works well for:

- Product pages
- User profiles
- Categories
- Search filters
- CMS content
- Product inventory (with careful invalidation)
- Configuration
- Public APIs
- Frequently accessed reports

---

# Unsuitable Use Cases

Avoid Cache Aside for:

- High-frequency financial balances
- Real-time stock trading
- Strongly consistent transactional systems
- Ultra-low latency write-heavy workloads

Other caching patterns may be more appropriate.

---

# Common Production Use Cases

Large-scale systems commonly use Cache Aside for:

- E-commerce catalogs
- News websites
- Blogging platforms
- Recommendation systems
- Customer profiles
- Product pricing
- User settings
- API Gateway caching
- Search APIs
- Frequently viewed content

---

# Common Mistakes

## Forgetting Cache Invalidation

```
Database Updated

↓

Redis Not Deleted

↓

Old Data Returned
```

Always invalidate the cache after writes.

---

## Very Long TTL

```
Cache

↓

24 Hours

↓

Old Data
```

Choose TTLs based on business requirements.

---

## Caching Rarely Used Data

Caching every object wastes memory.

Prioritize frequently accessed data.

---

## Caching Large Objects

Instead of

```
Entire Product Catalog
```

Cache

```
Product ID

↓

Individual Product
```

Smaller cache entries improve efficiency.

---

# Best Practices

- Use descriptive cache keys.
- Always define TTL values.
- Delete cache entries after database updates.
- Monitor cache hit ratio.
- Cache frequently accessed objects only.
- Serialize objects efficiently (JSON, MessagePack, Protocol Buffers where appropriate).
- Consider adding randomized TTLs to reduce synchronized expirations.
- Use distributed locking or request coalescing to prevent duplicate cache population under high load.

---

# Performance Considerations

| Operation | Typical Latency |
|------------|----------------:|
| Redis Cache Hit | <1 ms |
| Database Query | 5–100 ms |
| Cache Miss | Database + Redis Write |
| Cache Hit | Redis Only |

Higher cache hit ratios significantly reduce application latency.

---

# Production Considerations

For production deployments:

- Use Redis as a shared distributed cache across application instances.
- Implement cache invalidation immediately after successful database writes.
- Add a small random offset (jitter) to TTL values to avoid mass expiration events.
- Monitor hit ratio, miss ratio, eviction count, and memory usage.
- Consider request coalescing or distributed locks to avoid multiple servers loading the same missing key simultaneously.
- Ensure applications continue to function correctly if Redis becomes temporarily unavailable (graceful degradation).
- Version cache keys when schema changes occur (for example, `v2:user:1001`).

---

# Cache Aside vs Direct Database Access

| Feature | Direct Database | Cache Aside |
|---------|-----------------|-------------|
| Latency | High | Very Low (Cache Hit) |
| Database Load | High | Low |
| Scalability | Limited | Excellent |
| Infrastructure Cost | Higher | Lower |
| Application Complexity | Low | Moderate |

---

# Summary

The Cache Aside Pattern is the most common caching strategy used in backend applications because it gives the application full control over cache population and invalidation. Data is loaded into Redis only when requested, reducing unnecessary memory consumption while significantly lowering database load for frequently accessed resources. Although developers must carefully manage cache invalidation and handle cache misses efficiently, Cache Aside remains the preferred approach for most read-heavy workloads due to its simplicity, flexibility, and scalability.

---

# Key Takeaways

- Cache Aside is also known as **Lazy Loading**.
- The application is responsible for reading from and writing to Redis.
- Cache hits are served directly from Redis, while cache misses query the database and populate the cache.
- Invalidate cache entries immediately after database updates to prevent stale data.
- Define appropriate TTL values based on data volatility.
- Add randomized TTLs and request coalescing to reduce cache stampedes.
- Cache Aside is ideal for read-heavy applications such as product catalogs, user profiles, and public APIs.
- Monitor hit ratio and cache performance continuously in production.