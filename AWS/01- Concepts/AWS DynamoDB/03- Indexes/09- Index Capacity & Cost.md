# 09 - Index Capacity & Cost

## Overview

Secondary indexes dramatically improve query flexibility in DynamoDB, but they are **not free**.

Every Global Secondary Index (GSI) or Local Secondary Index (LSI) introduces additional:

- Storage
- Read capacity consumption
- Write capacity consumption
- Replication work
- Operational cost

Many production systems experience unexpectedly high DynamoDB bills because indexes were added without understanding their impact.

Designing cost-efficient indexes is therefore a critical skill for senior backend engineers.

---

# Why Do Indexes Increase Cost?

Consider a simple table.

```text
Base Table

CustomerID

OrderID

Status
```

Now create:

```text
Email GSI
```

Every new item now requires:

```text
Write Base Table

↓

Write Email GSI
```

One write becomes two writes.

If another GSI exists:

```text
Write Base Table

↓

Write GSI 1

↓

Write GSI 2
```

The number of write operations grows with every index.

---

# Components of Index Cost

Every secondary index contributes to:

- Storage cost
- Write cost
- Read cost
- Replication overhead
- Backup size
- Restore duration

These costs scale with traffic.

---

# Storage Cost

Indexes store copies of attributes.

Suppose each item contains:

```text
2 KB
```

Base Table

```text
1 Million Items

↓

2 GB
```

One GSI with ALL projection:

```text
Another

2 GB
```

Total storage:

```text
4 GB
```

Two GSIs:

```text
6 GB
```

Storage increases linearly.

---

# Write Cost

Every write updates:

```text
Base Table

↓

Indexes
```

Example:

Table

```text
1 Write
```

One GSI

```text
2 Writes
```

Three GSIs

```text
4 Writes
```

Every index multiplies write work.

---

# Read Cost

Queries against indexes consume capacity.

Workflow:

```text
Application

↓

Query GSI

↓

Consumes Read Capacity
```

Indexes are not "free reads."

Each query consumes RCUs or On-Demand read request units.

---

# Capacity Consumption

Suppose:

```text
1000 Writes/Second
```

Table

↓

One GSI

↓

Another GSI

Total write activity:

```text
Base Table

1000

+

GSI1

1000

+

GSI2

1000

=

3000 Write Operations
```

Actual costs depend on:

- Item size
- Projection type
- Capacity mode

---

# Write Amplification

Indexes introduce write amplification.

Without index:

```text
Insert Item

↓

Done
```

With three GSIs:

```text
Insert

↓

Table

↓

Index 1

↓

Index 2

↓

Index 3
```

A single business write results in multiple storage writes.

---

# Projection Impact

Projection choice directly affects cost.

## KEYS_ONLY

Small index.

Lowest storage.

Lowest write cost.

---

## INCLUDE

Medium storage.

Medium write cost.

---

## ALL

Largest storage.

Highest write cost.

---

# Storage Comparison

Suppose:

Base item:

```text
10 KB
```

Projection:

KEYS_ONLY

```text
300 Bytes
```

INCLUDE

```text
2 KB
```

ALL

```text
10 KB
```

Across 500 million records:

The storage difference becomes enormous.

---

# Read Cost Example

Dashboard needs:

```text
Order Status

Order Date
```

Using:

```text
INCLUDE Projection
```

Query:

```text
Single Read
```

Using:

```text
KEYS_ONLY
```

Workflow:

```text
Query Index

↓

Read Table

↓

Return Result
```

Two reads instead of one.

Sometimes paying more storage reduces read costs.

---

# Cost of Unused Indexes

Many applications accumulate indexes over time.

Example:

```text
EmailIndex

CountryIndex

DepartmentIndex

RoleIndex

StatusIndex
```

Only:

```text
EmailIndex
```

is actively queried.

The remaining indexes still consume:

- Storage
- Writes
- Backups

Unused indexes are hidden expenses.

---

# Global Secondary Index Cost

Every GSI introduces:

- Additional storage
- Additional writes
- Additional reads
- Capacity planning
- CloudWatch metrics

Each GSI should justify its existence.

---

# Local Secondary Index Cost

LSIs:

- Share table throughput
- Increase storage
- Increase write activity

Although LSIs do not have separate capacity settings, they still increase operational costs.

---

# Sparse Index Savings

Suppose:

```text
100 Million Orders
```

Only:

```text
20,000

Pending
```

Sparse GSI stores only:

```text
20,000 Items
```

Instead of:

```text
100 Million
```

Storage savings are substantial.

---

# Projection Optimization

Poor design:

```text
ALL

Projection
```

Every attribute copied.

Better:

```text
INCLUDE

Status

Amount

CreatedDate
```

Only attributes needed by queries are stored.

---

