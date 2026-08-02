# Common Integration Mistakes

## Overview

Redis is relatively simple to use, but integrating it into production Django and FastAPI applications incorrectly can introduce serious problems.

Many production incidents involving Redis are caused not by Redis itself, but by:

- Poor cache design
- Missing expiration policies
- Incorrect key naming
- Lack of monitoring
- Connection management issues
- Security misconfigurations
- Improper serialization
- Incorrect assumptions about Redis persistence

This chapter covers the most common Redis integration mistakes seen in production systems and how to avoid them.

---

# Mistake 1: Creating a New Connection for Every Request

Bad

```
Incoming Request

↓

Create Redis Connection

↓

Execute

↓

Close Connection
```

Example

```python
@app.get("/products")
async def products():

    client = Redis(
        host="localhost"
    )

    return await client.get("products")
```

Problems

- High latency
- TCP handshake overhead
- Resource exhaustion
- Poor scalability

---

Correct Approach

```
Application Startup

↓

Create Connection Pool

↓

Reuse Connections
```

Example

```python
from redis.asyncio import Redis

redis_client = Redis(
    host="redis"
)
```

Reuse the same client everywhere.

---

# Mistake 2: Forgetting TTL

Bad

```python
redis.set(
    "otp",
    "483921"
)
```

OTP never expires.

Eventually Redis becomes full.

---

Correct

```python
redis.set(

    "otp",

    "483921",

    ex=300
)
```

Always assign expiration to temporary data.

Examples

- OTP
- Password reset token
- Verification code
- Login challenge

---

# Mistake 3: Using Generic Cache Keys

Bad

```
products
```

```
profile
```

```
orders
```

Large applications quickly experience collisions.

---

Better

```
products:page:1
```

```
user:15:profile
```

```
tenant:12:orders
```

Namespaced keys are easier to manage.

---

# Mistake 4: Storing Huge Objects

Bad

```
Entire DataFrame

↓

Redis
```

Problems

- Large memory usage
- Slow serialization
- Network overhead

---

Better

```
Report ID

↓

Worker Loads Data
```

Only store lightweight objects.

---

# Mistake 5: Caching QuerySets

Bad

```python
cache.set(

    "products",

    Product.objects.all()
)
```

QuerySets are lazy.

Unexpected behavior may occur.

---

Correct

```python
products = list(

    Product.objects.all()
)

cache.set(

    "products",

    products
)
```

---

# Mistake 6: Never Invalidating Cache

```
Database Updated

↓

Redis

↓

Old Data
```

Users continue seeing stale information.

---

Correct Workflow

```
Update Database

↓

Delete Cache

↓

Next Request

↓

Fresh Cache
```

---

Example

```python
cache.delete(

    "products"
)
```

---

# Mistake 7: Using Redis as Primary Storage

Redis is not a replacement for relational databases.

Bad

```
Orders

↓

Redis Only
```

Redis restart

↓

Orders lost.

---

Correct

```
PostgreSQL

↓

Source of Truth

↓

Redis Cache
```

Redis accelerates access.

The database stores permanent data.

---

# Mistake 8: Ignoring Redis Failures

Bad

```
Redis Down

↓

API Crash
```

---

Correct

```
Redis Down

↓

Read Database

↓

Continue
```

Always implement graceful degradation.

Example

```python
try:

    data = cache.get("products")

except Exception:

    data = None
```

---

# Mistake 9: No Monitoring

Without monitoring

```
Memory Full

↓

Redis Slow

↓

Application Slow
```

Nobody knows why.

---

Monitor

- Memory
- Latency
- Hit ratio
- Miss ratio
- Evictions
- Connections
- Slow commands

---

# Mistake 10: Unlimited Memory

Without

```
maxmemory
```

Redis consumes all available RAM.

Eventually

```
Linux OOM Killer

↓

Redis Killed
```

Configure

```
maxmemory
```

and

```
maxmemory-policy
```

---

# Mistake 11: No Authentication

Bad

```
Internet

↓

Redis

↓

Everyone Can Connect
```

---

Correct

```
Application

↓

Authentication

↓

Redis
```

Enable

- Password
- ACL
- TLS

---

# Mistake 12: Public Redis

Bad

```
Internet

↓

Redis
```

Common attack target.

---

Correct

```
Application

↓

Private Network

↓

Redis
```

Never expose Redis publicly.

---

# Mistake 13: Using KEYS in Production

Bad

```
KEYS *
```

Redis blocks while scanning.

Large datasets may freeze Redis.

---

Correct

```
SCAN
```

Example

```bash
SCAN 0
```

Non-blocking.

---

# Mistake 14: Blocking Commands

Avoid

```
KEYS

FLUSHALL

FLUSHDB

SAVE
```

during peak traffic.

Prefer

- SCAN
- Asynchronous operations
- Scheduled maintenance

---

# Mistake 15: Huge Pipelines

Bad

```
1 Million Commands

↓

Pipeline
```

Consumes excessive memory.

Better

```
1000 Commands

↓

Execute

↓

Repeat
```

Batch large operations.

---

# Mistake 16: Using Redis for Large Files

Bad

```
PDF

↓

Redis
```

```
Video

↓

Redis
```

Redis is an in-memory database.

Large binary objects waste memory.

---

Correct

```
S3

↓

Store File

↓

Redis Stores Metadata
```

---

# Mistake 17: No Connection Pooling

