# CAP Theorem

The CAP Theorem is the foundational constraint that governs every distributed database decision you will ever make. Proposed by Eric Brewer in 2000 and formally proven by Gilbert and Lynch in 2002, it states that a distributed data store can satisfy **at most two** of three guarantees simultaneously: **Consistency**, **Availability**, and **Partition Tolerance**.

If you are designing systems on AWS — or anywhere — and you do not deeply understand CAP, you are guessing. Stop guessing.

---

## The Three Guarantees

### Consistency (C)

Every read receives the most recent write or an error. All nodes in the cluster see the same data at the same time. This is **linearizability** — the strongest form of consistency.

When a write completes on the leader, all subsequent reads (on any node) return that updated value. No stale reads. No ambiguity.

### Availability (A)

Every request (read or write) receives a non-error response, without the guarantee that it contains the most recent write. The system remains operational — every node that has not failed returns a response.

Availability does not mean "fast." It means "responsive." A system that returns stale data is available. A system that returns an error is not.

### Partition Tolerance (P)

The system continues to operate despite arbitrary message loss or failure of part of the network. Network partitions are not theoretical — they are inevitable in any distributed system running across multiple nodes, availability zones, or regions.

---

## Why Partition Tolerance Is Non-Negotiable

```
  ┌─────────────────────────────────────────────────┐
  │           THE CAP TRIANGLE                      │
  │                                                 │
  │                 C                                │
  │                /  \                              │
  │               /    \                             │
  │              /      \                            │
  │             /   CA    \      ← Only possible on  │
  │            /  (single  \       a single node.    │
  │           /    node)    \      Not distributed.  │
  │          /               \                       │
  │         P ─────────────── A                      │
  │              │       │                           │
  │             CP      AP                           │
  │                                                  │
  │   CP: Consistent + Partition Tolerant            │
  │       → Sacrifices Availability during partition  │
  │                                                  │
  │   AP: Available + Partition Tolerant             │
  │       → Sacrifices Consistency during partition   │
  │                                                  │
  │   CA: Consistent + Available                     │
  │       → Not possible in distributed systems      │
  └─────────────────────────────────────────────────┘
```

In any real distributed system, network partitions **will** happen. Hardware fails. Cables get cut. AZs lose connectivity. This is not a question of "if" — it is "when."

The moment a partition occurs, you have exactly two options:

1. **Choose Consistency (CP):** Refuse to serve requests on the partitioned side. The system becomes unavailable to some clients, but every response that is returned is correct.
2. **Choose Availability (AP):** Continue serving requests on all sides of the partition. Every client gets a response, but some responses may be stale or conflicting.

A CA system — consistent and available but not partition tolerant — only exists as a single-node database. The moment you add a second node, you have a distributed system, and you must handle partitions. **CA is not a real option for distributed architectures.**

---

## CP vs AP: Concrete Systems

### CP Systems — Consistency Over Availability

These systems will reject writes or return errors during a network partition rather than risk serving stale data.

| System | Behavior During Partition |
|---|---|
| **Amazon RDS Multi-AZ** | Synchronous replication to standby. Failover promotes standby; old primary is fenced off. No split-brain. Writes halt briefly during failover. |
| **ZooKeeper** | Quorum-based. Minority partition becomes read-only. Majority partition continues. |
| **etcd** | Raft consensus. Requires majority quorum. Minority nodes reject writes. |
| **Google Spanner** | TrueTime + Paxos. Rejects operations if it cannot reach quorum. |
| **Amazon Aurora (single-region)** | 4/6 write quorum, 3/6 read quorum. Writes fail if fewer than 4 of 6 storage nodes are reachable. |

**When to choose CP:** Financial transactions, inventory management, leader election, configuration management — anywhere a wrong answer is worse than no answer.

### AP Systems — Availability Over Consistency

These systems continue serving requests during partitions, accepting that data may temporarily diverge across nodes.

| System | Behavior During Partition |
|---|---|
| **DynamoDB Global Tables** | Multi-region, multi-active. Each region accepts writes independently. Conflicts resolved via last-writer-wins. |
| **Cassandra** | Tunable consistency. At `ONE` consistency level, any single replica can serve reads/writes. |
| **Amazon ElastiCache (Redis Cluster)** | Async replication. Read replicas may serve stale data during partition. |
| **CouchDB** | Multi-master replication. Conflicts stored and resolved by application logic. |
| **DNS** | Caches propagate updates eventually. TTL-based convergence. |

**When to choose AP:** Social media feeds, product catalogs, user session data, DNS, caching layers — anywhere an approximate answer now is better than no answer.

---

## AWS Services and CAP Alignment

| AWS Service | CAP Classification | Rationale |
|---|---|---|
| RDS Multi-AZ (MySQL/PostgreSQL) | CP | Synchronous replication to standby. Failover blocks writes briefly. |
| Aurora (Single-Region) | CP | 4/6 write quorum ensures consistency. Writes fail if quorum lost. |
| Aurora Global Database | AP (tunable) | Async replication across regions. ~1s lag. Read-after-write in primary region only. |
| DynamoDB (Single-Region) | CP (strong reads) | Strong consistency reads go to leader. |
| DynamoDB Global Tables | AP | Multi-region active-active. Last-writer-wins conflict resolution. |
| ElastiCache (Redis) | AP | Async replication. Replicas may serve stale data. |
| Amazon S3 | AP | Strong read-after-write for new objects (since Dec 2020), but cross-region replication is eventual. |
| Amazon Neptune | CP | ACID-compliant. Quorum-based writes. |

