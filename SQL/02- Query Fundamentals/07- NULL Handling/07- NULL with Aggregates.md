# 07- NULL with Aggregates

## Overview

SQL aggregate functions operate over sets of rows, but `NULL` values are generally treated as **missing or unknown values**, not as ordinary values.

This distinction matters because aggregate functions do not all handle `NULL` in the same way:

- `COUNT(*)` counts rows, including rows whose columns are `NULL`.
- `COUNT(column)` counts only non-`NULL` values.
- `SUM(column)`, `AVG(column)`, `MIN(column)`, and `MAX(column)` ignore `NULL` values.
- An aggregate over an empty input set can return `NULL`, depending on the aggregate.
- `GROUP BY` treats `NULL` grouping values as belonging to the same group.

These semantics become important in reporting, analytics, dashboards, billing, financial calculations, API responses, and production queries where missing data has business meaning.

## How Aggregates Treat NULL

Consider:

```sql
CREATE TABLE payments (
    id BIGINT PRIMARY KEY,
    amount NUMERIC(12, 2),
    refunded_amount NUMERIC(12, 2)
);
```

Example data:

| `id` | `amount` | `refunded_amount` |
|---:|---:|---:|
| 1 | 100.00 | 10.00 |
| 2 | 200.00 | `NULL` |
| 3 | 150.00 | 20.00 |
| 4 | `NULL` | `NULL` |

The aggregate behavior is:

| Expression | Result | Why |
|---|---:|---|
| `COUNT(*)` | 4 | Counts rows |
| `COUNT(amount)` | 3 | Ignores `NULL` |
| `COUNT(refunded_amount)` | 2 | Ignores `NULL` |
| `SUM(amount)` | 450.00 | Ignores `NULL` |
| `AVG(amount)` | 150.00 | Average of 100, 200, 150 |
| `MIN(amount)` | 100.00 | Ignores `NULL` |
| `MAX(amount)` | 200.00 | Ignores `NULL` |

The crucial distinction is:

```sql
COUNT(*)
```

means:

> How many rows are present?

while:

```sql
COUNT(amount)
```

means:

> How many rows contain a non-NULL amount?

These are different business questions.

## COUNT and NULL

### `COUNT(*)`

`COUNT(*)` counts rows regardless of whether individual columns contain `NULL`.

```sql
SELECT COUNT(*)
FROM payments;
```

Result:

```text
4
```

Use this when the requirement is to count records.

### `COUNT(column)`

`COUNT(column)` counts only rows where the expression is not `NULL`.

```sql
SELECT COUNT(amount)
FROM payments;
```

Result:

```text
3
```

The row with:

```text
amount = NULL
```

is not counted.

### `COUNT(DISTINCT column)`

`COUNT(DISTINCT column)` also ignores `NULL`.

```sql
SELECT COUNT(DISTINCT refunded_amount)
FROM payments;
```

If the values are:

```text
10
NULL
20
NULL
```

the distinct non-null values are:

```text
10, 20
```

so the result is:

```text
2
```

This is different from:

```sql
SELECT COUNT(DISTINCT *)
```

which is not valid general SQL syntax for counting distinct complete rows.

## SUM and NULL

`SUM()` ignores `NULL` values.

Given:

```text
100
200
NULL
150
```

then:

```sql
SELECT SUM(amount)
FROM payments;
```

returns:

```text
450
```

The `NULL` does not contribute zero explicitly; it is excluded from the aggregate input.

This distinction becomes important when **all** input values are `NULL`.

```sql
SELECT SUM(amount)
FROM payments
WHERE amount IS NULL;
```

The result is:

```text
NULL
```

not:

```text
0
```

There is no non-null value to sum.

## AVG and NULL

`AVG()` ignores `NULL` values.

For:

```text
100
200
NULL
150
```

the result is:

```text
(100 + 200 + 150) / 3
= 150
```

not:

```text
(100 + 200 + 150) / 4
= 112.5
```

This means:

```sql
AVG(amount)
```

