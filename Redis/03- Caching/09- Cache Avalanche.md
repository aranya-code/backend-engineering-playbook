# Cache Avalanche

## Overview

A **Cache Avalanche** occurs when **a large number of cache entries expire simultaneously**, causing a sudden surge of requests to the backend database.

Unlike a **Cache Stampede**, which involves a **single hot key**, a Cache Avalanche involves **many keys expiring at nearly the same time**.

The result is a massive increase in database traffic, which can overload backend services and potentially lead to cascading failures across the system.

Cache Avalanche is one of the most common scalability issues in large Redis deployments.

---

# Cache Stampede vs Cache Avalanche

Cache Stampede

```
One Hot Key

↓

Expires

↓

Thousands of Requests

↓

Database
```

Only one cache entry expires.

---

Cache Avalanche

```
100,000 Keys

↓

Expire Together

↓

Millions of Requests

↓

Database
```

Thousands of cache entries expire simultaneously.

---

# Why Cache Avalanche Happens

Imagine an application starts at 9:00 AM.

All cached objects receive exactly the same TTL.

```
Application Startup

↓

Cache Everything

↓

TTL = 1 Hour

↓

10:00 AM

↓

Everything Expires
```

Now every request becomes a database query.

---

# Example Timeline

```
09:00

↓

Cache Loaded

↓

TTL = 3600 Seconds

↓

10:00

↓

All Keys Expire

↓

Database Traffic Explosion
```

---

# Normal Operation

```
Users

↓

Redis

↓

Cache Hits

↓

Fast Responses
```

Database load remains low.

---

# Avalanche Scenario

```
               Redis

                 │

        100,000 Keys Expire

                 │

      ┌──────────┼──────────┐

      ▼          ▼          ▼

 Database    Database    Database

      ▼          ▼          ▼

     Overloaded Backend
```

Every request bypasses Redis.

---

# Real Production Example

Imagine an e-commerce platform.

Cached:

- Products
- Categories
- Reviews
- Inventory
- Recommendations

All have

```
TTL = 1 Hour
```

Exactly one hour later

```
Millions of Requests

↓

Redis Miss

↓

Millions of SQL Queries
```

Database CPU reaches 100%.

---

# Consequences

Cache avalanche may cause:

- Database overload
- API timeouts
- Slow response times
- Cascading microservice failures
- Thread exhaustion
- Connection pool exhaustion
- Auto-scaling events
- Increased cloud costs
- Complete service outage

---

# Detecting Cache Avalanche

Typical metrics

Redis

```
Hit Ratio

↓

Sudden Drop
```

Database

```
Queries

↓

Massive Spike
```

Application

```
Latency

↓

Sharp Increase
```

Infrastructure

```
CPU

↓

Memory

↓

Connections

↓

Spike
```

---

# Root Causes

## Identical TTL Values

```
All Keys

↓

TTL = 3600

↓

Expire Together
```

Most common cause.

---

## Redis Restart

Suppose Redis loses memory.

```
Redis Restart

↓

Cache Empty

↓

Every Request

↓

Database
```

Entire cache must be rebuilt.

---

## Mass Cache Flush

```
FLUSHALL

↓

Cache Empty

↓

Database Storm
```

A production mistake can trigger an avalanche instantly.

---

## Scheduled Jobs

```
Nightly Refresh

↓

Delete Cache

↓

Morning Traffic

↓

Database Overload
```

Improper cache refresh strategies can create synchronized expirations.

---

# Prevention Strategy 1 — Randomized TTL (Jitter)

Instead of

```
TTL

↓

3600

3600

3600

3600
```

Use

```
3512

3625

3740

3448

3695
```

Keys expire gradually.

---

Python example

```python
import random

ttl = 3600 + random.randint(-300, 300)

redis.set(
    key,
    value,
    ex=ttl
)
```

A small amount of randomness dramatically reduces synchronized expiration.

---

# Prevention Strategy 2 — Refresh Ahead

Refresh important cache entries before expiration.

```
Worker

↓

Refresh

↓

TTL Reset

↓

No Expiration Wave
```

Ideal for:

- Homepages
- Product catalogs
- Dashboards

---

# Prevention Strategy 3 — Multi-Level Cache

```
Client

↓

Application Cache

↓

Redis

↓

Database
```

Even if Redis expires, the application cache absorbs part of the traffic.

Common technologies:

- Local in-memory cache
- Redis
- CDN

---

# Prevention Strategy 4 — Distributed Lock

If a cache miss occurs

```
Request

↓

Acquire Lock

↓

One Database Query

↓

Update Cache
```

Other requests wait.

Prevents database flooding.

---

# Prevention Strategy 5 — Cache Warming

After deployment

```
Deployment

↓

Worker

↓

Redis

↓

Popular Data Loaded
```

Users never experience cold cache.

---

# Prevention Strategy 6 — High Availability

Use Redis replication.

```
Application

↓

Redis Cluster

↓

Replica

↓

Primary Failure

↓

Replica Promoted
```

Reduces cache outages caused by Redis failures.

---

# Prevention Strategy 7 — Circuit Breaker

If the database becomes overloaded

```
Database

↓

Failure Threshold

↓

Circuit Opens

↓

Temporary Fallback
```

Prevents cascading failures.

---

# Prevention Strategy 8 — Rate Limiting

```
Database

↓

Maximum Queries

↓

Extra Requests Delayed
```

Protects backend systems during recovery.

---

# Architecture with Protection

