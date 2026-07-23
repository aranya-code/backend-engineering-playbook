# 11 - Common Index Design Patterns

## Overview

Indexes are not created randomly in production systems.

Instead, experienced DynamoDB architects repeatedly use a handful of proven **index design patterns** to solve common business problems.

These patterns have emerged from building systems such as:

- E-commerce platforms
- Banking applications
- IoT platforms
- Social networks
- SaaS products
- Event-driven architectures
- Workflow engines
- Analytics systems

Understanding these patterns is far more valuable than memorizing DynamoDB APIs because **production systems are designed around access patterns, not tables.**

---

# Design Philosophy

Every index should answer one question:

> **"What business query does this index support?"**

The design process should always be:

```text
Business Requirement

↓

Access Pattern

↓

Primary Key Design

↓

Secondary Index Design
```

Never:

```text
Create Table

↓

Add Random Indexes
```

---

# Pattern 1 — Lookup Pattern

## Purpose

Retrieve an item using an alternate identifier.

Example:

```text
User

↓

Email Address
```

instead of

```text
UserID
```

---

### Table

```text
PK = UserID
```

---

### GSI

```text
PK = Email
```

---

### Architecture

```text
Application

↓

Email

↓

Email GSI

↓

UserID

↓

Return User
```

---

### Production Examples

- Login using email
- Find customer by phone number
- Search employee by badge number
- Find product by SKU

---

# Pattern 2 — Time-Series Pattern

## Purpose

Retrieve records ordered by time.

Example:

```text
Device Readings

↓

Newest First
```

---

### GSI

```text
PK = DeviceID

SK = Timestamp
```

---

### Query

```text
Device

↓

Last Hour

↓

Last Day

↓

Last Week
```

---

### Production Examples

- IoT sensors
- Financial transactions
- Audit logs
- Monitoring systems
- User activity history

---

# Pattern 3 — Status Pattern

Retrieve items by workflow status.

Example:

```text
Pending Orders

Failed Jobs

Open Tickets
```

---

### GSI

```text
PK = Status

SK = CreatedDate
```

Better:

```text
PK = Status#Region
```

to improve partition distribution.

---

### Architecture

```text
Pending

↓

Newest Pending Items
```

---

### Production Examples

- Approval systems
- Support tickets
- Order processing
- Background jobs

---

# Pattern 4 — Sparse Index Pattern

Only index important records.

Example:

```text
FraudFlag
```

Only suspicious transactions appear.

---

### GSI

```text
PK = FraudFlag

SK = DetectionTime
```

---

### Architecture

```text
Transactions

↓

FraudFlag Exists?

↓

Yes

↓

Sparse GSI
```

---

### Production Examples

- Failed payments
- Escalated tickets
- Compliance reviews
- Security incidents

---

# Pattern 5 — Composite Sort Key Pattern

Support multiple dimensions using one Sort Key.

Example:

```text
HIGH#2026-07-20
```

Structure:

```text
Priority

+

Timestamp
```

Applications can query:

```text
HIGH

↓

Newest First
```

---

### Production Examples

- Task schedulers
- Workflow engines
- Priority queues

---

# Pattern 6 — Hierarchical Pattern

Represent parent-child relationships.

Composite Sort Key:

```text
USA#Texas#Dallas#Store10
```

Query:

```text
USA

↓

Texas

↓

All Stores
```

using:

```text
begins_with()
```

---

### Production Examples

- Organization hierarchy
- Product catalog
- File systems
- Geographic data

---

# Pattern 7 — Leaderboard Pattern

Retrieve highest-ranked items.

GSI

```text
PK = GameID

SK = Score
```

Query:

```text
Descending

↓

Top Players
```

---

### Production Examples

- Gaming
- Sales rankings
- Product popularity
- Employee performance

---

# Pattern 8 — Multi-Tenant Pattern

Group tenant data together.

```text
PK = TenantID

SK = ResourceID
```

Applications retrieve:

```text
Tenant

↓

Resources
```

---

### Benefits

- Logical isolation
- Efficient billing
- Tenant-specific queries

---

### Production Examples

- SaaS platforms
- CRM systems
- HR platforms

---

# Pattern 9 — Search Pattern

Support alternate lookup paths.

Base Table

```text
PK = ProductID
```

GSIs

```text
CategoryIndex

BrandIndex

SellerIndex
```

Applications search products using different business attributes.

---

### Production Examples

- Marketplace search
- Product catalog
- Customer directory

---

# Pattern 10 — Recent Activity Pattern

Retrieve latest activity.

```text
PK = UserID

SK = ActivityTimestamp
```

Applications query:

```text
Latest Activity
```

instead of scanning historical data.

---

### Production Examples

- Notifications
- Social media feeds
- User timelines
- Login history

---

# Pattern 11 — Event Sourcing Pattern

Store immutable events.

```text
PK = AggregateID

SK = EventTimestamp
```

Applications replay events chronologically.

---

### Production Examples

- Banking
- CQRS
- Audit systems
- Inventory management

---

# Pattern 12 — Analytics Pattern

Support reporting dashboards.

Example:

```text
PK = Region

SK = Date
```

Retrieve:

```text
Sales

For Region

Between Dates
```

---

### Production Examples

- BI dashboards
- Executive reports
- Operational metrics

---

# Pattern Comparison

