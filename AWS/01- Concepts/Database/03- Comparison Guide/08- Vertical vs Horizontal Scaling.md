# Vertical vs Horizontal Scaling

Two fundamental approaches to handling growing database load. Vertical scaling buys time. Horizontal scaling buys architecture — but at the cost of distributed systems complexity.

---

## Vertical Scaling (Scale-Up)

Throw a bigger machine at the problem. More CPU, more RAM, faster storage.

```
BEFORE                          AFTER
┌──────────────┐               ┌─────────────────────┐
│  db.r6g.large │               │  db.r6g.4xlarge     │
│  2 vCPU       │    ──────►   │  16 vCPU             │
│  16 GB RAM    │               │  128 GB RAM          │
│  gp3 storage  │               │  io2 storage         │
└──────────────┘               └─────────────────────┘
   Single node                    Still single node
   Same app code                  Same app code
   No arch changes                No arch changes
```

### AWS-Specific Vertical Scaling

**RDS/Aurora:** Modify the instance class via `modify-db-instance`. Multi-AZ deployments failover to the standby with ~30s downtime. Single-AZ requires a maintenance window — plan for 5-15 minutes. Aurora Serverless v2 scales vertically in-place from 0.5 to 128 ACUs without downtime.

**ElastiCache Redis:** Modify the node type. Cluster mode disabled: brief failover to replica. Cluster mode enabled: online vertical scaling with zero downtime (scale each shard sequentially).

**DynamoDB:** Not applicable. DynamoDB doesn't expose instance classes — it's serverless. You scale throughput (RCU/WCU) or use on-demand mode.

### The Ceiling

Every vertical path hits a wall:

| Service       | Largest Instance         | vCPU | RAM      | Max Storage  |
|---------------|--------------------------|------|----------|--------------|
| RDS MySQL     | db.r6g.16xlarge          | 64   | 512 GB   | 64 TB        |
| RDS PostgreSQL| db.r6g.16xlarge          | 64   | 512 GB   | 64 TB        |
| Aurora        | db.r6g.16xlarge          | 64   | 512 GB   | 128 TB       |
| ElastiCache   | cache.r7g.16xlarge       | 64   | 512 GB   | N/A          |

When you hit `db.r6g.16xlarge`, the only direction left is out, not up.

---

## Horizontal Scaling (Scale-Out)

Add more nodes. Distribute the load across them.

```
BEFORE                          AFTER
┌──────────────┐               ┌──────────────┐
│   Primary     │               │   Primary     │ ◄── Writes
│   (RW)        │               │   (RW)        │
└──────────────┘               └──────┬───────┘
                                       │ Replication
                               ┌───────┼───────┐
                               ▼       ▼       ▼
                          ┌────────┐┌────────┐┌────────┐
                          │Replica ││Replica ││Replica │ ◄── Reads
                          │  #1    ││  #2    ││  #3    │
                          └────────┘└────────┘└────────┘

                          Read throughput = N × single node
                          Write throughput = still single primary
```

### AWS-Specific Horizontal Scaling

**RDS Read Replicas:** Up to 5 read replicas for MySQL/PostgreSQL/MariaDB. Async replication with typical lag of <1 second (but can spike under load). App must route read queries to replica endpoints explicitly.

**Aurora Read Replicas:** Up to 15 replicas sharing the same storage layer. Replication lag typically <10ms because replicas read from the same distributed storage — no data shipping. Aurora auto-scales replicas based on CPU/connections via Auto Scaling policies.

**DynamoDB:** Fully automatic horizontal scaling. Data is partitioned by partition key across storage nodes. On-demand mode handles this transparently. Provisioned mode requires capacity planning but still auto-partitions. Global tables add cross-region horizontal scaling with multi-master writes.

**ElastiCache Redis (Cluster Mode Enabled):** Data is sharded across up to 500 shards, each with up to 5 replicas. Online resharding lets you add/remove shards without downtime. Slot migration happens in the background. Total cluster: up to 500 shards × 6 nodes = 3,000 nodes.

---

## Complexity Cost of Horizontal Scaling

Horizontal scaling isn't free. You pay in architectural complexity:

**Replication Lag:** A write to the primary takes milliseconds to propagate to replicas. During that window, replicas serve stale data. If your app writes a record then immediately reads it from a replica, it may get the old value. Solution: read-after-write consistency by routing recent writes to the primary.

**Distributed Transactions:** Two-phase commit across multiple nodes is slow and fragile. Most systems avoid it entirely and use eventual consistency, saga patterns, or application-level compensation logic instead.