answers:

> What is the average among rows having a non-NULL amount?

It does **not** necessarily answer:

> What is the average across all records, treating missing amounts as zero?

Those are different business requirements.

If `NULL` semantically means zero, that can be made explicit:

```sql
SELECT AVG(COALESCE(amount, 0))
FROM payments;
```

But this changes the meaning of the calculation. Do not use `COALESCE()` merely to eliminate `NULL` without confirming the business semantics.

## MIN and MAX

`MIN()` and `MAX()` ignore `NULL` values.

For:

```text
100
200
NULL
150
```

```sql
SELECT
    MIN(amount),
    MAX(amount)
FROM payments;
```

returns:

```text
100
200
```

If every value is `NULL`:

```text
NULL
NULL
NULL
```

then:

```sql
SELECT MIN(amount), MAX(amount)
FROM payments;
```

returns:

```text
NULL | NULL
```

This is an important distinction from zero:

```text
MIN(amount) = NULL
```

means there is no non-null value from which to determine a minimum.

## Empty Input vs NULL Input

These cases must be distinguished.

### All Values Are NULL

Suppose:

```sql
SELECT SUM(amount)
FROM payments
WHERE amount IS NULL;
```

There may be rows, but every aggregate input is `NULL`.

The result is:

```text
NULL
```

### No Rows

Suppose:

```sql
SELECT SUM(amount)
FROM payments
WHERE id = -1;
```

No rows qualify.

For PostgreSQL, `SUM()`, `AVG()`, `MIN()`, and `MAX()` return `NULL` for an empty input set.

`COUNT()` returns `0`.

| Input | `COUNT(*)` | `SUM(amount)` |
|---|---:|---:|
| Rows with non-null values | positive | value |
| Rows with some NULL values | positive | sum of non-null values |
| Rows where all values are NULL | positive | `NULL` |
| No rows | `0` | `NULL` |

This distinction is particularly important when building API responses.

## COALESCE With Aggregates

`COALESCE()` can convert an aggregate's `NULL` result into a defined fallback.

For example:

```sql
SELECT COALESCE(SUM(amount), 0) AS total_amount
FROM payments
WHERE customer_id = 123;
```

This gives the application:

```text
0
```

instead of:

```text
NULL
```

This is often useful for metrics where the API contract defines "no total" as zero.

However:

```sql
SUM(COALESCE(amount, 0))
```

and:

```sql
COALESCE(SUM(amount), 0)
```

are not conceptually identical.

The first changes individual aggregate inputs:

```text
NULL → 0
```

The second changes the final result:

```text
NULL aggregate result → 0
```

For `SUM()`, these can often produce the same numeric result when rows exist, but they differ in how empty input and other aggregate expressions behave. Prefer the form that clearly expresses the business rule.

For example:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments;
```

clearly communicates:

> If there is no aggregate result, expose zero.

## NULL With GROUP BY

`GROUP BY` groups `NULL` values together.

Consider:

```sql
SELECT
    refunded_amount,
    COUNT(*)
FROM payments
GROUP BY refunded_amount;
```

Conceptually:

| `refunded_amount` | `COUNT(*)` |
|---:|---:|
| `10.00` | 1 |
| `20.00` | 1 |
| `NULL` | 2 |

All rows where `refunded_amount` is `NULL` belong to the same group.

This does **not** mean `NULL = NULL` is `TRUE` in ordinary comparison logic. `GROUP BY` has grouping semantics that allow rows with `NULL` grouping keys to form a group.

To identify the group explicitly:

```sql
SELECT
    refunded_amount,
    COUNT(*)
FROM payments
GROUP BY refunded_amount
ORDER BY refunded_amount;
```

## GROUP BY and Aggregate Counts

A common reporting query is:

```sql
SELECT
    customer_id,
    COUNT(*) AS payment_count,
    COUNT(refunded_amount) AS refunded_payment_count
