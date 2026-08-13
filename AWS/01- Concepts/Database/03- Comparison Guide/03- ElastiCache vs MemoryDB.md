# ElastiCache vs MemoryDB

Both are AWS-managed Redis-compatible services, but they serve fundamentally different purposes. **ElastiCache is a cache.** **MemoryDB is a database.** The distinction lies in the durability guarantees of the write path and what happens when things fail.

---

## Architecture

### ElastiCache for Redis

ElastiCache is a managed in-memory cache. Data lives in RAM. Replication is asynchronous. The primary acknowledges writes as soon as they hit memory—before replication to replicas. If the primary fails before replication completes, those writes are lost.

ElastiCache supports cluster mode (sharding across hash slots) and non-cluster mode (single shard with read replicas). Backups are RDB snapshots to S3—point-in-time, not continuous.

**Design intent:** Accelerate reads from a slower primary database. The source of truth lives elsewhere (RDS, DynamoDB, etc.). Cache loss is recoverable by re-reading from the primary.

### MemoryDB for Redis

MemoryDB is a durable, Redis-compatible, in-memory database. It uses a **Multi-AZ transaction log** that durably stores every write across multiple Availability Zones before acknowledging it to the client. Data in memory is the same Redis data structure engine, but the transaction log ensures zero data loss even during full node failure.

MemoryDB can serve as a **primary database** because it provides the durability guarantees that ElastiCache cannot. It achieves microsecond read latency and single-digit millisecond write latency (the write penalty comes from the durable transaction log commit).

**Design intent:** Replace both your cache and your primary database for workloads where the data model fits Redis's API. Eliminate the cache-aside pattern entirely.

---

## Write Path Comparison

This is the critical architectural difference. How a write is acknowledged determines the durability contract.

```
ElastiCache Write Path:
┌────────┐    ┌─────────────┐    ┌─────────────┐
│ Client │───►│  Primary    │───►│  Replica    │
│        │    │  (in-memory)│    │  (async)    │
│        │◄───│  ACK ✓      │    │             │
└────────┘    └─────────────┘    └─────────────┘
     │
     │  Write ACK'd after memory write on primary.
     │  If primary crashes before async replication → DATA LOSS.
     │  RPO: Seconds of data (replication lag window).


MemoryDB Write Path:
┌────────┐    ┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│ Client │───►│  Primary    │───►│  Transaction Log  │───►│  Replica    │
│        │    │  (in-memory)│    │  (Multi-AZ durable│    │  (from log) │
│        │◄───│             │◄───│   ACK ✓)          │    │             │
└────────┘    └─────────────┘    └──────────────────┘    └─────────────┘
     │
     │  Write ACK'd ONLY after durable commit to Multi-AZ transaction log.
     │  If primary crashes → rebuild from transaction log. ZERO DATA LOSS.
     │  RPO: 0 (zero).
```

**Key insight:** ElastiCache optimizes for write speed (memory-only ACK). MemoryDB optimizes for durability (transaction log ACK). Both serve reads from memory at the same speed.

---

## Durability Deep Dive

| Scenario | ElastiCache | MemoryDB |
|----------|-------------|----------|
| Primary node failure | Failover to replica. Writes in the async replication window are lost. | Failover to replica. Transaction log replays any missing writes. Zero loss. |
| Full cluster failure | Restore from last RDB snapshot (minutes to hours old). Data between snapshots is lost. | Rebuild from transaction log. All committed writes recovered. |
| AZ failure | Multi-AZ replicas survive, but recent writes to failed primary may be lost. | Transaction log is Multi-AZ. All committed writes survive. |
| Backup/Restore | RDB snapshots to S3. Manual or scheduled. PITR not available. | Transaction log provides continuous durability. Snapshots also available. |
| **RPO** | **Seconds to minutes** (replication lag + snapshot interval) | **Zero** |
| **RTO** | **Seconds** (replica promotion) | **Seconds** (replica promotion + log replay) |

---

## Detailed Comparison Table

