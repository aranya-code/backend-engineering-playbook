# 05 - Primary Keys

## Overview

A database is only useful if it can locate data efficiently.

Imagine a library containing millions of books. Without a cataloging system, finding a single book would require searching every shelf. Databases face the same challenge. Regardless of how much data is stored, they must be able to locate a specific record quickly.

In DynamoDB, the **Primary Key** is that cataloging system.

Unlike relational databases, where a primary key is mainly used to uniquely identify a row, DynamoDB's primary key is much more significant. It determines:

- Where data is physically stored
- How data is partitioned
- How data is retrieved
- How the database scales
- How efficiently queries execute

For this reason, choosing the correct primary key is the single most important decision when designing a DynamoDB table.

---

# Why Primary Keys Matter

Consider a table storing one billion customer records.

```text
Customers

Customer 1

Customer 2

Customer 3

...

Customer 1,000,000,000
```

Suppose an application needs customer **CUST-458721**.

Without a primary key, DynamoDB would have no option except to examine every item until it found the matching customer.

```text
Customer 1

↓

Customer 2

↓

Customer 3

↓

...

↓

Customer 458721
```

This approach is called a **full table scan**.

Even on modern hardware, scanning billions of records for every request would be impractical.

Instead, DynamoDB uses the primary key to calculate exactly where the item should exist.

The lookup becomes nearly instantaneous.

---

# A Primary Key is More Than an Identifier

Developers familiar with SQL often think of a primary key simply as a unique identifier.

For example,

```sql
CustomerID INT PRIMARY KEY
```

In PostgreSQL or MySQL, this primarily ensures uniqueness.

In DynamoDB, however, the primary key also determines the physical placement of data across partitions.

This means that the primary key directly influences:

- Performance
- Scalability
- Throughput
- Hot partition avoidance
- Query efficiency

A poorly designed primary key can create a bottleneck, even if the application logic is otherwise correct.

---

# Types of Primary Keys

DynamoDB supports two primary key models.

```text
Primary Key

├── Partition Key

└── Composite Primary Key

      ├── Partition Key

      └── Sort Key
```

Both uniquely identify items, but they serve different purposes.

The following chapters explore each model in detail.

---

# Simple Primary Key (Partition Key Only)

A simple primary key consists of a single attribute.

Example:

```text
Users Table

Partition Key

UserId
```

Example item:

```json
{
    "UserId":"U1001",
    "Name":"Alice",
    "Country":"USA"
}
```

Each value must be unique.

Attempting to insert another item with the same UserId replaces or overwrites the existing item, depending on the operation used.

Simple primary keys are ideal when every entity has a naturally unique identifier.

Examples include:

- Employee ID
- User ID
- Product ID
- Device ID

---

# Composite Primary Key

Many business problems require storing multiple related records under the same logical entity.

Consider an Orders table.

One customer may place hundreds of orders.

Instead of creating separate tables, DynamoDB allows multiple items to share the same partition while remaining uniquely identifiable.

This is achieved using a composite primary key.

```text
Partition Key

CustomerId

+

Sort Key

OrderId
```

Example:

```text
PK = CUSTOMER#1001

SK = ORDER#001

------------------------

PK = CUSTOMER#1001

SK = ORDER#002

------------------------

PK = CUSTOMER#1001

SK = ORDER#003
```

All orders belong to the same customer while remaining individually identifiable.

This design is fundamental to efficient querying and is one of DynamoDB's greatest strengths.

---

# How DynamoDB Uses the Primary Key

Internally, DynamoDB performs a hashing operation on the partition key.

```text
Partition Key

↓

Hash Function

↓

Partition Selection

↓

Storage Node
```

The application never sees this process.

Developers simply provide the primary key.

DynamoDB determines:

- Which partition stores the item
- Which replicas contain copies
- Which storage node processes the request

This automation is one of the reasons DynamoDB scales without manual sharding.

---

# Uniqueness Rules

For a simple primary key:

```text
UserId

↓

Must be unique
```

For a composite key:

```text
Partition Key

+

Sort Key

↓

Combined value must be unique
```

This means the following is valid.

```text
PK = CUSTOMER#1001

SK = ORDER#001

-------------------

PK = CUSTOMER#1001

SK = ORDER#002
```

The partition key is repeated, but the overall key remains unique because the sort key differs.

---

# Primary Keys and Query Performance

DynamoDB is optimized to retrieve data using the primary key.

A request such as:

```text
Get User

UserId = U1001
```

allows DynamoDB to calculate the item's location immediately.

This operation is extremely efficient because the database does not need to inspect unrelated items.

Queries that do not use the primary key are generally less efficient and may require indexes or scans.

---

# Designing Good Primary Keys

An effective primary key should satisfy several goals.

It should:

- Distribute requests evenly.
- Avoid concentrating traffic on one partition.
- Support application access patterns.
- Remain stable throughout the item's lifetime.
- Minimize unnecessary scans.

Choosing a primary key based solely on uniqueness is often insufficient.

The distribution of requests is equally important.

---

# Common Mistakes

## Using Sequential Values

```text
1

2

3

4

5
```

Sequential identifiers often create uneven write patterns.

Depending on the workload, this may increase the likelihood of hot partitions.

Randomized identifiers such as UUIDs generally distribute traffic more evenly.

---

## Designing Around the Database Instead of Queries

Many beginners ask:

> What should my tables look like?

A better question is:

> How will my application retrieve data?

The answer determines the primary key.

DynamoDB tables are designed around **access patterns**, not entity relationships.

---

## Choosing Frequently Updated Keys

Primary keys should be stable.

Changing a primary key requires deleting the existing item and inserting a new one because the primary key determines the physical storage location.

Unlike relational databases, a primary key cannot simply be updated in place.

---

# Interview Notes

A common interview question is:

> **Why is choosing the correct primary key considered the most important part of DynamoDB design?**

Because nearly every core capability of DynamoDB depends on it.

The primary key determines:

- Data distribution
- Scalability
- Query efficiency
- Partition utilization
- Cost
- Performance

A well-designed schema can handle millions of requests per second.

A poorly designed primary key can create bottlenecks long before the application reaches that scale.

---

# Key Takeaways

- Every DynamoDB table requires a primary key.
- The primary key determines both logical identity and physical data placement.
- DynamoDB supports simple and composite primary keys.
- Composite keys enable efficient one-to-many data modeling.
- The primary key is central to partitioning, querying, and scalability.
- Designing primary keys around application access patterns is one of the most important DynamoDB design principles.