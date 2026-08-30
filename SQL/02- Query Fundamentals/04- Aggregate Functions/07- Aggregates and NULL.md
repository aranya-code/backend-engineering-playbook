# 07- Aggregates and NULL

## Overview

`NULL` is not a value; it represents the absence or unknown state of a value. Aggregate functions must therefore define how they behave when input rows contain `NULL`.

For backend systems, this matters because aggregates are commonly used for:

- Reporting and analytics
- API metrics
- Data-quality checks
- Billing calculations
- Operational dashboards
- Pagination counts
- Financial totals
- Customer and tenant statistics

The most important rule is:

> Most SQL aggregates ignore `NULL` inputs, while `COUNT(*)` counts rows regardless of column values.

However, there is an important distinction between **no rows**, **rows containing only NULL**, and **zero-valued rows**. Confusing these states can produce incorrect production metrics.

## NULL and Aggregate Semantics

Consider:

```text
id | amount
---+-------
1  | 100
2  | 200
3  | NULL
4  | 300
```

Different aggregates behave differently:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(amount) AS non_null_amounts,
    SUM(amount) AS total_amount,
    AVG(amount) AS average_amount,
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount
FROM payments;
```

Conceptually:

```text
COUNT(*)          → 4
COUNT(amount)     → 3
SUM(amount)       → 600
AVG(amount)       → 200
MIN(amount)       → 100
MAX(amount)       → 300
```

The `NULL` amount is ignored by `SUM`, `AVG`, `MIN`, and `MAX`.

It is still a row, so `COUNT(*)` includes it.

## Aggregate NULL Behavior

| Aggregate | Typical NULL behavior |
|---|---|
| `COUNT(*)` | Counts rows, including rows whose columns are NULL |
| `COUNT(column)` | Ignores NULL values |
| `COUNT(DISTINCT column)` | Ignores NULL and counts unique non-NULL values |
| `SUM(column)` | Ignores NULL values |
| `AVG(column)` | Ignores NULL values |
| `MIN(column)` | Ignores NULL values |
| `MAX(column)` | Ignores NULL values |

This means:

```sql
AVG(amount)
```

is effectively calculated over the non-NULL amounts, not over every physical row.

For:

```text
100
200
NULL
300
```

the average is:

```text
(100 + 200 + 300) / 3 = 200
```

It is **not**:

```text
(100 + 200 + 0 + 300) / 4 = 150
```

`NULL` is not automatically interpreted as zero.

## NULL Is Not Zero

This distinction is critical in financial and operational systems.

Consider:

```text
order_id | discount
---------+---------
1        | 10
2        | NULL
3        | 0
```

These states can have different meanings:

- `10` → a discount of 10
- `0` → explicitly no discount
- `NULL` → discount is unknown, not applicable, or not recorded

Therefore:

```sql
SUM(discount)
```

does not mean that NULL discounts were explicitly zero.

It means the aggregate ignores those NULL inputs.

If the business requirement explicitly defines NULL as zero, make that transformation intentional:

```sql
SELECT SUM(COALESCE(discount, 0))
FROM orders;
```

This changes the semantic interpretation of the data.

## SUM and NULL

`SUM` ignores NULL values.

Given:

```text
amount
------
100
NULL
200
```

```sql
SELECT SUM(amount)
FROM payments;
```

returns:

```text
300
```

The NULL row does not contribute to the sum.

### All Values Are NULL

The important edge case is when every input value is NULL:

```text
amount
------
NULL
NULL
NULL
```

Then:

```sql
SELECT SUM(amount)
FROM payments;
```

returns `NULL`, not `0`.

This distinction matters:

```text
NULL → no non-NULL numeric input exists
0    → an aggregate result of zero
```

If the business requirement treats no values as zero:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments;
```

Use this intentionally rather than mechanically applying `COALESCE` to every aggregate.

## AVG and NULL

`AVG` ignores NULL values.

```sql
SELECT AVG(score)
FROM assessments;
```

Given:

```text
score
-----
80
90
NULL
100
```

the result is:

```text
90
```

