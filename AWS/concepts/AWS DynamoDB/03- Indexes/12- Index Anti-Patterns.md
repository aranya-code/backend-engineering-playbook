# 12 - Index Anti-Patterns

## Overview

Knowing how to design a good index is only half of the equation.

Senior DynamoDB engineers spend just as much time **avoiding bad index designs**.

Many production performance issues are not caused by DynamoDB itself—they are caused by poorly designed secondary indexes.

Common consequences include:

- Hot partitions
- High AWS bills
- Throttling
- Slow queries
- Poor scalability
- Difficult schema evolution
- Excessive write amplification

Understanding these anti-patterns helps prevent expensive architectural mistakes before they reach production.

---

# What is an Anti-Pattern?

An anti-pattern is a design that appears reasonable at first but causes significant operational problems as the system scales.

Example:

```text
Need Search

↓

Create Index

On Every Field
```

Works for:

```text
1,000 Records
```

Fails for:

```text
500 Million Records
```

---

# Anti-Pattern 1 — Indexing Every Attribute

One of the most common mistakes is creating a GSI for every searchable attribute.

Example:

```text
EmailIndex

PhoneIndex

CountryIndex

CityIndex

DepartmentIndex

ManagerIndex

StatusIndex

RoleIndex
```

Every write now updates:

```text
Base Table

↓

8 GSIs
```

---

## Why It Is Bad

Problems:

- High write cost
- Large storage usage
- Difficult maintenance
- Longer deployments
- Complex monitoring

---

## Better Approach

Ask:

```text
Is This Query

Actually Used?
```

Only create indexes for critical business access patterns.

---

# Anti-Pattern 2 — Low-Cardinality Partition Keys

Bad design:

```text
PK = Status
```

Values:

```text
ACTIVE

ACTIVE

ACTIVE

ACTIVE

ACTIVE
```

Millions of records map to one partition.

Result:

```text
Hot Partition
```

---

## Better Design

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

or

```text
Status#Shard
```

Traffic becomes evenly distributed.

---

# Anti-Pattern 3 — Using Scan Instead of Designing an Index

Application:

```text
Need Orders

By Customer
```

Developer:

```text
Scan Table

↓

Filter Customer
```

This defeats the purpose of DynamoDB.

---

## Better Design

Create:

```text
GSI

PK = CustomerID
```

Applications perform:

```text
Query

Instead of

Scan
```

---

# Anti-Pattern 4 — Using ALL Projection Everywhere

Developer chooses:

```text
Projection = ALL
```

for every index.

Now every index stores:

```text
Entire Item
```

Problems:

- Storage doubles
- Write cost increases
- Backup size grows
- Replication slows

---

## Better Design

Usually:

```text
INCLUDE
```

or

```text
KEYS_ONLY
```

is sufficient.

---

# Anti-Pattern 5 — Duplicate Indexes

Example:

```text
EmailIndex
```

and

```text
UserEmailIndex
```

Both support:

```text
Find User

By Email
```

Only one is necessary.

Duplicate indexes waste:

- Storage
- Write capacity
- Maintenance effort

---

# Anti-Pattern 6 — Ignoring Future Access Patterns

Poor design:

```text
PK = UserID
```

No Sort Key.

Later requirements:

- Latest Orders
- Orders This Month
- Orders Between Dates

Now:

New indexes.

Schema changes.

Migration work.

---

## Better Design

Use:

```text
PK = CustomerID

SK = OrderDate
```

Supports multiple future queries.

---

# Anti-Pattern 7 — Using Random Sort Keys

Example:

```text
UUID
```

Random values cannot support:

- Ordering
- Range queries
- Pagination

---

## Better Sort Keys

Examples:

```text
Timestamp
```

```text
Priority#Timestamp
```

```text
Status#Date
```

These support meaningful business queries.

---

# Anti-Pattern 8 — Large Projections

Projecting:

```text
Images

PDFs

Videos

Large JSON

Binary Files
```

into every GSI.

Problems:

- Massive storage
- High write latency
- Expensive replication

---

## Better Approach

Keep large objects outside the index.

Project only metadata.

---

# Anti-Pattern 9 — Assuming GSIs Are Strongly Consistent

Developer:

```text
Update User

↓

Immediately Query GSI
```

Expected:

```text
New Data
```

Reality:

```text
Old Data

Possible
```

GSIs are eventually consistent.

---

## Better Design

Critical read-after-write workflows should query:

```text
Base Table
```

or

```text
LSI
```

---

# Anti-Pattern 10 — Ignoring Hot Partitions

Example:

```text
PK = Country
```

Data:

```text
USA

↓

80 Million Records
```

Traffic:

```text
Everyone

↓

USA Partition
```

Result:

- Throttling
- Increased latency
- Uneven scaling

---

## Better Design

Example:

```text
USA#East

USA#West

USA#Central
```

or

```text
Country#Month
```

---

# Anti-Pattern 11 — Never Reviewing Index Usage

