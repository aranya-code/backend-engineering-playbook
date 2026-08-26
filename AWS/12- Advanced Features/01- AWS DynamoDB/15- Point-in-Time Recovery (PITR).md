# 23 - Point-in-Time Recovery (PITR)

## Overview

Imagine your production application has been running flawlessly for months.

Then, a deployment bug executes:

```text
DELETE FROM Orders
```

(or the DynamoDB equivalent)

Within seconds:

- Millions of records disappear.
- Applications begin failing.
- Customers cannot access their data.

The infrastructure is healthy.

The DynamoDB service is healthy.

The problem is that **the application has corrupted the data**.

How do you recover?

This is exactly the problem that **Point-in-Time Recovery (PITR)** solves.

PITR continuously records every change made to a DynamoDB table, allowing you to restore the table to **almost any second** within the last **35 days**.

Unlike traditional backups that capture only snapshots, PITR enables continuous recovery.

---

# Why PITR Exists

Consider an e-commerce platform.

Timeline:

```text
09:00 AM

↓

Customers place orders

↓

Everything works
```

At:

```text
11:15 AM
```

A deployment bug executes:

```text
Delete Orders
```

Production now looks like:

```text
Orders Table

↓

Empty
```

Without PITR:

Recovery may be impossible.

With PITR:

```text
Restore

↓

11:14:59 AM
```

The system returns to its state just before the bug.

---

# PITR Architecture

Unlike manual backups:

```text
Snapshot

↓

One Point
```

PITR continuously records changes.

```text
Write

↓

Internal Recovery Log

↓

Write

↓

Recovery Log

↓

Write

↓

Recovery Log
```

Conceptually:

```text
                DynamoDB Table

                       │

      Continuous Change Recording

                       │

                       ▼

        Point-in-Time Recovery Log

                       │

             Select Timestamp

                       │

                       ▼

             Restore New Table
```

AWS manages this process automatically.

---

# Recovery Window

PITR provides a rolling recovery window.

```text
Today

↓

Yesterday

↓

2 Days Ago

↓

...

↓

35 Days Ago
```

You may restore the table to nearly any second within this period.

Older recovery points expire automatically.

---

# How PITR Works

Step 1

Enable PITR.

```text
Table

↓

Continuous Protection
```

---

Step 2

Applications continue normally.

```text
PutItem

↓

UpdateItem

↓

DeleteItem
```

Every modification becomes part of the recovery history.

---

Step 3

Suppose corruption occurs.

```text
Deployment

↓

Bad Data
```

---

Step 4

Choose a recovery time.

```text
10:42:14 AM
```

AWS restores the table.

---

Step 5

A new table is created.

```text
Orders

↓

Orders_Restore
```

Applications can now switch to the restored table.

---

# Restore Process

PITR never overwrites production.

Instead:

```text
Current Table

↓

Restore

↓

New Table
```

Benefits:

- Validate restored data
- Compare tables
- Recover selectively
- Avoid additional damage

---

# Timeline Example

```text
09:00

Normal Operations

↓

10:00

Customers Continue Working

↓

11:00

Bug Introduced

↓

11:10

Mass Deletion

↓

11:20

Issue Detected

↓

Restore to

10:59:59
```

Very little data is lost.

---

# Internal Recovery Concept

Although AWS does not publicly disclose every implementation detail, conceptually PITR functions like a continuously maintained recovery history.

```text
Insert

↓

Update

↓

Update

↓

Delete

↓

Recovery History
```

When restoration is requested:

```text
Recovery History

↓

Replay Until Selected Time

↓

Build New Table
```

This resembles database log replay used by many relational databases.

---

# PITR vs On-Demand Backup

Many engineers confuse these features.

## On-Demand Backup

```text
Manual Snapshot

↓

Restore Snapshot
```

Recovery is limited to snapshot times.

---

## PITR

```text
Continuous Recovery

↓

Restore

↓

Any Second

Within 35 Days
```

PITR offers much finer recovery granularity.

---

# PITR vs Global Tables

Global Tables improve:

```text
Availability
```

PITR improves:

```text
Recoverability
```

Suppose an application deletes:

```text
All Users
```

Global Tables replicate:

```text
Deletion
```

Every region loses data.

PITR allows recovery.

---

# PITR vs AWS Backup

AWS Backup manages backups across multiple AWS services.

