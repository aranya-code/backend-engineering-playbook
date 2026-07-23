# 10 - Index Performance & Optimization

## Overview

Creating a secondary index is only the first step.

The real challenge is ensuring that the index continues to perform efficiently as the application grows from:

```text
Thousands

↓

Millions

↓

Billions

of items
```

Poorly designed indexes eventually lead to:

- Hot partitions
- Throttling
- Increased latency
- Higher AWS costs
- Uneven traffic distribution
- Poor scalability

Production DynamoDB systems require continuous index optimization based on real traffic patterns rather than assumptions.

---

# What Determines Index Performance?

The performance of a DynamoDB index depends on several factors:

- Partition Key design
- Sort Key design
- Item size
- Projection type
- Traffic distribution
- Read/write ratio
- Capacity mode
- Access patterns

All of these work together to determine how efficiently an index performs.

---

# Internal Query Flow

```text
             Application

                   │

             Query Index

                   │

                   ▼

          Find Partition

                   │

                   ▼

        Read Matching Items

                   │

                   ▼

          Return Response
```

The faster DynamoDB can locate the correct partition and retrieve a small number of items, the better the performance.

---

# Importance of Partition Keys

The Partition Key has the greatest impact on index performance.

Good example:

```text
CustomerID
```

Millions of unique customers create excellent distribution.

Poor example:

```text
Status = ACTIVE
```

Millions of active records share one partition.

Result:

```text
Hot Partition
```

---

# High Cardinality

High-cardinality keys create many partitions.

Example:

```text
Email

UserID

OrderID

InvoiceID
```

Excellent choices.

---

# Low Cardinality

Avoid keys like:

```text
Country

Status

Department

Region
```

These values repeat frequently.

Traffic becomes concentrated.

---

# Hot Partition Example

Suppose a GSI uses:

```text
PK = Status
```

Data:

```text
ACTIVE

ACTIVE

ACTIVE

ACTIVE

ACTIVE

ACTIVE
```

Every request targets:

```text
One Partition
```

Performance degrades under heavy traffic.

---

# Better Design

Instead of:

```text
Status
```

Use:

```text
Status#Region
```

or

```text
Status#Date
```

Example:

```text
ACTIVE#US

ACTIVE#EU

ACTIVE#APAC
```

Traffic spreads naturally.

---

# Sort Key Optimization

Good Sort Keys enable:

- Ordering
- Filtering
- Range queries

Example:

```text
OrderDate
```

Queries:

```text
Latest Orders
```

or

```text
Orders Between Dates
```

become extremely efficient.

---

# Composite Sort Keys

Instead of:

```text
Timestamp
```

Consider:

```text
Priority#Timestamp
```

Example:

```text
HIGH#2026-07-21

LOW#2026-07-22
```

Supports:

- Priority filtering
- Chronological ordering

using a single Sort Key.

---

# Reduce Item Size

Large items reduce performance.

Bad:

```text
Customer

↓

Entire Purchase History

↓

Images

↓

Invoices

↓

Comments
```

Good:

```text
Customer Summary
```

Store large objects separately when possible.

---

# Projection Optimization

Projection directly impacts index performance.

## KEYS_ONLY

Smallest index.

Fastest writes.

---

## INCLUDE

Balanced.

Most production systems.

---

## ALL

Largest.

Higher storage.

Higher replication cost.

Project only attributes required by queries.

---

# Query vs Scan

Always prefer:

```text
Query
```

instead of:

```text
Scan
```

Query:

```text
One Partition
```

Scan:

```text
Entire Table
```

Indexes exist to eliminate scans.

---

# Pagination

Avoid reading thousands of items at once.

Instead:

```text
Query

↓

100 Items

↓

Next Page

↓

100 Items
```

Pagination reduces latency and memory usage.

---

# Filter Expressions

Bad:

```text
Query

↓

10000 Items

↓

Filter

↓

10 Results
```

Although only 10 items are returned, DynamoDB still reads all 10,000 matching items.

Better:

Design the index so the required items can be identified directly by the key structure.

---

# Efficient Access Patterns

Example:

Need:

```text
Orders

For Customer

Last 30 Days
```

Good index:

```text
PK = CustomerID

SK = OrderDate
```

Bad index:

```text
PK = CustomerID
```

Without the Sort Key, filtering becomes expensive.

---

# Sparse Index Optimization

Sparse indexes reduce:

- Storage
- Reads
- Writes

Instead of:

```text
All Orders
```

Index only:

```text
Pending Orders
```

Smaller indexes generally perform better.

---

# Avoid Over-Indexing

Poor design:

```text
EmailIndex

CountryIndex

DepartmentIndex

StatusIndex

CityIndex

PhoneIndex

ManagerIndex
```

Many of these may never be queried.

Each one:

- Uses storage
- Increases writes
- Adds maintenance

---

# Monitor CloudWatch Metrics

Useful metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- SuccessfulRequestLatency
- ThrottledRequests
- OnlineIndexConsumedWriteCapacity
- OnlineIndexThrottleEvents

