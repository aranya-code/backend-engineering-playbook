# Best Practices and MemoryDB

In-memory data stores can be used as transient caching layers or as primary, durable databases. AWS provides two distinct options for Redis: **Amazon ElastiCache for Redis** (optimized for speed and low cost) and **Amazon MemoryDB for Redis** (optimized for durability and transactional consistency).

Understanding the trade-offs between these services and configuring memory reserves correctly is essential for running reliable production systems.

---

# ElastiCache Redis vs. Amazon MemoryDB

While both services are Redis-compatible, they utilize fundamentally different storage architectures.

```text
ElastiCache Redis (Cache-First)
  Writes go to Primary Memory ──► Acknowledged immediately (Sub-millisecond)
         │
         ├──► Asynchronous disk snapshot (Optional RDB/AOF)
         └──► Asynchronous replication to standby nodes

MemoryDB for Redis (Database-First)
  Writes go to Multi-AZ Transaction Log (S3/SSD) ──► Wrote to Memory ──► Acknowledged
         │
         └──► Synchronous transaction durability (RPO = 0, RTO = Seconds)
```

## Amazon MemoryDB for Redis

MemoryDB is a **durable, in-memory database service**. It uses a distributed, multi-AZ transaction log to ensure that any write confirmed to the application is durably stored across multiple Availability Zones before being acknowledged.

- **Primary Database**: Designed to be used as a primary transactional database, not just a cache.
- **RPO = 0**: Guarantees zero data loss on node failure or AZ outage.
- **Performance**: Reads are sub-millisecond (served from memory). Writes have slightly higher latency than ElastiCache because they must be committed to the distributed transaction log first.
- **Cost**: Higher cost compared to ElastiCache (hourly instance charges + transactional write charges per GB).

---

# Service Comparison: ElastiCache vs. MemoryDB

| Feature | ElastiCache for Redis | MemoryDB for Redis |
|---------|-----------------------|--------------------|
| **Primary Use Case** | Volatile Caching layer | Primary Transactional Database |
| **Data Durability** | Volatile (Data loss possible on reboot/crash) | Durable (Zero data loss guarantee, RPO = 0) |
| **Write Performance** | Sub-millisecond (In-memory) | Milliseconds (Committed to transaction log first) |
| **Read Performance** | Sub-millisecond | Sub-millisecond |
| **Storage Architecture**| Volatile RAM, optional disk backup | Distributed multi-AZ transactional write log |
| **Multi-AZ Failover** | Automatic (Data loss possible on replication lag)| Automatic (No data loss, reads from log) |
| **Pricing** | Instance hours | Instance hours + Write data volume charges |

---

# ElastiCache Production Best Practices

To run ElastiCache for Redis reliably, implement the following configuration and operational practices:

## 1. Configure Memory Reserves (`reserved-memory-percent`)

By default, Redis can consume up to 100% of the instance memory. However, during background operations (such as taking snapshots, executing failovers, or syncing replicas), Redis uses a fork operation that duplicates the memory footprint (Copy-on-Write).

If no memory is reserved, the host OS may run out of memory, killing the Redis process.

- **Recommendation**: Set `reserved-memory-percent` to **25%** in your custom parameter groups. This reserves 25% of the node's memory for background processes, preventing OOM crashes during backup/restore/replication operations.

## 2. Monitor Swap Usage (`SwapUsage`)

- **What is Swap**: When physical RAM is exhausted, the OS writes memory pages to disk (Swap space) to prevent crashes.
- **Performance Impact**: Disk I/O is orders of magnitude slower than RAM. If Redis begins swapping data, query latency will spike from sub-milliseconds to seconds.
- **Action**: Set CloudWatch alarms on the `SwapUsage` metric. If swap usage exceeds 50 MB, scale up the instance class to add more RAM.

## 3. Cache Key Naming Conventions

Maintain structured, readable cache keys using colons to create namespaces:

- Format: `<environment>:<service>:<resource>:<id>`
- Example: `prod:auth:session:usr_99812`

This simplifies key debugging, wildcard deletion scripts, and prevents namespace collisions across microservices sharing a cache cluster.

---

# Key Takeaways

- **ElastiCache** is optimized for speed and cost as a volatile cache; **MemoryDB** is a durable, transactional primary database with RPO = 0.
- Writes in MemoryDB are slower than ElastiCache due to distributed log synchronization.
- Always reserve **25% of memory** (`reserved-memory-percent`) to prevent crashes during backups and failovers.
- Monitor **`SwapUsage`** in CloudWatch; swap activity degrades in-memory database performance.
- Use structured key names with namespaces (`prod:service:resource:id`) to prevent collisions.

---
