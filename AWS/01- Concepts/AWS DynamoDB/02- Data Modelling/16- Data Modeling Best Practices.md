# 16 - Data Modeling Best Practices

## Overview

Designing an efficient DynamoDB schema is fundamentally different from designing a relational database.

In SQL databases, developers typically:

1. Design normalized tables
2. Define relationships
3. Add indexes
4. Write queries

In DynamoDB, the recommended approach is almost the reverse:

1. Identify business access patterns
2. Design partition and sort keys
3. Optimize for Query operations
4. Add secondary indexes only when necessary
5. Duplicate data when it improves performance

A well-designed DynamoDB data model can serve millions of requests with single-digit millisecond latency, while a poor design may suffer from throttling, hot partitions, excessive scans, and expensive redesigns.

This chapter summarizes the most important best practices used in production DynamoDB systems.

---

# Think About Queries, Not Tables

The biggest mindset shift is this:

> **Design for how data will be accessed—not how it should be stored.**

Relational thinking:

```text
Customers

Orders

Products

Invoices

Payments
```

DynamoDB thinking:

```text
Get Customer

↓

Get Customer Orders

↓

Get Active Orders

↓

Get Recent Payments
```

The access pattern determines the schema.

---

# Identify Access Patterns First

Before creating a table, answer questions like:

- How will users search for data?
- What are the most frequent queries?
- Which operations must be low latency?
- Which queries occur together?
- What reports are required?

Example:

E-commerce application

```text
Get Order

Get Orders by Customer

Get Active Orders

Get Orders by Date

Get Product Inventory
```

These become the foundation of your schema.

---

# Choose Good Partition Keys

A Partition Key should:

- Distribute traffic evenly
- Prevent hot partitions
- Support common queries

Good example:

```text
CUSTOMER#100
```

Poor example:

```text
STATUS#ACTIVE
```

Thousands of users may share:

```text
STATUS#ACTIVE
```

creating a hotspot.

---

# Design Meaningful Sort Keys

Sort Keys allow:

- Ordering
- Filtering
- Hierarchies
- Versioning
- Time-series queries

Example:

```text
PK = CUSTOMER#100

SK = ORDER#2026-07-20
```

Now:

```text
Query Customer

↓

Orders Sorted by Date
```

No additional index required.

---

# Design for Query, Not Scan

Always prefer:

```text
Query
```

Avoid:

```text
Scan
```

Query:

- Reads one partition
- Efficient
- Low latency

Scan:

- Reads the entire table
- Expensive
- Slow
- Poor scalability

Production systems should rarely depend on table scans.

---

# Keep Items Small

Smaller items provide:

- Faster reads
- Lower latency
- Lower storage cost
- Better cache utilization

Instead of:

```json
{
    "Customer": "...",
    "Orders": [...],
    "Invoices": [...],
    "Reviews": [...],
    "Wishlist": [...]
}
```

Store related entities separately.

---

# Denormalize Intentionally

SQL:

```text
Customer

↓

JOIN

↓

Orders
```

DynamoDB:

Duplicate data.

Example:

Order Item:

```json
{
    "CustomerName": "Alice",
    "CustomerTier": "Gold"
}
```

Instead of performing joins, duplicate only the attributes required by your access patterns.

---

# Duplicate Data Strategically

Data duplication is expected.

Duplicate when it improves:

- Read performance
- Simplicity
- Scalability

Avoid duplicating:

- Large documents
- Frequently changing data
- Unnecessary attributes

The goal is to reduce database round trips, not maximize storage efficiency.

---

# Use Composite Keys

Composite keys provide flexibility.

Example:

```text
PK = CUSTOMER#100

SK = ORDER#500
```

Other examples:

```text
PRODUCT#200

REVIEW#15
```

```text
PROJECT#10

TASK#5
```

Composite keys support multiple related entities within a single partition.

---

# Keep Related Data Together

Store data that is frequently accessed together.

Example:

```text
CUSTOMER#100

↓

PROFILE

↓

ORDER#1

↓

ORDER#2

↓

PAYMENT#1
```

One partition.

One query.

---

# Design for High Cardinality

Good Partition Keys have many unique values.

Good:

```text
USER#10001

USER#10002

USER#10003
```

Poor:

```text
USA

CANADA

UK
```

High-cardinality keys distribute data more evenly across partitions.

---

# Monitor Hot Partitions

Watch for:

- High write rates
- High read rates
- Uneven traffic
- Frequent throttling

Solutions:

- Write Sharding
- Better key selection
- Time bucketing
- Adaptive Capacity

---

# Use GSIs Carefully

Global Secondary Indexes are powerful.

However, every GSI:

- Consumes write capacity
- Requires additional storage
- Must be maintained

Create GSIs only for important access patterns.

Avoid creating an index "just in case."

---

# Keep GSIs Sparse

A sparse index stores only selected items.

Example:

Only active orders:

```text
Status = ACTIVE
```

Inactive orders are omitted.

Benefits:

- Smaller indexes
- Faster queries
- Lower costs

---

# Avoid Large Partitions

A partition containing millions of items can become inefficient.

Instead of:

```text
CUSTOMER#100
```

forever,

consider:

```text
CUSTOMER#100#2026
```

or

```text
CUSTOMER#100#July
```