---

## PACELC: The Extension That Actually Matters

CAP only describes behavior **during** a partition. But what about normal operation? The PACELC theorem (Abadi, 2012) extends CAP:

```
  ┌──────────────────────────────────────────────┐
  │              PACELC Framework                 │
  │                                               │
  │   IF (Partition) {                            │
  │       Choose: Availability (A) or             │
  │                Consistency (C)                │
  │   } ELSE {                                   │
  │       Choose: Latency (L) or                  │
  │                Consistency (C)                │
  │   }                                           │
  │                                               │
  │   Examples:                                   │
  │   ─────────────────────────────────────────   │
  │   DynamoDB Global Tables:  PA / EL            │
  │     → Partition: Available                    │
  │     → Normal: Low Latency (eventual reads)    │
  │                                               │
  │   RDS Multi-AZ:            PC / EC            │
  │     → Partition: Consistent (failover)        │
  │     → Normal: Consistent (sync replication)   │
  │                                               │
  │   Cassandra (tunable):     PA / EL or EC      │
  │     → Partition: Available                    │
  │     → Normal: Tunable (consistency level)     │
  │                                               │
  │   Aurora Global:           PA / EL            │
  │     → Partition: Available (cross-region)     │
  │     → Normal: Low latency (async replication) │
  └──────────────────────────────────────────────┘
```

PACELC is the real decision framework. In daily operation (no partition), the tradeoff is between **latency** and **consistency**. DynamoDB's eventual consistent reads are faster (and cheaper) than strongly consistent reads because they do not need to hit the leader node.

---

## Common Mistakes

1. **Treating CAP as a permanent, binary choice.** CAP is about behavior during partitions. Most systems are tunable — DynamoDB lets you choose strong or eventual consistency per-read. Cassandra lets you set consistency levels per-query.

2. **Ignoring that "Availability" in CAP is absolute.** CAP-availability means **every** non-failing node must respond. In practice, engineers conflate this with "high availability" (99.99% uptime), which is a different concept.

3. **Assuming single-region systems are immune to partitions.** Network partitions happen within a single data center. A misconfigured security group or a saturated network link can create an effective partition between nodes in the same VPC.

4. **Choosing AP for financial systems.** If two regions independently process a withdrawal on the same account during a partition, you have created money. Do not create money. Use CP.

5. **Forgetting PACELC.** The partition case is rare. The everyday latency-vs-consistency tradeoff affects every single request. Optimize for the common case, not just the failure case.

---

## Real-World Production Scenario

**E-Commerce Checkout on AWS:**

- **Product Catalog (AP):** Served via DynamoDB Global Tables with eventual consistent reads. A customer seeing a product description that is 500ms out of date is acceptable. Availability matters more — a down catalog means zero revenue.
- **Inventory Count (CP):** Managed by Aurora Single-Region with strong consistency. Overselling is unacceptable. If the database cannot confirm stock, the checkout fails with an error. Better to lose one sale than ship products you do not have.
- **Shopping Cart (AP):** Stored in ElastiCache Redis. If a partition causes a stale cart read, the customer re-adds items. Annoying, but recoverable.
- **Payment Processing (CP):** RDS Multi-AZ PostgreSQL. Double-charging a customer is a regulatory and trust disaster. Synchronous replication and failover ensure no write is lost.

---

## Interview Questions

**Q1: A system claims to be CA (Consistent and Available without Partition Tolerance). Is this possible in a distributed environment?**

No. In any distributed system, network partitions are inevitable. A CA system can only exist as a single-node deployment, which is not distributed by definition. The moment you replicate data across nodes, you must handle partitions, forcing a choice between C and A. Any vendor claiming CA in a distributed system is either lying or redefining terms.

**Q2: DynamoDB offers both strongly consistent and eventually consistent reads. Does this mean it is both CP and AP?**

DynamoDB single-region is CP for strongly consistent reads (they go to the leader and may fail if the leader is unreachable) and AP for eventually consistent reads (any replica can respond). DynamoDB Global Tables is AP — multi-region active-active with last-writer-wins. The CAP classification depends on the consistency mode you choose per operation. It is not a fixed property of the system.

**Q3: Your team is building a global ride-sharing app. The driver location service needs sub-second updates visible worldwide. How do you apply CAP?**

Driver location is inherently AP. A driver's position 500ms ago is still useful for matching. Use DynamoDB Global Tables with eventually consistent reads. If a partition isolates a region, riders see slightly stale driver positions but the system remains functional. Payment and trip records, however, must be CP — use Aurora or RDS Multi-AZ in the primary region with strong consistency to prevent double-charges or lost trip data.

---

## Key Takeaways

- **CAP is a constraint, not a menu.** You do not pick two — the partition forces the choice between C and A. You choose what to sacrifice.
- **Partition Tolerance is mandatory.** Any distributed system must handle network partitions. CA only exists on a single node.
- **CP means correctness over uptime.** Use CP for financial transactions, inventory, and any domain where a wrong answer has irreversible consequences.
- **AP means resilience over precision.** Use AP for caching, session data, content delivery, and domains where stale data is tolerable and self-correcting.
- **PACELC is the real framework.** During normal operation, the latency-vs-consistency tradeoff matters more than the partition-time tradeoff. Optimize for the common case.
- **Most production systems are not purely CP or AP.** They are hybrid. Different data paths within the same application will have different CAP requirements. Design accordingly.
