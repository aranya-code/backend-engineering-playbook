# 01 - Query vs Scan

## Overview

One of the biggest differences between **Amazon DynamoDB** and traditional relational databases is **how data is retrieved**.

In SQL databases, developers often write arbitrary queries using the `WHERE` clause, and the database optimizer determines how to execute them.

In DynamoDB, data retrieval revolves around two operations:

- **Query**
- **Scan**

Although both retrieve data, they behave very differently in terms of:

- Performance
- Scalability
- Cost
- Capacity consumption
- Production suitability

Understanding when to use **Query** and when to avoid **Scan** is fundamental to building scalable DynamoDB applications.

---

# Why Does DynamoDB Have Two Read Operations?

DynamoDB is a distributed key-value database.

Instead of searching the entire database for matching records, it is designed to retrieve data directly from the correct partition whenever possible.

```text
Application

      │

      ▼

Partition Key

      │

      ▼

Correct Partition

      │

      ▼

Matching Items
```

This is exactly what a **Query** does.

A **Scan**, however, examines every item in the table.

---

# Query

A Query operation retrieves items by using:

- Partition Key
- Optional Sort Key conditions

Example:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = 1001
```

DynamoDB immediately knows which partition contains the data.

---

## Query Architecture

```text
             Query

               │

               ▼

      Partition Key

               │

               ▼

      Locate Partition

               │

               ▼

      Read Matching Items

               │

               ▼

          Return Results
```

Only one partition (or a very small number of partitions) is accessed.

---

# Scan

A Scan operation reads every item in a table or index.

Workflow:

```text
Application

      │

      ▼

Read Partition 1

↓

Read Partition 2

↓

Read Partition 3

↓

Read Partition N

↓

Filter Results

↓

Return Matches
```

Even if only one item matches, DynamoDB still reads the entire dataset.

---

# SQL Comparison

SQL:

```sql
SELECT *
FROM Orders
WHERE CustomerID = 1001;
```

The database optimizer chooses whether to use an index.

DynamoDB:

```text
Query

↓

Uses Primary Key

↓

Reads Matching Partition
```

If the required key is unavailable:

```text
Scan

↓

Entire Table
```

---

# Query Example

Orders Table

```text
PK = CustomerID

SK = OrderDate
```

Data:

```text
Customer001

    2026-07-01

    2026-07-05

    2026-07-10
```

Application:

```text
Find Orders

For Customer001
```

DynamoDB:

```text
Reads One Partition

↓

Returns Results
```

---

# Scan Example

Orders Table:

```text
100 Million Orders
```

Requirement:

```text
Find Orders

Above $1000
```

No appropriate index exists.

Application performs:

```text
Scan
```

Workflow:

```text
100 Million Items

↓

Read Every Item

↓

Filter

↓

Return Matches
```

---

# Performance Comparison

## Query

Reads:

```text
One Partition
```

Latency:

```text
Milliseconds
```

Scales efficiently.

---

## Scan

Reads:

```text
Entire Table
```

Latency increases as data grows.

Large tables become expensive.

---

# Capacity Consumption

Suppose:

```text
Table

100 Million Items
```

Query:

```text
CustomerID = 1001
```

Reads:

```text
50 Items
```

Capacity consumed:

Very small.

---

Scan:

```text
Entire Table
```

Reads:

```text
100 Million Items
```

Capacity consumed:

Extremely high.

---

# Filtering Difference

Many developers misunderstand Filter Expressions.

Example:

```text
Scan

↓

100 Million Items

↓

Filter Status = ACTIVE

↓

100 Results
```

Although only 100 items are returned,

DynamoDB still reads:

```text
100 Million Items
```

Filters do **not** reduce read capacity consumption.

---

# Query with Sort Key

Queries can efficiently retrieve ranges.

Example:

```text
PK = CustomerID

SK = OrderDate
```

Retrieve:

```text
Orders

Between

July 1

and

July 31
```

Only matching items are read.

---

# Pagination

Query naturally supports pagination.

```text
Query

↓

100 Items

↓

LastEvaluatedKey

↓

Next Page
```

Applications retrieve data incrementally.

---

# Scan Pagination

Scans also paginate,

but every page still reads additional portions of the table.

Large scans may require thousands of requests.

---

# Querying GSIs

Queries work against:

- Base Tables
- Global Secondary Indexes
- Local Secondary Indexes

Example:

```text
Email GSI

