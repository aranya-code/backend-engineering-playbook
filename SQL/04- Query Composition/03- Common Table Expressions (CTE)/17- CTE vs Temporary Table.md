# 17- CTE vs Temporary Table

## Overview

Common Table Expressions (CTEs) and temporary tables both provide ways to work with intermediate query results, but they operate at fundamentally different levels.

A **CTE** is a named query expression scoped to a single SQL statement. A **temporary table** is a database object created for temporary storage, typically scoped to a session or transaction depending on the database and configuration.

The distinction matters in production because temporary tables can provide:

- Reuse across multiple SQL statements.
- Explicit indexes on intermediate data.
- Statistics that can influence later query planning.
- Persistence for the lifetime of a session or transaction.
- Separation between expensive preparation and subsequent processing.

CTEs are generally preferable when intermediate data is needed only as part of one statement. Temporary tables become useful when intermediate data must survive across multiple statements or requires database-object capabilities such as indexes.

## Core Difference

```text
CTE

SQL statement
    │
    ├── CTE
    │     │
    │     └── Final query
    │
    └── Statement ends
          │
          └── CTE is gone


Temporary table

Session / transaction
    │
    ├── CREATE TEMP TABLE
    │
    ├── INSERT / SELECT
    │
    ├── CREATE INDEX
    │
    ├── Query 1
    │
    ├── Query 2
    │
    └── DROP / scope ends
```

A CTE is therefore primarily a **query-composition mechanism**, while a temporary table is a **temporary relational object**.

## CTE

A CTE is introduced with `WITH`:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM recent_orders
GROUP BY customer_id;
```

The CTE exists only for this statement.

### Why CTEs Exist

CTEs make complex SQL easier to compose by allowing intermediate query stages to be named.

They are especially useful for:

- Multi-stage transformations.
- Aggregation pipelines.
- Window-function workflows.
- Recursive queries.
- Data-modifying statements supported by the database.
- Improving readability of complex SQL.

### Advantages

- Clear logical structure.
- No explicit temporary-table lifecycle.
- Naturally contained within one statement.
- Can express recursive relationships.
- Can compose multiple transformations.
- Can sometimes be optimized or inlined by the database optimizer.

### Limitations

- Scope is limited to one statement.
- Cannot generally be indexed independently like a temporary table.
- Reuse across separate statements requires repeating the query or using another database object.
- Performance depends on optimizer behavior and query shape.
- Large intermediate results can still consume significant memory, CPU, or temporary storage.

## Temporary Tables

A temporary table is explicitly created by the database:

```sql
CREATE TEMPORARY TABLE recent_orders AS
SELECT
    customer_id,
    total_amount
FROM orders
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days';
```

It can then be queried by subsequent statements:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM recent_orders
GROUP BY customer_id;
```

The table remains available according to the database's temporary-table lifecycle rules.

In PostgreSQL, for example:

```sql
CREATE TEMP TABLE recent_orders (
    customer_id bigint NOT NULL,
    total_amount numeric(12, 2) NOT NULL
) ON COMMIT DROP;
```

`ON COMMIT DROP` causes the temporary table to be dropped when the current transaction commits.

Other databases have different temporary-table semantics, so production code should follow the target DBMS documentation.

## Why Temporary Tables Exist

Temporary tables are useful when an intermediate dataset needs to behave like a real relational object for more than one statement.

They are particularly valuable when you need:

- Multiple queries against the same intermediate result.
- Indexes on the intermediate dataset.
- Explicit lifecycle control.
- Staging data for a complex database operation.
- Statistics or query-planning benefits from materialized intermediate data.
- A procedural multi-step workflow inside a database transaction.

## Advantages

- Can be reused across multiple SQL statements.
- Can have indexes.
- Can have constraints depending on the database.
- Can be explicitly populated, modified, and queried.
- Can separate expensive preparation from subsequent operations.
- Can be useful for very large intermediate datasets when repeated processing would otherwise be expensive.

## Limitations

- Requires explicit object creation and lifecycle management.
- Consumes database resources.
- Can introduce temporary I/O.
- May require additional transaction or session management.
- Temporary objects can complicate connection-pool behavior.
- Database-specific semantics vary.
- Creating indexes and loading data introduces additional work.

## Direct Comparison

