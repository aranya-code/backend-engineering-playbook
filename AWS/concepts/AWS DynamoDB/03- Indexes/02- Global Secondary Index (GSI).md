# 02 - Global Secondary Index (GSI)

## Overview

A **Global Secondary Index (GSI)** is the most commonly used secondary index in Amazon DynamoDB.

It allows you to query the same data using a **completely different Primary Key** than the one defined on the base table.

Without a GSI, DynamoDB can efficiently retrieve items only by the table's Primary Key.

With a GSI, the same table can support multiple business access patterns without performing expensive table scans.

GSIs are one of the primary reasons DynamoDB can support highly scalable applications while maintaining single-digit millisecond latency.

---

# Why Do We Need GSIs?

Suppose we have a Users table.

Primary Key:

```text
PK = USER#100
```

The application can efficiently perform:

```text
Get User

By User ID
```

However, the business introduces new requirements:

- Find User by Email
- Find User by Username
- Find Users by Department
- Find Active Users
- Find Users by Country

None of these attributes are part of the Primary Key.

Without a GSI:

```text
Scan Entire Table

↓

Filter Results

↓

Return User
```

As the table grows, this becomes increasingly slow and expensive.

A GSI solves this problem.

---

# What is a Global Secondary Index?

A GSI is a separate index maintained automatically by DynamoDB.

It contains:

- A different Partition Key
- An optional different Sort Key
- A subset (or all) of the table's attributes

Conceptually:

```text
               Base Table

        PK          SK

        USER#1      PROFILE

        USER#2      PROFILE

        USER#3      PROFILE

                │

                ▼

        Global Secondary Index

        Email      UserID

alice@example.com USER#1

bob@example.com   USER#2

john@example.com  USER#3
```

The same data is now searchable in two different ways.

---

# Why Is It Called "Global"?

The term **Global** means:

The index is built across **all partitions** of the table.

Unlike Local Secondary Indexes, a GSI has its own partition key.

This allows:

```text
Base Table

Partition Key = UserID
```

Index:

```text
Partition Key = Email
```

The two structures are completely independent.

---

# GSI Architecture

```text
                 Application

                        │

                        ▼

                 Query Email

                        │

                        ▼

              Global Secondary Index

                        │

                        ▼

                 Base Table Item
```

Applications query the GSI directly.

DynamoDB handles synchronization automatically.

---

# Example Table

Users table:

| UserID | Name | Email | Department |
|---------|------|--------|------------|
| U100 | Alice | alice@example.com | HR |
| U200 | Bob | bob@example.com | IT |
| U300 | John | john@example.com | Sales |

Primary Key:

```text
PK = UserID
```

Business requirement:

```text
Find User

By Email
```

Create GSI:

```text
PK = Email
```

Now queries become:

```text
Email

↓

User
```

without scanning.

---

# Example with Sort Key

Suppose employees belong to departments.

Business requirement:

```text
Show Employees

By Department

Sorted By Joining Date
```

Base Table:

```text
PK = UserID
```

GSI:

```text
PK = Department

SK = JoiningDate
```

Now queries become:

```text
Department

↓

Employees

↓

Ordered by Joining Date
```

---

# Multiple GSIs

A single table may have multiple GSIs.

Example:

```text
Users Table

↓

GSI 1

Email
```

```text
GSI 2

Department
```

```text
GSI 3

Country
```

```text
GSI 4

Role
```

Each GSI supports a different access pattern.

---

# Visual Representation

```text
                     Users Table

                PK = UserID

                     │

     ┌───────────────┼─────────────────┐

     ▼               ▼                 ▼

 Email GSI     Department GSI     Country GSI

PK = Email     PK = Department    PK = Country
```

One table.

Multiple efficient query paths.

---

# GSI Synchronization

Suppose an item changes.

```text
User

↓

Email Updated
```

DynamoDB automatically updates:

```text
Base Table

↓

Email GSI
```

Applications do not update the GSI manually.

Synchronization is handled internally.

---

# Eventual Consistency

Unlike the base table,

GSIs are **eventually consistent**.

Workflow:

```text
Write

↓

Base Table Updated

↓

Short Delay

↓

GSI Updated
```

Most updates propagate within milliseconds.

However,

immediately querying the GSI after a write may temporarily return stale data.

---

# Querying a GSI

Instead of querying:

```text
Base Table
```

Applications specify:

```text
Index Name
```

Example workflow:

```text
Application

↓

Query

↓

EmailIndex

↓

Matching User
```