```
                 Client Requests

                        │

                        ▼

                     Redis

                        │

        ┌───────────────┼───────────────┐

        ▼                               ▼

   Cache Hit                      Cache Miss

        │                               │

        ▼                               ▼

  Return Response            Distributed Lock

                                      │

                                      ▼

                               Database Query

                                      │

                                      ▼

                                Refresh Cache
```

---

# Multi-Level Cache Architecture

```
Client

↓

Application Cache

↓

Redis

↓

Database
```

Benefits

- Lower latency
- Reduced Redis traffic
- Better resilience

---

# Real-World Example

## Online Shopping

Without protection

```
Products

↓

Expire

↓

Database

↓

Crash
```

With randomized TTL

```
Products

↓

Expire Gradually

↓

Database Stable
```

---

## Video Streaming

```
Trending Videos

↓

Refresh Ahead

↓

Always Cached
```

Users experience consistent response times.

---

## Banking Dashboard

```
Dashboard

↓

Worker Refresh

↓

Latest Statistics

↓

Users
```

---

## News Portal

```
Breaking News

↓

CDN

↓

Redis

↓

Database
```

Multiple caching layers reduce backend pressure.

---

# Cache Avalanche vs Cache Stampede

| Feature | Cache Stampede | Cache Avalanche |
|----------|----------------|-----------------|
| Keys Involved | One | Many |
| Cause | Single Hot Key Expires | Large Number of Keys Expire |
| Database Load | High | Extremely High |
| Prevention | Locking | TTL Jitter + Refresh |
| Typical Scale | Hundreds of Requests | Millions of Requests |

---

# Cache Avalanche vs Cache Breakdown

Some engineers use **Cache Breakdown** as another name for **Cache Stampede**, while others define it as a hot key expiration causing concentrated database traffic.

Regardless of terminology:

- Stampede → One hot key
- Avalanche → Many keys
- Both require mitigation strategies.

---

# Common Production Use Cases

Avalanche prevention is critical for:

- Product catalogs
- CMS platforms
- News portals
- Video streaming
- Recommendation engines
- Search services
- Analytics dashboards
- Gaming leaderboards
- API Gateways

---

# Common Mistakes

## Same TTL Everywhere

```
3600

3600

3600

3600
```

Always introduce randomness.

---

## Cache Flush in Production

```
FLUSHALL

↓

Millions of Misses
```

Never execute destructive commands on production caches without a recovery strategy.

---

## Ignoring Redis Restart

Warm the cache after restart.

Cold Redis causes enormous backend load.

---

## No Monitoring

Monitor:

- Cache hit ratio
- Database QPS
- Evictions
- CPU
- Connection pool usage
- Latency

---

# Best Practices

- Add **5–10% TTL jitter** to all cache entries.
- Refresh hot keys before expiration.
- Warm critical cache entries after deployments or Redis restarts.
- Use Redis Cluster with replication for high availability.
- Implement distributed locking for expensive cache rebuilds.
- Introduce circuit breakers and rate limiting to protect backend services.
- Avoid bulk cache invalidation during peak traffic.
- Continuously monitor cache hit ratio and backend database load.

---

# Performance Considerations

| Technique | Database Load | Availability | Complexity |
|------------|---------------|--------------|------------|
| Random TTL | Very Low | High | Low |
| Refresh Ahead | Very Low | Very High | Medium |
| Cache Warming | Low | High | Medium |
| Distributed Lock | Low | High | Medium |
| Multi-Level Cache | Very Low | Excellent | High |
| Circuit Breaker | Protects DB | Excellent | Medium |

---

# Production Considerations

For production deployments:

- Never assign identical TTLs to large groups of cache entries.
- Apply randomized TTL values when writing cache data.
- Design cache warming jobs that prioritize the most frequently accessed keys.
- Use monitoring and alerting for sudden drops in cache hit ratio.
- Ensure Redis replication and automatic failover are configured for high availability.
- Combine multiple protection techniques—TTL jitter alone is often insufficient at large scale.
- Regularly load test cache expiration scenarios to validate system resilience.

---

# Decision Guide

| Scenario | Recommended Solution |
|----------|----------------------|
| Product Catalog | Refresh Ahead + TTL Jitter |
| Homepage | Refresh Ahead |
| Trending Content | Refresh Ahead + Multi-Level Cache |
| API Gateway | TTL Jitter + Circuit Breaker |
| CMS | Cache Warming |
| News Portal | CDN + Redis + Refresh Ahead |
| Banking Dashboard | Refresh Ahead |
| Large Enterprise Platform | Multi-Level Cache + Distributed Lock |

---

# Summary

A Cache Avalanche occurs when many cache entries expire simultaneously, causing a sudden surge of requests to the backend database. Unlike a Cache Stampede, which affects a single hot key, an avalanche impacts a large portion of the cache and can overwhelm backend infrastructure. Effective mitigation includes randomized TTLs, Refresh Ahead, cache warming, distributed locking, multi-level caching, and resilient backend protection mechanisms such as circuit breakers and rate limiting. Preventing cache avalanches is a key aspect of building highly available, internet-scale caching systems.

---

# Key Takeaways

- A Cache Avalanche occurs when **many cache entries expire at the same time**.
- The most common cause is assigning identical TTL values to large numbers of keys.
- Randomized TTLs (jitter) are the simplest and most effective prevention technique.
- Refresh Ahead and cache warming help keep hot data continuously available.
- Multi-level caching and Redis replication improve resilience during cache failures.
- Circuit breakers and rate limiting protect backend systems during traffic spikes.
- Monitor cache hit ratio, database QPS, CPU usage, and latency to detect avalanches early.
- Combining multiple mitigation strategies provides the best protection in production environments.