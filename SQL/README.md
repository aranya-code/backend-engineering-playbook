# SQL Engineering Playbook

## Overview

This is the SQL section of the backend engineering playbook. It covers relational database fundamentals, query writing, schema design, performance, operations, security, and production engineering patterns — primarily using PostgreSQL.

SQL is the primary interface between backend applications and relational data. Writing syntactically correct SQL is not enough for production engineering. A senior backend engineer must also understand:

- Why a query plan chooses a sequential scan over an index scan.
- How isolation levels affect data visibility under concurrent writes.
- Why a schema change can lock a 100-million-row table and take down production.
- How connection pool exhaustion manifests at the application layer.
- When to normalize and when denormalization is the correct trade-off.
- How to diagnose a slow query in production without causing more harm.

The material is structured to progress from foundational SQL knowledge through production-grade backend engineering judgment.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Concepts](./01-%20Concepts/README.md) | SQL Foundations | Relational database fundamentals, SQL command categories, and the relational model |
| 02 | [Query Fundamentals](./02-%20Query%20Fundamentals/README.md) | SQL Foundations | SELECT, filtering, sorting, operators, aggregate functions, string functions, dates, and NULL handling |
| 03 | [Query-Logic and Transformation](./03-%20Query-Logic%20and%20Transformation/README.md) | SQL Foundations | CASE WHEN, type casting, and set operators |
| 04 | [Query Composition](./04-%20Query%20Composition/README.md) | SQL Foundations | JOINs, subqueries, and Common Table Expressions |
| 05 | [Advanced Queries](./05-%20Advanced%20Queries/README.md) | SQL Foundations | Window functions, ranking, value functions, and decision guides |
| 06 | [Database Objects](./06-%20Database%20Objects/README.md) | Schema and Data Management | Views and stored procedures |
| 07 | [Data Modification](./07-%20Data%20Modification/README.md) | Schema and Data Management | INSERT, UPDATE, DELETE, UPSERT, and bulk data operations |
| 08 | [Data Modelling](./08-%20Data%20Modelling/README.md) | Schema and Data Management | Data types, database constraints, schema design, and normalization |
| 09 | [Performance and Optimization](./09-%20Performance%20and%20Optimization/README.md) | Performance and Reliability | Indexes, query execution, execution plans, and table partitioning |
| 10 | [Transactions and Concurrency](./10-%20Transactions%20and%20Concurrency/README.md) | Performance and Reliability | ACID properties, isolation levels, locking, and deadlocks |
| 11 | [Architecture](./11-%20Architecture/README.md) | Production Engineering | Database internals, replication, scaling, HA, and production architecture patterns |
| 12 | [Security](./12-%20Security/README.md) | Production Engineering | Roles, privileges, SQL injection, encryption, auditing, and credential management |
| 13 | [CLI](./13-%20CLI/README.md) | Production Engineering | PostgreSQL psql CLI, database inspection, diagnostics, and operational workflows |
| 14 | [Troubleshooting](./14-%20Troubleshooting/README.md) | Production Engineering | Diagnosing query problems, slow queries, locks, timeouts, and production incidents |
| 15 | [Operations](./15-%20Operations/README.md) | Production Engineering | Monitoring, maintenance, backups, recovery, capacity planning, and failover |
| 16 | [Deployment](./16-%20Deployment/README.md) | Production Engineering | Schema migrations, zero-downtime changes, CI/CD, and production deployment safety |
| 17 | [Interview Questions](./17-%20Interview%20Questions/README.md) | Applied SQL | SQL interview questions from fundamentals through senior backend and production scenarios |
| 18 | [Practice](./18-%20Practice/README.md) | Applied SQL | Hands-on SQL exercises from basic CRUD through transactions, optimization, and production scenarios |
| 19 | [SQL Patterns and Decision Guides](./19-%20SQL%20Patterns%20and%20Decision%20Guides/README.md) | Applied SQL | Choosing the right SQL technique for common backend engineering decisions |
| 20 | [SQL Anti-Patterns and Common Mistakes](./20-%20SQL%20Anti-Patterns%20and%20Common%20Mistakes/README.md) | Applied SQL | Production SQL mistakes covering correctness, performance, concurrency, and security |
| 21 | [Projects](./21-%20projects/README.md) | Applied SQL | End-to-end SQL projects: e-commerce, banking, multi-tenant SaaS, and analytics databases |

---

## What This Playbook Covers

### Layer 1 — SQL Foundations (01–05)

The foundation layer develops the ability to read, write, and reason about SQL queries correctly.

**[01- Concepts](./01-%20Concepts/README.md)** establishes the relational model: tables, rows, keys, relationships, and how SQL commands are categorised into DDL, DML, DQL, DCL, and TCL. This is the mental model everything else builds on.