| Feature | ElastiCache for Redis | MemoryDB for Redis |
|---------|----------------------|-------------------|
| **Primary Use Case** | Caching layer (cache-aside, read-through) | Primary database (Redis-compatible) |
| **Durability** | Volatile; async replication, RDB snapshots | Durable; Multi-AZ transaction log |
| **Write Latency** | Microseconds (memory-only) | Single-digit milliseconds (transaction log commit) |
| **Read Latency** | Microseconds | Microseconds (reads from memory, identical to ElastiCache) |
| **RPO** | Seconds to minutes | Zero (0) |
| **Data Loss on Failover** | Possible (async replication window) | Not possible (transaction log) |
| **Redis Compatibility** | Full Redis API | Full Redis API |
| **Cluster Mode** | Supported (up to 500 shards) | Supported (up to 500 shards) |
| **Encryption** | At-rest (KMS), in-transit (TLS) | At-rest (KMS), in-transit (TLS) |
| **Snapshots** | RDB to S3 | Snapshots + continuous transaction log |
| **Multi-AZ** | Supported (async replica) | Required (transaction log is Multi-AZ by design) |
| **Pricing** | Base Redis managed pricing | ~20-25% premium over ElastiCache |
| **Node Types** | r7g, r6g, m7g, t4g, etc. | r7g, r6g, t4g (subset of ElastiCache types) |
| **Global Datastore** | Supported (cross-region replication) | Supported (cross-region replication) |
| **ACLs** | Redis 6+ ACLs | Redis 6+ ACLs |
| **Engine Versions** | Redis 5.x through 7.x | Redis 6.2 and 7.x |

---

## Pricing Comparison

MemoryDB costs approximately 20-25% more than ElastiCache for equivalent node types. But the TCO comparison must include what MemoryDB replaces.

```
Typical cache-aside architecture (ElastiCache):
├── ElastiCache cluster:        $X/month
├── RDS/DynamoDB (source of truth): $Y/month
├── Data sync complexity:        Engineering time
└── Total:                       $X + $Y + engineering overhead

MemoryDB as primary database:
├── MemoryDB cluster:            $1.2X/month (20% premium)
├── No separate database needed: $0
├── No sync logic:               $0
└── Total:                       $1.2X
```

**When the math works:** If your data model fits Redis and you're currently running ElastiCache + RDS/DynamoDB, MemoryDB can be cheaper overall because you eliminate the backing database entirely.

**When it doesn't:** If you're only caching hot keys from a large relational database, you still need the relational database. MemoryDB's premium buys durability you don't need for ephemeral cache data.

---

## When to Choose Each

### Choose ElastiCache when:

- **Caching read-heavy workloads** from a primary database (RDS, Aurora, DynamoDB). Classic cache-aside pattern.
- **Session storage** where session loss is tolerable (user re-authenticates).
- **Computed result caching** (API responses, query results, rendered pages) where the source data lives elsewhere.
- **Cost sensitivity** on the caching layer. The data is reconstructable—you're paying for speed, not durability.
- **Sub-microsecond write latency is critical.** ElastiCache's memory-only ACK is faster than MemoryDB's transaction log commit.

### Choose MemoryDB when:

- **Redis IS your primary database.** Leaderboards, session stores (where loss is unacceptable), real-time inventory, feature flags, rate limiting state.
- **You want to eliminate the cache + database pattern.** MemoryDB collapses the cache and database into one service.
- **Zero RPO is a requirement.** Financial transactions, e-commerce carts, game state—anywhere "we lost the last 5 seconds of writes" is unacceptable.
- **Event sourcing or stream processing.** Redis Streams with durable storage for consumer group state.
- **Compliance requires durable storage.** Audit trails, regulatory data that must survive infrastructure failures.

---

## Interview-Ready Explanation

> "ElastiCache and MemoryDB are both AWS-managed Redis services, but they differ fundamentally in durability. ElastiCache acknowledges writes after they hit memory on the primary—it's a cache, and data loss on failover is expected and acceptable because the source of truth lives elsewhere. MemoryDB adds a Multi-AZ transaction log: writes are only acknowledged after durable commit, giving you RPO of zero. This makes MemoryDB suitable as a primary database, not just a cache. The trade-off is write latency—single-digit milliseconds for MemoryDB versus microseconds for ElastiCache—and a 20-25% cost premium. I'd use ElastiCache for cache-aside patterns where the data is reconstructable, and MemoryDB when Redis is my system of record and I can't tolerate data loss."

---

## Key Takeaways

- **ElastiCache = cache, MemoryDB = database.** The naming tells you the intent. ElastiCache accelerates reads from a durable primary. MemoryDB *is* the durable primary.
- **The write path is the differentiator.** Memory-only ACK (ElastiCache) vs. transaction-log ACK (MemoryDB). Everything else follows from this design choice.
- **RPO zero is MemoryDB's headline feature.** If you can't afford to lose writes during failover, MemoryDB is the only Redis-compatible option on AWS.
- **Read latency is identical.** Both serve reads from in-memory Redis data structures. The durability difference only affects writes.
- **MemoryDB can eliminate architectural complexity.** Replacing a cache + database with a single durable Redis service removes sync logic, consistency bugs, and operational overhead.
- **Don't over-pay for durability you don't need.** If the data is ephemeral or reconstructable, ElastiCache's lower cost and faster writes make it the right choice.
- **Both are fully Redis-compatible.** Application code, client libraries, and Redis commands work identically. Migration between them is a connection string change, not a code rewrite.
