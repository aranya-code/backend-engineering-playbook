# Consistency Models

Consistency models define the contract between a distributed system and its clients: what guarantees do you get about the data you read relative to the data that was written? This is not an academic exercise — choosing the wrong consistency model for a workload either wastes money (over-engineering) or causes data corruption (under-engineering).

Every distributed system you deploy on AWS — from DynamoDB to Aurora Global Database to ElastiCache — implements one or more consistency models. Understanding the spectrum, the tradeoffs, and the AWS-specific behaviors is a prerequisite for designing systems that behave correctly under load and failure.

---

## The Consistency Spectrum

Consistency is not binary. It is a spectrum from strongest (most expensive, highest latency, safest) to weakest (cheapest, lowest latency, most permissive).

```
  ┌──────────────────────────────────────────────────────────┐
  │              CONSISTENCY SPECTRUM                         │
  │                                                          │
  │   Strongest ◄─────────────────────────────► Weakest      │
  │                                                          │
  │   ┌──────────┬──────────┬───────────┬────────┬────────┐  │
  │   │Lineariz- │ Sequen-  │  Causal   │Session │Eventual│  │
  │   │able      │ tial     │           │        │        │  │
  │   │(Strong)  │          │           │        │        │  │
  │   └──────────┴──────────┴───────────┴────────┴────────┘  │
  │                                                          │
  │   ◄── Higher Latency          Lower Latency ──►          │
  │   ◄── Lower Throughput     Higher Throughput ──►          │
  │   ◄── More Coordination  Less Coordination  ──►          │
  │   ◄── Easier to Reason   Harder to Reason   ──►          │
  │                                                          │
  │   AWS Mappings:                                          │
  │   ├─ RDS Multi-AZ ─────────── Linearizable              │
  │   ├─ Aurora (single-region) ── Linearizable              │
  │   ├─ DynamoDB (strong read) ── Linearizable              │
  │   ├─ Aurora Global DB ──────── Session / Eventual        │
  │   ├─ DynamoDB (eventual) ───── Eventual                  │
  │   ├─ DynamoDB Global Tables ── Eventual                  │
  │   ├─ ElastiCache ───────────── Eventual                  │
  │   └─ S3 CRR ───────────────── Eventual                  │
  └──────────────────────────────────────────────────────────┘
```

---

## Strong Consistency (Linearizability)

The strongest possible guarantee. Every read returns the value of the most recent completed write. The system behaves as if there is a single copy of the data, even though it is replicated across multiple nodes.

**Formal definition:** If write W completes before read R starts, then R must return the value written by W (or a later write). There is a total order on all operations that is consistent with real-time ordering.

### How It Works

The read request must contact the **leader node** (the node that processes writes) or verify freshness with the leader before returning. This requires at least one round-trip to the leader, adding latency.

```
  ┌────────────────────────────────────────────────┐
  │           STRONG CONSISTENCY READ              │
  │                                                │
  │   Client ──── READ(key) ────▶ Leader Node      │
  │                                  │              │
  │                                  ▼              │
  │                          Check latest value     │
  │                          (may require quorum)   │
  │                                  │              │
  │   Client ◀── value=42 ─────────┘              │
  │                                                │
  │   Guarantee: This IS the latest value.         │
  │   Latency:   Higher (must contact leader)      │
  │   Cost:      2x read capacity (DynamoDB)       │
  └────────────────────────────────────────────────┘
```

### AWS Implementations

| Service | How Strong Consistency Is Achieved |
|---|---|
| **RDS Multi-AZ** | Synchronous replication to standby. All reads and writes go to the primary. Standby is not readable (failover only). |
| **Aurora (single-region)** | Writer endpoint handles all writes. Reader endpoints use MVCC with Aurora's shared storage layer, which provides read-after-write consistency via the Volume Sequence Number (VSN). |
| **DynamoDB (strongly consistent read)** | Read goes to the leader storage node for the partition. Costs 2x the read capacity units of an eventually consistent read. May fail if the leader is unreachable. |

### When to Use

- Financial transactions and balance checks
- Inventory decrements at checkout
- User authentication and authorization decisions
- Configuration management and feature flags
- Any operation where acting on stale data has irreversible consequences

---

## Eventual Consistency

The weakest useful guarantee. If no new writes occur, all replicas will **eventually** converge to the same value. During the convergence window, different clients may read different values for the same key.

### How It Works

Reads can be served by any replica, including those that have not yet received the latest write. The system prioritizes availability and low latency over freshness.

