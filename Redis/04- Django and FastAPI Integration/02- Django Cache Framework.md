# Django Cache Framework

## Overview

Django provides a built-in **Cache Framework** that abstracts caching behind a consistent API. Instead of interacting directly with Redis commands (`GET`, `SET`, `DEL`), developers use Django's cache interface while Redis acts as the underlying backend.

This abstraction allows applications to switch between different cache backends (Redis, Memcached, Local Memory, File-based, etc.) with minimal code changes.

For production applications, **Redis is the recommended backend** because it provides:

- High performance
- Persistence (optional)
- Distributed caching
- Atomic operations
- TTL support
- Horizontal scalability

---

# Django Cache Architecture

```
                Client

                   │

                   ▼

                Django

                   │

        Django Cache Framework

                   │

                   ▼

             Redis Backend

                   │

                   ▼

             PostgreSQL
```

The application interacts only with Django's cache API.

---

# Why Use Django Cache Framework?

Instead of

```python
import redis

client = redis.Redis(...)

client.set(...)
client.get(...)
```

Use

```python
from django.core.cache import cache

cache.set(...)
cache.get(...)
```

Advantages:

- Cleaner code
- Backend-independent
- Easier testing
- Better maintainability
- Built-in middleware support

---

# Installing Redis Backend

Install the required packages.

```bash
pip install redis django-redis
```

Verify installation

```bash
pip freeze
```

Example

```
django-redis==6.x.x

redis==6.x.x
```

---

# Configuring Redis

Open

```
settings.py
```

Configuration

```python
CACHES = {

    "default": {

        "BACKEND": "django_redis.cache.RedisCache",

        "LOCATION": "redis://127.0.0.1:6379/1",

        "OPTIONS": {

            "CLIENT_CLASS":
                "django_redis.client.DefaultClient"

        }
    }
}
```

---

# Using Environment Variables

Never hardcode Redis URLs.

Example

```python
import os

REDIS_URL = os.getenv(
    "REDIS_URL"
)

CACHES = {

    "default": {

        "BACKEND": "django_redis.cache.RedisCache",

        "LOCATION": REDIS_URL
    }
}
```

Example

```
REDIS_URL=redis://localhost:6379/1
```

---

# Testing Cache

Open Django shell

```bash
python manage.py shell
```

Example

```python
from django.core.cache import cache

cache.set(
    "hello",
    "world",
    timeout=60
)

cache.get("hello")
```

Output

```
world
```

---

# Cache Operations

## Store

```python
cache.set(
    "username",
    "alice",
    timeout=300
)
```

---

## Retrieve

```python
cache.get(
    "username"
)
```

---

## Delete

```python
cache.delete(
    "username"
)
```

---

## Check Existence

```python
cache.has_key(
    "username"
)
```

---

## Clear Cache

```python
cache.clear()
```

Be careful in production.

---

# Cache Timeout

Example

```python
cache.set(
    "product",
    value,
    timeout=1800
)
```

Meaning

```
30 Minutes
```

No timeout

```python
timeout=None
```

Immediate expiration

```python
timeout=0
```

---

# Cache Get with Default Value

Instead of

```python
value = cache.get("x")
```

Use

```python
value = cache.get(
    "x",
    default=[]
)
```

Avoids handling

```
None
```

---

# Increment and Decrement

Redis supports atomic counters.

```python
cache.set(
    "views",
    10
)

cache.incr(
    "views"
)
```

Decrement

```python
cache.decr(
    "views"
)
```

Useful for

- Page views
- API usage
- Inventory counters

---

# Cache Add

Only stores data if the key does not exist.

```python
cache.add(
    "lock",
    "1",
    timeout=30
)
```

Useful for simple distributed locks.

---

# Get or Set

One of the most useful methods.

```python
products = cache.get_or_set(

    "products",

    Product.objects.all(),

    timeout=1800
)
```

Workflow

```
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

---

# Cache Multiple Objects

Store

```python
cache.set_many({

    "user": user,

    "cart": cart,

    "profile": profile

})
```

Retrieve

```python
cache.get_many(

    ["user", "cart", "profile"]

)
```

Fewer network round trips.

---

# Delete Multiple Keys

```python
cache.delete_many(

    [

        "user",

        "cart"

    ]

)
```

---

# Cache Versioning

Django supports versioned cache keys.

```python
cache.set(

    "settings",

    data,

    version=2
)
```

Key becomes

```
settings:v2
```

Useful after schema changes.

---

# Low-Level Redis Access

Sometimes Redis features are needed.

```python
from django_redis import get_redis_connection

redis = get_redis_connection("default")
```

Now

```python
redis.publish(...)

redis.pipeline()

redis.scan()
```

Available.

---

# Caching Database Queries

Without cache

```
Client

↓

Django

↓

SQL

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

Response
```

Example

```python
products = cache.get("products")

if not products:

    products = list(

        Product.objects.all()

    )

    cache.set(

        "products",

        products,

        1800

    )
