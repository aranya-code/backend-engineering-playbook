# README

## Overview

This section establishes the foundation for understanding SQL as a backend engineering skill.

The goal is not to learn SQL as an isolated query language. The objective is to understand how relational databases work, how SQL is executed, how database dialects differ, and how SQL fits into modern backend systems.

This section provides the conceptual foundation required before moving into query construction, advanced SQL, transactions, performance optimization, and production database engineering.

---

## What This Section Covers

The introduction is organized around five complementary areas:

```text
SQL Fundamentals
      ↓
Relational Database Context
      ↓
SQL Standards & Dialects
      ↓
SQL Execution Model
      ↓
Backend Engineering Application
      ↓
Learning Strategy
```

Each document answers a different question:

## Navigation

- [01- What Is SQL](./01-%20What%20Is%20SQL.md) — What SQL is and what problem it solves
- [02- SQL and Relational Databases](./02-%20SQL%20and%20Relational%20Databases.md) — How SQL relates to the relational model
- [03- SQL Standards and Database Dialects](./03-%20SQL%20Standards%20and%20Database%20Dialects.md) — Standard SQL versus database-specific implementations
- [04- SQL Execution Model](./04-%20SQL%20Execution%20Model.md) — What the database does when it receives and executes SQL
- [05- SQL for Backend Engineers](./05-%20SQL%20for%20Backend%20Engineers.md) — How SQL fits into real backend systems
- [06- SQL Learning Strategy](./06-%20SQL%20Learning%20Strategy.md) — How to learn and practice SQL for backend engineering

---

## Learning Sequence

Read the documents in order.

### SQL Fundamentals

Start with [What Is SQL](./01-%20What%20Is%20SQL.md).

This establishes:

- What SQL is
- Why SQL exists
- What problems SQL solves
- How applications interact with databases
- The role of SQL in backend development

The objective is to establish the correct mental model before learning syntax in depth.

### Relational Database Context

Continue with [SQL and Relational Databases](./02-%20SQL%20and%20Relational%20Databases.md).

This connects SQL to the relational model and introduces the concepts that explain why SQL is structured around:

- Tables
- Rows
- Columns
- Relationships
- Keys
- Constraints
- Sets
- Relational operations

This foundation becomes important when learning joins, aggregation, normalization, transactions, and schema design.

### Standards and Dialects

Read [SQL Standards and Database Dialects](./03-%20SQL%20Standards%20and%20Database%20Dialects.md).

SQL has standardized language concepts, but real databases implement SQL differently.

This document establishes the distinction between:

```text
SQL Standard
     ↓
Database Implementation
     ↓
Database Dialect
```

This is particularly important when working with PostgreSQL, MySQL, SQL Server, Oracle, or database-specific features.

### Execution Model

Continue with [SQL Execution Model](./04-%20SQL%20Execution%20Model.md).

This introduces the transition from:

> "What SQL do I write?"

to:

> "What does the database actually do with this SQL?"

The execution model provides the foundation for later understanding:

- Query planning
- Execution plans
- Indexes
- Joins
- Scans
- Sorting
- Aggregation
- Query optimization
- Database performance

### Backend Engineering Context

Read [SQL for Backend Engineers](./05-%20SQL%20for%20Backend%20Engineers.md).

This connects SQL knowledge to practical backend systems involving:

- Django
- FastAPI
- ORMs
- REST APIs
- gRPC
- PostgreSQL
- Redis
- Kafka
- Celery
- Microservices
- AWS
- Connection pooling
- Transactions
- Concurrency
- Production operations

The focus shifts from SQL as a language to SQL as part of an application architecture.

### Learning Strategy

Finish with [SQL Learning Strategy](./06-%20SQL%20Learning%20Strategy.md).

This defines how to progress from basic SQL knowledge toward production-level database engineering.

It emphasizes:

```text
Learn
  ↓
Practice
  ↓
Combine concepts
  ↓
Solve realistic problems
  ↓
Inspect execution
  ↓
Optimize
  ↓
Apply to backend systems
```

---

## How This Section Fits Into the SQL Journey

This introduction should be completed before moving into detailed SQL query topics.

The broader progression is:

```text
01- Introduction
        ↓
02- Query Fundamentals
        ↓
03- Relational Querying
        ↓
04- Advanced Querying
        ↓
05- Data Modification
        ↓
06- Transactions & Concurrency
        ↓
07- Database Design
        ↓
08- Indexes & Performance
        ↓
09- Production Database Engineering
        ↓
10- Advanced PostgreSQL
        ↓
11- Interview Questions
```

The exact folder structure may evolve as additional SQL topics are added, but the conceptual dependency should remain:

```text
Understand SQL
      ↓
Understand relational data
      ↓
Write queries
      ↓
Understand complex queries
      ↓
Modify data safely
      ↓
Control transactions
      ↓
Understand concurrency
      ↓
Optimize queries
      ↓
Operate databases
```

---

## Recommended Study Approach

Do not treat this section as a syntax memorization exercise.

For each document, focus on four questions:

1. **What problem does this concept solve?**
2. **How does it work?**
3. **When should a backend engineer use it?**
4. **What changes when the system reaches production scale?**

The conceptual knowledge should then be reinforced through hands-on PostgreSQL practice.

A useful progression is:

```text
Read the concept
      ↓
Write a small example
      ↓
Modify the example
      ↓
Break the example intentionally
      ↓
Understand the behavior
      ↓
Apply it to a backend scenario
```

---



## Key Takeaways

- **Start with the relational model and SQL fundamentals** before moving into advanced query techniques.
- **Understand the difference between SQL as a standard and database-specific dialects**, especially when specializing in PostgreSQL.
- **Learn the SQL execution model early** because query planning, indexes, joins, and performance depend on understanding what the database actually executes.
- **Connect SQL directly to backend engineering**, including ORMs, APIs, transactions, concurrency, connection pools, caching, and production operations.
- **Use hands-on practice alongside conceptual study** and progressively move from simple queries to realistic production-oriented database problems.