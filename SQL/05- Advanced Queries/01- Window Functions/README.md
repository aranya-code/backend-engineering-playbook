# Window Functions

## Overview

Window functions are one of the most important SQL features for analytical and backend data workloads. They allow calculations to be performed across a set of related rows — the **window** — while preserving every row in the result set intact.

Unlike `GROUP BY`, which collapses rows into summary records, window functions return one output row per input row. Each row keeps all of its own values and also receives the result of a calculation over a defined window of related rows. This makes them essential for running totals, rankings, period-over-period comparisons, and row-context lookups — all without sub-queries or application-level post-processing.

> **The core model:** `function() OVER (PARTITION BY ... ORDER BY ... frame_clause)`

---

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Fundamentals](./01-%20Fundamentals/README.md) | OVER clause, PARTITION BY, ORDER BY, frame boundaries, and execution rules |
| 02 | [02- Aggregate Functions](./02-%20Aggregate%20Functions/README.md) | Running totals, cumulative aggregates, and group-level metrics without collapsing rows |
| 03 | [03- Ranking Functions](./03-%20Ranking%20Functions/README.md) | ROW_NUMBER, RANK, DENSE_RANK, and NTILE |
| 04 | [04- Value Functions](./04-%20Value%20Functions/README.md) | LAG, LEAD, FIRST_VALUE, LAST_VALUE, and NTH_VALUE |
| 05 | [05- Decision Guides](./05-%20Decision%20Guides/README.md) | When to use window functions versus GROUP BY, subqueries, and CTEs |

---

## What This Section Covers

### 01- Fundamentals

The foundation of window functions is the `OVER` clause, which defines the window — the set of rows each function operates against. This section covers `PARTITION BY` (dividing rows into independent groups), `ORDER BY` within the window (establishing row ordering for ranking and frame calculations), frame clauses (`ROWS` vs `RANGE`, `UNBOUNDED PRECEDING`, `CURRENT ROW`, `FOLLOWING`), and the execution order of window functions relative to `WHERE`, `GROUP BY`, `HAVING`, and `SELECT`.

### 02- Aggregate Functions

Window aggregate functions extend `SUM()`, `AVG()`, `COUNT()`, `MIN()`, and `MAX()` to operate over a window rather than a collapsed group. This section covers running totals, cumulative sums, moving averages, group-level metrics alongside row-level data, percentage-of-total calculations, and the interaction between frame boundaries and aggregate results.

### 03- Ranking Functions

Ranking functions assign an ordered position to rows within a window partition. This section covers `ROW_NUMBER()` (unique sequential position), `RANK()` (same rank for ties, gaps after ties), `DENSE_RANK()` (same rank for ties, no gaps), and `NTILE()` (dividing rows into N equal buckets). It includes top-N queries, deduplication patterns, latest-record-per-group queries, and ranking across independent partitions.

### 04- Value Functions

Value window functions retrieve values from other rows in the same window — the previous row, the next row, the first row, the last row, or an arbitrary Nth row. This section covers `LAG()` (value from a preceding row), `LEAD()` (value from a following row), `FIRST_VALUE()`, `LAST_VALUE()`, and `NTH_VALUE()`. It includes period-over-period comparisons, sequential difference calculations, and session boundary detection.

### 05- Decision Guides

Knowing when to use a window function — and when GROUP BY, a subquery, a CTE, or a JOIN is more appropriate — is the engineering skill that makes window functions useful in practice. This section provides practical decision rules for choosing between SQL techniques based on the relational requirement, the performance characteristics, and the maintainability of the resulting query.

---

## Key Takeaways

- **Window functions preserve the result set** — every input row produces exactly one output row, unlike GROUP BY which collapses rows.
- **PARTITION BY is not GROUP BY** — it divides the window into independent sub-sets for the function, but all rows are returned.
- **Frame boundaries define what "the window" actually means** — the default frame behavior varies by whether ORDER BY is present, and incorrect defaults cause incorrect running totals.
- **Window functions execute after filtering and grouping** — they see the result set produced by WHERE, JOIN, GROUP BY, and HAVING, not the raw table rows.
- **Use ranking functions to select one row per group** — ROW_NUMBER() with a CTE or subquery is the standard pattern for deduplication and latest-record queries.
- **Use value functions for row-to-row comparisons** — LAG and LEAD eliminate the need for self-joins when comparing a row to the row before or after it.
