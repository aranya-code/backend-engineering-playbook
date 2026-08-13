# Disaster Recovery for Databases on AWS

Disaster recovery is not optional — it is a business requirement. Every production database must have a documented, tested DR plan. The question is never "will a failure happen?" but "when it happens, how fast can you recover and how much data can you afford to lose?"

---

## DR vs High Availability

These two concepts are frequently conflated. They solve different problems.

**High Availability (HA)** prevents downtime. It uses redundancy within a single region — Multi-AZ deployments, read replicas, automatic failover. HA handles hardware failures, AZ outages, and routine maintenance without human intervention.

**Disaster Recovery (DR)** recovers from catastrophic failures. It assumes the entire primary environment is gone — region-wide outage, data corruption propagated to replicas, or accidental mass deletion. DR requires a separate recovery environment, usually in another AWS region.

```
  HA (Same Region)                    DR (Cross-Region)
  ┌─────────────────────┐             ┌─────────────────────┐
  │   Region: us-east-1 │             │   Region: us-east-1 │
  │  ┌───────┐ ┌───────┐│             │  ┌───────┐          │
  │  │Primary│→│Standby││             │  │Primary│──────────┼──→ us-west-2
  │  │  AZ-a │ │  AZ-b ││             │  │  AZ-a │          │    (Recovery)
  │  └───────┘ └───────┘│             │  └───────┘          │
  │  Automatic Failover  │             │  Manual/Auto Switch │
  └─────────────────────┘             └─────────────────────┘
  Handles: AZ failure,                Handles: Region failure,
  instance crash, patching            data corruption, regional disaster
```

HA is your first line of defense. DR is your last resort. You need both.

---

## RPO and RTO

Two metrics define every DR plan:

| Metric | Definition | Question It Answers |
|--------|-----------|---------------------|
| **RPO** (Recovery Point Objective) | Maximum acceptable data loss measured in time | "How much data can we lose?" |
| **RTO** (Recovery Time Objective) | Maximum acceptable downtime | "How long can we be down?" |

An RPO of 1 hour means you accept losing up to 1 hour of transactions. An RTO of 30 minutes means the application must be serving traffic within 30 minutes of failure detection.

**RPO drives your replication strategy.** Zero RPO requires synchronous replication. Minutes of RPO allows asynchronous replication. Hours of RPO allows periodic backups.

**RTO drives your infrastructure readiness.** Zero RTO requires hot standby infrastructure. Minutes of RTO requires warm infrastructure. Hours of RTO allows cold provisioning from backups.

---

## The Four DR Strategies on AWS

```
  Cost $$$$  │                                          ● Multi-Site
             │                                         ╱  Active-Active
             │                                        ╱
             │                              ● Warm  ╱
             │                             ╱ Standby
             │                            ╱
             │                  ● Pilot  ╱
             │                 ╱  Light
             │                ╱
             │    ● Backup  ╱
             │     & Restore
  Cost $     │──────────────────────────────────────────────
             Hours          Minutes        Seconds    ~Zero
                              RTO →
```

### 1. Backup & Restore

- **RPO**: Hours | **RTO**: Hours | **Cost**: $
- Take periodic snapshots of RDS, export DynamoDB tables, replicate S3 backups to another region
- On disaster: provision new infrastructure from backups in the DR region
- Cheapest option but slowest recovery — suitable for non-critical workloads

### 2. Pilot Light

- **RPO**: Minutes | **RTO**: Tens of minutes | **Cost**: $$
- Core database infrastructure runs continuously in the DR region (e.g., RDS cross-region read replica)
- Application servers and supporting services are pre-configured but not running
- On disaster: promote read replica, scale up application tier, update DNS

### 3. Warm Standby

- **RPO**: Seconds | **RTO**: Minutes | **Cost**: $$$
- Fully functional but scaled-down copy of production runs in the DR region
- Database replication is continuous with minimal lag
- On disaster: scale up the DR environment and redirect traffic

### 4. Multi-Site Active-Active

- **RPO**: ~0 | **RTO**: ~0 | **Cost**: $$$$
- Both regions actively serve traffic simultaneously
- Database writes happen in both regions with conflict resolution
- On disaster: DNS removes the failed region — remaining region absorbs full load

---

## AWS Database DR Mechanisms

### RDS Cross-Region Read Replicas

Asynchronous replication to a different region. Replica can be promoted to standalone primary during DR. Replication lag is typically seconds but can spike under heavy write load. Promotion takes 5-10 minutes.

### Aurora Global Database

Purpose-built for cross-region DR. Uses dedicated replication infrastructure separate from the database engine. Typical replication lag under 1 second. Managed cross-region failover with RPO of 1 second and RTO under 1 minute. Supports up to 5 secondary regions.

### DynamoDB Global Tables

Multi-region, multi-active replication. Writes in any region propagate to all other regions within seconds. Last-writer-wins conflict resolution. No manual failover needed — application reads/writes from the nearest region.

