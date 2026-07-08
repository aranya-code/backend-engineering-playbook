# RDS vs Database on EC2

Managed vs self-managed is the single most consequential database decision you make on AWS. It dictates your operational burden, your blast radius during incidents, and how your on-call engineers spend their weekends. Get this wrong and you either pay the RDS premium for nothing or drown in undifferentiated heavy lifting.

---

## Shared Responsibility Model

The core difference is **who owns the ops**. RDS shifts the entire infrastructure stack to AWS. EC2 shifts it to you.

```
┌─────────────────────────────────────────────────────┐
│              RESPONSIBILITY LAYERS                  │
├─────────────────────┬───────────────────────────────┤
│        RDS          │       Database on EC2         │
├─────────────────────┼───────────────────────────────┤
│  YOU: App queries,  │  YOU: Everything below        │
│  schema design,     │                               │
│  query tuning,      │  - Application queries        │
│  connection mgmt,   │  - Schema design              │
│  parameter groups   │  - Query optimization         │
│                     │  - Connection management       │
│                     │  - DB engine install/config    │
│                     │  - Patch management            │
│  AWS: Everything    │  - Backup/restore scripts     │
│  below              │  - Replication setup           │
│                     │  - HA/failover automation      │
│  - Engine patching  │  - Monitoring/alerting         │
│  - OS patching      │  - OS hardening                │
│  - Automated backup │  - OS patching                 │
│  - Multi-AZ HA      │  - Security groups/NACLs       │
│  - Monitoring       │  - Storage management          │
│  - Storage mgmt     │  - Encryption at rest/transit  │
│  - Host maintenance │  - Host-level monitoring       │
│  - Hardware repair  │                               │
│  - Encryption setup │  AWS: EC2 instance,            │
│                     │  hypervisor, physical host,    │
│                     │  network, data center          │
└─────────────────────┴───────────────────────────────┘
```

**What RDS manages for you:**
- Automated daily snapshots with configurable retention (1-35 days)
- Engine version patching within maintenance windows
- OS-level security patches (invisible to you)
- Multi-AZ synchronous replication and automatic failover
- Read replica creation and management
- Storage autoscaling (up to 64 TiB)
- CloudWatch metrics, Enhanced Monitoring, Performance Insights
- Encryption at rest (KMS) and in transit (SSL/TLS)

**What you manage on EC2:**
- Database engine installation, configuration, and version upgrades
- Backup scripts (pg_dump, mysqldump, xtrabackup), retention, and restore testing
- Replication setup (streaming replication, GTID, log shipping)
- Failover automation (custom scripts, Pacemaker, Patroni, Orchestrator)
- OS patching cadence, kernel tuning, filesystem selection (ext4 vs XFS)
- Monitoring stack (Prometheus, Grafana, custom CloudWatch metrics)
- Security hardening (CIS benchmarks, audit logging, firewall rules)
- Storage management (EBS snapshots, RAID, IOPS provisioning)

---

## When to Choose EC2

EC2 is not the default choice. You pick EC2 when RDS physically cannot do what you need:

- **OS-level access required** — kernel parameter tuning (`vm.swappiness`, `transparent_hugepages`), custom shared libraries, OS-level audit daemons (auditd, OSSEC)
- **Unsupported engine** — IBM Db2, Informix, InterSystems Caché, TimeScaleDB (as a full extension), ClickHouse, CockroachDB
- **Custom replication topology** — multi-source replication, circular replication, delayed replicas for point-in-time rollback, custom conflict resolution
- **Compliance mandates** — regulations requiring full OS-level audit trails, specific hardening baselines (STIG, CIS), or on-instance encryption tooling
- **Version pinning** — need a specific minor version or a custom-compiled engine with patches not yet in RDS
- **Performance edge cases** — need local NVMe instance storage (i3/i3en) for ephemeral high-IOPS workloads, or bare metal instances for licensing

If none of these apply, use RDS. The operational burden of EC2 databases is substantial and often underestimated.

---

## Detailed Comparison Table

