# Query Fundamentals

## Overview

This section covers the core SQL querying skills required for backend engineering. These are not introductory topics — they are the foundational techniques that appear in nearly every production query: selecting and filtering rows, controlling sort order and result size, combining conditions with operators, aggregating data into metrics, transforming strings and dates, and handling the absence of data correctly.

Mastery of these fundamentals is what separates engineers who can write syntactically valid SQL from engineers who can write correct, performant, maintainable queries on real production data.

---

## Navigation

- [01- SELECT and Filtering](./01-%20SELECT%20and%20Filtering/README.md) — Projecting columns, filtering rows, and writing correct WHERE clauses
- [02- Sorting Pagination and Result Control](./02-%20Sorting%20Pagination%20and%20Result%20Control/README.md) — ORDER BY, LIMIT, OFFSET, and pagination strategy
- [03- SQL Operators](./03-%20SQL%20Operators/README.md) — Comparison, logical, membership, and range operators
- [04- Aggregate Functions](./04-%20Aggregate%20Functions/README.md) — COUNT, SUM, AVG, MIN, MAX, GROUP BY, and HAVING
- [05- String Functions](./05-%20String%20Functions/README.md) — Concatenation, trimming, pattern matching, and string transformations
- [06- Date and Time](./06-%20Date%20and%20Time/README.md) — Temporal types, date arithmetic, filtering, and timezone-safe queries
- [07- NULL Handling](./07-%20NULL%20Handling/README.md) — Three-valued logic, NULL predicates, COALESCE, NULLIF, and NULL-safe design

---

## What This Section Covers

### 01- SELECT and Filtering

The `SELECT` statement is the primary tool for retrieving data. This section covers how to project columns and computed expressions, alias output, remove duplicates, and filter rows with `WHERE` clauses. It also covers the full range of filtering constructs — comparison operators, logical operators, `IN`, `BETWEEN`, `LIKE`, and NULL filtering — along with the rules for writing correct, index-friendly predicates.

### 02- Sorting, Pagination and Result Control

Ordering and pagination are database access-pattern decisions with index, performance, and API design implications. This section covers `ORDER BY`, sort direction, multi-column ordering, expression-based sorting, `LIMIT`/`TOP`, `OFFSET`, and the three major pagination strategies — offset, keyset, and cursor — including their tradeoffs and when to choose each.

### 03- SQL Operators

SQL operators determine how predicates compare values, combine conditions, and test relationships. This section covers comparison operators, logical operators (`AND`, `OR`, `NOT`), membership operators (`IN`, `NOT IN`, `EXISTS`), range operators (`BETWEEN`, `LIKE`), arithmetic operators, and string operators — with emphasis on NULL behavior, operator precedence, and the index and correctness implications of each.

### 04- Aggregate Functions

Aggregate functions compute metrics over sets of rows. This section covers `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING`, and the interaction between aggregation and NULL semantics. It includes the rules governing query grain, join cardinality before aggregation, the difference between `WHERE` and `HAVING`, and common aggregation mistakes in production workloads.

### 05- String Functions

String processing in SQL involves more than simple concatenation. This section covers the full range of string operations: `CONCAT`, `LENGTH`, `UPPER`, `LOWER`, `TRIM`, `SUBSTRING`, `REPLACE`, `LIKE`/`ILIKE`, string splitting, string aggregation, and NULL behavior in string expressions. It emphasizes correct function selection, performance implications, and normalization as a production design concern.

### 06- Date and Time

Temporal data requires careful handling across storage, filtering, arithmetic, and API design. This section covers SQL temporal types, current date/time functions, date extraction, date arithmetic, date truncation, date formatting, filtering with temporal predicates, time zone semantics, range boundary design, and how date functions interact with indexes.

### 07- NULL Handling

`NULL` represents the absence of a value and behaves differently from every other SQL value. This section covers three-valued logic (`TRUE`, `FALSE`, `UNKNOWN`), NULL predicates, NULL behavior in comparisons, logical operators, aggregates, and JOINs, and the NULL-handling functions `COALESCE`, `NULLIF`, `ISNULL`, and `IFNULL`. It also covers production-oriented NULL design rules and common NULL mistakes.

---

## Key Takeaways

- **Query fundamentals are not beginner topics** — NULL semantics, aggregation grain, pagination strategies, and operator behavior are constant sources of production bugs.
- **Filtering correctness depends on understanding three-valued logic** — NULLs in predicates, JOINs, and aggregates require explicit handling rather than relying on assumed behavior.
- **Pagination is a database access-pattern decision** — offset, keyset, and cursor pagination have different performance, consistency, and API contract implications.
- **String and date operations applied to indexed columns change query plans** — always validate index usage when filtering or grouping on transformed values.
- **Aggregate queries require explicit reasoning about grain** — knowing what one output row represents is the prerequisite for writing a correct GROUP BY.
