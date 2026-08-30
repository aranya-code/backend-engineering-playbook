# 23- Practical CTE Patterns

## Overview

Common Table Expressions (CTEs) provide a named, statement-scoped way to compose SQL from logical query stages. Their primary value is **query structure**: a complex relational operation can be decomposed into meaningful intermediate relations without introducing persistent database objects.

A practical CTE usually represents a meaningful transformation such as:

- Filtering a working dataset.
- Aggregating transactional data.
- Joining multiple derived datasets.
- Ranking or deduplicating rows.
- Building multi-stage analytical queries.
- Preparing data for `INSERT`, `UPDATE`, or `DELETE`.
- Traversing hierarchical data with recursive CTEs.

A CTE should not be treated as automatically faster than a subquery or as a replacement for views and temporary tables. The database optimizer determines the physical execution strategy.

A useful mental model is:

```text
Base tables
    │
    ▼
CTE: filter / normalize
    │
    ▼
CTE: aggregate
    │
    ▼
CTE: rank / enrich
    │
    ▼
Final query
```

The strongest CTE designs make each stage understandable while preserving a query that the database can execute efficiently.

## Basic CTE Pattern

The basic structure is:

```sql
WITH cte_name AS (
    SELECT ...
)
SELECT ...
FROM cte_name;
```

Multiple CTEs can be chained:

```sql
WITH first_stage AS (
    SELECT ...
),
second_stage AS (
    SELECT ...
    FROM first_stage
)
SELECT ...
FROM second_stage;
```

Later CTEs can reference earlier CTEs, but a CTE should generally depend only on stages that logically precede it.

## Pattern: Filter a Working Dataset

Use a CTE when a complex query repeatedly needs a well-defined filtered relation.

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM recent_orders
GROUP BY customer_id;
```

This is useful when the filtered dataset represents a meaningful concept such as `recent_orders`.

### Why It Works Well

The CTE creates a semantic boundary:

```text
orders
  │
  ├── status = completed
  └── created_at >= last 30 days
          │
          ▼
    recent_orders
          │
          ▼
      aggregation
```

The important point is not that the CTE necessarily materializes the rows. It is a logical query expression whose physical treatment depends on the database optimizer.

### Production Considerations

Avoid:

```sql
WITH recent_orders AS (
    SELECT *
    FROM orders
)
```

when no meaningful transformation occurs. Selecting unnecessary columns can increase memory, I/O, and downstream processing.

Prefer:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE ...
)
```

Project only columns needed by later stages.

## Pattern: Multi-Stage Aggregation

CTEs are particularly useful when an aggregate becomes an input to another relational operation.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
qualified_customers AS (
    SELECT
        customer_id,
        revenue
    FROM customer_revenue
    WHERE revenue >= 10000
)
SELECT
    c.id,
    c.email,
    qc.revenue
FROM customers AS c
JOIN qualified_customers AS qc
    ON qc.customer_id = c.id
ORDER BY qc.revenue DESC;
```

Each stage has a clear responsibility:

| Stage | Responsibility |
|---|---|
| `customer_revenue` | Calculate customer-level revenue |
| `qualified_customers` | Apply the revenue threshold |
| Final query | Enrich with customer attributes |

This structure is often easier to review than a single deeply nested query.

## Pattern: Deduplicate Rows

A common backend requirement is to select one canonical row from multiple candidates.

Window functions combined with CTEs make this explicit.

```sql
WITH ranked_events AS (
    SELECT
        id,
        user_id,
        event_type,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, event_type
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM user_events
)
SELECT
    id,
    user_id,
    event_type,
    created_at
