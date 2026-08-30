# 10- CASE for Conditional Logic

## Overview

`CASE` is SQL's primary conditional expression. It allows a query to choose a value based on one or more conditions without moving the decision-making into application code.

For backend systems, this is useful when conditional logic naturally belongs close to relational data:

- Classifying records.
- Deriving API response fields.
- Calculating conditional metrics.
- Translating database states into business categories.
- Applying conditional updates.
- Ordering records according to business priority.
- Building reporting and analytics queries.

A typical pattern is:

```sql
SELECT
    order_id,
    CASE
        WHEN total_amount >= 10000 THEN 'enterprise'
        WHEN total_amount >= 1000 THEN 'high_value'
        ELSE 'standard'
    END AS customer_segment
FROM orders;
```

The important distinction is that `CASE` is an **expression**, not a procedural control-flow statement. It produces a value that can be used anywhere SQL permits an expression.

## Why Conditional Logic Belongs in SQL

Suppose an API needs to display an order category derived entirely from database columns.

One approach is:

```text
PostgreSQL
    ↓
return raw order data
    ↓
Python
    ↓
calculate category
    ↓
JSON response
```

Another is:

```text
PostgreSQL
    ↓
calculate category with CASE
    ↓
return final relational result
    ↓
Python
    ↓
JSON response
```

When the classification is fundamentally relational, the second approach can be cleaner and more efficient.

The database can evaluate the expression while scanning the relevant rows, avoiding unnecessary data transfer and application-side iteration.

However, not every business rule belongs in SQL. Rules that require external APIs, complex application state, or frequently changing domain workflows may be better implemented elsewhere.

## CASE as an Expression

A `CASE` expression returns one result:

```sql
CASE
    WHEN condition THEN result
    ELSE fallback
END
```

For example:

```sql
CASE
    WHEN age >= 18 THEN 'adult'
    ELSE 'minor'
END
```

The expression can appear in:

```text
SELECT
WHERE
ORDER BY
GROUP BY
HAVING
UPDATE
INSERT
JOIN conditions
computed expressions
```

Example:

```sql
SELECT
    user_id,
    CASE
        WHEN is_active THEN 'active'
        ELSE 'inactive'
    END AS account_state
FROM users;
```

The resulting column is not physically stored unless the expression is used to populate or maintain a stored/generated value.

## Searched CASE

The searched form evaluates arbitrary Boolean conditions:

```sql
CASE
    WHEN condition_1 THEN result_1
    WHEN condition_2 THEN result_2
    ELSE result_default
END
```

Example:

```sql
SELECT
    order_id,
    CASE
        WHEN total_amount >= 10000 THEN 'enterprise'
        WHEN total_amount >= 1000 THEN 'premium'
        WHEN total_amount > 0 THEN 'standard'
        ELSE 'invalid'
    END AS order_class
FROM orders;
```

This is the most flexible form because each `WHEN` can use different columns and predicates.

## Simple CASE

The simple form compares one expression against several values:

```sql
CASE expression
    WHEN value_1 THEN result_1
    WHEN value_2 THEN result_2
    ELSE result_default
END
```

Example:

```sql
SELECT
    status,
    CASE status
        WHEN 'pending' THEN 'Waiting'
        WHEN 'processing' THEN 'In Progress'
        WHEN 'completed' THEN 'Done'
        WHEN 'failed' THEN 'Error'
        ELSE 'Unknown'
    END AS status_label
FROM orders;
```

Use simple `CASE` when the decision is essentially a mapping.

Use searched `CASE` when the decision depends on predicates, ranges, or multiple columns.

| Requirement | Preferred form |
| --- | --- |
| Map one value to another | Simple `CASE` |
| Compare numeric ranges | Searched `CASE` |
| Check multiple columns | Searched `CASE` |
| Combine predicates with `AND` / `OR` | Searched `CASE` |
| Translate enum-like values | Simple `CASE` |

## First-Match Evaluation

`CASE` evaluates its conditions in order.

The first matching `WHEN` determines the result.

```sql
SELECT CASE
    WHEN amount >= 1000 THEN 'high'
    WHEN amount >= 500 THEN 'medium'
    ELSE 'low'
END AS risk_band
FROM payments;
```

For:

```text
amount = 1500
```

the first condition matches, so the result is:

```text
high
```

The second condition is not selected even though it is also logically true.

This makes condition ordering part of the correctness of the query.

## Overlapping Conditions

Consider:

```sql
CASE
    WHEN score >= 50 THEN 'pass'
    WHEN score >= 90 THEN 'excellent'
    ELSE 'fail'
END
```

The `score >= 90` branch is effectively unreachable because every score above `90` already satisfies `score >= 50`.

Correct:

```sql
CASE
    WHEN score >= 90 THEN 'excellent'
    WHEN score >= 50 THEN 'pass'
    ELSE 'fail'
END
```

A useful engineering practice is to review `CASE` branches for:

- Overlapping ranges.
- Unreachable conditions.
- Missing boundaries.
- Incorrect ordering.
- Unexpected `NULL` behavior.

## ELSE and Default Behavior

`ELSE` defines the fallback result:

```sql
CASE
    WHEN status = 'active' THEN 1
    WHEN status = 'suspended' THEN 2
    ELSE 0
END
```

If no `WHEN` matches and no `ELSE` exists, the result is `NULL`.

Therefore:

```sql
CASE
    WHEN status = 'active' THEN 'A'
END
```

is not equivalent to:

```sql
CASE
    WHEN status = 'active' THEN 'A'
    ELSE 'unknown'
END
```

For production queries, explicitly choosing the fallback is usually clearer than relying on implicit `NULL`.

## NULL in Conditional Logic

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

`NULL` comparisons normally produce `UNKNOWN`, not `TRUE`.

For example:

```sql
SELECT
    CASE
        WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
        ELSE 'complete'
    END
FROM orders;
```

If `shipped_at` is `NULL`, the comparison is not true, so the `ELSE` branch is selected.

If `NULL` means "not shipped", the logic should state that explicitly:

```sql
SELECT
    CASE
        WHEN shipped_at IS NULL THEN 'not shipped'
        WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
        ELSE 'shipped'
    END AS shipment_state
FROM orders;
```

This distinction is especially important in production data models where `NULL` represents "unknown", "not applicable", or "not yet populated" rather than a default value.

## Conditional Calculations

`CASE` is often used to calculate values conditionally.

For example:

```sql
SELECT
    order_id,
    CASE
        WHEN customer_type = 'enterprise'
            THEN total_amount * 0.90
        WHEN customer_type = 'premium'
            THEN total_amount * 0.95
        ELSE total_amount
    END AS discounted_amount
FROM orders;
```

The database calculates the result for each row.

This is useful for:

- Pricing calculations.
- Fee calculations.
- Score calculations.
- SLA measurements.
- Derived reporting fields.

Be careful with financial calculations. Use an appropriate exact numeric type such as `NUMERIC`/`DECIMAL` rather than relying on floating-point arithmetic.

## Conditional Aggregation

One of the most important uses of `CASE` is conditional aggregation.

For example:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_orders
FROM orders;
```

This produces multiple metrics from one scan of the logical input.

In PostgreSQL, the equivalent `FILTER` syntax can sometimes be clearer:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_orders
FROM orders;
```

`CASE` remains highly portable across SQL implementations.

## CASE with Aggregation and Ratios

Conditional aggregation can calculate operational metrics:

```sql
SELECT
    COUNT(*) AS total_requests,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors,
    SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors
FROM api_requests
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
```

A ratio can then be calculated carefully:

```sql
SELECT
    100.0 * SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0) AS server_error_percentage
FROM api_requests
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
```

`NULLIF` prevents division by zero.

## Conditional Logic in WHERE

Although `CASE` can appear in `WHERE`, it is often unnecessary.

Less direct:

```sql
SELECT *
FROM orders
WHERE CASE
    WHEN status = 'active' THEN 1
    ELSE 0
END = 1;
```

Prefer:

```sql
SELECT *
FROM orders
WHERE status = 'active';
```

The direct predicate is clearer and usually gives the optimizer a more straightforward expression to reason about.

Use `CASE` in `WHERE` when it genuinely expresses conditional predicate logic that cannot be stated more clearly using ordinary Boolean predicates.

## CASE in ORDER BY

`CASE` can implement business-specific sorting:

```sql
SELECT
    order_id,
    status,
    created_at
FROM orders
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'processing' THEN 3
        WHEN 'completed' THEN 4
        ELSE 5
    END,
    created_at ASC;
```

This allows the query to prioritize records according to domain rules rather than alphabetical status order.

A common backend use case is returning work items to an operations dashboard:

```text
failed
↓
pending
↓
processing
↓
completed
```

followed by a secondary sort such as creation time.

## CASE in UPDATE

`CASE` can perform different updates for different rows:

```sql
UPDATE orders
SET priority = CASE
    WHEN status = 'failed' THEN 1
    WHEN status = 'pending' THEN 2
    WHEN status = 'processing' THEN 3
    ELSE priority
END
WHERE status IN ('failed', 'pending', 'processing');
```

Here:

```text
WHERE → selects candidate rows
CASE  → determines new priority
```

This is useful for bulk transformations and migrations.

For large updates, consider transaction duration, locks, replication lag, WAL/redo generation, and index maintenance.

## CASE in INSERT

`CASE` can derive a value during insertion:

```sql
INSERT INTO customer_segments (
    customer_id,
    segment
)
SELECT
    customer_id,
    CASE
        WHEN lifetime_value >= 10000 THEN 'enterprise'
        WHEN lifetime_value >= 1000 THEN 'premium'
        ELSE 'standard'
    END
FROM customers;
```

This is useful when populating derived tables or materialized reporting structures.

## Conditional JOIN Logic

`CASE` can also participate in join expressions, although it should be used carefully.

Example:

```sql
SELECT
    o.order_id,
    r.rate
FROM orders AS o
JOIN shipping_rates AS r
    ON r.region = CASE
        WHEN o.country = 'US' THEN 'NA'
        WHEN o.country = 'CA' THEN 'NA'
        ELSE 'INTL'
    END;
```

This can be valid, but complex expressions in join predicates may make indexing and query optimization harder.

If the mapping is stable and data-driven, a mapping table can often be a better design:

```text
countries
    ↓
regions
    ↓
shipping_rates
```

This moves business mapping from hard-coded SQL into relational data.

## CASE and Data-Driven Rules

A short `CASE` is often appropriate:

```sql
CASE
    WHEN status = 'active' THEN 'A'
    WHEN status = 'inactive' THEN 'I'
    ELSE 'U'
END
```

A massive rule set is a design warning:

```sql
CASE
    WHEN ...
    WHEN ...
    WHEN ...
    -- dozens of additional rules
END
```

If business users or operations teams frequently change the mapping, consider storing the rules in tables.

For example:

```text
pricing_rules
-------------
rule_id
min_amount
max_amount
customer_type
discount_rate
priority
```

The database can then evaluate relational data rather than requiring a code deployment whenever a threshold changes.

## CASE Versus Application Logic

The decision about where conditional logic belongs should be deliberate.

| Logic | Often best location |
| --- | --- |
| Simple database classification | SQL |
| Aggregation-dependent classification | SQL |
| Data transformation during migration | SQL |
| Formatting database-derived categories | SQL or application |
| External API decision | Application/service |
| Complex workflow | Application/service |
| Frequently changing business rules | Often data-driven configuration |
| Security authorization | Explicit authorization layer plus database constraints where appropriate |

Do not move every business rule into SQL simply because SQL can express it.

Likewise, avoid pulling millions of rows into Python just to perform a transformation that the database can efficiently calculate.

## PostgreSQL Example with a Backend API

Suppose a FastAPI endpoint returns customer summaries:

```sql
SELECT
    customer_id,
    lifetime_value,
    CASE
        WHEN lifetime_value >= 10000 THEN 'enterprise'
        WHEN lifetime_value >= 1000 THEN 'premium'
        ELSE 'standard'
    END AS segment
FROM customers
WHERE is_active = TRUE;
```

The application receives already-classified rows:

```text
PostgreSQL
    ↓
filter active customers
    ↓
calculate segment
    ↓
return rows
    ↓
FastAPI
    ↓
serialize JSON
```

The application does not need to duplicate the segmentation algorithm.

This reduces the risk that different services implement slightly different versions of the same classification.

## Django ORM

Django exposes SQL `CASE` through `Case` and `When`.

