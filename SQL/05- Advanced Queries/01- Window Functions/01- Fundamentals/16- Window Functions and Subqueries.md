# 16- Window Functions and Subqueries

## Overview

Window functions and subqueries are both mechanisms for composing SQL logic, but they solve different problems.

A **subquery** creates a nested query whose result is consumed by an outer query. A **window function** calculates a value using related rows while preserving the current row.

They are frequently combined for analytical and production queries such as:

- Finding the latest record per entity.
- Returning top-N records per group.
- Comparing a row with an aggregate.
- Calculating percentages against a total.
- Detecting changes between consecutive records.
- Filtering results produced by window functions.
- Building multi-stage reporting queries.

The key distinction is:

> A subquery creates another query boundary; a window function performs an analysis over rows available to its query block without collapsing those rows.

## Subquery Mental Model

A subquery is a query nested inside another SQL statement:

```sql
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue > (
    SELECT AVG(revenue)
    FROM customer_revenue
);
```

The inner query produces a scalar value:

```text
Average customer revenue
        ↓
Outer query compares every customer
```

Subqueries can return:

| Subquery type | Result |
|---|---|
| Scalar subquery | One value |
| Single-column subquery | One or more values |
| Row subquery | One row |
| Table subquery | Multiple rows and columns |
| Correlated subquery | Evaluated with reference to the outer row |
| `EXISTS` subquery | Boolean existence test |

Subqueries are useful when the nested result represents a logical dependency of the outer query.

## Window Function Mental Model

A window function operates over a set of rows associated with the current row.

```sql
SELECT
    customer_id,
    revenue,
    AVG(revenue) OVER () AS average_revenue
FROM customer_revenue;
```

Every customer row remains in the result:

```text
customer A → revenue → overall average
customer B → revenue → overall average
customer C → revenue → overall average
```

This differs from:

```sql
SELECT AVG(revenue)
FROM customer_revenue;
```

which returns only the aggregate value.

### Subquery vs Window Function

| Requirement | Subquery | Window function |
|---|---|---|
| Produce a nested result | Excellent | Not its purpose |
| Compare each row to an aggregate | Possible | Usually cleaner |
| Preserve individual rows | Yes, depending on query | Yes |
| Rank rows | Possible but cumbersome | Excellent |
| Compare previous/next row | Cumbersome | Excellent with `LAG()`/`LEAD()` |
| Running total | Possible but often inefficient | Excellent |
| Filter based on window result | Outer query required | Outer query/CTE required |
| Existence check | Excellent with `EXISTS` | Not appropriate |
| Correlated row-specific lookup | Useful | Sometimes replaceable |

## Comparing a Row Against an Aggregate

Suppose an API needs customers whose revenue is above the average customer revenue.

### Using a Subquery

```sql
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue > (
    SELECT AVG(revenue)
    FROM customer_revenue
);
```

The scalar subquery produces one value used by the outer query.

### Using a Window Function

```sql
SELECT
    customer_id,
    revenue
FROM (
    SELECT
        customer_id,
        revenue,
        AVG(revenue) OVER () AS average_revenue
    FROM customer_revenue
) AS metrics
WHERE revenue > average_revenue;
```

The window version attaches the average to every row and then filters it in an outer query.

The subquery is often simpler when the aggregate is only needed for comparison. The window approach becomes more useful when several row-level analytical calculations are needed together.

## Subqueries for Filtering

Subqueries are particularly useful when the requirement is naturally expressed as membership or existence.

### `IN`

```sql
SELECT
    customer_id,
    email
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'completed'
);
```

This asks:

> Which customers have at least one completed order?

### `EXISTS`

For existence checks, `EXISTS` is often the more direct expression:

```sql
SELECT
    c.customer_id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'completed'
);
```

The database optimizer may transform these forms substantially, so performance should be evaluated using the actual execution plan rather than the SQL syntax alone.

## Correlated Subqueries

A correlated subquery references a value from the outer query.

For example:

```sql
SELECT
    c.customer_id,
    c.email
FROM customers AS c
WHERE (
    SELECT COUNT(*)
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
) >= 10;
```

Conceptually, the inner query depends on the current customer.

Correlated subqueries can be useful, but they deserve careful performance analysis because naïvely thinking of them as "run the inner query once per outer row" can lead to poor designs. Modern optimizers may decorrelate or transform them.

