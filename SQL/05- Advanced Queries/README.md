# Advanced Queries

## Overview

This section covers SQL features that go beyond fundamental querying into analytical and pattern-oriented techniques. The focus is on capabilities that allow backend engineers to compute metrics, rankings, running totals, period-over-period comparisons, and row-context values directly in SQL — without requiring multiple round-trips or post-processing in application code.

These are not exotic features. Window functions, in particular, appear in production analytical queries, reporting pipelines, dashboards, and data-intensive backend workloads regularly.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Advanced Queries](./README.md) | SQL Foundations | Window functions, ranking, value functions, and decision guides |
| 02 | [01- Window Functions](./01-%20Window%20Functions/README.md) | SQL Foundations | Calculations across related rows without collapsing the result set |

---

## What This Section Covers

### 01- Window Functions

Window functions extend SQL by allowing aggregate and analytical calculations to be performed over a defined set of related rows — the **window** — while preserving every row in the result set. Unlike `GROUP BY`, window functions do not collapse rows. Each row retains its own values and also receives the result of the calculation across its window.

This section covers window function fundamentals (OVER, PARTITION BY, ORDER BY, frame clauses), aggregate window functions (running totals, moving averages, group-level metrics), ranking functions (ROW_NUMBER, RANK, DENSE_RANK, NTILE), value functions (LAG, LEAD, FIRST_VALUE, LAST_VALUE, NTH_VALUE), and decision guides for choosing window functions over GROUP BY, subqueries, or CTEs.

---

## Key Takeaways

- **Window functions preserve the row set** — each output row still represents its original data, plus the result of a calculation over a defined window of related rows.
- **PARTITION BY divides rows into independent windows** — each partition is processed separately, similar to GROUP BY but without collapsing the result.
- **Frame boundaries control which rows the function sees** — misunderstanding ROWS vs RANGE and frame defaults is a common source of incorrect running totals and moving averages.
- **Window functions execute after WHERE, GROUP BY, and HAVING** — they operate on the result set produced by the rest of the query, not on raw table rows.
- **Choose window functions when you need row-level output with group-level context** — use GROUP BY when you need one row per group, subqueries when you need existence or scalar lookups, and window functions when you need both the row and an analytical value across related rows.
