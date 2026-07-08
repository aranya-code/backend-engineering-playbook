# Database Sharding

Sharding splits your data across **independent database instances** (shards), each holding a subset of the total dataset. Every shard is a fully autonomous database — its own compute, storage, connections, and failure domain. This is how you scale writes beyond the ceiling of a single machine.

If you're reading this because someone said "let's shard the database," stop. Exhaust vertical scaling, read replicas, caching, and query optimization first. Sharding is a one-way door that trades operational simplicity for horizontal scale.

---

## Sharding vs Partitioning

These terms get used interchangeably. They shouldn't.

| Aspect | Partitioning | Sharding |
|---|---|---|
| **Scope** | Within a single database instance | Across multiple database instances |
| **Compute** | Shared CPU/memory | Independent CPU/memory per shard |
| **Storage** | Shared disk | Independent disk per shard |
| **Failure domain** | Single point of failure | Isolated failures per shard |
| **Connection pool** | One pool | Pool per shard |
| **Cross-partition queries** | Database handles internally | Application must coordinate |
| **Operational complexity** | Low — database manages it | High — you manage it |

**Partitioning** is a database feature. PostgreSQL table partitioning, MySQL partition pruning — the engine handles routing internally. **Sharding** is an architectural decision. Your application (or a proxy layer) decides which shard to hit.

In practice, you'll often use both: shard across instances, then partition within each shard.

---

## Sharding Strategies

### Hash-Based Sharding

```
shard_id = hash(shard_key) % number_of_shards
```

Distributes data uniformly. No hotspots if the hash function is good. The problem: adding or removing shards invalidates the entire mapping.

**Best for:** Even write distribution, no range-scan requirements.

### Range-Based Sharding

```
Shard 0: user_id 1 - 1,000,000
Shard 1: user_id 1,000,001 - 2,000,000
Shard 2: user_id 2,000,001 - 3,000,000
```

Natural for time-series data or sequential keys. Range queries stay within a shard. The problem: recent data piles onto the last shard (hotspot).

**Best for:** Time-series data, range queries, archival patterns.

### Directory-Based Sharding

A lookup service maps each key to its shard. Maximum flexibility — you can move individual keys between shards without rehashing. The problem: the directory is a single point of failure and a potential bottleneck.

**Best for:** Uneven data distribution, tenant-based isolation, compliance requirements.

---

## Shard Key Selection

The shard key is the single most consequential decision in your sharding design. Get it wrong and you'll resharding within months.

**Good shard key properties:**
- **High cardinality** — enough distinct values to distribute evenly
- **Even distribution** — no value dominates the dataset
- **Query affinity** — most queries include the shard key
- **Immutable** — changing the key means moving data between shards

**Common shard keys and tradeoffs:**

| Shard Key | Pros | Cons |
|---|---|---|
| `user_id` | Even distribution, queries are user-scoped | Cross-user analytics require scatter-gather |
| `tenant_id` | Natural isolation, compliance-friendly | Large tenants cause hotspots |
| `created_at` | Range queries, archival | Write hotspot on latest shard |
| `region` | Data locality, compliance | Uneven population distribution |
| `order_id` | High cardinality | No query affinity for user lookups |

---

## Architecture: Sharded Users Table

```
                        ┌──────────────────┐
                        │   Application    │
                        │   (Shard Router)  │
                        └────────┬─────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │ Shard 0  │ │ Shard 1  │ │ Shard 2  │
            │          │ │          │ │          │
            │ users    │ │ users    │ │ users    │
            │ orders   │ │ orders   │ │ orders   │
            │ payments │ │ payments │ │ payments │
            │          │ │          │ │          │
            │ hash(id) │ │ hash(id) │ │ hash(id) │
            │ % 3 = 0  │ │ % 3 = 1  │ │ % 3 = 2  │
            └──────────┘ └──────────┘ └──────────┘
                 │            │            │
            ┌────┘       ┌────┘       ┌────┘
            ▼            ▼            ▼
        [Replica]    [Replica]    [Replica]
```

Each shard holds the **complete schema** but only a subset of rows. Related tables (users, orders, payments) are co-located on the same shard using the same shard key (`user_id`), so joins within a user context stay local.

---

## Cross-Shard Queries

This is the biggest operational pain point. Any query that can't be routed to a single shard becomes a **scatter-gather** operation.

```
"SELECT * FROM users WHERE email = 'alice@example.com'"
```

If you sharded by `user_id`, this query has no shard key. The application must:
1. Fan out the query to **all shards**
2. Collect results
3. Merge and return

**Mitigation strategies:**
- **Secondary index shard** — a separate lookup mapping `email → user_id → shard`
- **Broadcast tables** — small reference tables replicated to every shard
- **Denormalization** — duplicate data to avoid cross-shard joins
- **CQRS** — separate read models that aggregate across shards asynchronously

Cross-shard transactions are worse. Two-phase commit across shards is slow, fragile, and operationally brutal. Avoid them. Redesign your data model instead.

---

## Resharding