## Replacing Correlated Logic with Window Functions

Some correlated analytical logic can be expressed more naturally using aggregation followed by a window function.

Suppose the requirement is:

> Rank each customer's monthly revenue against other customers in the same month.

First establish the correct grain:

```sql
WITH monthly_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
)
SELECT
    customer_id,
    month,
    revenue,
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank
FROM monthly_revenue;
```

This is considerably clearer than constructing nested correlated aggregate queries.

## Latest Record Per Entity

A common backend requirement is:

> Return the latest status for every account.

A window function is usually the cleanest solution.

```sql
WITH ranked_statuses AS (
    SELECT
        id,
        account_id,
        status,
        changed_at,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY changed_at DESC, id DESC
        ) AS row_num
    FROM account_status_history
)
SELECT
    account_id,
    status,
    changed_at
FROM ranked_statuses
WHERE row_num = 1;
```

The CTE creates the query boundary required to filter the window result.

### Why Not a Simple Subquery?

A traditional approach might be:

```sql
SELECT
    h.account_id,
    h.status,
    h.changed_at
FROM account_status_history AS h
WHERE h.changed_at = (
    SELECT MAX(h2.changed_at)
    FROM account_status_history AS h2
    WHERE h2.account_id = h.account_id
);
```

This can return multiple rows when multiple records have the same maximum timestamp.

The `ROW_NUMBER()` approach makes tie-breaking explicit:

```sql
ORDER BY changed_at DESC, id DESC
```

That is often preferable for deterministic production behavior.

## Top-N Per Group

Window functions are especially strong when a query needs the top N rows within every group.

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(quantity * unit_price) AS revenue
    FROM order_items
    GROUP BY
        category_id,
        product_id
),
ranked_products AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS category_rank
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue,
    category_rank
FROM ranked_products
WHERE category_rank <= 3
ORDER BY category_id, category_rank;
```

A subquery can also implement this logic, but it generally requires more complicated correlation or anti-join logic.

## Window Functions Inside a Subquery

A subquery can expose a window result to an outer query.

```sql
SELECT
    customer_id,
    revenue,
    revenue_rank
FROM (
    SELECT
        customer_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM customer_revenue
) AS ranked
WHERE revenue_rank <= 10;
```

This pattern is fundamental because window-function results cannot normally be referenced in the same query block's `WHERE` clause.

A CTE expresses the same query more explicitly:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue,
    revenue_rank
FROM ranked
WHERE revenue_rank <= 10;
```

The choice between a CTE and derived table is primarily about query organization unless database-specific optimizer behavior makes the distinction relevant.

## Subquery Inside a Window Query

The relationship also works in the opposite direction: a window-function query can consume the result of a subquery.

```sql
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
) AS customer_revenue;
```

The nested query establishes the required grain:

```text
orders
  ↓
one row per customer
  ↓
window ranking
```

This is often preferable to ranking individual orders when the business requirement concerns customer-level revenue.

## Scalar Subqueries vs Window Functions

Consider calculating the total revenue beside every order.

### Scalar Subquery

```sql
SELECT
    order_id,
    amount,
    (
        SELECT SUM(amount)
        FROM orders
    ) AS total_revenue
FROM orders;
```

### Window Function

```sql
SELECT
    order_id,
    amount,
    SUM(amount) OVER () AS total_revenue
FROM orders;
```

The window expression communicates the intent more directly:

> Calculate the total across the same result set while preserving each row.

It also integrates naturally with other window calculations.

## Percentage of Total

A common reporting requirement is each category's contribution to total revenue.

```sql
WITH category_revenue AS (
    SELECT
        category_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY category_id
)
SELECT
    category_id,
    revenue,
    ROUND(
        100.0 * revenue
        / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS percentage_of_total
FROM category_revenue
ORDER BY revenue DESC;
```

The CTE establishes category-level revenue.

The window function calculates the denominator across those category rows.

This is a useful example of how query composition changes the meaning of a window function.

## Previous and Next Row Analysis

Subqueries are often unnecessarily complex for sequential comparisons.

For example, finding the previous monthly revenue:

```sql
WITH monthly_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
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
FROM monthly_revenue;
```

A correlated subquery would need to locate the preceding month for every customer, making the intent and optimization problem more complicated.