FROM ranked_events
WHERE row_number = 1;
```

The CTE separates:

1. Ranking the candidates.
2. Filtering to the winner.

The secondary `id DESC` ordering provides deterministic tie-breaking when timestamps are equal.

### Production Use Cases

This pattern is useful for:

- Latest user state.
- Latest payment attempt.
- Most recent configuration.
- Canonical event selection.
- Deduplicating imported records.

Always define a deterministic ordering when selecting one row from a group.

## Pattern: Top N Per Group

A CTE combined with `ROW_NUMBER()` is a standard pattern for retrieving the top N records within each group.

```sql
WITH ranked_orders AS (
    SELECT
        customer_id,
        id AS order_id,
        total_amount,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rank
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    order_id,
    total_amount,
    created_at
FROM ranked_orders
WHERE rank <= 3;
```

This differs from a global `LIMIT`.

```sql
LIMIT 3
```

returns three rows for the entire result, whereas:

```sql
ROW_NUMBER() OVER (PARTITION BY customer_id ...)
```

allows three rows **per customer**.

## Pattern: Compare Current and Previous Values

CTEs provide a clean boundary around window-function calculations.

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE_TRUNC('month', created_at)
),
revenue_with_previous AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (
            ORDER BY month
        ) AS previous_revenue
    FROM monthly_revenue
)
SELECT
    month,
    revenue,
    previous_revenue,
    revenue - previous_revenue AS revenue_change
FROM revenue_with_previous
ORDER BY month;
```

This pattern is useful for:

- Month-over-month metrics.
- State transitions.
- Change detection.
- Operational reporting.
- Time-series analysis.

## Pattern: Aggregate Before Joining

A frequent production problem is accidentally multiplying rows through joins.

Suppose a customer has many orders and many support tickets. Joining both tables directly can create a Cartesian multiplication at the customer level.

Instead, aggregate each one-to-many relationship independently.

```sql
WITH order_summary AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS order_revenue
    FROM orders
    GROUP BY customer_id
),
ticket_summary AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    COALESCE(os.order_count, 0) AS order_count,
    COALESCE(os.order_revenue, 0) AS order_revenue,
    COALESCE(ts.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_summary AS os
    ON os.customer_id = c.id
LEFT JOIN ticket_summary AS ts
    ON ts.customer_id = c.id;
```

This pattern protects the intended cardinality:

```text
Customer
   │
   ├── Orders ──► aggregate ──► one row/customer
   │
   └── Tickets ─► aggregate ──► one row/customer
                              │
                              ▼
                         final join
```

It is one of the most useful CTE patterns in reporting queries.

## Pattern: Conditional Aggregation

A CTE can establish the reporting population before calculating multiple metrics.

```sql
WITH completed_orders AS (
    SELECT
        customer_id,
        total_amount,
        payment_method
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    COUNT(*) FILTER (
        WHERE payment_method = 'card'
    ) AS card_orders,
    COUNT(*) FILTER (
        WHERE payment_method = 'bank_transfer'
    ) AS bank_transfer_orders
FROM completed_orders
GROUP BY customer_id;
```

This is preferable to repeatedly applying the same filtering predicate across separate aggregates.

## Pattern: Identify Missing Relationships

CTEs can build the expected population and compare it against existing records.

For example, identify active customers with no completed order in the last 90 days:

```sql
WITH active_customers AS (
    SELECT
        id,
        email
    FROM customers
    WHERE status = 'active'
),
recent_buyers AS (
    SELECT DISTINCT
        customer_id
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_DATE - INTERVAL '90 days'
)
SELECT
    ac.id,
    ac.email
FROM active_customers AS ac
LEFT JOIN recent_buyers AS rb
    ON rb.customer_id = ac.id
WHERE rb.customer_id IS NULL;
```

This is useful for:

- Customer engagement reports.
- Missing configuration detection.
- Data-quality checks.
- Operational audits.

For existence checks, `NOT EXISTS` can sometimes express the intent more directly:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.status = 'active'
  AND NOT EXISTS (
      SELECT 1
      FROM orders AS o
      WHERE o.customer_id = c.id
        AND o.status = 'completed'
        AND o.created_at >= CURRENT_DATE - INTERVAL '90 days'
  );
```

Do not use a CTE merely because it can express a query that is clearer as `EXISTS` or `NOT EXISTS`.

## Pattern: Build an Explicit Reporting Pipeline

For complex reports, use CTEs as logical stages.

```sql
WITH eligible_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_DATE - INTERVAL '12 months'
),
customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue,
        COUNT(*) AS order_count
    FROM eligible_orders
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        revenue,
        order_count,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM customer_revenue
)
SELECT
    c.id,
    c.email,
    rc.revenue,
    rc.order_count,
    rc.revenue_rank
FROM ranked_customers AS rc
JOIN customers AS c
    ON c.id = rc.customer_id
