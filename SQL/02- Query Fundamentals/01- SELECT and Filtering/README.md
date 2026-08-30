# README

## Overview

This section covers the core mechanics of retrieving and filtering relational data with `SELECT`. These queries form the foundation for nearly every backend workload: REST and gRPC APIs, administrative interfaces, reporting, background jobs, and data-access layers.

The material progresses from basic projection and row filtering to the reasoning required for production SQL: predictable result sets, correct `NULL` semantics, safe parameterization, query performance, and choosing the right filtering strategy.

The documents in this section build on each other:



## Navigation

- [01- SELECT Fundamentals](./01-%20SELECT%20Fundamentals.md) — Retrieving and projecting columns
- [02- Selecting Columns and Expressions](./02-%20Selecting%20Columns%20and%20Expressions.md) — Computed values and expressions in projections
- [03- Aliases](./03-%20Aliases.md) — Naming columns and expressions
- [04- DISTINCT](./04-%20DISTINCT.md) — Removing duplicate result rows
- [05- WHERE Clause](./05-%20WHERE%20Clause.md) — Row-level filtering
- [06- Comparison Operators](./06-%20Comparison%20Operators.md) — Equality, inequality, ordering, and comparisons
- [07- Logical Operators](./07-%20Logical%20Operators.md) — Combining predicates with AND, OR, and NOT
- [08- Operator Precedence](./08-%20Operator%20Precedence.md) — Correct evaluation of compound predicates
- [09- IN and NOT IN](./09-%20IN%20and%20NOT%20IN.md) — Matching against a set of values
- [10- BETWEEN](./10-%20BETWEEN.md) — Inclusive range predicates
- [11- LIKE and Pattern Matching](./11-%20LIKE%20and%20Pattern%20Matching.md) — Prefix, suffix, and wildcard searches
- [12- NULL Filtering](./12-%20NULL%20Filtering.md) — SQL three-valued logic and null-safe filtering
- [13- Filtering Rules and Best Practices](./13-%20Filtering%20Rules%20and%20Best%20Practices.md) — Correctness and production-oriented filtering
- [14- WHERE vs HAVING](./14-%20WHERE%20vs%20HAVING.md) — Row-level versus group-level filtering
- [15- When to Use Which Filter](./15-%20When%20to%20Use%20Which%20Filter.md) — Choosing the appropriate predicate
- [16- Common Filtering Mistakes](./16-%20Common%20Filtering%20Mistakes.md) — Debugging and avoiding filtering failures

## Core SQL Pattern

A typical filtered query follows this shape:

```sql
SELECT
    id,
    email,
    created_at
FROM users
WHERE status = 'active'
  AND created_at >= $1
ORDER BY created_at DESC, id DESC
LIMIT $2;
```

The important distinction is between:

- **Projection** — which columns or expressions are returned.
- **Filtering** — which rows qualify.
- **Ordering** — how qualifying rows are arranged.
- **Pagination** — how many rows are returned and how subsequent pages are identified.

Filtering is performed logically before ordering and limiting the final result:

```text
Table
  │
  ▼
FROM / JOIN
  │
  ▼
WHERE predicates
  │
  ▼
GROUP BY / HAVING
  │
  ▼
SELECT projection
  │
  ▼
ORDER BY
  │
  ▼
LIMIT / OFFSET
  │
  ▼
Result
```

The database optimizer is free to physically execute operations in a different order when the result remains semantically equivalent. SQL's logical processing order is therefore useful for reasoning about correctness, not as a literal description of every execution-plan step.

## Recommended Learning Progression

### Projection

Start with retrieving exactly the data required by the application:

```sql
SELECT
    id,
    email,
    created_at
FROM users;
```

Avoid defaulting to:

```sql
SELECT *
FROM users;
```

Explicit projections make API contracts clearer, reduce transferred data, and avoid accidentally coupling application code to future schema changes.

### Row Filtering

Use `WHERE` to restrict rows:

```sql
SELECT
    id,
    email
FROM users
WHERE status = 'active';
```

Predicates should represent business requirements as directly as possible.

### Predicate Composition

Combine independent conditions deliberately:

```sql
SELECT
    id,
    email
FROM users
WHERE status = 'active'
  AND tenant_id = $1;
```

