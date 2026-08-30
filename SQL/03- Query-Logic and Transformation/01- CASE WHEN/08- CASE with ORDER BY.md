# 08- CASE with ORDER BY

## Overview

`CASE` can be used inside `ORDER BY` to implement business-specific sorting rules that cannot be expressed by simply sorting a column ascending or descending.

This is especially useful when the desired order is semantic rather than lexical or numeric.

For example, an operational API may need orders displayed in this priority:

```text
failed
pending
processing
completed
cancelled
```

A normal:

```sql
ORDER BY status
```

does not guarantee that business order.

`CASE` allows the application to explicitly define the ranking:

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
        WHEN 'cancelled' THEN 5
        ELSE 6
    END,
    created_at DESC;
```

The first expression determines business priority. The second expression provides deterministic ordering within each priority.

## Why Use CASE in ORDER BY

SQL's normal ordering operators work well when the desired order corresponds directly to a stored value:

```sql
ORDER BY created_at DESC;
```

But production systems frequently require rules such as:

- Show urgent records first.
- Show failed jobs before retrying jobs.
- Put active subscriptions before inactive ones.
- Sort customers by a derived risk category.
- Put records with missing values last.
- Sort API results according to a user-selected business priority.
- Apply different sort directions to different columns.

`CASE` converts those business rules into sortable values.

Conceptually:

```text
Raw row
   ↓
CASE evaluates business rule
   ↓
Derived sort key
   ↓
ORDER BY compares sort keys
   ↓
Final ordered result
```

## Basic Syntax

A searched `CASE` can be used directly in `ORDER BY`:

```sql
SELECT
    order_id,
    status
FROM orders
ORDER BY
    CASE
        WHEN status = 'failed' THEN 1
        WHEN status = 'pending' THEN 2
        WHEN status = 'completed' THEN 3
        ELSE 4
    END;
```

A simple `CASE` is convenient when comparing one expression against several known values:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'completed' THEN 3
        ELSE 4
    END;
```

Both forms can express the same rule.

Use searched `CASE` when the conditions involve ranges or multiple columns:

```sql
ORDER BY
    CASE
        WHEN status = 'failed' AND retry_count > 3 THEN 1
        WHEN status = 'failed' THEN 2
        WHEN status = 'pending' THEN 3
        ELSE 4
    END;
```

## Custom Business Ordering

A common use case is sorting categorical values according to domain priority.

```sql
SELECT
    ticket_id,
    priority,
    created_at
FROM support_tickets
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END,
    created_at ASC;
```

The result is ordered by:

```text
critical
high
medium
low
unknown
```

This is preferable to relying on:

- Alphabetical ordering
- Enum implementation values
- Database-specific enum ordering
- Application-side sorting

when the ordering itself is a business rule.

## CASE with Secondary Sorting

A `CASE` expression often defines only the primary priority.

You should usually add a secondary sort when multiple rows can have the same priority.

```sql
SELECT
    ticket_id,
    priority,
    created_at
FROM support_tickets
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END,
    created_at ASC,
    ticket_id ASC;
```

The ordering is:

```text
business priority
    ↓
creation time
    ↓
unique identifier
```

The final unique tie-breaker is valuable for stable pagination.

## Deterministic Ordering

A query without a complete ordering specification should not be assumed to return tied rows in a stable order.

For example:

```sql
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        ELSE 3
    END;
```

Multiple rows may have the same sort key.

The database is free to return those tied rows in an order that can change between executions, query plans, or database versions.

For API pagination, prefer:

```sql
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        ELSE 3
    END,
    created_at DESC,
    ticket_id DESC;
```

A deterministic tie-breaker becomes particularly important when using:

```text
LIMIT / OFFSET
```

or keyset/cursor pagination.

## CASE for NULL Ordering

Different database engines have different default ordering behavior for `NULL`.

Instead of relying on defaults, make the desired behavior explicit when portability or correctness matters.

For example, to place missing values last:

```sql
SELECT
    user_id,
    last_login_at
FROM users
ORDER BY
    CASE
        WHEN last_login_at IS NULL THEN 1
        ELSE 0
    END,
    last_login_at DESC;
```

The first sort key produces:

```text
non-NULL → 0
NULL     → 1
```

so non-NULL values appear first.

In PostgreSQL, `NULLS FIRST` and `NULLS LAST` are usually clearer:

```sql
SELECT
    user_id,
    last_login_at
FROM users
ORDER BY
    last_login_at DESC NULLS LAST;
```

Prefer the native syntax when the target database supports it and portability is not a requirement.

## CASE with ASC and DESC

`CASE` can control which rows receive priority, while normal `ASC` or `DESC` controls the ordering inside each category.

```sql
SELECT
    order_id,
    status,
    created_at
FROM orders
ORDER BY
    CASE
        WHEN status = 'failed' THEN 1
        WHEN status = 'pending' THEN 2
        ELSE 3
    END,
    created_at DESC;
```

This means:

1. Failed orders first.
2. Pending orders second.
3. All other orders afterward.
4. Within each group, newest orders first.

## Different Sort Directions

Sometimes different categories need different sort directions.

For example:

- High-priority orders: oldest first.
- Normal orders: newest first.

A single `CASE` cannot simply return a date and magically change its direction for each row. Separate sort expressions are clearer:

```sql
SELECT
    order_id,
    priority,
    created_at
FROM orders
ORDER BY
    CASE
        WHEN priority = 'high' THEN 0
        ELSE 1
    END,
    CASE
        WHEN priority = 'high' THEN created_at
    END ASC,
    CASE
        WHEN priority <> 'high' THEN created_at
    END DESC;
```

This pattern is more complex, so verify that the resulting ordering exactly matches the business requirement.

An alternative is to normalize the ordering requirement into a common sort key before the query reaches SQL.

## CASE with Multiple Columns

A searched `CASE` can inspect several columns.

```sql
SELECT
    job_id,
    status,
    retry_count,
    scheduled_at
FROM jobs
ORDER BY
    CASE
        WHEN status = 'failed' AND retry_count >= 3 THEN 1
        WHEN status = 'failed' THEN 2
        WHEN status = 'retrying' THEN 3
        WHEN status = 'queued' THEN 4
        ELSE 5
    END,
    scheduled_at ASC,
    job_id ASC;
```

This is useful for operational queues where priority depends on multiple attributes.

However, once the classification becomes large, consider whether the priority belongs in the data model rather than being reconstructed on every query.

## CASE and Boolean Conditions

Some databases allow boolean expressions directly in ordering.

For example, PostgreSQL supports:

```sql
ORDER BY
    (status = 'failed') DESC,
    created_at DESC;
```

This can be concise, but it is less expressive when several ordered categories exist.

For multiple business priorities:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'processing' THEN 3
        ELSE 4
    END;
```

is usually clearer.

Prefer the expression that makes the business rule easiest to understand and maintain.

## CASE with Calculated Priority

A derived priority can combine several conditions:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    created_at
FROM orders
ORDER BY
    CASE
        WHEN amount >= 10000 THEN 1
        WHEN created_at < CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 2
        ELSE 3
    END,
    created_at ASC;
```

The database evaluates the `CASE` for each candidate row and uses the resulting value as the sort key.

Be careful with overlapping conditions. An order older than 24 hours and worth more than 10,000 matches both conditions, but only the first matching branch is selected.

## CASE and Pagination

Ordering becomes more important when the query is paginated.

Consider:

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
        ELSE 3
    END,
    created_at DESC,
    order_id DESC
LIMIT 50;
```

For offset pagination:

```sql
LIMIT 50 OFFSET 100;
```

the database still needs to determine the ordered result before skipping rows. Large offsets can become expensive.

With cursor-based pagination, the cursor must represent the complete ordering state.

If the ordering is:

```text
priority_rank
created_at
order_id
```

the cursor generally needs enough information to identify the position across all three dimensions.

A cursor containing only `created_at` is not sufficient if `priority_rank` can change the ordering.

## CASE and Keyset Pagination

For a complex ordering expression, keyset pagination can become difficult because the cursor predicate must reproduce the same ordering semantics.

Conceptually:

```text
ORDER BY
    priority_rank,
    created_at DESC,
    order_id DESC