WHERE rc.revenue_rank <= 100
ORDER BY rc.revenue_rank;
```

Each stage represents a business-relevant transformation:

```text
eligible_orders
      │
      ▼
customer_revenue
      │
      ▼
ranked_customers
      │
      ▼
customer enrichment
      │
      ▼
top 100 customers
```

This is an effective structure for analytical SQL that would otherwise become difficult to maintain.

## Pattern: Use CTEs for Data Modification

CTEs are not limited to `SELECT`.

They can prepare rows for `INSERT`, `UPDATE`, or `DELETE`.

### Insert From a CTE

```sql
WITH eligible_customers AS (
    SELECT
        id AS customer_id
    FROM customers
    WHERE status = 'active'
)
INSERT INTO customer_segments (
    customer_id,
    segment
)
SELECT
    customer_id,
    'active'
FROM eligible_customers
ON CONFLICT (customer_id)
DO UPDATE SET
    segment = EXCLUDED.segment;
```

This is useful when the target data is derived from a multi-stage query.

### Update From a CTE

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
UPDATE customers AS c
SET lifetime_revenue = ct.revenue
FROM customer_totals AS ct
WHERE ct.customer_id = c.id;
```

### Delete Using a CTE

```sql
WITH duplicate_events AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, event_type, occurred_at
            ORDER BY id
        ) AS row_number
    FROM user_events
)
DELETE FROM user_events AS e
USING duplicate_events AS d
WHERE e.id = d.id
  AND d.row_number > 1;
```

Modification queries require additional care around:

- Locking.
- Transaction boundaries.
- Concurrency.
- Affected-row counts.
- Retry behavior.
- Referential integrity.
- Audit requirements.

## Pattern: Data Modification With `RETURNING`

In PostgreSQL, a data-modifying CTE can be combined with `RETURNING` to feed results into another operation.

For example:

```sql
WITH deleted_sessions AS (
    DELETE FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
    RETURNING user_id
)
INSERT INTO session_cleanup_audit (
    user_id,
    cleaned_at
)
SELECT
    user_id,
    CURRENT_TIMESTAMP
FROM deleted_sessions;
```

This can keep related database operations within one SQL statement and transaction context.

Use this carefully for operational jobs. A large deletion can generate substantial WAL, locking, replication traffic, and transaction pressure.

## Pattern: Recursive Hierarchies

Recursive CTEs are appropriate for hierarchical data such as:

- Organization structures.
- Category trees.
- Folder hierarchies.
- Dependency graphs.
- Bill-of-materials structures.

A basic hierarchy traversal:

```sql
WITH RECURSIVE subordinates AS (
    SELECT
        id,
        manager_id,
        name,
        0 AS depth
    FROM employees
    WHERE id = $1

    UNION ALL

    SELECT
        e.id,
        e.manager_id,
        e.name,
        s.depth + 1
    FROM employees AS e
    JOIN subordinates AS s
        ON e.manager_id = s.id
)
SELECT
    id,
    manager_id,
    name,
    depth
FROM subordinates
ORDER BY depth, id;
```

The recursive query has two logical components:

- **Anchor member** — establishes the starting rows.
- **Recursive member** — discovers the next level.

Conceptually:

```text
Anchor
  │
  ▼
Level 0
  │
  ▼
Recursive step
  │
  ▼
Level 1
  │
  ▼
Recursive step
  │
  ▼
Level 2
  │
  ▼
...
```

Recursive CTEs require explicit protection against unbounded traversal, cycles, and unexpectedly large result sets.

## Pattern: Generate Time Ranges

Some databases support recursive CTEs for sequence generation, but built-in set-generating functions are often preferable when available.

For PostgreSQL, for example:

```sql
SELECT
    day::date
FROM generate_series(
    CURRENT_DATE - INTERVAL '29 days',
    CURRENT_DATE,
    INTERVAL '1 day'
) AS day;
```

A recursive CTE is possible, but it is not automatically the best tool for every sequence-generation problem.

The broader principle is:

> Prefer a database-native primitive when it directly expresses the operation.

## Pattern: Gap Detection

A CTE can make a multi-stage data-quality query easier to understand.

For example, detect missing daily activity:

```sql
WITH days AS (
    SELECT
        day::date AS activity_date
    FROM generate_series(
        CURRENT_DATE - INTERVAL '29 days',
        CURRENT_DATE,
        INTERVAL '1 day'
    ) AS day
),
activity AS (
    SELECT DISTINCT
        occurred_at::date AS activity_date
    FROM user_events
    WHERE occurred_at >= CURRENT_DATE - INTERVAL '29 days'
)
SELECT
    d.activity_date
FROM days AS d
LEFT JOIN activity AS a
    ON a.activity_date = d.activity_date
WHERE a.activity_date IS NULL
ORDER BY d.activity_date;
```

This separates:

1. Expected dates.
2. Observed dates.
3. Missing dates.

The same structure applies to many data-quality problems where an expected relation must be compared with an observed relation.

## Pattern: Reuse an Intermediate Relation Within One Statement

A CTE is particularly useful when the same logical result is needed more than once in the statement.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    cr.revenue,
    CASE
        WHEN cr.revenue >= 50000 THEN 'enterprise'
        WHEN cr.revenue >= 10000 THEN 'high_value'
        ELSE 'standard'
    END AS segment
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id
WHERE cr.revenue > 0;
```

The same intermediate result can support multiple expressions without duplicating the aggregation logic.

However, do not assume that every database physically computes the CTE once. Optimizer behavior is database- and query-dependent.

## Pattern: Explicitly Control PostgreSQL CTE Materialization

PostgreSQL supports `MATERIALIZED` and `NOT MATERIALIZED` for CTEs in supported versions.

### Prefer Inlining When Appropriate

```sql
WITH recent_orders AS NOT MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM recent_orders
GROUP BY customer_id;
```

`NOT MATERIALIZED` allows PostgreSQL to treat the CTE more like an inline subquery when applicable.

### Force Materialization When Appropriate

```sql
WITH expensive_result AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT ...
FROM expensive_result;
```

Materialization can be useful when an expensive intermediate result is reused and computing it independently would be more expensive.

Do not use either option as a default optimization technique. Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH ...
SELECT ...;
```

## Pattern: Build a Single Logical Boundary for API Queries

Backend services often need a query that combines filtering, authorization, aggregation, and pagination.

For example:

```sql
WITH accessible_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE organization_id = $1
      AND status = 'completed'
),
customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM accessible_orders
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    ct.revenue
FROM customer_totals AS ct
JOIN customers AS c
    ON c.id = ct.customer_id
ORDER BY ct.revenue DESC, c.id
LIMIT $2
OFFSET $3;
```

The authorization boundary should be applied as early as practical.

Do not retrieve unrestricted data into a CTE and attempt to enforce tenant isolation later in the query.

For multi-tenant systems, predicates such as:

```sql
organization_id = $1
```

should be parameterized and consistently enforced.

## Pattern: CTEs in Django and FastAPI Applications

ORMs can generate sophisticated SQL, but some reporting and analytical queries are easier to express directly in SQL.

A production application can expose a carefully reviewed query through a repository or data-access layer:

```python
from django.db import connection


def get_customer_revenue(organization_id: int, limit: int) -> list[dict]:
    sql = """
        WITH customer_revenue AS (
            SELECT
                customer_id,
                SUM(total_amount) AS revenue
            FROM orders
            WHERE organization_id = %s
              AND status = 'completed'
            GROUP BY customer_id
        )
        SELECT
            customer_id,
            revenue
        FROM customer_revenue
        ORDER BY revenue DESC, customer_id
        LIMIT %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [organization_id, limit])
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

The same principle applies to FastAPI with the database access library used by the service.

The important production concerns are:

- Bind parameters instead of string interpolation.
- Keep authorization predicates inside the query where appropriate.
- Define stable ordering for pagination.
- Monitor execution time.
- Test against production-scale data.
- Keep SQL close to the data-access boundary rather than scattering raw SQL across request handlers.

## Pattern: Stable Pagination

CTEs do not solve pagination by themselves. If a query produces a ranked or aggregated relation, use deterministic ordering.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
ORDER BY revenue DESC, customer_id ASC
LIMIT $1
OFFSET $2;
```

For high-volume APIs, offset pagination may become expensive at large offsets. Keyset pagination can be more appropriate.