because the average is calculated over three non-NULL values.

### Why This Matters

A common production mistake is assuming NULL observations should participate in the denominator.

For example, if NULL means "customer did not submit a rating", then:

```sql
AVG(rating)
```

correctly calculates the average among submitted ratings.

If NULL means "rating should be treated as zero", the data model or query must explicitly encode that business rule:

```sql
AVG(COALESCE(rating, 0))
```

These queries answer different questions.

## COUNT and NULL

`COUNT(*)` and `COUNT(column)` have fundamentally different semantics.

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(amount) AS rows_with_amount
FROM payments;
```

For:

```text
100
NULL
200
```

the result is:

```text
total_rows       = 3
rows_with_amount = 2
```

This is useful for data-quality metrics:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(shipped_at) AS shipped_orders,
    COUNT(*) - COUNT(shipped_at) AS not_shipped_or_unknown
FROM orders;
```

The final expression identifies rows where `shipped_at` is NULL, but the business interpretation still depends on what NULL means in the schema.

## COUNT(DISTINCT) and NULL

`COUNT(DISTINCT column)` ignores NULL.

Given:

```text
customer_id
-----------
10
10
20
NULL
20
```

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

returns:

```text
2
```

The distinct non-NULL values are:

```text
10
20
```

If the requirement is to count NULL as its own category, use explicit grouping or a NULL replacement:

```sql
SELECT COUNT(DISTINCT COALESCE(customer_id, -1))
FROM orders;
```

However, replacing NULL with a sentinel can be dangerous if that sentinel is a valid domain value.

A safer approach is often to calculate the components explicitly:

```sql
SELECT
    COUNT(DISTINCT customer_id)
        + CASE
            WHEN COUNT(*) > COUNT(customer_id) THEN 1
            ELSE 0
          END AS distinct_values_including_null
FROM orders;
```

Whether this is appropriate depends on the database and business requirement.

## MIN and MAX with NULL

`MIN` and `MAX` ignore NULL values.

```sql
SELECT
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price
FROM products;
```

Given:

```text
100
NULL
300
200
```

the result is:

```text
minimum_price = 100
maximum_price = 300
```

If all values are NULL:

```sql
SELECT MIN(price)
FROM products;
```

returns `NULL`.

This means:

```text
MIN(price) = NULL
```

should not automatically be interpreted as:

```text
minimum price = 0
```

It usually means there is no non-NULL price to evaluate.

## No Rows vs All NULL Rows

One of the most important aggregate edge cases is distinguishing:

1. No rows matched the query.
2. Rows matched, but all aggregate inputs were NULL.

For example:

```sql
SELECT SUM(amount)
FROM payments
WHERE customer_id = :customer_id;
```

Both of these situations can result in `NULL`:

```text
Case A:
No matching rows

Case B:
Matching rows exist, but amount is NULL for every row
```

If your application needs to distinguish them, return additional information:

```sql
SELECT
    COUNT(*) AS matching_rows,
    COUNT(amount) AS non_null_amounts,
    SUM(amount) AS total_amount
FROM payments
WHERE customer_id = :customer_id;
```

Now the states can be distinguished:

| `matching_rows` | `non_null_amounts` | `SUM(amount)` | Interpretation |
|---:|---:|---:|---|
| 0 | 0 | NULL | No matching rows |
| > 0 | 0 | NULL | Rows exist, but all amounts are NULL |
| > 0 | > 0 | value | At least one amount exists |

This pattern is valuable when API semantics or business reporting require precision.

## COALESCE with Aggregates

`COALESCE` converts NULL results into a fallback value.

```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments;
```

This is commonly used when an API contract requires a numeric response rather than NULL.

For example:

```json
{
  "total_revenue": 0
}
```

instead of:

```json
{
  "total_revenue": null
}
```

However, this changes the meaning.

```sql
SUM(amount)
```

means:

> Return the aggregate result, which may be NULL.

```sql
COALESCE(SUM(amount), 0)
```

means:

> Treat a NULL aggregate result as zero.

The application should make that decision based on domain semantics.

