# Database Replication

Replication keeps copies of the same data on multiple database instances. Every replication design answers one question: **how do you keep copies consistent when data changes?** The answer determines your availability, durability, latency, and failure modes.

Understand the tradeoffs cold. When your primary goes down at 3 AM, you need to know exactly what your replication topology guarantees — and what it doesn't.

---

## Synchronous vs Asynchronous Replication

| Aspect | Synchronous | Asynchronous |
|---|---|---|
| **Commit behavior** | Writer waits for replica acknowledgment | Writer commits immediately, replica catches up |
| **Data loss on failover** | Zero (RPO = 0) | Possible (RPO > 0, depends on lag) |
| **Write latency** | Higher (network round-trip to replica) | Lower (local commit only) |
| **Availability impact** | Replica failure blocks writes | Replica failure has no write impact |
| **Consistency** | Strong — replica is always current | Eventual — replica may lag |
| **Use case** | Durability-critical (financial, health) | Read scaling, analytics, geo-distribution |

**Semi-synchronous** is the middle ground: one replica is synchronous (guaranteeing at least one durable copy), the rest are asynchronous. This is what RDS Multi-AZ does under the hood.

---

## Replication Topologies

### Single-Leader (Master-Slave)

```
        ┌──────────────┐
        │    Leader     │
        │  (Read/Write) │
        └──────┬───────┘
               │  Replication Stream
        ┌──────┼──────────────┐
        │      │              │
        ▼      ▼              ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Follower │ │Follower │ │Follower │
   │ (Read)  │ │ (Read)  │ │ (Read)  │
   └─────────┘ └─────────┘ └─────────┘
```

All writes go to one leader. Followers replicate the leader's write-ahead log (WAL) and serve reads. Simple, well-understood, and the default for most relational databases.

**Tradeoff:** Single write endpoint = single point of failure for writes. Failover promotes a follower to leader.

**AWS examples:**
- **RDS Multi-AZ** — synchronous standby in another AZ, automatic failover (~60s)
- **RDS Read Replicas** — asynchronous followers for read scaling

### Multi-Leader (Master-Master)

```
   ┌──────────────┐         ┌──────────────┐
   │   Leader A   │◄───────►│   Leader B   │
   │  (Read/Write)│  Async  │  (Read/Write)│
   │  Region: US  │  Repl   │  Region: EU  │
   └──────┬───────┘         └──────┬───────┘
          │                        │
     ┌────┴────┐              ┌────┴────┐
     ▼         ▼              ▼         ▼
  [Follower] [Follower]   [Follower] [Follower]
```

Multiple nodes accept writes independently. Each leader replicates to the others asynchronously. Enables multi-region writes with local latency.

**The hard problem: write conflicts.** Two leaders accept conflicting updates to the same row simultaneously. Resolution strategies:
- **Last-writer-wins (LWW)** — timestamp-based, silently drops one write
- **Application-level resolution** — custom merge logic
- **CRDTs** — conflict-free replicated data types (counters, sets)

**AWS example:**
- **DynamoDB Global Tables** — multi-leader across regions, LWW conflict resolution, replication lag typically under 1 second

### Leaderless (Dynamo-Style)

```
        ┌──────────────┐
        │    Client     │
        └──────┬───────┘
               │  Write to W nodes
        ┌──────┼──────────────┐
        │      │              │
        ▼      ▼              ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Node A  │ │ Node B  │ │ Node C  │
   │  (R/W)  │ │  (R/W)  │ │  (R/W)  │
   └─────────┘ └─────────┘ └─────────┘
               │
               │  Read from R nodes
               │  Quorum: W + R > N
```

No designated leader. Clients write to `W` nodes and read from `R` nodes simultaneously. Consistency is tuned via quorum: `W + R > N` guarantees a read sees the latest write.

**Quorum examples (N=3):**
- `W=2, R=2` — strong consistency, tolerates 1 node failure
- `W=1, R=3` — fast writes, slow reads, strong consistency
- `W=1, R=1` — fast everything, eventual consistency (stale reads possible)