These metrics help identify:

- Hot indexes
- Underused indexes
- Capacity bottlenecks

---

# Adaptive Capacity

Adaptive Capacity automatically shifts throughput toward busy partitions.

Example:

```text
Partition A

High Traffic
```

Adaptive Capacity temporarily allocates additional resources.

However,

it is **not** a substitute for good key design.

---

# Write Optimization

Heavy write workloads benefit from:

- Minimal projections
- Fewer GSIs
- Sparse indexes
- High-cardinality Partition Keys

Every additional index increases write latency.

---

# Read Optimization

Read-heavy workloads benefit from:

- Composite indexes
- INCLUDE projections
- Well-designed Sort Keys
- Query operations
- Proper pagination

These reduce both latency and cost.

---

# Real-World Example – Social Media

Posts table.

Need:

```text
Latest Posts

By User
```

Index:

```text
PK = UserID

SK = PostTimestamp
```

Queries:

```text
Newest First
```

No scans.

---

# Real-World Example – IoT

Sensor readings.

```text
PK = DeviceID

SK = Timestamp
```

Retrieve:

```text
Last Hour
```

Only a small range of data is read.

Performance remains predictable even with billions of records.

---

# Real-World Example – Banking

Transactions.

```text
PK = AccountID

SK = TransactionDate
```

Retrieve:

```text
Last 20 Transactions
```

Descending query.

No filtering required.

---

# Performance Optimization Checklist

Before deploying a new index, verify:

- High-cardinality Partition Key
- Meaningful Sort Key
- Minimal projection
- No Scan operations
- Supports actual business queries
- Sparse design where appropriate
- Pagination strategy
- CloudWatch monitoring enabled

---

# Best Practices

- Design indexes around access patterns, not table structure.
- Prefer Query over Scan.
- Use high-cardinality Partition Keys.
- Keep projected attributes small.
- Use composite Sort Keys for multiple query dimensions.
- Regularly review index performance metrics.
- Remove unused indexes.

---

# Common Mistakes

## Using Low-Cardinality Keys

This often creates hot partitions and throttling.

---

## Ignoring Sort Keys

Without a meaningful Sort Key, applications perform unnecessary filtering.

---

## Returning Large Result Sets

Avoid querying thousands of items in one request.

Use pagination.

---

## Overusing ALL Projections

Copying every attribute into every index increases storage and slows writes.

---

## Assuming Adaptive Capacity Solves Everything

Adaptive Capacity improves uneven workloads, but it cannot fix fundamentally poor Partition Key design.

---

# Performance Comparison

| Design Choice | Performance Impact |
|---------------|--------------------|
| High-cardinality Partition Key | Excellent |
| Low-cardinality Partition Key | Poor |
| Composite Index | Excellent |
| Sparse Index | Excellent |
| Query Operation | Excellent |
| Scan Operation | Poor |
| INCLUDE Projection | High |
| ALL Projection | Medium (higher storage/write cost) |
| KEYS_ONLY Projection | Excellent writes, may require additional reads |

---

# Architecture Perspective

```text
                  Application

                        │

                  Query Index

                        │

                        ▼

          High-Cardinality Partition

                        │

                        ▼

            Sorted Item Collection

                        │

                        ▼

              Small Result Set

                        │

                        ▼

             Fast Response (<10 ms)
```

Efficient index design minimizes the amount of data DynamoDB must examine and maximizes partition distribution, resulting in predictable low-latency performance.

---

# Production Considerations

Large enterprise applications routinely perform **index performance reviews** during capacity planning.

Typical optimization activities include:

- Identifying hot partitions
- Reviewing unused GSIs
- Reducing projection size
- Introducing Sparse Indexes
- Redesigning composite keys
- Monitoring latency trends
- Load testing new access patterns before production deployment

Index optimization is an ongoing operational responsibility rather than a one-time design task.

---

# Interview Notes

A common interview question is:

> **What is the most important factor affecting DynamoDB index performance?**

The Partition Key design. High-cardinality Partition Keys distribute traffic evenly across partitions, preventing hot partitions and improving scalability.

Another common question is:

> **How do you optimize a slow DynamoDB index?**

Review the Partition Key distribution, reduce projection size, replace Scan operations with Query operations, use composite keys, implement pagination, and monitor CloudWatch metrics for bottlenecks.

Another common question is:

> **Can Adaptive Capacity fix a poorly designed index?**

No. Adaptive Capacity can temporarily redistribute throughput, but it cannot compensate for fundamentally poor Partition Key design or inappropriate access patterns.

---

# Key Takeaways

- Index performance depends primarily on Partition Key design and access patterns.
- High-cardinality Partition Keys distribute traffic evenly and improve scalability.
- Composite indexes and meaningful Sort Keys enable efficient ordering and range queries.
- Query operations are significantly more efficient than Scan operations.
- Projection type, item size, and pagination all influence performance and cost.
- Continuous monitoring and optimization are essential for maintaining high-performance DynamoDB indexes in production.