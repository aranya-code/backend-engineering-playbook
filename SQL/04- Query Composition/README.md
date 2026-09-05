# Query Composition

## Overview

This section covers the SQL tools used to compose queries from multiple relations and stages. Query composition is where SQL becomes a genuine relational algebra — combining tables through JOINs, embedding queries within queries through subqueries, and structuring multi-stage logic through Common Table Expressions.

These are not advanced topics in the sense of being rare. Every non-trivial production query involves at least one of these constructs. The focus here is not on syntax but on correctness, cardinality reasoning, performance behavior, and knowing when to choose one composition strategy over another.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Query Composition](./README.md) | SQL Foundations | JOINs, subqueries, and Common Table Expressions |
| 02 | [01- JOINs](./01-%20JOINs/README.md) | SQL Foundations | Combining rows from related tables with full cardinality control |
| 03 | [02- Subqueries](./02-%20Subqueries/README.md) | SQL Foundations | Embedding queries as scalar values, derived tables, and existence tests |
| 04 | [03- Common Table Expressions (CTE)](./03-%20Common%20Table%20Expressions%20%28CTE%29/README.md) | SQL Foundations | Named, reusable query stages using the WITH clause |

---

## What This Section Covers

### 01- JOINs

JOINs combine rows from two or more relations based on a join condition. The difficulty in production is not the syntax — it is choosing the correct join type, preserving the intended result cardinality, placing predicates in the right clause, and avoiding row multiplication. This section covers all JOIN types (INNER, LEFT, RIGHT, FULL OUTER, CROSS, SELF), join conditions, NULL behavior in joins, relationship cardinality, result duplication, JOIN ordering, and how to compare JOINs against subqueries and EXISTS checks. It also covers JOIN performance and practical JOIN patterns.

### 02- Subqueries

Subqueries embed one `SELECT` statement inside another. They can appear in the `SELECT` list as scalar expressions, in the `FROM` clause as derived tables, and in the `WHERE` clause as membership tests or existence checks. This section covers scalar, single-row, and multi-row subqueries; correlated versus non-correlated subqueries; `IN`, `NOT IN`, `EXISTS`, and `NOT EXISTS`; subquery execution rules; and how subqueries compare to JOINs, CTEs, and window functions. It also covers when to use subqueries and when to avoid them.

### 03- Common Table Expressions (CTE)

CTEs define named, temporary result sets using the `WITH` clause. They make multi-stage queries readable by giving each relational stage a meaningful name. This section covers CTE syntax, single and multiple CTEs, CTE dependencies, CTEs used with JOINs, aggregations, window functions, and DML statements, recursive CTEs (for hierarchies and graph traversal), CTE scope and lifetime, comparisons with subqueries, derived tables, views, and temporary tables, and production performance considerations.

---

## Key Takeaways

- **Define the result grain before writing any JOIN** — what one output row should represent determines which JOIN type is appropriate and whether row multiplication is a risk.
- **Subquery placement affects semantics** — scalar subqueries in SELECT, derived tables in FROM, and existence checks in WHERE serve different relational purposes and have different execution characteristics.
- **CTEs are a query-composition mechanism, not a performance guarantee** — their value is in readability and maintainability; materialization behavior varies by database and query.
- **Correlated subqueries execute once per outer row** — this is correct behavior but can be expensive on large datasets; validate with execution plans.
- **Choose the composition strategy based on the relational intent** — JOINs for row relationships, subqueries for inline filtering and scalar values, CTEs for multi-stage structured logic.
