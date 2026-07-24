# Cache Eviction Strategies

## Overview

Redis stores data entirely in memory. Since memory is finite, Redis eventually reaches its configured memory limit. When that happens, Redis must decide **which keys should be removed** to make room for new ones.

This process is known as **Cache Eviction**.

Choosing the correct eviction strategy is one of the most important decisions when designing a caching architecture because it directly affects:

- Cache hit ratio
- Memory utilization
- Application latency
- Database load
- Overall system performance

A poor eviction strategy can significantly reduce cache effectiveness, while the right strategy can dramatically improve application performance.

---

# Why Eviction is Needed

Imagine Redis has 8 GB of RAM.

```
Application

↓

Redis Memory

↓

7.9 GB Used

↓

New Object Arrives

↓

Memory Full
```

Redis must remove existing data before storing the new object.

Without an eviction strategy:

```
SET product:5000

↓

ERROR

↓

OOM Command Not Allowed
```

The write fails.

---

# How Redis Eviction Works

```
New Write

↓

Enough Memory?

├── Yes

│      ↓

│   Store Key

│

└── No

       ↓

Eviction Policy

↓

Remove Keys

↓

Store New Key
```

Redis evaluates the configured policy whenever memory is exhausted.

---

# maxmemory Configuration

Redis begins eviction only after reaching the configured **maxmemory** value.

Example

```conf
maxmemory 8gb
```

When usage exceeds 8 GB:

```
Redis

↓

Eviction Policy

↓

Remove Keys
```

---

# Eviction Policies

Redis supports multiple eviction strategies.

| Policy | Description |
|---------|-------------|
| noeviction | Reject new writes |
| allkeys-lru | Remove least recently used keys |
| volatile-lru | Remove least recently used keys with TTL |
| allkeys-lfu | Remove least frequently used keys |
| volatile-lfu | Remove least frequently used keys with TTL |
| allkeys-random | Remove random keys |
| volatile-random | Remove random TTL keys |
| volatile-ttl | Remove keys closest to expiration |

Each policy serves different workloads.

---

# 1. noeviction

This is the safest policy for systems where losing cached data is unacceptable.

```
Memory Full

↓

Reject New Writes
```

Example

```
SET user:100

↓

OOM Error
```

Advantages

- No data removed
- Predictable behavior

Disadvantages

- Applications receive write failures
- Cache stops accepting new entries

Suitable for:

- Persistent Redis databases
- Message queues
- Critical application state

---

# 2. allkeys-lru

**Least Recently Used (LRU)** removes keys that have not been accessed recently.

```
Keys

↓

A

B

C

D

↓

Least Recently Used

↓

Removed
```

Example timeline

```
10:00 Read A

10:05 Read B

10:10 Read C

10:20 Write D

↓

Memory Full

↓

A Evicted
```

Advantages

- Excellent cache hit ratio
- Popular data remains cached
- Ideal for general caching

Disadvantages

- Recently used does not always mean frequently used

Most commonly used Redis policy.

---

# 3. volatile-lru

Similar to LRU but only considers keys that have an expiration time.

```
TTL Keys

↓

LRU

↓

Evict
```

Keys without TTL are protected.

Suitable when:

- Permanent keys must never disappear
- Only temporary cache entries should be removed

---

# 4. allkeys-lfu

**Least Frequently Used (LFU)** removes keys accessed the fewest number of times.

```
Product A

500 Reads

↓

Keep

Product B

3 Reads

↓

Evict
```

LFU focuses on popularity rather than recency.

---

# Example

```
Key A

1000 Reads

↓

Keep

Key B

2 Reads

↓

Evict
```

A popular object remains cached even if it hasn't been accessed recently.

---

# Advantages

- Excellent for long-term popularity
- Better for recommendation systems
- Stable cache hit ratio

Disadvantages

- Slightly more bookkeeping than LRU

---

# 5. volatile-lfu

LFU only considers keys with expiration.

```
TTL Keys

↓

LFU

↓

Evict
```

Permanent keys remain untouched.

---

# 6. allkeys-random

Redis randomly removes any key.

```
A

B

C

D

↓

Random

↓

B Removed
```

Advantages

- Very fast
- Minimal overhead

Disadvantages

- Poor cache efficiency
- Frequently used keys may disappear

Rarely recommended.

---

# 7. volatile-random

Random eviction only among keys with TTL.

```
TTL Keys

↓

Random

↓

Evict
```

---

# 8. volatile-ttl

Redis removes keys closest to expiration.

Example

```
Key A

10 Seconds

↓

Evict

Key B

2 Hours

↓

Keep
```

Useful when expiration naturally reflects business value.

---

# LRU vs LFU

Suppose two products.

```
Product A

1000 Views Yesterday

No Views Today

Product B

5 Views Every Minute
```

### LRU

Recently viewed items stay longer.

### LFU

Frequently viewed items stay longer.

---

Comparison

| Metric | LRU | LFU |
|---------|-----|-----|
| Uses Recency | ✅ | ❌ |
| Uses Frequency | ❌ | ✅ |
| Better for Trending Content | ✅ | ❌ |
| Better for Stable Popular Content | ❌ | ✅ |

---

# Redis LRU Approximation

Redis does **not** implement a true LRU.

Instead, it uses an approximation.

```
Random Sample

↓

Compare Access Time

↓

Evict Oldest
```

Advantages

- Lower CPU usage
- Faster decisions
- Minimal overhead

