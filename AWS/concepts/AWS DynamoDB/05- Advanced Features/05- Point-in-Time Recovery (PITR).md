# 05 - Point-in-Time Recovery (PITR)

## Overview

Point-in-Time Recovery (PITR) is a continuous backup feature that enables a DynamoDB table to be restored to **any second within the previous 35 days**.

Unlike traditional scheduled backups that capture data only at specific intervals, PITR continuously records changes made to the table, allowing recovery from accidental writes, deletes, corruption, or application bugs.

PITR is designed to minimize data loss while simplifying disaster recovery for production workloads.

Typical use cases include:

- Accidental table deletion
- Buggy application deployments
- Data corruption
- Operational mistakes
- Disaster recovery
- Compliance requirements
- Incident response

---

# Why PITR Exists

Imagine an application bug.

```text
Deployment

↓

Bug Introduced

↓

Delete Every User

↓

Production Outage
```

Without PITR:

```text
Restore Last Backup

↓

Lose Hours of Data
```

With PITR:

```text
Choose Time

09:14:37

↓

Restore Table

↓

Continue Investigation
```

Only a few seconds of data are lost.

---

# Internal Architecture

```text
                 DynamoDB Table

                       │

          Continuous Change Logging

                       │

        ───────────────────────────

          Rolling 35-Day Window

        ───────────────────────────

                       │

               Restore Request

                       │

                       ▼

            New Restored Table
```

PITR continuously records changes without affecting application logic.

---

# Recovery Window

PITR maintains a rolling recovery window.

```text
Today

↓

35 Days

↓

Recovery Available
```

As time progresses:

```text
Day 1

↓

Day 2

↓

Day 36

↓

Day 1 Removed
```

The oldest recovery point automatically expires.

---

# Continuous Backups

Unlike scheduled snapshots:

```text
12:00 AM

↓

Backup

↓

24 Hours Later

↓

Backup
```

PITR continuously captures changes.

```text
09:01

↓

09:02

↓

09:03

↓

09:04
```

Every modification contributes to the recovery timeline.

---

# Recovery Workflow

Suppose data corruption occurs.

```text
09:15

↓

Bad Deployment

↓

Delete Records

↓

09:20

↓

Issue Detected

↓

Restore Table

↓

09:14:59
```

Applications recover to the desired point.

---

# Restoration Process

PITR never overwrites the existing table.

Instead:

```text
Original Table

↓

Restore

↓

New Table
```

Example:

```text
Orders

↓

Orders-Restored
```

Applications decide when to switch traffic.

---

# Restore Timeline

```text
Current Table

↓

Accidental Delete

↓

Select Timestamp

↓

AWS Creates New Table

↓

Validation

↓

Switch Application
```

This minimizes production risk.

---

# PITR vs On-Demand Backup

| Feature | PITR | On-Demand Backup |
|----------|------|------------------|
| Continuous | ✅ | ❌ |
| Restore to Any Second | ✅ | ❌ |
| Manual Backup Required | ❌ | ✅ |
| Recovery Window | Rolling 35 Days | Specific Snapshot |
| Automation | Fully Managed | Manual |

---

# PITR vs Global Tables

| Feature | PITR | Global Tables |
|----------|------|---------------|
| Disaster Recovery | ✅ | Partial |
| Multi-Region Availability | ❌ | ✅ |
| Historical Recovery | ✅ | ❌ |
| Protection from Accidental Deletes | ✅ | ❌ |

Global Tables improve availability.

PITR protects historical data.

---

# PITR vs Traditional Database Backups

| Feature | Traditional Backup | PITR |
|----------|-------------------|------|
| Scheduled | Usually | No |
| Continuous | Rare | Yes |
| Point-in-Time Recovery | Sometimes | Yes |
| Operational Complexity | High | Low |

---

# Real-World Example — Bad Deployment

Developer deploys:

```text
UPDATE Users

↓

Set Email = NULL
```

Result:

```text
Millions of Rows Corrupted
```

Recovery:

```text
Restore

↓

Five Minutes Earlier
```

---

# Real-World Example — Accidental Delete

Administrator runs:

```text
DeleteItem

↓

Wrong Table
```

Recovery:

```text
Restore

↓

Before Delete
```

---

# Real-World Example — Data Corruption

A software bug writes invalid values.

```text
Price

↓

-9999
```

Instead of repairing millions of records manually:

```text
Restore

↓

Before Bug
```

---

# Real-World Example — Security Incident

Suppose ransomware modifies application data.

```text
Attack

↓

Corrupt Records

↓

Restore

↓

Before Attack
```

Recovery is significantly faster than rebuilding data.

---

# Performance Considerations

Enabling PITR does **not** affect:

- Read latency
- Write latency
- Query performance
- Capacity planning

AWS manages continuous backups in the background.

However:

- Storage costs increase.
- Restore time depends on table size.

---

# Best Practices

- Enable PITR for all production tables.
- Regularly test restoration procedures.
- Document disaster recovery runbooks.
- Validate restored data before redirecting production traffic.
- Combine PITR with CloudFormation or Infrastructure as Code.
- Monitor backup status using CloudWatch and AWS Config.

---

# Common Mistakes

## Assuming PITR Restores the Existing Table

Incorrect:

```text
Restore

↓

Original Table Replaced
```

Correct:

```text
Restore

↓

New Table Created
```

Applications must switch to the restored table manually.

---

## Not Testing Recovery

Many teams enable PITR but never verify it.

Disaster recovery plans should include periodic restoration drills.

---

## Using PITR Instead of High Availability

PITR restores lost data.

It does **not** prevent outages.

For high availability:

- Global Tables
- Multi-AZ architecture
- Route 53 failover

should be used alongside PITR.

---

## Waiting Too Long

PITR stores only the last **35 days** of changes.

Older recovery points are permanently removed.

---

# Architecture Perspective

```text
                Application

                      │

               Read / Write

                      │

               DynamoDB Table

                      │

       Continuous Change Recording

                      │

         Rolling 35-Day Recovery Log

                      │

              Restore Request

                      │

                      ▼

            Newly Restored Table
```

PITR provides continuous data protection without interrupting application operations.

---

# Production Considerations

PITR is considered a standard best practice for production DynamoDB deployments.

Typical workloads include:

- Banking systems
- E-commerce platforms
- Healthcare applications
- SaaS products
- Financial ledgers
- User account databases
- Inventory systems

A robust disaster recovery strategy typically combines:

- Point-in-Time Recovery
- On-Demand Backups
- Global Tables
- CloudFormation
- AWS Backup

Together, these services provide protection against both infrastructure failures and operational mistakes.

---

# Interview Notes

A common interview question is:

> **What is Point-in-Time Recovery (PITR) in DynamoDB?**

PITR is a continuous backup feature that allows a DynamoDB table to be restored to any second within the previous 35 days.

Another common question is:

> **Does PITR overwrite the existing table?**

No. Restoring from PITR always creates a **new table**. The original table remains unchanged.

Another common question is:

> **Does enabling PITR impact application performance?**

No. PITR runs in the background and does not significantly affect read or write performance.

Another common question is:

> **When should PITR be enabled?**

For virtually all production tables where data loss from accidental deletion, corruption, or faulty deployments would have business impact.

---

# Key Takeaways

- PITR continuously backs up DynamoDB tables and maintains a rolling 35-day recovery window.
- Tables can be restored to any second within that window.
- Restores always create a new table rather than replacing the original.
- PITR protects against accidental deletes, application bugs, and data corruption.
- It has minimal operational overhead and no noticeable impact on application performance.
- PITR should be a standard component of every production disaster recovery strategy.