| Pattern | Primary Purpose | Typical Keys |
|----------|-----------------|--------------|
| Lookup | Alternate lookup | Email, Phone |
| Time-Series | Chronological data | DeviceID + Timestamp |
| Status | Workflow state | Status + CreatedDate |
| Sparse | Small subsets | Flag + Time |
| Composite | Multi-dimensional queries | PK + Composite SK |
| Hierarchical | Parent-child navigation | Parent + Path |
| Leaderboard | Rankings | Category + Score |
| Multi-Tenant | Tenant isolation | TenantID + Resource |
| Search | Alternate discovery | Category, Brand |
| Recent Activity | Latest events | UserID + Timestamp |
| Event Sourcing | Immutable history | AggregateID + EventTime |
| Analytics | Reporting | Region + Date |

---

# Choosing the Right Pattern

| Requirement | Recommended Pattern |
|-------------|---------------------|
| Login by Email | Lookup |
| Latest Orders | Time-Series |
| Pending Tasks | Status |
| Failed Jobs | Sparse |
| Product Search | Search |
| User Timeline | Recent Activity |
| Company Hierarchy | Hierarchical |
| Tenant Isolation | Multi-Tenant |
| Financial Ledger | Event Sourcing |
| Sales Dashboard | Analytics |

---

# Combining Patterns

Production systems rarely use only one pattern.

Example:

Order Management System

```text
Primary Table

↓

CustomerID

↓

OrderID
```

Additional indexes:

```text
StatusIndex
```

```text
CustomerDateIndex
```

```text
PendingSparseIndex
```

```text
RegionAnalyticsIndex
```

Each supports a different business capability.

---

# Architecture Example

```text
                    Orders Table

                          │

      ┌───────────────────┼───────────────────┐

      ▼                   ▼                   ▼

CustomerDateGSI      StatusGSI        PendingSparseGSI

      │                   │                   │

Latest Orders     Workflow Queue     Manual Review

      ▼                   ▼                   ▼

Customer Portal    Operations Team     Support Team
```

One table can power multiple business functions through carefully designed indexes.

---

# Selecting an Index Pattern

Before creating an index, ask:

1. What business question does this query answer?
2. Will this query occur frequently?
3. Can the Primary Key already support it?
4. Will this Partition Key distribute traffic evenly?
5. Does the Sort Key support filtering or ordering?
6. Can multiple access patterns share one composite index?
7. Would a Sparse Index reduce storage and write costs?

If you cannot clearly answer these questions, reconsider the index design.

---

# Best Practices

- Design indexes around business access patterns.
- Reuse composite indexes whenever possible.
- Prefer high-cardinality Partition Keys.
- Combine Sparse Indexes with composite Sort Keys.
- Monitor usage and remove obsolete indexes.
- Review index designs as application requirements evolve.

---

# Common Mistakes

## Creating One Index Per Screen

Different UI screens often share the same access pattern.

Avoid creating duplicate indexes for similar queries.

---

## Ignoring Future Growth

A design that works for 10,000 records may fail with 500 million records.

Plan for long-term scalability.

---

## Using Low-Cardinality Keys

Indexes built on values like:

```text
ACTIVE
```

or

```text
USA
```

can create severe hot partitions under heavy traffic.

---

## Duplicating Access Patterns

If two indexes answer the same business query, one is likely unnecessary.

Consolidate where possible.

---

# Architecture Perspective

```text
                  Business Requirements

                           │

                           ▼

                  Identify Access Patterns

                           │

                           ▼

                 Select Design Pattern

                           │

        ┌──────────────────┼──────────────────┐

        ▼                  ▼                  ▼

   Lookup Pattern    Time-Series Pattern   Sparse Pattern

        │                  │                  │

        └──────────────────┼──────────────────┘

                           ▼

                  Optimized Secondary Index

                           │

                           ▼

                 Low-Latency Query Response
```

The best DynamoDB schemas are built by selecting the right pattern for each access requirement rather than creating indexes reactively.

---

# Production Considerations

Large-scale enterprise systems rarely exceed **5–10 carefully designed secondary indexes**, even when supporting dozens of application features.

The reason is that each index is intentionally built to satisfy **multiple related access patterns**, minimizing storage, write amplification, and operational complexity.

Successful DynamoDB architectures prioritize:

- Reusable composite indexes
- Sparse indexes for operational workflows
- High-cardinality Partition Keys
- Continuous monitoring and refinement

---

# Interview Notes

A common interview question is:

> **What is the most common DynamoDB index design pattern?**

The **Lookup Pattern** using a GSI for alternate identifiers (such as Email or Username) is one of the most common, followed closely by Time-Series and Composite Index patterns.

Another common question is:

> **Can one GSI support multiple business queries?**

Yes. A well-designed composite index with an appropriate Partition Key and Sort Key can support multiple related access patterns, reducing the need for additional indexes.

Another common question is:

> **Why are index design patterns important?**

They provide proven solutions for recurring architectural problems, helping engineers build scalable, cost-efficient DynamoDB applications without relying on table scans.

---

# Key Takeaways

- Index design patterns are reusable solutions to common DynamoDB access requirements.
- Always start with business queries before designing indexes.
- Composite, Sparse, Time-Series, and Lookup patterns are among the most widely used in production.
- Reusing indexes across multiple access patterns reduces storage, write costs, and operational complexity.
- Good index design is driven by access patterns, not by database structure.
- Mastering these patterns is essential for designing scalable, production-grade DynamoDB systems.