## COALESCE Before Aggregation vs After Aggregation

These two expressions are not always equivalent conceptually:

```sql
SUM(COALESCE(amount, 0))
```

and:

```sql
COALESCE(SUM(amount), 0)
```

### Before Aggregation

```sql
SUM(COALESCE(amount, 0))
```

converts every NULL input into zero before aggregation.

### After Aggregation

```sql
COALESCE(SUM(amount), 0)
```

first calculates the aggregate and then converts a NULL result to zero.

For:

```text
100
NULL
200
```

both produce:

```text
300
```

But their semantics differ for an empty input set or an all-NULL set.

A useful rule is:

> Use `COALESCE` before aggregation when NULL inputs are genuinely zero; use it after aggregation when only the final NULL result should be represented as zero.

## NULL and GROUP BY

Aggregates interact with NULL grouping keys differently from aggregate input values.

Consider:

```text
country | revenue
--------+--------
IN      | 100
IN      | 200
NULL    | 300
US      | 400
```

```sql
SELECT
    country,
    SUM(revenue) AS total_revenue
FROM orders
GROUP BY country;
```

The database creates a group for the NULL `country` value.

Conceptually:

```text
country | total_revenue
--------+--------------
IN      | 300
US      | 400
NULL    | 300
```

This is different from:

```sql
SUM(country)
```

where NULL values would be ignored if the data type supported such an aggregate.

The key distinction is:

> `NULL` in a grouping key can form a group, while `NULL` as an aggregate input is generally ignored.

## NULL and HAVING

`HAVING` evaluates aggregate results.

Consider:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_amount
FROM payments
GROUP BY customer_id
HAVING SUM(amount) > 1000;
```

If `SUM(amount)` is NULL, the comparison:

```sql
NULL > 1000
```

does not evaluate to TRUE.

The group therefore does not satisfy the `HAVING` condition.

If NULL should be interpreted as zero:

```sql
HAVING COALESCE(SUM(amount), 0) > 1000
```

The explicit transformation makes the intended semantics clearer.

## NULL and Conditional Aggregation

Conditional aggregation is particularly useful for data-quality and operational metrics.

PostgreSQL:

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(*) FILTER (
        WHERE email IS NOT NULL
    ) AS users_with_email,
    COUNT(*) FILTER (
        WHERE phone IS NOT NULL
    ) AS users_with_phone
FROM users;
```

This produces separate completeness metrics without requiring multiple queries.

A portable `CASE` pattern is:

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(CASE
        WHEN email IS NOT NULL THEN 1
    END) AS users_with_email,
    COUNT(CASE
        WHEN phone IS NOT NULL THEN 1
    END) AS users_with_phone
FROM users;
```

The expression returns a non-NULL value only when the condition is satisfied.

## NULL and LEFT JOIN Aggregates

`LEFT JOIN` is a common source of aggregate bugs.

Suppose:

```text
customers
+----+-------+
| id | name  |
+----+-------+
| 1  | Alice |
| 2  | Bob   |
+----+-------+

orders
+----+-------------+--------+
| id | customer_id | amount |
+----+-------------+--------+
| 10 | 1           | 100    |
| 11 | 1           | 200    |
+----+-------------+--------+
```

Query:

```sql
SELECT
    c.id,
    COUNT(*) AS row_count,
    COUNT(o.id) AS order_count,
    SUM(o.amount) AS total_amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

For Bob, the joined order columns are NULL.

The result is conceptually:

```text
customer | row_count | order_count | total_amount
---------+-----------+-------------+-------------
Alice    | 2         | 2           | 300
Bob      | 1         | 0           | NULL
```

If the API contract requires zero revenue for customers with no orders:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.amount), 0) AS total_amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Now Bob receives:

```text
order_count = 0
total_amount = 0
```

This is often the desired API representation, but only if "no orders" semantically means zero total.

## NULL and Data Quality

Aggregate functions can be used to monitor NULL rates.

For example:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(email) AS populated_emails,
    COUNT(*) - COUNT(email) AS null_emails
