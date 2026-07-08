# Cache Failure Scenarios and Mitigations

Caching introduces operational risks to application architectures. If the cache layer behaves unexpectedly or fails, backend databases can be suddenly overwhelmed by query traffic, leading to database outages.

Understanding the mechanics of **Cache Stampede**, **Cache Penetration**, and **Cache Avalanche**, and implementing engineering mitigations, is essential for building resilient systems.

---

# 1. Cache Stampede (Thundering Herd)

A Cache Stampede occurs when a highly popular key (e.g., home page feed, global configuration) expires, and thousands of concurrent application instances detect the cache miss at the same time. All instances attempt to fetch the data from the database and write it to the cache simultaneously.

```text
               Cache Key Expired (Cache Miss)
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
Application (1)         Application (2)         Application (N)
     │                       │                       │
     ▼                       ▼                       ▼
  Query DB                Query DB                Query DB
     │                       │                       │
     └───────────────────────┬───────────────────────┘
                             ▼
              Database Saturated / Outage ✗
```

## Mitigations

### Mutual Exclusion (Mutex/Locking)
Use a distributed lock (e.g., Redis lock via Redlock or a simple `SETNX` key) so that only the first application instance to detect the miss can query the database. Other instances wait or return a slightly stale result while the lock owner updates the cache.

### Probabilistic Early Expiration (XFetch)
The application occasionally recalculates and updates the cached value *before* it officially expires. The probability of early recalculation increases as the key approaches its expiration time.

### Background Pre-fetching
Set background worker processes to query the database and update the cache at regular intervals, ensuring the cache is never read-empty and never naturally expires for users.

---

# 2. Cache Penetration

Cache Penetration occurs when requests are made for data that does not exist in **either the cache or the database** (e.g., malicious requests looking for non-existent user IDs). Since the data never exists, every request results in a cache miss and queries the database, bypassing the cache entirely.

```text
Request for non-existent ID "999"
       │
       ▼
┌──────────────┐
│ Check Cache  ├────── Miss ──────┐
└──────────────┘                  │
                                  ▼
                            ┌──────────┐
                            │ Query DB ├─► Data not found!
                            └──────────┘
```

## Mitigations

### Caching Null/Empty Results
When a query returns "no data," write an empty or dummy value (e.g., `{"status": "not_found"}`) to the cache with a short TTL (e.g., 5 minutes). Subsequent requests for the same ID will result in a cache hit containing the null value, protecting the database.

### Bloom Filters
Use a Bloom Filter (a space-efficient probabilistic data structure) in front of the cache. The Bloom Filter can quickly verify if an ID definitely does *not* exist in the system. If it does not exist, the application rejects the request immediately without checking the cache or database.

---

# 3. Cache Avalanche

A Cache Avalanche occurs when a massive number of cached keys expire at the **exact same time**, or when the cache cluster crashes entirely, causing all subsequent reads to hit the backend database simultaneously.

```text
       All Cache Keys Expire simultaneously OR Cache Crashes
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
     Read Query              Read Query              Read Query
         │                       │                       │
         ▼                       ▼                       ▼
    Cache Miss              Cache Miss              Cache Miss
         │                       │                       │
         └───────────────────────┬───────────────────────┘
                                 ▼
                     Primary Database Crashes ✗
```

## Mitigations

### Randomize TTLs (Jitter)
Avoid setting the exact same TTL (e.g., exactly 24 hours) for large batches of data. Add a small, randomized offset (jitter) to the expiration time (e.g., `24 hours + rand(1 to 30 minutes)`) to spread expiration events evenly over time.

### High Availability (Clustering)
Deploy ElastiCache with Multi-AZ replication and Cluster Mode Enabled to ensure that if a single node fails, automatic failover occurs with minimal data loss, preventing complete cache unavailability.

### Circuit Breakers & Rate Limiting
Implement circuit breakers (e.g., Resilience4j) in the application. If the database latency spikes due to cache failure, the circuit breaker opens, returning cached default or fallback data instead of continuing to query the database.

---

# 4. Cache Warmup

When launching a new application version or restoring a failed cache, the cache is completely empty ("cold"). Sending production traffic to a cold cache can trigger immediate database saturation.

- **Warmup Process**: Pre-populate the cache with popular or critical data *before* directing user traffic to the application.
- **Implementation**: Run a script during deployment to query the database for the top 10% most active records and write them to the cache.

---

# Key Takeaways

- **Cache Stampede** is caused by popular key expiration; mitigate using locks/mutex or background pre-fetching.
- **Cache Penetration** occurs when querying non-existent data; mitigate by caching null values or using Bloom Filters.
- **Cache Avalanche** is a mass expiration event; mitigate by adding **jitter** (randomized offsets) to TTLs and using HA cluster architectures.
- Always perform a **Cache Warmup** before routing production traffic to a newly deployed or recovered cache cluster.

---
