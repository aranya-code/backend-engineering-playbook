# Redis vs. Memcached

Amazon ElastiCache supports two open-source in-memory engines: **Redis** and **Memcached**. While both operate in-memory to provide sub-millisecond latencies, they are architecturally different and serve distinct engineering requirements.

Understanding these structural differences and their performance characteristics is critical for making database caching decisions.

---

# Memcached: Simple and Multi-Threaded

Memcached is a high-performance, distributed memory object caching system designed for simplicity and speed.

- **Data Model**: Simple key-value store. Keys are strings, and values are arbitrary data (up to 1 MB). There is no understanding of data structures.
- **Multithreading**: Memcached utilizes a **multi-threaded architecture**. It can scale vertically to utilize all CPU cores on a large instance class, making it extremely efficient for raw, high-throughput caching.
- **No Replication**: Memcached instances run as independent nodes. There is no built-in master-replica replication. If a node fails, the data on that node is lost (cache cold start).
- **No Persistence**: Data is stored purely in volatile memory. There is no snapshot or write-ahead logging.
- **Use Case**: Simple key-value caching, session stores, and scenarios where caching can be completely lost without affecting application logic (beyond database database load).

---

# Redis: Advanced and Feature-Rich

Redis (Remote Dictionary Server) is an in-memory data store that can function as a database, cache, message broker, and streaming engine.

- **Data Model**: Supports rich data structures (Strings, Hashes, Lists, Sets, Sorted Sets, Bitmaps, HyperLogLogs, Geospatial indexes). Redis understands and manipulates these data structures natively.
- **Execution Model**: Historically **single-threaded** for command execution. This guarantees atomic operations (no race conditions inside the engine). Modern Redis (v6+) uses multi-threading for network I/O, but command execution remains single-threaded.
- **Replication**: Supports master-replica replication. Writes are sent to a master node, which replicates data asynchronously to one or more read replicas.
- **High Availability**: Supported via Redis Sentinel or Redis Cluster (automatic failover, cluster sharding).
- **Persistence**: Supports data persistence to disk using RDB snapshots (periodic dumps) and AOF (Append-Only File logs).
- **Pub/Sub**: Built-in support for message publishing and subscription.
- **Lua Scripting**: Allows executing custom logic atomically on the database engine.

---

# Side-by-Side Comparison

| Feature | Memcached | Redis |
|---------|-----------|-------|
| **Primary Focus** | Simplicity and raw speed | Advanced data structures and persistence |
| **Data Types** | Strings only (up to 1 MB) | Strings, Lists, Sets, Hashes, Sorted Sets (up to 512 MB) |
| **Architecture** | Multi-threaded | Single-threaded command execution |
| **High Availability** | No (relies on client-side hashing) | Yes (Redis Sentinel, Redis Cluster) |
| **Persistence** | No | Yes (RDB and AOF) |
| **Replication** | No | Yes (Master-Replica) |
| **Pub/Sub** | No | Yes |
| **Lua Scripting** | No | Yes |
| **Scaling** | Horizontal (add nodes to pool) | Horizontal (sharding) & Vertical |

---

# Selection Guide: When to Choose Which

```text
Decision Flow:

Need advanced data types (Lists, Sets, Sorted Sets)?
       ├── YES ──► Choose Redis
       └── NO
            │
Need high availability / automatic failover / persistence?
       ├── YES ──► Choose Redis
       └── NO
            │
Workload is strictly simple key-value and needs multi-threaded CPU scaling?
       ├── YES ──► Choose Memcached
       └── NO  ──► Choose Redis (Default recommendation)
```

## Choose Memcached When:
- You are caching simple HTML fragments, database query results, or session tokens.
- You require multi-threaded scaling to handle millions of operations per second on large, single-node configurations.
- The cache is completely transient, and node replacement does not risk database overload.

## Choose Redis When:
- You need data sorting (Sorted Sets for leaderboards), sets (uniqueness), or hashes.
- High Availability is mandatory (Multi-AZ with automatic failover).
- You want the cache to persist across reboots.
- You need geospatial indexing, pub/sub messaging, or transaction execution via Lua scripts.

---

# Key Takeaways

- **Memcached** is multi-threaded, simple, and volatile — best for high-throughput, raw key-value caching.
- **Redis** is single-threaded (for commands), supports rich data types, replication, HA, and persistence.
- Redis is the industry default for most modern application architectures due to its feature set.
- Memcached scales vertically using multiple threads; Redis scales horizontally using clustering and sharding.

---
