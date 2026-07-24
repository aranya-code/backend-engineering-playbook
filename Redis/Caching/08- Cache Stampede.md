# Cache Stampede

## Overview

A **Cache Stampede** (also called **Dogpile Effect**) occurs when a popular cache entry expires and **many requests simultaneously attempt to regenerate the same data from the database**.

Instead of one request rebuilding the cache, hundreds or thousands of requests hit the backend at the same time, overwhelming the database and potentially causing cascading failures.

Cache stampedes are one of the most common causes of production outages in high-traffic applications.

Companies that operate at internet scale spend considerable effort preventing cache stampedes because a single expired key can trigger thousands of expensive database queries.

---

# Why Cache Stampede Happens

Suppose an API response is cached for one hour.

```
Product Cache

↓

TTL = 1 Hour

↓

Expires

↓

10,000 Requests Arrive

↓

Database Hit
```

Instead of one database query, every request performs one.

---

# Normal Cache Flow

```
Client

↓

Redis

↓

Cache Hit

↓

Response
```

Everything works efficiently.

---

# Stampede Scenario

```
                 Redis

                   │

            Cache Expired

                   │

     ┌──────┬──────┬──────┬──────┐

     ▼      ▼      ▼      ▼

 Request Request Request Request

     ▼      ▼      ▼      ▼

 Database Database Database Database

     ▼      ▼      ▼      ▼

 Database Overloaded
```

Every request independently regenerates the same cache entry.

---

# Timeline

```
10:00

↓

Cache Created

↓

10:59

↓

Thousands of Users

↓

11:00

↓

Cache Expires

↓

11:00:01

↓

Database Storm
```

The database receives a sudden spike in traffic.

---

# Real Production Example

Imagine an e-commerce website.

```
Homepage Cache

↓

TTL = 30 Minutes

↓

Millions of Users

↓

Cache Expires

↓

Homepage Queries Database
```

Instead of one SQL query:

```
5000 Users

↓

5000 SQL Queries
```

Database CPU spikes dramatically.

---

# Why It Is Dangerous

A cache stampede can trigger:

- Database overload
- Slow API responses
- Increased latency
- Thread pool exhaustion
- Connection pool exhaustion
- Cascading service failures
- Complete application outage

---

# Database Impact

Without stampede

```
10,000 Requests

↓

Redis

↓

1 Database Query
```

With stampede

```
10,000 Requests

↓

10,000 Database Queries
```

Huge difference.

---

# Symptoms

Common production symptoms include:

- CPU spikes
- Slow SQL queries
- High database connections
- Increased API latency
- Redis hit ratio drops
- Application timeouts
- Auto-scaling events
- Increased cloud costs

---

# Detecting a Stampede

Monitor:

```
Redis

↓

Hit Ratio

↓

Sudden Drop
```

Database

```
Queries

↓

Huge Spike
```

Application

```
Latency

↓

Sudden Increase
```

These indicators often occur together.

---

# Prevention Strategy 1 — Distributed Lock

The most common solution.

```
Cache Miss

↓

Acquire Lock

↓

Success?

├── Yes

│      ↓

│ Database Query

│      ↓

│ Update Redis

│

└── No

       ↓

Wait

↓

Retry Redis
```

Only one request regenerates the cache.

---

# Lock Workflow

```
1000 Requests

↓

Redis Lock

↓

1 Winner

↓

Database

↓

Redis Updated

↓

999 Requests Read Cache
```

Database receives only one query.

---

# Redis Lock Example

```
SET lock:product:1001

value

NX

PX 5000
```

Meaning:

- NX → Create only if absent
- PX → Automatically expire after 5 seconds

If lock acquisition fails:

```
Sleep

↓

Retry Cache
```

---

# Python Example

```python
key = "product:1001"

value = redis.get(key)

if value:
    return value

lock = redis.set(
    "lock:product:1001",
    "1",
    nx=True,
    ex=5
)

if lock:

    value = database.load()

    redis.set(key, value, ex=3600)

    redis.delete("lock:product:1001")

else:

    time.sleep(0.1)

    return redis.get(key)
```

---

# Prevention Strategy 2 — Randomized TTL

Instead of identical expiration times:

```
Every Key

↓

1 Hour
```

Use:

```
58 Minutes

61 Minutes

63 Minutes

55 Minutes

59 Minutes
```

Keys expire gradually.

---

# Example

Instead of

```python
TTL = 3600
```

Use

```python
TTL = random.randint(3300, 3900)
```

This spreads database load over time.

---

# Prevention Strategy 3 — Refresh Ahead

Refresh popular cache entries before they expire.

```
55 Minutes

↓

Worker Refresh

↓

TTL Reset
```

Users never experience expiration.

---

# Prevention Strategy 4 — Request Coalescing

Instead of

```
100 Requests

↓

100 Database Calls
```

Coalesce requests.

```
100 Requests

↓

1 Database Call

↓

100 Responses
```

Many modern API gateways implement this optimization.

---

# Prevention Strategy 5 — Never Expire Hot Keys

Some data changes infrequently.

```
Configuration

↓

No TTL

↓

Update By Event
```

Instead of relying on expiration, update the cache when the source data changes.

---

# Prevention Strategy 6 — Stale-While-Revalidate

Serve slightly stale data while refreshing in the background.

```
Client

↓

Old Cache

↓

Immediate Response

↓

Background Refresh

↓

New Cache
```

