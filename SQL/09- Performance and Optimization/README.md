# Performance and Optimization

## Overview

This section covers the SQL and database-level techniques used to make backend systems fast, scalable, and operationally efficient. Performance optimization is not guesswork — it is a measurement-driven engineering discipline that starts with understanding how the database executes queries, how data is stored and located, and what the actual workload demands.

The topics here range from index design and query execution to table partitioning. Each represents a different layer at which a backend engineer can intervene to reduce unnecessary database work and improve response times under production load.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Performance and Optimization](./README.md) | Performance and Reliability | Indexes, query execution, execution plans, and table partitioning |
| 02 | [01- Indexes](./01-%20Indexes/README.md) | Performance and Reliability | Index types, design, workload-driven strategy, maintenance, and anti-patterns |
| 03 | [02- Query Execution and Optimization](./02-%20Query%20Execution%20and%20Optimization/README.md) | Performance and Reliability | Execution plans, SARGability, predicate pushdown, and optimization decision guides |
| 04 | [03- Partitioning](./03-%20Partitioning/README.md) | Performance and Reliability | Table partitioning strategies, partition pruning, and lifecycle management |

---

## What This Section Covers

### 01- Indexes

Indexes are the primary tool for improving SQL read performance, but effective indexing is a workload-design problem — not a checklist to apply blindly. This section covers all major PostgreSQL index types (B-tree, hash, composite, partial, expression, covering, unique), how indexes interact with `ORDER BY`, `JOIN`, `GROUP BY`, `DISTINCT`, `LIKE`, `NULL`, and range queries, index selectivity and cardinality, the read/write performance trade-off, indexing strategy, monitoring and maintenance, identifying missing and duplicate indexes, and common indexing anti-patterns.

### 02- Query Execution and Optimization

SQL performance problems require understanding how the database executes queries before attempting to fix them. This section covers predicate pushdown, SARGability (writing predicates that allow index usage), avoiding functions on indexed columns, JOIN optimization, aggregation optimization, subquery and CTE optimization, pagination optimization, and when to optimize versus when not to. It includes a structured query optimization decision guide and a catalogue of common SQL performance anti-patterns.

### 03- Partitioning

Partitioning divides a large logical table into smaller physical partitions while keeping a single query interface for the application. The primary benefits are partition pruning (reducing data scanned), data lifecycle management, and maintenance isolation. This section covers range, list, hash, and composite partitioning strategies, partition key selection, partition maintenance and lifecycle automation, multi-tenant and time-series partitioning patterns, and how partitioning compares with indexing, caching, read replicas, and sharding.

---

## Key Takeaways

- **Measure before optimizing** — execution plans, query latency metrics, and index usage statistics are the starting point; do not add indexes or restructure queries without evidence.
- **Indexes change query plans, not query correctness** — a missing index causes a performance problem, not a correctness problem; always validate the execution plan after adding an index.
- **SARGability determines whether an index can be used** — predicates that apply functions, type casts, or implicit conversions to indexed columns often prevent index scans.
- **Partitioning is a table design decision, not a query optimization** — it is most valuable for pruning, data lifecycle management, and maintenance at large scale, and requires the partition key to match the actual query patterns.
- **Query optimization is an engineering process, not an art** — identify the bottleneck from measurements, understand the root cause, apply the targeted change, and validate the result.
