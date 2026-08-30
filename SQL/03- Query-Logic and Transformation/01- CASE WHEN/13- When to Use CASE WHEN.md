# 13- When to Use CASE WHEN

## Overview

`CASE WHEN` is SQL's primary conditional expression. It is useful when a query needs to derive a value from existing data based on one or more conditions.

The important engineering question is not whether SQL *can* express a condition. It is whether the condition should execute in the database and whether `CASE` is the clearest representation of that rule.

A good use of `CASE` usually has these characteristics:

- The decision is based primarily on database values.
- The result is needed as part of the query.
- The logic benefits from database-side filtering, grouping, aggregation, or ordering.
- Moving the calculation into the application would increase data transfer or duplicate logic.
- The expression remains understandable and maintainable.

```text
Database columns
       │
       ▼
   CASE WHEN
       │
       ├── derived value
       ├── conditional aggregate
       ├── custom sort key
       └── conditional classification
       │
       ▼
Application / API
```

## The Core Decision

Before adding `CASE`, ask:

> "Am I deriving data, or am I implementing application behavior?"

If the operation derives information directly from database state, SQL is often the right place.

If the operation coordinates behavior across services, performs side effects, or depends heavily on application state, application code is usually more appropriate.

| Requirement | Preferred location |
| --- | --- |
| Categorize rows | SQL `CASE` |
| Conditional aggregation | SQL `CASE` |
| Custom database ordering | SQL `CASE` |
| Conditional projection | SQL `CASE` |
| Filter records | SQL predicate |
| Replace `NULL` | `COALESCE` / `CASE` |
| Call another service | Application |
| Publish Kafka event | Application |
| Send email | Application |
| Complex workflow | Application/service layer |
| Presentation-only behavior | Application |
| Frequently changing rule data | Mapping/rule table |

## Use CASE for Derived Columns

One of the most common uses is deriving a value that does not physically exist as a column.

For example, an order table may contain:

```text
orders
├── id
├── total_amount
├── status
└── created_at
```

The application may need an order category:

```sql
SELECT
    id,
    total_amount,
    CASE
        WHEN total_amount >= 10000 THEN 'large'
        WHEN total_amount >= 1000 THEN 'medium'
        ELSE 'small'
    END AS order_category
FROM orders;
```

This is a strong use case because the classification is entirely derived from database values.

The application receives:

```text
id | total_amount | order_category
---|--------------|---------------
1  | 250          | small
2  | 2500         | medium
3  | 15000        | large
```

There is no need to duplicate the classification in Python.

## Use CASE for Conditional Aggregation

