# High Availability

High availability means your database keeps serving requests when things fail — and things will fail. Disks, networks, entire availability zones. HA design assumes failure is inevitable and engineers around it.

The question is never "will it fail?" It's "when it fails, does the user notice?"

---

## Availability Percentages and Downtime

These numbers define your SLA. Know them by heart.

| Availability | Common Name | Downtime/Year | Downtime/Month | Downtime/Week |
|---|---|---|---|---|
| 99% | Two nines | 3.65 days | 7.31 hours | 1.68 hours |
| 99.9% | Three nines | 8.77 hours | 43.83 minutes | 10.08 minutes |
| 99.95% | Three and a half nines | 4.38 hours | 21.92 minutes | 5.04 minutes |
| 99.99% | Four nines | 52.60 minutes | 4.38 minutes | 1.01 minutes |
| 99.999% | Five nines | 5.26 minutes | 26.30 seconds | 6.05 seconds |

**Context:**
- RDS Multi-AZ SLA: **99.95%** (~4.38 hours/year)
- Aurora SLA: **99.99%** (~52.6 minutes/year)
- DynamoDB SLA: **99.999%** for Global Tables (~5.26 minutes/year)

Every additional nine is exponentially harder and more expensive. Most applications don't need five nines. Know your actual business requirement before over-engineering.

---

## Single Points of Failure (SPOF)

A SPOF is any component whose failure takes down the entire system. HA design systematically eliminates SPOFs.

```
  BEFORE (SPOFs everywhere):

  [App Server] ──► [Single DB] ──► [Single Disk]
       │
  Single network path
       │
  Single load balancer


  AFTER (SPOFs eliminated):

  ┌────────────┐
  │    Route 53 │ (DNS failover, health-checked)
  └──────┬─────┘
         │
  ┌──────┼──────┐
  ▼      ▼      ▼
 [ALB]  [ALB]  [ALB]  (Multi-AZ load balancers)
  │      │      │
  ▼      ▼      ▼
 [App]  [App]  [App]  (Auto Scaling Group, multi-AZ)
  │      │      │
  └──────┼──────┘
         ▼
  ┌──────────────┐
  │  RDS Primary │──sync──► [RDS Standby]
  │    (AZ-a)    │          │   (AZ-b)    │
  └──────────────┘          └─────────────┘
```

**Common database SPOFs and fixes:**

| SPOF | Fix |
|---|---|
| Single database instance | Multi-AZ standby (RDS) or Aurora replicas |
| Single availability zone | Deploy across 2-3 AZs |
| Single region | Cross-region replication + DNS failover |
| Single network path | Multi-AZ subnets in different AZs |
| Single DNS endpoint | Route 53 health-checked failover routing |

---

## Active-Passive vs Active-Active

### Active-Passive

```
                    ┌─────────────────┐
                    │   DNS / Proxy   │
                    └────────┬────────┘
                             │
                    Writes & Reads
                             │
                             ▼
                    ┌─────────────────┐
                    │     PRIMARY     │ ◄── All traffic
                    │    (Active)     │
                    └────────┬────────┘
                             │
                      Sync Replication
                             │
                             ▼
                    ┌─────────────────┐
                    │     STANDBY     │ ◄── No traffic
                    │   (Passive)     │      (hot spare)
                    └─────────────────┘

  Failover: Standby promoted, DNS flipped
  Downtime: 30-60 seconds (typical RDS Multi-AZ)
```

One instance handles all traffic. The standby is a hot spare that receives synchronous replication but serves no requests. On failure, the standby is promoted.

**Characteristics:**
- Simple — no write conflicts, no split-brain risk (with proper fencing)
- Wasted capacity — standby resources are idle during normal operation
- Failover gap — 30-60 seconds of unavailability during promotion

**AWS examples:** RDS Multi-AZ, ElastiCache with replicas

### Active-Active

```
              ┌──────────────────────────┐
              │    Global Load Balancer   │
              │    (Route 53 / CloudFront)│
              └────────────┬─────────────┘
                           │
                ┌──────────┼──────────┐
                │                     │
                ▼                     ▼
       ┌────────────────┐   ┌────────────────┐
       │   REGION A      │   │   REGION B      │
       │   (Active)      │   │   (Active)      │
       │                 │   │                 │
       │  ┌───────────┐  │   │  ┌───────────┐  │
       │  │   DB A    │◄─┼───┼─►│   DB B    │  │
       │  │  (R/W)    │  │   │  │  (R/W)    │  │
       │  └───────────┘  │   │  └───────────┘  │
       └────────────────┘   └────────────────┘

  Both regions serve traffic simultaneously
  Async cross-region replication
  Conflict resolution required
```

