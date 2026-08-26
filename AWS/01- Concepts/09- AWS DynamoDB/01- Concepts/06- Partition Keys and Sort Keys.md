# 06 - Partition Keys and Sort Keys

## Overview

In the previous chapter, we learned that every DynamoDB table requires a **Primary Key**. However, not all primary keys are created equal.

A well-designed primary key determines far more than how an item is uniquely identified. It influences data distribution, query flexibility, scalability, storage efficiency, and application performance.

DynamoDB supports two types of key attributes:

- **Partition Key**
- **Sort Key**

These keys work together to organize data efficiently across a distributed storage system.

Understanding their purpose is one of the most important concepts in DynamoDB because almost every advanced design pattern—including Single Table Design, Global Secondary Indexes (GSIs), and access pattern modeling—depends on them.

---

# The Partition Key

The **Partition Key** is the most important attribute in a DynamoDB table.

Every item must contain a partition key value.

When an item is written, DynamoDB hashes the partition key and uses the result to determine where the item should be stored.

```text
Partition Key

↓

Hash Function

↓

Physical Partition

↓

Storage Node
```

Developers never choose the storage location directly.

Instead, AWS automatically distributes items across partitions using the partition key.

This automatic distribution is one of the reasons DynamoDB scales transparently without requiring manual sharding.

---

# Why Does DynamoDB Hash the Partition Key?

Imagine storing one billion customer records.

Without partitioning, every request would target the same storage server.

```text
Application

↓

Database Server

↓

1 Billion Records
```

As traffic increases, that server quickly becomes overloaded.

Instead, DynamoDB distributes data.

```text
Application

↓

Hash(UserId)

↓

Partition A

Partition B

Partition C

Partition D
```

Each partition stores only a subset of the overall dataset.

Because requests are spread across multiple partitions, DynamoDB can process a much larger number of concurrent reads and writes.

---

# Characteristics of a Good Partition Key

A good partition key should satisfy three goals.

## 1. High Cardinality

Cardinality refers to the number of unique values.

Example:

Good

```text
UserId

ProductId

OrderId

InvoiceId
```

Poor

```text
Country

Status

Department
```

A high-cardinality key distributes data more evenly across partitions.

Low-cardinality keys concentrate data into fewer partitions, increasing the risk of hotspots.

---

## 2. Even Traffic Distribution

A partition key should distribute requests evenly.

Suppose an application receives:

```text
User A

100 Requests

User B

120 Requests

User C

110 Requests

User D

95 Requests
```

Traffic is well balanced.

Now consider:

```text
USA

2 Million Requests

Canada

20,000 Requests

India

15,000 Requests
```

The "USA" partition receives almost all requests.

This creates a **hot partition**, reducing overall performance.

---

## 3. Stable Values

Partition keys should rarely change.

For example:

Good

```text
UserId
```

Poor

```text
CurrentStatus

CurrentDepartment
```

Changing the partition key requires moving the item to an entirely different partition.

Unlike SQL databases, DynamoDB cannot simply update the key in place.

---

# The Sort Key

The **Sort Key** is optional.

It is available only when using a **Composite Primary Key**.

The sort key allows multiple related items to share the same partition while remaining uniquely identifiable.

Example:

```text
Partition Key

CustomerId

Sort Key

OrderId
```

Result:

```text
PK = CUSTOMER#1001

SK = ORDER#001

---------------------

PK = CUSTOMER#1001

SK = ORDER#002

---------------------

PK = CUSTOMER#1001

SK = ORDER#003
```

All three items belong to the same customer.

The sort key distinguishes one order from another.

---

# Why the Sort Key Exists

Without a sort key:

```text
CustomerId

↓

One Item
```

Only one item could exist for each customer.

With a sort key:

```text
CustomerId

↓

Many Related Items
```

This enables one-to-many relationships while preserving efficient lookups.

Examples include:

- Customer → Orders
- User → Sessions
- Product → Reviews
- Employee → Payroll Records