| Concern | CTE | Temporary Table |
|---|---|---|
| Lifetime | One SQL statement | Session/transaction/database-specific |
| Creation | `WITH` | `CREATE TEMP TABLE` |
| Reuse across statements | No | Yes |
| Explicit indexes | No independent index | Yes |
| Explicit lifecycle | No | Yes |
| Recursive queries | Yes | Not inherently |
| Multiple processing stages | Within one statement | Across multiple statements |
| Statistics | Optimizer-dependent | DBMS-dependent; may support statistics |
| Data modification | Supported in some DBMSs | Yes |
| Setup overhead | Low | Higher |
| Operational complexity | Low | Higher |
| Best use | Query composition | Multi-step intermediate data |

## Scope and Lifetime

Scope is one of the most important differences.

### CTE Scope

A CTE is visible only to the statement in which it is declared:

```sql
WITH active_customers AS (
    SELECT
        id
    FROM customers
    WHERE status = 'active'
)
SELECT *
FROM active_customers;
```

This works.

The following does not:

```sql
WITH active_customers AS (
    SELECT id
    FROM customers
    WHERE status = 'active'
)
SELECT *
FROM active_customers;

SELECT *
FROM active_customers;
```

The second statement cannot see the CTE.

### Temporary Table Scope

A temporary table can be used by subsequent statements while it remains within its configured scope:

```sql
CREATE TEMP TABLE active_customers AS
SELECT
    id
FROM customers
WHERE status = 'active';

SELECT *
FROM active_customers;

SELECT COUNT(*)
FROM active_customers;
```

This is one of the strongest reasons to choose a temporary table over a CTE.

## Materialization

A critical distinction is that **a CTE and a temporary table should not be treated as equivalent materialization mechanisms**.

A temporary table explicitly stores a relation as a database object.

A CTE describes a query expression. Depending on the database and optimizer, its result may be:

- Inlined into the surrounding query.
- Materialized.
- Evaluated using an execution strategy chosen by the optimizer.

For PostgreSQL, explicit controls are available:

```sql
WITH expensive_result AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM expensive_result;
```

Or:

```sql
WITH expensive_result AS NOT MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM expensive_result;
```

These controls are database-specific and should not be treated as portable SQL.

A temporary table, by contrast, creates an actual temporary relation:

```sql
CREATE TEMP TABLE expensive_result AS
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

The intermediate relation now exists independently of the original `SELECT`.

## Indexing Intermediate Results

This is a major advantage of temporary tables.

Suppose a large intermediate dataset will repeatedly be joined using `customer_id`:

```sql
CREATE TEMP TABLE customer_revenue AS
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

You can create an index:

```sql
CREATE INDEX idx_customer_revenue_customer_id
ON customer_revenue (customer_id);
```

Then reuse the indexed relation:

```sql
SELECT
    c.id,
    c.email,
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

A CTE does not provide the same ability to independently create an index on its result.

This does not mean a temporary table will automatically be faster. The cost of:

1. Creating the table.
2. Writing the data.
3. Building the index.
4. Reading it again.

must be justified by subsequent reuse or query-planning benefits.

## Multi-Statement Workflows

Temporary tables are often appropriate when a workflow contains multiple database operations.

For example:

```sql
BEGIN;

CREATE TEMP TABLE target_customers AS
SELECT
    id
FROM customers
WHERE status = 'active'
  AND last_order_at < CURRENT_TIMESTAMP - INTERVAL '180 days';

CREATE INDEX idx_target_customers_id
ON target_customers (id);

UPDATE customers AS c
SET
    status = 'dormant',
    updated_at = CURRENT_TIMESTAMP
FROM target_customers AS tc
WHERE c.id = tc.id;

INSERT INTO customer_status_history (
    customer_id,
    previous_status,
    new_status
)
SELECT
    tc.id,
    'active',
    'dormant'
FROM target_customers AS tc;

COMMIT;
```

The intermediate customer set is needed by multiple statements.

A CTE could compose parts of an operation into a single statement, but once the workflow naturally spans multiple statements, a temporary table may be a better fit.

## Single-Statement Transformation

For a single logical query, a CTE is usually simpler.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id
WHERE cr.revenue >= 10000;
```

Creating a temporary table for this operation would add unnecessary lifecycle and I/O overhead unless there is another reason to persist the intermediate result.

## Reuse Across Multiple Statements

A temporary table becomes more compelling when the same expensive intermediate dataset is consumed repeatedly.

