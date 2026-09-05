# Query-Logic and Transformation

## Overview

This section covers the SQL tools that transform raw query results into meaningful, structured output. While the previous section established how to retrieve and filter data, this section focuses on how to apply conditional logic, convert values between types, and combine independent result sets using set operations.

These capabilities are essential for backend engineers building reporting pipelines, data transformation layers, classification systems, and multi-source aggregations. They shift SQL from a simple data-retrieval tool into a data-processing layer.

---

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Query-Logic and Transformation](./README.md) | SQL Foundations | CASE WHEN, type casting, and set operators |
| 02 | [01- CASE WHEN](./01-%20CASE%20WHEN/README.md) | SQL Foundations | Conditional expressions, classifications, and derived values |
| 03 | [02- Type Casting and Conversion](./02-%20Type%20Casting%20and%20Conversion/README.md) | SQL Foundations | CAST, CONVERT, FORMAT, and safe type transformation |
| 04 | [03- Set Operators](./03-%20Set%20Operators/README.md) | SQL Foundations | UNION, UNION ALL, INTERSECT, and EXCEPT |

---

## What This Section Covers

### 01- CASE WHEN

`CASE WHEN` is SQL's primary conditional expression. It allows queries to derive values, classify rows, and implement data-oriented transformations without moving that logic into application code. This section covers simple and searched CASE expressions, branch evaluation rules, NULL handling inside CASE, conditional aggregation, conditional sorting, and conditional data modification. It also covers the decision between CASE and COALESCE, CASE versus application logic, and common CASE mistakes.

### 02- Type Casting and Conversion

SQL values often need to be converted between types — for comparisons, formatting, storage, or API contracts. This section covers the standard `CAST` function, SQL Server's `CONVERT` and `FORMAT`, implicit versus explicit conversion behavior, numeric conversion, string conversion, date and time conversion, conversion errors, conversion rules, and the performance implications of type conversion on indexed columns.

### 03- Set Operators

Set operators combine or compare the result sets of multiple independent `SELECT` statements. Unlike JOINs, which relate rows based on conditions, set operators work on entire result sets. This section covers `UNION` (deduplicated), `UNION ALL` (all rows), `INTERSECT` (rows in both results), and `EXCEPT` (rows in the first but not the second), along with their column compatibility requirements, deduplication behavior, ordering rules, and practical backend use cases.

---

## Key Takeaways

- **Conditional logic belongs in SQL when it operates on data** — `CASE WHEN` keeps data-oriented classifications close to the data source and avoids redundant round-trips.
- **Explicit type conversion is safer than implicit** — implicit conversions can silently change query plans, break index usage, and produce unexpected results across database versions.
- **Set operators work on populations, not row relationships** — use them when combining independent result sets; use JOINs when relating rows from the same or different tables.
- **`UNION ALL` is almost always preferable to `UNION` when duplicates are not a concern** — deduplication has a measurable cost on large result sets.
- **Type mismatches should be addressed at the schema or application boundary** — repeated in-query conversions signal a design problem rather than a query problem.