`LAG()` directly expresses the analytical relationship.

## CTE, Derived Table, and Subquery

These concepts overlap but should not be treated as interchangeable terminology.

| Technique | Primary role | Typical use |
|---|---|---|
| Scalar subquery | Produce a value | Compare against aggregate |
| `EXISTS` subquery | Test existence | Authorization/eligibility checks |
| Correlated subquery | Row-dependent lookup | Complex per-row conditions |
| Derived table | Create an inline relation | Feed another query stage |
| CTE | Name a query stage | Multi-stage analytical queries |
| Window function | Analyze related rows | Ranking, running totals, comparisons |

A CTE is syntactically a form of named query expression, while a derived table is an inline subquery in the `FROM` clause.

## Query Composition Pattern

A robust analytical query often follows this structure:

```text
Base tables
    ↓
Filter invalid/unwanted rows
    ↓
Join required entities
    ↓
Aggregate to business grain
    ↓
CTE / derived table
    ↓
Window calculation
    ↓
Outer filter
    ↓
API/report result
```

For example:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = 'completed'
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        order_count,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS position
    FROM customer_metrics
)
SELECT
    customer_id,
    order_count,
    revenue,
    position
FROM ranked_customers
WHERE position <= :limit
ORDER BY position;
```

This structure is well suited to backend reporting endpoints because every stage has a clear responsibility.

## Performance Considerations

Do not assume that a window function is always faster than a subquery, or that a subquery is always slower.

The optimizer may transform logically equivalent SQL into similar execution plans.

Performance depends on:

- Input cardinality.
- Join cardinality.
- Filter selectivity.
- Indexes.
- Sort requirements.
- Aggregation cost.
- Memory availability.
- Database engine and version.
- Statistics quality.
- Whether intermediate data spills to disk.

For PostgreSQL, inspect the actual plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_metrics AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_metrics;
```

Pay particular attention to:

- Sort operations.
- Actual versus estimated row counts.
- Sequential scans.
- Index scans.
- Hash aggregation.
- Temporary disk usage.
- Join row multiplication.
- Total execution time.

## Indexing and Window Functions

Indexes are generally most valuable for reducing the amount of data entering the analytical stage.

For example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_status_customer
ON orders (status, customer_id);
```

Whether this is beneficial depends on the query and data distribution.

A window function may still require sorting the intermediate result:

```sql
ORDER BY revenue DESC
```

especially when `revenue` is calculated dynamically.

Do not create indexes solely because a window function contains an `ORDER BY`. Measure the workload first.

## Security and Multi-Tenancy

Window functions operate over the rows available to them.

This makes tenant isolation especially important.

Unsafe analytical structure:

```text
all tenants
    ↓
aggregate
    ↓
window calculation
    ↓
tenant filter
```

The calculation may already have incorporated another tenant's data.

Prefer:

```text
tenant filter
    ↓
aggregate
    ↓
window calculation
```

For example:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    SUM(revenue) OVER () AS tenant_total
FROM customer_metrics;
```

The tenant boundary is established before the window calculation.

Always parameterize external values rather than constructing SQL through string interpolation.

## Backend Integration

For Python services such as Django or FastAPI, complex analytical SQL is often best kept as explicit SQL when ORM abstractions become difficult to reason about.

For example, a service layer can execute a parameterized query:

```python
query = """
    WITH customer_metrics AS (
        SELECT
            customer_id,
            SUM(amount) AS revenue
        FROM orders
        WHERE tenant_id = %s
          AND status = %s
        GROUP BY customer_id
    )
    SELECT
        customer_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS revenue_rank
    FROM customer_metrics
    ORDER BY revenue_rank
    LIMIT %s
"""

cursor.execute(query, [tenant_id, "completed", limit])
```

Production considerations include:

- Keep user-controlled values parameterized.
- Set appropriate statement timeouts for expensive reporting queries.
- Monitor query latency and database load.
- Avoid executing large analytical queries synchronously on latency-sensitive request paths when they can be precomputed or moved to asynchronous jobs.
- Consider read replicas for workloads where replica lag is acceptable.
- Use caching carefully when report freshness permits it.

## When to Prefer Each Approach

### Prefer Window Functions When

Use window functions when the problem involves relationships among rows in the same result set:

- Ranking.
- Running totals.
- Moving averages.
- Previous/next values.
- Percent-of-total.
- Per-group comparisons.
- Top-N per group.

