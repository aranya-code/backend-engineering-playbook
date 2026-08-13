# 09 - PartiQL

## Overview

PartiQL (SQL-Compatible Query Language) is a SQL-compatible query language supported by Amazon DynamoDB that allows developers to interact with DynamoDB tables using familiar SQL-like syntax.

Instead of using DynamoDB's native APIs such as `GetItem`, `PutItem`, `Query`, and `UpdateItem`, developers can write statements like:

```sql
SELECT * FROM Orders WHERE OrderId = '12345';
```

Internally, DynamoDB translates PartiQL statements into native DynamoDB API calls.

**Important:** PartiQL is **not** a relational database engine. It is simply another interface for interacting with DynamoDB.

---

# Why PartiQL Exists

Many developers coming from relational databases already know SQL.

Traditional DynamoDB development requires learning APIs like:

- GetItem
- PutItem
- Query
- Scan
- UpdateItem
- DeleteItem

AWS introduced PartiQL to reduce the learning curve.

Instead of:

```text
Application

↓

AWS SDK

↓

GetItem()
```

Developers can write:

```sql
SELECT * FROM Products
WHERE ProductId='P100';
```

The underlying database remains DynamoDB.

---

# Internal Architecture

```text
          Application

                │

         PartiQL Statement

                │

                ▼

       PartiQL Translation Layer

                │

                ▼

      Native DynamoDB API Calls

                │

                ▼

          DynamoDB Storage
```

The translation layer converts SQL-like statements into DynamoDB operations.

---

# Supported Operations

PartiQL supports common database operations including:

```sql
SELECT
INSERT
UPDATE
DELETE
```

These operations are translated into DynamoDB APIs.

---

# SELECT

Retrieve an item.

Example:

```sql
SELECT *
FROM Products
WHERE ProductId='P100';
```

Internally becomes:

```text
GetItem
```

or

```text
Query
```

depending on the query.

---

# INSERT

Insert a new item.

Example:

```sql
INSERT INTO Products VALUE
{
    'ProductId':'P100',
    'Name':'Laptop',
    'Price':1200
};
```

Internally:

```text
PutItem
```

---

# UPDATE

Modify existing attributes.

Example:

```sql
UPDATE Products
SET Price=1500
WHERE ProductId='P100';
```

Internally:

```text
UpdateItem
```

---

# DELETE

Remove an item.

Example:

```sql
DELETE
FROM Products
WHERE ProductId='P100';
```

Internally:

```text
DeleteItem
```

---

# Parameterized Statements

Applications should avoid dynamically concatenating SQL strings.

Instead:

```text
Statement

+

Parameters
```

Benefits:

- Prevents injection attacks
- Improves readability
- Easier maintenance

---

# PartiQL and Primary Keys

PartiQL still requires proper DynamoDB access patterns.

Good:

```sql
SELECT *
FROM Orders
WHERE CustomerId='C100';
```

Bad:

```sql
SELECT *
FROM Orders
WHERE Amount > 100;
```

Unless supported by an index, the second query results in a table scan.

SQL syntax does **not** eliminate DynamoDB limitations.

---

# PartiQL vs Native APIs

| Feature | Native API | PartiQL |
|----------|------------|----------|
| SQL Syntax | ❌ | ✅ |
| Learning Curve | Higher | Lower |
| Performance | Same | Same |
| Uses DynamoDB APIs | Yes | Yes |
| Access Pattern Rules | Yes | Yes |

Performance is effectively identical because both use the same underlying APIs.

---

# PartiQL vs SQL Databases

| Feature | SQL Database | DynamoDB PartiQL |
|----------|--------------|------------------|
| JOIN | ✅ | ❌ |
| Foreign Keys | ✅ | ❌ |
| Transactions | ✅ | Limited |
| GROUP BY | ✅ | ❌ |
| Window Functions | ✅ | ❌ |

PartiQL looks like SQL but does **not** provide full relational database capabilities.

---

# Execution Flow

```text
SELECT Statement

↓

Parser

↓

Translate

↓

GetItem / Query

↓

Return Result
```

---

