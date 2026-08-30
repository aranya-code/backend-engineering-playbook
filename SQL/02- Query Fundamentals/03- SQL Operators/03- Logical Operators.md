# 03- Logical Operators

## Overview

Logical operators combine or negate boolean predicates. They are the primary mechanism for expressing multi-condition filtering in SQL and are used extensively with `WHERE`, `HAVING`, `JOIN ... ON`, and conditional expressions.

The three core logical operators are:

| Operator | Purpose | Example |
|---|---|---|
| `AND` | All conditions must be true | `status = 'paid' AND total_amount > 100` |
| `OR` | At least one condition must be true | `status = 'paid' OR status = 'pending'` |
| `NOT` | Negates a predicate | `NOT status = 'cancelled'` |

Logical operators become more subtle when combined with SQL's three-valued logic. Because predicates can evaluate to `TRUE`, `FALSE`, or `UNKNOWN`, `NULL` can produce results that differ from ordinary two-valued boolean logic.

## AND

`AND` requires both operands to evaluate to `TRUE` for the complete expression to be `TRUE`.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    status
FROM orders
WHERE status = 'paid'
  AND total_amount >= 100;
```

This returns orders that satisfy both conditions.

`AND` is useful when a query represents a conjunction of business constraints:

- A user belongs to a tenant **and** is active.
- An order is paid **and** exceeds a threshold.
- A timestamp falls inside a range **and** the record has a particular status.
- A product belongs to a category **and** is available.

### AND Truth Table

With two-valued boolean logic:

| A | B | `A AND B` |
|---|---|---|
| `TRUE` | `TRUE` | `TRUE` |
| `TRUE` | `FALSE` | `FALSE` |
| `FALSE` | `TRUE` | `FALSE` |
| `FALSE` | `FALSE` | `FALSE` |

With SQL `NULL`, the third state matters:

| A | B | `A AND B` |
|---|---|---|
| `TRUE` | `UNKNOWN` | `UNKNOWN` |
| `FALSE` | `UNKNOWN` | `FALSE` |
| `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

The `FALSE AND UNKNOWN = FALSE` behavior is particularly useful for understanding why some predicates can still exclude rows containing `NULL`.

## OR

`OR` evaluates to `TRUE` when at least one operand is `TRUE`.

```sql
SELECT
    id,
    status
FROM orders
WHERE status = 'paid'
   OR status = 'pending';
```

This is useful for expressing alternative valid conditions.

### OR Truth Table

| A | B | `A OR B` |
|---|---|---|
| `TRUE` | `TRUE` | `TRUE` |
| `TRUE` | `FALSE` | `TRUE` |
| `FALSE` | `TRUE` | `TRUE` |
| `FALSE` | `FALSE` | `FALSE` |

With `UNKNOWN`:

| A | B | `A OR B` |
|---|---|---|
| `TRUE` | `UNKNOWN` | `TRUE` |
| `FALSE` | `UNKNOWN` | `UNKNOWN` |
| `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

Therefore:

```sql
WHERE status = 'paid'
   OR status = 'pending'
```

does not automatically include rows where `status IS NULL`.

If `NULL` should be treated as another valid case, state that explicitly:

```sql
WHERE status IN ('paid', 'pending')
   OR status IS NULL;
```

## NOT

`NOT` negates a predicate.

```sql
SELECT
    id,
    status
FROM orders
WHERE NOT status = 'cancelled';
```

Conceptually:

```text
NOT TRUE     → FALSE
NOT FALSE    → TRUE
NOT UNKNOWN  → UNKNOWN
```

Therefore, this does not include `NULL` statuses:

```sql
WHERE NOT status = 'cancelled'
```

If the requirement is "anything except cancelled, including records with no status", write the condition explicitly:

```sql
WHERE status <> 'cancelled'
   OR status IS NULL;
```

## Operator Precedence

When an expression contains multiple logical operators, SQL evaluates them according to precedence rules.

A common precedence order is:

```text
NOT
AND
OR
```

For example:

```sql
WHERE status = 'paid'
   OR status = 'pending'
  AND total_amount >= 100;
```

is interpreted conceptually as:

```sql
WHERE status = 'paid'
   OR (
       status = 'pending'
       AND total_amount >= 100
   );
```

It is **not** equivalent to:

```sql
WHERE (
    status = 'paid'
    OR status = 'pending'
)
AND total_amount >= 100;
```

When business logic matters, use parentheses rather than relying on precedence.

```sql
SELECT
    id,
    status,
    total_amount
