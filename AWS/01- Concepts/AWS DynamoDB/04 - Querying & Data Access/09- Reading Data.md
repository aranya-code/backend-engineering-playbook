# 09 - Reading Data

## Overview

Reading data is one of the most fundamental operations in DynamoDB. Unlike relational databases, DynamoDB provides multiple read APIs optimized for different access patterns rather than a single `SELECT` statement.

Each read operation has a specific purpose:

- Reading a single item
- Reading multiple known items
- Reading items sharing the same Partition Key
- Reading an entire table
- Reading multiple items transactionally

Choosing the correct read API is critical for building scalable, low-latency applications while minimizing read capacity consumption.

This chapter provides a high-level overview of all DynamoDB read operations and explains when each should be used.

---

# The DynamoDB Read APIs

DynamoDB provides five primary read operations.

| API | Purpose |
|------|----------|
| GetItem | Retrieve one item by its primary key |
| BatchGetItem | Retrieve multiple known items |
| Query | Retrieve multiple related items using a Partition Key |
| Scan | Read every item in a table or index |
| TransactGetItems | Retrieve multiple items with ACID consistency |

Each operation is optimized for a different workload.

---

# Choosing the Correct Read Operation

```text
                Need Data

                    │

        ┌───────────┼────────────┐

        ▼                        ▼

 Know Primary Key?         Need Entire Table?

        │                        │

       Yes                      Yes

        │                        │

        ▼                        ▼

  One Item?                 Use Scan

        │

 ┌──────┴──────┐

 ▼             ▼

Yes           No

 │             │

 ▼             ▼

GetItem   Multiple Keys?

               │

        ┌──────┴──────┐

        ▼             ▼

      Yes            No

       │              │

       ▼              ▼

BatchGetItem     Query
```

This simple decision tree covers most production use cases.

---

# GetItem

`GetItem` retrieves exactly one item using its complete primary key.

Example:

```text
PK = Customer123
```

or

```text
PK = Customer123

SK = Order789
```

Characteristics:

- Fastest read operation
- Lowest latency
- Reads exactly one item
- No searching
- No filtering

Ideal for:

- User profiles
- Product lookup
- Configuration data
- Session storage

---

# BatchGetItem

`BatchGetItem` retrieves multiple known items in a single request.

Example:

```text
Customer123

Customer456

Customer789
```

Instead of three GetItem requests:

```text
GetItem

↓

GetItem

↓

GetItem
```

Use:

```text
BatchGetItem

↓

Retrieve All Items
```

Ideal for:

- Shopping carts
- Dashboards
- Recommendation systems
- Bulk lookups

---

# Query

`Query` retrieves multiple related items sharing the same Partition Key.

Example:

```text
Customer123

↓

Order001

Order002

Order003

Order004
```

The Query operation efficiently retrieves an item collection.

Characteristics:

- Requires Partition Key
- Can filter using Sort Key
- Extremely efficient
- Reads only one partition

Ideal for:

- Order history
- Chat messages
- Time-series data
- IoT sensor readings

---

# Scan

`Scan` reads every item in a table.

```text
Table

↓

Item1

Item2

Item3

...

ItemN
```

Unlike Query:

- No Partition Key required
- Reads all partitions
- Highest RCU consumption
- Slowest read operation

Typical use cases:

- Analytics
- Data migration
- Administrative tools
- Background processing

Avoid Scan in latency-sensitive APIs.

---

# TransactGetItems

`TransactGetItems` retrieves multiple items as a single ACID transaction.

Example:

```text
Account A

Account B

Transaction Record
```

All items are read from the same consistent snapshot.

Ideal for:

- Banking
- Financial systems
- Inventory management
- Reservation systems

---

# Read Consistency

DynamoDB supports two consistency models.

## Eventually Consistent Read

```text
Write

↓

Read

↓

May Return Older Data
```

Characteristics:

- Lower latency
- Lower cost
- Default behavior

Used by most applications.

---

## Strongly Consistent Read

```text
Write

↓

Read

↓

Latest Data Guaranteed
```

Characteristics:

- Latest committed data
- Higher latency
- Higher RCU consumption
- Supported only on base tables and LSIs

---

# Capacity Consumption

Every read operation consumes Read Capacity Units (RCUs).

| Operation | Capacity Consumption |
|------------|----------------------|
| GetItem | Per item read |
| BatchGetItem | Sum of individual reads |
| Query | Items evaluated |
| Scan | Entire table scanned |
| TransactGetItems | Sum of transactional reads |

The most efficient operation is usually the one that reads the least amount of data.

---

# Read Operation Comparison

| Feature | GetItem | BatchGetItem | Query | Scan | TransactGetItems |
|----------|----------|--------------|-------|------|------------------|
| One Item | ✅ | ❌ | ❌ | ❌ | ❌ |
| Multiple Items | ❌ | ✅ | ✅ | ✅ | ✅ |
| Requires Primary Key | ✅ | ✅ | Partition Key | ❌ | ✅ |
| Reads Whole Table | ❌ | ❌ | ❌ | ✅ | ❌ |
| Transactional | ❌ | ❌ | ❌ | ❌ | ✅ |
| Fastest | ✅ | ✅ | ✅ | ❌ | Slightly Slower |

