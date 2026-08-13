# Interview Questions: Caching and Performance

This section provides detailed, senior-level interview questions and model answers focusing on database caching strategies, performance tuning, and scaling caches on AWS.

---

# Caching Strategies and Resiliency

## Q1: How do you choose between Cache-Aside and Write-Through caching patterns?

The choice depends on data consistency needs, write/read frequencies, and latency tolerances.

- **Cache-Aside (Lazy Loading)**:
  - **Mechanics**: Application checks the cache; on a miss, queries the database, returns data, and writes to the cache. Writes go directly to the database.
  - **Choose When**: Workload is read-heavy but writes are infrequent, or when cached data is not accessed immediately.
  - **Trade-off**: Cache misses incur double queries. Data can become stale if not explicitly invalidated on database updates.
- **Write-Through**:
  - **Mechanics**: Application writes to the cache, which writes to the database immediately. The write transaction completes when both are updated.
  - **Choose When**: Data consistency is critical, or when cached data is read immediately after writing.
  - **Trade-off**: Higher write latency because writes must succeed in both locations before returning.

---

## Q2: How do you mitigate a Cache Stampede (Thundering Herd) in a high-traffic application?

A Cache Stampede occurs when a popular key expires, and thousands of concurrent requests attempt to fetch data from the database at the same time, saturating the database.

- **Mitigations**:
  - **Mutual Exclusion (Distributed Locks)**: Use a lock (e.g., Redis `SETNX` or Redlock) so that only the first request to detect the cache miss is allowed to query the database. Other requests wait or return slightly stale data while the cache is being updated.
  - **Background Pre-fetching**: Run background worker processes to query the database and update the cache at regular intervals *before* keys naturally expire, ensuring the cache is never empty for incoming requests.
  - **Probabilistic Early Expiration**: Use the XFetch algorithm to allow applications to asynchronously recalculate and refresh the cache key as it approaches its expiration time.

---

## Q3: What is the difference between Cache Penetration and Cache Avalanche? How do you prevent them?

- **Cache Penetration**:
  - **Definition**: Requests are made for keys that do not exist in the cache *or* database (e.g., checking for invalid user IDs). Every request results in a cache miss and queries the database.
  - **Mitigation**: 
    1. **Cache Null Results**: Write a dummy or empty value (e.g., `{"status": "not_found"}`) to the cache with a short TTL.
    2. **Bloom Filters**: Place a Bloom filter in front of the cache to quickly verify if an ID exists in the database. If not, reject the request immediately.
- **Cache Avalanche**:
  - **Definition**: A large number of cached keys expire at the exact same time, or the cache cluster crashes, routing all query traffic to the database simultaneously.
  - **Mitigation**:
    1. **Randomize TTL (Jitter)**: Add a small, random time offset (jitter) to cache TTLs (e.g., `24 hours + rand(1-15 minutes)`) to spread out expiration events.
    2. **High Availability**: Deploy ElastiCache in Multi-AZ mode with auto-failover.
    3. **Circuit Breakers**: Use circuit breakers to return fallback data if database query latency spikes.

---

# Caching Performance Tuning

## Q4: Why is host CPU utilization (CPUUtilization) a misleading metric for Redis? What should you monitor instead?

Redis is historically a single-threaded execution engine. All database commands run on a single thread.

- **The Problem**: On a multi-core host (e.g., 4 vCPUs), if the single Redis engine thread is running at 100% capacity, the host-level `CPUUtilization` metric will report only **25%** (100% / 4 cores). If you set CPU alerts at 80% on host utilization, the alert will never trigger, even though the database is completely saturated.
- **The Solution**: Monitor **`EngineCPUUtilization`** in CloudWatch. This metric measures the CPU utilization of the specific thread running the Redis database engine. Always set performance alerts on `EngineCPUUtilization` at 80%.

```text
Core 1: Redis Engine Thread ──────► 100% (Saturated)
Core 2: Idle ──────────────────────► 0%
Core 3: Idle ──────────────────────► 0%
Core 4: Idle ──────────────────────► 0%

Average Host CPUUtilization = 25% (Misleading!)
EngineCPUUtilization = 100% (Accurate!)
```

---

## Q5: How do you configure Amazon ElastiCache to prevent OOM crashes during backups?

During background operations (taking snapshots, syncing replicas), Redis forks a background process to write memory pages to disk using the operating system's Copy-on-Write (CoW) mechanism. If write traffic is high during a fork, the memory usage can double. If no memory is reserved, the OS will trigger an Out-Of-Memory (OOM) crash.

- **Mitigation**: Configure **`reserved-memory-percent`** to **25%** in your custom parameter groups. This reserves 25% of the database memory for background processes, ensuring the Redis process has enough overhead to complete snapshots and failovers without crashing.
- **Related Metric**: Monitor **`SwapUsage`** in CloudWatch. If swap space is actively being used, it indicates the cache is out of physical memory and is swapping data to disk, causing latency to spike.

---