---

# Lexicographical Ordering

Items sharing the same partition key are automatically stored in **sorted order** based on the sort key.

Example:

```text
PK = USER#1001

SK = 001

SK = 002

SK = 003

SK = 004
```

This ordering allows DynamoDB to perform efficient range queries.

Applications can request:

- First item
- Last item
- Items between two values
- Items beginning with a prefix

without scanning unrelated data.

---

# Designing Useful Sort Keys

The sort key should reflect how data is accessed.

Common examples include:

## Timestamp

```text
2026-01-01

2026-01-02

2026-01-03
```

Useful for:

- Logs
- Transactions
- Events
- Sensor data

---

## Version Number

```text
V1

V2

V3
```

Useful for document history.

---

## Order Number

```text
ORDER#100

ORDER#101

ORDER#102
```

Useful for customer purchases.

---

## Composite Values

Sort keys often combine multiple pieces of information.

Example:

```text
ORDER#2026-07-22#1001
```

or

```text
USER#PROFILE

USER#ADDRESS

USER#SETTINGS
```

These patterns become powerful when implementing Single Table Design.

---

# Partition Key vs Sort Key

| Partition Key | Sort Key |
|---------------|----------|
| Determines physical data distribution | Determines logical ordering within a partition |
| Required | Optional |
| Used for hashing | Used for sorting |
| Controls scalability | Controls query flexibility |
| Should have high cardinality | Should reflect access patterns |

Although both are part of the primary key, they serve completely different purposes.

---

# Querying with a Composite Key

Suppose the following items exist.

```text
PK = CUSTOMER#1001

SK = ORDER#001

SK = ORDER#002

SK = ORDER#003

SK = ORDER#004
```

A query can retrieve:

All orders

```text
PK = CUSTOMER#1001
```

Specific order

```text
PK = CUSTOMER#1001

SK = ORDER#003
```

Orders after a certain date

```text
PK = CUSTOMER#1001

SK > ORDER#002
```

Notice that DynamoDB searches only one partition.

This is significantly more efficient than scanning the entire table.

---

# Common Design Patterns

Several widely used DynamoDB patterns rely on partition and sort keys.

Examples include:

Customer → Orders

```text
PK = CUSTOMER#1001

SK = ORDER#001
```

Blog → Comments

```text
PK = BLOG#500

SK = COMMENT#001
```

Product → Reviews

```text
PK = PRODUCT#10

SK = REVIEW#500
```

User → Sessions

```text
PK = USER#20

SK = SESSION#100
```

Each pattern groups related information together while preserving efficient queries.

---

# Common Mistakes

## Choosing a Low-Cardinality Partition Key

Examples:

```text
Gender

Country

Department

Status
```

These values generate uneven traffic distribution.

---

## Using Frequently Changing Keys

Keys should remain stable.

Changing them requires deleting and recreating items.

---

## Ignoring Access Patterns

Many beginners design keys around entities.

Experienced DynamoDB engineers design keys around **queries**.

---

## Overloading the Sort Key

Although composite sort keys are powerful, making them excessively complex can reduce readability and increase maintenance effort.

Design sort keys that clearly reflect business requirements.

---

# Interview Notes

A common interview question is:

> **Why doesn't DynamoDB simply use one unique ID for every item?**

Because uniqueness alone does not solve the challenges of distributed systems.

The partition key determines how data is distributed across physical storage, while the sort key enables efficient organization and querying of related data within a partition.

Together, they allow DynamoDB to achieve both horizontal scalability and predictable query performance.

---

# Key Takeaways

- The partition key determines where data is physically stored.
- DynamoDB hashes the partition key to distribute data across partitions.
- High-cardinality partition keys improve scalability and reduce hotspots.
- The sort key organizes related items within a partition.
- Composite primary keys enable efficient one-to-many data modeling.
- Effective key design should always be driven by application access patterns rather than database structure.