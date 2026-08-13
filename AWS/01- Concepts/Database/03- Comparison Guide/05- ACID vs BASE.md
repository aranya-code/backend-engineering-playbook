# ACID vs BASE

Two consistency models that define how databases handle concurrent operations and failure scenarios. ACID prioritizes correctness — every transaction either fully completes or fully rolls back. BASE prioritizes availability — the system stays responsive even if some nodes have stale data. Every database you deploy on AWS sits somewhere on this spectrum. Understanding where is non-negotiable.

---

## ACID Breakdown

**Atomicity**
A transaction is all-or-nothing. If a bank transfer debits $500 from Account A but the credit to Account B fails, the entire transaction rolls back. No partial state. On Aurora/RDS, this is handled by the write-ahead log (WAL) — changes are logged before being applied, enabling rollback on failure.

**Consistency**
The database moves from one valid state to another. Constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK) are enforced at commit time. If an INSERT violates a constraint, the transaction aborts. The database never persists invalid data.

**Isolation**
Concurrent transactions don't interfere with each other. SQL databases implement this through isolation levels, each trading correctness for performance:

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Performance |
|----------------|-------------|---------------------|---------------|-------------|
| READ UNCOMMITTED | Yes | Yes | Yes | Fastest |
| READ COMMITTED | No | Yes | Yes | Fast |
| REPEATABLE READ | No | No | Yes | Moderate |
| SERIALIZABLE | No | No | No | Slowest |

Aurora PostgreSQL defaults to READ COMMITTED. Aurora MySQL defaults to REPEATABLE READ. Know these defaults — they show up in production bugs and interviews.

**Durability**
Once a transaction commits, it survives crashes. Aurora stores data across 6 copies in 3 AZs. It can lose 2 copies and still write, lose 3 copies and still read. RDS uses EBS volumes with replication within the AZ, plus Multi-AZ for cross-AZ durability.

---

## BASE Breakdown

**Basically Available**
The system guarantees availability — it will respond to every request, even if the response contains stale or inconsistent data. DynamoDB's 99.999% availability SLA for Global Tables is a direct result of this philosophy. The system never says "I don't know" — it says "here's what I last knew."

**Soft State**
The state of the system may change over time even without new input, because data is propagating between nodes. A DynamoDB Global Table write in us-east-1 hasn't reached eu-west-1 yet. Both regions have valid but different states. The system is "soft" — not yet converged.

**Eventually Consistent**
Given enough time without new updates, all nodes will converge to the same value. DynamoDB's default read is eventually consistent — you might read a value that was just overwritten. Use `ConsistentRead: true` for strong consistency at 2x the cost (double RCU consumption).

---

## AWS Service Mapping

| Service | Default Model | Strong Consistency Available? | Notes |
|---------|--------------|-------------------------------|-------|
| RDS (all engines) | ACID | Yes (default) | Full SQL transactions |
| Aurora | ACID | Yes (default) | 6 copies across 3 AZs |
| DynamoDB | BASE | Yes (per-read option) | `ConsistentRead: true` costs 2x RCU |
| DynamoDB Transactions | ACID-like | Yes | `TransactWriteItems`, `TransactGetItems` — up to 100 items |
| ElastiCache (Redis) | BASE | No | In-memory, async replication to replicas |
| DocumentDB | ACID (single-doc) | Yes | Multi-document transactions supported since 4.0 compat |
| Neptune | ACID | Yes | SPARQL/Gremlin with full transaction support |
| Keyspaces | BASE | No | Cassandra model — tunable consistency (LOCAL_QUORUM) |
| QLDB | ACID | Yes | Immutable ledger, cryptographic verification |

**DynamoDB Transactions Deep Dive**
`TransactWriteItems` lets you group up to 100 actions (Put, Update, Delete, ConditionCheck) across multiple tables into a single atomic operation. It's idempotent with client tokens. Cost is 2x WCU per item. Use it for workflows like: "create an order AND decrement inventory AND charge the balance — all or nothing."

`TransactGetItems` reads up to 100 items atomically with strong consistency. Useful for reading a consistent snapshot of related items across tables.

---

## CAP Theorem Connection

```
         Consistency
            /\
           /  \
          /    \
         / ACID \
        / (RDS,  \
       / Aurora,  \
      /  Neptune)  \
     /______________\
    /\              /\
   /  \   BASE    /  \
  / AP \(DynamoDB/ CP \
 /      \ Elasti-/     \
/________\Cache /______\
Availability    Partition
                Tolerance
```

In a distributed system, you get two of three during a network partition:

- **CP (Consistency + Partition Tolerance):** System rejects writes it can't guarantee are consistent. Aurora during failover — brief unavailability to maintain consistency.
- **AP (Availability + Partition Tolerance):** System accepts writes on all available nodes even if they diverge. DynamoDB Global Tables — both regions accept writes during partition, conflicts resolved by last-writer-wins.
- **CA (Consistency + Availability):** Only possible without network partitions. Single-node RDS — no partition concern, but no fault tolerance either.