```sql
CREATE TEMP TABLE eligible_orders AS
SELECT
    id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'completed'
  AND created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days';

CREATE INDEX idx_eligible_orders_customer
ON eligible_orders (customer_id);

SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM eligible_orders
GROUP BY customer_id;

SELECT
    customer_id,
    COUNT(*) AS order_count
FROM eligible_orders
GROUP BY customer_id;

SELECT
    customer_id,
    MAX(total_amount) AS largest_order
FROM eligible_orders
GROUP BY customer_id;
```

The expensive filtering step happens once.

With independent CTEs in separate statements, the filtering query would have to be repeated.

## Temporary Tables and Statistics

Temporary tables can provide another production-level advantage: the database may maintain statistics for them according to DBMS-specific rules.

In PostgreSQL, for example, after loading a substantial temporary table, you may explicitly analyze it:

```sql
ANALYZE eligible_orders;
```

This can help the optimizer estimate:

- Row counts.
- Data distribution.
- Selectivity.
- Join cardinality.

That can matter when the temporary dataset is large and subsequent queries have complex joins.

The exact behavior varies by database engine.

## Performance Decision

A useful mental model is:

```text
Is the intermediate result needed only
inside one SQL statement?
        │
        ├── Yes
        │    │
        │    ├── Simple/local logic → Subquery
        │    │
        │    └── Multi-stage/reusable within
        │        statement → CTE
        │
        └── No
             │
             ▼
        Is it needed across multiple statements?
             │
             ├── Yes → Consider temporary table
             │
             └── No → Re-evaluate query design
```

For performance-sensitive systems, validate both approaches against realistic data.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

for query execution analysis, and inspect temporary-table operations separately.

## Temporary Tables vs CTEs in PostgreSQL

PostgreSQL provides strong support for both approaches.

### CTE

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM recent_orders
GROUP BY customer_id;
```

### Temporary Table

```sql
CREATE TEMP TABLE recent_orders AS
SELECT
    customer_id,
    total_amount
FROM orders
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days';

SELECT
    customer_id,
    SUM(total_amount)
FROM recent_orders
GROUP BY customer_id;
```

The first is concise and statement-local.

The second introduces an independently addressable temporary relation.

## Connection Pooling Considerations

Temporary tables require special care in application servers using connection pools.

Consider a Django or FastAPI application:

```text
Application
    │
    ▼
Connection Pool
    │
    ├── Connection A
    │      └── TEMP TABLE exists
    │
    ├── Connection B
    │      └── TEMP TABLE does not exist
    │
    └── Connection C
           └── TEMP TABLE does not exist
```

A temporary table is associated with a database session/connection in many systems.

If application code creates a temporary table on one connection and later attempts to use it through another pooled connection, the table may not exist there.

This can produce intermittent production failures.

If temporary tables are used from application code:

- Keep dependent operations on the same database connection.
- Use explicit transaction boundaries where appropriate.
- Understand the pool's connection lifecycle.
- Ensure cleanup semantics are correct.
- Test under concurrent requests.

In Django, operations requiring a shared database connection should be designed carefully around transaction management and connection reuse.

## Transaction Semantics

Temporary-table lifetime and transaction behavior are database-specific.

For PostgreSQL:

```sql
CREATE TEMP TABLE session_data (
    id bigint
) ON COMMIT DROP;
```

The table is dropped when the transaction commits.

Other options include:

```sql
ON COMMIT DELETE ROWS
```

and:

```sql
ON COMMIT PRESERVE ROWS
```

The default behavior is database-specific, so production code should explicitly choose the desired behavior when lifecycle semantics matter.

CTEs do not require this kind of lifecycle management because their scope is inherently tied to the statement.

## Concurrency Considerations

Temporary tables generally belong to an individual database session, which prevents different sessions from directly sharing the same temporary relation.

However, temporary tables still consume resources:

- Memory.
- Disk or temporary storage.
- CPU.
- Metadata/object-management resources.

High request concurrency combined with large temporary tables can therefore increase database pressure.

Avoid creating large temporary tables per API request unless the workload has been tested at expected concurrency.

For high-throughput APIs, a single well-optimized query using a CTE may be preferable to repeatedly creating and indexing temporary tables.

## CTEs and Temporary Tables in ETL

Temporary tables become particularly useful in data-processing workflows.

Example:

```text
Raw orders
    │
    ▼
Temporary staging table
    │
    ├── validation
    ├── deduplication
    ├── indexing
    └── enrichment
    │
    ▼