↓

Query Email

↓

Find User
```

Indexes exist primarily to enable efficient Query operations.

---

# Common Production Use Cases

## Query

- Customer orders
- User profiles
- Shopping carts
- Recent transactions
- Device telemetry
- Chat history
- Notifications

---

## Scan

- One-time migration
- Data export
- Analytics
- Administrative tools
- Batch cleanup jobs

Scans should rarely be used in customer-facing APIs.

---

# Query vs Scan Comparison

| Feature | Query | Scan |
|----------|-------|------|
| Reads Entire Table | ❌ | ✅ |
| Requires Partition Key | ✅ | ❌ |
| Supports Sort Key Conditions | ✅ | ❌ |
| Uses Indexes | ✅ | ✅ (can scan indexes too) |
| Performance | Excellent | Poor on large tables |
| Capacity Consumption | Low | High |
| Production APIs | Recommended | Avoid whenever possible |
| Scalability | Excellent | Limited |

---

# Real-World Example — E-commerce

Requirement:

```text
Show Orders

For Customer
```

Good design:

```text
PK = CustomerID
```

Application performs:

```text
Query
```

Latency remains low even with hundreds of millions of orders.

---

Requirement:

```text
Find All Orders

Over $1000
```

Without an index:

```text
Scan
```

This operation becomes expensive and slow.

A better design is:

```text
Amount GSI

↓

Query Amount
```

---

# Real-World Example — Banking

Transactions:

```text
PK = AccountID

SK = TransactionDate
```

Retrieve:

```text
Last 20 Transactions
```

Uses:

```text
Query
```

Never:

```text
Scan
```

---

# Architecture Perspective

```text
                   Application

                        │

          ┌─────────────┴─────────────┐

          ▼                           ▼

       Query                        Scan

          │                           │

          ▼                           ▼

   Locate Partition        Read Every Partition

          │                           │

          ▼                           ▼

   Read Matching Items      Read Entire Table

          │                           │

          ▼                           ▼

    Fast Response          High Latency & Cost
```

The fundamental difference is that **Query targets specific partitions**, while **Scan examines the entire dataset**.

---

# Best Practices

- Design tables to support Query operations.
- Create GSIs instead of relying on Scan.
- Use high-cardinality Partition Keys.
- Keep customer-facing APIs Query-based.
- Reserve Scan for administrative or offline workloads.
- Use pagination for large Query results.
- Monitor Scan activity using CloudWatch.

---

# Common Mistakes

## Using Scan in Production APIs

A Scan may work during development with a few hundred records but becomes a major bottleneck as data grows.

---

## Relying on Filter Expressions

Filter Expressions reduce the number of returned items, **not** the number of items read.

---

## Ignoring Access Patterns

If an application frequently performs Scan operations, the table design likely needs additional indexes or a different key structure.

---

## Forgetting Capacity Costs

Scans consume read capacity for every item examined, making them expensive on large tables.

---

# Production Considerations

Large-scale DynamoDB deployments are designed so that **nearly all application requests use Query operations**.

Scans are typically reserved for:

- Data migrations
- ETL pipelines
- Reporting jobs
- Administrative maintenance
- Background batch processing

Many organizations monitor CloudWatch metrics for unexpected Scan activity, as a sudden increase often indicates an inefficient query pattern or a missing index.

---

# Interview Notes

A common interview question is:

> **What is the difference between Query and Scan in DynamoDB?**

A Query retrieves items using a Partition Key (and optional Sort Key conditions), reading only the relevant partition. A Scan reads every item in a table or index, making it significantly slower and more expensive.

Another common question is:

> **Why should Scan be avoided in production applications?**

Because Scan examines the entire dataset, consuming large amounts of read capacity, increasing latency, and reducing scalability. Query operations are far more efficient.

Another common question is:

> **Do Filter Expressions make Scan operations cheaper?**

No. Filter Expressions are applied **after** DynamoDB reads the data, so they reduce the response size but do not reduce read capacity consumption.

---

# Key Takeaways

- Query is the preferred read operation for DynamoDB because it targets specific partitions using keys.
- Scan reads every item in a table or index and should be reserved for administrative or offline workloads.
- Filter Expressions do not reduce the number of items read during a Scan.
- Proper data modeling and secondary indexes eliminate the need for most Scan operations.
- Query operations provide lower latency, lower cost, and significantly better scalability for production applications.