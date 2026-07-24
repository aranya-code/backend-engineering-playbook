# Redis with Django

## Overview

Redis is one of the most commonly used technologies in Django applications. While many developers initially adopt Redis only for caching, production Django systems use Redis for much more:

- Caching
- Session storage
- Celery broker
- Celery result backend
- Distributed locks
- Rate limiting
- Real-time notifications
- Background processing
- Temporary data storage

A modern Django application often communicates with Redis on nearly every request, making Redis a core infrastructure component rather than just an optional cache.

---

# Why Django Uses Redis

Without Redis

```
Client

↓

Django

↓

PostgreSQL

↓

Response
```

Every request accesses the database.

---

With Redis

```
Client

↓

Django

↓

Redis

↓

Cache Hit

↓

Response
```

Database load decreases significantly.

---

# Common Django Architecture

```
                Client

                   │

                   ▼

             Nginx / Load Balancer

                   │

                   ▼

                 Django

        ┌─────────┼─────────┐

        ▼         ▼         ▼

     Redis      Celery    PostgreSQL

        │

        ▼

 Session / Cache / Queue
```

Redis serves multiple responsibilities simultaneously.

---

# Installing Redis

Ubuntu

```bash
sudo apt update
sudo apt install redis-server
```

Start Redis

```bash
sudo systemctl start redis
```

Enable startup

```bash
sudo systemctl enable redis
```

Check status

```bash
redis-cli ping
```

Output

```
PONG
```

---

# Installing Python Packages

The recommended client is **redis-py**.

```bash
pip install redis
```

Verify

```bash
pip freeze | grep redis
```

Example

```
redis==6.x.x
```

---

# Connecting Django to Redis

Example

```python
import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)
```

---

# Testing Connection

```python
redis_client.set("name", "Aranya")

print(redis_client.get("name"))
```

Output

```
Aranya
```

---

# Django Project Structure

```
project/

├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── app/
│
├── requirements.txt
│
└── manage.py
```

Redis configuration generally belongs in

```
settings.py
```

or

```
redis.py
```

---

# Environment Variables

Never hardcode Redis credentials.

Example

```
REDIS_HOST=localhost

REDIS_PORT=6379

REDIS_DB=0

REDIS_PASSWORD=
```

Using Django settings

```python
import os

REDIS_HOST = os.getenv("REDIS_HOST")
```

---

# Redis Connection Helper

Instead of creating multiple clients

```python
redis.Redis(...)
```

Create one reusable client.

```python
import redis

client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)
```

Import

```python
from config.redis import client
```

throughout the project.

---

# Basic Redis Operations

Store

```python
client.set(
    "username",
    "alice"
)
```

Retrieve

```python
client.get("username")
```

Delete

```python
client.delete("username")
```

Exists

```python
client.exists("username")
```

---

# Using Expiration

Temporary cache

```python
client.set(
    "otp",
    "348291",
    ex=300
)
```

Automatically expires after

```
300 Seconds
```

---

# JSON Objects

Redis stores strings.

Serialize

```python
import json

user = {
    "id": 1,
    "name": "Alice"
}

client.set(
    "user:1",
    json.dumps(user)
)
```

Retrieve

```python
user = json.loads(
    client.get("user:1")
)
```

---

# Using Redis in Django Views

Example

```python
from django.http import JsonResponse

from config.redis import client

def home(request):

    visits = client.incr("homepage")

    return JsonResponse({
        "visits": visits
    })
```

Redis becomes a distributed counter.

---

# Caching Expensive Queries

Instead of

```
Request

↓

Database

↓

Response
```

Use

```
Request

↓

Redis

↓

Miss?

↓

Database

↓

Redis

↓

Response
```

Example

```python
from django.core.serializers import serialize

def products(request):

    data = client.get("products")

    if data:

        return JsonResponse(data, safe=False)

    queryset = Product.objects.all()

    serialized = serialize(
        "json",
        queryset
    )

    client.set(
        "products",
        serialized,
        ex=1800
    )

    return JsonResponse(
        serialized,
        safe=False
    )
```

---

# Using Redis for Counters

Example

```
Article Views
```

```python
client.incr(
    f"article:{id}:views"
)
```

Much faster than SQL

```
UPDATE views = views + 1
```

---

# Feature Flags

Example

```
feature:new-dashboard
```

```python
client.set(
    "feature:new-dashboard",
    "enabled"
)
```

Application

```python
if client.get(
    "feature:new-dashboard"
):
    ...
```

Feature flags can be changed without redeploying.

---

# Temporary Tokens