For example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE (revenue, customer_id) < ($1, $2)
ORDER BY revenue DESC, customer_id DESC
LIMIT $3;
```

The cursor values must correspond to the ordering semantics.

## CTE Composition Guidelines

Good CTEs generally follow these rules:

| Guideline | Recommendation |
|---|---|
| Naming | Describe the relation's business or technical meaning |
| Projection | Select only required columns |
| Dependencies | Keep stages logically ordered |
| Granularity | Make the row grain clear |
| Filtering | Push selective predicates down where appropriate |
| Aggregation | Aggregate before joins when it prevents row multiplication |
| Ordering | Do not rely on CTE ordering unless the final query requires ordering |
| Recursion | Define termination and cycle behavior |
| Performance | Validate execution plans |
| Scope | Use CTEs for statement-local composition |

The concept of **row grain** is especially important.

If a CTE produces:

```text
one row per customer
```

document that assumption through naming and query structure. A later join that accidentally changes the grain can invalidate every aggregate.

## Common Mistakes

### Using `SELECT *`

```sql
WITH recent_orders AS (
    SELECT *
    FROM orders
)
```

This can pull unnecessary columns through multiple query stages.

Prefer explicit projections.

### Assuming CTEs Are Temporary Tables

A CTE is not a general-purpose temporary storage mechanism.

If data must be reused across several statements or independently indexed, consider a temporary table or staging table.

### Assuming CTEs Are Always Materialized

A CTE is a logical query expression. Do not assume its rows are always physically stored.

Inspect the execution plan for the target database.

### Creating One CTE Per SQL Fragment

This:

```sql
WITH a AS (...),
b AS (...),
c AS (...),
d AS (...)
SELECT ...
```

is not automatically better than a simpler query.

Each CTE should represent a useful logical boundary.

### Ignoring Row Multiplication

Aggregating after joining multiple one-to-many relationships can produce incorrect totals.

Aggregate independently first when necessary.

### Forgetting Deterministic Ordering

Queries using `ROW_NUMBER()`, pagination, or "latest row" logic should use deterministic ordering.

For example:

```sql
ORDER BY created_at DESC, id DESC
```

is safer than relying only on `created_at`.

### Building Unbounded Recursive Queries

Recursive CTEs can traverse far more rows than expected.

Use appropriate predicates, depth limits, cycle handling, and indexes on traversal columns.

### Using CTEs Without Checking the Plan

Readable SQL can still be operationally expensive.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH ...
SELECT ...;
```

Review:

- Actual execution time.
- Rows estimated versus actual.
- Sequential scans.
- Index scans.
- Join strategy.
- Sort operations.
- Hash operations.
- Memory usage.
- Temporary reads and writes.

## Performance Considerations

CTE performance depends on the database engine, version, optimizer, data distribution, and query shape.

Do not use these rules:

> "CTEs are always faster."

or:

> "CTEs are always slower."

Neither is generally correct.

A production evaluation should compare the complete query plans.

### Push Selective Filters Early

When logically safe, reduce the working dataset early:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_DATE - INTERVAL '30 days'
)
...
```

Reducing rows early can lower downstream join, aggregation, and sort costs.

The optimizer may perform predicate pushdown itself, so manually restructuring SQL should still be validated against the execution plan.

### Avoid Unnecessary Sorts

Do not add:

```sql
ORDER BY ...
```

inside a CTE merely because you want the CTE "sorted."

Unless ordering is semantically required by an operation such as a window function or the final query, an intermediate ordering may be unnecessary work.

### Watch Large Intermediate Relations

Large intermediate results can consume:

- CPU.
- Memory.
- Temporary disk.
- I/O bandwidth.
- Database connection time.

A CTE that reads millions of rows and then discards most of them deserves investigation.

## Security Considerations

CTEs do not provide an authorization boundary by themselves.

For multi-tenant backend systems, tenant filtering should be explicit:

```sql
WITH accessible_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE organization_id = $1
)
SELECT
    customer_id,
    SUM(total_amount)
