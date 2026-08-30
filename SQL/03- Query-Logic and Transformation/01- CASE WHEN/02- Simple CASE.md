# 02- Simple CASE

## Overview

A **simple `CASE` expression** compares one expression against a sequence of possible values and returns the result associated with the first match.

It is the concise form of `CASE` for equality-based mappings:

```sql
CASE expression
    WHEN value_1 THEN result_1
    WHEN value_2 THEN result_2
    ELSE default_result
END
```

For example:

```sql
SELECT
    order_id,
    CASE status
        WHEN 'pending' THEN 'awaiting_payment'
        WHEN 'paid' THEN 'processing'
        WHEN 'shipped' THEN 'in_transit'
        WHEN 'cancelled' THEN 'inactive'
        ELSE 'unknown'
    END AS normalized_status
FROM orders;
```

Simple `CASE` is particularly useful when a single column or expression has a finite set of known values that must be translated into another representation.

It should not be confused with searched `CASE`. Simple `CASE` is designed around comparing one expression to values; searched `CASE` is designed around arbitrary boolean conditions.

---

## Syntax

The general syntax is:

```sql
CASE expression
    WHEN comparison_value_1 THEN result_1
    WHEN comparison_value_2 THEN result_2
    WHEN comparison_value_3 THEN result_3
    ELSE default_result
END
```

For example:

```sql
SELECT
    CASE status
        WHEN 'active' THEN 'enabled'
        WHEN 'suspended' THEN 'blocked'
        WHEN 'deleted' THEN 'removed'
        ELSE 'unknown'
    END AS account_state
FROM accounts;
```

The database conceptually performs the following process for each row:

```text
Evaluate expression
       |
       v
Compare with first WHEN value
       |
   Match? ---- yes ----> Return THEN result
       |
       no
       v
Compare with next WHEN value
       |
      ...
       |
       v
No match
       |
       v
Return ELSE result
       |
       |
       v
No ELSE -> NULL
```

The comparison is equality-based. If the requirement involves ranges, inequalities, multiple predicates, or more complex boolean logic, searched `CASE` is usually the appropriate form.

---

## How Simple CASE Works

Consider:

```sql
SELECT
    CASE status
        WHEN 'pending' THEN 'waiting'
        WHEN 'paid' THEN 'processing'
        WHEN 'shipped' THEN 'delivered'
        ELSE 'unknown'
    END AS state
FROM orders;
```

For a row where:

```text
status = 'paid'
```

the database compares `status` with the `WHEN` values until it finds the matching branch:

```text
status = 'paid'

'pending'  -> no
'paid'     -> yes

result = 'processing'
```

The result is one value for that row.

The important distinction is that the expression after `CASE` is evaluated once conceptually as the value being compared, while each `WHEN` supplies a comparison value.

---

## Simple CASE vs Searched CASE

The two forms can sometimes express the same rule.

### Simple CASE

```sql
CASE status
    WHEN 'pending' THEN 'waiting'
    WHEN 'paid' THEN 'processing'
    WHEN 'failed' THEN 'error'
    ELSE 'unknown'
END
```

### Searched CASE

```sql
CASE
    WHEN status = 'pending' THEN 'waiting'
    WHEN status = 'paid' THEN 'processing'
    WHEN status = 'failed' THEN 'error'
    ELSE 'unknown'
END
```

Both are equality-based here.

Simple `CASE` is usually more readable because the expression being classified is obvious.

| Requirement | Preferred form |
| --- | --- |
| Map one column to fixed values | Simple `CASE` |
| Check ranges | Searched `CASE` |
| Check multiple columns | Searched `CASE` |
| Use `>`, `<`, `>=`, `<=` | Searched `CASE` |
| Check `IS NULL` | Searched `CASE` |
| Equality mapping | Simple `CASE` |

---

## Mapping Enumerated Values

One of the strongest use cases is converting database state values into another vocabulary.

```sql
SELECT
    payment_id,
    CASE status
        WHEN 'authorized' THEN 'pending_capture'
        WHEN 'captured' THEN 'successful'
        WHEN 'failed' THEN 'failed'
        WHEN 'refunded' THEN 'refunded'
        ELSE 'unknown'
    END AS api_status
FROM payments;
```

This is useful when an internal schema has more detailed states than an external API needs to expose.

For example:

```text
Database state     API state
---------------    ----------------
authorized        pending_capture
captured          successful
failed            failed
refunded          refunded
```