Bad

```
Every Request

↓

New Connection
```

---

Correct

```
Application Startup

↓

Shared Pool

↓

Reuse
```

Connection pooling dramatically improves performance.

---

# Mistake 18: Using Synchronous Redis in Async FastAPI

Bad

```python
import redis
```

Inside

```python
async def
```

Blocks the event loop.

---

Correct

```python
from redis.asyncio import Redis
```

---

# Mistake 19: Sharing Cache Keys Across Tenants

Bad

```
products
```

Tenant A overwrites

Tenant B.

---

Correct

```
tenant:15:products
```

Isolation prevents data leakage.

---

# Mistake 20: Caching Sensitive Data

Avoid caching

- Passwords
- Credit cards
- Secrets
- Access tokens
- Encryption keys

Instead

Cache

- User IDs
- Configuration
- Temporary metadata

---

# Mistake 21: Ignoring Serialization Cost

Large JSON

↓

Slow

Small DTO

↓

Fast

Consider

- ORJSON
- MessagePack
- Efficient DTOs

---

# Mistake 22: Poor TTL Strategy

Bad

```
Everything

↓

24 Hours
```

Different data changes at different rates.

Example

| Data | TTL |
|-------|-----|
| OTP | 5 Minutes |
| Product List | 30 Minutes |
| User Profile | 15 Minutes |
| Feature Flags | 1 Hour |
| AI Responses | 24 Hours |

---

# Mistake 23: Mixing Workloads

Bad

```
Cache

Sessions

Celery

Pub/Sub

Rate Limits

↓

Same Keys
```

Better

```
cache:

session:

queue:

rate:

pubsub:
```

Namespaces improve organization.

---

# Mistake 24: No Retry Strategy

External services fail.

```
Redis

↓

Temporary Failure

↓

Retry

↓

Success
```

Configure retries with exponential backoff.

---

# Mistake 25: Assuming Redis is Always Fast

Redis performance depends on

- Memory
- Network
- CPU
- Large keys
- Slow commands
- Replication lag

Always measure performance.

---

# Production Incident Example

Suppose an e-commerce platform caches products.

```
Update Price

↓

Database Updated

↓

Redis Not Updated

↓

Customers See Wrong Price
```

Root cause

No cache invalidation.

Solution

```
Update Database

↓

Delete Cache

↓

Next Request

↓

Fresh Cache
```

---

# Production Readiness Checklist

| Item | Status |
|-------|--------|
| Connection Pooling | ✅ |
| TTL Configured | ✅ |
| Authentication Enabled | ✅ |
| TLS Enabled | ✅ |
| Monitoring Enabled | ✅ |
| Cache Invalidation Strategy | ✅ |
| Retry Logic | ✅ |
| Key Namespace | ✅ |
| Async Client (FastAPI) | ✅ |
| Graceful Fallback | ✅ |

---

# Common Mistakes Summary

| Mistake | Solution |
|----------|----------|
| New Connection Per Request | Connection Pool |
| No TTL | Expiration |
| Generic Keys | Namespaced Keys |
| Huge Objects | Store IDs |
| No Cache Invalidation | Delete/Refresh Cache |
| Public Redis | Private Network |
| No Monitoring | Prometheus/Grafana |
| KEYS * | SCAN |
| Sync Redis in FastAPI | Async Redis |
| No Fallback | Graceful Degradation |

---

# Best Practices

- Create a single shared Redis client backed by a connection pool.
- Use descriptive, namespaced cache keys.
- Apply TTLs to all temporary data.
- Treat PostgreSQL or another durable database as the source of truth.
- Never expose Redis directly to the internet.
- Enable authentication, TLS, and ACLs.
- Monitor memory usage, hit ratio, latency, and connection counts.
- Regularly test Redis failure scenarios and disaster recovery.

---

# Performance Considerations

| Practice | Benefit |
|-----------|----------|
| Connection Pooling | Lower latency |
| Async Redis | Better concurrency |
| Small Cache Entries | Faster serialization |
| SCAN Instead of KEYS | Non-blocking operations |
| TTL Management | Prevents stale data |
| Cache Invalidation | Maintains consistency |

---

# Production Considerations

For production deployments:

- Review Redis integration during code reviews to catch common mistakes early.
- Load test cache behavior under realistic traffic patterns.
- Validate cache invalidation for every data modification workflow.
- Configure alerts for memory usage, eviction rates, connection exhaustion, and replication lag.
- Regularly audit Redis security settings, including authentication, ACLs, and network access.
- Document key naming conventions and TTL policies across engineering teams.

---

# Summary

Most Redis-related production issues arise from integration mistakes rather than Redis itself. Poor key design, missing expiration policies, inadequate security, lack of monitoring, and improper connection management can lead to stale data, performance degradation, and outages. By following established best practices—using connection pools, namespaced keys, TTLs, graceful fallbacks, and comprehensive monitoring—you can build Redis integrations that are reliable, secure, and scalable.

---

# Key Takeaways

- Reuse Redis connections through connection pooling.
- Always apply TTLs to temporary data.
- Use descriptive, namespaced cache keys.
- Never use Redis as the primary database for critical business data.
- Invalidate caches after data changes.
- Use `SCAN` instead of `KEYS` in production.
- Protect Redis with authentication, TLS, ACLs, and private networking.
- Monitor Redis continuously and design applications to tolerate Redis outages.