The query API is almost identical to querying the base table.

---

# Projection Types

GSIs do not always store every attribute.

Projection determines what data is copied into the index.

Options include:

```text
KEYS_ONLY
```

```text
INCLUDE
```

```text
ALL
```

Projection types will be covered in a dedicated chapter.

---

# Capacity Consumption

Every write affects:

```text
Base Table
```

and

```text
Every Matching GSI
```

Example:

```text
Insert User

↓

Table Updated

↓

Email Index Updated

↓

Department Index Updated

↓

Country Index Updated
```

Each index increases write cost.

---

# Storage Overhead

Indexes store copies of data.

More GSIs mean:

- More storage
- More write operations
- Higher AWS costs

Design indexes carefully.

---

# Real-World Example

A food delivery platform stores restaurants.

Primary Key:

```text
PK = RestaurantID
```

Customers search using:

- Cuisine
- City
- Rating

Instead of scanning:

```text
Restaurants
```

the platform creates:

```text
CuisineIndex

CityIndex

RatingIndex
```

Each customer query becomes an efficient index lookup.

---

# Benefits

GSIs provide:

- Multiple access patterns
- Efficient queries
- Horizontal scalability
- Flexible schema evolution
- Low-latency lookups

They eliminate many table scans.

---

# Limitations

GSIs also introduce:

- Additional storage
- Additional write cost
- Eventual consistency
- Capacity planning
- Index maintenance overhead

Indexes should solve real business requirements.

---

# Best Practices

- Create GSIs only for important access patterns.
- Use high-cardinality partition keys.
- Monitor GSI utilization in CloudWatch.
- Minimize projected attributes where possible.
- Design GSIs alongside the base table schema.
- Periodically review unused indexes.

---

# Common Mistakes

## Indexing Every Attribute

Not every searchable field deserves its own GSI.

Each additional index increases cost.

---

## Ignoring Eventual Consistency

Applications requiring immediate consistency should query the base table when appropriate.

---

## Poor Partition Key Selection

Avoid low-cardinality values like:

```text
Status = Active
```

Large numbers of identical partition keys can create hot partitions.

---

## Over-Projecting Attributes

Projecting every attribute into every GSI increases storage and write costs unnecessarily.

---

# SQL Index vs GSI

| Feature | SQL Index | DynamoDB GSI |
|----------|-----------|--------------|
| Purpose | Speed up queries | Enable new access patterns |
| Primary Key | Same table key | Different partition/sort keys |
| Storage | Separate index | Separate index with projected data |
| Consistency | Immediate | Eventual |
| Schema Change | Easy | Requires index creation |
| Horizontal Scaling | Database-dependent | Built into DynamoDB |

---

# Architecture Perspective

```text
                    Application

                          │

                          ▼

                  Query Email Address

                          │

                          ▼

                 Global Secondary Index

                          │

                          ▼

                  Matching Primary Key

                          │

                          ▼

                    Return Item
```

The GSI acts as an alternate lookup path while the base table remains the authoritative source of data.

---

# Production Considerations

Large enterprise applications commonly maintain multiple GSIs to support:

- Customer search
- Product discovery
- Order tracking
- Reporting dashboards
- Administrative tools
- Analytics
- Audit systems

Each GSI is treated as a production resource with its own:

- Capacity planning
- Cost monitoring
- Performance analysis
- CloudWatch metrics
- Operational reviews

Indexes should be added only when their business value outweighs their operational cost.

---

# Interview Notes

A common interview question is:

> **What is a Global Secondary Index?**

A Global Secondary Index is a secondary index that allows a DynamoDB table to be queried using a different partition key and optional sort key than the base table, enabling additional access patterns without scanning the table.

Another common question is:

> **Why is it called "Global"?**

Because the index spans all partitions of the table and has its own independent partition key, unlike an LSI, which shares the base table's partition key.

Another common question is:

> **What are the trade-offs of using a GSI?**

GSIs improve read flexibility but increase storage usage, write costs, and introduce eventual consistency. They should be created only for valuable business access patterns.

---

# Key Takeaways

- A Global Secondary Index (GSI) enables alternate query paths using different key attributes.
- GSIs are the primary mechanism for supporting multiple access patterns in DynamoDB.
- Each GSI has its own partition key and optional sort key.
- GSIs are eventually consistent and maintained automatically by DynamoDB.
- Every GSI increases write cost and storage consumption.
- Careful GSI design is essential for building scalable, cost-efficient DynamoDB applications.