FROM payments
GROUP BY customer_id;
```

These metrics answer different questions:

```text
COUNT(*)                  → number of payments
COUNT(refunded_amount)   → payments with a refund amount
```

This is a useful production pattern because a nullable column can encode whether an event or attribute has occurred.

However, if `NULL` means "unknown" rather than "not refunded", then `COUNT(refunded_amount)` should not automatically be interpreted as the number of non-refunded/refunded business states without verifying the schema semantics.

## Conditional Aggregation

Conditional aggregation is one of the most useful applications of `NULL` handling.

For example:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders
FROM orders;
```

PostgreSQL's `FILTER` syntax makes the intended aggregation explicit.

Another common pattern is:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed_orders
FROM orders;
```

The `CASE` expression returns:

```text
1    → completed
NULL → everything else
```

and `COUNT(expression)` ignores the `NULL` values.

This relies directly on `COUNT()`'s NULL semantics.

### Prefer FILTER in PostgreSQL

For PostgreSQL:

```sql
COUNT(*) FILTER (WHERE status = 'completed')
```

is generally clearer than:

```sql
COUNT(CASE WHEN status = 'completed' THEN 1 END)
```

Both are useful patterns, but `FILTER` directly expresses the relationship between a condition and an aggregate.

## SUM With Conditional Logic

Conditional sums often use `CASE`:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders;
```

A more explicit PostgreSQL formulation is:

```sql
SELECT
    COALESCE(
        SUM(amount) FILTER (WHERE status = 'completed'),
        0
    ) AS completed_revenue
FROM orders;
```

The latter makes two decisions explicit:

1. Which rows participate in the sum.
2. What value to return if the aggregate has no result.

## NULL and Arithmetic Inside Aggregates

Consider:

```sql
SELECT SUM(amount - refunded_amount)
FROM payments;
```

If:

```text
amount = 100
refunded_amount = NULL
```

then:

```text
amount - refunded_amount → NULL
```

and that row contributes nothing to `SUM()`.

This may be incorrect if `NULL` means "no refund".

If the domain defines missing refund amounts as zero:

```sql
SELECT SUM(amount - COALESCE(refunded_amount, 0))
FROM payments;
```

Now:

```text
100 - NULL
```

is interpreted as:

```text
100 - 0 = 100
```

The critical point is that aggregate functions do not necessarily protect you from `NULL` created **inside the expression**.

## Aggregate Expression vs Aggregate Column

Compare:

```sql
SUM(amount)
```

with:

```sql
SUM(amount * quantity)
```

For:

```text
amount = 100
quantity = NULL
```

the expression:

```sql
amount * quantity
```

evaluates to:

```text
NULL
```

Therefore that row contributes nothing to:

```sql
SUM(amount * quantity)
```

If the business rule says a missing quantity means one unit, then:

```sql
SUM(amount * COALESCE(quantity, 1))
```

may be appropriate.

But if missing quantity means bad or incomplete data, silently replacing it with `1` would hide a data-quality problem.

## NULL and COUNT for Data Quality

Aggregate functions can be used to measure missing data.

For example:

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(email) AS users_with_email,
    COUNT(*) - COUNT(email) AS users_without_email
FROM users;
```

If `email` is nullable, this provides a basic completeness metric.

Another approach is:

```sql
SELECT
    COUNT(*) FILTER (WHERE email IS NULL) AS missing_email_count,
    COUNT(*) FILTER (WHERE email IS NOT NULL) AS present_email_count
FROM users;
```

The second version is often clearer because it directly expresses the conditions being measured.

These metrics can feed operational dashboards and data-quality checks.

## NULL and HAVING

`HAVING` is evaluated after grouping and aggregation, and its predicate follows SQL's three-valued logic.

Consider:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_amount
FROM payments
GROUP BY customer_id
HAVING SUM(amount) > 1000;
```

If every `amount` for a customer is `NULL`:

```text
SUM(amount) → NULL
NULL > 1000 → UNKNOWN
```

The group is excluded.

If the business requirement is to treat a missing total as zero:

```sql
HAVING COALESCE(SUM(amount), 0) > 1000;
```

The result becomes:

```text
0 > 1000 → FALSE
```

The group is still excluded, but for an explicitly defined reason.

## LEFT JOIN and Aggregates

This is a common production scenario.

Suppose:

```sql
customers
---------
id
email

orders
------
id
customer_id
amount
```

You want every customer, including customers with no orders:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.amount), 0) AS total_spent
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id, c.email;
```

For a customer with no orders, the outer join produces a row where:

```text
o.id     → NULL
o.amount → NULL
```

Therefore:

```sql
COUNT(o.id)
```

returns:

```text
0
```

and:

```sql
COALESCE(SUM(o.amount), 0)
```

returns:

```text
0
```

This is a highly useful pattern for API and dashboard queries.

### Why `COUNT(*)` Is Dangerous Here

Consider:

```sql
SELECT
    c.id,
    COUNT(*) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

A customer with no orders still has one output row because of the `LEFT JOIN`.

Therefore:

```text
COUNT(*) → 1
```

That does **not** mean the customer has one order.

Instead use:

```sql
COUNT(o.id)
```

because the generated NULL `o.id` is ignored.

This is one of the most important `NULL` and aggregate interview traps.

## COUNT DISTINCT With LEFT JOIN

Suppose a customer can have multiple orders:

```sql
SELECT
    c.id,
    COUNT(DISTINCT o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

For customers with no orders:

```text
o.id → NULL
```

and:

```text
COUNT(DISTINCT o.id) → 0
```

This is useful when joins can multiply rows and you need to count unique entities rather than joined records.

However, `COUNT(DISTINCT ...)` can be more expensive than a normal `COUNT()`, particularly on large datasets. Validate performance against real cardinalities and execution plans.

## NULL Semantics by Aggregate

| Aggregate | NULL behavior | Empty input |
|---|---|---|
| `COUNT(*)` | Counts rows regardless of column NULLs | `0` |
| `COUNT(column)` | Ignores NULL | `0` |
| `COUNT(DISTINCT column)` | Ignores NULL | `0` |
| `SUM(column)` | Ignores NULL values | `NULL` |
| `AVG(column)` | Ignores NULL values | `NULL` |
| `MIN(column)` | Ignores NULL values | `NULL` |
| `MAX(column)` | Ignores NULL values | `NULL` |

This table is worth memorizing for interviews, but production work requires understanding what the `NULL` represents in the domain.

## Schema Design and Aggregation

A senior engineer should ask whether a nullable column is necessary.

For example:

```sql
discount_amount NUMERIC(12, 2)
```

could mean:

- no discount;
- discount not calculated;
- discount unknown;
- data not yet migrated.

Those meanings are not equivalent.

If `NULL` means "no discount", a better schema may be:

```sql
discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
```

Then:

```sql
SUM(discount_amount)
```

has simpler semantics.

If `NULL` means "discount has not yet been calculated", preserving `NULL` is appropriate.

The right choice depends on the domain, but avoiding unnecessary nullable states reduces query complexity and reporting ambiguity.

## Production Performance Considerations

Aggregates can become expensive on large tables.

For example:

```sql
SELECT
    customer_id,
    SUM(amount)
FROM payments
GROUP BY customer_id;
```

may require scanning a large portion of the payments table.

Consider:

- filtering early with selective predicates;
- appropriate indexes for filtering;
- partitioning for very large time-series tables;
- pre-aggregated reporting tables;
- materialized views;
- incremental aggregation;
- read replicas for reporting workloads.

Indexes do not automatically make aggregation fast. If most rows must be read to calculate the result, a sequential scan may be cheaper than repeatedly accessing an index.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    SUM(amount)
FROM payments
GROUP BY customer_id;
```

to understand the actual execution plan.

For high-volume analytics, separate OLTP query paths from analytical workloads when necessary rather than repeatedly running expensive aggregations against primary transactional tables.

## Application API Considerations

An aggregate query might return:

```json
{
  "total_spent": null
}
```

or:

```json
{
  "total_spent": 0
}
```

These values communicate different states.

For example:

- `0` can mean there were no monetary transactions.
- `null` can mean the value is unavailable or not computable.
- A separate field can indicate data completeness.

Do not blindly convert every SQL `NULL` to zero in Python, Django serializers, or FastAPI response models. Decide at the database or application boundary what each value means.

For a metric explicitly defined as zero when no rows qualify:

```sql
SELECT COALESCE(SUM(amount), 0) AS total_spent
FROM orders
WHERE customer_id = :customer_id;
```

This keeps the API contract deterministic.

## Common Mistakes

| Mistake | Why it fails | Better approach |
|---|---|---|
| Using `COUNT(*)` after a `LEFT JOIN` to count child records | The outer row still exists when no child exists | Use `COUNT(child.id)` |
| Assuming `COUNT(column)` counts NULLs | `COUNT(expression)` ignores NULL | Use `COUNT(*)` when counting rows |
| Assuming `SUM()` returns zero for no rows | Most numeric aggregates return NULL for empty input | Use `COALESCE(SUM(...), 0)` when zero is correct |
| Assuming `AVG()` treats NULL as zero | NULL values are excluded from the average | Explicitly use `COALESCE` only if zero is the intended value |
| Forgetting NULL inside an expression | `amount * NULL` becomes NULL before aggregation | Define the missing-value semantics explicitly |
| Treating NULL as zero automatically | NULL may represent unknown or unavailable data | Decide what NULL means in the domain |
| Using `COUNT(DISTINCT ...)` unnecessarily | Distinct aggregation can be expensive | Use it only when uniqueness is required |
| Filtering aggregates incorrectly in `WHERE` | Aggregate results do not exist until after grouping | Use `HAVING` for aggregate predicates |
| Assuming all NULL aggregate results mean the same thing | Empty input and all-NULL input can have different business meanings | Distinguish row existence from value presence |
| Ignoring nullable schema design | Every query must repeatedly handle ambiguous states | Use `NOT NULL` when the domain supports a definitive value |

## Interview Traps

### What is the difference between `COUNT(*)` and `COUNT(column)`?

```sql
COUNT(*)
```

counts rows.

```sql
COUNT(column)
```

counts non-`NULL` values of the expression.

### What does `SUM()` return when all values are NULL?

Typically:

```text
NULL
```

not zero.

### What does `SUM()` return when there are no matching rows?

Typically:

```text
NULL
```

while:

```sql
COUNT(*)
```

returns:

```text
0
```

### Why use `COUNT(child.id)` with a LEFT JOIN?

Because an unmatched child produces:

```text
child.id → NULL
```

and `COUNT(child.id)` therefore returns zero.

`COUNT(*)` would count the outer-join result row.

### Does `GROUP BY` create a separate group for every NULL?

No. Rows with a `NULL` grouping key are grouped together.

### Does `COUNT(DISTINCT column)` count NULL as a distinct value?

No. `COUNT(DISTINCT column)` ignores `NULL`.

### Should NULL always be converted to zero?

No.

`NULL` and zero have different meanings. Convert `NULL` to zero only when the business contract defines missing aggregate results as zero.

## Key Takeaways

- **`COUNT(*)` counts rows, while `COUNT(column)` and `COUNT(DISTINCT column)` ignore `NULL` values.**
- **`SUM()`, `AVG()`, `MIN()`, and `MAX()` ignore `NULL` inputs and generally return `NULL` when there is no non-NULL value to aggregate.**
- **Use `COALESCE()` when the business contract explicitly requires a deterministic fallback such as zero; do not use it to hide ambiguous data semantics.**
- **After a `LEFT JOIN`, use `COUNT(child.id)` rather than `COUNT(*)` when counting child records, because unmatched children produce `NULL` values.**
- **Treat NULL semantics as part of schema and domain design: a well-defined `NOT NULL` model can eliminate entire classes of aggregation bugs.**