# Real-World Example — Administration

Support engineer:

Instead of writing Python:

```text
AWS SDK

↓

GetItem
```

They execute:

```sql
SELECT *
FROM Users
WHERE UserId='123';
```

Useful for operational troubleshooting.

---

# Real-World Example — Updating Orders

Customer service changes status.

```sql
UPDATE Orders
SET Status='SHIPPED'
WHERE OrderId='10001';
```

Simple and readable.

---

# Real-World Example — Development

Backend developers familiar with PostgreSQL can begin working with DynamoDB faster using SQL-like statements.

---

# Real-World Example — AWS CLI

Instead of writing SDK code:

```text
Python

↓

Boto3

↓

UpdateItem
```

Operations teams can execute:

```sql
DELETE
FROM Sessions
WHERE SessionId='ABC123';
```

through the AWS CLI or SDKs that support PartiQL.

---

# Performance Considerations

PartiQL does **not** improve performance.

Example:

```sql
SELECT *
FROM Orders
WHERE CustomerId='C100';
```

Performance:

```text
Same

as

Query API
```

Likewise:

```sql
SELECT *
FROM Orders
WHERE Status='OPEN';
```

without an appropriate index performs the equivalent of a Scan.

SQL syntax does not bypass DynamoDB design principles.

---

# Best Practices

- Continue designing tables around access patterns.
- Use parameterized statements.
- Prefer Query over Scan.
- Use GSIs where additional access patterns are required.
- Monitor consumed RCUs and WCUs.
- Use PartiQL for developer productivity, not performance optimization.

---

# Common Mistakes

## Thinking PartiQL Makes DynamoDB Relational

Incorrect.

DynamoDB remains a NoSQL key-value/document database.

---

## Expecting SQL Features

Unsupported features include:

- JOIN
- GROUP BY
- HAVING
- Stored Procedures
- Window Functions
- Views

---

## Ignoring Primary Keys

This query:

```sql
SELECT *
FROM Orders
WHERE Amount > 100;
```

still requires a Scan if no supporting index exists.

---

## Choosing PartiQL for Speed

PartiQL provides a different syntax—not a faster execution engine.

---

# Architecture Perspective

```text
          SQL Statement

                │

            PartiQL

                │

     DynamoDB Translation Layer

                │

        Native API Operation

                │

           DynamoDB Table
```

PartiQL improves developer experience while preserving DynamoDB's architecture and performance characteristics.

---

# Production Considerations

PartiQL is commonly used for:

- Administrative tools
- Internal dashboards
- Operational scripts
- Data correction
- Developer productivity
- AWS CLI automation

High-throughput production services typically continue using native SDK APIs because they provide stronger typing, finer control, and clearer integration with application code.

The underlying performance characteristics remain the same regardless of whether the request originates from PartiQL or the native SDK.

---

# Interview Notes

A common interview question is:

> **What is PartiQL in DynamoDB?**

PartiQL is a SQL-compatible query language that allows developers to interact with DynamoDB using familiar SQL-like syntax. Internally, DynamoDB translates PartiQL statements into native API calls.

Another common question is:

> **Does PartiQL improve DynamoDB performance?**

No. PartiQL is only a different query interface. Performance is effectively the same as using the native DynamoDB APIs.

Another common question is:

> **Can PartiQL perform SQL JOIN operations?**

No. DynamoDB does not support relational joins. PartiQL does not change this limitation.

Another common question is:

> **When should you use PartiQL?**

PartiQL is useful for administrative tasks, operational tooling, scripting, ad hoc queries, and helping SQL developers work with DynamoDB. Native SDK APIs are generally preferred for high-performance production applications.

---

# Key Takeaways

- PartiQL provides a SQL-compatible interface for DynamoDB.
- It translates SQL-like statements into native DynamoDB API calls.
- It supports familiar operations such as `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.
- PartiQL does not make DynamoDB a relational database and does not support features such as joins or `GROUP BY`.
- Performance is the same as the equivalent native DynamoDB operation.
- PartiQL is best suited for administration, scripting, troubleshooting, and improving developer productivity.
```