Password reset

```python
client.set(
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
Phone Number

↓

OTP

↓

Redis

↓

Expire
```

Example

```python
client.set(
    "otp:9876543210",
    "841923",
    ex=300
)
```

---

# Distributed Locks

Example

```python
client.set(
    "lock:invoice",
    "1",
    nx=True,
    ex=30
)
```

Useful for preventing duplicate processing.

---

# Using Redis for API Rate Limiting

```
User

↓

Redis Counter

↓

Allow?

↓

Response
```

Example

```python
count = client.incr(
    "rate:user:15"
)

if count == 1:
    client.expire(
        "rate:user:15",
        60
    )
```

---

# Redis as Shared State

Without Redis

```
App A

Session

App B

Different Session
```

With Redis

```
App A

↓

Redis

↑

App B
```

All Django instances share the same state.

---

# High Availability

Production architecture

```
                 Django

        ┌────────┼────────┐

        ▼        ▼        ▼

     App1     App2     App3

        │        │        │

        └────────┼────────┘

                 ▼

           Redis Sentinel

                 ▼

           Redis Primary

                 ▼

             Replicas
```

---

# Monitoring Redis

Useful commands

Memory

```
INFO memory
```

Statistics

```
INFO stats
```

Clients

```
CLIENT LIST
```

Slow operations

```
SLOWLOG GET
```

---

# Production Folder Structure

```
project/

config/

├── redis.py

├── settings.py

├── celery.py

├── logging.py

apps/

services/

cache/

utils/
```

Keep Redis code centralized.

---

# Common Production Use Cases

Redis is commonly used in Django for:

- Page caching
- Query caching
- Session storage
- Authentication
- OTP storage
- Feature flags
- Shopping carts
- Distributed locks
- API rate limiting
- Leaderboards
- Background task queues
- Notification systems

---

# Common Mistakes

## Creating a New Redis Connection Per Request

Bad

```python
def view(request):

    client = redis.Redis(...)
```

Reuse a shared connection pool instead.

---

## Hardcoding Configuration

Avoid

```python
host="localhost"
```

Use environment variables.

---

## Storing Large Objects

Avoid caching huge querysets or binary data.

Redis performs best with relatively small values.

---

## Forgetting Expiration

Temporary data should always have a TTL.

Examples include:

- OTPs
- Password reset tokens
- Sessions
- Verification codes

---

## Ignoring Redis Failures

Applications should continue functioning if Redis becomes unavailable.

Implement graceful fallbacks to the database where appropriate.

---

# Best Practices

- Use a single shared Redis client or connection pool.
- Store configuration in environment variables.
- Cache only expensive and frequently accessed data.
- Apply TTLs to temporary keys.
- Serialize complex objects using JSON or MessagePack.
- Keep Redis values reasonably small.
- Monitor Redis memory, latency, and slow commands.
- Design the application to degrade gracefully if Redis is unavailable.

---

# Performance Considerations

| Feature | Benefit |
|----------|----------|
| Query Cache | Reduces database load |
| Shared Sessions | Supports horizontal scaling |
| Counters | Atomic and extremely fast |
| Feature Flags | No application restart required |
| OTP Storage | Automatic expiration |
| Distributed Locks | Prevent duplicate processing |

---

# Production Considerations

For production deployments:

- Use Redis with connection pooling rather than creating clients per request.
- Deploy Redis with Sentinel or Cluster for high availability.
- Secure Redis using authentication, network isolation, and TLS where supported.
- Monitor cache hit ratio, memory usage, latency, and connection counts.
- Separate logical databases or key namespaces for different workloads (cache, sessions, queues).
- Avoid treating Redis as the primary data store for critical business data.
- Test application behavior during Redis outages to ensure graceful degradation.

---

# Summary

Redis is a foundational component in modern Django applications, enabling high-performance caching, distributed sessions, rate limiting, background processing, and temporary data storage. Beyond simple caching, Redis helps Django applications scale horizontally, reduce database load, and improve response times. Proper configuration, connection management, monitoring, and failure handling are essential for building reliable production systems.

---

# Key Takeaways

- Redis integrates seamlessly with Django for much more than caching.
- Use a shared Redis client with connection pooling for efficiency.
- Store sessions, OTPs, counters, feature flags, and temporary tokens in Redis.
- Apply TTLs to short-lived data to avoid stale entries.
- Centralize Redis configuration and use environment variables.
- Design applications to handle Redis failures gracefully.
- Monitor Redis continuously in production for performance and reliability.
- Redis is a core infrastructure component for scalable Django applications.