```

requires a corresponding "after cursor" condition based on:

```text
priority_rank
created_at
order_id
```

For example:

```sql
WHERE
    priority_rank > :priority_rank
    OR (
        priority_rank = :priority_rank
        AND created_at < :created_at
    )
    OR (
        priority_rank = :priority_rank
        AND created_at = :created_at
        AND order_id < :order_id
    )
```

If `priority_rank` is computed by `CASE`, this can become verbose.

For heavily used APIs, consider materializing a stable priority column if the priority is part of the persistent domain model.

## CASE with Expressions and Aliases

A derived sort key can sometimes be exposed as a `SELECT` alias:

```sql
SELECT
    order_id,
    status,
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        ELSE 3
    END AS priority_rank
FROM orders
ORDER BY priority_rank;
```

This is often cleaner than repeating the expression.

If the expression is needed only for sorting, you may not need to expose it:

```sql
SELECT
    order_id,
    status
FROM orders
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        ELSE 3
    END;
```

Use a derived table when the same computed value needs to be reused in several query clauses and dialect-specific alias behavior becomes problematic.

## Performance Considerations

`ORDER BY CASE` can require the database to compute a sort key for rows participating in the query.

For example:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'completed' THEN 3
        ELSE 4
    END;
```

An ordinary index on:

```sql
status
```

does not necessarily provide the exact ordering required by the `CASE`.

The optimizer may need to:

```text
Scan qualifying rows
        ↓
Evaluate CASE
        ↓
Sort by derived value
        ↓
Return rows
```

For large datasets, inspect the plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    order_id,
    status,
    created_at
FROM orders
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'completed' THEN 3
        ELSE 4
    END,
    created_at DESC
LIMIT 100;
```

Do not optimize based solely on the presence of a `CASE`. Measure the actual query.

## Expression Indexes and Generated Values

If a particular derived ordering is used frequently, database-specific features may help.

For PostgreSQL, an expression index can sometimes support an expression used for ordering:

```sql
CREATE INDEX idx_orders_priority_rank
ON orders (
    (
        CASE status
            WHEN 'failed' THEN 1
            WHEN 'pending' THEN 2
            WHEN 'completed' THEN 3
            ELSE 4
        END
    )
);
```

Whether this improves the complete query depends on the rest of the ordering, filtering conditions, cardinality, and query plan.

If the priority is a genuine domain attribute, a stored column may be more maintainable:

```text
status        priority_rank
-----------   -------------
failed        1
pending       2
processing    3
completed     4
```

Do not add a generated or indexed sort key merely to optimize one query. Validate the workload first.

## Production API Example

Suppose a FastAPI endpoint exposes:

```text
GET /orders?sort=priority
```

The API may need to return:

```text
failed
pending
processing
completed
```

A safe implementation should not interpolate the user-provided sort parameter directly into SQL.

Instead, map allowed API values to predefined query expressions.

Conceptually:

```python
SORT_OPTIONS = {
    "priority": "priority",
    "newest": "newest",
}
```

Then construct the query using trusted application-controlled expressions or ORM constructs.

Never do:

```python
query = f"""
    SELECT *
    FROM orders
    ORDER BY {request.query_params["sort"]}
"""
```

A user-controlled `ORDER BY` clause can become an SQL injection vector.

The database should receive only values and identifiers that have been explicitly validated and allowlisted.

## Django ORM Example

Django can express conditional ordering using `Case` and `When`:

```python
from django.db.models import Case, IntegerField, Value, When