Adding or removing shards with naive hash-based routing (`hash % N`) invalidates most key-to-shard mappings. Resharding means migrating terabytes of data with zero downtime.

### Consistent Hashing

Instead of `hash % N`, map both keys and shards onto a hash ring (0 to 2^32). Each key is assigned to the next shard clockwise on the ring.

```
                    0
                    │
            Shard C ●───────────● Shard A
                   ╱             ╲
                  ╱   Hash Ring   ╲
                 ╱                 ╲
                ●───────────────────●
            Shard D             Shard B
                    │
                   2^32

  Adding Shard E between A and B:
  - Only keys between A and E move to E
  - All other keys stay on their current shard
  - ~1/N of keys migrate instead of nearly all
```

**Benefits:**
- Adding a shard moves only `~1/N` of keys (not `N-1/N`)
- Virtual nodes (multiple points per shard) smooth distribution
- Used by DynamoDB, Cassandra, and most distributed databases internally

### Resharding Process (Production)

1. **Provision new shard** — empty instance with identical schema
2. **Double-write** — application writes to both old and new shard
3. **Backfill** — migrate historical data from old shard to new
4. **Verify** — checksums, row counts, consistency checks
5. **Cutover** — update routing, stop double-write
6. **Drain old shard** — remove migrated data after bake period

---

## When to Shard

Sharding is a last resort. Run through this checklist first:

| Try This First | Why |
|---|---|
| Vertical scaling | Bigger instance, zero code changes |
| Read replicas | Offload read traffic |
| Connection pooling (PgBouncer) | More efficient connection usage |
| Query optimization | Indexes, query plans, N+1 fixes |
| Caching (Redis/ElastiCache) | Reduce database load |
| Table partitioning | Database-managed, transparent to app |
| Archival / data lifecycle | Reduce active dataset size |

**Shard when:**
- Single-instance write throughput is the bottleneck (not reads)
- Dataset exceeds single-instance storage limits
- Tenant isolation is a compliance or SLA requirement
- You need independent failure domains per customer segment

---

## Common Mistakes

1. **Sharding too early** — premature sharding adds years of operational overhead for problems you don't have yet. A single PostgreSQL instance handles more than most teams think.

2. **Choosing a low-cardinality shard key** — sharding by `country` when 60% of users are in one country creates a permanent hotspot that can't be fixed without resharding.

3. **Ignoring cross-shard query patterns** — the shard key optimizes writes, but if every read query spans all shards, you've made reads worse without fixing the actual bottleneck.

4. **No co-location strategy** — sharding `users` by `user_id` but `orders` by `order_id` guarantees every user-order join is cross-shard. Co-locate related entities on the same shard key.

5. **Treating shards as disposable** — each shard is a production database that needs monitoring, backups, failover, and capacity planning. Ten shards means ten times the operational surface area.

---

## Interview Questions

**Q1: You have a multi-tenant SaaS platform with 10,000 tenants. One tenant generates 40% of all traffic. How do you shard this?**

Use directory-based sharding. Assign the large tenant its own dedicated shard. Distribute remaining tenants across shared shards using hash-based routing. The directory approach lets you move tenants between shards without resharding. Monitor per-shard metrics and rebalance when any shard exceeds 70% capacity.

**Q2: Your team sharded by `user_id` but now product wants a global leaderboard across all users. How do you handle this?**

Don't scatter-gather across all shards on every request. Build a separate read-optimized aggregation — a CQRS pattern. Use change data capture (CDC) or event streams to feed a dedicated leaderboard service (Redis sorted set or a single aggregation database). Accept eventual consistency for the leaderboard.

**Q3: Explain why consistent hashing is preferred over modulo-based sharding in distributed systems.**

Modulo-based (`hash % N`) remaps nearly all keys when `N` changes. Consistent hashing maps keys and shards onto a ring, so adding or removing a shard only affects `~1/N` of keys. Virtual nodes further improve balance. This makes scaling operations dramatically cheaper in terms of data migration.

**Q4: What happens during a resharding operation if the application crashes mid-migration?**

If using double-write with backfill, the old shard still has all data — it's the source of truth until cutover. Resume the backfill from the last checkpoint. Idempotent migration scripts are critical: every row migration must be safe to retry. The routing layer should still point to the old shard, so reads are unaffected.

---

## Key Takeaways

- **Sharding splits data across independent database instances** — each shard is its own server with separate compute, storage, and failure domain. Partitioning stays within one instance.

- **Shard key selection is permanent and consequential** — optimize for high cardinality, even distribution, and query affinity. Co-locate related entities on the same shard key.

- **Cross-shard queries are the primary operational cost** — every query without a shard key becomes a scatter-gather. Design your data model around the shard key, not the other way around.

- **Consistent hashing minimizes resharding impact** — adding a shard moves `~1/N` keys instead of nearly all. Virtual nodes smooth distribution further.

- **Shard only after exhausting simpler options** — vertical scaling, read replicas, caching, connection pooling, and table partitioning handle far more traffic than most teams realize.

- **Each shard multiplies operational burden** — backups, monitoring, failover, schema migrations, and capacity planning all scale linearly with shard count.
