# 04 - Key Condition Expressions

## Overview

A **Key Condition Expression** is the most important part of a DynamoDB **Query** operation.

It tells DynamoDB:

- Which partition to search
- Which items inside that partition should be returned

Unlike a **Filter Expression**, a Key Condition Expression is evaluated **before** DynamoDB reads the data.

Because of this, it directly affects:

- Query performance
- Read capacity consumption
- Scalability
- Response latency

Well-designed Key Condition Expressions enable DynamoDB to retrieve data in **single-digit milliseconds**, even when tables contain billions of items.

---

# What is a Key Condition Expression?

A Key Condition Expression specifies:

- A required Partition Key equality
- An optional Sort Key condition

Example table:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001

AND

OrderDate >= 2026-07-01
```

Only matching items are read.

---

# Why is it Important?

Unlike SQL databases, DynamoDB cannot search arbitrary attributes.

Every Query begins with:

```text
Partition Key
```

Without it:

```text
Query

↓

Cannot Execute
```

This requirement allows DynamoDB to immediately locate the correct partition.

---

# Internal Architecture

```text
                Query

                  │

                  ▼

      Key Condition Expression

                  │

                  ▼

       Locate Partition Key

                  │

                  ▼

     Evaluate Sort Key Condition

                  │

                  ▼

        Read Matching Items

                  │

                  ▼

          Return Results
```

Only matching items are read.

---

# Partition Key Requirement

Every Key Condition Expression must contain:

```text
PartitionKey = Value
```

Example:

```text
CustomerID = CUST1001
```

Valid.

---

Invalid:

```text
CustomerID > CUST1001
```

Partition Keys only support:

```text
=
```

---

# Sort Key is Optional

If the table has a Sort Key:

```text
PK = CustomerID

SK = OrderDate
```

You may query:

```text
CustomerID = CUST1001
```

or

```text
CustomerID = CUST1001

AND

OrderDate > 2026-07-01
```

---

# Supported Sort Key Operators

| Operator | Purpose |
|----------|----------|
| = | Exact match |
| < | Less than |
| <= | Less than or equal |
| > | Greater than |
| >= | Greater than or equal |
| BETWEEN | Range query |
| begins_with() | Prefix search |

---

# Equality Example

Table:

```text
PK = EmployeeID

SK = Month
```

Query:

```text
EmployeeID = EMP100

Month = July
```

Returns:

```text
Only July Record
```

---

# Greater Than Example

Query:

```text
CustomerID = CUST1001

AND

OrderDate > 2026-07-15
```

Returns:

```text
Recent Orders
```

---

# BETWEEN Example

Orders:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001

AND

OrderDate BETWEEN

2026-07-01

AND

2026-07-31
```

Returns:

```text
Orders During July
```

Efficiently reads only matching items.

---

# begins_with() Example

Sort Key:

```text
USA#California#LosAngeles

USA#California#SanDiego

USA#Texas#Dallas
```

Query:

```text
begins_with(

USA#California

)
```

Returns:

```text
California Records
```

Useful for hierarchical data.

---

# Composite Sort Keys

Composite Sort Keys unlock multiple query patterns.

Example:

```text
SK

Priority#Timestamp
```

Data:

```text
HIGH#2026-07-20

HIGH#2026-07-21

LOW#2026-07-22
```

Query:

```text
begins_with(

HIGH

)
```

Returns:

```text
High Priority Items
```

---

# Hierarchical Queries

Example:

```text
Company

↓

Department

↓

Team

↓

Employee
```

Sort Key:

```text
Engineering#Backend#Alice
```

Query:

```text
begins_with(

Engineering

)
```

Returns:

Entire Engineering department.

---

# Query Execution Flow

```text
Application

↓

Partition Key

↓

Locate Partition

↓

Apply Sort Key Condition

↓

Read Matching Items

↓

Return Results
```

Notice that DynamoDB does **not** scan unrelated items.

---

# Key Condition vs Filter Expression

Key Condition:

```text
Locate Data
```

Filter Expression:

```text
Remove Data

After Reading
```

Workflow:

```text
Key Condition

↓

Read Items

↓

Filter Expression

↓

Return Final Results
```

Only the Key Condition reduces the amount of data read.

---

# Capacity Consumption

Example:

```text
Customer

1000 Orders
```