FROM accessible_orders
GROUP BY customer_id;
```

Use bound parameters:

```python
cursor.execute(sql, [organization_id])
```

not:

```python
cursor.execute(
    f"SELECT ... WHERE organization_id = {organization_id}"
)
```

For sensitive systems, database-level controls such as PostgreSQL Row-Level Security can provide an additional enforcement layer. Application authorization and database authorization should be designed deliberately rather than assuming a CTE itself provides isolation.

## Scalability and Reliability

For production systems, consider the workload around the query rather than just the query's syntax.

### High-Concurrency API Queries

A query that takes 200 ms may be acceptable for an occasional report but expensive when executed thousands of times per minute.

Evaluate:

- Requests per second.
- Query concurrency.
- Connection pool size.
- Database CPU.
- I/O.
- Lock contention.
- Replica capacity.
- Cache behavior.

### Reporting Workloads

Complex CTEs can be excellent for low-frequency reports.

For high-frequency analytical access, consider:

- Summary tables.
- Materialized views.
- Read replicas.
- Dedicated analytics systems.
- Precomputed aggregates.
- Caching where correctness permits.

### Transactions

When CTEs are used with data modification, understand transaction behavior.

A single SQL statement provides atomicity according to the database's transaction semantics, but application-level workflows may still require explicit transaction management.

In Django:

```python
from django.db import transaction

with transaction.atomic():
    # Execute related database operations.
    ...
```

Do not hold large transactions open while performing unrelated network calls.

## Monitoring and Operations

Track CTE-heavy queries like any other important SQL workload.

Useful PostgreSQL tooling includes:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH ...
SELECT ...;
```

and, where enabled, `pg_stat_statements` for identifying expensive or frequently executed query patterns.

Monitor:

- p95/p99 query latency.
- Total execution time.
- Calls per query.
- Rows returned.
- Buffer reads.
- Temporary file usage.
- Database CPU.
- Lock waits.
- Replication lag for write-heavy operations.

The most important query is not always the one with the highest individual latency. A moderately expensive query executed extremely frequently can dominate database capacity.

## Practical Decision Matrix

| Requirement | CTE | Subquery | Temporary Table | View | Materialized View |
|---|---:|---:|---:|---:|---:|
| Complex one-statement composition | Excellent | Good | Poor | Good | Good |
| Simple one-use transformation | Good | Excellent | Poor | Poor | Poor |
| Reuse within one statement | Excellent | Limited | Excellent | Excellent | Excellent |
| Reuse across statements | No | No | Yes | Yes | Yes |
| Recursive traversal | Excellent | Poor | Possible | Possible | Usually poor fit |
| Index intermediate data | No | No | Yes | No | Yes |
| Persist precomputed results | No | No | Session/transaction scoped | No | Yes |
| Query-specific intermediate logic | Excellent | Excellent | Good | Limited | Limited |
| Frequent expensive reads | Usually poor fit | Usually poor fit | Poor | Sometimes | Often appropriate |

## Interview Traps

### Are CTEs always materialized?

No. Physical treatment depends on the database engine and optimizer. PostgreSQL can inline eligible CTEs and also supports explicit materialization controls.

### Are CTEs always faster than subqueries?

No. Equivalent CTE and subquery formulations can produce equivalent execution plans.

### Can a CTE be referenced by multiple statements?

No. A normal CTE belongs to a single SQL statement.

### What makes a good CTE?

A good CTE represents a meaningful intermediate relation with a clear purpose, predictable row grain, and useful name.

### Why aggregate before joining?

Joining multiple one-to-many relations before aggregation can multiply rows and produce incorrect aggregates. Independent aggregation can preserve the intended cardinality.

### What are the two parts of a recursive CTE?

A recursive CTE typically has an **anchor member**, which establishes the starting rows, and a **recursive member**, which derives subsequent rows.

### Should every complex query use CTEs?

No. CTEs improve composition, but excessive CTE layering can reduce readability and may complicate optimization. Choose the simplest abstraction that accurately expresses the required relational operation.

## Key Takeaways

- **Use CTEs to create meaningful, statement-local stages for filtering, aggregation, ranking, data modification, and recursive traversal.**
- **Treat row grain, cardinality, deterministic ordering, and predicate placement as first-class concerns when composing CTEs.**
- **Do not assume CTE materialization or performance characteristics; validate the actual execution plan on the target database and workload.**
- **Use temporary tables, views, materialized views, or application-level abstractions when the required lifetime or reuse exceeds a single statement.**
- **In production, combine CTE readability with parameterized SQL, authorization boundaries, transaction discipline, monitoring, and workload-aware performance testing.**