### S3 Cross-Region Replication (CRR)

Replicate backup files, exports, and snapshots to a DR region. Enable versioning and replication rules on source bucket. Replication is asynchronous — typically completes within 15 minutes for most objects.

| Service | DR Mechanism | Replication Lag | Failover Time | Effort |
|---------|-------------|-----------------|---------------|--------|
| RDS | Cross-region read replica | Seconds (variable) | 5-10 min (manual promote) | Medium |
| Aurora | Global Database | < 1 second | < 1 min (managed) | Low |
| DynamoDB | Global Tables | ~1 second | Automatic (multi-active) | Low |
| S3 | Cross-Region Replication | Minutes | N/A (backup target) | Low |

---

## Real-World Runbook: Primary Region Failure

This is what your on-call engineer executes when `us-east-1` goes down.

```
INCIDENT: Primary Region Failure — DR Activation Runbook

1. DETECT (0-5 min)
   ├── CloudWatch cross-region health checks trigger alarm
   ├── Route 53 health checks fail for primary endpoints
   └── PagerDuty alerts on-call engineer

2. ASSESS (5-10 min)
   ├── Confirm region-wide outage (not just one service)
   ├── Check AWS Health Dashboard for official status
   └── Decision: ACTIVATE DR — notify incident commander

3. DATABASE FAILOVER (10-20 min)
   ├── Aurora Global DB: Initiate managed failover via CLI
   │   aws rds failover-global-cluster --global-cluster-identifier my-global-cluster \
   │       --target-db-cluster-identifier arn:aws:rds:us-west-2:...:cluster:my-dr-cluster
   ├── RDS: Promote cross-region read replica
   │   aws rds promote-read-replica-db-cluster --db-cluster-identifier my-dr-replica
   ├── DynamoDB Global Tables: No action — already multi-active
   └── Verify: Run read/write tests against DR databases

4. APPLICATION FAILOVER (20-30 min)
   ├── Update application config to point at DR database endpoints
   ├── Scale up DR application tier (if warm standby)
   └── Run smoke tests against DR application

5. TRAFFIC SWITCH (30-35 min)
   ├── Update Route 53 to point at DR region
   └── Monitor error rates and latency

6. POST-FAILOVER (ongoing)
   ├── Monitor for data consistency issues
   ├── Plan failback once primary region recovers
   └── Write post-incident review
```

---

## Common Mistakes

1. **Never testing DR.** A DR plan that has never been executed is a hope, not a plan. Run GameDay exercises quarterly at minimum.
2. **Forgetting the application layer.** Failing over the database is useless if application config, secrets, and DNS still point to the dead region.
3. **Ignoring replication lag.** Cross-region read replicas can have minutes of lag under load. If you assume zero lag, you will lose data.
4. **No runbook.** During a real outage, engineers are stressed and making mistakes. Every DR step must be scripted and documented — ideally automated.
5. **Skipping RPO/RTO agreements.** Without agreed-upon RPO/RTO from the business, engineering teams guess — and usually guess wrong.

---

## Interview Questions

**Q1: Your RDS cross-region read replica shows 45 seconds of replication lag during peak hours. The business requires an RPO of 10 seconds. What do you do?**

Migrate to Aurora Global Database, which provides dedicated replication infrastructure with sub-second lag. RDS cross-region replicas use standard async replication that shares I/O with the primary workload and cannot guarantee low lag under heavy write load.

**Q2: You run a DynamoDB Global Table across us-east-1 and eu-west-1. Both regions receive writes to the same item simultaneously. What happens?**

DynamoDB Global Tables use last-writer-wins conflict resolution based on timestamps. The write with the later timestamp prevails. If your application requires stricter conflict handling, you must implement application-level conflict detection using conditional writes or versioning.

**Q3: Your company runs a Pilot Light DR setup. During a DR test, the promoted database comes up but the application shows stale data from 2 hours ago. What went wrong?**

The cross-region replica was likely lagging significantly, or automated backups were being used instead of continuous replication. Investigate `ReplicaLag` CloudWatch metrics. For Pilot Light, you must have continuous replication — not periodic snapshot restores — and you must monitor replication health as a production metric.

---

## Key Takeaways

- **HA prevents downtime within a region; DR recovers from regional or catastrophic failures.** You need both, and they require separate engineering effort.
- **RPO and RTO are business decisions, not engineering decisions.** Get sign-off from stakeholders before choosing a DR tier.
- **Aurora Global Database is the most cost-effective DR option for relational workloads** — sub-second RPO, sub-minute RTO, with managed failover.
- **DynamoDB Global Tables provide the simplest DR story** — multi-active by design with no manual failover required.
- **Test your DR plan regularly.** Schedule quarterly GameDay exercises. A plan that works on paper but fails in practice is worthless.
- **Automate every DR step.** Manual runbooks are error-prone under pressure. Use AWS Lambda, Step Functions, or SSM Automation to codify failover procedures.
