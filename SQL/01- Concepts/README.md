# Concepts

## Overview

This section establishes the conceptual foundation required for backend SQL engineering. Before writing queries, constructing schemas, or optimizing workloads, a backend engineer must understand what SQL is, how relational databases model data, what guarantees the database enforces, and how SQL operations are categorized.

The material here is not about syntax. It is about building the mental model that makes every subsequent SQL topic easier to reason about correctly.

---

## Navigation

- [01- Introduction](./01-%20Introduction/README.md) — What SQL is, how it executes, and how it fits into backend systems
- [02- Relational Database Fundamentals](./02-%20Relational%20Database%20Fundamentals/README.md) — Tables, keys, relationships, constraints, and data integrity
- [03- SQL Command Categories](./03-%20SQL%20Command%20Categories/README.md) — DDL, DML, DQL, DCL, and TCL

---

## What This Section Covers

### 01- Introduction

The introduction establishes SQL as a backend engineering skill rather than an isolated query language. It covers what SQL is, how relational databases execute queries, what SQL standards mean in practice, and how SQL fits into backend systems.

Key topics: SQL fundamentals, the relational model, SQL standards and dialects, the SQL execution model, SQL for backend engineers, and a practical learning strategy.

### 02- Relational Database Fundamentals

This section covers the relational data model in depth — how tables, rows, columns, primary keys, foreign keys, relationships, constraints, and integrity rules work together. The goal is to understand schema design as an engineering discipline with direct consequences for correctness, performance, and maintainability.

Key topics: tables, primary keys, foreign keys, one-to-one, one-to-many, and many-to-many relationships, NULL and missing data, constraints, data integrity, referential integrity, and database design rules.

### 03- SQL Command Categories

This section explains how SQL operations are organized by responsibility. Understanding the distinction between DDL, DML, DQL, DCL, and TCL gives backend engineers a structured way to reason about schema changes, data manipulation, querying, access control, and transaction management.

Key topics: DDL (schema definition), DML (data modification), DQL (data retrieval), DCL (access control), TCL (transaction control), category comparison, and when to use each category.

---

## Key Takeaways

- **Understand the relational model before focusing on query syntax** — tables, keys, and relationships define the structure that all SQL queries operate against.
- **SQL is not just a query language** — it controls schema structure, data modification, access permissions, and transaction boundaries through distinct command categories.
- **Database constraints enforce correctness at the persistence layer** — not relying on application code alone makes systems more reliable across services, jobs, and migrations.
- **The SQL execution model matters** — understanding how the database parses, plans, and executes SQL explains why indexes, JOINs, and predicates behave the way they do.
- **SQL fits into backend systems in multiple ways** — through ORMs, raw queries, migrations, API design, concurrency control, and production operations.