The transformation can happen at the database boundary instead of requiring application code to perform another mapping after retrieving the rows.

---

## Using ELSE

`ELSE` defines the fallback value when no `WHEN` value matches.

```sql
SELECT
    CASE status
        WHEN 'active' THEN 'enabled'
        WHEN 'suspended' THEN 'blocked'
        ELSE 'unknown'
    END AS state
FROM accounts;
```

If `status = 'pending'`, neither `WHEN` matches, so the result is:

```text
unknown
```

If `ELSE` is omitted:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    WHEN 'suspended' THEN 'blocked'
END
```

an unmatched value produces `NULL`.

For production classification, an explicit `ELSE` is usually safer because new or unexpected states do not silently become `NULL`.

---

## Ordering of WHEN Clauses

Although simple `CASE` normally maps discrete values, the order of `WHEN` clauses still matters when multiple branches could be considered equivalent or when expressions have database-specific comparison behavior.

For ordinary exact mappings:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    WHEN 'inactive' THEN 'disabled'
    ELSE 'unknown'
END
```

each status normally maps to one branch.

However, when the requirement starts becoming conditional rather than equality-based, switch to searched `CASE` rather than trying to force the logic into simple `CASE`.

For example, this belongs in searched `CASE`:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

Do not sacrifice clarity merely to keep the simple syntax.

---

## Simple CASE and NULL

`NULL` is a particularly important edge case.

This does **not** provide a reliable way to match `NULL`:

```sql
CASE status
    WHEN NULL THEN 'missing'
    WHEN 'active' THEN 'enabled'
    ELSE 'unknown'
END
```

The reason is SQL's three-valued logic: `NULL` does not compare equal to `NULL` using ordinary equality semantics.

If `NULL` needs its own branch, use searched `CASE`:

```sql
CASE
    WHEN status IS NULL THEN 'missing'
    WHEN status = 'active' THEN 'enabled'
    ELSE 'unknown'
END
```

This is one of the most important distinctions between simple and searched `CASE`.

### Practical Rule

Use:

```sql
CASE column
    WHEN 'value' THEN ...
END
```

for ordinary equality mappings.

Use:

```sql
CASE
    WHEN column IS NULL THEN ...
    WHEN column = 'value' THEN ...
END
```

when `NULL` has explicit domain meaning.

---

## Simple CASE in SELECT

The most common placement is `SELECT`.

```sql
SELECT
    customer_id,
    status,
    CASE status
        WHEN 'trialing' THEN 'trial'
        WHEN 'active' THEN 'customer'
        WHEN 'past_due' THEN 'attention_required'
        WHEN 'cancelled' THEN 'inactive'
        ELSE 'unknown'
    END AS customer_state
FROM subscriptions;
```

The source column remains unchanged. The `CASE` expression creates a derived value.

This is useful for:

- API projections
- Reporting
- Operational dashboards
- Data exports
- Read models
- Analytics queries

---

## Simple CASE in ORDER BY

A simple `CASE` can define a custom ordering for discrete values.

```sql
SELECT
    ticket_id,
    priority
FROM support_tickets
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END;
```

The numeric result is used only for ordering.

This is useful when the lexical order of values does not represent business priority.

For example:

```text
critical
high
medium
low
```

should not be sorted alphabetically.

---

## Simple CASE in GROUP BY

Simple `CASE` can normalize discrete values into reporting groups.

```sql
SELECT
    CASE status
        WHEN 'paid' THEN 'successful'
        WHEN 'captured' THEN 'successful'
        WHEN 'failed' THEN 'unsuccessful'
        WHEN 'declined' THEN 'unsuccessful'
        ELSE 'other'
    END AS payment_group,
    COUNT(*) AS payment_count
FROM payments
GROUP BY
    CASE status
        WHEN 'paid' THEN 'successful'
        WHEN 'captured' THEN 'successful'
        WHEN 'failed' THEN 'unsuccessful'
        WHEN 'declined' THEN 'unsuccessful'
        ELSE 'other'
    END;
```

Multiple raw states are mapped into a smaller set of business categories.

For frequently reused transformations, avoid copying the same long expression across many queries. Consider a view, generated/materialized representation where appropriate, or a reference table depending on the domain.

---

## Simple CASE with Aggregates

Simple `CASE` can be used for conditional aggregation when the condition is based on discrete values.

```sql
SELECT
    SUM(
        CASE status
            WHEN 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders;
```

Another example:

```sql
SELECT
    SUM(
        CASE status
            WHEN 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_count,
    SUM(
        CASE status
            WHEN 'cancelled' THEN 1
            ELSE 0
        END
    ) AS cancelled_count
FROM orders;
```

For PostgreSQL, equivalent `FILTER` syntax can sometimes be clearer:

```sql
SELECT
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_count
FROM orders;
```

`CASE` remains useful when database portability matters.

---

## Simple CASE in UPDATE

A simple `CASE` can transform one set of discrete values into another during data migrations.

```sql
UPDATE orders
SET normalized_status = CASE status
    WHEN 'paid' THEN 'processing'
    WHEN 'shipped' THEN 'in_transit'
    WHEN 'delivered' THEN 'completed'
    WHEN 'cancelled' THEN 'inactive'
    ELSE 'unknown'
END;
```

For large tables, the expression is only one part of the migration problem.

Consider:

- Lock duration
- Transaction size
- Replication lag
- WAL/binlog generation
- Database I/O
- Application traffic
- Rollback strategy
- Batch processing

For a large production table, a migration may need to process rows incrementally rather than performing one unbounded update.

---

## Simple CASE with Numeric Codes

Legacy systems sometimes store compact numeric codes:

```text
1 = pending
2 = active
3 = suspended
4 = deleted
```

A simple `CASE` can translate them:

```sql
SELECT
    user_id,
    CASE account_state
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'active'
        WHEN 3 THEN 'suspended'
        WHEN 4 THEN 'deleted'
        ELSE 'unknown'
    END AS state
FROM users;
```

This can be useful during migrations or integration with legacy systems.

However, if the mapping is business-critical and frequently reused, a reference table can be more maintainable than repeating numeric mappings throughout application queries.

---

## CASE with Expressions

The expression after `CASE` does not have to be a simple column.

For example:

```sql
SELECT
    CASE LOWER(status)
        WHEN 'active' THEN 'enabled'
        WHEN 'suspended' THEN 'blocked'
        ELSE 'unknown'
    END AS state
FROM accounts;
```

Another example:

```sql
SELECT
    CASE EXTRACT(MONTH FROM created_at)
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        ELSE 'other'
    END AS month_group
FROM orders;
```

Be careful with functions applied to columns in large queries. The transformation may add CPU work and, when used in predicates or joins, can affect index usability.

---

## Result Data Types

The `THEN` and `ELSE` expressions should resolve to compatible data types.

Good:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    WHEN 'inactive' THEN 'disabled'
    ELSE 'unknown'
END
```

Potentially problematic:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    ELSE 0
END
```

Different database engines have different type-resolution rules and may attempt implicit conversions or reject the expression.

Prefer explicit, consistent result types.

For example:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    ELSE 'unknown'
END
```

is unambiguous.

---

## Simple CASE and API Design

A database may contain internal states that should not be exposed directly by an API.

For example:

```text
Database:

authorized
partially_captured
captured
capture_failed
refunded
```

An API might intentionally expose:

```text
pending
successful
failed
refunded
```

A simple `CASE` can perform the projection:

```sql
SELECT
    payment_id,
    CASE status
        WHEN 'authorized' THEN 'pending'
        WHEN 'partially_captured' THEN 'successful'
        WHEN 'captured' THEN 'successful'
        WHEN 'capture_failed' THEN 'failed'
        WHEN 'refunded' THEN 'refunded'
        ELSE 'unknown'
    END AS api_status
FROM payments;
```

This is useful when the query is specifically an API read projection.

However, do not confuse an API projection with the authoritative domain model. If the mapping is shared across REST, gRPC, Kafka events, background workers, and multiple services, it may deserve a centralized domain representation rather than being independently implemented in SQL.

---

## Simple CASE and Django

Django supports SQL `CASE` expressions through conditional expressions.

A simple SQL expression such as:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
    WHEN 'suspended' THEN 'blocked'
    ELSE 'unknown'
END
```

can be represented with Django's `Case` and `When` constructs.

In practice, Django commonly expresses the equality checks explicitly:

```python
from django.db.models import Case, CharField, Value, When

accounts = Account.objects.annotate(
    state_label=Case(
        When(status="active", then=Value("enabled")),
        When(status="suspended", then=Value("blocked")),
        default=Value("unknown"),
        output_field=CharField(),
    )
)
```

The ORM abstraction is not identical to writing simple `CASE` manually, but the database performs the conditional transformation.

For performance-sensitive ORM queries, inspect generated SQL and the execution plan instead of assuming that an ORM expression is free.