orders = (
    Order.objects
    .annotate(
        priority_rank=Case(
            When(status="failed", then=Value(1)),
            When(status="pending", then=Value(2)),
            When(status="processing", then=Value(3)),
            When(status="completed", then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    )
    .order_by("priority_rank", "-created_at", "-id")
)
```

This produces the same conceptual structure:

```text
CASE → priority_rank
             ↓
ORDER BY priority_rank
             ↓
created_at DESC
             ↓
id DESC
```

The generated SQL should still be inspected for performance-sensitive endpoints.

## Operational Considerations

For production APIs, custom ordering should be treated as part of the API contract.

Document:

- Allowed sort options.
- Default ordering.
- Tie-breaking behavior.
- NULL behavior.
- Pagination semantics.
- Whether ordering can change as records are updated.

A useful API contract might define:

```text
sort=priority
    failed → pending → processing → completed

sort=newest
    created_at DESC

sort=oldest
    created_at ASC
```

Avoid exposing arbitrary SQL expressions as an API feature.

## Common Mistakes

### Relying on Alphabetical Ordering

This:

```sql
ORDER BY status;
```

does not mean:

```text
pending
processing
failed
completed
```

unless the database's lexical order happens to match the business requirement.

Use an explicit ranking.

### Forgetting ELSE

This:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
    END;
```

returns `NULL` for every unhandled status.

Depending on the database and sort direction, those rows may appear at an unexpected position.

Prefer:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        ELSE 3
    END;
```

### Assuming Ties Are Stable

This:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        ELSE 2
    END;
```

does not define the order among rows with the same status.

For stable API results:

```sql
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        ELSE 2
    END,
    created_at DESC,
    order_id DESC;
```

### Using CASE When Native NULL Ordering Is Clearer

In PostgreSQL:

```sql
ORDER BY last_login_at DESC NULLS LAST;
```

is clearer than:

```sql
ORDER BY
    CASE
        WHEN last_login_at IS NULL THEN 1
        ELSE 0
    END,
    last_login_at DESC;
```

Use `CASE` when it expresses a genuine custom rule.

### Putting Conditions in the Wrong Order

Because `CASE` stops at the first matching branch:

```sql
CASE
    WHEN amount >= 100 THEN 'medium'
    WHEN amount >= 1000 THEN 'high'
    ELSE 'low'
END
```

never returns `'high'`.

Correct:

```sql
CASE
    WHEN amount >= 1000 THEN 'high'
    WHEN amount >= 100 THEN 'medium'
    ELSE 'low'
END
```

### Sorting in Application Code Unnecessarily

Fetching thousands of rows into Python and then sorting them:

```python
orders = list(Order.objects.filter(...))
orders.sort(key=...)
```

can waste memory, increase network transfer, and break database-level pagination.

If the ordering can be expressed safely in SQL, let the database perform it.

### Ignoring Pagination Stability

A custom ordering without a unique tie-breaker can cause duplicate or missing records across pages.

For APIs, prefer:

```sql
ORDER BY
    priority_rank,
    created_at DESC,
    id DESC;
```

and design the cursor around the complete ordering tuple when using keyset pagination.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Why use `CASE` in `ORDER BY`? | To create a custom sort key from business rules |
| Does `CASE` modify the stored data? | No; it produces a value used by the query |
| What happens when no `WHEN` matches and there is no `ELSE`? | The expression returns `NULL` |
| Does `ORDER BY priority` guarantee business priority? | Only if the stored value's ordering represents that business rule |
| Why add a unique tie-breaker? | To make result ordering deterministic, especially for pagination |
| Can `CASE` inspect multiple columns? | Yes; searched `CASE` can evaluate arbitrary boolean conditions |
| Does an index on `status` automatically optimize `ORDER BY CASE`? | No; the derived ordering may still require expression evaluation and sorting |
| Is application-side sorting preferable? | Usually not for database-sized result sets; SQL ordering preserves database-side filtering and pagination |
| Is `CASE` always the best way to handle NULL ordering? | No; database-native `NULLS FIRST/LAST` may be clearer |
| Why does `CASE` branch order matter? | The first matching `WHEN` determines the result |
| Can user input be placed directly into `ORDER BY`? | No; validate and allowlist sort options to prevent SQL injection |
| What does a cursor need for custom ordering? | Enough state to represent the complete ordering tuple, not merely one visible column |

## Key Takeaways

- `CASE` in `ORDER BY` converts business-specific priority rules into explicit sort keys.
- Always define a sensible `ELSE` and order overlapping conditions carefully because the first matching `WHEN` wins.
- Add deterministic secondary and unique tie-breakers when custom ordering is used with production APIs or pagination.
- Measure `ORDER BY CASE` with execution plans; frequent expensive orderings may justify expression indexes, generated values, or a persistent priority field.
- Never interpolate untrusted sort parameters into SQL; expose a small allowlist of supported application-level sort options.