```

---

# Cache Invalidation

Suppose a product changes.

```
Update Product

↓

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
cache.delete(

    "products"
)
```

---

# View-Level Caching

Django provides decorators.

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)

def home(request):

    ...
```

Entire response cached.

TTL

```
15 Minutes
```

---

# URL-Based Caching

```
GET /products

↓

Cache Response
```

Different URLs receive different cache entries.

---

# Template Fragment Caching

Instead of caching an entire page

```
Navbar

↓

Cache

↓

Page Generated
```

Template

```html
{% load cache %}

{% cache 600 navbar %}

...

{% endcache %}
```

Useful for

- Navigation
- Footer
- Sidebar
- Trending products

---

# Middleware Caching

Entire site

```
Client

↓

Cache Middleware

↓

Response
```

Enable

```python
MIDDLEWARE = [

'django.middleware.cache.UpdateCacheMiddleware',

...

'django.middleware.cache.FetchFromCacheMiddleware'

]
```

---

# Cache Key Strategy

Poor

```
products
```

Better

```
products:category:12
```

Best

```
tenant:5:products:category:12
```

Namespaced keys prevent collisions.

---

# Serialization

Redis stores bytes.

Django automatically serializes objects.

Large objects increase:

- Memory usage
- Network traffic
- Serialization time

Prefer caching:

- IDs
- DTOs
- Lightweight dictionaries

---

# High Availability

Production

```
              Django

        ┌──────┼──────┐

        ▼      ▼      ▼

      App1   App2   App3

        │      │      │

        └──────┼──────┘

               ▼

         Redis Sentinel

               ▼

        Primary + Replicas
```

---

# Monitoring

Useful metrics

Redis

```
Hit Ratio

Memory

Latency

Evictions
```

Django

- Cache hit rate
- Cache misses
- Slow views
- Database queries

---

# Common Production Use Cases

Django Cache Framework is commonly used for:

- Product catalogs
- Homepages
- User profiles
- Search results
- Category pages
- Dashboard widgets
- API responses
- Feature flags
- Configuration data
- Frequently executed queries

---

# Common Mistakes

## Caching Entire QuerySets

Bad

```python
cache.set(
    "products",
    Product.objects.all()
)
```

QuerySets are lazy.

Instead

```python
list(
    Product.objects.all()
)
```

or serialize the data.

---

## Never Invalidating Cache

```
Database Updated

↓

Redis Still Old
```

Always delete or refresh affected cache entries.

---

## Very Long TTL

```
24 Hours
```

May cause stale data.

Choose TTLs based on data volatility.

---

## Caching User-Specific Data Globally

Bad

```
profile
```

Better

```
user:15:profile
```

Avoid data leakage between users.

---

## Using cache.clear()

```
Entire Cache

↓

Deleted
```

Prefer deleting only affected keys.

---

# Best Practices

- Use Django's cache API instead of directly interacting with Redis for standard caching.
- Namespace cache keys to avoid collisions.
- Cache serialized objects or lightweight dictionaries rather than lazy QuerySets.
- Apply appropriate TTLs based on business requirements.
- Invalidate cache immediately after successful database updates.
- Use view or template fragment caching for frequently rendered pages.
- Monitor hit ratio, evictions, latency, and memory usage.
- Keep cache entries small to reduce serialization overhead.

---

# Performance Considerations

| Technique | Benefit |
|------------|----------|
| Query Cache | Reduces SQL queries |
| View Cache | Eliminates view execution |
| Template Cache | Speeds page rendering |
| get_many() | Fewer Redis round trips |
| get_or_set() | Simplifies Cache Aside |
| Versioned Keys | Easy cache invalidation |

---

# Production Considerations

For production deployments:

- Use **django-redis** as the Redis backend.
- Configure Redis through environment variables.
- Deploy Redis with Sentinel or Cluster for high availability.
- Use key namespaces and versioning for maintainable cache management.
- Avoid caching sensitive user information without proper key isolation.
- Regularly monitor cache hit ratio and optimize TTL values.
- Ensure the application can continue operating if Redis becomes temporarily unavailable.

---

# Summary

Django's Cache Framework provides a clean, backend-independent API for integrating Redis into web applications. It simplifies caching by abstracting Redis operations while still allowing access to advanced Redis features when necessary. By combining query caching, view caching, template fragment caching, proper cache invalidation, and production-grade Redis configuration, developers can significantly improve application performance while maintaining consistency and scalability.

---

# Key Takeaways

- Django Cache Framework abstracts Redis behind a simple API.
- `django-redis` is the recommended Redis backend for Django.
- Use `cache.get()`, `cache.set()`, `cache.get_or_set()`, and `cache.get_many()` for efficient caching.
- Namespace keys and invalidate caches after database updates.
- Cache serialized data rather than lazy QuerySets.
- View and template fragment caching reduce rendering overhead.
- Monitor hit ratio, memory usage, and cache latency in production.
- Design cache strategies around application consistency and performance requirements.