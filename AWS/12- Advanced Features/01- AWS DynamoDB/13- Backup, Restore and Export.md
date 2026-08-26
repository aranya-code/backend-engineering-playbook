# 21 - Backup, Restore and Export

## Overview

Data is one of the most valuable assets of any application.

No matter how well an application is designed, failures can still occur:

- Accidental deletions
- Application bugs
- Corrupted deployments
- Malicious users
- Region failures
- Compliance requirements
- Disaster recovery scenarios

Although DynamoDB is a highly durable managed database, **durability does not eliminate the need for backups**.

For example, if an application accidentally deletes every customer record, DynamoDB faithfully replicates those deletions. The database is behaving correctly—the application is not.

This is why DynamoDB provides multiple mechanisms for protecting and recovering data:

- On-Demand Backups
- Point-in-Time Recovery (PITR)
- Restore Operations
- Export to Amazon S3
- AWS Backup Integration

Each feature solves a different business problem.

---

# Why Backups Exist

Imagine an employee accidentally executes:

```text
Delete Customer Records
```

Result:

```text
500,000 Items Deleted
```

DynamoDB successfully processes the request.

Unfortunately:

```text
Production Data

↓

Gone
```

Without backups:

```text
Recovery

↓

Impossible
```

With backups:

```text
Restore

↓

Application Running Again
```

---

# Backup Options

DynamoDB supports two primary backup mechanisms.

```text
Backup

├── On-Demand Backup
│
└── Point-in-Time Recovery (PITR)
```

Each has different use cases.

---

# On-Demand Backup

An On-Demand Backup captures the **entire table** at a specific moment.

Think of it as taking a snapshot.

```text
Current Table

↓

Create Backup

↓

Snapshot Stored
```

Months later:

```text
Restore Snapshot
```

Useful before:

- Major deployments
- Schema migrations
- Bulk imports
- Data cleanup jobs

---

# Point-in-Time Recovery (PITR)

PITR continuously protects your table.

Instead of restoring only fixed snapshots:

```text
9:00 AM

↓

9:05 AM

↓

9:10 AM

↓

9:15 AM
```

You can restore the table to **almost any second** within the configured recovery window (up to **35 days**).

Example:

Application bug begins at:

```text
10:42:15 AM
```

Restore to:

```text
10:42:14 AM
```

Almost no data is lost.

---

# Backup Architecture

```text
               DynamoDB Table

                      │

      ┌───────────────┴───────────────┐

      ▼                               ▼

On-Demand Backup          Point-in-Time Recovery

      │                               │

      ▼                               ▼

 Manual Snapshot         Continuous Change Log
```

Both mechanisms are managed entirely by AWS.

---

# Restore Operations

Backups do not overwrite the original table.

Instead:

```text
Backup

↓

Restore

↓

New DynamoDB Table
```

Example:

```text
Original Table

Orders
```

Restored as:

```text
Orders_Restore
```

This allows engineers to:

- Verify restored data
- Compare tables
- Copy missing records
- Switch applications safely

---

# Point-in-Time Recovery Workflow

```text
Application Bug

↓

Data Corrupted

↓

Select Recovery Time

↓

Restore New Table

↓

Verify

↓

Redirect Application
```

Recovery does not modify the damaged table.

---

# Export to Amazon S3

Sometimes organizations don't want another DynamoDB table.

Instead, they need:

- Analytics
- Long-term storage
- Compliance archives
- Machine learning datasets

DynamoDB supports exporting table data directly to Amazon S3.

```text
DynamoDB

↓

Export

↓

Amazon S3
```

No application code is required.

---

# Export Formats

Exports support common formats including:

```text
Amazon DynamoDB JSON

JSON

Ion
```

These formats can later be consumed by:

- Amazon Athena
- AWS Glue
- Amazon EMR
- Apache Spark
- Machine Learning pipelines

---

# Analytics Workflow

```text
DynamoDB

↓

Export

↓

Amazon S3

↓

AWS Glue

↓

Athena

↓

Business Intelligence Dashboard
```

Operational databases remain isolated from analytical workloads.

---

# AWS Backup Integration

Large organizations often manage backups centrally.

Instead of configuring each DynamoDB table individually:

```text
AWS Backup

↓

Backup Policies

↓

Multiple AWS Services
```

AWS Backup supports:

- DynamoDB
- Amazon EFS
- Amazon RDS
- Amazon EC2
- Amazon FSx

This enables consistent backup governance across an AWS environment.

---

# Backup vs PITR

These features solve different problems.

