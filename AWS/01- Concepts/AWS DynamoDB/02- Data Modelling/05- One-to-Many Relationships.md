# 05 - One-to-Many Relationships

## Overview

One-to-many relationships are among the most common data modeling patterns in any application.

Examples include:

- A customer places many orders.
- A blog post has many comments.
- A department has many employees.
- A user owns many devices.
- A playlist contains many songs.

In relational databases, these relationships are modeled using **foreign keys**.

In DynamoDB, one-to-many relationships are modeled by storing all related items under the **same partition key** and distinguishing them with different **sort keys**.

This allows all related records to be retrieved using a single, efficient `Query` operation.

---

# Understanding One-to-Many

A one-to-many relationship means:

```text
One Parent

↓

Many Children
```

Examples:

```text
Customer

↓

Order 1

Order 2

Order 3

Order 4
```

Another example:

```text
Blog Post

↓

Comment 1

Comment 2

Comment 3
```

---

# SQL Approach

A relational database typically uses two tables.

```text
Customers

CustomerID
Name
Email
```

```text
Orders

OrderID
CustomerID
Amount
Status
```

Relationship:

```sql
Customers.CustomerID

↓

Orders.CustomerID
```

Query:

```sql
SELECT *

FROM Customers

JOIN Orders

ON Customers.CustomerID = Orders.CustomerID
```

This works well in relational databases.

---

# DynamoDB Approach

Instead of joins:

Store related data inside the same partition.

Example:

```text
PK = CUSTOMER#100

SK = PROFILE
```

```text
PK = CUSTOMER#100

SK = ORDER#1001
```

```text
PK = CUSTOMER#100

SK = ORDER#1002
```

```text
PK = CUSTOMER#100

SK = ORDER#1003
```

Everything belongs to the same customer.

---

# Visual Representation

```text
Partition

CUSTOMER#100

│

├── PROFILE

├── ORDER#1001

├── ORDER#1002

├── ORDER#1003

└── ORDER#1004
```

One partition contains the complete customer history.

---

# Query Example

Retrieve all customer orders.

```text
Query

PK = CUSTOMER#100
```

Result:

```text
PROFILE

ORDER#1001

ORDER#1002

ORDER#1003

ORDER#1004
```

Need only orders?

Use a sort key condition.

```text
PK = CUSTOMER#100

SK Begins With

ORDER#
```

---

# Why Use Sort Keys?

The sort key organizes related items.

Example:

```text
ORDER#1001

ORDER#1002

ORDER#1003

ORDER#1004
```

Items are stored in sort key order.

This enables:

- Range queries
- Prefix queries
- Pagination
- Time-based queries

---

# Time-Based Relationships

Suppose orders include timestamps.

```text
PK = CUSTOMER#100

SK = ORDER#2026-07-01
```

```text
PK = CUSTOMER#100

SK = ORDER#2026-07-03
```

```text
PK = CUSTOMER#100

SK = ORDER#2026-07-10
```

Now retrieving recent orders becomes straightforward.

```text
Query

PK = CUSTOMER#100

Reverse Order

Limit 10
```

No additional sorting is required.

---

# Example – Blog System

Partition:

```text
POST#500
```

Contains:

```text
POST

COMMENT#001

COMMENT#002

COMMENT#003

COMMENT#004
```

Application:

```http
GET /posts/500
```

Returns:

- Post
- Comments

using one Query.

---

# Example – IoT Devices

Each device generates sensor readings.

```text
PK = DEVICE#100

SK = READING#2026-07-20T10:00

SK = READING#2026-07-20T10:01

SK = READING#2026-07-20T10:02
```

Query:

```text
PK = DEVICE#100

Last 100 Readings
```

Efficient and scalable.

---

# Pagination

Large collections should be paginated.

Example:

Customer:

```text
50,000 Orders
```

Do not retrieve everything.

Instead:

```text
Query

↓

100 Items

↓

LastEvaluatedKey

↓

Next Page
```

Pagination improves:

- Performance
- Memory usage
- Network efficiency