### Prefer Subqueries When

Use subqueries when the nested query represents an independent logical condition:

- `EXISTS`.
- Membership with `IN`.
- Scalar aggregate comparison.
- Row-specific existence or lookup.
- Encapsulating a small derived relation.

### Prefer CTEs When

Use CTEs when query stages need names and clear boundaries:

- Multi-stage transformations.
- Preparing data for window functions.
- Filtering window results.
- Complex analytical pipelines.
- Recursive queries.
- Reusing a logically meaningful intermediate relation.

The best production query is not necessarily the shortest query. It is the query whose semantics, data grain, failure modes, and execution characteristics are easy to understand and verify.

## Common Mistakes

### Using a Subquery When a Window Function Directly Expresses the Requirement

A query that repeatedly finds previous rows or rankings through correlated subqueries can become difficult to maintain.

Prefer:

```sql
LAG(...)
LEAD(...)
ROW_NUMBER(...)
RANK(...)
DENSE_RANK(...)
```

when the problem is fundamentally window-based.

### Assuming a Window Function Can Be Filtered Immediately

Incorrect:

```sql
SELECT
    customer_id,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC
    ) AS row_num
FROM customer_revenue
WHERE row_num <= 10;
```

Correct:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS row_num
    FROM customer_revenue
)
SELECT *
FROM ranked
WHERE row_num <= 10;
```

### Ignoring Query Grain

If the input contains multiple rows per customer, then:

```sql
SUM(revenue) OVER (
    PARTITION BY customer_id
)
```

operates over those rows.

It does not magically know that the business entity is one customer.

Establish the intended grain first.

### Forgetting Tie-Breakers

Avoid nondeterministic ranking when downstream systems depend on stable ordering.

Prefer:

```sql
ROW_NUMBER() OVER (
    ORDER BY revenue DESC, customer_id
)
```

over:

```sql
ROW_NUMBER() OVER (
    ORDER BY revenue DESC
)
```

when `revenue` is not unique.

### Applying Tenant Filters Too Late

For multi-tenant reporting, tenant isolation should occur before calculations that aggregate or compare tenant data.

### Assuming Correlated Subqueries Always Execute Once Per Row

That is a useful conceptual warning but not a reliable description of modern database execution.

The optimizer can transform correlated queries.

Use `EXPLAIN` rather than reasoning from syntax alone.

### Using `IN` Carelessly With `NULL`

`NULL` introduces three-valued SQL logic.

For existence checks, `EXISTS` is often clearer:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
)
```

rather than relying on potentially subtle `IN` semantics involving `NULL`.

## Interview Traps

| Question | Correct answer |
|---|---|
| What is the primary difference between a window function and a subquery? | A window function analyzes related rows while preserving the query's rows; a subquery creates a nested query result consumed by another query. |
| Can a window-function result normally be used in the same query block's `WHERE` clause? | No. Use a CTE, derived table, or another query boundary. |
| Are window functions replacements for all subqueries? | No. `EXISTS`, scalar lookups, and other nested-query patterns remain appropriate subquery use cases. |
| Is a correlated subquery always executed once per outer row? | No. That is a conceptual model; the optimizer may transform or decorrelate it. |
| Why use a CTE before a window function? | To establish a clear query stage and, commonly, the correct data grain before analytical calculations. |
| Why is data grain important? | Window functions operate over the rows supplied to them, so incorrect grain produces incorrect analytical results. |
| Are CTEs always faster than subqueries? | No. Performance depends on the database optimizer and execution plan. |
| When is `ROW_NUMBER()` preferable to a correlated "maximum value" subquery? | When selecting one deterministic row per group, especially when explicit tie-breaking is required. |

## Key Takeaways

- **Window functions analyze related rows without collapsing them; subqueries create nested query boundaries for values, relations, or conditions.**
- **Use window functions for ranking, running calculations, row-to-row comparisons, and other problems that naturally operate across a result set.**
- **Use subqueries for independent scalar, membership, existence, or correlated conditions where nesting expresses the business rule clearly.**
- **CTEs and derived tables provide the query boundary needed to consume or filter window-function results and make analytical stages explicit.**
- **Production correctness depends on data grain, deterministic ordering, tenant filtering, parameterization, and validation of the actual execution plan.**