When combining `AND` and `OR`, use parentheses to make intent explicit:

```sql
WHERE tenant_id = $1
  AND (
      status = 'active'
      OR status = 'pending'
  );
```

### Set and Range Filtering

Use `IN` when matching a finite set:

```sql
WHERE status IN ('active', 'pending');
```

Use range predicates when filtering ordered values:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

For timestamps, half-open intervals are generally safer than inclusive upper boundaries.

### Pattern Matching

Use `LIKE` when the requirement is genuinely pattern-based:

```sql
WHERE email LIKE 'admin%';
```

Be careful with leading wildcards:

```sql
WHERE email LIKE '%example.com';
```

Large-scale search requirements may require database-specific indexes or a dedicated search system rather than repeatedly scanning a large table.

### NULL Semantics

`NULL` represents the absence of a value and requires dedicated predicates:

```sql
WHERE deleted_at IS NULL;
```

Do not use:

```sql
WHERE deleted_at = NULL;
```

Understanding SQL's three-valued logic is essential for reliable filtering.

## Production Query Pattern

A production API query should normally combine filtering with parameterization, deterministic ordering, and an explicit result boundary:

```sql
SELECT
    id,
    customer_id,
    status,
    total_amount,
    created_at
FROM orders
WHERE tenant_id = $1
  AND status = $2
  AND created_at >= $3
  AND created_at < $4
ORDER BY created_at DESC, id DESC
LIMIT $5;
```

The application supplies values separately from the SQL statement.

In Python, the database driver or ORM should handle parameter binding:

```python
query = """
    SELECT
        id,
        customer_id,
        status,
        total_amount,
        created_at
    FROM orders
    WHERE tenant_id = %s
      AND status = %s
      AND created_at >= %s
      AND created_at < %s
    ORDER BY created_at DESC, id DESC
    LIMIT %s
"""

cursor.execute(
    query,
    (tenant_id, status, start_time, end_time, page_size),
)
```

Never construct SQL by interpolating untrusted request values into the statement.

## Backend Engineering Context

Filtering appears throughout common backend architectures.

```text
Client
  │
  │ HTTP / gRPC
  ▼
API Service
  │
  │ authenticated request context
  ▼
Repository / ORM
  │
  │ parameterized SQL
  ▼
PostgreSQL
  │
  │ filtered rows
  ▼
Repository
  │
  ▼
API Service
  │
  ▼
Client
```

A filter should not be treated as merely a database concern. The complete request path includes:

- API input validation.
- Authentication.
- Authorization and tenant isolation.
- Query construction.
- Parameter binding.
- Database execution.
- Result serialization.
- Pagination.
- Observability.

For example, a request such as:

```http
GET /orders?status=completed
```

may become:

```sql
SELECT
    id,
    status,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC, id DESC
LIMIT $3;
```

The trusted `tenant_id` should come from authenticated application context rather than from a client-controlled filter.

## ORM Considerations

Frameworks such as Django provide abstractions for many SQL filtering operations.

For example:

```python
orders = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .order_by("-created_at", "-id")
)
```

ORM abstractions improve maintainability, but they do not remove the need to understand SQL.

Senior backend engineers should still understand:

- The SQL generated by the ORM.
- Join cardinality.
- Index usage.
- `NULL` semantics.
- Query plans.
- N+1 query behavior.
- Pagination behavior.
- Transaction boundaries.

For important queries, inspect the generated SQL and execution plan rather than assuming the ORM produced an efficient query.

## Filtering and Indexes

Filtering is often closely coupled to index design.

Suppose the application frequently executes:

```sql
SELECT
    id,
    total_amount,
    created_at
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT $3;
```

An appropriate index may significantly improve the query, but the correct design depends on:

- Cardinality.
- Data distribution.
- Query frequency.
- Write volume.
- Table size.
- Existing indexes.
- PostgreSQL planner estimates.
- Whether the index can also support ordering.

Do not create an index for every column appearing in `WHERE`.

Indexes consume storage and add write and maintenance overhead. Validate important workloads with execution plans and realistic data.

## Filtering and Pagination