```
  ┌────────────────────────────────────────────────┐
  │           EVENTUAL CONSISTENCY READ            │
  │                                                │
  │   Client ──── READ(key) ────▶ Nearest Replica  │
  │                                  │              │
  │                                  ▼              │
  │                          Return local value     │
  │                          (may be stale)         │
  │                                  │              │
  │   Client ◀── value=37 ─────────┘              │
  │                                                │
  │   Reality: Leader has value=42 (written 5ms    │
  │   ago, not yet replicated to this replica).    │
  │   Latency:   Lowest (local replica)            │
  │   Cost:      1x read capacity (DynamoDB)       │
  └────────────────────────────────────────────────┘
```

### AWS Implementations

| Service | Convergence Time | Notes |
|---|---|---|
| **DynamoDB (default reads)** | < 50ms | Reads from any replica. Half the cost of strong reads. |
| **DynamoDB Global Tables** | < 1 second | Cross-region replication. LWW conflict resolution. |
| **Aurora Global Database** | < 1 second | Cross-region read replicas. Async replication of redo log. |
| **ElastiCache (Redis replicas)** | < 10ms | Async replication from primary. |
| **S3 Cross-Region Replication** | Minutes | No SLA. Typically 5-15 minutes. |
| **Route 53** | TTL-dependent | 60s default TTL. Global DNS cache convergence. |

### When to Use

- Social media timelines and feeds
- Product catalog browsing (not checkout)
- Analytics dashboards and reporting
- Search indices
- CDN content freshness

---

## Read-After-Write Consistency (Read-Your-Writes)

A client that writes a value is guaranteed to read that value back on subsequent reads. Other clients may still see stale data. This is a **session-scoped** guarantee, not a global one.

### How It Works

The system tracks which writes a client has performed and ensures that reads from the same client reflect at least those writes. This can be implemented via:

- Routing the client's reads to the same node that processed the write
- Attaching a write timestamp/version to the client session and rejecting stale reads
- Using the leader for reads that immediately follow writes

```
  ┌────────────────────────────────────────────────┐
  │       READ-AFTER-WRITE CONSISTENCY             │
  │                                                │
  │   Client A: WRITE(key, 42) ──▶ Leader          │
  │   Client A: READ(key)  ──────▶ Leader          │
  │   Client A: ◀── value=42 ✓  (own write)       │
  │                                                │
  │   Client B: READ(key) ───────▶ Replica         │
  │   Client B: ◀── value=37    (stale, no        │
  │                               guarantee for B) │
  │                                                │
  │   Client A sees their own write immediately.   │
  │   Client B may not — depends on replication.   │
  └────────────────────────────────────────────────┘
```

### AWS Implementations

| Service | Read-After-Write Support |
|---|---|
| **S3 (same-region)** | Full read-after-write consistency for PUTs of new objects since Dec 2020. Also for overwrites and DELETEs. |
| **DynamoDB** | Achievable by using strongly consistent reads immediately after writes. Not automatic with eventual reads. |
| **Aurora** | Writer endpoint provides read-after-write. Reader endpoints have replication lag (typically < 20ms). |

### When to Use

- User profile updates: user saves their bio, then immediately sees the updated bio
- Order placement: customer submits order, then views order confirmation page
- Content publishing: author publishes article, then sees it on their dashboard

### Common Implementation Pattern

```
  ┌────────────────────────────────────────────────┐
  │   APPLICATION-LEVEL READ-AFTER-WRITE           │
  │                                                │
  │   1. User updates profile                      │
  │      → Write to DynamoDB (returns timestamp)   │
  │                                                │
  │   2. Set cookie/header: X-Last-Write: T1       │
  │                                                │
  │   3. Subsequent reads check X-Last-Write       │
  │      → If T1 is recent (< 5 seconds):          │
  │        Use strongly consistent read            │
  │      → Else:                                   │
  │        Use eventually consistent read          │
  │                                                │
  │   Cost-optimized: strong reads only when       │
  │   needed, eventual reads for everything else.  │
  └────────────────────────────────────────────────┘
```

---

## Causal Consistency

Preserves the causal ordering of operations. If operation A causally precedes operation B (A happened-before B), then every node must see A before B. Concurrent operations (no causal relationship) may be seen in any order.

### How It Works

The system tracks causal dependencies between operations, typically via vector clocks or version vectors. When a client reads value V1 and then writes V2, the system knows V2 depends on V1. Any node that has V2 must also have V1.

```
  ┌────────────────────────────────────────────────┐
  │           CAUSAL CONSISTENCY                   │
  │                                                │
  │   User A posts: "I got the job!"      (P1)     │
  │   User B reads P1, replies: "Congrats!" (P2)   │
  │                                                │
  │   Causal: P2 depends on P1                     │
  │                                                │
  │   ✅ Valid ordering:   P1 → P2                  │
  │   ❌ Invalid ordering: P2 → P1                  │
  │      (reply appears before the original post)  │
  │                                                │
  │   Concurrent events (no causal link):          │
  │   User C posts: "Nice weather today"  (P3)     │
  │   P3 has no causal relationship with P1 or P2  │
  │   P3 can appear before, after, or between      │
  │   P1 and P2 — all orderings are valid.         │
  └────────────────────────────────────────────────┘
```

