# ElastiCache Overview and Caching Patterns

Amazon ElastiCache is a fully managed in-memory caching service that supports the Redis and Memcached engines. By storing frequently accessed data in memory, ElastiCache reduces database load, accelerates application performance, and delivers sub-millisecond query response times at scale.

Implementing caching effectively requires choosing the correct caching patterns based on read/write frequency and data consistency requirements.

---

# Caching Fundamentals: Hit vs. Miss

- **Cache Hit**: The requested data is found in the cache. The application returns the data immediately, bypassing the primary database.
- **Cache Miss**: The requested data is not found in the cache. The application must query the primary database, return the data to the client, and optionally write the data to the cache for future requests.
- **Cache Hit Ratio**: The percentage of database read requests successfully served by the cache. A low hit ratio indicates suboptimal key selection, short Time-To-Live (TTL) values, or cache eviction.

```text
Query Request
      │
      ▼
┌──────────────┐
│ Check Cache  ├────── Hit ──────► Return Data immediately
└──────┬───────┘
       │
      Miss
       │
       ▼
┌──────────────┐
│ Query DB     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Write Cache  │
└──────┬───────┘
       │
       ▼
  Return Data
```

---

# Caching Patterns

There are four primary patterns for loading data into and maintaining a cache:

## 1. Cache-Aside (Lazy Loading) - Recommended for general use

The application interacts with both the cache and the database. Data is only written to the cache when a cache miss occurs.

- **Write Path**: Data is written directly to the database. The cache is either updated or the corresponding key is deleted (invalidated) to prevent stale data.
- **Read Path**: The application checks the cache. On a miss, it queries the database and writes the returned data to the cache.
- **Pros**:
  - The cache only contains data that is actively being read (no memory wasted on unused data).
  - Cache failure is non-fatal (the application falls back to querying the database).
- **Cons**:
  - Cache misses incur double queries (checks cache, then queries DB, then writes to cache).
  - Risk of stale data if the database is updated directly without invalidating the cache.

---

## 2. Write-Through

The database and cache are updated simultaneously on every write operation.

- **Write Path**: The application writes to the cache. The caching layer (or application) writes directly to the database. The write transaction completes only when both are updated.
- **Read Path**: The application reads from the cache. Since data is pre-populated on write, cache hits are maximized.
- **Pros**:
  - Data in the cache is never stale.
  - Read performance is consistently fast.
- **Cons**:
  - High write latency (writes must succeed in both memory and disk).
  - Wasted memory if written data is rarely read (mitigated by setting a low TTL).

```text
Write-Through:
Application ──► Write Cache ──► Write DB ──► Acknowledge Write

Write-Back:
Application ──► Write Cache ──► Acknowledge Write (Immediate)
                     │
            (Asynchronous Batch)
                     ▼
                  Write DB
```

---

## 3. Write-Back (Write-Behind)

Writes are written directly to the cache, which acknowledges the write immediately. The cache then writes the data asynchronously to the database in batches.

- **Pros**:
  - Extremely fast write performance (sub-millisecond latency).
  - database write spikes are smoothed out through batching.
- **Cons**:
  - Risk of data loss: If the cache crashes before the data is flushed to the database, the data is permanently lost.
  - Complex implementation and synchronization management.

---

## 4. Read-Through

Similar to Cache-Aside, but the application only interacts with the cache. On a cache miss, the cache provider library itself queries the database, updates the cache, and returns the data to the application.

---

# Caching Pattern Decision Matrix

| Pattern | Write Latency | Read Latency | Data Consistency | Risk |
|---------|---------------|--------------|------------------|------|
| **Cache-Aside** | Low | Low (on hit) | Eventually Consistent | Stale data if not invalidated |
| **Write-Through**| High | Low | Strongly Consistent | Write overhead |
| **Write-Back** | Very Low | Low | Eventually Consistent | **Data Loss** on cache crash |

---

# Key Takeaways

- **Cache-Aside** is the most common and robust caching pattern, keeping the cache clean by storing only active data.
- **Write-Through** avoids stale data but incurs write latency overhead.
- **Write-Back** provides maximum write performance but introduces data loss risks.
- Always implement a **Time-To-Live (TTL)** on cached data to limit the lifespan of stale data.

---