`CASE` becomes particularly valuable when calculating multiple metrics from the same dataset.

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(
        CASE
            WHEN status = 'completed' THEN 1
        END
    ) AS completed_orders,
    COUNT(
        CASE
            WHEN status = 'cancelled' THEN 1
        END
    ) AS cancelled_orders,
    SUM(
        CASE
            WHEN status = 'completed' THEN total_amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders;
```

This allows the database to scan and aggregate the data in one query.

In PostgreSQL, `FILTER` can often express conditional aggregates more directly:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
    COALESCE(
        SUM(total_amount) FILTER (WHERE status = 'completed'),
        0
    ) AS completed_revenue
FROM orders;
```

The general principle remains:

> Perform large-scale aggregation in the database rather than transferring raw rows to Python.

## Use CASE for Custom Ordering

Standard alphabetical or chronological ordering is not always the desired business order.

For example:

```text
failed
pending
processing
completed
```

may be the operational priority.

Use:

```sql
SELECT
    id,
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

This is especially useful for operational dashboards, queues, and administrative interfaces.

### Production Consideration

A `CASE` in `ORDER BY` can prevent the database from using a simple index ordering for that expression.

For a small result set this may not matter. For a high-volume query, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    status
FROM orders
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'processing' THEN 3
        ELSE 4
    END;
```

If the custom priority is a stable and heavily used concept, consider a persisted priority column, generated column, expression index, or another schema-level design appropriate to the database.

## Use CASE for Conditional Labels

Database-side labels are useful when the label represents a query-level classification.

```sql
SELECT
    id,
    CASE
        WHEN deleted_at IS NOT NULL THEN 'deleted'
        WHEN status = 'active' THEN 'active'
        WHEN status = 'suspended' THEN 'suspended'
        ELSE 'unknown'
    END AS lifecycle_state
FROM users;
```

This is often preferable to returning several raw fields and requiring every consumer to reconstruct the same state.

However, the precedence must be deliberate. If `deleted_at` takes priority over `status`, that should be explicit in the `CASE` ordering.

## Use CASE for Conditional Aggregation by Category

`CASE` can transform raw values into reporting buckets.

```sql
SELECT
    CASE
        WHEN total_amount < 1000 THEN 'under_1000'
        WHEN total_amount < 5000 THEN '1000_to_4999'
        WHEN total_amount < 10000 THEN '5000_to_9999'
        ELSE '10000_plus'
    END AS revenue_bucket,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY
    CASE
        WHEN total_amount < 1000 THEN 'under_1000'
        WHEN total_amount < 5000 THEN '1000_to_4999'
        WHEN total_amount < 10000 THEN '5000_to_9999'
        ELSE '10000_plus'
    END;
```

The database performs the classification and aggregation without sending every order to the application.

## Use CASE When It Reduces Data Transfer

Consider a reporting API that needs only counts.

Poor architecture:

```text
PostgreSQL
    │
    │ millions of rows
    ▼
Application
    │
    ├── classify
    ├── count
    └── aggregate
```

Better architecture:

```text
PostgreSQL
    │
    ├── classify
    ├── filter
    └── aggregate
    │
    │ small result set
    ▼
Application
```

For example:

```sql
SELECT
    CASE
        WHEN amount >= 10000 THEN 'large'
        ELSE 'normal'
    END AS category,
    COUNT(*) AS count
FROM payments
GROUP BY
    CASE
        WHEN amount >= 10000 THEN 'large'
        ELSE 'normal'
    END;
```

The application receives only the aggregated result.

This can reduce:

- Network traffic.
- Application memory usage.
- Python CPU consumption.
- Serialization overhead.
- Request latency.

## Do Not Use CASE When a Predicate Is Enough

A common anti-pattern is converting a condition into a numeric expression merely to filter rows.

Avoid:

```sql
SELECT *
FROM orders
WHERE
    CASE
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

The direct predicate communicates the intent more clearly and gives the optimizer a simpler expression to work with.

`CASE` is for deriving values. It should not replace straightforward predicates without a reason.

## Do Not Use CASE When COALESCE Is Clearer

If the only requirement is to select the first non-`NULL` value, `COALESCE` is generally more expressive.

Instead of:

```sql
CASE
    WHEN phone_number IS NOT NULL THEN phone_number
    ELSE email
END
```

use:

```sql
COALESCE(phone_number, email)
```

Use `CASE` when the decision involves actual conditional logic rather than simple null fallback.

## Do Not Use CASE for Complex Workflows

SQL `CASE` is an expression, not a general-purpose workflow engine.

Avoid turning a query into a representation of an application workflow:

```text
validate payment
    ↓
call fraud service
    ↓
reserve inventory
    ↓
charge customer
    ↓
publish event
    ↓
send notification
```

These operations require application/service orchestration.

A database query can determine a data-derived state, such as:

```sql
CASE
    WHEN payment_status = 'failed' THEN 'payment_failed'
    WHEN inventory_reserved = TRUE THEN 'ready'
    ELSE 'pending'
END
```

But executing the workflow based on that state belongs in application code.

## Use CASE with Database State

`CASE` is particularly appropriate when the database is already the authoritative source of state.

For example:

```sql
SELECT
    id,
    CASE
        WHEN shipped_at IS NULL THEN 'not_shipped'
        WHEN delivered_at IS NOT NULL THEN 'delivered'
        ELSE 'in_transit'
    END AS shipping_state
FROM shipments;
```

The database owns:

- `shipped_at`
- `delivered_at`

so deriving the current state during the query is natural.

## Use CASE with API Read Models

For read-heavy APIs, database-side derived fields can simplify response construction.

A Django application might use an annotation:

```python
from django.db.models import Case, CharField, Value, When

orders = Order.objects.annotate(
    size=Case(
        When(total_amount__gte=10_000, then=Value("large")),
        When(total_amount__gte=1_000, then=Value("medium")),
        default=Value("small"),
        output_field=CharField(),
    )
)
```

The database performs the conditional expression.

The serializer can then expose the annotated value without reproducing the classification.

This is particularly useful for:

- Admin interfaces.
- Reporting APIs.
- Search endpoints.
- Read models.
- Dashboard queries.

## Use CASE with Query-Time Permissions Carefully

`CASE` can conditionally project values:

```sql
SELECT
    id,
    CASE
        WHEN is_internal_user THEN salary
        ELSE NULL
    END AS salary
FROM employees;
```

But this should not be confused with authorization.

A `CASE` expression is not a replacement for access control.

Security-sensitive systems should ensure unauthorized records or columns are not exposed through the data-access layer merely because application code intends to hide them afterward.

## Use CASE for Stable Business Classifications

A stable rule such as:

```text
0–99       → low
100–999    → medium
1000+      → high
```

can be represented cleanly:

```sql
CASE
    WHEN score >= 1000 THEN 'high'
    WHEN score >= 100 THEN 'medium'
    ELSE 'low'
END
```

The ordering matters.

Conditions should normally be written from the most restrictive threshold to the least restrictive when ranges overlap.

For example:

```sql
CASE
    WHEN score >= 1000 THEN 'high'
    WHEN score >= 100 THEN 'medium'
    ELSE 'low'
END
```

not:

```sql
CASE
    WHEN score >= 100 THEN 'medium'
    WHEN score >= 1000 THEN 'high'
    ELSE 'low'
END
```

The second version never reaches the `score >= 1000` branch.

## Do Not Use CASE for Frequently Changing Rules Without a Plan

Hard-coded thresholds become difficult to maintain when business users frequently change them.

Avoid embedding hundreds of configuration values:

```sql
CASE
    WHEN ...
    WHEN ...
    WHEN ...
    WHEN ...
    WHEN ...
    ...
END
```

Consider a rule or mapping table when the logic is fundamentally data.

For example:

```text
risk_rules
├── rule_name
├── minimum_amount
├── maximum_amount
├── risk_level
└── priority
```

This allows rule changes to occur as data changes rather than requiring SQL code changes and deployments.

## Use CASE for Conditional UPDATEs

`CASE` can efficiently update different rows to different values in one statement.

```sql
UPDATE orders
SET priority = CASE
    WHEN status = 'failed' THEN 1
    WHEN total_amount >= 10000 THEN 2
    WHEN total_amount >= 1000 THEN 3
    ELSE 4
END
WHERE priority IS NULL;
```

This is useful for controlled bulk transformations.

### Production Considerations

Before executing a large update:

1. Verify the `WHERE` clause.
2. Estimate the affected row count.
3. Understand transaction and locking behavior.
4. Test the statement against representative data.
5. Consider batching for very large tables.
6. Monitor transaction duration and replication impact.

A `CASE` expression does not make a bulk update inherently safe.

## CASE and Indexes

`CASE` can affect index usage depending on where it appears.

A direct predicate:

```sql
WHERE status = 'active'
```

is generally easier to optimize using an index on `status`.

A transformed predicate:

```sql
WHERE
    CASE
        WHEN status = 'active' THEN 1
        ELSE 0
    END = 1
```

may make optimization more difficult.

For frequently queried derived expressions, database-specific options may include:

- Expression indexes.
- Generated columns.
- Functional indexes.
- Materialized views.
- Persisted classification columns.

For example, PostgreSQL supports expression indexes:

```sql
CREATE INDEX idx_orders_priority
ON orders (
    CASE
        WHEN status = 'failed' THEN 1
        WHEN status = 'pending' THEN 2
        ELSE 3
    END
);
```

Whether this is worthwhile depends on query frequency, table size, write volume, and the execution plan.

## Performance Heuristic

Use this practical decision sequence:

```text
Is the condition based on database data?
        │
       yes
        │
        ▼
Is the result needed by SQL itself?
        │
       yes
        │
        ▼
Use CASE / SQL expression
        │
       no
        │
        ▼
Would SQL reduce transferred data
or avoid duplicated logic?
        │
       yes
        │
        ▼
Consider CASE
        │
       no
        │
        ▼
Application logic may be clearer
```

Do not optimize based on the assumption that database CPU is always cheaper than application CPU. Measure the complete request path.

## Common Mistakes

### Overlapping Conditions

Incorrect:

```sql
CASE
    WHEN amount >= 100 THEN 'medium'
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

`amount = 5000` becomes `medium`.

Correct:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    WHEN amount >= 100 THEN 'medium'
    ELSE 'small'
END
```

### Missing ELSE

Without an `ELSE`, unmatched rows return `NULL`.

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
END
```

If that is not intentional, use:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 'disabled'
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

### Using CASE Instead of WHERE

Avoid turning a simple filter into a computed expression:

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

### Duplicating the Same Rule

If SQL says:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

while Python says:

```python
if amount > 1000:
    category = "large"
else:
    category = "small"
```

the boundary condition differs.

Centralize the rule where practical.

### Creating Unmaintainable CASE Expressions

A `CASE` containing dozens of branches may technically work while still being a poor engineering design.

Consider:

- A mapping table.
- A configuration table.
- A generated column.
- A database view.
- A domain service.

The correct choice depends on whether the logic is data, a derived query concern, or domain behavior.

## Production Checklist

Before introducing `CASE`, verify:

- Is the condition actually data-oriented?
- Is `CASE` clearer than a simpler SQL expression?
- Are conditions mutually exclusive or intentionally ordered?
- Is `NULL` behavior explicit?
- Is there an appropriate `ELSE`?
- Does the expression participate in `WHERE`, `GROUP BY`, or `ORDER BY`?
- Could a direct predicate be used instead?
- Could `COALESCE` express the requirement more clearly?
- Will the expression affect index usage?
- Is the query executed frequently enough to justify optimization?
- Is the logic duplicated elsewhere?
- Would a mapping table be more maintainable?
- Has the execution plan been checked for large datasets?

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| When should `CASE` be used? | For conditional value derivation inside SQL |
| Should `CASE` replace a simple `WHERE` predicate? | Usually no; use the direct predicate |
| Why is condition order important? | The first matching `WHEN` determines the result |
| What happens when no `WHEN` matches and there is no `ELSE`? | The result is `NULL` |
| When is `COALESCE` preferable? | When the requirement is simply first-non-`NULL` selection |
| Why use `CASE` for aggregation? | It enables conditional metrics to be computed in the database |
| Can `CASE` improve API performance? | Yes, when database-side computation reduces rows or payload transferred |
| Does `CASE` automatically use indexes? | No; expressions can affect index usability and must be evaluated through the execution plan |
| Should complex workflows be implemented with `CASE`? | No; orchestration belongs in the application/service layer |
| When should a mapping table replace a large `CASE`? | When rules are data-driven or change frequently |
| Is `CASE` an authorization mechanism? | No; authorization must be enforced separately |
| Is database-side logic always faster? | No; evaluate the complete workload and verify with measurement |

## Key Takeaways

- Use `CASE` when conditional logic naturally derives values from database state, especially for projections, aggregation, grouping, and custom ordering.
- Prefer direct predicates, `COALESCE`, and other simpler SQL constructs when they express the requirement more clearly.
- Treat condition ordering, `NULL` handling, and `ELSE` behavior as explicit parts of the query's contract.
- Avoid using `CASE` for complex workflows or frequently changing rule sets when application logic or data-driven configuration is more maintainable.
- For production queries, consider index usage, execution plans, data volume, network transfer, and whether the same business rule is duplicated elsewhere.