### AWS Implementations

No AWS managed service explicitly exposes causal consistency as a configurable option. However:

- **DynamoDB Streams:** Provides per-item ordered change capture. Consumers see changes to a single item in the order they occurred, which preserves causal order for single-item operations.
- **Kinesis:** Preserves ordering within a shard (partition key). Causal events routed to the same shard maintain causal order.

### When to Use

- Messaging systems: replies must appear after the message they reference
- Collaborative editing: edits based on a prior version must be applied in order
- Social feeds: comments on a post must not appear before the post itself

---

## Session Consistency

Guarantees consistency within a single client session. The client sees a monotonically progressing view of the data — reads within the session never go backward. This combines read-after-write consistency with monotonic reads.

### Properties

- **Monotonic Reads:** If a client reads value V at time T, subsequent reads will return V or a newer value. The client never sees older data than what it has already observed.
- **Monotonic Writes:** Writes from a session are applied in order. Write W2 (after W1) will not be visible at any node until W1 is also visible.
- **Read-Your-Writes:** The client sees its own writes immediately.

### AWS Implementations

| Service | Session Consistency Support |
|---|---|
| **Aurora Global Database** | Session consistency via "write forwarding." Secondary regions forward writes to the primary. Subsequent reads in the session reflect the forwarded write (eventually). |
| **DynamoDB** | Application-managed. Track version/timestamp in client session. Use conditional reads/writes. |
| **ElastiCache** | Sticky sessions (route to same replica) provide session consistency. Without sticky routing, not guaranteed. |

### When to Use

- Shopping cart: user adds items and expects to see them persist across pages
- Multi-step forms: user progresses through a wizard and expects prior steps to be visible
- Any UX where "going backward" would confuse or frustrate the user

---

## Consistency Models Comparison

| Model | Guarantee | Latency | Cost | AWS Example | Best For |
|---|---|---|---|---|---|
| **Strong (Linearizable)** | Latest value, globally ordered | Highest | Highest | RDS Multi-AZ, DynamoDB strong read | Financial, inventory |
| **Sequential** | Total order, but not real-time | High | High | ZooKeeper (consensus) | Distributed coordination |
| **Causal** | Causal order preserved | Medium | Medium | DynamoDB Streams (per-item) | Messaging, social feeds |
| **Session** | Monotonic within session | Medium | Medium | Aurora Global (write forwarding) | User-facing workflows |
| **Read-After-Write** | Client sees own writes | Medium | Medium | S3 (same-region PUT) | Profile updates, order confirmation |
| **Eventual** | Converges eventually | Lowest | Lowest | DynamoDB default, ElastiCache | Catalogs, analytics, caching |

---

## Real-World Production Scenarios

### Scenario 1: Global E-Commerce Platform

```
  ┌────────────────────────────────────────────────┐
  │   DATA TIER          CONSISTENCY MODEL          │
  │   ──────────────     ──────────────────         │
  │   User Auth          Strong (RDS Multi-AZ)     │
  │   Product Catalog    Eventual (DynamoDB)        │
  │   Shopping Cart      Session (ElastiCache)      │
  │   Inventory          Strong (Aurora)            │
  │   Order Placement    Strong (Aurora)            │
  │   Order History      Eventual (DynamoDB)        │
  │   Recommendations    Eventual (DynamoDB)        │
  │   Price Display      Read-After-Write (DDB)     │
  └────────────────────────────────────────────────┘
```

### Scenario 2: Multi-Region SaaS Application

Primary region: us-east-1. Secondary region: eu-west-1.

- **Within primary region:** Strong consistency via Aurora writer. All writes and critical reads go to the writer endpoint.
- **Within secondary region:** Eventual consistency via Aurora read replicas. Lag is typically < 1 second but can spike during high write load.
- **Cross-region reads after write:** Application-level read-after-write. After a write in us-east-1, set a session flag. For 5 seconds, route that user's reads to us-east-1 (even if they are in Europe). After 5 seconds, resume reading from eu-west-1.

### Scenario 3: IoT Sensor Data Pipeline

- **Sensor ingestion:** Eventual consistency. Sensors push data to regional DynamoDB tables via IoT Core. Data replicates globally via DynamoDB Global Tables.
- **Real-time dashboards:** Eventual consistency. Dashboard reads from the nearest region. A sensor reading from 2 seconds ago is acceptable.
- **Alerting and threshold breaches:** Strong consistency. Alert evaluation queries use strongly consistent reads against the primary region's table. A missed breach because of stale data is unacceptable.

