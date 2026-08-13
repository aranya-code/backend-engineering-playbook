# 09 - Global Secondary Index (GSI) Issues

## Overview

Global Secondary Indexes (GSIs) are one of the most powerful features of Amazon DynamoDB because they allow applications to query data using alternate access patterns.

However, GSIs are also one of the most common sources of production issues.

Typical production problems include:

- Slow queries
- Missing data
- Index throttling
- Delayed propagation
- Hot indexes
- Incorrect projections
- Backfilling delays
- Increased costs

Understanding how GSIs work internally is essential for designing scalable DynamoDB applications.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How GSIs work
- Common GSI problems
- Eventual consistency
- Backfilling
- Index throttling
- Projection issues
- Monitoring
- Production troubleshooting

---

# GSI Architecture

```text
                DynamoDB Table

                     │

      ┌──────────────┼──────────────┐

      ▼                             ▼

Primary Key                  Global Secondary Index

CustomerID                  Email

OrderID                     Status
```

A GSI stores a separate copy of selected attributes optimized for different query patterns.

---

# Data Flow

```text
Application

      │

      ▼

Write Item

      │

      ▼

Base Table

      │

      ▼

GSI Update

      │

      ▼

Query Index
```

---

# Common Problems

Production issues commonly include:

- Missing items
- Delayed updates
- Hot partitions
- Wrong projection
- Capacity throttling
- Backfill delays
- Incorrect key design

---

# Problem 1 — Missing Data

Application:

```text
Insert Item

↓

Immediately Query GSI

↓

Item Missing
```

Reason:

GSIs are **eventually consistent**.

Updates propagate asynchronously.

---

# Timeline Example

```text
12:00:00

Write Item

↓

12:00:01

Base Table Updated

↓

12:00:03

GSI Updated
```

A query during propagation may not return the item.

---

# Problem 2 — Incorrect Projection

Projection Types:

```text
KEYS_ONLY

INCLUDE

ALL
```

---

## Example

Application expects:

```text
Customer Name

Order Total
```

Projection:

```text
KEYS_ONLY
```

Result:

```text
Attributes Missing
```

---

# Choosing the Right Projection

| Projection | Stores |
|------------|--------|
| KEYS_ONLY | Primary and index keys only |
| INCLUDE | Selected non-key attributes |
| ALL | Entire item |

Choose the smallest projection that satisfies application requirements.

---

# Problem 3 — Index Throttling

Even when the base table is healthy:

```text
Base Table

Healthy

↓

GSI

Throttled
```

Reason:

Indexes have their own throughput consumption.

---

# Symptoms

Applications experience:

- Slow queries
- Throttling
- Increased latency
- Retry storms

Common exception:

```text
ProvisionedThroughputExceededException
```

---

# Problem 4 — Hot GSI

Poor index key:

```text
Status

OPEN
```

Millions of items:

```text
OPEN

↓

Same Partition

↓

Hot Index
```

---

# Better Design

Instead of:

```text
status
```

Use:

```text
status#customerId
```

or another higher-cardinality key that better distributes traffic.

---

# Problem 5 — Backfilling

Creating a GSI on an existing table:

```text
Create GSI

↓

Backfill Existing Items

↓

Index Ready
```

Large tables may require significant time before the index becomes active.

---

# Monitoring Backfill

CLI:

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Review:

```text
GlobalSecondaryIndexes

↓

IndexStatus
```

Possible values:

```text
CREATING

ACTIVE

UPDATING

DELETING
```

Applications should wait until the index is **ACTIVE**.

---

# Problem 6 — Querying Wrong Index

Example:

```bash
aws dynamodb query \
    --table-name Orders
```

Missing:

```text
--index-name
```

The query executes against the base table rather than the intended GSI.

---

# Problem 7 — Missing Partition Key

Query:

```text
Status = OPEN
```

GSI key:

```text
CustomerID
```

Result:

```text
ValidationException
```

Queries must provide the partition key defined for the index.

---

# Monitoring GSIs

Useful CloudWatch metrics:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ReadThrottleEvents

WriteThrottleEvents

SuccessfulRequestLatency
```

Monitor index metrics separately from table metrics.

---

# Investigation Workflow

```text
Slow Query

↓

Base Table?

↓

GSI?

↓

Index ACTIVE?

↓

Projection?

↓

Hot Partition?

↓

CloudWatch

↓

Root Cause
```

---

# Production Example

E-commerce system:

```text
Orders Table

↓

CustomerID

↓

Query by Status
```

Without GSI:

```text
Scan

↓

Slow
```

With GSI:

```text
Status Index

↓

Query

↓

Fast
```

---

# Another Production Example

Users:

```text
Primary Key

↓

UserID
```

Login requires:

```text
Email
```

Solution:

```text
Email GSI
```

Authentication becomes an efficient Query instead of a full table Scan.

---

# GSI Cost Considerations

Every write:

```text
Base Table

↓

Update GSI

↓

Additional Cost
```

More GSIs mean:

- Higher write costs
- More storage
- Longer write paths

Only create indexes that support real access patterns.

---

# Capacity Planning

Consider:

- Read traffic
- Write traffic
- Index growth
- Projected attributes
- Storage usage

Poor capacity planning can lead to throttling.

---

# Performance Considerations

- GSIs are eventually consistent.
- Large projections increase storage and write costs.
- Hot index keys create bottlenecks.
- Monitor GSI metrics independently.
- Avoid unnecessary indexes.

---

# Best Practices

- Design GSIs around application access patterns.
- Use high-cardinality partition keys.
- Keep projections small.
- Monitor index-specific CloudWatch metrics.
- Wait until indexes become ACTIVE.
- Review index usage periodically.

---

# Common Mistakes

## Creating Too Many GSIs

Every additional GSI increases:

- Storage
- Write cost
- Maintenance complexity

---

## Assuming Strong Consistency

GSIs provide eventual consistency.

Applications should account for propagation delays.

---

## Using Low-Cardinality Keys

Examples:

```text
ACTIVE

OPEN

YES

NO
```

These values often produce hot partitions.

---

## Projecting Every Attribute

Using:

```text
Projection = ALL
```

for every GSI increases storage and write amplification unnecessarily.

---

## Ignoring Index Metrics

Healthy table metrics do not guarantee healthy index performance.

Always monitor GSI-specific CloudWatch metrics.

---

# Interview Notes

### What is a Global Secondary Index?

A GSI is an alternate index that enables efficient queries using different partition and sort keys than the base table.

---

### Why are GSIs eventually consistent?

Updates are propagated asynchronously from the base table to the index, so newly written data may not appear immediately.

---

### Why might a GSI become throttled?

Because indexes consume their own read and write capacity, poor key design or insufficient capacity can cause index-level throttling even when the base table appears healthy.

---

### What is GSI backfilling?

When a new GSI is created on an existing table, DynamoDB scans existing items and populates the index before it becomes ACTIVE.

---

### How do you troubleshoot a slow GSI query?

1. Verify the index is ACTIVE.
2. Review CloudWatch metrics.
3. Check partition-key distribution.
4. Examine projection type.
5. Identify hot partitions.
6. Ensure the query targets the correct index.

---

# Key Takeaways

- GSIs enable alternate query patterns without scanning the base table.
- Most production issues stem from eventual consistency, poor key design, incorrect projections, or index throttling.
- Every GSI introduces additional storage, write amplification, and operational overhead.
- CloudWatch metrics and proper capacity planning are essential for maintaining healthy indexes.
- Senior backend engineers design only the GSIs required by real application access patterns while continuously monitoring their performance.