**[02- Query Fundamentals](./02-%20Query%20Fundamentals/README.md)** covers the complete SELECT statement — filtering with WHERE, sorting with ORDER BY, pagination with LIMIT/OFFSET, logical and comparison operators, aggregate functions (COUNT, SUM, AVG, MIN, MAX), string manipulation, date and time arithmetic, and NULL handling. These are the building blocks of every SQL query a backend application will ever run.

**[03- Query-Logic and Transformation](./03-%20Query-Logic%20and%20Transformation/README.md)** covers conditional logic with CASE WHEN, type casting and conversion between data types, and set operators (UNION, INTERSECT, EXCEPT). These constructs allow complex business logic to be expressed directly in SQL.

**[04- Query Composition](./04-%20Query%20Composition/README.md)** covers the techniques for combining data from multiple sources: INNER, LEFT, RIGHT, FULL OUTER, CROSS, and self JOINs; scalar, row, and table subqueries; and Common Table Expressions (CTEs) including recursive CTEs. This is where result grain, cardinality, and JOIN correctness become critical skills.

**[05- Advanced Queries](./05-%20Advanced%20Queries/README.md)** covers window functions — the most powerful analytical SQL construct. Topics include window frame definition, aggregate window functions, ranking functions (ROW_NUMBER, RANK, DENSE_RANK), value functions (LAG, LEAD, FIRST_VALUE, LAST_VALUE), and decision guides for choosing between GROUP BY and window functions.

---

### Layer 2 — Schema and Data Management (06–08)

The schema layer covers how data is defined, structured, modified, and protected.

**[06- Database Objects](./06-%20Database%20Objects/README.md)** covers views — persistent query abstractions used to simplify complex queries, enforce access control, and hide schema complexity — and stored procedures, including their appropriate use cases, trade-offs vs application logic, and performance implications.

**[07- Data Modification](./07-%20Data%20Modification/README.md)** covers the full DML surface: INSERT, UPDATE, DELETE, UPSERT with ON CONFLICT, RETURNING clauses, soft deletes, bulk inserts, and safe patterns for modifying large datasets without causing lock contention or replication lag.

**[08- Data Modelling](./08-%20Data%20Modelling/README.md)** covers data type selection (choosing the right type for correctness, storage, and indexing), all database constraint types (NOT NULL, UNIQUE, PRIMARY KEY, FOREIGN KEY, CHECK, DEFAULT), schema design principles, entity-relationship modeling, normalization through 3NF and BCNF, denormalization trade-offs, and schema evolution strategies.

---

### Layer 3 — Performance and Reliability (09–10)

The performance layer covers the mechanics that determine whether a query runs in milliseconds or minutes, and whether concurrent writes remain correct.

**[09- Performance and Optimization](./09-%20Performance%20and%20Optimization/README.md)** is the largest technical section. It covers index internals (B-tree, Hash, GIN, GiST, partial, composite), index design strategy, cardinality, selectivity, index maintenance, the query execution lifecycle (parse → plan → execute), the cost-based optimizer, execution plan reading with EXPLAIN and EXPLAIN ANALYZE, scan types (sequential, index, bitmap), join algorithms (nested loop, hash, merge), SARGability, query rewriting, and table partitioning (range, list, hash, composite).

**[10- Transactions and Concurrency](./10-%20Transactions%20and%20Concurrency/README.md)** covers ACID guarantees, the four isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable), MVCC, shared and exclusive locks, row-level and table-level locks, deadlock detection and prevention, optimistic vs pessimistic concurrency, and transaction design rules for backend applications.

---

### Layer 4 — Production Engineering (11–16)

The production layer covers everything required to operate a database reliably in a real backend system.

**[11- Architecture](./11-%20Architecture/README.md)** covers the internal architecture of a relational database — storage engine, buffer pool, WAL, query parser/planner/executor — and how it connects to production backend systems. Topics include OLTP vs OLAP architecture, primary/replica topology, connection pooling, vertical and horizontal scaling, replication, sharding, multi-tenancy, and high availability.

**[12- Security](./12-%20Security/README.md)** covers the full database security model: authentication vs authorization, PostgreSQL roles and privilege management, least privilege principle, SQL injection and parameterized queries, row-level security, encryption at rest and in transit, secret and credential management, database auditing, and security logging. Security is treated as a layered system, not a checklist item.

**[13- CLI](./13-%20CLI/README.md)** covers the PostgreSQL `psql` command-line interface as an engineering tool — not just a query runner. Topics include connecting to databases, schema inspection, running diagnostics with EXPLAIN, transaction control from the CLI, import/export workflows, administrative commands, and production diagnostic workflows.