**Connection Management:** 5 replicas means 5 separate endpoints (or a reader endpoint that load-balances). Your connection pooling, health checks, and failover logic multiply accordingly.

**Operational Overhead:** More nodes = more monitoring, more patching, more failure domains. Each replica is a potential failure point that needs automated recovery.

---

## Comparison Table

| Dimension                    | Vertical Scaling              | Horizontal Scaling              |
|------------------------------|-------------------------------|---------------------------------|
| **Approach**                 | Bigger instance               | More instances                  |
| **Downtime required**        | Yes (brief, 30s–15min)        | No (add replicas online)        |
| **Application changes**      | None                          | Read/write routing required     |
| **Write throughput**         | Increases with CPU/RAM        | Still limited to single primary |
| **Read throughput**          | Increases with CPU/RAM        | Scales linearly with replicas   |
| **Upper limit**              | Instance class ceiling         | Practically unlimited           |
| **Cost curve**               | Exponential (2× perf ≠ 2× $) | Linear (2× nodes ≈ 2× $)       |
| **Data consistency**         | Strong (single node)          | Eventual (replication lag)      |
| **Failure blast radius**     | Total (single node failure)   | Partial (one replica fails)     |
| **Operational complexity**   | Low                           | High                            |
| **Schema changes**           | Single node DDL               | Must propagate to all replicas  |
| **Connection pooling**       | Single endpoint               | Multiple endpoints              |
| **Backup/restore**           | Single snapshot               | Coordinate across nodes         |
| **Best for**                 | Quick wins, low complexity    | Long-term scale, read-heavy     |

---

## Decision Guidance

### Start Vertical, Go Horizontal

This is the pragmatic path for most teams.

1. **Phase 1 — Vertical:** Upgrade instance class when you hit CPU or memory limits. Zero application changes. Buys you weeks to months.
2. **Phase 2 — Read replicas:** When the largest instance can't keep up or you need read isolation (analytics queries on replicas, not production primary). Requires routing logic in app.
3. **Phase 3 — Sharding:** When write throughput hits the single-primary ceiling. This is a major architectural shift — plan for months of migration work.

### When Vertical Is the Right Answer

- Team is small and moving fast — don't introduce distributed complexity yet
- Workload is write-heavy — read replicas don't help with writes
- You're nowhere near the instance ceiling — jumping from `db.r6g.large` to `db.r6g.4xlarge` is a 10-minute operation
- Compliance or simplicity requirements make single-node architectures preferable

### When Horizontal Is the Right Answer

- Read-heavy workload (>70% reads) that a single node can't serve at acceptable latency
- You need fault tolerance — a single primary with no replicas is a single point of failure
- You need geographic distribution (Aurora Global Database, DynamoDB Global Tables)
- You've already maxed out the largest available instance class

---

## Interview-Ready Explanation

> "Vertical scaling means upgrading to a larger instance — more CPU, RAM, and faster storage. In AWS, this is a `modify-db-instance` call with brief downtime. It's the simplest path because nothing in the application changes. The limit is the largest available instance class — once you hit `db.r6g.16xlarge` with 64 vCPU and 512 GB RAM, there's nowhere else to go.
>
> Horizontal scaling means adding more nodes. For reads, you add read replicas — Aurora supports up to 15 with sub-10ms replication lag because replicas share the storage layer. For writes at scale, you shard the data across multiple independent instances, which requires application-level routing and gives up cross-shard joins and transactions.
>
> The practical approach is to scale vertically first because it's fast and risk-free, then add read replicas when you need read throughput or fault tolerance, and only shard when write volume exceeds what a single primary can handle. Each step adds complexity, so you want to defer it until the business need justifies the engineering cost."

---

## Key Takeaways

1. **Vertical first, horizontal when forced.** Don't over-engineer. Scaling up is a 10-minute operation with zero app changes.
2. **The ceiling is real.** `db.r6g.16xlarge` is 64 vCPU / 512 GB RAM. Plan your horizontal strategy before you hit it.
3. **Read replicas are the easy win** for horizontal scaling. Aurora makes this nearly painless with shared storage and <10ms lag.
4. **Horizontal doesn't help writes** unless you shard. Read replicas only scale read throughput.
5. **Cost scales differently.** Vertical cost is exponential (diminishing returns). Horizontal cost is linear but adds operational overhead.
6. **DynamoDB sidesteps the choice.** It scales horizontally by design — you never pick an instance class.
7. **Replication lag is the tax** you pay for horizontal scaling. Design your app to tolerate it or route accordingly.