FROM orders
WHERE (
    status = 'paid'
    OR status = 'pending'
)
AND total_amount >= 100;
```

Parentheses improve correctness, readability, and maintainability.

## Combining AND and OR

Production queries frequently combine multiple conditions.

```sql
SELECT
    id,
    customer_id,
    status,
    priority,
    total_amount
FROM orders
WHERE customer_id = :customer_id
  AND (
      status = 'paid'
      OR (
          status = 'pending'
          AND priority = 'high'
      )
  );
```

The parentheses define the business rule explicitly:

```text
customer belongs to the customer
AND
(
    order is paid
    OR
    order is pending and high priority
)
```

This is preferable to writing a dense expression and expecting every future maintainer to remember SQL operator precedence.

## Three-Valued Logic

SQL predicates can evaluate to:

```text
TRUE
FALSE
UNKNOWN
```

`UNKNOWN` commonly occurs when a comparison involves `NULL`.

Consider:

```sql
SELECT
    id,
    status
FROM orders
WHERE status = 'paid'
   OR status <> 'paid';
```

It is tempting to assume this returns every row because every non-null value is either equal or not equal to `'paid'`.

It does not.

For:

```text
status = NULL
```

both:

```sql
status = 'paid'
status <> 'paid'
```

evaluate to `UNKNOWN`.

Then:

```text
UNKNOWN OR UNKNOWN
```

is still `UNKNOWN`, so the row is excluded by `WHERE`.

This is a common SQL interview and production correctness trap.

## NULL-Aware Logical Expressions

Consider:

```sql
WHERE status <> 'cancelled'
   AND priority <> 'low';
```

A row with:

```text
status = 'paid'
priority = NULL
```

produces:

```text
TRUE AND UNKNOWN
→ UNKNOWN
```

and is therefore excluded.

If the application treats missing priority as acceptable, the query must express that:

```sql
WHERE status <> 'cancelled'
  AND (
      priority <> 'low'
      OR priority IS NULL
  );
```

Do not rely on informal interpretations such as "not low means everything except low." In SQL, `NULL` requires explicit handling.

## De Morgan's Laws

Logical expressions can often be transformed using De Morgan's laws.

```text
NOT (A AND B)
    =
(NOT A) OR (NOT B)

NOT (A OR B)
    =
(NOT A) AND (NOT B)
```

For example:

```sql
WHERE NOT (
    status = 'cancelled'
    OR status = 'failed'
);
```

can be expressed as:

```sql
WHERE status <> 'cancelled'
  AND status <> 'failed';
```

However, `NULL` can affect the practical behavior of equivalent-looking expressions because SQL uses three-valued logic.

For predicates involving nullable columns, verify the desired semantics rather than blindly applying transformations.

## IN as a Logical Alternative

Multiple equality comparisons joined with `OR` can often be represented with `IN`.

Instead of:

```sql
WHERE status = 'paid'
   OR status = 'pending'
   OR status = 'processing';
```

prefer:

```sql
WHERE status IN ('paid', 'pending', 'processing');
```

This is generally clearer and communicates the intent directly.

For application code:

```sql
SELECT
    id,
    status
FROM orders
WHERE status IN (:status_1, :status_2, :status_3);
```

The exact parameter syntax depends on the database driver or ORM.

`IN` is not merely a readability feature; the optimizer can often handle it efficiently, but actual performance should be verified for large lists.

## BETWEEN as a Logical Alternative

A numeric range:

```sql
WHERE total_amount >= 100
  AND total_amount <= 1000
```

can be expressed as:

```sql
WHERE total_amount BETWEEN 100 AND 1000;
```

`BETWEEN` is inclusive at both ends.

For timestamp ranges, many backend systems prefer explicit half-open intervals:

```sql
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

This makes boundaries easier to reason about when processing adjacent time windows.

## Logical Operators in JOIN Conditions

Logical expressions are also used in join predicates.

```sql
SELECT
    o.id,
    r.name
FROM orders AS o
JOIN shipping_rates AS r
  ON o.total_amount >= r.minimum_amount
 AND o.total_amount < r.maximum_amount
 AND r.region = o.shipping_region;
```

For complex joins, carefully distinguish:

```text
JOIN ... ON
    relationship conditions

WHERE
    result filtering conditions
```

Moving a predicate between `ON` and `WHERE` can change the semantics of an outer join.

For example, with a `LEFT JOIN`, filtering a nullable right-side table in `WHERE` can effectively turn the result into inner-join behavior:

```sql
SELECT
    u.id,
    p.plan_name
FROM users AS u
LEFT JOIN plans AS p
    ON p.id = u.plan_id
WHERE p.plan_name = 'premium';
```