Multiple instances serve traffic simultaneously, each accepting reads and writes. Cross-region replication keeps data synchronized.

**Characteristics:**
- Full resource utilization — all instances serve traffic
- Near-zero RTO — no promotion needed, traffic shifts instantly
- Write conflicts — concurrent writes to the same data must be resolved
- Higher complexity — conflict resolution, consistency models, network partitions

**AWS examples:** DynamoDB Global Tables, Aurora Global Database (with write forwarding)

### Comparison

| Aspect | Active-Passive | Active-Active |
|---|---|---|
| **Write endpoints** | 1 | Multiple |
| **Resource utilization** | ~50% (standby idle) | ~100% |
| **Failover time** | 30-60 seconds | Near-zero |
| **Write conflicts** | None | Must handle |
| **Consistency** | Strong | Eventual (cross-region) |
| **Cost** | Lower (but wasted standby) | Higher (full infra per region) |
| **Operational complexity** | Low | High |
| **Best for** | Single-region HA | Multi-region global apps |

---

## Health Checks and Heartbeats

Health checks are how the system detects failures and triggers failover.

### Database-Level Health Checks

- **TCP check** — can we connect to port 5432/3306?
- **Query check** — does `SELECT 1` return within the timeout?
- **Application check** — does a realistic query (e.g., `SELECT COUNT(*) FROM health_check_table`) succeed?
- **Replication check** — is replication lag below the threshold?

### RDS Health Monitoring

RDS uses internal health checks to detect:
- Instance unresponsiveness
- Storage failure
- Network unreachability in the primary's AZ

When the health check fails, Multi-AZ triggers automatic failover.

### Route 53 Health Checks for DNS Failover

```
  Route 53 Health Check Flow:

  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Route 53   │────►│ Health Check  │────►│  Primary     │
  │  DNS        │     │ (every 10s)  │     │  Endpoint    │
  └─────────────┘     └──────┬───────┘     └──────────────┘
                             │
                     3 consecutive failures
                             │
                             ▼
                    ┌──────────────────┐
                    │ Failover to      │
                    │ Secondary Record │
                    │ (DR endpoint)    │
                    └──────────────────┘
```

- Health checkers run from multiple AWS regions
- Configurable interval (10s or 30s) and failure threshold (1-10)
- Can check HTTP endpoints, TCP connections, or other health checks (calculated)
- Failover DNS records activate when the primary health check fails

---

## AWS HA Database Architectures

### RDS Multi-AZ (Active-Passive)

- Synchronous replication to standby in a different AZ
- Automatic failover: DNS endpoint flips (~30-60 seconds)
- Standby does **not** serve read traffic
- Zero data loss on failover (synchronous replication)
- Covers: instance failure, storage failure, AZ failure

### Aurora Multi-AZ (Active Readers)

- Shared storage layer replicated 6 ways across 3 AZs
- Up to 15 read replicas that serve read traffic
- Failover promotes a reader to writer (~30 seconds, often under 15s)
- Storage is shared — no replication lag for data durability
- Reader endpoint auto-removes failed instances

```
  Aurora Architecture:

  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  Writer  │    │ Reader 1 │    │ Reader 2 │
  │  (AZ-a)  │    │  (AZ-b)  │    │  (AZ-c)  │
  └────┬─────┘    └────┬─────┘    └────┬─────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
              ┌────────┴────────┐
              │  Shared Storage  │
              │  (6 copies,     │
              │   3 AZs)        │
              └─────────────────┘
```

### DynamoDB Global Tables (Active-Active)

- Multi-region, multi-leader replication
- Any region accepts writes with single-digit millisecond latency
- Replication lag: typically under 1 second cross-region
- Last-writer-wins conflict resolution
- No failover needed — all regions are always active
- 99.999% availability SLA

---

## DNS Failover with Route 53

Route 53 is often the outermost layer of database HA — routing traffic away from a failed region entirely.

**Failover routing policy:**
- Primary record: points to the production database endpoint
- Secondary record: points to the DR database endpoint
- Health check: monitors the primary endpoint
- On failure: Route 53 returns the secondary record