---

# Large Collections

One-to-many relationships may become very large.

Example:

```text
Customer

↓

5 Orders
```

Easy.

But consider:

```text
Twitter User

↓

20 Million Tweets
```

Storing everything under one partition key creates a hotspot.

Alternative strategies include:

- Time-based partitioning
- Write sharding
- Composite partition keys

These patterns will be covered later in this section.

---

# Ordering Matters

Since sort keys are ordered lexicographically:

```text
ORDER#001

ORDER#002

ORDER#003
```

Sorting occurs automatically.

Poor naming:

```text
ORDER1

ORDER10

ORDER2
```

Results in:

```text
ORDER1

ORDER10

ORDER2
```

Use zero-padding or timestamps.

---

# Cost Benefits

Traditional approach:

```text
Customer Query

↓

Orders Query

↓

Merge
```

Multiple requests.

Single Table Design:

```text
Query CUSTOMER#100
```

One request.

Lower latency.

Lower RCU consumption.

---

# Choosing the Parent

Always ask:

> Which entity naturally owns the children?

Examples:

```text
Customer

↓

Orders
```

```text
Blog

↓

Comments
```

```text
Playlist

↓

Songs
```

The parent typically becomes the partition key.

---

# When This Pattern Doesn't Work

One-to-many is ideal when:

- Children belong to one parent.
- Access starts with the parent.

It becomes less effective when:

- Children belong to multiple parents.
- Relationships are bidirectional.
- Data must be queried from multiple directions.

Those scenarios require:

- Global Secondary Indexes
- Many-to-Many patterns
- Adjacency Lists

---

# Best Practices

- Store related children under the same partition key.
- Use meaningful sort key prefixes.
- Design sort keys for natural ordering.
- Paginate large collections.
- Monitor for hot partitions.
- Keep access patterns predictable.

---

# Common Mistakes

## Using Scan to Find Children

Avoid:

```text
Scan Orders

↓

Filter Customer
```

Always use:

```text
Query

PK = CUSTOMER#100
```

---

## Ignoring Collection Growth

A parent with millions of children may require additional partitioning strategies.

---

## Poor Sort Key Design

Avoid random sort keys when ordering matters.

Use timestamps, sequence numbers, or meaningful prefixes.

---

## Treating Every Child as a Separate Partition

Children should typically remain with their parent unless scaling requirements dictate otherwise.

---

# Real-World Example

An online learning platform stores student enrollments.

Partition:

```text
STUDENT#500
```

Contains:

```text
PROFILE

COURSE#Python

COURSE#AWS

COURSE#Docker

COURSE#Redis
```

Retrieving all enrolled courses requires a single Query operation, making the application fast and predictable.

---

# Architecture Perspective

```text
Application

        │

        ▼

Query

PK = CUSTOMER#100

        │

        ▼

Partition

CUSTOMER#100

        │

        ├── PROFILE

        ├── ORDER#1001

        ├── ORDER#1002

        ├── ORDER#1003

        └── ORDER#1004

        │

        ▼

Application Response
```

One partition represents one aggregate of related data.

---

# Interview Notes

A common interview question is:

> **How do you model a one-to-many relationship in DynamoDB?**

The parent entity becomes the partition key, while each child is stored as a separate item with a unique sort key. This allows all related children to be retrieved efficiently using a single `Query`.

Another common question is:

> **What happens if a parent has millions of child records?**

A very large item collection can create hot partitions and performance bottlenecks. In such cases, techniques such as time-based partitioning, write sharding, or composite partition keys should be considered to distribute load while preserving efficient access.

---

# Key Takeaways

- One-to-many relationships are naturally modeled using a shared partition key.
- Each child entity is represented by a separate item with a distinct sort key.
- Sort keys enable ordered retrieval, prefix searches, and pagination.
- This pattern eliminates joins and minimizes database requests.
- Monitor large collections for partition hotspots and apply advanced partitioning strategies when necessary.
- Designing around the parent entity enables efficient, scalable access patterns in DynamoDB.