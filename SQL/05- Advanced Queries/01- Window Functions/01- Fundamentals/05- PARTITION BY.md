# 05- PARTITION BY

## Overview

`PARTITION BY` is the windowing mechanism used to divide a query's result set into independent logical groups. A window function then evaluates each row against the rows belonging to its partition.

```sql
function(...) OVER (
    PARTITION BY expression
    ORDER BY expression
)
```

Unlike `GROUP BY`, `PARTITION BY` does **not** collapse rows. It preserves the result-set grain while giving each row access to calculations performed within its logical group.

For backend systems, this makes `PARTITION BY` useful for:

- Ranking records within a tenant, customer, or department.
- Calculating per-group totals and averages.
- Finding the latest record per entity.
- Comparing a row with previous or next rows in the same entity.
- Calculating running totals independently for each account.
- Implementing top-N-per-group queries.

The most important mental model is:

> **`PARTITION BY` determines who belongs to the same window; `ORDER BY` determines the sequence inside that window.**

## `PARTITION BY` vs `GROUP BY`

Consider an orders table:

```text
id | customer_id | amount
---+-------------+-------
1  | 101         | 100
2  | 101         | 250
3  | 102         | 400
4  | 102         | 150
```

A grouped aggregate:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_amount
FROM orders
GROUP BY customer_id;
```

returns:

```text
customer_id | total_amount
------------+-------------
101         | 350
102         | 550
```

The original four rows are reduced to two rows.

A window aggregate:

```sql
SELECT
    id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

returns:

```text
id | customer_id | amount | customer_total
---+-------------+--------+---------------
1  | 101         | 100    | 350
2  | 101         | 250    | 350
3  | 102         | 400    | 550
4  | 102         | 150    | 550
```

The difference is fundamental:

| `GROUP BY` | `PARTITION BY` |
|---|---|
| Groups rows into aggregate groups | Defines windows for window functions |
| Usually reduces row count | Preserves rows |
| Produces one result per group | Produces a result for each input row |
| Useful for aggregation | Useful for row-level analytics |
| Changes result-set grain | Preserves result-set grain |

## Mental Model

Suppose:

```sql
AVG(salary) OVER (
    PARTITION BY department_id
)
```

The database conceptually performs:

```text
Employees
    │
    ├── department_id = 10
    │       ├── employee A
    │       ├── employee B
    │       └── employee C
    │
    ├── department_id = 20
    │       ├── employee D
    │       └── employee E
    │
    └── department_id = 30
            └── employee F
```

Each department is an independent window.

For employee B, the function can evaluate the rows in department 10 without considering employees in departments 20 or 30.

The output still contains employee B as an individual row.

## Basic Syntax

The general form is:

```sql
window_function(...) OVER (
    PARTITION BY expression
)
```

Partitioning can be combined with ordering:

```sql
window_function(...) OVER (
    PARTITION BY expression
    ORDER BY expression
)
```

It can also include an explicit frame:

```sql
window_function(...) OVER (
    PARTITION BY expression
    ORDER BY expression
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

The three components have different responsibilities:

| Component | Responsibility |
|---|---|
| `PARTITION BY` | Defines independent groups |
| `ORDER BY` | Defines ordering inside each group |
| Frame | Defines which ordered rows are visible to the function |

## Single-Column Partitioning

The most common form partitions by one entity:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Every customer receives an independent total.

This is useful when an API needs both:

- The individual record.
- Context about that record's group.

For example, an order response might expose:

```json
{
  "order_id": 1001,
  "amount": 250,
  "customer_total": 4200
}
```

without requiring the application to fetch and aggregate all customer orders in Python.

## Multiple Partition Columns

`PARTITION BY` accepts multiple expressions:

```sql
SELECT
    employee_id,
    company_id,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY company_id, department_id
    ) AS department_average
FROM employees;
```

The partition key is the combination:

```text
(company_id, department_id)
```

So:

```text
company_id | department_id
------------+---------------
1           | 10
1           | 20
2           | 10
2           | 20
```

represent four independent partitions.

This pattern is particularly important in multi-tenant systems.

## `PARTITION BY` as a Tenant Boundary

In a multi-tenant application, partitioning can naturally align analytical calculations with tenant boundaries.

```sql
SELECT
    tenant_id,
    user_id,
    created_at,
    login_count,
    AVG(login_count) OVER (
        PARTITION BY tenant_id
    ) AS tenant_average_login_count