---

## Simple CASE and Reporting

Simple `CASE` is particularly effective for turning low-cardinality state values into reporting categories.

Suppose an order system contains:

```text
pending
paid
processing
shipped
delivered
cancelled
failed
```

A report could group them:

```sql
SELECT
    CASE status
        WHEN 'pending' THEN 'open'
        WHEN 'paid' THEN 'open'
        WHEN 'processing' THEN 'open'
        WHEN 'shipped' THEN 'fulfilled'
        WHEN 'delivered' THEN 'fulfilled'
        WHEN 'cancelled' THEN 'closed'
        WHEN 'failed' THEN 'closed'
        ELSE 'unknown'
    END AS lifecycle_group,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE status
        WHEN 'pending' THEN 'open'
        WHEN 'paid' THEN 'open'
        WHEN 'processing' THEN 'open'
        WHEN 'shipped' THEN 'fulfilled'
        WHEN 'delivered' THEN 'fulfilled'
        WHEN 'cancelled' THEN 'closed'
        WHEN 'failed' THEN 'closed'
        ELSE 'unknown'
    END;
```

This is straightforward for small, stable mappings.

If the mapping changes frequently, hard-coding it in every reporting query becomes an operational liability.

---

## When Simple CASE Is the Right Choice

Use simple `CASE` when:

- One expression is being compared against discrete values.
- The mapping is easy to enumerate.
- The values have low or moderate cardinality.
- The transformation is local to a query or projection.
- Readability improves compared with repeated equality predicates.

Example:

```sql
CASE country_code
    WHEN 'IN' THEN 'India'
    WHEN 'US' THEN 'United States'
    WHEN 'GB' THEN 'United Kingdom'
    ELSE 'Other'
END
```

This is clearer than:

```sql
CASE
    WHEN country_code = 'IN' THEN 'India'
    WHEN country_code = 'US' THEN 'United States'
    WHEN country_code = 'GB' THEN 'United Kingdom'
    ELSE 'Other'
END
```

Both are valid, but the simple form communicates the mapping more directly.

---

## When to Use Searched CASE Instead

Switch to searched `CASE` when the conditions are not simple equality comparisons.

For ranges:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

For multiple columns:

```sql
CASE
    WHEN status = 'active' AND verified = TRUE THEN 'trusted'
    WHEN status = 'active' THEN 'unverified'
    ELSE 'inactive'
END
```

For `NULL`:

```sql
CASE
    WHEN shipped_at IS NULL THEN 'not_shipped'
    ELSE 'shipped'
END
```

For date conditions:

```sql
CASE
    WHEN created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
        THEN 'old'
    ELSE 'recent'
END
```

Do not force these requirements into simple `CASE`.

---

## Simple CASE vs Lookup Tables

A simple mapping can be perfectly reasonable:

```sql
CASE status
    WHEN 'P' THEN 'pending'
    WHEN 'A' THEN 'active'
    WHEN 'S' THEN 'suspended'
    ELSE 'unknown'
END
```

But a reference table may be a better design when the mapping is:

- Frequently changed
- Managed by non-developers
- Large
- Shared by many services
- Subject to effective dates
- Audited
- Configuration-driven

For example:

```sql
SELECT
    u.user_id,
    COALESCE(m.display_name, 'Unknown') AS state_name
FROM users AS u
LEFT JOIN account_state_mapping AS m
    ON m.state_code = u.status;
```

The architectural decision is not about whether `CASE` can represent the mapping. It is about where the mapping should be maintained.

---

## Performance Considerations

Simple `CASE` generally has low computational cost when it performs straightforward equality comparisons.

The main performance concerns arise from scale and placement.

### Projection

This is usually straightforward:

```sql
SELECT
    order_id,
    CASE status
        WHEN 'paid' THEN 'processing'
        ELSE 'other'
    END AS state
FROM orders;
```

The expression must be evaluated for rows being returned, but it does not necessarily prevent an efficient lookup.

### Filtering

Avoid wrapping an indexed column in a `CASE` when a direct predicate expresses the same condition.

Prefer:

```sql
SELECT *
FROM orders
WHERE status = 'paid';
```

over:

```sql
SELECT *
FROM orders
WHERE CASE status
    WHEN 'paid' THEN 1
    ELSE 0
END = 1;
```

The direct predicate is simpler and gives the optimizer a straightforward condition to evaluate.

### Sorting

A computed `CASE` used in `ORDER BY` can require a sort operation:

```sql
ORDER BY CASE priority
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
END
```

For large datasets, inspect the execution plan and consider whether the ordering requirement justifies a derived or indexed representation.

---

## Production Considerations

### Keep Mappings Explicit

Prefer:

```sql
CASE status
    WHEN 'pending' THEN 'open'
    WHEN 'paid' THEN 'open'
    WHEN 'cancelled' THEN 'closed'
    ELSE 'unknown'
END
```

over obscure expressions that make the mapping difficult to audit.

### Define Unknown-State Behavior

Database enums and application state machines evolve.

A new value such as:

```text
chargeback
```

may appear after the query was originally written.

An explicit `ELSE` makes the behavior deterministic:

```sql
ELSE 'unknown'
```

For critical systems, also consider monitoring unexpected values rather than merely displaying `unknown`.

### Avoid Duplicated Mappings

If ten services independently contain:

```text
P -> pending
A -> active
S -> suspended
```

eventual drift is likely.

A mapping used across multiple systems should have an authoritative source.

### Keep SQL Dialect Differences in Mind

Basic `CASE` syntax is highly portable across major relational databases, but surrounding expressions, date functions, boolean behavior, type conversion, and optimizer behavior can differ.

If the application supports multiple database engines, test the generated SQL against every supported engine.

---

## Common Mistakes

### Trying to Match NULL with WHEN NULL

Incorrect:

```sql
CASE status
    WHEN NULL THEN 'missing'
    WHEN 'active' THEN 'enabled'
    ELSE 'unknown'
END
```

Correct:

```sql
CASE
    WHEN status IS NULL THEN 'missing'
    WHEN status = 'active' THEN 'enabled'
    ELSE 'unknown'
END
```

### Using Simple CASE for Ranges

Avoid trying to represent this:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

as a complicated simple `CASE`.

Searched `CASE` is designed for conditional expressions.

### Forgetting ELSE

Without `ELSE`, unmatched values become `NULL`.

That may silently break:

- API responses
- reporting
- sorting
- grouping
- downstream ETL
- metrics

Use an explicit fallback when unknown values matter.

### Hard-Coding Large Configuration Sets

A `CASE` with hundreds of mappings is difficult to review and deploy.

If the mapping is configuration rather than logic, model it as data.

### Using CASE to Hide a WHERE Predicate

Avoid:

```sql
WHERE CASE status
    WHEN 'active' THEN 1
    ELSE 0
END = 1
```

Prefer:

```sql
WHERE status = 'active'
```

The latter communicates the intent directly.

### Assuming SQL and Python Mappings Are Automatically Equivalent

This:

```python
if status == "active":
    return "enabled"
```

and this:

```sql
CASE status
    WHEN 'active' THEN 'enabled'
END
```

may look equivalent, but their handling of `NULL`, unexpected values, type conversion, and downstream consumers can differ.

Test the actual database behavior for important rules.

---

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| What is the structure of simple `CASE`? | `CASE expression WHEN value THEN result ... ELSE result END` |
| What does simple `CASE` compare? | One expression against each `WHEN` value |
| Can simple `CASE` handle ranges directly? | No; use searched `CASE` for range conditions |
| Can simple `CASE` directly match `NULL` with `WHEN NULL`? | No; use `IS NULL` in searched `CASE` |
| What happens without `ELSE`? | An unmatched row produces `NULL` |
| Does `CASE` filter rows? | No; it produces a value. `WHERE` determines row filtering |
| Where can simple `CASE` be used? | Anywhere an expression is valid, including `SELECT`, `ORDER BY`, `GROUP BY`, aggregates, and `UPDATE` |
| When is simple `CASE` preferable to searched `CASE`? | When one expression is mapped against discrete equality values |
| When should a `CASE` mapping become a table? | When the mapping is large, frequently changing, shared, or configuration-driven |
| Does `CASE` automatically make a query slow? | No; performance depends on expression complexity, row count, query placement, and execution plan |

## Key Takeaways

- Simple `CASE` is best for mapping one expression to discrete equality-based values.
- Use searched `CASE` for ranges, compound predicates, `NULL` checks, and other non-equality conditions.
- `WHEN NULL` does not match SQL `NULL`; use `IS NULL` when `NULL` requires explicit handling.
- Always define intentional fallback behavior with `ELSE` when unexpected values must not silently become `NULL`.
- Keep small stable mappings in `CASE`, but move large, changing, or shared mappings into authoritative reference data.