**[14- Troubleshooting](./14-%20Troubleshooting/README.md)** is a systematic reference for diagnosing SQL problems in production. It covers query correctness problems (no rows, too many rows, NULL errors, JOIN issues), transaction and locking problems (deadlocks, lock contention), performance problems (slow queries, bad execution plans, missing indexes), resource problems (high CPU, high memory, connection exhaustion), and production incident workflows.

**[15- Operations](./15-%20Operations/README.md)** covers the ongoing work of running a database in production: monitoring (query performance, locks, connections, storage), index and table maintenance, VACUUM and ANALYZE, backup strategies, point-in-time recovery, capacity planning, connection pooling operations, read replica management, and database failover.

**[16- Deployment](./16-%20Deployment/README.md)** covers the engineering discipline of changing a production database safely. Topics include schema migration design, migration ordering, backward-compatible schema changes, zero-downtime migrations, safe column addition and removal, production index creation (CONCURRENTLY), large table migration strategies, migration rollback planning, CI/CD integration, Django migrations, and SQLAlchemy/Alembic workflows.

---

### Layer 5 — Applied SQL (17–21)

The applied layer connects all previous knowledge to realistic engineering scenarios.

**[17- Interview Questions](./17-%20Interview%20Questions/README.md)** covers the full range of SQL interview topics — from SELECT and JOIN questions through aggregation, NULL semantics, window functions, indexing, transactions, concurrency, performance, security, and senior-level production scenarios. The goal is not to memorize answers but to develop the reasoning required to explain decisions clearly under interview conditions.

**[18- Practice](./18-%20Practice/README.md)** provides hands-on exercises across the complete SQL topic range. Exercises progress from schema creation and CRUD through filtering, JOINs, aggregation, CTEs, window functions, indexing, query optimization, transactions, concurrency, pagination, backend API query patterns, and production scenario exercises.

**[19- SQL Patterns and Decision Guides](./19-%20SQL%20Patterns%20and%20Decision%20Guides/README.md)** is a practical decision reference for choosing between SQL constructs that solve similar problems — JOIN vs subquery vs EXISTS, CTE vs subquery vs temporary table, GROUP BY vs window function, offset vs keyset pagination, normalization vs denormalization, and more. Each guide explains the trade-offs and when each option is appropriate.

**[20- SQL Anti-Patterns and Common Mistakes](./20-%20SQL%20Anti-Patterns%20and%20Common%20Mistakes/README.md)** catalogs the SQL mistakes that most commonly become expensive or dangerous in production — SELECT *, missing WHERE clauses, Cartesian products, NOT IN with NULLs, functions on indexed columns, N+1 queries, unbounded queries, large transactions, and SQL injection. Each anti-pattern includes the diagnosis, production impact, and correct alternative.

**[21- projects](./21-%20projects/README.md)** applies all SQL knowledge to four end-to-end projects: an e-commerce database (schema design through backend query patterns), a banking transaction database (financial modeling, concurrency, and isolation), a multi-tenant SaaS database (tenant isolation, RLS, and scaling), and an analytics database (OLAP schema, aggregation, window functions, and reporting views).

---

## Recommended Learning Path

```text
01- Concepts
      ↓
02- Query Fundamentals
      ↓
03- Query-Logic and Transformation
      ↓
04- Query Composition
      ↓
05- Advanced Queries
      ↓
08- Data Modelling
      ↓
07- Data Modification
      ↓
06- Database Objects
      ↓
09- Performance and Optimization
      ↓
10- Transactions and Concurrency
      ↓
11- Architecture
      ↓
12- Security
      ↓
13- CLI
      ↓
14- Troubleshooting
      ↓
15- Operations
      ↓
16- Deployment
      ↓
19- SQL Patterns and Decision Guides
      ↓
20- SQL Anti-Patterns and Common Mistakes
      ↓
17- Interview Questions  +  18- Practice  +  21- projects
```

The path is sequential but not strictly linear. Practitioners with SQL experience can enter at the relevant layer. The Performance, Architecture, and Deployment sections require foundational query knowledge to be meaningful.

---

## Engineering Standards

Every section in this playbook is written to the following standard:

- **Correctness first** — a query must return the right result under all data conditions, including NULLs, duplicates, empty sets, and concurrent writes.
- **Production awareness** — every construct is evaluated for its behavior at scale, under load, and in a concurrent multi-application environment.
- **Decision reasoning** — the goal is not to memorize syntax but to develop the ability to choose the right tool and explain the trade-off.
- **Backend integration** — SQL decisions are always connected to their implications for Django, FastAPI, connection pools, ORMs, background workers, caching, and infrastructure.