# Write-Heavy Applications

Examples:

- IoT telemetry
- Event ingestion
- Log processing
- Sensor platforms

Adding unnecessary GSIs dramatically increases costs because every incoming write updates multiple indexes.

Indexes should be kept to the minimum required for business access patterns.

---

# Read-Heavy Applications

Examples:

- Product catalogs
- Search pages
- Dashboards
- Analytics portals

Here,

additional indexes may reduce expensive scans and improve latency, making the additional storage worthwhile.

---

# Cost Optimization Strategy

Start with:

```text
Business Queries

↓

Design Primary Key

↓

Add Minimal GSIs

↓

Optimize Projection

↓

Measure Usage

↓

Remove Unused Indexes
```

Never begin by indexing every searchable field.

---

# Monitoring Index Costs

Useful CloudWatch metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ThrottledRequests
- SuccessfulRequestLatency
- OnlineIndexPercentageProgress
- Storage metrics

These metrics help identify:

- Underused indexes
- Hot indexes
- Expensive workloads

---

# Example – E-commerce

Table:

```text
Orders
```

Indexes:

```text
CustomerIndex

StatusIndex

DateIndex

RegionIndex
```

After monitoring:

```text
RegionIndex

0 Queries

Last 90 Days
```

Delete it.

Immediately reduce:

- Storage
- Write costs
- Backup size

---

# Example – Banking

Transactions:

```text
AccountID

TransactionDate

Amount
```

Dashboard needs:

```text
Date

Amount

Status
```

Projection:

```text
INCLUDE
```

instead of:

```text
ALL
```

Storage decreases significantly without affecting dashboard performance.

---

# Cost Comparison

| Design | Storage | Write Cost | Read Performance |
|---------|----------|------------|------------------|
| No Index | Lowest | Lowest | Poor for alternate queries |
| GSI + KEYS_ONLY | Low | Low | Medium |
| GSI + INCLUDE | Medium | Medium | High |
| GSI + ALL | Highest | Highest | Very High |
| Sparse GSI | Very Low | Very Low | Very High |

---

# Best Practices

- Create indexes only for real business access patterns.
- Prefer INCLUDE projections over ALL in most workloads.
- Regularly review CloudWatch metrics for index usage.
- Remove obsolete or unused indexes.
- Use Sparse GSIs whenever only a subset of records is queried.
- Consider write amplification before adding new indexes.

---

# Common Mistakes

## Creating "Future-Proof" Indexes

Developers often create indexes "just in case."

Most are never used.

---

## Choosing ALL Projection by Default

ALL projection duplicates every attribute and often doubles storage unnecessarily.

---

## Ignoring Write Amplification

Every write affects the table and all matching indexes.

Heavy write workloads become increasingly expensive.

---

## Never Reviewing Existing Indexes

Applications evolve.

Indexes that were useful years ago may no longer be needed.

Periodic audits reduce long-term operational costs.

---

# Architecture Perspective

```text
                   Application

                        │

                  Write Order

                        │

                        ▼

                  Base Table

                        │

      ┌─────────────────┼──────────────────┐

      ▼                 ▼                  ▼

 Email GSI         Status GSI        Date GSI

      │                 │                  │

      ▼                 ▼                  ▼

Additional Write   Additional Write   Additional Write

                        │

                        ▼

              Increased Storage & Cost
```

Every additional index improves query flexibility but also increases storage, write activity, and operational expense.

---

# Production Considerations

Large enterprise systems often perform **quarterly index reviews**.

Typical review questions include:

- Is this index still queried?
- Can projection be reduced?
- Would a Sparse GSI be more efficient?
- Is the Partition Key causing hot partitions?
- Can multiple access patterns share one composite index?

Treat indexes as production infrastructure that requires continuous optimization rather than a one-time design decision.

---

# Interview Notes

A common interview question is:

> **Why do GSIs increase write costs?**

Every write to the base table must also update each affected GSI, increasing the total number of write operations.

Another common question is:

> **Which projection type is usually the most cost-effective?**

**INCLUDE** is generally the best balance because it projects only the attributes required by application queries while avoiding the storage overhead of ALL projections.

Another common question is:

> **How can you reduce DynamoDB index costs?**

Reduce costs by creating only necessary indexes, using sparse indexes where appropriate, selecting minimal projection types, removing unused indexes, and monitoring CloudWatch metrics to optimize capacity and storage.

---

# Key Takeaways

- Every secondary index increases storage and write costs.
- Projection type has a major impact on index size and operational expense.
- Write amplification grows with every additional GSI or LSI.
- Sparse indexes can significantly reduce storage and write costs.
- Regularly monitor and remove unused indexes to keep DynamoDB deployments cost-efficient.
- Effective index design balances query performance, scalability, and long-term operational cost.