Key Condition:

```text
Last Month
```

Reads:

```text
50 Orders
```

Capacity consumed:

Only for those 50 matching items.

Efficient.

---

# Real-World Example — Banking

Table:

```text
PK = AccountID

SK = TransactionDate
```

Requirement:

```text
Transactions

This Week
```

Key Condition:

```text
AccountID = ACC100

AND

TransactionDate BETWEEN

Monday

Sunday
```

No Scan required.

---

# Real-World Example — IoT

Table:

```text
PK = DeviceID

SK = Timestamp
```

Requirement:

```text
Sensor Data

Last Hour
```

Query:

```text
DeviceID = SENSOR01

AND

Timestamp > OneHourAgo
```

Reads only recent telemetry.

---

# Real-World Example — E-commerce

Orders:

```text
PK = CustomerID

SK = OrderDate
```

Requirement:

```text
Latest Orders
```

Query:

```text
CustomerID = CUST1001

↓

Descending

↓

Limit 10
```

Very efficient.

---

# Best Practices

- Always design tables around Key Condition Expressions.
- Use high-cardinality Partition Keys.
- Use meaningful Sort Keys.
- Prefer BETWEEN over filtering date ranges.
- Use begins_with() for hierarchical data.
- Minimize Filter Expressions.
- Model access patterns before designing keys.

---

# Common Mistakes

## Treating Partition Keys Like SQL Columns

Invalid:

```text
CustomerID >

100
```

Partition Keys only support equality.

---

## Filtering Instead of Designing Keys

Poor:

```text
Query

↓

10000 Items

↓

Filter
```

Better:

Design the Sort Key so only the required items are queried.

---

## Random Sort Keys

Random UUIDs prevent:

- Range queries
- Ordering
- Prefix searches

Business-oriented Sort Keys are far more useful.

---

## Ignoring Access Patterns

If queries frequently require filters after reading thousands of items, the data model likely needs redesign.

---

# Comparison

| Feature | Key Condition | Filter Expression |
|----------|---------------|-------------------|
| Evaluated Before Read | ✅ | ❌ |
| Reduces RCUs | ✅ | ❌ |
| Uses Keys | ✅ | ❌ |
| Improves Performance | ✅ | Limited |
| Required for Query | ✅ | ❌ |

---

# Architecture Perspective

```text
                   Application

                         │

                  Query Request

                         │

                         ▼

          Key Condition Expression

                         │

        ┌────────────────┴───────────────┐

        ▼                                ▼

 Locate Partition                 Sort Key Check

        │                                │

        └────────────────┬───────────────┘

                         ▼

                Read Matching Items

                         ▼

                Optional Filter

                         ▼

                 Return Results
```

Key Condition Expressions determine **what DynamoDB reads**, while Filter Expressions determine **what the application receives**.

---

# Production Considerations

In large-scale production systems, Key Condition Expressions are carefully designed during the data modeling phase.

Common production patterns include:

- Customer order history
- Financial transactions by date
- User activity timelines
- IoT telemetry by time window
- Chat messages by conversation
- Audit logs by resource

These workloads achieve predictable low latency because the required data can be identified directly through the Partition Key and Sort Key.

---

# Interview Notes

A common interview question is:

> **What is the purpose of a Key Condition Expression?**

It tells DynamoDB which Partition Key to search and optionally applies Sort Key conditions, allowing the database to retrieve only the required items efficiently.

Another common question is:

> **Can you query DynamoDB without specifying a Partition Key?**

No. Every Query operation requires an equality condition on the Partition Key. Without it, you must use a secondary index or perform a Scan.

Another common question is:

> **Why are Key Condition Expressions more efficient than Filter Expressions?**

Key Condition Expressions are evaluated before DynamoDB reads data, reducing the number of items read and lowering read capacity consumption. Filter Expressions are evaluated after the data has already been read.

---

# Key Takeaways

- Every Query operation requires a Key Condition Expression.
- The Partition Key must always use an equality (`=`) condition.
- Sort Keys support range operators such as `BETWEEN`, `>`, `<`, and `begins_with()`.
- Key Condition Expressions reduce latency and read capacity consumption by limiting the data DynamoDB reads.
- Well-designed Partition Keys and Sort Keys eliminate unnecessary filtering and enable highly scalable, production-grade query performance.