Time bucketing helps distribute storage and traffic.

---

# Use Time Bucketing

For time-series data:

Avoid:

```text
DEVICE#100
```

forever.

Prefer:

```text
DEVICE#100#2026-07
```

Benefits:

- Smaller partitions
- Faster queries
- Better scalability

---

# Implement Versioning When Needed

Instead of overwriting:

```text
Document
```

Store:

```text
CURRENT

VERSION#1

VERSION#2

VERSION#3
```

This enables:

- Audit history
- Rollback
- Compliance

---

# Plan for Growth

Design schemas assuming:

```text
Today

↓

10,000 Users
```

Future:

```text
10 Million Users
```

Changing primary keys later often requires migrating the entire table.

Choose keys with long-term scalability in mind.

---

# Use TTL for Temporary Data

Suitable for:

- Sessions
- Temporary tokens
- Cache entries
- Short-lived events
- Temporary notifications

Expired items are automatically removed by DynamoDB.

---

# Use Streams for Event-Driven Systems

DynamoDB Streams enable:

```text
Insert

↓

Lambda

↓

Analytics
```

or

```text
Update

↓

Notification

↓

Email
```

Streams allow downstream systems to react to data changes without impacting the primary workload.

---

# Monitor Performance

Track metrics such as:

- Read capacity usage
- Write capacity usage
- Throttled requests
- Partition utilization
- GSI consumption
- Request latency

CloudWatch provides visibility into these metrics.

---

# Think About Cost

Every design decision affects cost.

Examples:

- Larger items cost more to read.
- Every GSI consumes additional writes.
- Strongly consistent reads cost more capacity than eventually consistent reads.
- Scans consume significantly more capacity than targeted queries.
- Poor key design may require unnecessary read operations.

Efficient schemas reduce both latency and operational cost.

---

# Real-World Example

An online marketplace stores:

```text
PK = CUSTOMER#500

SK = PROFILE
```

```text
PK = CUSTOMER#500

SK = ORDER#1001
```

```text
PK = CUSTOMER#500

SK = ORDER#1002
```

```text
PK = CUSTOMER#500

SK = PAYMENT#100
```

The application can retrieve the customer profile, recent orders, and payment history using efficient Query operations without joins or scans.

---

# Best Practices Checklist

✅ Design around access patterns

✅ Choose high-cardinality partition keys

✅ Use meaningful sort keys

✅ Prefer Query over Scan

✅ Keep items small

✅ Denormalize intentionally

✅ Duplicate data only when beneficial

✅ Use GSIs only when necessary

✅ Monitor hot partitions

✅ Apply write sharding for high-write workloads

✅ Use TTL for temporary data

✅ Enable Streams for event-driven architectures

✅ Plan for long-term scalability

---

# Common Mistakes

## Designing Like a Relational Database

Attempting to normalize everything leads to excessive queries and poor performance.

---

## Ignoring Access Patterns

Without understanding how data is queried, it is impossible to design an efficient schema.

---

## Overusing GSIs

Every additional GSI increases storage requirements and write costs.

---

## Using Scan in Production

Scans become increasingly expensive as tables grow.

Design targeted Query operations instead.

---

## Choosing Low-Cardinality Keys

Partition keys with very few distinct values create uneven traffic distribution and hot partitions.

---

## Underestimating Future Scale

Primary keys are difficult to change after deployment.

Design with future growth in mind.

---

# Architecture Perspective

```text
Business Requirements

        │

        ▼

Identify Access Patterns

        │

        ▼

Design Primary Keys

        │

        ▼

Choose GSIs (If Needed)

        │

        ▼

Optimize Reads

        │

        ▼

Validate Distribution

        │

        ▼

Deploy

        │

        ▼

Monitor & Refine
```

Successful DynamoDB schemas evolve from business requirements rather than database structure.

---

# Production Considerations

Enterprise teams typically review DynamoDB schemas against a checklist before deployment:

- Can every critical query use `Query` instead of `Scan`?
- Are partition keys evenly distributed?
- Will the design still work at 100x traffic?
- Are GSIs justified by business requirements?
- Can large tenants or popular entities create hot partitions?
- Is data retention handled using TTL or archival?
- Are Streams required for downstream processing?

Performing these reviews early helps avoid expensive schema migrations later.

---

# Interview Notes

A common interview question is:

> **What is the biggest difference between SQL and DynamoDB data modeling?**

SQL models data around relationships and normalization. DynamoDB models data around access patterns, often using denormalization and data duplication to optimize reads.

Another common question is:

> **What are the most important considerations when choosing a partition key?**

The partition key should support common queries, have high cardinality, distribute traffic evenly, and avoid creating hot partitions.

Another common question is:

> **When should you use a GSI?**

Use a Global Secondary Index only when a new access pattern cannot be efficiently supported by the primary key. Each GSI introduces additional storage and write costs, so indexes should be created intentionally.

---

# Key Takeaways

- Design DynamoDB schemas around business access patterns.
- Choose partition keys that distribute data evenly.
- Prefer `Query` operations over `Scan`.
- Keep items small and duplicate data strategically.
- Use GSIs sparingly and only for required access patterns.
- Monitor performance continuously and design for future scale.
- Good data modeling is the foundation of every successful DynamoDB application.