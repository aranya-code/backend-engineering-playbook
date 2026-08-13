# 06 - Composite Index Design

## Overview

A **Composite Index** in DynamoDB is a secondary index that uses **both a Partition Key (PK) and a Sort Key (SK)** to support complex query patterns.

While a simple index allows querying by a single attribute, a composite index enables applications to:

- Filter data into logical partitions
- Sort data within each partition
- Perform efficient range queries
- Retrieve the latest or earliest records
- Build scalable business queries without table scans

In production systems, most Global Secondary Indexes (GSIs) and Local Secondary Indexes (LSIs) are designed as **composite indexes** because they provide significantly more flexibility than single-key indexes.

---

# Why Do We Need Composite Indexes?

Suppose an e-commerce application stores orders.

Business requirements:

```text
Find Orders

By Customer
```

Simple GSI:

```text
PK = CustomerID
```

Works.

Later, Product Management requests:

```text
Show Customer Orders

Sorted By Order Date
```

A Partition Key alone cannot define ordering.

A Composite Index solves this by adding a Sort Key.

```text
PK = CustomerID

SK = OrderDate
```

---

# What is a Composite Index?

A Composite Index consists of:

```text
Partition Key

+

Sort Key
```

Example:

```text
PK = Department

SK = JoiningDate
```

This allows queries like:

```text
All Employees

↓

Engineering

↓

Sorted by Joining Date
```

---

# Visual Representation

```text
            GSI

PK = CustomerID

SK = OrderDate

----------------------------

Customer100   2026-07-01

Customer100   2026-07-15

Customer100   2026-07-20

Customer200   2026-07-05

Customer200   2026-07-18
```

Each customer's data is grouped together and sorted by date.

---

# Internal Architecture

```text
                  CustomerID

                        │

        ┌───────────────┴───────────────┐

        ▼                               ▼

    Customer100                   Customer200

        │                               │

        ▼                               ▼

Sorted by Date                 Sorted by Date
```

Each partition maintains its own sorted order.

---

# Query Capabilities

Composite indexes support:

- Exact partition lookups
- Ordered retrieval
- Range queries
- Prefix searches
- Pagination

Unlike a simple index, applications can retrieve much richer datasets efficiently.

---

# Example 1 – Orders

Table:

```text
PK = OrderID
```

Business requirement:

```text
Customer Orders

Sorted by Date
```

Composite GSI:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
Customer100

↓

Latest Orders
```

---

# Example 2 – Employees

Requirement:

```text
Engineering Employees

Sorted by Joining Date
```

Composite GSI:

```text
PK = Department

SK = JoiningDate
```

Query:

```text
Department

↓

Engineering

↓

Ascending Date
```

---

# Example 3 – Banking

Transactions:

```text
PK = AccountNumber

SK = TransactionTime
```

Application:

```text
Show Last 20 Transactions
```

Because transactions are ordered,

the query simply reads the latest records.

---

# Example 4 – Chat Application

Messages:

```text
PK = ChatRoomID

SK = MessageTimestamp
```

Query:

```text
Latest Messages

For Room
```

Applications never scan the table.

---

# Example 5 – IoT Sensors

```text
PK = DeviceID

SK = Timestamp
```

Query:

```text
Sensor Readings

Last Hour
```

Efficient range query.

---

# Range Queries

Composite indexes support operators like:

```text
Between
```

```text
Greater Than
```

```text
Less Than
```

```text
Begins With
```

Example:

```text
Customer100

↓

Orders

Between

July 1

and

July 31
```

No scan required.

---

# Sorting

Sort Keys are automatically ordered.

Example:

```text
2026-07-01

2026-07-05

2026-07-15

2026-07-20
```

Applications may retrieve:

- Oldest first
- Newest first

using query direction.

---

# Descending Queries

Default:

```text
Ascending
```

Applications can request:

```text
Reverse Order
```

Result:

```text
Newest

↓

Oldest
```

Ideal for:

- Recent orders
- Latest notifications
- Newest comments
- Activity feeds

---

# Composite Key Design

Good design:

```text
PK = CustomerID

SK = OrderDate
```

Poor design:

```text
PK = Country

SK = Status
```

Reason:

```text
Millions

Of Records

One Partition
```

Hot partition risk.

---

# Composite Sort Keys

Sort Keys often combine multiple attributes.

Example:

```text
2026#07#20#Order100
```

or

```text
HIGH#2026-07-20
```

Benefits:

- Multiple dimensions
- Natural ordering
- Efficient filtering

---

# Hierarchical Sorting

Example:

```text
Country