For example:

```python
from django.db.models import Case, CharField, Value, When

customers = Customer.objects.annotate(
    segment=Case(
        When(lifetime_value__gte=10000, then=Value("enterprise")),
        When(lifetime_value__gte=1000, then=Value("premium")),
        default=Value("standard"),
        output_field=CharField(),
    )
)
```

The conditional logic is translated into SQL and evaluated by the database.

This is preferable to:

```python
for customer in customers:
    if customer.lifetime_value >= 10000:
        customer.segment = "enterprise"
```

when the operation can be expressed entirely as a database query.

The latter can cause unnecessary row retrieval and application-side processing.

## Performance Considerations

A `CASE` expression itself is usually inexpensive compared with large scans, joins, sorts, or aggregations.

However, performance depends on where and how it is used.

Potential concerns include:

- Complex expressions evaluated for many rows.
- Functions preventing effective index use.
- `CASE` inside join predicates.
- `CASE` inside filtering expressions.
- Large sorts caused by computed ordering.
- Repeatedly calculating expensive expressions.
- Very large bulk updates.

The most important optimization is usually to reduce the candidate row set before expensive computation.

Prefer:

```sql
SELECT
    CASE
        WHEN ...
        THEN ...
    END
FROM orders
WHERE created_at >= :cutoff;
```

over unnecessarily processing the entire table.

Use `EXPLAIN` to verify assumptions:

```sql
EXPLAIN
SELECT
    CASE
        WHEN status = 'failed' THEN 'urgent'
        ELSE 'normal'
    END AS priority
FROM orders
WHERE created_at >= :cutoff;
```

Do not optimize `CASE` syntax in isolation. Optimize the complete query plan.

## Indexing Considerations

A normal index generally cannot make an arbitrary computed `CASE` expression free to evaluate.

For example:

```sql
ORDER BY CASE
    WHEN status = 'failed' THEN 1
    WHEN status = 'pending' THEN 2
    ELSE 3
END;
```

may require a sort.

If this ordering is performance-critical and stable, database-specific options such as expression indexes or generated/stored columns may be appropriate.

For PostgreSQL, an expression index can support certain expressions:

```sql
CREATE INDEX idx_orders_priority_order
ON orders (
    CASE
        WHEN status = 'failed' THEN 1
        WHEN status = 'pending' THEN 2
        ELSE 3
    END
);
```

Whether the optimizer can use such an index depends on the complete query and ordering requirements.

Do not add expression indexes without measuring the workload. Every additional index increases storage and write overhead.

## Production Considerations

### Keep CASE Expressions Readable

Prefer:

```sql
CASE
    WHEN status = 'failed' THEN 'urgent'
    WHEN status = 'pending' THEN 'normal'
    ELSE 'low'
END
```

over deeply nested expressions that are difficult to review.

### Make Boundaries Explicit

For numeric rules, document the boundary through the conditions themselves:

```sql
CASE
    WHEN amount >= 10000 THEN 'enterprise'
    WHEN amount >= 1000 THEN 'premium'
    WHEN amount >= 0 THEN 'standard'
    ELSE 'invalid'
END
```

This makes negative or unexpected values visible.

### Consider Unknown Values

An `ELSE 'standard'` can accidentally hide corrupted or newly introduced values.

For state mappings, consider:

```sql
CASE status
    WHEN 'pending' THEN 'waiting'
    WHEN 'processing' THEN 'running'
    WHEN 'completed' THEN 'done'
    WHEN 'failed' THEN 'error'
    ELSE 'unknown'
END
```

This makes unexpected states observable instead of silently assigning a valid-looking category.

### Keep Domain Semantics Consistent

If the same classification is needed by:

- Django APIs.
- FastAPI services.
- Reporting queries.
- Kafka consumers.
- Celery jobs.

avoid independently implementing subtly different versions.

Where practical, centralize the rule or define a canonical source for it.

### Test Boundary Conditions

For:

```sql
CASE
    WHEN score >= 90 THEN 'A'
    WHEN score >= 80 THEN 'B'
    ELSE 'C'
END
```

test at least:

```text
89
80
90
91
NULL
```

Boundary-focused testing catches many conditional logic defects.

## Security Considerations