**AWS example:**
- **DynamoDB** uses leaderless replication internally within a region, though this is abstracted away from the user

---

## Replication Lag

Asynchronous replication means the follower is always **behind** the leader. The gap is replication lag.

### Causes

| Cause | Description |
|---|---|
| Network latency | Physical distance or congestion between leader and follower |
| Follower overload | Replica CPU/IO saturated by heavy read traffic |
| Large transactions | Bulk writes create a backlog in the replication stream |
| Schema changes | DDL operations (ALTER TABLE) can block replication |
| Long-running queries | On the replica, blocking WAL replay |

### Effects

- **Stale reads** — user writes data, immediately reads from replica, gets old value
- **Phantom reads** — related rows replicated at different times produce inconsistent state
- **Broken read-after-write** — user updates profile, page refresh shows old data

### Mitigation

- **Read-your-own-writes** — route reads to the leader for a short window after a write
- **Monotonic reads** — pin a user session to a specific replica
- **Causal consistency** — track logical timestamps, ensure reads respect write order
- **Promote monitoring** — alert on replication lag exceeding SLA thresholds (e.g., >5s)

---

## Failover Process

When the leader fails, a follower must be promoted. This is failover.

```
  Normal Operation:           Failover:

  ┌────────┐                  ┌────────┐
  │ Leader │ ──── X (DOWN)    │ Leader │ (DEAD)
  └────────┘                  └────────┘
       │
  ┌────┴────┐                 ┌─────────────┐
  │         │                 │  Follower B  │
  ▼         ▼                 │  PROMOTED    │
┌─────┐  ┌─────┐             │  New Leader  │
│ F-A │  │ F-B │──PROMOTE──►  └──────┬──────┘
└─────┘  └─────┘                     │
                              ┌──────┴──────┐
                              ▼             ▼
                           [F-A]     [New Follower]
```

### Failover Steps

1. **Detection** — health checks detect leader is unresponsive (timeout threshold)
2. **Election** — choose the follower with the least replication lag
3. **Promotion** — promoted follower accepts writes
4. **Reconfiguration** — remaining followers point to the new leader
5. **DNS/endpoint update** — clients route to the new leader
6. **Old leader fencing** — prevent the old leader from accepting writes if it recovers (STONITH)

### RDS Multi-AZ Failover

- Synchronous standby in another AZ
- Automatic failover: DNS endpoint flips to standby (~30-60 seconds)
- No data loss (synchronous replication)
- Application must handle brief connection interruption and retry

---

## Split-Brain Problem

Split-brain occurs when **two nodes both believe they are the leader** and accept writes independently. This creates divergent data that is extremely difficult to reconcile.

```
  Network Partition:

  ┌────────────┐              ┌────────────┐
  │  Leader A  │     ╳ ╳ ╳    │  Leader B  │
  │  (thinks   │   Network    │  (promoted  │
  │   it's     │   Partition  │   itself    │
  │   leader)  │              │   leader)  │
  └────────────┘              └────────────┘
       │                           │
    Clients                     Clients
    write here                  write here
       │                           │
    DIVERGED DATA ◄──────────► DIVERGED DATA
```

**Prevention:**
- **Fencing tokens** — monotonically increasing tokens; storage rejects writes with old tokens
- **STONITH** (Shoot The Other Node In The Head) — forcibly power off the old leader
- **Quorum-based election** — require majority consensus before promotion
- **Lease-based leadership** — leader must renew a time-limited lease; expired lease = step down

RDS Multi-AZ avoids split-brain by using shared storage fencing — the old primary is forcibly disconnected from the underlying EBS volumes during failover.

---

## Replication Topology Comparison

