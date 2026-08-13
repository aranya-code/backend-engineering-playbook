# Redis vs Memcached

Both are in-memory key-value stores. Both deliver sub-millisecond latency. But the similarities end there. Redis is a data structure server with persistence, replication, and programmability. Memcached is a distributed memory cache — fast, simple, and deliberately featureless. Your choice depends on whether you need a cache or a data platform.

---

## Threading Model

This is the most misunderstood difference.

**Redis** executes commands in a single-threaded event loop. One CPU core processes all commands sequentially. This guarantees atomicity of individual commands without locks but caps throughput per instance at what one core can deliver. Redis 6.x+ added I/O threads for network read/write, but command execution remains single-threaded. You scale Redis horizontally with sharding (Redis Cluster) or read replicas.

**Memcached** is multi-threaded from the ground up. It uses a worker thread pool to process requests concurrently across all available CPU cores on a single node. For simple GET/SET workloads on large multi-core instances, Memcached can deliver significantly higher throughput per node.

```
┌──────────────────────────────────────────────────────────┐
│              THREADING MODEL COMPARISON                  │
├──────────────────────────┬───────────────────────────────┤
│         Redis            │        Memcached              │
├──────────────────────────┼───────────────────────────────┤
│                          │                               │
│  Client ──► I/O Thread   │  Client ──► Worker Thread 1   │
│              │            │  Client ──► Worker Thread 2   │
│              ▼            │  Client ──► Worker Thread 3   │
│      ┌─────────────┐     │  Client ──► Worker Thread 4   │
│      │ Single-Thread│     │              │ │ │ │          │
│      │  Event Loop  │     │              ▼ ▼ ▼ ▼          │
│      │  (commands)  │     │      ┌──────────────────┐    │
│      └─────────────┘     │      │  Shared Hash Map  │    │
│              │            │      │   (lock-based)    │    │
│              ▼            │      └──────────────────┘    │
│  Client ◄── I/O Thread   │                               │
│                          │  All cores utilized            │
│  One core for commands   │  Higher raw throughput/node    │
└──────────────────────────┴───────────────────────────────┘
```

---

## Data Structures

| Structure | Redis | Memcached |
|---|---|---|
| **Strings** | ✅ (up to 512 MB) | ✅ (up to 1 MB default) |
| **Lists** | ✅ (linked lists, blocking pops) | ❌ |
| **Sets** | ✅ (union, intersect, diff) | ❌ |
| **Sorted Sets** | ✅ (leaderboards, range queries) | ❌ |
| **Hashes** | ✅ (field-level ops, partial updates) | ❌ |
| **Streams** | ✅ (append-only log, consumer groups) | ❌ |
| **HyperLogLog** | ✅ (cardinality estimation) | ❌ |
| **Bitmaps** | ✅ (bit-level operations) | ❌ |
| **Geospatial** | ✅ (GEOADD, GEORADIUS) | ❌ |

Redis's rich data structures let you push logic to the cache layer. Leaderboards with Sorted Sets, rate limiting with INCR + EXPIRE, session stores with Hashes, message queues with Lists or Streams — all server-side, all atomic.

Memcached stores opaque byte blobs. Your application serializes, deserializes, and handles all logic.

---

## Persistence

**Redis** offers two persistence mechanisms:
- **RDB (Redis Database)** — point-in-time snapshots at configurable intervals. Fast restarts, but data loss between snapshots.
- **AOF (Append-Only File)** — logs every write operation. Configurable fsync policy (always, every second, never). Slower restarts but minimal data loss.
- You can run both simultaneously for durability + fast recovery.

**Memcached** has no persistence. Process restarts = total data loss. This is by design — Memcached is a pure volatile cache. If your cache goes cold, your database eats the thundering herd.

---

## Replication and High Availability

| Capability | Redis | Memcached |
|---|---|---|
| **Replication** | Master-replica async replication | None (no native replication) |
| **Failover** | Redis Sentinel (automatic promotion) | None (client handles) |
| **Sharding** | Redis Cluster (hash slots, 16384) | Client-side consistent hashing |
| **Cross-AZ** | ElastiCache Multi-AZ with auto-failover | ElastiCache distributes nodes across AZs |
| **Read scaling** | Read from replicas | Add more nodes to pool |

Redis Sentinel monitors masters, detects failures, and promotes replicas automatically. Redis Cluster distributes data across shards using hash slots, providing both HA and horizontal scaling.

Memcached relies entirely on the client library for distribution. If a node dies, its keys are lost and requests go to the origin database until the client remaps.