If users without a plan must remain in the result, the condition may belong in the join predicate instead:

```sql
SELECT
    u.id,
    p.plan_name
FROM users AS u
LEFT JOIN plans AS p
    ON p.id = u.plan_id
   AND p.plan_name = 'premium';
```

This distinction is important in production reporting and API queries.

## Logical Operators in HAVING

Logical operators can combine aggregate conditions.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10
   AND SUM(total_amount) >= 5000;
```

`WHERE` filters rows before aggregation, while `HAVING` filters groups after aggregation.

Prefer pushing row-level conditions into `WHERE` when possible:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

This can reduce the amount of data processed by grouping and aggregation.

## Dynamic API Filters

Backend APIs often expose multiple optional filters:

```text
GET /orders?status=paid&min_total=100&priority=high
```

The application can construct a query whose predicates are combined with `AND`.

Conceptually:

```sql
SELECT
    id,
    customer_id,
    status,
    priority,
    total_amount
FROM orders
WHERE customer_id = :customer_id
  AND status = :status
  AND priority = :priority
  AND total_amount >= :min_total;
```

A query builder or ORM should handle parameter binding.

With Django:

```python
queryset = Order.objects.filter(customer_id=customer_id)

if status:
    queryset = queryset.filter(status=status)

if priority:
    queryset = queryset.filter(priority=priority)

if min_total is not None:
    queryset = queryset.filter(total_amount__gte=min_total)
```

This keeps values separate from SQL syntax and allows the ORM to generate parameterized SQL.

For dynamic filters, validate:

- Allowed fields.
- Allowed operators.
- Data types.
- Maximum filter-list sizes.
- Business authorization constraints.

## Performance Implications

Logical operators themselves are rarely the primary performance problem. The important issue is the resulting predicate and how the optimizer can execute it.

### AND and Indexes

A query such as:

```sql
SELECT *
FROM orders
WHERE customer_id = :customer_id
  AND created_at >= :start_time;
```

may benefit from a composite index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

The appropriate index depends on:

- Query shape.
- Column cardinality.
- Selectivity.
- Sort requirements.
- Data distribution.
- Other workload patterns.

### OR Can Be More Difficult

Consider:

```sql
WHERE customer_id = :customer_id
   OR email = :email;
```

Depending on the database and indexes, the optimizer may use multiple access paths, combine them, or choose another strategy.

Do not automatically rewrite every `OR` as a `UNION`. Measure first.

For performance-sensitive queries, inspect the execution plan:

```sql
EXPLAIN
SELECT
    id
FROM users
WHERE customer_id = :customer_id
   OR email = :email;
```

In PostgreSQL, detailed analysis can use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id
FROM users
WHERE customer_id = :customer_id
   OR email = :email;
```

## Predicate Pushdown

When filtering through joins or aggregations, applying restrictive predicates as early as logically possible can reduce the amount of data processed.

For example:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The database can eliminate non-completed orders before grouping.

At the application architecture level, avoid fetching a broad dataset into Python and then applying filtering in application code:

```python
# Avoid for large datasets
orders = list(Order.objects.all())
completed = [order for order in orders if order.status == "completed"]
```

Prefer database-side filtering:

```python
completed = Order.objects.filter(status="completed")
```

The database is optimized to filter data close to where it is stored and can use indexes and query-planning strategies.

## Common Mistakes

### Forgetting Parentheses

Risky:

```sql
WHERE tenant_id = :tenant_id
  AND status = 'paid'
  OR status = 'pending';
```

This can return pending records from other tenants.

Correct:

```sql
WHERE tenant_id = :tenant_id
  AND (
      status = 'paid'
      OR status = 'pending'
  );
```

For multi-tenant systems, this mistake can become a serious data-isolation issue.

### Treating NULL as FALSE

`NULL` is not equivalent to `FALSE`.

For a nullable boolean column:

```sql
WHERE is_active = TRUE;
```

does not include rows where `is_active IS NULL`.

If `NULL` has domain meaning, handle it explicitly.

### Assuming NOT Includes NULL

This:

```sql
WHERE NOT status = 'cancelled';
```

does not include `NULL` statuses.

Use explicit `IS NULL` logic if required.

### Overusing NOT

Negated predicates can be harder to reason about, particularly with nullable columns.

Prefer explicit positive conditions when they make the business rule clearer.

Instead of:

```sql
WHERE NOT (status = 'cancelled' OR status = 'failed')
```

consider:

```sql
WHERE status IN ('paid', 'pending', 'processing');
```

when those are the actual allowed states.

### Building SQL with User Input

Never directly concatenate API input into logical expressions or operators.

Unsafe:

```python
query = f"""
    SELECT *
    FROM orders
    WHERE status = '{status}'
"""
```

Use parameterized database access or an ORM.

### Filtering After Fetching Large Datasets

Avoid retrieving thousands or millions of rows only to filter them in application code.

Push filtering into SQL whenever the database can perform it efficiently.

### Assuming Equivalent Expressions Have Identical NULL Behavior

Expressions that appear logically equivalent under two-valued Boolean algebra can behave differently when `NULL` is involved.

Always test nullable predicates against representative data.

## Security Considerations

Logical expressions are directly involved in authorization and tenant isolation.

A dangerous pattern is:

```sql
WHERE tenant_id = :tenant_id
  AND owner_id = :owner_id
  OR is_public = TRUE;
```

Due to precedence, this means:

```sql
WHERE (
    tenant_id = :tenant_id
    AND owner_id = :owner_id
)
OR is_public = TRUE;
```

That may be correct for a deliberately public resource, but if `is_public` is not intended to bypass tenant boundaries, it creates an authorization vulnerability.

When authorization predicates are security-critical, make the intended scope explicit:

```sql
WHERE tenant_id = :tenant_id
  AND (
      owner_id = :owner_id
      OR is_public = TRUE
  );
```

In multi-tenant applications, tenant constraints should be consistently enforced at the appropriate application or database layer rather than being accidentally omitted from individual queries.

## Production Best Practices

- Use parentheses whenever `AND` and `OR` are mixed.
- Treat `NULL` explicitly rather than assuming ordinary Boolean behavior.
- Prefer `IN` for multiple equality alternatives.
- Keep authorization and tenant predicates structurally obvious.
- Push filtering into the database rather than filtering large result sets in application code.
- Parameterize values rather than interpolating user input.
- Validate dynamic filter fields and operators with allowlists.
- Check execution plans for complex predicates.
- Use composite indexes based on actual query patterns.
- Test logical predicates with `NULL` and boundary cases.
- Keep generated ORM queries observable in production.
- Add regression tests for authorization predicates and multi-tenant filtering.

## Interview Traps

| Question | Key Point |
|---|---|
| What is the precedence of `NOT`, `AND`, and `OR`? | Generally `NOT` before `AND`, and `AND` before `OR` |
| Why use parentheses with `AND` and `OR`? | To make intended grouping explicit and prevent logic errors |
| Does `NOT column = value` include NULL? | No; `NOT UNKNOWN` remains `UNKNOWN` |
| What are SQL's three logical states? | `TRUE`, `FALSE`, and `UNKNOWN` |
| Why doesn't `A OR NOT A` always return every row? | If `A` is `UNKNOWN`, the result remains `UNKNOWN` |
| When should `IN` replace multiple `OR` equality predicates? | When checking whether a value belongs to a known set |
| Can moving a predicate from `ON` to `WHERE` change results? | Yes, especially with `LEFT JOIN` and other outer joins |
| Why can `OR` affect performance? | The optimizer may need to consider multiple access paths |
| Why are logical operators important for authorization? | Incorrect grouping can unintentionally bypass tenant or ownership constraints |

## Practical Predicate Checklist

Before shipping a complex SQL predicate, verify:

- Is the intended grouping explicit?
- Are nullable columns handled intentionally?
- Are `AND` and `OR` combinations covered by tests?
- Does the predicate enforce tenant boundaries?
- Can an `OR` condition unintentionally bypass authorization?
- Are API-supplied values parameterized?
- Are dynamic fields and operators allowlisted?
- Can filtering happen in SQL rather than application memory?
- Does the query use appropriate indexes?
- Has the execution plan been checked for high-volume queries?
- Are `LEFT JOIN` predicates placed in the correct `ON` or `WHERE` clause?
- Have `NULL`, empty, boundary, and unexpected values been tested?

## Key Takeaways

- `AND`, `OR`, and `NOT` combine predicates, but SQL's three-valued logic makes `NULL` behavior different from ordinary Boolean algebra.
- Use parentheses whenever `AND` and `OR` are mixed, especially around authorization and multi-tenant predicates.
- Treat `NULL` explicitly; `NOT`, `<>`, and other comparisons do not automatically include null-valued rows.
- Prefer clear constructs such as `IN`, database-side filtering, and parameterized queries for production applications.
- Complex logical predicates should be validated for both correctness and performance using representative tests and execution plans.