| Feature | Single-Leader | Multi-Leader | Leaderless |
|---|---|---|---|
| **Write endpoints** | 1 | N (one per leader) | Any node |
| **Write conflicts** | None | Yes — must resolve | Yes — quorum-based |
| **Read scaling** | Add followers | Add followers per leader | Add nodes |
| **Write scaling** | Vertical only | Horizontal (per region) | Horizontal |
| **Consistency** | Strong (sync) or eventual (async) | Eventual | Tunable (quorum) |
| **Failover complexity** | Moderate | Low (other leaders available) | Low (no leader to fail) |
| **Cross-region writes** | High latency (remote leader) | Local latency | Local latency |
| **Operational complexity** | Low | High (conflict resolution) | High (quorum tuning) |
| **AWS example** | RDS Multi-AZ | DynamoDB Global Tables | DynamoDB (internal) |

---

## Common Mistakes

1. **Reading from replicas immediately after writing** — asynchronous replication means the replica hasn't received the write yet. Implement read-after-write consistency by routing post-write reads to the leader for a configurable window.

2. **Ignoring replication lag monitoring** — lag spikes silently degrade user experience. Set CloudWatch alarms on `ReplicaLag` for RDS. Alert at thresholds meaningful to your SLA (e.g., >5 seconds for user-facing reads).

3. **No failover testing** — failover is a production event you must rehearse. Use RDS reboot-with-failover regularly. Verify your application reconnects, retries, and doesn't cache the old endpoint.

4. **Assuming Multi-AZ is a read scaling solution** — RDS Multi-AZ standby does not serve reads. It's a hot standby for failover only. Use Read Replicas for read scaling.

5. **Using multi-leader replication without conflict resolution** — LWW silently drops writes. If your domain can't tolerate silent data loss, you need application-level merge logic or a different replication topology.

---

## Interview Questions

**Q1: Your application writes to the leader and immediately reads from a replica, but users report seeing stale data. What's happening and how do you fix it?**

Asynchronous replication lag. The read hits the replica before the write propagates. Fix with read-after-write consistency: after a write, route subsequent reads to the leader for a short window (e.g., 5 seconds). Alternatively, use the leader for all reads in write-heavy user sessions, or use session-sticky routing to a specific replica for monotonic reads.

**Q2: Explain the split-brain problem and how RDS Multi-AZ prevents it.**

Split-brain occurs when a network partition causes two nodes to both act as leader, accepting conflicting writes. RDS prevents this through storage-level fencing: during failover, the old primary is forcibly disconnected from its EBS volumes. Only the promoted standby can write to storage. Additionally, the DNS endpoint is updated atomically, so clients can only reach one writer at a time.

**Q3: When would you choose multi-leader replication over single-leader?**

When you need low-latency writes in multiple geographic regions simultaneously. Single-leader forces all writes to one region, adding cross-region latency. Multi-leader places a writable leader in each region. The tradeoff is conflict resolution complexity — you must handle concurrent writes to the same data. DynamoDB Global Tables use this pattern with last-writer-wins semantics.

**Q4: What is the difference between RDS Multi-AZ and RDS Read Replicas?**

Multi-AZ is a **high availability** feature: synchronous replication to a standby that doesn't serve reads, with automatic failover (~60s). Read Replicas are a **read scaling** feature: asynchronous replication to followers that serve read traffic but cannot be automatically promoted. Multi-AZ guarantees zero data loss on failover. Read Replicas may lose recent writes if promoted manually during a failure.

---

## Key Takeaways

- **Synchronous replication guarantees zero data loss but increases write latency** — the writer waits for at least one replica to confirm. Asynchronous is faster but risks losing recent writes on failover.

- **Single-leader is the default for good reason** — no write conflicts, simple mental model. Use multi-leader only when multi-region write latency is a hard requirement.

- **Replication lag is not a bug, it's a feature tradeoff** — design your application to handle stale reads with patterns like read-after-write consistency and monotonic reads.

- **Failover must be tested regularly, not assumed** — untested failover is no failover. Trigger RDS failovers in staging. Measure reconnection time. Validate no data loss.

- **Split-brain is the worst-case replication failure** — always have fencing mechanisms. Never rely solely on timeout-based leader detection without a kill switch for the old leader.

- **RDS Multi-AZ is for availability, Read Replicas are for read scaling** — they solve different problems and are often used together.