---

## Advanced Features

**Pub/Sub** — Redis natively supports publish/subscribe messaging. Lightweight, fire-and-forget. No persistence of messages (subscribers must be connected). Useful for real-time notifications, cache invalidation broadcasts.

**Lua Scripting** — Execute atomic server-side scripts with `EVAL`. Complex operations run atomically without round-trip overhead. Rate limiting, conditional updates, multi-key transactions — all in a single atomic call.

**Transactions** — `MULTI`/`EXEC` groups commands into atomic batches. Not true transactions (no rollback), but guarantees sequential execution without interleaving.

**TTL Management** — Both support per-key TTL. Redis adds `EXPIREAT`, `PERSIST`, and TTL inspection. Memcached supports TTL at SET time only.

---

## Detailed Comparison Table

| Feature | Redis | Memcached |
|---|---|---|
| **Data types** | Strings, Lists, Sets, Sorted Sets, Hashes, Streams, HyperLogLog, Bitmaps, Geo | Strings/blobs only |
| **Max value size** | 512 MB | 1 MB (default) |
| **Threading** | Single-threaded commands (I/O threads in 6.x+) | Multi-threaded |
| **Persistence** | RDB snapshots + AOF | None |
| **Replication** | Master-replica (async) | None |
| **High availability** | Sentinel + Cluster | Client-side only |
| **Pub/Sub** | Native | Not supported |
| **Scripting** | Lua (EVAL) | Not supported |
| **Transactions** | MULTI/EXEC | CAS (compare-and-swap) |
| **Cluster mode** | Hash slot sharding (16384 slots) | Client-side consistent hashing |
| **Memory efficiency** | Higher per-key overhead (metadata) | Lower per-key overhead |
| **Eviction policies** | 8 policies (LRU, LFU, random, volatile, allkeys) | LRU only |
| **AWS service** | ElastiCache for Redis, MemoryDB | ElastiCache for Memcached |
| **Backup/restore** | Snapshot to S3 | Not available |

---

## Decision Tree

```
Need caching?
│
├── Need rich data structures (Sets, Sorted Sets, Hashes, Streams)?
│   └── YES ──► Redis
│
├── Need persistence or replication?
│   └── YES ──► Redis
│
├── Need Pub/Sub or Lua scripting?
│   └── YES ──► Redis
│
├── Need automatic failover and HA?
│   └── YES ──► Redis (Sentinel/Cluster)
│
├── Need maximum multi-threaded throughput for simple GET/SET?
│   └── YES ──► Memcached (especially on large multi-core instances)
│
├── Need simplest possible cache with lowest memory overhead?
│   └── YES ──► Memcached
│
└── Unsure?
    └── Default to Redis (superset of Memcached features)
```

---

## When Memcached Wins

Memcached is the right choice in these specific scenarios:
- **Pure multi-threaded throughput** — simple key-value workloads on large instances where Memcached's multi-threaded architecture saturates all CPU cores
- **Lower memory overhead** — Memcached uses less memory per key (no metadata for data structure support), better for very large numbers of small keys
- **Simplicity** — no replication, no persistence, no cluster management. Just a hash table in memory. Easier to reason about and operate
- **Existing Memcached ecosystem** — legacy applications with established Memcached client libraries and operational tooling

In every other scenario, Redis is the better choice due to its feature breadth.

---

## Interview-Ready Explanation

> "Redis and Memcached are both sub-millisecond in-memory stores, but they serve different purposes. Redis is a data structure server — it supports Lists, Sets, Sorted Sets, Hashes, Streams, persistence, replication, Pub/Sub, and Lua scripting. Memcached is a pure multi-threaded cache for simple key-value lookups. I default to Redis because it's a superset of Memcached's capabilities. The only scenario where I'd pick Memcached is when I need maximum multi-threaded throughput for simple GET/SET operations on large instances and I don't need any of Redis's advanced features."

---

## Key Takeaways

- **Default to Redis** — it does everything Memcached does and more
- Redis's single-threaded command execution is rarely a bottleneck; scale with Cluster mode or read replicas
- Memcached wins only on raw multi-threaded throughput for simple key-value patterns
- Redis data structures (Sorted Sets, Streams, HyperLogLog) enable server-side logic that eliminates application complexity
- Redis persistence (RDB + AOF) provides warm restarts; Memcached cold-starts from zero
- On AWS, ElastiCache supports both; MemoryDB is Redis-compatible only — further validating Redis as the default