```text
AWS Backup

↓

Policy

↓

Multiple Resources
```

PITR is DynamoDB-specific.

It provides continuous protection for a single table.

Many enterprises use both together.

---

# Recovery Time Objective (RTO)

RTO answers:

> **How quickly can the application recover?**

Example:

```text
Failure

↓

Restore

↓

Switch Traffic

↓

Application Running
```

PITR significantly reduces RTO compared to rebuilding data manually.

---

# Recovery Point Objective (RPO)

RPO answers:

> **How much data can be lost?**

Without PITR:

```text
Yesterday's Backup

↓

Lose One Day
```

With PITR:

```text
Restore

↓

One Second Before Failure
```

Data loss is minimized.

---

# Cost Considerations

PITR incurs additional charges.

Costs depend on:

- Table size
- Retention period
- Restore operations

However:

The cost of PITR is often insignificant compared to the business impact of permanent data loss.

---

# Production Recovery Workflow

```text
Deployment

↓

Bug

↓

Production Alert

↓

Freeze Writes

↓

Identify Failure Time

↓

Restore Using PITR

↓

Validate Data

↓

Redirect Traffic

↓

Resume Operations
```

Having a documented runbook is just as important as enabling PITR.

---

# Limitations

PITR has several important limitations.

### Does Not Restore In Place

Recovery creates a new table.

Applications must migrate to it.

---

### Limited Recovery Window

Maximum:

```text
35 Days
```

Older data cannot be recovered using PITR.

---

### Table-Level Recovery

PITR restores the table.

It does not selectively restore:

- Individual items
- Attributes
- Collections

Fine-grained recovery requires additional tooling.

---

### Additional Cost

Continuous protection increases storage costs.

Organizations should evaluate recovery requirements against budget.

---

# Best Practices

- Enable PITR on every production table.
- Document recovery procedures.
- Perform recovery drills regularly.
- Combine PITR with CloudWatch alarms.
- Continue taking On-Demand Backups before major deployments.
- Monitor restore times.
- Validate restored data before switching production traffic.

---

# Common Mistakes

## Assuming PITR Is Enabled by Default

It must be explicitly enabled.

---

## Never Testing Recovery

A recovery feature is only valuable if the team knows how to use it.

---

## Confusing PITR with High Availability

PITR restores deleted data.

It does not automatically keep applications running during regional outages.

---

## Ignoring Recovery Procedures

Technical recovery is only one part of disaster recovery.

Operational playbooks are equally important.

---

# Real-World Example

An online retailer deploys a faulty inventory update.

```text
Deployment

↓

Incorrect Logic

↓

Delete Inventory

↓

Production Failure
```

Recovery:

```text
Determine Failure Time

↓

Restore Table Using PITR

↓

Validate Inventory

↓

Update Application Configuration

↓

Resume Service
```

Customers experience minimal downtime and almost no data loss.

---

# Architecture Perspective

```text
Application

↓

DynamoDB

↓

Continuous Change Recording

↓

Point-in-Time Recovery

↓

Restore Request

↓

New DynamoDB Table

↓

Validation

↓

Production Cutover
```

Notice that PITR operates entirely outside the application's request path. It acts as a safety mechanism for recovery rather than participating in normal database operations.

---

# Interview Notes

A common interview question is:

> **If you already take nightly backups, why enable PITR?**

Nightly backups can lose up to 24 hours of data. PITR allows restoration to nearly any second within the last 35 days, dramatically reducing the Recovery Point Objective (RPO).

Another common question is:

> **Does PITR overwrite the existing table during recovery?**

No.

PITR always restores to a **new DynamoDB table**. This allows engineers to verify the recovered data before redirecting production traffic, reducing the risk of additional errors during recovery.

---

# Key Takeaways

- Point-in-Time Recovery (PITR) continuously protects DynamoDB tables by recording changes over time.
- Tables can be restored to nearly any second within a rolling 35-day recovery window.
- PITR creates a **new table** during recovery and never overwrites the existing table.
- It minimizes data loss and significantly improves disaster recovery capabilities.
- PITR complements—not replaces—On-Demand Backups, Global Tables, and AWS Backup.
- Production teams should combine PITR with documented recovery procedures and regular recovery drills.
- Enabling PITR is one of the most valuable safeguards for production DynamoDB workloads.