| Feature | On-Demand Backup | PITR |
|----------|------------------|------|
| Manual | ✅ | ❌ |
| Continuous | ❌ | ✅ |
| Restore to Specific Second | ❌ | ✅ |
| Good Before Deployments | ✅ | Limited |
| Recovery Window | Until Deleted | Up to 35 Days |

Many production systems enable both.

---

# Backup vs Global Tables

These features are frequently confused.

| Feature | Backup | Global Tables |
|----------|--------|---------------|
| Protect Against Accidental Delete | ✅ | ❌ |
| Multi-Region Access | ❌ | ✅ |
| Disaster Recovery | ✅ | ✅ |
| Data Replication | ❌ | ✅ |
| Historical Recovery | ✅ | ❌ |

Global Tables improve availability.

Backups recover lost or corrupted data.

---

# Restore Considerations

Restoring a backup creates:

```text
New Table
```

Applications must then:

- Update configuration
- Validate restored data
- Recreate alarms if necessary
- Recreate auto scaling policies
- Verify IAM permissions
- Re-enable integrations such as Streams if required

Recovery involves more than simply restoring the table.

---

# Cost Considerations

Backup-related costs include:

- Backup storage
- PITR storage
- Export operations
- S3 storage
- Cross-region storage (if applicable)

While backups increase infrastructure costs, they are often insignificant compared to the cost of permanent data loss.

---

# Security

Backup data should receive the same protection as production data.

Best practices include:

- Encrypt backups using AWS KMS.
- Restrict restore permissions through IAM.
- Enable CloudTrail auditing.
- Apply lifecycle policies for exported S3 data.
- Regularly test recovery procedures.

---

# Best Practices

- Enable PITR for production tables.
- Take On-Demand Backups before major deployments.
- Test restore procedures regularly.
- Export historical data to S3 for analytics.
- Use AWS Backup for centralized governance.
- Encrypt backups with KMS.
- Monitor backup status and recovery readiness.

---

# Common Mistakes

## Assuming Global Tables Replace Backups

Replication copies mistakes.

Backups recover mistakes.

---

## Never Testing Restores

A backup is only valuable if it can be restored successfully.

Regular recovery drills are essential.

---

## Restoring Directly Into Production

Always restore to a new table first.

Validate the data before redirecting production traffic.

---

## Forgetting Backup Costs

Old backups retained indefinitely can generate unnecessary storage costs.

Implement lifecycle and retention policies.

---

# Real-World Example

A deployment bug accidentally deletes millions of customer orders.

```text
Deployment

↓

Application Bug

↓

Delete Operations

↓

Production Table Empty
```

Recovery process:

```text
PITR

↓

Restore Table

↓

Verify Data

↓

Switch Traffic

↓

Application Restored
```

Without PITR, recovery could require rebuilding data from logs—or may be impossible.

---

# Architecture Perspective

A production backup architecture often looks like this:

```text
Application

↓

DynamoDB

├──────────────┐
│              │
▼              ▼

PITR       On-Demand Backup

│              │
└──────┬───────┘
       ▼

 Restore Table

       ▼

Validation

       ▼

Production Cutover

---------------------------

Analytics Path

DynamoDB

↓

Export to S3

↓

Glue Catalog

↓

Athena

↓

QuickSight
```

Operational recovery and analytical exports are independent workflows, allowing production systems to remain performant while supporting business intelligence.

---

# Interview Notes

A common interview question is:

> **If Global Tables replicate data across Regions, why do we still need backups?**

Because Global Tables replicate **both valid and invalid changes**.

If an application accidentally deletes customer data, that deletion is replicated to every region. Backups provide a historical copy that can be restored after accidental deletions, application bugs, or data corruption.

Another common interview question is:

> **When would you choose PITR over an On-Demand Backup?**

Use **PITR** for continuous protection of production workloads where recovery to an exact point in time is important.

Use an **On-Demand Backup** before high-risk operations such as deployments, schema migrations, or bulk data imports, where a known recovery snapshot is sufficient.

---

# Key Takeaways

- DynamoDB provides multiple data protection mechanisms, each addressing different recovery scenarios.
- **On-Demand Backups** create manual snapshots of an entire table.
- **Point-in-Time Recovery (PITR)** enables restoration to nearly any second within a recovery window of up to 35 days.
- Restoring always creates a **new table**, protecting the original data during recovery.
- Export to Amazon S3 enables analytics, compliance, and long-term archival without impacting production workloads.
- Global Tables improve availability but do **not** replace backups.
- A robust disaster recovery strategy combines PITR, scheduled backups, S3 exports, encryption, and regularly tested recovery procedures.