↓

State

↓

City

↓

Store
```

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

using prefix matching.

---

# Time-Series Pattern

One of the most common production designs.

```text
PK = DeviceID

SK = Timestamp
```

Supports:

- Latest events
- Historical events
- Time windows
- Pagination

---

# Event Logs

Application logs:

```text
PK = ServiceName

SK = Timestamp
```

Query:

```text
Payment Service

↓

Last 100 Errors
```

Very common monitoring pattern.

---

# Combining with Sparse Indexes

Example:

```text
PK = FailedJobs

SK = FailureTime
```

Only failed jobs exist.

Applications retrieve:

```text
Newest Failures
```

instantly.

---

# Performance Benefits

Composite indexes provide:

- Fast lookups
- Ordered results
- Range filtering
- Efficient pagination
- Predictable latency

---

# Storage Considerations

Composite indexes duplicate projected attributes.

Adding multiple indexes increases:

- Storage
- Write cost
- Replication work

Design indexes carefully.

---

# Best Practices

- Design around business access patterns.
- Use high-cardinality Partition Keys.
- Choose Sort Keys that naturally support ordering.
- Combine multiple attributes into Sort Keys when appropriate.
- Keep projected attributes minimal.
- Test query patterns before production deployment.

---

# Common Mistakes

## Low-Cardinality Partition Keys

Example:

```text
Status = Active
```

Millions of records share one partition.

---

## Unsortable Sort Keys

Random UUIDs make ordering meaningless.

Choose Sort Keys that support real business queries.

---

## Ignoring Future Access Patterns

Composite indexes should anticipate realistic query requirements.

Avoid rebuilding indexes later if predictable access patterns already exist.

---

## Overloading the Sort Key

Including unrelated attributes in a Sort Key can make queries difficult to understand and maintain.

Keep Sort Keys purposeful and aligned with business requirements.

---

# SQL Composite Index vs DynamoDB Composite Index

| Feature | SQL Composite Index | DynamoDB Composite Index |
|----------|---------------------|--------------------------|
| Structure | Multiple indexed columns | Partition Key + Sort Key |
| Ordering | Depends on index definition | Automatic within partition |
| Range Queries | Supported | Supported |
| Prefix Queries | Limited by index order | Native with `begins_with` |
| Horizontal Scaling | Database dependent | Built into DynamoDB |

---

# Architecture Perspective

```text
                   Application

                        │

                        ▼

              Query Customer Orders

                        │

                        ▼

             Composite Secondary Index

           PK = CustomerID

           SK = OrderDate

                        │

        ┌───────────────┴───────────────┐

        ▼                               ▼

    Customer100                   Customer200

        │                               │

        ▼                               ▼

 Ordered by Date                Ordered by Date

                        │

                        ▼

                Application Response
```

The Partition Key determines **where** to search, while the Sort Key determines **how the results are organized** within that partition.

---

# Production Considerations

Composite indexes are the default choice for most enterprise DynamoDB applications because they support:

- User activity timelines
- Order history
- Financial transactions
- Messaging systems
- IoT telemetry
- Audit logs
- Monitoring dashboards
- Event sourcing architectures

Most production GSIs are designed as composite indexes because business queries almost always require both grouping and ordering.

---

# Interview Notes

A common interview question is:

> **What is a Composite Index in DynamoDB?**

A Composite Index is a secondary index that consists of a Partition Key and a Sort Key, enabling efficient grouping, sorting, and range queries.

Another common question is:

> **Why use a Composite Index instead of a simple Partition Key?**

A simple Partition Key supports exact lookups only. A Composite Index adds ordering and range query capabilities, making it suitable for real-world business queries.

Another common question is:

> **Give a production example of a Composite Index.**

An order management system might use:

```text
PK = CustomerID

SK = OrderDate
```

This allows retrieving a customer's orders in chronological order, fetching only recent orders, or querying orders within a specific date range without scanning the table.

---

# Key Takeaways

- Composite indexes combine a Partition Key with a Sort Key to support rich query patterns.
- They enable ordered retrieval, range queries, prefix matching, and efficient pagination.
- Most production GSIs and LSIs are implemented as composite indexes.
- Well-designed composite indexes align directly with business access patterns.
- Choosing appropriate Partition and Sort Keys is critical for scalability and performance.
- Composite indexes are a cornerstone of scalable DynamoDB data modeling.