FROM users;
```

Calculate the NULL ratio:

```sql
SELECT
    100.0 * (COUNT(*) - COUNT(email)) / NULLIF(COUNT(*), 0)
        AS null_email_percentage
FROM users;
```

`NULLIF` prevents division by zero.

This type of query can feed:

- Data-quality dashboards
- ETL validation
- CI/CD data checks
- Operational alerts
- Schema migration validation

For a production system, sudden changes in NULL rates can indicate application regressions or failed data pipelines.

## NULL in Financial Aggregation

Financial systems require especially careful NULL semantics.

Consider:

```text
invoice_id | tax
-----------+-----
1          | 10
2          | NULL
3          | 20
```

This:

```sql
SELECT SUM(tax)
FROM invoices;
```

returns:

```text
30
```

But that does not prove the total tax liability is 30.

The NULL row may mean:

- Tax was not calculated.
- Tax is not applicable.
- Tax calculation failed.
- Data has not yet been migrated.
- The value is genuinely unknown.

Replacing NULL with zero may hide a data-quality problem:

```sql
SUM(COALESCE(tax, 0))
```

Therefore, financial reporting often benefits from calculating both the aggregate and completeness:

```sql
SELECT
    SUM(tax) AS total_tax,
    COUNT(*) AS invoice_count,
    COUNT(tax) AS invoices_with_tax
FROM invoices;
```

The application can then detect whether the aggregate is complete.

## NULL and API Contracts

Database NULL semantics should not accidentally determine API semantics.

Suppose:

```sql
SELECT COALESCE(SUM(amount), 0) AS total
FROM orders
WHERE customer_id = :customer_id;
```

The API might return:

```json
{
  "total": 0
}
```

That is appropriate if:

```text
No orders → total is zero
```

But it may be incorrect if:

```text
No orders → total is unknown/not applicable
```

In that case:

```sql
SELECT SUM(amount) AS total
FROM orders
WHERE customer_id = :customer_id;
```

may be the more accurate representation.

The database query should reflect the domain contract rather than merely making the API payload convenient.

## NULL and Django ORM

Django aggregation follows the underlying SQL semantics.

For example:

```python
from django.db.models import Sum

result = Order.objects.aggregate(
    total_amount=Sum("amount"),
)
```

If there are no non-NULL values, the aggregate can be `None` in Python.

If the application explicitly wants zero:

```python
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

result = Order.objects.aggregate(
    total_amount=Coalesce(
        Sum("amount"),
        Value(0),
    ),
)
```

For counting populated values:

```python
from django.db.models import Count

result = User.objects.aggregate(
    users_with_phone=Count("phone"),
)
```

For a complete row count:

```python
result = User.objects.count()
```

When using ORM aggregation, understand the generated SQL, especially when relationships and joins are involved.

## Production Considerations

### Define What NULL Means

Before aggregating, determine whether NULL means:

- Unknown
- Missing
- Not applicable
- Not yet calculated
- Not provided
- Deleted or unavailable

Do not automatically equate NULL with zero.

### Preserve Data Quality Signals

For important metrics, consider returning both the aggregate and population information:

```sql
SELECT
    COUNT(*) AS total_records,
    COUNT(amount) AS records_with_amount,
    SUM(amount) AS total_amount
