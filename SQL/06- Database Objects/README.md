# Database Objects

## Overview

This section covers database-side objects that extend SQL beyond raw queries and data manipulation. Where previous sections focused on how to retrieve and modify data, this section focuses on how to encapsulate and expose data through the database itself — using views as stable query abstractions and stored procedures as database-resident logic.

These objects are tools for managing complexity, enforcing consistency, and controlling access. They also introduce coupling, deployment considerations, and portability tradeoffs that backend engineers must understand before choosing to use them.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Database Objects](./README.md) | Schema and Data Management | Views and stored procedures |
| 02 | [01- Views](./01-%20Views/README.md) | Schema and Data Management | Reusable query abstractions, updatable views, security, and maintainability |
| 03 | [02- Stored Procedures](./02-%20Stored%20Procedures/README.md) | Schema and Data Management | Database-side procedural logic, transactions, parameters, and architectural tradeoffs |

---

## What This Section Covers

### 01- Views

A view is a named query stored in the database that can be referenced like a table. Views provide stable, reusable projections of relational data — hiding joins, filters, and computed fields behind a consistent interface. This section covers how views work, the types of views (simple, updatable, materialized), creating and dropping views, using views with JOINs, aggregations, and CTEs, view security use cases (column-level access control, row-level filtering), view maintenance and dependency management, and the decision between views and alternatives such as CTEs, temporary tables, and stored procedures.

### 02- Stored Procedures

A stored procedure is a named, parameterized, database-resident program containing procedural logic. It can encapsulate multi-step operations, conditional logic, loops, error handling, and transaction control — all executing close to the data. This section covers stored procedure structure, parameters (input, output, inout), variables and control flow, conditional logic, error handling, transactions inside procedures, stored procedures versus application logic, stored procedures versus functions and CTEs, database portability considerations, and common stored procedure mistakes.

---

## Key Takeaways

- **Views are query abstractions, not data stores** — except for materialized views, a standard view executes its underlying query every time it is referenced.
- **Use views to enforce stable interfaces** — when the underlying tables change, views can absorb that complexity and protect dependent queries from breaking.
- **Updatable views have strict requirements** — not every view can be used for INSERT, UPDATE, or DELETE; violating these requirements silently or with errors depending on the database.
- **Stored procedures couple logic to the database** — they are powerful for data-intensive operations but introduce a second deployment surface, a second testing environment, and reduced portability.
- **Choose stored procedures deliberately** — they are appropriate for atomic multi-step workflows, data-intensive batch operations, and database-enforced access control; they are not appropriate as a substitute for well-designed application services.