`CASE` is not an authorization mechanism.

For example:

```sql
SELECT
    CASE
        WHEN role = 'admin' THEN secret_value
        ELSE NULL
    END
FROM accounts;
```

should not be treated as a substitute for proper access control.

Authorization should be enforced at the appropriate service and database boundaries.

Also, `CASE` does not make dynamically constructed SQL safe.

Avoid string interpolation:

```python
query = f"""
SELECT CASE
    WHEN status = '{status}'
    THEN ...
END
"""
```

Use parameterized queries instead.

In Django, use ORM expressions or parameterized raw SQL. In other Python database libraries, use the driver's parameter binding mechanism.

## Common Mistakes

### Using CASE Where a Direct Predicate Is Better

Avoid:

```sql
WHERE CASE
    WHEN status = 'active' THEN 1
    ELSE 0
END = 1
```

Prefer:

```sql
WHERE status = 'active'
```

The direct predicate is easier to understand and generally gives the optimizer a clearer expression.

### Forgetting ELSE

This:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
END
```

returns `NULL` for every other status.

Use an explicit fallback when required:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 'disabled'
END
```

### Incorrect Condition Ordering

Avoid:

```sql
CASE
    WHEN amount >= 100 THEN 'qualified'
    WHEN amount >= 1000 THEN 'enterprise'
    ELSE 'standard'
END
```

because the enterprise branch is unreachable.

Prefer:

```sql
CASE
    WHEN amount >= 1000 THEN 'enterprise'
    WHEN amount >= 100 THEN 'qualified'
    ELSE 'standard'
END
```

### Ignoring NULL

This:

```sql
CASE
    WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
    ELSE 'complete'
END
```

does not distinguish `NULL` from a genuinely completed shipment.

If `NULL` has domain meaning:

```sql
CASE
    WHEN shipped_at IS NULL THEN 'not shipped'
    WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
    ELSE 'shipped'
END
```

### Building Huge CASE Expressions

A `CASE` with dozens or hundreds of hard-coded business rules becomes difficult to test and maintain.

Consider a mapping or rules table when the logic is data-driven.

### Duplicating Business Rules

If the same classification is independently implemented in:

- SQL.
- Django.
- FastAPI.
- Kafka consumers.
- Reporting jobs.

the system can eventually produce inconsistent answers.

Establish a clear owner for important domain rules.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| What does `CASE` return? | A value; it is an SQL expression |
| What happens when no `WHEN` matches and there is no `ELSE`? | The result is `NULL` |
| Which `WHEN` branch wins when multiple conditions match? | The first matching branch |
| What is the difference between simple and searched `CASE`? | Simple `CASE` compares one expression to values; searched `CASE` evaluates Boolean conditions |
| Does `CASE` itself filter rows? | No; `WHERE` determines which rows qualify |
| Why can `CASE` produce unexpected results with `NULL`? | SQL uses three-valued logic, so comparisons involving `NULL` usually evaluate to `UNKNOWN` |
| Should `CASE` replace ordinary predicates? | No; use direct predicates when they express the requirement more clearly |
| Can `CASE` be used with aggregate functions? | Yes; conditional aggregation is a common pattern |
| Can `CASE` be used in `ORDER BY`? | Yes; it can implement custom business ordering |
| Does `CASE` automatically improve query performance? | No; performance depends on the complete query plan and workload |
| Is `CASE` an authorization mechanism? | No; authorization requires explicit access-control enforcement |
| When should a large `CASE` be replaced with a table? | When the rules are numerous, data-driven, or frequently changed |

## Key Takeaways

- `CASE` is an SQL expression for deriving values from conditional logic and can be used across `SELECT`, `ORDER BY`, aggregation, `UPDATE`, and other expressions.
- Conditions are evaluated in order, so overlapping rules must be ordered deliberately and `ELSE` should be explicit when unmatched rows have meaningful behavior.
- Use SQL `CASE` for relational transformations, but avoid moving complex workflows or frequently changing rule sets into large hard-coded expressions.
- Optimize the complete query rather than the `CASE` expression alone; inspect filtering, joins, sorting, indexes, and execution plans.
- Treat `NULL`, boundary values, unexpected states, and duplicated business rules as first-class production concerns.