FROM user_activity;
```

Each tenant gets its own analytical population.

However, `PARTITION BY` is **not a security boundary**.

A query such as:

```sql
SELECT ...
FROM user_activity
```

can still return data from every tenant.

Tenant isolation must be enforced separately through mechanisms such as:

- Correct application-level filtering.
- PostgreSQL Row-Level Security where appropriate.
- Database roles and permissions.
- Separate databases or schemas where required by the architecture.

Use:

```sql
WHERE tenant_id = :tenant_id
```

when the request is scoped to a specific tenant.

Then partition within the filtered data when needed.

## `PARTITION BY` Without `ORDER BY`

Many aggregate window functions only require partitioning:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders;
```

Every order receives its customer's order count.

Similarly:

```sql
AVG(amount) OVER (
    PARTITION BY customer_id
)
```

calculates the average across the customer's partition.

No sequence is required because the calculation does not depend on row order.

## `PARTITION BY` With `ORDER BY`

When the calculation depends on sequence, add `ORDER BY`.

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS order_number
FROM orders;
```

For each customer, the rows are ordered independently.

Conceptually:

```text
Customer 101
    2026-01-01 → row 1
    2026-01-04 → row 2
    2026-01-10 → row 3

Customer 102
    2026-01-02 → row 1
    2026-01-08 → row 2
```

The numbering restarts at the beginning of every partition.

## Ranking Within Partitions

A major use case is ranking records within each group.

```sql
SELECT
    employee_id,
    department_id,
    salary,
    RANK() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees;
```

The rank restarts for every department.

Example:

```text
department | salary | rank
-----------+--------+-----
Engineering| 180000 | 1
Engineering| 160000 | 2
Engineering| 160000 | 2
Engineering| 120000 | 4
Sales      | 150000 | 1
Sales      | 130000 | 2
```

Common ranking functions include:

```sql
ROW_NUMBER()
RANK()
DENSE_RANK()
NTILE()
```

The choice depends on how ties should behave.

## Top-N Per Partition

One of the most valuable production patterns is selecting the top N rows from every partition.

For example:

> Return the three highest-value completed orders for each customer.

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        amount,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY amount DESC, order_id DESC
        ) AS row_number
    FROM orders
    WHERE status = 'completed'
)
SELECT
    order_id,
    customer_id,
    amount,
    created_at
FROM ranked_orders
WHERE row_number <= 3;
```

The `PARTITION BY` causes ranking to restart for each customer.

Without it:

```sql
ROW_NUMBER() OVER (
    ORDER BY amount DESC
)
```

would return only a global ranking.

## Latest Row Per Group

Another common backend requirement is:

> Return the latest record for every customer.

Use:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        created_at,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, order_id DESC
        ) AS row_number
    FROM orders
)
SELECT
    order_id,
    customer_id,
    created_at,
    amount
FROM ranked_orders
WHERE row_number = 1;
```

The deterministic secondary ordering is important.

If two orders have the same `created_at`, `order_id` determines which row wins.

This pattern is frequently used for:

- Latest user profile state.
- Latest payment status.
- Latest device registration.
- Latest configuration.
- Latest event per entity.

## Running Totals Per Partition

`PARTITION BY` can also create independent running totals.

```sql
SELECT
    transaction_id,
    account_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY created_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance_change
FROM transactions;
```

The accumulation restarts for every account.

Conceptually:

```text
Account A
    +100 → 100
    +50  → 150
    -20  → 130

Account B
    +500 → 500
    -100 → 400
```

The accounts do not influence one another.

For financial calculations, be explicit about:

- Ordering.
- Tie-breaking.
- Frame type.
- Numeric precision.
- Transaction semantics.

## Previous and Next Rows

`LAG()` and `LEAD()` are naturally combined with partitioning.

```sql
SELECT
    event_id,
    user_id,
    occurred_at,
    status,
    LAG(status) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
    ) AS previous_status
