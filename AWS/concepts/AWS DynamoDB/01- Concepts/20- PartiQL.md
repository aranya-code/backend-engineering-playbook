# 20 - PartiQL

## Overview

One of the biggest challenges developers face when learning DynamoDB is transitioning from a **SQL mindset** to a **NoSQL mindset**.

In relational databases, developers write queries like:

```sql
SELECT *
FROM Users
WHERE UserId = 1001;
```

In DynamoDB, the equivalent operation traditionally requires an API call such as:

```text
GetItem
```

or

```text
Query
```

using SDKs or the AWS CLI.

To make DynamoDB more approachable, AWS introduced **PartiQL**.

PartiQL is a **SQL-compatible query language** that allows developers to interact with DynamoDB using familiar SQL-like syntax while DynamoDB internally translates those statements into native API operations.

It is important to understand that **PartiQL is not a relational database engine**. It is simply another way of interacting with DynamoDB.

---

# Why PartiQL Exists

Suppose a development team has spent years working with:

- MySQL
- PostgreSQL
- SQL Server
- Oracle

Moving to DynamoDB requires learning an entirely new API.

Instead of:

```sql
SELECT *
FROM Orders
WHERE OrderId = 1001;
```

developers must write:

```text
GetItem
```

or

```text
Query
```

using SDK-specific syntax.

PartiQL lowers the learning curve by allowing SQL-like statements.

---

# PartiQL Architecture

Applications can communicate with DynamoDB in two ways.

```text
Application

        │

 ┌──────┴─────────┐

 ▼                ▼

PartiQL         SDK API

 │                │

 └──────┬─────────┘

        ▼

 DynamoDB Engine
```

Regardless of which interface is used, DynamoDB executes native operations internally.

---

# SQL vs PartiQL

Traditional SQL:

```sql
SELECT *
FROM Users
WHERE UserId = 1001;
```

Equivalent PartiQL:

```sql
SELECT *
FROM Users
WHERE UserId = 'USER#1001';
```

Behind the scenes, DynamoDB converts the statement into a native **GetItem** or **Query** request.

---

# Supported Operations

PartiQL supports familiar SQL operations.

## SELECT

Retrieve items.

```sql
SELECT *
FROM Products
WHERE ProductId = 'P100'
```

---

## INSERT

Insert new items.

```sql
INSERT INTO Users VALUE
{
    'UserId':'USER#1001',
    'Name':'Alice'
}
```

---

## UPDATE

Modify existing items.

```sql
UPDATE Users

SET Age = 30

WHERE UserId = 'USER#1001'
```

---

## DELETE

Delete items.

```sql
DELETE

FROM Users

WHERE UserId = 'USER#1001'
```

---

# How SELECT Works

Unlike relational databases, PartiQL still follows DynamoDB's access model.

Good example:

```sql
SELECT *

FROM Orders

WHERE OrderId='ORDER#1001'
```

Efficient.

Because:

```text
Partition Key

↓

Known
```

---

Poor example:

```sql
SELECT *

FROM Orders

WHERE CustomerName='John'
```

Unless:

```text
CustomerName

↓

Indexed
```

DynamoDB must scan the table.

The SQL syntax looks familiar, but DynamoDB's performance rules still apply.

---

# PartiQL Doesn't Remove DynamoDB Limitations

Many developers mistakenly assume PartiQL turns DynamoDB into PostgreSQL.

It does not.

For example:

Relational SQL supports:

```sql
JOIN
```

PartiQL for DynamoDB does **not**.

Similarly:

```sql
GROUP BY

HAVING

WINDOW FUNCTIONS

FOREIGN KEYS
```

are not supported.

The underlying database remains DynamoDB.

---

# PartiQL and Primary Keys

Efficient queries still require:

```text
Partition Key

or

Partition Key + Sort Key
```

Example:

```sql
SELECT *

FROM Users

WHERE UserId='USER#1001'
```

Fast.

Example:

```sql
SELECT *

FROM Users

WHERE Age=30
```

Without an index:

```text
Table Scan
```

---

# Conditional Updates

PartiQL supports conditional operations.

Example:

```sql
UPDATE Inventory

SET Stock = Stock - 1

WHERE ProductId='P100'

AND Stock > 0
```

This prevents negative inventory.

---

# Batch Operations

PartiQL can execute multiple statements through batch APIs.

Example workflow:

```text
Application

↓

Batch Execute Statement

↓

Statement 1

Statement 2

Statement 3
```

Each statement is translated into the appropriate DynamoDB operation.

---

# Parameterized Statements

Applications should avoid concatenating user input directly into queries.