---

## Common Mistakes

1. **Using eventual consistency for read-after-write scenarios without compensation.** User updates their email, refreshes the page, sees the old email. Ticket filed: "your system is broken." Always provide read-after-write for user-facing mutations.

2. **Assuming strong consistency across regions.** Aurora Global Database provides strong consistency only in the primary region. Cross-region reads are eventually consistent (~1 second lag). If you need global strong consistency, use DynamoDB strongly consistent reads per-request — but accept the latency penalty of cross-region round-trips.

3. **Conflating consistency models with durability.** Eventual consistency does not mean data can be lost. A successfully acknowledged write in DynamoDB is durable — it is replicated to multiple storage nodes. The consistency model only governs when replicas converge, not whether the data survives.

4. **Over-using strong consistency.** If 95% of your reads can tolerate 50ms of staleness, using strong consistency for all reads doubles your cost and latency for zero benefit. Audit your read paths and downgrade where possible.

5. **Ignoring replication lag monitoring.** Aurora exposes `AuroraReplicaLag` as a CloudWatch metric. DynamoDB Global Tables exposes `ReplicationLatency`. Set alarms. If lag spikes beyond your tolerance, your "eventual" consistency is becoming "way too eventual."

---

## Interview Questions

**Q1: Your application reads a user's profile from an Aurora read replica immediately after the user updates it via the writer. The user sees stale data. How do you fix this?**

Three approaches, in order of preference. First, use the writer endpoint for reads that immediately follow writes — accept the slight latency increase. Second, implement application-level read-after-write: after a write, set a short-lived session flag (e.g., 5 seconds), and during that window, route reads to the writer. Third, use Aurora's `ReplicaLag` CloudWatch metric to detect stale replicas and route away from them. The first approach is simplest and most reliable.

**Q2: What is the difference between strong consistency and read-after-write consistency?**

Strong consistency guarantees that **any** client reading the data sees the latest write. Read-after-write only guarantees that the **client who performed the write** sees it. Other clients may still see stale data. Strong consistency is a global guarantee; read-after-write is a session-scoped guarantee. Strong consistency is more expensive because it requires coordinating all reads through the leader.

**Q3: You are designing a chat application. Messages must appear in the correct order: replies after the message they reference. Which consistency model do you need, and why not eventual?**

Causal consistency. Eventual consistency only guarantees convergence but not ordering — a reply could temporarily appear before the message it references. Strong consistency is overkill because unrelated messages do not need global ordering. Causal consistency preserves the happened-before relationship between a message and its reply without the overhead of total ordering all operations. Implement this by tracking message dependencies (parent message ID) and using ordered delivery within a conversation partition (e.g., Kinesis shard per conversation).

**Q4: DynamoDB charges 2x RCU for strongly consistent reads vs eventually consistent reads. How do you decide which to use for each access pattern?**

Audit every read path. Ask: "If this read returns data that is 50ms stale, does the business logic produce an incorrect result?" If yes, use strong consistency (e.g., inventory check at checkout, balance verification). If no, use eventual consistency (e.g., product listing, user profile display, dashboard data). In practice, 90%+ of reads in most applications can safely use eventual consistency. The 2x cost difference adds up quickly at scale — a table doing 100K RCU would cost double for strong reads.

---

## Key Takeaways

- **Consistency is a spectrum, not a toggle.** Linearizable, causal, session, read-after-write, and eventual are all distinct guarantees with different costs and use cases. Choose the weakest model your use case can tolerate.
- **Strong consistency costs 2x in money and latency.** On DynamoDB, strong reads cost double the RCUs and require a round-trip to the leader. On Aurora, reading from the writer eliminates the benefit of read replicas. Use strong consistency deliberately, not by default.
- **Read-after-write is the minimum for user-facing mutations.** Users expect to see their own changes immediately. Failing to provide this creates support tickets, erodes trust, and makes your system feel broken.
- **Monitor replication lag as a first-class metric.** `AuroraReplicaLag`, DynamoDB `ReplicationLatency`, Redis `repl_offset` — track these. Alarm on them. Replication lag is the operational manifestation of eventual consistency, and it must stay within your tolerance.
- **Mix consistency models within an application.** Different data paths have different requirements. Auth needs strong consistency. Product recommendations need eventual. Shopping carts need session. Design each data path independently.
- **Eventual consistency does not mean data loss.** A write that is acknowledged is durable. The consistency model determines when other clients can see that write, not whether it persists. Do not confuse durability with consistency.
