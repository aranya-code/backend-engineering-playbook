# 14- Common CASE Mistakes

## Overview

`CASE` is straightforward syntactically but easy to get subtly wrong. Most production problems are not syntax errors; they are incorrect branch ordering, unexpected `NULL` behavior, type mismatches, duplicated business rules, or expressions that unnecessarily complicate query execution.

The most important property to remember is:

> `CASE` returns the result of the first `WHEN` condition that evaluates to true.

That makes branch ordering part of the query's semantics.

```sql
CASE
    WHEN condition_1 THEN result_1
    WHEN condition_2 THEN result_2
    ELSE default_result
END
```

A production-quality `CASE` should make the following explicit:

- Which conditions have priority.
- What happens when no condition matches.
- What happens when input values are `NULL`.
- What data type the expression returns.
- Whether the expression affects filtering, grouping, ordering, or indexing.
- Whether the rule should actually live in SQL.

## Mistake: Incorrect Condition Ordering

This is one of the most common errors.

Consider:

```sql
CASE
    WHEN amount >= 100 THEN 'medium'
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

An amount of `5000` satisfies `amount >= 100`, so the first branch wins.

The `amount >= 1000` branch is therefore unreachable.

Correct:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    WHEN amount >= 100 THEN 'medium'
    ELSE 'small'
END
```

### Why It Happens

Developers often read the conditions as independent rules. SQL does not evaluate them that way.

`CASE` evaluates them in sequence:

```text
amount = 5000
     │
     ▼
amount >= 1000?
     │
    yes
     │
     ▼
"large"
```

The first matching branch terminates the decision process.

### Production Practice

For overlapping ranges, order conditions from the most specific or restrictive condition to the broader condition.

Also test boundary values explicitly:

```text
99
100
101
999
1000
1001
```

## Mistake: Forgetting ELSE

Consider:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    WHEN status = 'suspended' THEN 'blocked'
END
```

If `status` is `pending`, the result is `NULL`.

This may be intentional, but often it is accidental.

Prefer an explicit fallback when unmatched values have meaningful behavior:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    WHEN status = 'suspended' THEN 'blocked'
    ELSE 'unknown'
END
```

### Why ELSE Matters

An explicit `ELSE` documents the expected domain boundary.

It also makes future data anomalies easier to detect.

For example:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    WHEN status = 'suspended' THEN 'blocked'
    ELSE 'unexpected_status'
END
```

can make unexpected values visible in downstream reporting.

Do not automatically use `ELSE ''` or `ELSE 0`. The fallback should have correct domain semantics.

## Mistake: Ignoring NULL

`NULL` is not equal to another value, including another `NULL`.

This does not work as a `NULL` check:

```sql
CASE
    WHEN shipped_at = NULL THEN 'not shipped'
    ELSE 'shipped'
END
```

Use:

```sql
CASE
    WHEN shipped_at IS NULL THEN 'not shipped'
    ELSE 'shipped'
END
```

### NULL in Comparisons

Consider:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

If `amount` is `NULL`, the condition does not evaluate to true, so the `ELSE` branch is returned.

Therefore:

```text
amount = 5000  → large
amount = 500   → small
amount = NULL  → small
```

If `NULL` represents a distinct business state, handle it explicitly:

```sql
CASE
    WHEN amount IS NULL THEN 'unknown'
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

## Mistake: Confusing NULL with Zero

These values are not equivalent:

```text
NULL
0
```

For example:

```sql
CASE
    WHEN quantity = 0 THEN 'empty'
    ELSE 'available'
END
```

does not classify `NULL` as empty.

If both states need explicit treatment:

```sql
CASE
    WHEN quantity IS NULL THEN 'unknown'
    WHEN quantity = 0 THEN 'empty'
    ELSE 'available'
END
```

This distinction is important in financial, inventory, and analytics systems.

## Mistake: Using CASE Instead of a Simple Predicate

Avoid:

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

The direct predicate is easier to read and gives the optimizer a simpler expression.

`CASE` should generally be used when a value needs to be derived, not merely to disguise a straightforward condition.

## Mistake: Using CASE When COALESCE Is Better

This:

```sql
CASE
    WHEN phone_number IS NOT NULL THEN phone_number
    ELSE email
END
```

can usually be expressed more clearly as:

```sql
COALESCE(phone_number, email)
```

Use `COALESCE` when the requirement is:

> Return the first non-`NULL` value.

Use `CASE` when the decision involves actual conditional logic.

## Mistake: Treating CASE Like a Programming Language

SQL `CASE` is an expression, not a general-purpose procedural control-flow construct.

Do not try to represent an entire workflow inside one expression:

```text
validate payment
    ↓
reserve inventory
    ↓
call fraud service
    ↓
charge customer
    ↓
publish Kafka event
```

These operations belong in application or service orchestration.

SQL can derive state:

```sql
CASE
    WHEN payment_status = 'failed' THEN 'payment_failed'
    WHEN inventory_reserved = TRUE THEN 'ready'
    ELSE 'pending'
END
```

but it should not become the workflow engine.

## Mistake: Duplicating Business Rules

Suppose SQL contains:

```sql
CASE
    WHEN total_amount >= 1000 THEN 'large'
    ELSE 'small'
END AS order_size
```

while Python contains:

```python
if order.total_amount > 1000:
    order_size = "large"
else:
    order_size = "small"
```

The implementations disagree for exactly `1000`.

This is a common source of production inconsistencies.

### Typical Failure Pattern

```text
SQL report
   │
   └── "large"

REST API
   │
   └── "small"

Background job
   │
   └── "large"
```

Establish one authoritative implementation where possible.

If duplication is unavoidable, test the implementations against the same boundary cases.

## Mistake: Mixing Incompatible Result Types

A `CASE` should have compatible result expressions.

Avoid careless mixing such as:

```sql
CASE
    WHEN status = 'active' THEN 'active'
    ELSE 0
END
```

Depending on the database, implicit type conversion may fail or produce undesirable behavior.

Prefer a consistent result type:

```sql
CASE
    WHEN status = 'active' THEN 'active'
    ELSE 'inactive'
END
```

For numeric results:

```sql
CASE
    WHEN status = 'active' THEN 1
    ELSE 0
END
```

Explicit casts may be appropriate when the intended type is not obvious.

## Mistake: Forgetting That CASE Has a Result Type

The expression has a type determined from its result branches.

For example:

```sql
CASE
    WHEN status = 'active' THEN 1
    ELSE 0
END
```

is numeric.

Whereas:

```sql
CASE
    WHEN status = 'active' THEN 'active'
    ELSE 'inactive'
END
```

is textual.

This matters when the expression is:

- Stored in a view.
- Used in a generated column.
- Returned through an ORM.
- Used in arithmetic.
- Used in comparisons.
- Consumed by an API serializer.

Make the intended type explicit when necessary.

## Mistake: Incorrect Range Boundaries

Consider:

```sql
CASE
    WHEN score > 100 THEN 'high'
    WHEN score >= 50 THEN 'medium'
    ELSE 'low'
END
```

A score of exactly `100` is classified as `medium`.

That may or may not be correct.

Define ranges explicitly:

```text
low       < 50
medium    50–100
high      > 100
```

Then implement those semantics deliberately:

```sql
CASE
    WHEN score > 100 THEN 'high'
    WHEN score >= 50 THEN 'medium'
    ELSE 'low'
END
```

For financial and regulatory rules, boundary tests are especially important.

## Mistake: Overlapping Boolean Conditions

Consider:

```sql
CASE
    WHEN is_active = TRUE THEN 'active'
    WHEN is_active = TRUE AND is_verified = TRUE THEN 'verified'
    ELSE 'inactive'
END
```

The second branch is unreachable because every verified active user already matches the first branch.

Correct:

```sql
CASE
    WHEN is_active = TRUE AND is_verified = TRUE THEN 'verified'
    WHEN is_active = TRUE THEN 'active'
    ELSE 'inactive'
END
```

When branches overlap, place the more specific predicate first.

## Mistake: Assuming CASE Evaluation Means Every Expression Is Safely Skipped

Developers sometimes assume that an unselected branch can never cause an evaluation problem.

For example:

```sql
CASE
    WHEN divisor <> 0 THEN numerator / divisor
    ELSE 0
END
```

The intended logic is reasonable, but SQL optimizers and database-specific expression evaluation rules mean you should not build correctness around procedural assumptions about evaluation order outside the documented semantics of `CASE`.

For PostgreSQL, for example, constant expressions may be evaluated during planning, and some expressions can be transformed by the optimizer.

For potentially dangerous expressions, make the expression itself safe where practical:

```sql
numerator / NULLIF(divisor, 0)
```

Then handle the resulting `NULL` explicitly if required:

```sql
COALESCE(numerator / NULLIF(divisor, 0), 0)
```

The general principle is:

> Do not rely on `CASE` as a universal safety barrier around expressions whose evaluation has independent hazards.

## Mistake: Hiding Index-Friendly Predicates Behind CASE

Avoid unnecessarily transforming indexed predicates:

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

If a complex expression genuinely needs to be queried frequently, investigate:

- Expression indexes.
- Generated columns.
- Functional indexes.
- Materialized views.
- Schema redesign.

