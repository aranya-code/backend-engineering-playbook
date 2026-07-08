# Multi-AZ vs Read Replica

Two RDS features that solve completely different problems. **Multi-AZ** is about high availability — surviving an AZ failure without data loss. **Read Replicas** are about read scaling — offloading read traffic from the primary. They are not interchangeable. They are complementary. Production databases should use both.

---

## Purpose

**Multi-AZ: High Availability**
A synchronous standby replica in a different Availability Zone. Its only job is to take over if the primary fails. You cannot read from it (exception: Aurora, where replicas serve reads). It exists to minimize downtime — RDS automatically fails over in 60-120 seconds by flipping the DNS CNAME.

**Read Replica: Read Scaling**
An asynchronous copy of the primary that serves read traffic. It has its own endpoint. Applications connect to it directly for read queries. It reduces load on the primary so the primary can handle more writes. Read Replicas can also be promoted to standalone databases for migration or disaster recovery — but this is a manual, irreversible operation.

---

## Replication Mechanism

**Multi-AZ: Synchronous Replication**
Every write to the primary is simultaneously written to the standby before the transaction is acknowledged to the client. This guarantees zero data loss (RPO = 0) during failover. The trade-off is slightly higher write latency — each write waits for confirmation from two AZs.

```
Write Flow (Multi-AZ):

Client → Primary (AZ-a) ──sync──→ Standby (AZ-b)
                │                        │
                ├── Write to EBS ────────├── Write to EBS
                │                        │
                └── ACK to client ◄──────┘
                    (only after BOTH confirm)
```

**Read Replica: Asynchronous Replication**
The primary streams its write-ahead log (WAL/binlog) to replicas asynchronously. The primary doesn't wait for replicas to confirm. This means replicas may lag behind — typically by milliseconds to seconds, but under heavy write load, lag can grow to minutes. Monitor `ReplicaLag` in CloudWatch.

```
Write Flow (Read Replica):

Client → Primary (AZ-a) ──async──→ Replica 1 (AZ-a)
                │                  Replica 2 (AZ-b)
                │                  Replica 3 (AZ-c)
                │
                └── ACK to client
                    (immediately after primary confirms)
```

---

## Standby Behavior

**Multi-AZ Standby: Passive**
The standby instance is not accessible for any workload. You cannot connect to it. You cannot run queries against it. It has no endpoint. It is invisible to your application. It only activates during failover. Think of it as a hot spare sitting in a locked room.

Exception: **Multi-AZ with two readable standbys** (Aurora and RDS Multi-AZ DB Cluster) — these use a newer architecture with two reader instances that ARE queryable. This is the hybrid approach AWS introduced for RDS in 2022.

**Read Replica: Active and Readable**
Each replica has its own endpoint. Applications can send SELECT queries to it. You can have up to 5 read replicas per RDS instance (Aurora supports up to 15). Each replica can be in a different AZ or even a different Region for geographic read distribution.

---

## Failover

**Multi-AZ: Automatic DNS Failover**
When the primary fails, RDS flips the DNS CNAME to point to the standby. The standby becomes the new primary. No data loss. No manual intervention. Downtime is 60-120 seconds (RDS) or typically under 30 seconds (Aurora). Your application reconnects using the same endpoint — the DNS change is transparent.

```
Before Failover:
  app.cluster.endpoint → Primary (AZ-a) ✓
                         Standby (AZ-b) [passive]

Primary fails:
  app.cluster.endpoint → Primary (AZ-a) ✗ DOWN
                         Standby (AZ-b) [passive]

After Failover (60-120s):
  app.cluster.endpoint → New Primary (AZ-b) ✓
                         [old primary removed/recovered]
```

**Read Replica: Manual Promotion**
If you need to promote a Read Replica to a standalone primary, it's a manual API call (`promote-read-replica`). This breaks the replication link permanently — the replica becomes an independent database. It is NOT automatic. It is NOT reversible. Use this for disaster recovery when the primary region is down, or for blue/green deployments.

```
Before Promotion:
  Primary (us-east-1) ──async──→ Replica (eu-west-1)

After Promotion (manual):
  Primary (us-east-1)            New Primary (eu-west-1)
  [no longer connected]          [independent database]
```

---

## Backups

**Multi-AZ: Backups from Standby**
RDS takes automated snapshots and backups from the standby instance, not the primary. This eliminates I/O suspension on the primary during backup windows. Your application sees zero performance impact from backups. This is one of the hidden operational benefits of Multi-AZ that often gets overlooked.

**Read Replica: Backups from Primary**
Without Multi-AZ, backups are taken from the primary. For single-AZ deployments, this can cause brief I/O suspension (especially on MySQL). You can enable backups on a Read Replica, but this is engine-dependent and adds operational overhead.

---

## Cost

**Multi-AZ**
You pay for a second instance (standby) at the same instance class as the primary. It doubles your compute cost. Storage is replicated across AZs — EBS charges apply for both. There is no data transfer charge between AZs for synchronous replication within the same region.

**Read Replica**
Each replica is a separate billable instance. You choose the instance class independently — replicas can be smaller than the primary if they handle lighter workloads. Cross-region replicas incur data transfer charges for the replication stream. Same-region replicas have no data transfer cost.