| Feature | RDS | Database on EC2 |
|---|---|---|
| **Provisioning** | Console/CLI/CloudFormation, minutes | Manual install or AMI bake, hours |
| **Engine patching** | Automated in maintenance window | Manual, you schedule and execute |
| **OS patching** | AWS-managed, transparent | Your responsibility entirely |
| **Automated backups** | Built-in, 1-35 day retention | Custom scripts (pg_dump, xtrabackup) |
| **Point-in-time recovery** | Native, 5-min granularity | Only if you set up WAL archiving |
| **Multi-AZ HA** | One checkbox, sync replication | Patroni/Pacemaker/custom scripting |
| **Failover time** | 60-120 seconds automatic | Depends on your automation quality |
| **Read replicas** | Native, up to 5 (15 Aurora) | Manual streaming replication setup |
| **Monitoring** | CloudWatch + Performance Insights | Self-managed (Prometheus/Datadog) |
| **Encryption at rest** | KMS integration, one setting | Manual LUKS/dm-crypt or EBS encryption |
| **Encryption in transit** | SSL/TLS toggle | Manual cert management |
| **Storage scaling** | Autoscaling up to 64 TiB | Manual EBS resize + filesystem extend |
| **Instance scaling** | Modify instance class | Stop, change type, start |
| **OS access** | None (no SSH) | Full root access |
| **Engine choice** | MySQL, PostgreSQL, MariaDB, Oracle, SQL Server | Any engine that runs on Linux/Windows |
| **Parameter tuning** | Parameter groups (subset exposed) | Full config file access |
| **Custom extensions** | Limited set per engine | Install anything |
| **Networking** | VPC, security groups, no public by default | Full VPC, ENI, security group control |
| **IAM integration** | IAM DB authentication native | Manual IAM-to-DB mapping |
| **Maintenance windows** | Configurable, AWS-managed | Entirely your scheduling |

---

## Cost Comparison

**RDS costs more per-instance but less in total cost of ownership (TCO).**

```
RDS Instance Cost Breakdown:
  db.r6g.xlarge (Multi-AZ): ~$0.96/hr = ~$700/mo
  Equivalent EC2:           ~$0.40/hr = ~$290/mo
  RDS premium:              ~$410/mo  (~60% more for Multi-AZ)
```

But the EC2 TCO includes hidden costs:

| Cost Category | RDS | EC2 |
|---|---|---|
| Instance compute | Included (premium) | Lower base price |
| DBA operational time | Minimal | 10-20 hrs/mo per instance |
| Backup tooling | Included | Build/maintain scripts |
| Monitoring stack | Performance Insights free tier | Prometheus/Grafana infra |
| On-call incidents | Rare (AWS-managed infra) | Frequent (your problem) |
| Failover testing | Built-in | Manual runbook + drills |
| Compliance auditing | Managed certifications | Document everything yourself |
| **Estimated TCO** | **$700-900/mo** | **$800-1500/mo** |

The break-even point shifts in EC2's favor only at large scale (50+ instances) where dedicated DBA teams amortize their cost, or when RDS simply cannot support your requirements.

---

## Interview-Ready Explanation

> "RDS is a managed relational database service that handles provisioning, patching, backups, and high availability. You give up OS-level access in exchange for AWS managing the undifferentiated heavy lifting. I'd choose EC2 only when I need OS access for kernel tuning, need an unsupported engine, or have compliance requirements mandating full stack control. In practice, RDS covers 90%+ of relational workloads. The ~20-30% price premium pays for itself many times over in reduced operational burden and on-call fatigue."

---

## Key Takeaways

- **Default to RDS** unless you have a specific, documented reason requiring EC2
- RDS eliminates 80% of database operational work — patching, backups, HA, monitoring
- EC2 gives full control but demands a mature DBA practice and 24/7 operational readiness
- The RDS price premium is typically offset by reduced DBA hours and fewer incidents
- Multi-AZ RDS provides automatic failover in 60-120 seconds — replicating this on EC2 requires significant engineering investment
- EC2 is justified for unsupported engines, OS-level compliance mandates, or custom replication topologies
- Always factor in TCO (people + tooling + incidents), not just instance pricing
