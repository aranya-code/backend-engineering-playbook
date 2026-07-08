# Backup & Recovery

Backups are your last line of defense. Replication protects against hardware failure. Backups protect against **everything else** — accidental deletes, bad migrations, ransomware, corruption, and the intern who ran `DROP TABLE users` in production.

A backup you haven't restored is not a backup. It's a hope.

---

## Backup Types

### Full Backups

A complete copy of the entire database at a point in time. Self-contained — you can restore from a single full backup without any dependencies.

**Pros:** Simple restore, no dependency chain.
**Cons:** Slow to create, large storage footprint, heavy I/O impact on the source.

### Incremental Backups

Captures only the data that changed since the last backup (full or incremental). Restoring requires the base full backup plus every incremental in sequence.

**Pros:** Fast to create, minimal storage per backup.
**Cons:** Restore requires the full chain — one broken link and recovery fails.

### Transaction Log Backups (WAL Archiving)

Continuously archive the write-ahead log (WAL) to durable storage. Combined with a base backup, you can replay transactions to recover to **any point in time**.

```
  Full Backup          WAL Segments (continuous)
  ┌─────────┐    ┌────┬────┬────┬────┬────┬────┐
  │ Base     │ +  │ W1 │ W2 │ W3 │ W4 │ W5 │ W6 │
  │ Snapshot │    └────┴────┴────┴────┴────┴────┘
  └─────────┘         │              ▲
   Day 1              │    Restore to here
                      │    (replay W1-W4)
                      └──── Point-in-Time Recovery
```

This is how PostgreSQL PITR, MySQL binary log recovery, and RDS automated backups work.

### Comparison

| Type | Size | Creation Speed | Restore Speed | Granularity |
|---|---|---|---|---|
| Full | Large | Slow | Fast (single file) | Snapshot-level |
| Incremental | Small | Fast | Slow (chain replay) | Snapshot-level |
| WAL/Transaction Log | Continuous | Minimal overhead | Moderate (replay) | Any point in time |

---

## Point-in-Time Recovery (PITR)

PITR lets you restore a database to **any second** within the retention window. It works by combining a base snapshot with WAL replay.

**How RDS PITR works:**
1. RDS takes automated daily snapshots
2. RDS continuously archives transaction logs to S3 (every 5 minutes)
3. You specify a target timestamp
4. RDS restores the nearest snapshot before that timestamp
5. RDS replays WAL segments up to the exact target time
6. A new RDS instance is created with the recovered data

**Critical detail:** PITR creates a **new** instance. It does not restore in-place. You must update your application's connection string to point to the new instance, or rename it to match the old endpoint.

---

## RPO and RTO

These two metrics define your disaster recovery requirements. Every conversation about backups starts here.

```
        RPO                              RTO
  ◄──────────────────►          ◄──────────────────►

  Last Backup          Disaster           Recovery
  ┌─────────┐          ┌─────┐            ┌─────────┐
  │ Data     │          │  X  │            │ Service  │
  │ Saved    │          │FAIL │            │ Restored │
  └─────────┘          └─────┘            └─────────┘

  RPO = Maximum data you can afford to lose
  RTO = Maximum time to restore service
```

| Metric | Definition | Question It Answers |
|---|---|---|
| **RPO** (Recovery Point Objective) | Maximum acceptable data loss measured in time | "How much data can we lose?" |
| **RTO** (Recovery Time Objective) | Maximum acceptable downtime | "How long can we be down?" |

**Typical targets by tier:**

| Tier | RPO | RTO | Strategy |
|---|---|---|---|
| Tier 1 (Critical) | Near-zero | < 1 minute | Multi-site active-active |
| Tier 2 (Important) | < 5 minutes | < 30 minutes | Warm standby |
| Tier 3 (Standard) | < 1 hour | < 4 hours | Pilot light |
| Tier 4 (Non-critical) | < 24 hours | < 24 hours | Backup & restore |

---