Users receive fast responses while the cache is rebuilt.

---

# Stale-While-Revalidate Timeline

```
Cache Expired

↓

Serve Old Data

↓

Worker Refresh

↓

Replace Cache
```

Commonly used by CDNs and API gateways.

---

# Prevention Strategy 7 — Cache Warming

Preload frequently accessed data before users request it.

```
Deployment

↓

Worker

↓

Redis

↓

Users Arrive
```

Common for:

- Homepages
- Product catalogs
- Trending articles

---

# Architecture with Distributed Lock

```
                 Client Requests

          ┌──────────┼──────────┐

          ▼          ▼          ▼

        Redis      Redis      Redis

          ▼          ▼          ▼

     Cache Miss Cache Miss Cache Miss

              │

              ▼

       Distributed Lock

              │

       ┌──────┴──────┐

       ▼             ▼

 Database Query   Wait

       │             │

       ▼             ▼

   Update Cache   Retry Redis
```

---

# Real-World Example

## Product Details API

Without protection

```
10000 Users

↓

Product Cache Expires

↓

10000 SQL Queries
```

With distributed lock

```
10000 Users

↓

1 SQL Query

↓

Redis Updated

↓

9999 Cache Hits
```

---

# Banking Example

Exchange rates.

```
Redis

↓

Worker Refresh

↓

No User Waits
```

Critical financial APIs often refresh data before expiration.

---

# News Website

Trending articles.

```
Redis

↓

Refresh Ahead

↓

Always Available
```

---

# Social Media Feed

```
Popular Feed

↓

Refresh

↓

Millions of Reads
```

Hot content stays cached continuously.

---

# Common Production Use Cases

Stampede prevention is important for:

- Product catalogs
- User profiles
- Recommendation engines
- Homepages
- Trending content
- Configuration
- API Gateway responses
- Exchange rates
- Dashboard metrics

---

# Common Mistakes

## Identical TTLs

```
10000 Keys

↓

Expire Together

↓

Database Storm
```

Always add TTL jitter.

---

## No Locking

```
1000 Requests

↓

1000 SQL Queries
```

Use distributed locking for expensive cache rebuilds.

---

## Refreshing Everything

Only refresh frequently accessed data.

Refreshing cold keys wastes resources.

---

## Long Lock Duration

```
Worker Crashes

↓

Lock Never Released
```

Always use lock expiration (PX/EX).

---

## Ignoring Retry Logic

Requests that fail to acquire the lock should:

- Retry Redis
- Sleep briefly
- Use exponential backoff

Avoid immediately querying the database.

---

# Best Practices

- Use distributed locks for expensive cache regeneration.
- Add randomized TTLs (jitter) to avoid synchronized expiration.
- Refresh hot keys before they expire.
- Implement request coalescing where possible.
- Serve stale data while refreshing when business requirements allow.
- Continuously monitor cache hit ratio and database traffic.
- Keep lock durations short and always set expiration times.
- Cache only data that provides measurable performance benefits.

---

# Performance Considerations

| Technique | Database Load | User Latency | Complexity |
|-----------|---------------|--------------|------------|
| No Protection | Very High | High | Low |
| Distributed Lock | Very Low | Low | Moderate |
| Refresh Ahead | Very Low | Very Low | Moderate |
| Random TTL | Low | Low | Very Low |
| Request Coalescing | Very Low | Low | High |
| Stale-While-Revalidate | Very Low | Very Low | Moderate |

---

# Production Considerations

For production deployments:

- Use Redis distributed locks (`SET NX PX`) to ensure only one process rebuilds a cache entry.
- Add 5–10% random TTL jitter to all cache entries.
- Identify hot keys through monitoring and apply Refresh Ahead selectively.
- Monitor lock contention, cache misses, and database query spikes.
- Design cache rebuild operations to be idempotent.
- Consider stale-while-revalidate for APIs where slightly stale data is acceptable.
- Load test cache expiration scenarios before releasing new services.

---

# Decision Guide

| Scenario | Recommended Solution |
|----------|----------------------|
| Product Catalog | Distributed Lock + Refresh Ahead |
| Homepage Cache | Refresh Ahead |
| Configuration | Event-Based Updates |
| Dashboard | Refresh Ahead |
| User Profile | Distributed Lock |
| Exchange Rates | Stale-While-Revalidate |
| Trending Content | Random TTL + Refresh Ahead |
| Search Results | Request Coalescing |

---

# Summary

A Cache Stampede occurs when many requests simultaneously attempt to rebuild the same expired cache entry, causing a sudden surge in database traffic and potentially leading to service outages. Effective mitigation techniques include distributed locking, randomized TTLs, Refresh Ahead, request coalescing, stale-while-revalidate, and cache warming. Preventing cache stampedes is essential for maintaining low latency, protecting backend systems, and ensuring stable application performance under heavy traffic.

---

# Key Takeaways

- A cache stampede happens when multiple requests regenerate the same expired cache entry simultaneously.
- Without protection, a single expired key can overwhelm the database.
- Distributed locking (`SET NX PX`) is the most common prevention technique.
- Randomized TTLs reduce synchronized cache expirations.
- Refresh Ahead eliminates cache misses for frequently accessed data.
- Stale-While-Revalidate serves cached data while refreshing it in the background.
- Monitor hit ratio, cache misses, and database query spikes to detect stampedes.
- Stampede prevention is a critical component of production-grade Redis caching architectures.