Final transformation
    │
    ▼
Production tables
```

A batch process might:

```sql
CREATE TEMP TABLE staged_orders AS
SELECT
    order_id,
    customer_id,
    total_amount
FROM raw_orders
WHERE import_batch_id = $1;

CREATE INDEX idx_staged_orders_customer
ON staged_orders (customer_id);

-- Validation
SELECT customer_id, COUNT(*)
FROM staged_orders
GROUP BY customer_id
HAVING COUNT(*) > 1000;

-- Transformation
INSERT INTO order_summary (
    customer_id,
    order_count,
    total_revenue
)
SELECT
    customer_id,
    COUNT(*),
    SUM(total_amount)
FROM staged_orders
GROUP BY customer_id;
```

The temporary table acts as a controlled staging area.

For large-scale production ETL, dedicated staging tables, warehouse tables, or external processing systems may be more appropriate than per-session temporary tables.

## CTEs vs Temporary Tables for Backend APIs

For a normal REST or gRPC request, prefer CTEs when the entire operation is naturally one database statement.

Example:

```text
HTTP / gRPC request
        │
        ▼
Application service
        │
        ▼
Parameterized SQL
        │
        ├── CTE
        ├── CTE
        └── Final query
        │
        ▼
Database
        │
        ▼
Response
```

Temporary tables introduce additional database operations:

```text
HTTP / gRPC request
        │
        ▼
Application service
        │
        ├── CREATE TEMP TABLE
        ├── INSERT/SELECT
        ├── CREATE INDEX
        ├── Query 1
        ├── Query 2
        └── Cleanup / transaction end
        │
        ▼
Response
```

For latency-sensitive APIs, the additional setup cost should have a clear justification.

## When to Prefer a CTE

Use a CTE when:

- The intermediate data is needed by one statement.
- The query has multiple logical stages.
- Recursive traversal is required.
- Readability improves substantially.
- Multiple parts of the same statement consume the intermediate relation.
- You want to keep the database operation atomic as one statement.
- Temporary-table lifecycle would add unnecessary complexity.

Example:

```sql
WITH monthly_customer_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
)
SELECT
    customer_id,
    month,
    revenue,
    LAG(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
    ) AS previous_month_revenue
FROM monthly_customer_revenue;
```

## When to Prefer a Temporary Table

Consider a temporary table when:

- Multiple SQL statements need the same intermediate data.
- The intermediate result is expensive to compute and can be reused.
- An index on the intermediate data materially improves later queries.
- You need to inspect or validate intermediate data.
- You need explicit control over intermediate data lifecycle.
- The workflow naturally consists of multiple database stages.
- The optimizer benefits from statistics on the intermediate result.

Example:

```sql
CREATE TEMP TABLE candidate_customers AS
SELECT
    id
FROM customers
WHERE status = 'active'
  AND last_order_at < CURRENT_TIMESTAMP - INTERVAL '180 days';

CREATE INDEX idx_candidate_customers_id
ON candidate_customers (id);

UPDATE customers AS c
SET status = 'dormant'
FROM candidate_customers AS cc
WHERE c.id = cc.id;

INSERT INTO customer_status_history (
    customer_id,
    previous_status,
    new_status
)
SELECT
    cc.id,
    'active',
    'dormant'