---

## Cross-Region Capability

| Feature | Multi-AZ | Read Replica |
|---------|----------|--------------|
| Same-Region | Yes (default) | Yes |
| Cross-Region | No (Multi-AZ is intra-region only) | Yes (cross-region read replicas) |
| Cross-Region HA | Use Aurora Global Database instead | Promote replica in DR region |

Multi-AZ is strictly within a single region (across AZs). For cross-region disaster recovery, you need either Read Replicas in another region (with manual promotion) or Aurora Global Database (with managed failover under 1 minute, RPO of ~1 second).

---

## Can You Have Both? YES.

This is the production-grade architecture. Multi-AZ handles high availability. Read Replicas handle read scaling. They operate independently and complement each other.

```
Production Architecture: Multi-AZ + Read Replicas

                    ┌──────────────────────────────────────────┐
                    │              Same Region                 │
                    │                                          │
   Writes ─────►   │  ┌─────────┐    sync    ┌─────────┐     │
                    │  │ Primary │ ──────────►│ Standby │     │
   Reads  ─────►   │  │ (AZ-a)  │            │ (AZ-b)  │     │
      │             │  └────┬────┘            └─────────┘     │
      │             │       │ async                           │
      │             │       ├──────────────┐                  │
      │             │       ▼              ▼                  │
      │             │  ┌─────────┐    ┌─────────┐            │
      └────────────►│  │Replica 1│    │Replica 2│            │
                    │  │ (AZ-a)  │    │ (AZ-c)  │            │
                    │  └─────────┘    └─────────┘            │
                    │                                          │
                    └──────────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │            DR Region                     │
                    │                                          │
                    │  ┌─────────────────┐                    │
                    │  │ Cross-Region    │                    │
                    │  │ Read Replica    │ ◄── async from     │
                    │  │ (promote in DR) │    primary         │
                    │  └─────────────────┘                    │
                    └──────────────────────────────────────────┘
```

**Aurora simplifies this further.** Every Aurora replica can serve reads AND acts as a failover target. There is no separate "standby" — replicas ARE the standby. Aurora with 3 replicas across 3 AZs gives you both HA and read scaling in one architecture.

---

## Detailed Comparison Table

| Dimension | Multi-AZ | Read Replica |
|-----------|----------|--------------|
| Purpose | High availability (HA) | Read scaling |
| Replication | Synchronous | Asynchronous |
| Data Loss on Failover | Zero (RPO = 0) | Possible (depends on replica lag) |
| Failover | Automatic DNS flip (60-120s) | Manual promotion (irreversible) |
| Standby Accessible | No (passive standby) | Yes (active, queryable) |
| Endpoint | Same as primary (DNS CNAME) | Separate read endpoint |
| Max Count (RDS) | 1 standby (or 2 readable standbys) | Up to 5 per source |
| Max Count (Aurora) | Up to 15 (all are failover targets) | Up to 15 (same replicas) |
| Cross-Region | No | Yes |
| Backups From | Standby (no primary I/O impact) | Primary (unless replica backups enabled) |
| Cost | 2x compute (standby instance) | Per-replica instance cost |
| Use Case | Survive AZ failure | Offload read-heavy workloads |
| Promotion | Automatic (failover) | Manual (`promote-read-replica`) |
| Replication Lag | None (synchronous) | Milliseconds to minutes |

---

## Interview-Ready Explanation

> "Multi-AZ and Read Replicas solve different problems. Multi-AZ is for high availability — a synchronous standby in another AZ that takes over automatically in 60-120 seconds with zero data loss. You can't read from it; it's a passive hot spare. Read Replicas are for read scaling — asynchronous copies with their own endpoints that serve read traffic. They can be in different AZs or different regions, and you can manually promote them for disaster recovery. In production, you use both: Multi-AZ for HA within a region, Read Replicas for distributing read load, and a cross-region Read Replica for DR. Aurora simplifies this because every Aurora replica is both a read endpoint and a failover target — there's no separate standby concept. An Aurora cluster with 3 replicas across 3 AZs gives you HA, read scaling, and fast failover (typically under 30 seconds) in one architecture."

---

## Key Takeaways

1. **Multi-AZ = HA, Read Replica = scaling** — they solve different problems and should both be used in production
2. **Synchronous vs asynchronous** — Multi-AZ guarantees zero data loss, Read Replicas may lag behind
3. **Passive vs active** — Multi-AZ standby is invisible to your app, Read Replicas have their own endpoints
4. **Automatic vs manual failover** — Multi-AZ flips DNS automatically, Read Replica promotion is a manual irreversible operation
5. **Backups from standby** — Multi-AZ eliminates backup I/O impact on the primary, a frequently overlooked benefit
6. **Aurora changes the game** — replicas serve reads AND are failover targets, eliminating the Multi-AZ vs Read Replica dichotomy
7. **Cross-region DR** — Multi-AZ is intra-region only. Use cross-region Read Replicas or Aurora Global Database for regional disaster recovery
8. **Monitor ReplicaLag** — asynchronous replication lag is the silent killer. Set CloudWatch alarms on `ReplicaLag` for all Read Replicas