Instead of:

```sql
SELECT *

FROM Users

WHERE UserId='USER123'
```

SDKs support parameterized statements.

Benefits:

- Prevent injection attacks
- Simplify query generation
- Improve readability

---

# PartiQL vs Native SDK

Both approaches access the same database.

| Feature | PartiQL | Native SDK |
|----------|----------|------------|
| SQL Syntax | ✅ | ❌ |
| Familiar for SQL Developers | ✅ | ❌ |
| Performance | Equivalent | Equivalent |
| Supports All DynamoDB Features | Nearly | ✅ |
| Learning Curve | Lower | Higher |

Native SDKs expose every DynamoDB capability.

PartiQL provides a simpler interface for many common operations.

---

# PartiQL vs SQL

Although the syntax is similar, important differences remain.

| Feature | SQL Database | PartiQL on DynamoDB |
|----------|--------------|---------------------|
| JOIN | ✅ | ❌ |
| Foreign Keys | ✅ | ❌ |
| GROUP BY | ✅ | Limited |
| Transactions | ✅ | ✅ (Uses DynamoDB Transactions) |
| Tables | Relational | NoSQL |
| Schema | Fixed | Flexible |

PartiQL should be viewed as a query language—not evidence that DynamoDB has become relational.

---

# Performance Considerations

PartiQL does **not** improve performance.

These two operations perform similarly:

```sql
SELECT *

FROM Users

WHERE UserId='USER#1001'
```

and

```text
GetItem(UserId)
```

The execution path is different only at the client interface.

Internally:

```text
PartiQL

↓

Translation Layer

↓

Native DynamoDB API

↓

Storage Engine
```

Performance depends on:

- Access patterns
- Index design
- Partition keys

—not on whether SQL syntax is used.

---

# Common Use Cases

PartiQL is commonly used for:

- Database administration
- AWS Console queries
- Ad hoc investigations
- Learning DynamoDB
- Migration from SQL systems
- Simple CRUD applications
- Command-line operations

Many production applications continue using native SDKs for maximum control.

---

# Best Practices

- Design tables based on access patterns, not SQL habits.
- Continue using efficient partition keys.
- Avoid scans whenever possible.
- Use indexes for non-key lookups.
- Parameterize statements in production.
- Prefer native SDKs for advanced DynamoDB features.

---

# Common Mistakes

## Assuming SQL Performance Rules Apply

SQL syntax does not change DynamoDB's storage architecture.

Poor access patterns remain slow.

---

## Expecting JOIN Support

DynamoDB intentionally avoids joins.

Relationships should be modeled through denormalization or multiple queries.

---

## Forgetting About Partition Keys

A `WHERE` clause without an indexed attribute often results in a scan.

---

## Thinking PartiQL Replaces the SDK

PartiQL is an alternative interface.

The SDK still exposes the full DynamoDB feature set.

---

# Real-World Example

An operations engineer needs to investigate a production issue.

Instead of writing a Python script using the AWS SDK:

```text
Create Session

↓

Configure Client

↓

Call GetItem
```

they simply execute:

```sql
SELECT *

FROM Orders

WHERE OrderId='ORDER#987654'
```

The investigation becomes faster while still using DynamoDB underneath.

---

# Architecture Perspective

Typical request flow:

```text
Application

↓

PartiQL Statement

↓

DynamoDB PartiQL Engine

↓

Native API Translation

↓

Storage Partitions

↓

Response
```

PartiQL acts as a translation layer—not a separate database engine.

---

# Interview Notes

A common interview question is:

> **Does PartiQL make DynamoDB a relational database?**

No.

PartiQL provides a SQL-like syntax, but DynamoDB remains a NoSQL key-value and document database. There are still no joins, foreign keys, or relational query planning. Performance continues to depend on access patterns, partition keys, and indexes.

Another common question is:

> **Should production applications use PartiQL or the native SDK?**

It depends.

PartiQL is excellent for administrative tasks, ad hoc queries, and easing the transition for SQL developers. For production systems that require advanced features, precise control, or maximum flexibility, many teams prefer the native DynamoDB SDK because it exposes the complete API surface.

---

# Key Takeaways

- PartiQL is a SQL-compatible query language for DynamoDB.
- It translates SQL-like statements into native DynamoDB API operations.
- It supports common CRUD operations such as `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.
- PartiQL does **not** add relational database features like joins or foreign keys.
- Performance is determined by DynamoDB's data model, not by SQL syntax.
- Efficient PartiQL queries still require well-designed partition keys and indexes.
- PartiQL is a productivity feature that makes DynamoDB more accessible without changing its underlying architecture.