Always verify with `EXPLAIN`.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE status = 'active';
```

## Mistake: Using CASE in WHERE When OR Is Clearer

Sometimes developers write complicated conditional expressions when ordinary Boolean logic is sufficient.

Avoid:

```sql
WHERE CASE
    WHEN :include_cancelled = TRUE THEN TRUE
    ELSE status <> 'cancelled'
END
```

A direct predicate can be clearer:

```sql
WHERE :include_cancelled = TRUE
   OR status <> 'cancelled'
```

However, parameter-dependent `OR` predicates can have performance implications for some workloads. If the query is performance-sensitive, inspect the actual execution plan rather than assuming one form is always superior.

## Mistake: Repeating a Large CASE Expression

This can become difficult to maintain:

```sql
SELECT
    CASE
        WHEN ...
        WHEN ...
        ELSE ...
    END AS category
FROM orders
GROUP BY
    CASE
        WHEN ...
        WHEN ...
        ELSE ...
    END;
```

If the same expression is complex, consider a derived relation or CTE where appropriate:

```sql
WITH classified_orders AS (
    SELECT
        order_id,
        CASE
            WHEN total_amount >= 10000 THEN 'large'
            WHEN total_amount >= 1000 THEN 'medium'
            ELSE 'small'
        END AS category
    FROM orders
)
SELECT
    category,
    COUNT(*) AS order_count
FROM classified_orders
GROUP BY category;
```

Do not introduce a CTE merely for style; evaluate the query plan and database behavior for the specific workload.

## Mistake: Assuming CASE Is Free

A `CASE` expression consumes database CPU.

For a small query this is normally negligible. For billions of rows, repeatedly evaluating complex expressions can become meaningful.

Consider:

```sql
SELECT
    CASE
        WHEN expensive_condition_1 THEN ...
        WHEN expensive_condition_2 THEN ...
        WHEN expensive_condition_3 THEN ...
        ELSE ...
    END
FROM very_large_table;
```

Production considerations include:

- Number of rows processed.
- Complexity of each condition.
- Frequency of the query.
- Whether the expression is repeated.
- Whether precomputation is appropriate.
- Whether filtering can reduce the input set first.

A good optimization is often to reduce rows before applying expensive transformations.

```sql
SELECT
    CASE
        WHEN ...
        THEN ...
        ELSE ...
    END
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

## Mistake: Building Huge Hard-Coded CASE Statements

A `CASE` with dozens or hundreds of branches may indicate that the logic is actually data.

For example:

```sql
CASE
    WHEN country_code = 'IN' THEN ...
    WHEN country_code = 'US' THEN ...
    WHEN country_code = 'GB' THEN ...
    -- dozens more
END
```

If these mappings change independently of application releases, consider a lookup table:

```text
country_rules
├── country_code
├── category
└── priority
```

Then use a join.

This makes configuration data instead of SQL source code.

## Mistake: Putting Presentation Logic Into SQL

Avoid formatting data for one specific frontend when the database result is intended for multiple consumers.

For example:

```sql
CASE
    WHEN currency = 'USD' THEN '$' || amount
    WHEN currency = 'EUR' THEN '€' || amount
END
```

This may be appropriate for a reporting query, but is often a poor general-purpose API representation.

Prefer returning structured data:

```text
currency = "USD"
amount = 1250.50
```

and let the presentation layer format it.

This preserves data semantics and avoids coupling the database to a particular UI representation.

## Mistake: Using CASE as Authorization

This is unsafe as an authorization strategy:

```sql
CASE
    WHEN is_admin THEN salary
    ELSE NULL
END
```

A conditional projection does not replace access control.

Authorization should determine which data the caller is allowed to access before the result is exposed.

Use proper database permissions, row-level security where appropriate, application authorization, or a combination suitable for the architecture.

## Mistake: Ignoring Data Quality

A `CASE` often silently converts invalid or unexpected data into a valid-looking category.

For example:

```sql
CASE
    WHEN status = 'active' THEN 'active'
    ELSE 'inactive'
END
```

This classifies all of these as `inactive`:

```text
suspended
deleted
pending
typo
NULL
unexpected_future_status
```

If these states have different meanings, the query hides valuable information.

Prefer explicit classification:

```sql
CASE
    WHEN status = 'active' THEN 'active'
    WHEN status = 'suspended' THEN 'suspended'
    WHEN status = 'deleted' THEN 'deleted'
    WHEN status IS NULL THEN 'unknown'
    ELSE 'unexpected'
END
```

This is particularly useful in data-quality investigations and operational reporting.

## Mistake: Ignoring Time Zones