Filtering should generally occur before pagination:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC, id DESC
LIMIT $3;
```

For large datasets, keyset pagination can avoid the growing cost of deep offsets:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE tenant_id = $1
  AND status = $2
  AND (created_at, id) < ($3, $4)
ORDER BY created_at DESC, id DESC
LIMIT $5;
```

The ordering must be deterministic. A unique tie-breaker such as `id` prevents ambiguous ordering when multiple rows share the same timestamp.

## Security Considerations

Filtering and authorization must remain separate concerns.

This is insufficient for multi-tenant data:

```sql
SELECT
    id,
    total_amount
FROM orders
WHERE customer_id = $1;
```

if `$1` is simply supplied by the caller.

A tenant-aware query should enforce the security boundary:

```sql
SELECT
    id,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND customer_id = $2;
```

Additional controls may include:

- Application-level authorization.
- Repository-level tenant scoping.
- PostgreSQL Row-Level Security where appropriate.
- Parameterized queries.
- Allowlisted dynamic sort/filter identifiers.
- Audit logging for sensitive data access.

A user-controlled `WHERE` condition must never be treated as proof that the user is authorized to see the matching rows.

## Performance and Observability

For production queries that are slow or unexpectedly expensive, inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    total_amount
FROM orders
WHERE tenant_id = 42
  AND status = 'completed';
```

Look for:

- Sequential scans on unexpectedly large relations.
- Large row-estimation errors.
- Expensive joins.
- Excessive rows removed by filters.
- Sort operations.
- High buffer reads.
- Poor selectivity.
- Unexpected casts or expressions.
- Excessive execution time.

Optimization should follow measurement. A theoretically "index-friendly" predicate is not automatically faster than every alternative.

## Common Pitfalls

The most important filtering failures to recognize are:

| Problem | Safer practice |
|---|---|
| Comparing with `NULL` using `=` | Use `IS NULL` |
| Assuming `<>` includes `NULL` | Handle `NULL` explicitly |
| Mixing `AND` and `OR` casually | Use parentheses |
| Using `NOT IN` with nullable subqueries | Consider `NOT EXISTS` |
| Filtering an outer-joined table in `WHERE` unintentionally | Understand `ON` vs `WHERE` |
| Applying functions to indexed timestamp columns | Prefer range predicates |
| Using inclusive timestamp endpoints | Prefer `[start, end)` |
| Fetching all rows and filtering in Python | Push filterable predicates to SQL |
| Using `DISTINCT` to hide join errors | Fix join cardinality |
| Trusting client filters for authorization | Enforce server-side access boundaries |
| Interpolating request values into SQL | Use parameter binding |
| Assuming every filter needs an index | Validate with execution plans |
| Paginating before filtering | Filter first, then paginate |
| Using unstable ordering with pagination | Add deterministic ordering |

## How to Approach Any Filtering Requirement

When translating an application requirement into SQL, work through these questions:

1. **What rows should qualify?**  
   Define the business predicate precisely.

2. **Are any values nullable?**  
   Determine whether `NULL` should match, not match, or represent a separate state.

3. **Is this row-level or group-level filtering?**  
   Use `WHERE` for rows and `HAVING` for aggregate groups.

4. **Is the predicate a comparison, set membership, range, or pattern?**  
   Choose the operator that directly represents the requirement.

5. **Are multiple predicates combined?**  
   Parenthesize mixed `AND` / `OR` logic.

6. **Are joins involved?**  
   Check whether predicate placement changes outer-join behavior.

7. **Are values user-controlled?**  
   Parameterize values and validate dynamic identifiers.

8. **Does the query need pagination?**  
   Apply filtering before pagination and use deterministic ordering.

9. **Will the query run at production scale?**  
   Inspect indexes and execution plans using representative data.

10. **Does filtering enforce or merely refine authorization?**  
    Authorization boundaries must come from trusted application context.


---

## Key Takeaways

- Treat `SELECT` and filtering as the foundation of reliable data access: project only required data and express row predicates precisely.
- Understand `NULL`, operator precedence, joins, ranges, and membership predicates before optimizing query performance.
- Parameterize values and enforce authorization independently of client-controlled filters.
- Design filtering together with ordering, pagination, and indexes for production workloads rather than optimizing each concern in isolation.
- Use execution plans and realistic data to validate performance; never assume a filter or index is efficient solely from its syntax.