## Backup Strategy: The 3-2-1 Rule

```
  ┌─────────────────────────────────────────┐
  │              3-2-1 Rule                 │
  │                                         │
  │   3 copies of your data                 │
  │   ├── Primary database                  │
  │   ├── Local backup (same region)        │
  │   └── Remote backup (different region)  │
  │                                         │
  │   2 different storage types             │
  │   ├── EBS snapshots                     │
  │   └── S3 cross-region copy              │
  │                                         │
  │   1 copy offsite (different region)     │
  │   └── Cross-region snapshot copy        │
  └─────────────────────────────────────────┘
```

For AWS databases, this translates to:
- **Copy 1:** Live database (primary RDS instance)
- **Copy 2:** RDS automated backup (same region, S3-backed)
- **Copy 3:** Cross-region snapshot copy (different region, automated via AWS Backup or Lambda)

---

## RDS Backup Mechanisms

### Automated Backups

- Daily full snapshot during the backup window
- Transaction logs archived to S3 every 5 minutes
- Retention: 1-35 days (default: 7)
- Enables PITR to any second within retention window
- Slight I/O impact during backup window on single-AZ instances
- **Deleted when the RDS instance is deleted** (unless final snapshot is taken)

### Manual Snapshots

- User-initiated full snapshots
- Persist **indefinitely** — not tied to instance lifecycle
- Not automatically deleted when instance is deleted
- Use for: pre-migration snapshots, long-term retention, compliance archives

### Cross-Region Snapshot Copy

- Copy manual or automated snapshots to another AWS region
- Provides geographic redundancy for disaster recovery
- Can be automated via AWS Backup or custom Lambda
- Encrypted snapshots can be copied cross-region (re-encrypted with destination region KMS key)

### Backup Encryption

- RDS backups inherit the encryption setting of the source instance
- Encrypted instances produce encrypted snapshots (AES-256, AWS KMS)
- **You cannot create an unencrypted snapshot of an encrypted instance**
- To encrypt an unencrypted instance: snapshot → copy with encryption → restore from encrypted copy

---

## Disaster Recovery Tiers

```
  Cost ▲
       │                                    ┌──────────────┐
       │                                    │ Multi-Site   │
       │                                    │ Active-Active│
       │                                    │ RPO: ~0      │
       │                                    │ RTO: ~0      │
       │                          ┌─────────┤              │
       │                          │ Warm    └──────────────┘
       │                          │ Standby
       │                          │ RPO: mins
       │                          │ RTO: mins
       │               ┌─────────┤
       │               │ Pilot   └─────────┘
       │               │ Light
       │               │ RPO: mins
       │               │ RTO: 10s of mins
       │    ┌──────────┤
       │    │ Backup & └──────────┘
       │    │ Restore
       │    │ RPO: hours
       │    │ RTO: hours
       │    │
       └────┴──────────────────────────────────────► Recovery Speed
```

### Tier 1: Backup & Restore

- **What:** Cross-region snapshot copies. Restore from snapshot when disaster occurs.
- **RPO:** Hours (time since last snapshot)
- **RTO:** Hours (snapshot restore + data replay + DNS update)
- **Cost:** Lowest — storage costs only
- **Use:** Dev/test environments, non-critical workloads

### Tier 2: Pilot Light

- **What:** Core database replicated to DR region, but application infrastructure is off. Spin up compute on demand.
- **RPO:** Minutes (async replication lag)
- **RTO:** Tens of minutes (start application servers, update DNS)
- **Cost:** Low — database replication + minimal standby infra
- **Use:** Internal tools, batch processing systems

### Tier 3: Warm Standby

- **What:** Scaled-down replica of full production running in DR region. Scale up on failover.
- **RPO:** Minutes (async replication)
- **RTO:** Minutes (scale up existing infra, update DNS)
- **Cost:** Moderate — running infrastructure at reduced capacity
- **Use:** Customer-facing applications with moderate SLAs

### Tier 4: Multi-Site Active-Active