**Latency-based routing (active-active):**
- Multiple records in different regions
- Route 53 returns the lowest-latency endpoint for the user
- Failed endpoints removed via health checks
- Used with DynamoDB Global Tables or Aurora Global Database

**Weighted routing (canary deployments):**
- Gradually shift traffic between endpoints
- Useful for blue-green database migrations

---

## Common Mistakes

1. **Confusing high availability with disaster recovery** — HA handles component failures within a region (AZ outage, instance crash). DR handles regional failures or catastrophic events. You need both. RDS Multi-AZ is HA. Cross-region replication is DR.

2. **Not accounting for failover time in SLA calculations** — 99.99% uptime allows ~52 minutes of downtime per year. If your failover takes 60 seconds and happens twice, that's 2 minutes used. But if DNS TTL is 300 seconds and clients cache it, your actual downtime is much longer.

3. **Running Multi-AZ without connection retry logic** — during RDS failover, the DNS endpoint flips but existing connections break. Applications without retry logic crash. Implement exponential backoff, connection validation on checkout, and short connection timeouts.

4. **Using active-active without understanding conflict resolution** — DynamoDB Global Tables use last-writer-wins. If two regions update the same item simultaneously, one write is silently dropped. Design your data model to avoid concurrent writes to the same item, or accept LWW semantics.

5. **No regular failover testing** — use RDS reboot-with-failover in staging environments monthly. Measure actual failover time. Verify application recovery. Document the results.

---

## Interview Questions

**Q1: What is the difference between 99.9% and 99.99% availability in practical terms? When would you need four nines?**

99.9% allows ~8.77 hours of downtime per year; 99.99% allows ~52.6 minutes. The difference is whether your SLA tolerates multi-hour outages or not. Four nines is needed for customer-facing financial systems, real-time communication platforms, or services where downtime directly equals revenue loss. Most internal tools and batch systems are fine at three nines.

**Q2: Explain how RDS Multi-AZ failover works. What does the application experience during failover?**

RDS maintains a synchronous standby in another AZ. When the primary fails (detected by internal health checks), RDS promotes the standby and flips the DNS CNAME endpoint to point to it. This takes 30-60 seconds. During failover, the application experiences: broken existing connections (must reconnect), DNS propagation delay (respect TTL, use short TTLs), and a brief period of connection failures. Applications need retry logic with exponential backoff.

**Q3: When would you choose active-active over active-passive for a database?**

Active-active when you need: multi-region write latency (users in US and EU both need fast writes), near-zero RTO (no promotion delay), or maximum resource utilization. The tradeoff is conflict resolution complexity. Choose active-passive when: single-region is sufficient, strong consistency is required, or operational simplicity outweighs the 30-60 second failover gap.

**Q4: How does Aurora's storage architecture provide higher availability than standard RDS?**

Aurora replicates data 6 ways across 3 AZs at the storage layer, independently of compute. It can lose 2 copies and still write, or 3 copies and still read. Failover promotes an existing reader (which already has access to the shared storage) in ~15-30 seconds. Standard RDS Multi-AZ relies on block-level replication between two separate EBS volumes — a fundamentally different (and less resilient) architecture.

---

## Key Takeaways

- **Every additional nine of availability is exponentially harder and more expensive** — 99.9% to 99.99% is not a 0.09% improvement, it's a 10x reduction in allowed downtime. Match your target to actual business requirements.

- **Eliminate every Single Point of Failure systematically** — database, network, AZ, region, DNS. If any single component failure takes down the system, you don't have HA.

- **Active-passive is simpler and sufficient for most workloads** — RDS Multi-AZ provides 99.95% availability with zero operational overhead. Use active-active only when multi-region write latency or near-zero RTO is a hard requirement.

- **Health checks must go beyond TCP** — a database can accept connections but fail queries. Check query execution, replication lag, and disk space. Route 53 health checks should hit an application endpoint that verifies actual database health.

- **Failover without retry logic is not failover** — the database promotes in 30 seconds, but if your application crashes on broken connections and doesn't retry, users see downtime until pods restart. Implement connection validation, retry with backoff, and circuit breakers.

- **Test failover regularly in staging** — trigger RDS failover monthly. Measure actual downtime. Verify application reconnection. Compare against your SLA commitments. Untested HA is a false guarantee.
