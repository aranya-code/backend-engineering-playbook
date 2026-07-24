# 06 - Backup & Restore

## Overview

Amazon DynamoDB Backup & Restore enables you to create complete snapshots of a table and restore them whenever needed.

Unlike **Point-in-Time Recovery (PITR)**, which continuously captures changes over a rolling 35-day window, on-demand backups create a **fixed snapshot** of a table at a specific point in time.

Backups are durable, managed by AWS, and remain available until explicitly deleted.

They are commonly used for:

- Disaster recovery
- Long-term archival
- Compliance requirements
- Major application releases
- Schema migrations
- Data migration
- Testing environments
- Business continuity planning

---

# Why Backup & Restore Exists

Imagine deploying a major application update.

```text
Version 1

↓

Create Backup

↓

Deploy Version 2

↓

Unexpected Failure
```

Instead of repairing millions of records manually:

```text
Restore Backup

↓

Application Recovered
```

Snapshots provide a known good recovery point before major changes.

---

# Internal Architecture

```text
               DynamoDB Table

                      │

         Create On-Demand Backup

                      │

                      ▼

            Managed Backup Storage

                      │

              Restore Request

                      │

                      ▼

             Newly Created Table
```

Backups are managed entirely by AWS.

---

# Backup Workflow

```text
Application Running

↓

Create Backup

↓

Snapshot Created

↓

Stored Securely

↓

Restore Anytime

↓

New DynamoDB Table
```

The production table remains online during backup creation.

---

# What Gets Backed Up?

A backup includes:

- Table structure
- Items
- Primary Keys
- Local Secondary Indexes
- Global Secondary Indexes
- Provisioned capacity configuration
- Encryption settings

Everything required to recreate the table is preserved.

---

# Restore Workflow

Suppose a deployment corrupts production data.

```text
Production Table

↓

Restore Backup

↓

AWS Creates

Orders-Restore

↓

Validate

↓

Switch Traffic
```

The original table remains untouched.

---

# Backup Lifecycle

```text
Production Table

↓

Backup Created

↓

Stored

↓

Available

↓

Deleted Manually
```

Unlike PITR, backups do not expire automatically.

---

# Backup Timing

Backups are typically created:

```text
Before Deployment

Before Migration

Before Data Import

Before Schema Changes

Before Bulk Updates
```

These checkpoints simplify rollback.

---

# Backup vs Restore

Backup:

```text
Running Table

↓

Create Snapshot
```

Restore:

```text
Snapshot

↓

Create New Table
```

Backups preserve data.

Restores recreate tables.

---

# Backup vs PITR

| Feature | Backup | PITR |
|----------|---------|------|
| Snapshot | Yes | No |
| Continuous | No | Yes |
| Long-Term Storage | Yes | Rolling 35 Days |
| Restore to Any Second | No | Yes |
| Manual Creation | Yes | Automatic |

---

# Backup vs Export to S3

| Feature | Backup | Export to S3 |
|----------|---------|--------------|
| Disaster Recovery | Excellent | Limited |
| Restore Directly | Yes | No |
| Analytics | Limited | Excellent |
| Data Lake Integration | No | Yes |

Backups recover applications.

Exports support analytics.

---

# Backup vs Global Tables

| Feature | Backup | Global Tables |
|----------|---------|--------------|
| Historical Recovery | Yes | No |
| Multi-Region Availability | No | Yes |
| Disaster Recovery | Yes | Partial |
| Low Latency | No | Yes |

Global Tables provide availability.

Backups provide recoverability.

---

# Real-World Example — Production Deployment

Before deployment:

```text
Create Backup

↓

Deploy New Version
```

If deployment fails:

```text
Restore Backup

↓

Rollback Complete
```

---

# Real-World Example — Data Migration

Migration process:

```text
Backup

↓

Migration

↓

Validation
```

If validation fails:

```text
Restore Original
```

Risk is minimized.