- **What:** Full production stack in multiple regions, serving live traffic simultaneously.
- **RPO:** Near-zero (synchronous or fast async replication)
- **RTO:** Near-zero (traffic shifts via DNS/load balancer)
- **Cost:** Highest — full infrastructure in multiple regions
- **Use:** Mission-critical systems, financial platforms, global SaaS

---

## Common Mistakes

1. **Never testing restores** — a backup you've never restored is a file, not a backup. Schedule quarterly restore drills. Measure actual RTO. Compare against your SLA.

2. **Relying on replication as backup** — replication propagates deletes and corruption instantly. `DROP TABLE` on the leader is `DROP TABLE` on every replica. Backups and PITR are your only protection against logical errors.

3. **Forgetting that RDS automated backups are deleted with the instance** — delete an RDS instance without a final snapshot and your backup history is gone. Always take a final snapshot or use manual snapshots for retention beyond the instance lifecycle.

4. **Setting RPO/RTO targets without measuring actual recovery time** — claiming 1-hour RTO but never testing a restore is dishonest. Actual restore times include: snapshot restore, WAL replay, DNS propagation, connection pool warmup, and cache rebuild.

5. **No cross-region backup for single-region deployments** — a regional outage takes out your database and all your backups. Cross-region snapshot copies cost pennies compared to the cost of total data loss.

---

## Interview Questions

**Q1: What is the difference between RPO and RTO? Give a real-world example of each.**

RPO is maximum acceptable data loss (measured in time). RTO is maximum acceptable downtime. Example: an e-commerce platform sets RPO = 5 minutes (can lose at most 5 minutes of orders) and RTO = 30 minutes (must be serving traffic again within 30 minutes). RPO drives backup frequency; RTO drives infrastructure readiness.

**Q2: Your team runs RDS PostgreSQL with automated backups. Someone accidentally drops a critical table at 2:15 PM. Walk through the recovery process.**

Use PITR. RDS has daily snapshots and WAL archived every 5 minutes. Initiate a point-in-time restore targeting 2:14 PM (one minute before the DROP). RDS creates a new instance from the nearest snapshot before 2:14 PM, then replays WAL to that exact timestamp. Once the new instance is available, extract the dropped table's data and import it back into the primary, or redirect the application to the new instance.

**Q3: Why is replication not a substitute for backups?**

Replication copies every operation — including destructive ones. A `DELETE FROM users WHERE 1=1` replicates to every follower instantly. Corruption replicates. Ransomware encryption replicates. Backups (especially PITR) let you go back to a point before the destructive event. They protect against logical errors and human mistakes that replication faithfully propagates.

**Q4: Explain the 3-2-1 backup rule and how you'd implement it on AWS.**

Three copies of data, on two different storage types, with one copy offsite. On AWS: (1) primary RDS instance is copy one, (2) RDS automated backups to S3 in the same region is copy two on a different storage medium, (3) cross-region snapshot copy to a second AWS region is the offsite copy. Automate cross-region copies with AWS Backup or a scheduled Lambda.

---

## Key Takeaways

- **PITR is your most powerful recovery tool** — it restores to any second within the retention window by combining base snapshots with WAL replay. RDS archives WAL every 5 minutes automatically.

- **RPO and RTO define your recovery requirements** — every backup and DR conversation starts with these numbers. Set them based on business impact, then design infrastructure to meet them.

- **Replication is not backup** — replication propagates destructive operations. Backups protect against logical errors, accidental deletes, and corruption that replication faithfully copies.

- **Test your restores quarterly** — measure actual RTO including snapshot restore, WAL replay, DNS propagation, and cache warmup. Compare against your SLA.

- **Follow the 3-2-1 rule** — three copies, two storage types, one offsite. Cross-region snapshot copies are cheap insurance against regional failures.

- **RDS automated backups die with the instance** — always take a final snapshot before deleting an RDS instance. Use manual snapshots for retention beyond the instance lifecycle.