---

# Internal Read Architecture

```text
                 Application

                       │

                 Read Request

                       │

       ┌───────────────┼────────────────┐

       ▼               ▼                ▼

   GetItem         Query          BatchGetItem

       │               │                │

       └───────────────┼────────────────┘

                       ▼

              DynamoDB Storage

                       ▼

                 Return Results
```

Every read operation ultimately retrieves data from DynamoDB storage, but each follows a different execution path optimized for its access pattern.

---

# SQL Comparison

SQL databases typically use a single statement:

```sql
SELECT * FROM Orders
WHERE CustomerID = 101;
```

In DynamoDB, different APIs are used depending on the access pattern.

| SQL | DynamoDB |
|------|-----------|
| SELECT by Primary Key | GetItem |
| SELECT multiple known rows | BatchGetItem |
| SELECT with indexed key | Query |
| SELECT entire table | Scan |
| Transactional SELECT | TransactGetItems |

Instead of writing complex SQL queries, DynamoDB applications choose the appropriate API based on how the data is modeled.

---

# Production Example — E-commerce

Customer dashboard needs:

```text
Customer Profile

Recent Orders

Wishlist

Reward Points
```

Recommended reads:

```text
Profile

↓

GetItem

Orders

↓

Query

Wishlist

↓

Query

Rewards

↓

GetItem
```

Avoid using Scan.

---

# Production Example — Banking

Mobile banking application:

```text
Customer

↓

Accounts

↓

Recent Transactions

↓

Loans
```

Possible implementation:

- GetItem for customer profile
- Query for transactions
- TransactGetItems for financial consistency when required

---

# Production Example — IoT

Sensor readings:

```text
Sensor001

↓

2026-01

↓

Thousands of Events
```

Use:

```text
Query

PK = Sensor001

SK BETWEEN

StartTime

EndTime
```

This is significantly more efficient than scanning the entire table.

---

# Best Practices

- Prefer `GetItem` whenever possible.
- Use `Query` instead of `Scan`.
- Design tables around access patterns.
- Read only required attributes using Projection Expressions.
- Use BatchGetItem to reduce network round trips.
- Reserve transactions for business-critical consistency.
- Monitor RCU consumption using CloudWatch.

---

# Common Mistakes

## Using Scan for User APIs

Poor:

```text
Scan

↓

Find Customer
```

Better:

```text
GetItem
```

or

```text
Query
```

---

## Choosing Query When Keys Are Known

If the complete primary keys are already available, `BatchGetItem` is generally more efficient than performing multiple queries.

---

## Using Transactions Unnecessarily

Many applications do not require transactional reads.

Using `TransactGetItems` everywhere increases latency and resource consumption.

---

## Ignoring Read Capacity

Reading more data than necessary increases:

- RCUs
- Latency
- Network bandwidth
- Application costs

Use Projection Expressions and well-designed access patterns to minimize unnecessary reads.

---

# Architecture Perspective

```text
                 Client Request

                       │

                Determine Access Pattern

                       │

      ┌────────┼───────────┼───────────┐

      ▼        ▼           ▼           ▼

  GetItem   Query   BatchGetItem   Scan

      └────────┼───────────┼───────────┘

               ▼

        DynamoDB Storage Engine

               ▼

          Return Requested Data
```

The efficiency of a read operation depends largely on choosing the API that matches the application's access pattern.

---

# Interview Notes

A common interview question is:

> **Which read operation should be used most often?**

`GetItem` and `Query` are the most common production read operations because they retrieve only the data required for a specific access pattern.

Another common question is:

> **Why is Scan considered expensive?**

Because it reads every item in a table regardless of how many items are actually needed, consuming significantly more RCUs than targeted read operations.

Another common question is:

> **When should BatchGetItem be used instead of Query?**

Use `BatchGetItem` when the complete primary keys of multiple items are already known. Use `Query` when retrieving a collection of items that share the same Partition Key.

Another common question is:

> **When should TransactGetItems be used?**

Only when multiple related items must be read from a single, consistent transactional snapshot.

---

# Key Takeaways

- DynamoDB provides multiple read APIs, each optimized for a different access pattern.
- `GetItem` is the fastest option for retrieving a single known item.
- `Query` is the preferred operation for retrieving related items sharing a Partition Key.
- `BatchGetItem` efficiently retrieves multiple known items in one request.
- `Scan` should be reserved for administrative, analytical, or migration workloads.
- `TransactGetItems` provides ACID-compliant transactional reads for business-critical scenarios.
- Choosing the correct read API is one of the most important factors in building scalable, cost-efficient DynamoDB applications.