FROM transactions;
```

This prevents an aggregate from hiding incomplete data.

### Be Careful with COALESCE

`COALESCE` is useful for API-friendly output, but excessive use can erase meaningful distinctions between:

```text
unknown
missing
not applicable
zero
```

Use it at the boundary where the business contract requires the conversion.

### Test Empty and All-NULL Cases

For every important aggregate query, test at least:

| Dataset state | Example |
|---|---|
| Normal values | `100, 200, 300` |
| Some NULLs | `100, NULL, 300` |
| All NULLs | `NULL, NULL` |
| No rows | Empty result set |
| Explicit zero | `0, 0` |

The last two are particularly important because empty input and zero-valued input are semantically different.

### Monitor NULL Rates

For important production fields, track NULL ratios over time.

Unexpected changes can reveal:

- Application bugs
- Failed migrations
- ETL failures
- Schema changes
- Partial deployments
- Upstream data-quality regressions

## Common Mistakes and Pitfalls

| Mistake | Problem | Better approach |
|---|---|---|
| Treating NULL as zero | Unknown and zero are different states | Convert NULL only when domain semantics justify it |
| Assuming `COUNT(*)` ignores NULL | It counts rows, not populated values | Use `COUNT(column)` for non-NULL values |
| Assuming `AVG` includes NULL in the denominator | NULL inputs are ignored | Understand the effective population |
| Assuming `SUM(NULL)` is zero | All-NULL or empty input can produce NULL | Use `COALESCE` when zero is the required result |
| Using `COUNT(*)` after a `LEFT JOIN` | Preserved parent rows can be counted as children | Count a nullable child key |
| Applying `COALESCE` everywhere | Can hide data-quality problems | Preserve NULL where it carries business meaning |
| Confusing empty result with zero | No rows and zero-valued rows are different | Define the API/domain semantics explicitly |
| Ignoring NULL grouping behavior | NULL can form its own `GROUP BY` group | Distinguish grouping semantics from aggregate-input semantics |
| Assuming non-NULL aggregate means complete data | Some rows may still contain NULL | Track population and completeness separately |
| Replacing NULL with a sentinel blindly | Sentinel may collide with valid data | Prefer explicit NULL-aware logic |

## Interview Traps

### Does SUM Ignore NULL?

Yes.

```sql
SELECT SUM(value)
FROM metrics;
```

For:

```text
10
NULL
20
```

the result is:

```text
30
```

But if all values are NULL, `SUM` returns NULL rather than zero.

### Does AVG Count NULL Rows?

No.

For:

```text
10
20
NULL
```

```sql
AVG(value)
```

is:

```text
15
```

The denominator is 2, not 3.

### Does COUNT(*) Ignore NULL?

No.

```sql
COUNT(*)
```

counts rows regardless of whether their columns contain NULL.

### Does COUNT(column) Count NULL?

No.

```sql
COUNT(column)
```

counts only rows where the expression is non-NULL.

### What Does GROUP BY Do with NULL?

Rows with a NULL grouping key belong to the same NULL group.

```sql
SELECT country, COUNT(*)
FROM users
GROUP BY country;
```

can produce a group where:

```text
country = NULL
```

### What Does SUM Return for No Rows?

For standard SQL aggregate behavior, `SUM` over an empty input returns NULL.

If the application requires zero:

```sql
COALESCE(SUM(amount), 0)
```

## Production Checklist

Before shipping an aggregate query involving potentially NULL columns:

- [ ] Is NULL semantically different from zero?
- [ ] Does the aggregate ignore NULL values as expected?
- [ ] Does `COUNT(*)` or `COUNT(column)` match the requirement?
- [ ] What happens when all aggregate inputs are NULL?
- [ ] What happens when no rows match?
- [ ] Does a `LEFT JOIN` introduce NULL child rows?
- [ ] Does the API need `NULL` or `0`?
- [ ] Could `COALESCE` hide a data-quality issue?
- [ ] Should NULL rates be monitored?
- [ ] Have empty, all-NULL, zero, and normal cases been tested?
- [ ] If the metric is financial or operationally critical, is completeness measured separately?

## Key Takeaways

- Most SQL aggregates ignore NULL inputs; `COUNT(*)` is the major distinction because it counts rows regardless of NULL column values.
- `NULL` and zero represent different states; use `COALESCE` only when the domain explicitly requires NULL to be represented as zero.
- `SUM`, `AVG`, `MIN`, and `MAX` can return `NULL` when there are no non-NULL inputs, so empty and all-NULL cases must be tested explicitly.
- `LEFT JOIN` plus aggregation requires careful reasoning because unmatched child rows become NULL and can affect `COUNT(*)`, `SUM`, and related metrics differently.
- Production-grade aggregate queries should preserve data-quality signals by distinguishing the aggregate result from the number of rows containing valid non-NULL inputs.