Date-based `CASE` logic can become incorrect when timestamps are interpreted in different time zones.

For example:

```sql
CASE
    WHEN created_at::date = CURRENT_DATE THEN 'today'
    ELSE 'older'
END
```

may not represent the user's local calendar day if `created_at` and the database session use different time zones.

For production systems:

- Define the business time zone.
- Store timestamps consistently.
- Convert explicitly where required.
- Test around midnight and daylight-saving transitions when relevant.

For example, PostgreSQL applications should understand the distinction between `timestamp with time zone` and `timestamp without time zone`.

## Mistake: Using CASE Instead of Schema Design

Sometimes repeated `CASE` logic indicates that a derived concept has become an important domain attribute.

If every query repeatedly computes:

```sql
CASE
    WHEN ...
    THEN ...
END AS risk_level
```

ask whether `risk_level` should instead be:

- A persisted attribute.
- A generated column.
- A database view.
- A materialized view.
- A normalized lookup.
- A domain-level classification.

Do not persist every derived value automatically. Persist only when the performance, consistency, indexing, or domain requirements justify the additional write complexity.

## Debugging CASE Problems

When a `CASE` produces unexpected results, inspect the logic systematically.

### Check Branch Order

Ask:

```text
Can an earlier WHEN match rows intended for a later WHEN?
```

### Check Boundary Values

Test:

```text
minimum - 1
minimum
minimum + 1
maximum - 1
maximum
maximum + 1
```

### Check NULL

Explicitly test:

```sql
SELECT
    CASE
        WHEN amount IS NULL THEN 'null'
        WHEN amount >= 1000 THEN 'large'
        ELSE 'small'
    END
FROM orders;
```

### Check Actual Distinct Inputs

Before changing the query, inspect the source data:

```sql
SELECT DISTINCT status
FROM orders
ORDER BY status;
```

Unexpected values frequently explain apparently incorrect `CASE` output.

### Check the Execution Plan

For performance problems:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

Do not optimize a `CASE` expression in isolation without understanding the complete query plan.

## Production Review Checklist

Before merging a query containing significant `CASE` logic, verify:

- [ ] Conditions are ordered intentionally.
- [ ] Overlapping conditions are understood.
- [ ] Boundary values have been tested.
- [ ] `NULL` behavior is explicit.
- [ ] `ELSE` behavior is intentional.
- [ ] Result types are compatible.
- [ ] Simple predicates are not unnecessarily wrapped in `CASE`.
- [ ] `COALESCE` is used where it communicates intent better.
- [ ] Large or expensive expressions have been evaluated for performance.
- [ ] Index usage has been checked where relevant.
- [ ] Business logic is not duplicated unnecessarily.
- [ ] The expression is not hiding data-quality problems.
- [ ] Authorization is not being delegated to presentation logic.
- [ ] Time-zone semantics are correct for date/time conditions.
- [ ] A large `CASE` has not become a substitute for a lookup table or schema design.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Which `WHEN` branch wins? | The first branch whose condition evaluates to true |
| What happens when no branch matches and there is no `ELSE`? | The result is `NULL` |
| Does `= NULL` work in a `CASE` condition? | No; use `IS NULL` |
| Why does condition ordering matter? | Earlier overlapping conditions can make later branches unreachable |
| Why can a `CASE` silently hide bad data? | A broad `ELSE` can classify unexpected values as a valid category |
| Should `CASE` replace `WHERE status = 'active'`? | Usually no; the direct predicate is clearer and generally easier to optimize |
| When is `COALESCE` preferable? | When selecting the first non-`NULL` value |
| Can `CASE` be used for authorization? | No; authorization requires proper access-control enforcement |
| Why avoid huge `CASE` expressions? | They become difficult to maintain and may indicate data belongs in a mapping table |
| Can `CASE` affect query performance? | Yes; complex expressions consume CPU and can affect optimization or index usage depending on placement |
| What should be tested for range-based CASE logic? | Boundaries, overlapping conditions, `NULL`, and unexpected values |
| Should every derived CASE result become a database column? | No; persist derived values only when the performance or domain requirements justify it |

## Key Takeaways

- The first matching `WHEN` wins, so branch ordering and overlapping conditions are critical to correctness.
- Make `NULL`, `ELSE`, boundary values, and result types explicit rather than relying on accidental behavior.
- Prefer simple predicates, `COALESCE`, or other clearer SQL constructs when `CASE` adds unnecessary complexity.
- Treat large, duplicated, or frequently changing `CASE` expressions as potential signals for better schema, mapping-table, or application-level designs.
- Validate significant `CASE` logic with boundary tests, representative data, and execution plans before relying on it in production.