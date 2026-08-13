# 01 - Introduction to Indexes

## Overview

One of the biggest misconceptions developers have when learning DynamoDB is assuming that indexes work the same way as indexes in relational databases.

In SQL databases, indexes are primarily used to speed up queries on existing tables.

In DynamoDB, indexes serve a much broader purpose.

They allow a single table to support **multiple access patterns** without duplicating the entire dataset or performing expensive scans.

Understanding indexes is essential because **a poorly designed table often requires additional indexes to support new business requirements**, while a well-designed table with appropriate indexes can scale to millions of requests per second.

---

# What is an Index?

An index is an additional data structure maintained by DynamoDB that organizes data using **different key attributes** than the base table.

Instead of querying only by the table's Primary Key, an index allows querying the same data using another key.

Think of it as an alternate view of your data.

```text
               DynamoDB Table

            PK         SK

            USER#1     PROFILE
            USER#2     PROFILE
            USER#3     PROFILE

                    │
                    │
            Alternate View
                    │
                    ▼

              Secondary Index

          Email        UserID

alice@example.com      USER#1

bob@example.com        USER#2

john@example.com       USER#3
```

The underlying data remains the same.

Only the organization changes.

---

# Why Do We Need Indexes?

Suppose your Users table is designed like this:

```text
PK = USER#100
```

Business requirement:

```text
Get User

By User ID
```

Works perfectly.

Later, Product Management asks for:

```text
Find User

By Email Address
```

Unfortunately,

```text
Email
```

is not part of the Primary Key.

Without an index, your only option is:

```text
Scan Entire Table
```

Which means:

```text
Millions of Users

↓

Read Every Item

↓

Find One Email
```

This is extremely inefficient.

Instead, create an index.

---

# SQL vs DynamoDB Indexes

## SQL

Indexes improve query speed.

```text
Customers

↓

Index

↓

Email
```

Database still uses:

- Tables
- Joins
- Foreign Keys

Indexes mainly optimize searching.

---

## DynamoDB

Indexes are part of the data model.

They allow:

- New access patterns
- Alternate query paths
- Efficient lookups
- Horizontal scalability

Indexes are often designed before the application is built.

---

# Primary Index vs Secondary Index

Every DynamoDB table automatically has one Primary Index.

```text
Primary Key

↓

Partition Key

+

Sort Key
```

Additional indexes are called:

```text
Secondary Indexes
```

There are two types:

```text
Global Secondary Index (GSI)

Local Secondary Index (LSI)
```

We'll explore both in detail in upcoming chapters.

---

# How an Index Works

Suppose the table contains:

```text
PK = USER#100

Name = Alice

Email = alice@example.com
```

Primary access:

```text
Query

↓

USER#100
```

New requirement:

```text
Find

alice@example.com
```

Create an index:

```text
PK = Email

SK = UserID
```

Now DynamoDB maintains:

```text
alice@example.com

↓

USER#100
```

Applications query the index instead of scanning the table.

---

# Visual Representation

```text
                Base Table

+-------------------------------+
| PK          | Email           |
+-------------------------------+
| USER#100    | alice@...       |
| USER#200    | bob@...         |
| USER#300    | john@...        |
+-------------------------------+

                │

                ▼

          Email Index

+-------------------------------+
| Email          | PK           |
+-------------------------------+
| alice@...      | USER#100     |
| bob@...        | USER#200     |
| john@...       | USER#300     |
+-------------------------------+
```

The same data now supports two efficient query paths.

---

# Multiple Access Patterns

Imagine an e-commerce application.

Business requirements:

```text
Find Customer

By Customer ID
```

```text
Find Customer

By Email
```

```text
Find Orders

By Customer
```

```text
Find Orders

By Status
```

```text
Find Orders

By Date
```

A single Primary Key cannot efficiently support all these queries.

Indexes provide alternate access paths for each business requirement.

---

# Types of Secondary Indexes

DynamoDB provides two types of secondary indexes.

## Global Secondary Index (GSI)

Characteristics:

- Different Partition Key
- Different Sort Key
- Can be created after table creation
- Supports completely different query patterns

Example:

```text
Table

PK = UserID
```

GSI:

```text
PK = Email
```

---

## Local Secondary Index (LSI)

Characteristics:

- Same Partition Key as the base table
- Different Sort Key
- Must be created when the table is created
- Supports alternate sorting within a partition

Example:

```text
Table

PK = CustomerID

SK = OrderID
```

LSI:

```text
PK = CustomerID

SK = OrderDate
```

---

# Why Not Create an Index for Everything?

Indexes are powerful, but they are not free.

Every index requires:

- Additional storage
- Additional write operations
- Capacity consumption
- Maintenance by DynamoDB

Every write to the base table may also update one or more indexes.

More indexes mean:

```text
Higher Cost

Higher Write Latency

More Storage
```

Indexes should be created only when they support important business access patterns.

---

# Query Flow

Without index:

```text
Application

↓

Need User By Email

↓

Scan Table

↓

Find User
```

With index:

```text
Application

↓

Query Email Index

↓

Return User
```

The second approach is dramatically faster and more cost-effective.

---

# Relationship with Data Modeling

Indexes do not replace good schema design.

Instead, they complement it.

A recommended design process is:

```text
Business Requirements

↓

Access Patterns

↓

Primary Key Design

↓

Secondary Indexes

↓

Application Development
```

Indexes should support access patterns that cannot be efficiently handled by the primary key.

---

# Real-World Example

A food delivery platform stores restaurants.

Primary Key:

```text
PK = RESTAURANT#100
```

Customers search by:

- Restaurant ID
- Cuisine
- City
- Rating

Instead of scanning every restaurant,

the application creates:

```text
Cuisine Index

City Index

Rating Index
```

Each index supports a specific business query with low latency.

---

# Benefits of Indexes

Indexes enable:

- Multiple query patterns
- Low-latency lookups
- Reduced scans
- Better scalability
- Flexible application design

They are a cornerstone of production DynamoDB applications.

---

# Limitations

Indexes are not a solution for every problem.

They:

- Increase write costs
- Consume storage
- Can become hot if poorly designed
- Require thoughtful key selection

Poorly designed indexes can create the same bottlenecks as poorly designed tables.

---

# Best Practices

- Design indexes around business access patterns.
- Avoid creating unnecessary indexes.
- Choose high-cardinality index partition keys.
- Monitor index usage and capacity.
- Keep projected attributes minimal where appropriate.
- Review index costs as traffic grows.

---

# Common Mistakes

## Creating an Index for Every Attribute

Avoid indexing every column "just in case."

Each index increases operational cost.

---

## Using Scan Instead of an Index

If an application frequently scans a table for a predictable query, an index is usually a better solution.

---

## Ignoring Index Costs

Indexes duplicate data and consume additional write capacity.

Always evaluate the trade-off between performance and cost.

---

## Poor Index Key Selection

Using low-cardinality values (such as `Status = ACTIVE`) as partition keys can create hot partitions.

Design index keys with the same care as primary keys.

---

# Architecture Perspective

```text
                    Application

                         │

                         ▼

                Business Query

                         │

             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼

      Primary Key Query      Secondary Index Query

             │                       │

             ▼                       ▼

          Base Table          GSI / LSI

             │                       │

             └───────────┬───────────┘
                         │
                         ▼

                 Application Response
```

Indexes provide alternate query paths while the base table remains the single source of truth.

---

# Production Considerations

Large enterprise systems often maintain multiple GSIs to support:

- Customer search
- Order tracking
- Reporting
- Analytics
- Operational dashboards
- Administrative queries

However, each new index is reviewed carefully to ensure that its business value justifies the additional storage and write costs.

Successful DynamoDB designs balance **performance**, **cost**, and **operational simplicity**.

---

# Interview Notes

A common interview question is:

> **Why do DynamoDB indexes exist?**

Indexes allow a table to support additional access patterns beyond those supported by the primary key, eliminating expensive table scans.

Another common question is:

> **How are DynamoDB indexes different from SQL indexes?**

SQL indexes primarily improve query performance on normalized tables. DynamoDB indexes are fundamental to the data model and provide alternate key structures that enable entirely new query patterns.

Another common question is:

> **Should every frequently queried attribute have an index?**

No. Each index increases storage, write costs, and maintenance overhead. Indexes should only be created for important business access patterns that cannot be efficiently supported by the primary key.

---

# Key Takeaways

- Secondary indexes provide alternate query paths for DynamoDB tables.
- Indexes allow a single table to support multiple business access patterns efficiently.
- DynamoDB provides two secondary index types: Global Secondary Indexes (GSIs) and Local Secondary Indexes (LSIs).
- Indexes improve read performance but increase storage and write costs.
- Good index design begins with understanding business requirements and access patterns.
- Indexes are a fundamental part of production DynamoDB architecture, not merely a performance optimization.