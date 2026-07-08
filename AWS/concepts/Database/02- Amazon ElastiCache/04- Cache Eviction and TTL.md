# Cache Eviction and TTL

In-memory caches operate under strict memory limits. If the cache runs out of memory, it must decide how to handle new write requests. This is controlled by **Eviction Policies** (how data is cleared when memory is full) and **TTL (Time To Live)** configurations (how data naturally expires over time).

Understanding these mechanics is essential for preventing memory exhaustion (`OOM`) errors and maintaining high cache hit ratios.

---

# Time-To-Live (TTL)

TTL defines the lifespan of a cached key. Once the TTL expires, the key is considered dead and is no longer returned to the client.

## Redis Expired Key Cleanup Mechanics

Redis does not constantly scan all keys to delete expired ones, as this would consume high CPU. Instead, it uses a combination of passive and active expiration:

- **Passive Expiration**: When a client attempts to access a key, Redis checks if the key's TTL has expired. If expired, the key is deleted and `nil` is returned (lazy expiration).
- **Active Expiration**: Periodically (10 times per second), Redis runs a randomized test:
  1. Tests 20 random keys with an associated TTL.
  2. Deletes all keys found to be expired.
  3. If more than 25% of the 20 keys are expired, it repeats the process immediately.

---

# Cache Eviction Policies

When the database memory reaches its limit (controlled by the `maxmemory` parameter), Redis executes an **Eviction Policy** to free up memory for new writes.

There are three main eviction strategies:
1. **LRU (Least Recently Used)**: Evicts keys that haven't been accessed for the longest time.
2. **LFU (Least Frequently Used)**: Evicts keys that are accessed the least number of times, regardless of when they were last accessed.
3. **TTL-Based**: Evicts keys with the shortest remaining TTL.

These strategies are configured under different namespaces in the `maxmemory-policy` parameter:

```text
               maxmemory-policy Options
               ┌───────────────────────┐
               │  Eviction Categories  │
               └───────────┬───────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
   All Keys (allkeys-*)                TTL Keys (volatile-*)
  (Checks all keys in database)       (Only checks keys with a TTL set)
  ├── allkeys-lru                     ├── volatile-lru
  ├── allkeys-lfu                     ├── volatile-lfu
  ├── allkeys-random                  ├── volatile-random
  │                                   └── volatile-ttl
  │
  └───────────► noeviction (Default)
                (Returns errors on new writes)
```

---

# Detailed Eviction Policies

## 1. noeviction (Default)

- **Behavior**: Returns out-of-memory errors (`OOM command not allowed when used memory > 'maxmemory'`) for any command that attempts to write new data. Read queries continue to function.
- **Best Use Case**: When the cache is used as a primary database (e.g., Sidekiq queues, database store) where data loss is unacceptable.

## 2. allkeys-lru - Recommended for standard caches

- **Behavior**: Evicts the least recently used keys across the entire database, regardless of whether they have an associated TTL.
- **Best Use Case**: Standard caching layers where you want to keep active keys in memory and discard cold keys automatically.

## 3. volatile-lru

- **Behavior**: Evicts the least recently used keys, but **only** among keys that have an associated TTL. If no keys have a TTL, it behaves like `noeviction`.
- **Best Use Case**: When you have mixed workloads (some persistent keys and some cached keys) and only want to evict the cached keys.

## 4. allkeys-lfu & volatile-lfu

- **Behavior**: Evicts the least frequently used keys. Uses an access counter to preserve popular keys, even if they haven't been accessed recently.
- **Best Use Case**: Preventing "cache pollution" where a sudden read spike of cold keys evicts popular warm keys under an LRU policy.

---

# Monitoring Evictions in CloudWatch

When optimizing cache memory, monitor these critical metrics:

- **Evictions**: The number of keys evicted due to reaching `maxmemory`.
  - **Healthy**: Low or steady rate of evictions matching expected cache churn.
  - **Unhealthy**: A sudden spike in evictions combined with a dropping `CacheHitRatio`, indicating "cache thrashing" (data is evicted immediately after being written because memory is too small).
- **BytesUsedForCache**: The total memory consumed.
- **FreeableMemory**: The host-level memory remaining.

## Handling Out-of-Memory Conditions

If your cache is thrashing or returning `OOM` errors:

1. **Verify Caching Policies**: Ensure keys are configured with appropriate TTLs.
2. **Change Eviction Policy**: Switch from `noeviction` to `allkeys-lru` if the data is purely transient cache.
3. **Scale Horizontally**: Add shards (if in Cluster Mode Enabled) to distribute memory load.
4. **Scale Vertically**: Upgrade the database node instance class to one with more RAM.

---

# Key Takeaways

- **TTL** naturally expires keys over time using passive (lazy) and active (sampling) expiration.
- **Eviction Policies** determine what happens when the cache reaches `maxmemory`.
- **`noeviction`** is the default policy and rejects writes when full; **`allkeys-lru`** is the recommended policy for standard caching layers.
- `volatile-*` policies only evict keys that have a TTL set, protecting persistent keys.
- Monitor the **`Evictions`** and **`CacheHitRatio`** metrics in CloudWatch to detect cache thrashing.

---