---

# Real-World Example — Compliance

Financial systems often retain:

```text
Monthly Backup

↓

Yearly Archive

↓

Regulatory Audit
```

Snapshots satisfy compliance requirements.

---

# Real-World Example — Testing

Production snapshot:

```text
Backup

↓

Restore

↓

Testing Environment
```

Developers can safely test against production-like data without affecting live systems.

---

# Cross-Region Recovery

Backups can support disaster recovery strategies.

```text
Backup

↓

Restore

↓

Another AWS Region
```

Organizations often combine this with infrastructure automation for regional failover.

---

# Performance Considerations

Creating a backup:

- Does not block application traffic.
- Has minimal impact on table performance.
- Is fully managed by AWS.

Restoring:

- Creates a new table.
- Duration depends on table size.
- Does not affect the source table.

---

# Best Practices

- Create backups before major deployments.
- Keep backups before bulk imports or migrations.
- Automate backup creation using AWS Backup.
- Test restore procedures regularly.
- Define backup retention policies.
- Encrypt all backups.

---

# Common Mistakes

## Assuming Backup Replaces PITR

Incorrect.

Backups and PITR solve different problems.

```text
PITR

↓

Continuous Recovery

────────────

Backup

↓

Fixed Recovery Point
```

Many production systems use both.

---

## Never Testing Restores

A backup has little value if it cannot be restored successfully.

Perform regular disaster recovery exercises.

---

## Deleting Backups Too Early

Retention policies should align with:

- Business requirements
- Compliance regulations
- Disaster recovery objectives

---

## Forgetting Infrastructure

Restoring only data is often insufficient.

Recovery plans should also include:

- IAM
- CloudFormation
- Networking
- Auto Scaling
- Monitoring
- Alarms

---

# Architecture Perspective

```text
             Production Table

                    │

            Create Backup

                    │

          Managed Backup Store

                    │

          Restore on Demand

                    │

                    ▼

           Newly Created Table
```

Snapshots provide reliable recovery points independent of application changes.

---

# Production Considerations

Backup & Restore is a critical component of enterprise disaster recovery.

Production teams typically create backups:

- Before deployments
- Before schema migrations
- Before ETL jobs
- Before bulk imports
- Before infrastructure changes

Many organizations automate backups using:

- AWS Backup
- EventBridge
- AWS Lambda
- CloudFormation
- CI/CD pipelines

A mature recovery strategy usually combines:

- On-Demand Backups
- Point-in-Time Recovery
- Global Tables
- Multi-Region Infrastructure
- Infrastructure as Code

This combination protects against both operational mistakes and regional failures.

---

# Interview Notes

A common interview question is:

> **What is the difference between DynamoDB Backup and PITR?**

Backups are manually created snapshots that remain until deleted, while PITR continuously records table changes and allows restoration to any second within the previous 35 days.

Another common question is:

> **Does restoring a backup overwrite the original table?**

No. Restoring a backup always creates a **new DynamoDB table**. Applications must switch traffic manually if the restored table is to become the new production table.

Another common question is:

> **When should you create an on-demand backup?**

Before deployments, schema migrations, large data imports, or any high-risk operation that could affect production data.

Another common question is:

> **Can backups be part of a disaster recovery strategy?**

Yes. Combined with PITR, Global Tables, AWS Backup, and Infrastructure as Code, on-demand backups are an essential part of enterprise disaster recovery planning.

---

# Key Takeaways

- On-demand backups create complete snapshots of DynamoDB tables.
- Backups remain available until explicitly deleted.
- Restoring a backup creates a new table rather than replacing the existing one.
- Backups are ideal for deployments, migrations, compliance, and disaster recovery.
- They complement—not replace—Point-in-Time Recovery.
- Regular backup validation and restore testing are essential for production readiness.
- Enterprise recovery strategies typically combine backups, PITR, Global Tables, and automated infrastructure provisioning.