Many teams create indexes and never revisit them.

Example:

```text
AnalyticsIndex
```

Created:

```text
3 Years Ago
```

Current usage:

```text
Zero Queries
```

Still consuming:

- Storage
- Writes
- Backups

Unused indexes should be removed.

---

# Anti-Pattern 12 — Creating One Index Per API Endpoint

Poor API design:

```text
GET /orders

↓

OrderIndex
```

```text
GET /recent-orders

↓

RecentOrderIndex
```

```text
GET /monthly-orders

↓

MonthlyOrderIndex
```

Most of these can be handled by:

```text
One Composite Index
```

using different query conditions.

---

# Anti-Pattern 13 — Ignoring Write Amplification

Developer creates:

```text
12 GSIs
```

Application:

```text
1000 Writes/Sec
```

Actual writes:

```text
13,000 Storage Writes
```

Costs become enormous.

Always estimate write amplification before introducing a new index.

---

# Anti-Pattern 14 — Designing Without Access Patterns

Poor process:

```text
Create Table

↓

Create Indexes

↓

Build Application
```

Correct process:

```text
Business Requirements

↓

Access Patterns

↓

Primary Key

↓

Indexes

↓

Implementation
```

---

# Real-World Example

An online marketplace created GSIs for:

- Seller
- Buyer
- Product
- Brand
- Category
- Discount
- Rating
- Color
- Size
- Warehouse

After monitoring:

Only:

```text
Seller

Category

Brand
```

were frequently queried.

Removing unused indexes reduced:

- Storage costs
- Write costs
- Backup time

without affecting the application.

---

# Warning Signs

An index likely needs redesign if you observe:

- Frequent throttling
- Hot partitions
- Large Scan operations
- High write costs
- Very low index utilization
- Slow query latency
- Rapid storage growth

---

# Prevention Checklist

Before creating an index, ask:

- Does this support a real business requirement?
- Can an existing index support this query?
- Is the Partition Key high-cardinality?
- Is the Sort Key meaningful?
- Will projection remain small?
- Will writes become significantly more expensive?
- Can this index support multiple access patterns?

---

# Best Practices

- Design indexes around access patterns.
- Prefer reusable composite indexes.
- Use Sparse Indexes when appropriate.
- Monitor CloudWatch metrics regularly.
- Keep projections minimal.
- Remove obsolete indexes.
- Review index design during architecture reviews.

---

# Common Mistakes Summary

| Mistake | Better Solution |
|----------|-----------------|
| Index every field | Index only business-critical access patterns |
| Low-cardinality Partition Key | High-cardinality Partition Key |
| Scan instead of Query | Design an appropriate index |
| ALL projection everywhere | Prefer INCLUDE |
| Duplicate indexes | Consolidate into one index |
| Random Sort Keys | Use business-friendly ordering keys |
| Ignore write amplification | Estimate write costs before deployment |
| Never review indexes | Periodic optimization and cleanup |

---

# Architecture Perspective

```text
                  Business Query

                        │

                        ▼

             Existing Index Works?

              ┌─────────┴─────────┐

             Yes                  No

              │                   │

              ▼                   ▼

      Reuse Existing      Design New Access Pattern

              │                   │

              ▼                   ▼

        Avoid Duplicate     Build Optimized GSI

              │                   │

              └─────────┬─────────┘

                        ▼

              Efficient DynamoDB Design
```

Good DynamoDB architectures emphasize **reusing indexes whenever possible**, rather than creating new ones for every feature request.

---

# Production Considerations

Mature engineering teams perform regular **index health reviews** alongside performance and cost optimization.

Typical review questions include:

- Which indexes have the highest write amplification?
- Which indexes have low query frequency?
- Are any indexes causing hot partitions?
- Can two or more indexes be consolidated?
- Are projection types still appropriate?
- Have new business access patterns emerged that require redesign?

Treat indexes as living infrastructure that evolves with the application rather than static configuration.

---

# Interview Notes

A common interview question is:

> **What is the most common DynamoDB index anti-pattern?**

Creating indexes without first identifying business access patterns. This often leads to unnecessary indexes, higher costs, and poor scalability.

Another common question is:

> **Why is indexing every attribute a bad idea?**

Each index increases storage, write amplification, and operational complexity. Only attributes supporting important business queries should be indexed.

Another common question is:

> **How do you identify an unhealthy index?**

Indicators include low query usage, frequent throttling, hot partitions, excessive storage consumption, high write costs, and reliance on Scan operations instead of Query operations.

---

# Key Takeaways

- Poor index design is a leading cause of DynamoDB performance and cost problems.
- Avoid creating indexes without clear business access patterns.
- High-cardinality Partition Keys and reusable composite indexes lead to better scalability.
- Monitor index utilization regularly and remove obsolete indexes.
- Minimize projections and account for write amplification before adding new indexes.
- Preventing index anti-patterns is significantly easier and less expensive than fixing them in production.