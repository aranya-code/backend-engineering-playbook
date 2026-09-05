# SQL Projects

## Overview

The **Projects** section applies SQL skills developed throughout the playbook to realistic, end-to-end database design and query engineering challenges.

Each project is structured around a real-world backend system. Projects progress from schema design through query writing, indexing, transaction handling, concurrency, performance optimization, and backend integration patterns.

The goal is not to build working applications. The goal is to practice making production-quality SQL decisions in realistic contexts — the same decisions a senior backend engineer must make when designing and operating a database-backed system.

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Projects](./README.md) | Applied SQL | End-to-end SQL projects: e-commerce, banking, multi-tenant SaaS, and analytics databases |
| 02 | [01- E-Commerce Database](./01-%20E-Commerce%20Database/README.md) | Applied SQL | Relational schema, queries, indexing, and backend patterns for an e-commerce platform |
| 03 | [02- Banking Transaction Database](./02-%20Banking%20Transaction%20Database/README.md) | Applied SQL | Transaction modeling, concurrency, isolation levels, and locking for a banking system |
| 04 | [03- Multi Tenant SaaS Database](./03-%20Multi%20Tenant%20SaaS%20Database/README.md) | Applied SQL | Tenant isolation strategies, row-level security, and scaling for a SaaS platform |
| 05 | [04- Analytics and Reporting Database](./04-%20Analytics%20and%20Reporting%20Database/README.md) | Applied SQL | OLAP schema design, aggregation queries, window functions, and reporting views |

---

## What This Section Covers

### 01- E-Commerce Database

A practical project covering the design and operation of a relational database for an e-commerce platform. Topics include schema design, CRUD operations, JOIN queries, aggregation, subqueries, CTEs, window functions, indexing strategy, query optimization, transaction scenarios, and backend query patterns.

### 02- Banking Transaction Database

A project focused on the correctness and safety requirements of a financial transaction system. Topics include account and customer modeling, transaction design, concurrency scenarios, deadlock prevention, isolation level selection, indexing strategy, and backend integration patterns.

### 03- Multi Tenant SaaS Database

A project covering the architectural and operational challenges of serving multiple tenants from a shared database. Topics include tenant data modeling, isolation strategies, query patterns, indexing, row-level security, pagination, performance considerations, and scaling strategy.

### 04- Analytics and Reporting Database

A project focused on OLAP-oriented schema design and query engineering for analytics and reporting workloads. Topics include schema design, OLTP vs OLAP trade-offs, aggregation queries, window functions, CTE-based analytics, reporting views, and performance optimization.

---

## Key Takeaways

- **Schema design is a production decision** — the relational model chosen at the start constrains query patterns, indexing options, and scalability for the lifetime of the system.
- **Transactions and concurrency must be modeled explicitly** — financial and multi-tenant systems require deliberate isolation level and locking decisions, not defaults.
- **Indexing follows access patterns** — indexes should be designed around the actual queries the application runs, not added speculatively.
- **Analytics workloads require different schema trade-offs** — OLAP-oriented designs accept denormalization and materialization in exchange for query simplicity and aggregation performance.
- **Production SQL is validated end-to-end** — correctness, execution plans, index usage, concurrency behavior, and operational impact must all be verified before a query is considered production-ready.