FROM user_events;
```

The previous event is calculated independently for each user.

This is useful for detecting transitions:

```text
pending → paid
paid → shipped
shipped → delivered
```

Without `PARTITION BY`, the previous row could belong to a completely different user.

## Partitioning and Window Frames

`PARTITION BY` defines the population, while a frame defines the subset used for the current row.

Consider:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
)
```

For every customer:

1. Rows are separated by `customer_id`.
2. Rows inside each customer partition are ordered.
3. The current row and two preceding rows form the frame.
4. `SUM()` operates on that frame.

The frame never crosses the partition boundary.

```text
Customer A partition
┌──────────────────────────────────────┐
│ row 1 │ row 2 │ row 3 │ row 4 │ ... │
└──────────────────────────────────────┘
                    ↑
                  frame

Customer B partition
┌───────────────────────────────┐
│ row 1 │ row 2 │ row 3 │ ...   │
└───────────────────────────────┘
```

## Partitioning and Query Filtering

`WHERE` filtering occurs before window functions at the same query level.

Consider:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE status = 'completed';
```

The partition is formed from completed orders visible to this query.

It does **not** include cancelled or pending orders that were removed by the `WHERE` clause.

This distinction is important.

If the requirement is:

> Show completed orders but calculate the customer's total across all orders

use a different query structure:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS customer_total
    FROM orders
    GROUP BY customer_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.amount,
    ct.customer_total
FROM orders AS o
JOIN customer_totals AS ct
    ON ct.customer_id = o.customer_id
WHERE o.status = 'completed';
```

The analytical population must match the business requirement.

## `PARTITION BY` and Joins

Joins can change the row population before a window function executes.

Consider:

```sql
SELECT
    o.order_id,
    o.customer_id,
    SUM(o.amount) OVER (
        PARTITION BY o.customer_id
    ) AS customer_total
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.order_id;
```

If an order has multiple items, the join produces multiple rows for that order.

The window function then sees those duplicated order rows.

The result can therefore be incorrect.

This is a common production mistake:

> **Always verify the row grain after joins before applying a window calculation.**

If the calculation is supposed to operate at order grain, aggregate the items first or calculate the window before introducing row multiplication.

## Partition Size and Data Skew

`PARTITION BY` is logical, not a guarantee of equal-sized groups.

For example:

```sql
PARTITION BY customer_id
```

may produce:

```text
Customer A → 20 rows
Customer B → 150 rows
Customer C → 2,000,000 rows
```

One extremely large partition can dominate execution time and memory requirements.

This is especially important for:

- Multi-tenant SaaS.
- Large financial accounts.
- High-volume event streams.
- Social platforms.
- Audit logs.

Do not assume a query is scalable simply because it uses partitioning.

Measure the actual data distribution.

## Performance Considerations

Window functions frequently require the database to organize rows according to the partition and ordering requirements.

For:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
)
```

the database may need to perform substantial sorting or otherwise obtain rows in a compatible order.

For production queries, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ...
FROM ...;
```

Potential optimization strategies include:

- Filter unnecessary rows before the window calculation.
- Avoid accidental row multiplication from joins.
- Use appropriate indexes where they help the complete query.
- Keep partitions bounded when possible.
- Avoid computing expensive windows for rows that will never be returned.
- Test with production-scale and skewed datasets.

An index such as:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at, order_id);
```

may help a query whose access pattern aligns with that ordering, but index usefulness is query-plan dependent.

Do not create indexes based solely on the presence of `PARTITION BY`.

## Security Considerations

`PARTITION BY` does not enforce authorization.

This query:

```sql
SELECT
    tenant_id,
    user_id,
    AVG(amount) OVER (
        PARTITION BY tenant_id
    ) AS tenant_average
FROM transactions;
```

can calculate values across every tenant visible to the query.

For a tenant-scoped API request, establish the security boundary first:

```sql
SELECT
    transaction_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY tenant_id
    ) AS tenant_average