Accuracy is extremely high in practice.

---

# Redis LFU Approximation

Redis LFU also uses probabilistic counters.

```
Access

↓

Counter

↓

Decay

↓

Popularity Score
```

Benefits

- Small memory footprint
- Long-term popularity tracking

---

# Choosing an Eviction Policy

## API Responses

Recommended

```
allkeys-lru
```

Recently requested responses remain cached.

---

## Product Catalog

Recommended

```
allkeys-lfu
```

Popular products remain available.

---

## User Sessions

Recommended

```
volatile-lru
```

Expired sessions disappear naturally.

---

## Feature Flags

Recommended

```
volatile-ttl
```

Flags close to expiration are removed first.

---

## Persistent Data

Recommended

```
noeviction
```

Never remove stored data.

---

# Memory Lifecycle

```
Redis

↓

Memory Grows

↓

Limit Reached

↓

Eviction Policy

↓

Old Keys Removed

↓

New Keys Stored
```

---

# Monitoring Evictions

Useful Redis metrics

```
INFO stats
```

Important values

```
evicted_keys

keyspace_hits

keyspace_misses

used_memory

maxmemory
```

These metrics help evaluate cache effectiveness.

---

# Production Example

E-commerce site

```
Redis

↓

8 GB

↓

Product Cache

↓

Memory Full

↓

LFU

↓

Least Popular Products Removed

↓

New Products Cached
```

Frequently purchased products remain in memory.

---

# Real-World Use Cases

### News Website

```
Latest Articles

↓

LRU
```

Recent articles remain cached.

---

### Streaming Platform

```
Popular Movies

↓

LFU
```

Popular content stays longer.

---

### Social Media

```
Trending Posts

↓

LRU
```

Recent trends remain available.

---

### IoT Platform

```
Recent Sensor Data

↓

TTL

↓

Volatile LRU
```

---

# Common Mistakes

## Using noeviction for a Cache

```
Memory Full

↓

Writes Fail

↓

Application Errors
```

Use only when write failures are acceptable.

---

## No TTL

Without TTL

```
Keys

↓

Never Expire

↓

Memory Full
```

Evictions become less effective.

---

## Wrong Policy

Using Random

```
Popular Keys

↓

Randomly Removed
```

Cache hit ratio decreases significantly.

---

## Ignoring Monitoring

Never assume the policy is working well.

Track:

- Hit ratio
- Eviction count
- Memory usage
- Latency

---

# Best Practices

- Set an appropriate `maxmemory` limit based on available system RAM.
- Choose an eviction policy that matches the application's access pattern.
- Use TTLs for temporary cache entries.
- Monitor eviction rate, hit ratio, and memory fragmentation.
- Avoid caching extremely large objects.
- Group related cache keys using consistent naming conventions.
- Periodically review memory usage as traffic patterns evolve.

---

# Performance Considerations

| Policy | Performance | Typical Use Case |
|---------|-------------|------------------|
| noeviction | Excellent | Persistent storage |
| allkeys-lru | Excellent | General caching |
| volatile-lru | Excellent | Session caching |
| allkeys-lfu | Excellent | Product catalogs |
| volatile-lfu | Excellent | Popular TTL data |
| allkeys-random | Good | Rarely used |
| volatile-random | Good | Special workloads |
| volatile-ttl | Good | Expiring datasets |

---

# Production Considerations

For production deployments:

- Configure `maxmemory` conservatively to leave RAM for the operating system and Redis overhead.
- Prefer **allkeys-lru** for most web applications with unpredictable access patterns.
- Consider **allkeys-lfu** when long-term popularity matters more than recent activity.
- Monitor `evicted_keys`, `keyspace_hits`, and `keyspace_misses` continuously.
- Review eviction behavior after traffic spikes or major application releases.
- Avoid relying on eviction as the only memory management mechanism—combine it with sensible TTLs.
- Test different policies under production-like workloads before deployment.

---

# Decision Guide

| Scenario | Recommended Policy |
|----------|--------------------|
| REST API Cache | allkeys-lru |
| Product Catalog | allkeys-lfu |
| User Sessions | volatile-lru |
| Feature Flags | volatile-ttl |
| Persistent Redis Database | noeviction |
| Analytics Cache | allkeys-lfu |
| News Website | allkeys-lru |
| General Web Application | allkeys-lru |

---

# Summary

Cache eviction is a fundamental part of Redis memory management. When Redis reaches its configured memory limit, eviction policies determine which keys should be removed to make room for new data. Policies such as **LRU** and **LFU** optimize cache efficiency by preserving valuable entries based on recency or popularity, while policies like **noeviction** prioritize data retention over availability. Selecting the correct eviction strategy, combined with proper TTL configuration and continuous monitoring, is essential for maintaining high cache hit ratios and predictable application performance.

---

# Key Takeaways

- Redis evicts keys only after reaching the configured `maxmemory` limit.
- **LRU** removes the least recently used keys, while **LFU** removes the least frequently used ones.
- `allkeys-lru` is the most common choice for general-purpose web application caching.
- `allkeys-lfu` is well suited for workloads with stable popularity patterns.
- `noeviction` rejects writes instead of removing data and is best for persistent Redis deployments.
- Combine eviction policies with appropriate TTL values for optimal memory management.
- Monitor hit ratio, eviction count, and memory usage to evaluate cache effectiveness.
- Always validate eviction policies under realistic production traffic before deployment.