FROM candidate_customers AS cc;
```

## Production Pitfalls

### Creating Temporary Tables for Every Simple Query

This adds unnecessary:

- Table creation overhead.
- Catalog/object-management work.
- Temporary storage.
- Cleanup complexity.

Use a CTE or subquery when the operation is naturally a single statement.

### Assuming Temporary Tables Are Free

Temporary does not mean free.

Large temporary tables can consume substantial database resources, especially under high concurrency.

### Ignoring Connection Affinity

A temporary table may exist only on the connection that created it.

Application code using connection pools must ensure all dependent operations use the same connection/session.

### Forgetting Index Creation Costs

Indexes can improve repeated queries against a temporary table, but creating them also costs CPU, memory, and I/O.

Only add indexes that materially improve the subsequent workload.

### Treating a Temporary Table as a Cache

Temporary tables are not a replacement for:

- Redis.
- Application caches.
- Materialized views.
- Persistent staging tables.
- Data warehouses.

They are database-local temporary relations.

### Using Temporary Tables Across API Requests

A temporary table should not be used as a mechanism for sharing application state across independent requests.

Use an appropriate persistent or distributed storage mechanism instead.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Using temp tables for one simple query | Adds unnecessary overhead | Prefer a CTE or subquery |
| Assuming CTEs persist | CTE scope is statement-local | Use a temp table for multi-statement reuse |
| Assuming CTEs always materialize | Logical structure is confused with execution | Inspect optimizer behavior |
| Creating temp tables without indexes | Later joins may become expensive | Add indexes when plan evidence supports them |
| Creating indexes on every temp table | Index construction itself costs resources | Index only useful access paths |
| Ignoring transaction scope | Table may disappear earlier than expected | Define explicit lifecycle semantics |
| Using temp tables with connection pools carelessly | Different connection may not see the table | Maintain connection/session affinity |
| Loading huge datasets into temp tables per request | Can overload the database | Consider set-based SQL or batch processing |
| Assuming temp tables are portable | Syntax and lifecycle vary | Verify target DBMS behavior |
| Treating temp tables as application caches | Wrong lifecycle and ownership model | Use Redis or persistent storage |

## Interview Traps

### "Is a temporary table just a materialized CTE?"

**No.**

They can both represent intermediate data, but they have different semantics.

A CTE is part of one SQL statement. A temporary table is an actual temporary relation with its own lifecycle and potentially its own indexes and statistics.

### "Which is faster?"

There is no universal answer.

A CTE can be faster because it avoids creating and writing a temporary relation. A temporary table can be faster when an expensive intermediate result is reused repeatedly, indexed, or benefits from independent statistics.

The correct answer is workload- and optimizer-dependent.

### "Can I index a CTE?"

Not as an independent relation in the same way you can index a temporary table.

You can index the underlying permanent tables, and some database-specific execution strategies may create internal temporary structures, but those are not equivalent to creating an explicit index on a CTE.

### "When would you intentionally materialize intermediate data?"

Typical reasons include:

- Expensive computation reused multiple times.
- Need for indexes on intermediate data.
- Need for statistics.
- Breaking a very complex execution problem into stages.
- Multi-statement workflows.

### "Should temporary tables be used in web requests?"

They can be, but they should not be the default.

For latency-sensitive APIs, evaluate connection management, concurrency, temporary I/O, lifecycle, and setup overhead before adopting them.

## Production Decision Matrix

| Requirement | CTE | Temporary Table |
|---|---:|---:|
| One SQL statement | Excellent | Usually unnecessary |
| Multi-stage single query | Excellent | Usually unnecessary |
| Recursive traversal | Excellent | Not inherently recursive |
| Reuse across statements | No | Excellent |
| Add intermediate indexes | No | Yes |
| Explicit intermediate lifecycle | Limited | Excellent |
| Large reusable intermediate result | Sometimes | Often worth evaluating |
| Connection-pool simplicity | Better | More complex |
| Simple REST API query | Usually preferred | Usually avoid |
| ETL/batch workflow | Sometimes | Often useful |
| Need to inspect intermediate data | Limited | Excellent |
| Need statistics on intermediate relation | Limited/optimizer-dependent | Often useful |
| Lowest query-composition overhead | Excellent | Lower only when reuse justifies setup |

## Practical Rule

Use the simplest mechanism that matches the lifecycle of the intermediate data:

```text
Intermediate data needed only within one statement
                    │
                    ▼
                  CTE
                    │
                    ▼
Intermediate data needed across multiple statements
                    │
                    ▼
           Temporary table
                    │
                    ▼
Intermediate data needed across sessions/requests
                    │
                    ▼
Persistent table / materialized view / cache
```

This distinction prevents a common design mistake: using a temporary table merely because the query feels complex, or using a CTE when the intermediate result actually needs a longer lifecycle.

## Key Takeaways

- **A CTE is statement-scoped query composition; a temporary table is a temporary database relation with a longer, database-defined lifecycle.**
- **Prefer CTEs for single-statement transformations and use temporary tables when intermediate data must be reused across multiple statements.**
- **Temporary tables can be indexed and may benefit from independent statistics, making them valuable for expensive, reusable intermediate datasets.**
- **Application code must account for temporary-table connection and transaction semantics, especially when using Django, FastAPI, or other connection-pooled systems.**
- **Do not assume either approach is faster; validate the total cost of computation, materialization, indexing, I/O, reuse, and concurrency with realistic workloads.**