CAP is a spectrum, not a toggle. DynamoDB offers strong consistent reads (CP behavior per-read) while the system overall is AP. Aurora is CA within a region but becomes CP during cross-region Global Database failover.

---

## Trade-offs: Consistency vs Availability, Latency vs Correctness

**Consistency vs Availability**
- Banking: Consistency wins. A balance read must be accurate. Use Aurora with SERIALIZABLE isolation for critical financial operations.
- Social media feed: Availability wins. Showing a post 200ms late is fine. Use DynamoDB with eventually consistent reads.
- Shopping cart: Availability wins. Cart operations must never fail. Use DynamoDB. Reconcile inconsistencies at checkout with TransactWriteItems.

**Latency vs Correctness**
- Strong consistent read in DynamoDB: Routes to the leader node — higher latency, guaranteed latest value.
- Eventually consistent read: Routes to any replica — lower latency, might return stale value (typically <1 second stale).
- Caching layer (ElastiCache): Lowest latency, staleness depends on TTL. A 60-second TTL means up to 60 seconds of stale data.

---

## Consistency Spectrum — AWS Services

```
Strong                                                      Eventually
Consistent                                                  Consistent
◄──────────────────────────────────────────────────────────────────────►

  QLDB    Aurora   RDS     Neptune  DocumentDB  DynamoDB   ElastiCache
  │       │        │       │        │           (strong)    (Redis)
  │       │        │       │        │           │           │
  ▼       ▼        ▼       ▼        ▼           ▼           ▼
  ████████████████████████████████████          ████████████████████████
  ◄──── Always ACID ──────────────────►         ◄── BASE (tunable) ──►
                                        DynamoDB
                                        Transactions
                                           │
                                           ▼
                                     (ACID-like for
                                      grouped ops)
```

DynamoDB is the most interesting point on this spectrum. By default it's BASE with eventually consistent reads. Add `ConsistentRead: true` and it behaves like CP for that operation. Wrap operations in `TransactWriteItems` and you get ACID-like atomicity. It's the most tunable service on AWS.

---

## Comparison Table

| Dimension | ACID | BASE |
|-----------|------|------|
| Full Form | Atomicity, Consistency, Isolation, Durability | Basically Available, Soft State, Eventually Consistent |
| Priority | Correctness over availability | Availability over correctness |
| Data State | Always consistent | May be temporarily inconsistent |
| Transaction Model | Multi-row/table atomic operations | Single-item atomic, multi-item eventual |
| Scaling | Vertical (bigger instance) | Horizontal (more nodes) |
| Latency | Higher (coordination overhead) | Lower (no coordination required) |
| CAP Alignment | CP (consistency + partition tolerance) | AP (availability + partition tolerance) |
| AWS Services | RDS, Aurora, QLDB, Neptune | DynamoDB, ElastiCache, Keyspaces |
| Failure Mode | Rejects writes if consistency can't be guaranteed | Accepts writes, resolves conflicts later |
| Use Case | Financial, inventory, booking | Sessions, feeds, IoT telemetry |
| Conflict Resolution | Locks, MVCC (multi-version concurrency) | Last-writer-wins, vector clocks, CRDTs |
| Cost at Scale | Higher (bigger instances, fewer writes/sec) | Lower (horizontal scaling, pay-per-request) |

---

## Interview-Ready Explanation

> "ACID guarantees that every transaction is atomic, consistent, isolated, and durable — the database never persists invalid or partial state. On AWS, Aurora and RDS provide full ACID compliance with configurable isolation levels. BASE trades consistency for availability — the system always responds but data may be temporarily stale. DynamoDB is BASE by default with eventually consistent reads, but it offers strong consistent reads at 2x RCU cost and ACID-like transactions via TransactWriteItems for up to 100 items. The key insight is that most production systems need both — ACID for financial operations and order processing, BASE for session management and activity feeds. DynamoDB is uniquely flexible because you can dial consistency per-operation rather than per-database."

---

## Key Takeaways

1. **ACID = correctness first** — use for financial transactions, inventory management, anything where partial state is catastrophic
2. **BASE = availability first** — use for high-throughput, latency-sensitive workloads where brief staleness is acceptable
3. **DynamoDB bridges both** — eventually consistent by default, strong consistency per-read, ACID-like transactions via `TransactWriteItems`
4. **Isolation levels matter** — Aurora PostgreSQL defaults to READ COMMITTED, Aurora MySQL to REPEATABLE READ. Know the implications.
5. **CAP is a spectrum** — DynamoDB is AP overall but offers CP behavior per-operation. Aurora is CA within a region, CP during failover.
6. **Cost correlates with consistency** — strong consistent reads cost 2x RCU, transactions cost 2x WCU per item. Budget accordingly.
7. **Design for the trade-off** — don't use SERIALIZABLE isolation on a product catalog, don't use eventually consistent reads for a bank balance