FROM transactions
WHERE tenant_id = :tenant_id;
```

For systems using PostgreSQL Row-Level Security, ensure that the effective database policy prevents unauthorized rows from entering the query.

A window function cannot compensate for missing authorization controls.

## Backend API Example

A FastAPI or Django endpoint might need to return a customer's orders together with:

- Customer total.
- Order sequence.
- Previous order amount.

A single database query can provide all of this:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,

    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total,

    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS order_number,

    LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS previous_order_amount

FROM orders
WHERE customer_id = :customer_id
  AND status = 'completed'
ORDER BY created_at, order_id;
```

The database performs the relational analysis, while the application primarily handles:

1. Authentication and authorization.
2. Parameter binding.
3. Query execution.
4. Serialization.
5. API response handling.

Use parameterized queries or the ORM's parameter binding mechanisms. Do not construct `tenant_id`, customer IDs, or other request values through string concatenation.

## Common Mistakes

### Treating `PARTITION BY` Like `GROUP BY`

Incorrect mental model:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

does not produce one row per customer.

It produces one value per input row.

### Forgetting `PARTITION BY`

This:

```sql
ROW_NUMBER() OVER (
    ORDER BY created_at DESC
)
```

creates one global sequence.

If numbering must restart per customer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

is required.

### Using the Wrong Partition Key

The partition key should represent the actual business boundary.

For example, if ranking products within each store:

```sql
PARTITION BY store_id
```

may be correct.

Using:

```sql
PARTITION BY category_id
```

would silently produce a different analytical population.

### Missing Deterministic Ordering

Avoid:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

if multiple records can share the same timestamp.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, order_id DESC
)
```

### Ignoring Join Multiplication

A one-to-many join can duplicate rows before the window function executes.

Always verify:

```text
Expected grain → Join result grain → Window input grain
```

before trusting the calculation.

### Assuming Partitioning Improves Performance

`PARTITION BY` defines logical groups; it is not a performance optimization by itself.

A query can still require expensive sorting, large memory allocations, or disk-based processing.

## Interview Traps

### Does `PARTITION BY` Reduce Rows?

No.

It defines independent windows while preserving the input rows.

### Is `PARTITION BY` Equivalent to `GROUP BY`?

No.

`GROUP BY` changes result-set cardinality. `PARTITION BY` does not.

### Can You Use `PARTITION BY` Without `ORDER BY`?

Yes.

For example:

```sql
COUNT(*) OVER (
    PARTITION BY customer_id
)
```

does not need ordering.

### Does `PARTITION BY` Guarantee Physical Data Partitioning?

No.

It is a logical window-function concept. It does not mean the database physically partitions the table.

Physical table partitioning is a separate database storage feature.

### Can Multiple Window Functions Use Different Partitions?

Yes.

For example:

```sql
SELECT
    employee_id,
    department_id,
    region_id,
    salary,

    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_average,

    AVG(salary) OVER (
        PARTITION BY region_id
    ) AS region_average

FROM employees;
```

Each window has its own logical population and may require different execution work.

## Production Checklist

Before using `PARTITION BY` in production:

- [ ] Identify the exact business boundary represented by the partition key.
- [ ] Verify the input row grain before the window calculation.
- [ ] Check all joins for one-to-many row multiplication.
- [ ] Add deterministic tie-breakers when using `ORDER BY`.
- [ ] Define the window frame explicitly when frame semantics matter.
- [ ] Confirm that `WHERE` filtering produces the intended analytical population.
- [ ] Do not treat `PARTITION BY` as an authorization boundary.
- [ ] Check for highly skewed or extremely large partitions.
- [ ] Use `EXPLAIN (ANALYZE, BUFFERS)` for performance-sensitive queries.
- [ ] Test with production-scale data rather than a small development dataset.

## Key Takeaways

- **`PARTITION BY` divides rows into independent logical windows without reducing the result-set row count.**
- **Use `PARTITION BY` to restart rankings, calculations, running totals, and row-to-row comparisons at a business boundary such as customer, tenant, account, or department.**
- **`PARTITION BY` defines the population, `ORDER BY` defines sequence, and the frame defines the rows considered for the current row.**
- **Always validate row grain after joins and add deterministic tie-breakers when window ordering affects correctness.**
- **Partitioning is a logical SQL operation, not a performance or security boundary; large or skewed partitions and missing authorization controls remain production concerns.**