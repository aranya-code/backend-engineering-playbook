# 03- Searched CASE

## Overview

A **searched `CASE` expression** evaluates one or more boolean conditions and returns the result associated with the first condition that evaluates to true.

It is the more general form of `CASE` and is the appropriate choice when business logic depends on:

- Ranges
- Comparisons such as `>`, `<`, `>=`, and `<=`
- Multiple columns
- Compound predicates
- `NULL` checks
- Date and time conditions
- Existence or other boolean expressions

The general form is:

```sql
CASE
    WHEN condition_1 THEN result_1
    WHEN condition_2 THEN result_2
    WHEN condition_3 THEN result_3
    ELSE default_result
END
```

For example:

```sql
SELECT
    order_id,
    amount,
    CASE
        WHEN amount >= 10000 THEN 'high'
        WHEN amount >= 5000 THEN 'medium'
        WHEN amount > 0 THEN 'low'
        ELSE 'invalid'
    END AS order_value
FROM orders;
```

Unlike simple `CASE`, searched `CASE` does not compare one expression against a list of fixed values. Each `WHEN` contains a complete condition.

---

## Why Searched CASE Exists

Backend systems frequently need to transform raw database values into business classifications.

For example:

```text
amount = 12500
```

may need to become:

```text
high_value
```

A simple equality mapping cannot express:

```sql
amount >= 10000
```

A searched `CASE` can:

```sql
CASE
    WHEN amount >= 10000 THEN 'high_value'
    ELSE 'standard'
END
```

This makes `CASE` an important SQL mechanism for **conditional data transformation**.

It can keep straightforward projection logic close to the data instead of requiring the application to fetch raw rows and perform another transformation layer.

---

## Syntax

The standard structure is:

```sql
CASE
    WHEN condition THEN result
    WHEN condition THEN result
    ELSE result
END
```

For example:

```sql
SELECT
    user_id,
    CASE
        WHEN is_active = TRUE AND email_verified = TRUE THEN 'trusted'
        WHEN is_active = TRUE THEN 'active_unverified'
        ELSE 'inactive'
    END AS user_state
FROM users;
```

Each `WHEN` contains an expression that evaluates to SQL's boolean truth value.

The database evaluates the conditions in order and returns the result for the first matching branch.

If no condition matches:

- `ELSE` is returned when present.
- `NULL` is returned when `ELSE` is omitted.

---

## Evaluation Model

Consider:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    WHEN amount > 0 THEN 'low'
    ELSE 'invalid'
END
```

For:

```text
amount = 7500
```

the conditions are evaluated conceptually as:

```text
7500 >= 10000  -> false
7500 >= 5000   -> true
```

The result is:

```text
medium
```

The later condition is not needed for determining the result.

This means **condition ordering is part of the logic**.

---

## First Matching WHEN Wins

Consider:

```sql
CASE
    WHEN amount > 0 THEN 'positive'
    WHEN amount >= 10000 THEN 'high'
    ELSE 'non_positive'
END
```

For:

```text
amount = 15000
```

the first condition is already true:

```text
amount > 0 -> true
```

Therefore the result is:

```text
positive
```

The `high` branch is never selected.

The correct ordering is:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount > 0 THEN 'positive'
    ELSE 'non_positive'
END
```

### General Rule

Put **more specific conditions before broader conditions** when they overlap.

This is one of the most important production rules for searched `CASE`.

---

## Simple CASE vs Searched CASE

Both forms are useful, but they solve different problems.

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
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

| Requirement | Simple `CASE` | Searched `CASE` |
| --- | --- | --- |
| Equality mapping | Excellent | Supported |
| Ranges | Not suitable | Excellent |
| Multiple columns | Not suitable | Excellent |
| `IS NULL` | Not directly | Excellent |
| Compound conditions | Not suitable | Excellent |
| Date comparisons | Limited | Excellent |
| Readability for fixed mappings | Excellent | Good |
| Complex business rules | Limited | Excellent |

Use the simplest form that clearly expresses the requirement.

---

## Comparison Operators

Searched `CASE` can use ordinary comparison operators.

```sql
SELECT
    product_id,
    price,
    CASE
        WHEN price < 10 THEN 'budget'
        WHEN price < 100 THEN 'standard'
        WHEN price < 500 THEN 'premium'
        ELSE 'luxury'
    END AS price_category
FROM products;
```

The order matters because a value such as `50` satisfies both:

```sql
price < 100
```

and:

```sql
price < 500
```

The first matching condition determines the result.

---

## Compound Conditions

Searched `CASE` can combine conditions with `AND`, `OR`, and `NOT`.

```sql
SELECT
    customer_id,
    CASE
        WHEN is_active = TRUE
             AND email_verified = TRUE
             AND risk_score < 50
            THEN 'eligible'
        WHEN is_active = TRUE
            THEN 'review'
        ELSE 'ineligible'
    END AS eligibility
FROM customers;
```

This is substantially easier to express with searched `CASE` than with simple `CASE`.

Use parentheses when the logic contains both `AND` and `OR` to make precedence explicit.

```sql
CASE
    WHEN is_active = TRUE
         AND (country = 'IN' OR country = 'US')
        THEN 'supported'
    ELSE 'unsupported'
END
```

Do not rely on readers remembering operator precedence in complex business logic.

---

## Handling NULL

Searched `CASE` is the correct form when `NULL` needs explicit treatment.

For example:

```sql
SELECT
    order_id,
    CASE
        WHEN shipped_at IS NULL THEN 'not_shipped'
        WHEN shipped_at > CURRENT_TIMESTAMP THEN 'scheduled'
        ELSE 'shipped'
    END AS shipping_state
FROM orders;
```

This is preferable to attempting:

```sql
CASE shipped_at
    WHEN NULL THEN 'not_shipped'
    ELSE 'shipped'
END
```

`NULL` represents an unknown or absent value and does not behave like an ordinary value under equality comparison.

When `NULL` has business meaning, make the handling explicit.

---

## Three-Valued Logic

SQL predicates can evaluate to:

- `TRUE`
- `FALSE`
- `UNKNOWN`

`NULL` commonly causes `UNKNOWN`.

For example:

```sql
amount > 100
```

when `amount` is `NULL` does not evaluate to `FALSE`. It evaluates to `UNKNOWN`.

In a searched `CASE`:

```sql
CASE
    WHEN amount > 100 THEN 'large'
    ELSE 'not_large'
END
```

the `WHEN` branch is selected only when the condition is true. An `UNKNOWN` condition does not match the `WHEN`, so evaluation proceeds to the next branch.

If the distinction between `NULL` and an ordinary false condition matters, handle it explicitly:

```sql
CASE
    WHEN amount IS NULL THEN 'missing'
    WHEN amount > 100 THEN 'large'
    ELSE 'small'
END
```

This distinction is critical in production reporting and financial systems.

---

## Range Classification

One of the most common uses of searched `CASE` is bucketing numeric values.

```sql
SELECT
    customer_id,
    monthly_spend,
    CASE
        WHEN monthly_spend >= 100000 THEN 'enterprise'
        WHEN monthly_spend >= 50000 THEN 'large'
        WHEN monthly_spend >= 10000 THEN 'medium'
        ELSE 'small'
    END AS customer_segment
FROM customer_spend;
```

The ordering is intentionally descending.

A customer spending `120000` matches:

```sql
monthly_spend >= 100000
```

before reaching the lower thresholds.

### Boundary Testing

Production classification rules should explicitly test boundaries:

```text
9999
10000
10001

49999
50000
50001

99999
100000
100001
```

Off-by-one errors in classification logic can produce incorrect billing, pricing, eligibility, or reporting results.

---

## Date and Time Conditions

Searched `CASE` is useful for deriving temporal states.

```sql
SELECT
    subscription_id,
    CASE
        WHEN cancelled_at IS NOT NULL THEN 'cancelled'
        WHEN expires_at <= CURRENT_TIMESTAMP THEN 'expired'
        WHEN expires_at <= CURRENT_TIMESTAMP + INTERVAL '7 days'
            THEN 'expiring_soon'
        ELSE 'active'
    END AS lifecycle_state
FROM subscriptions;
```

The order represents business precedence:

1. Explicit cancellation
2. Expiration
3. Upcoming expiration
4. Active

Date logic should account for timezone semantics and the database's timestamp types.

For distributed backend systems, avoid mixing application-local time with database-server time without an explicit design decision.

---

## Boolean Classification

A searched `CASE` can convert complex conditions into a simple flag.

```sql
SELECT
    user_id,
    CASE
        WHEN is_active = TRUE
             AND email_verified = TRUE
            THEN TRUE
        ELSE FALSE
    END AS can_receive_email
FROM users;
```

However, do not automatically use `CASE` when the database can return the predicate directly.

If this is sufficient:

```sql
SELECT
    user_id,
    is_active AND email_verified AS can_receive_email
FROM users;
```

prefer the simpler expression where supported and where its `NULL` semantics are acceptable.

The goal is not to use `CASE`; the goal is to express the business rule clearly.

---

## Conditional Aggregation

Searched `CASE` is frequently used with aggregates.

For example, count completed orders:

```sql
SELECT
    COUNT(
        CASE
            WHEN status = 'completed' THEN 1
        END
    ) AS completed_orders
FROM orders;
```

A more explicit form is:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_orders
FROM orders;
```

For conditional sums:

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

PostgreSQL also provides `FILTER`:

```sql
SELECT
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    SUM(amount) FILTER (WHERE status = 'completed') AS completed_revenue
FROM orders;
```

`FILTER` can be clearer for conditional aggregates when PostgreSQL-specific SQL is acceptable.

---

## CASE in ORDER BY

Searched `CASE` can implement custom ordering based on business rules.

```sql
SELECT
    ticket_id,
    status,
    priority
FROM support_tickets
ORDER BY
    CASE
        WHEN status = 'open' AND priority = 'critical' THEN 1
        WHEN status = 'open' AND priority = 'high' THEN 2
        WHEN status = 'open' THEN 3
        ELSE 4
    END,
    created_at ASC;
```

This can implement a queue such as:

```text
Critical open tickets
High-priority open tickets
Other open tickets
Everything else
```

For large datasets, inspect the execution plan. Computed ordering may require sorting and can become expensive at scale.

---

## CASE in GROUP BY

A searched `CASE` can create reporting buckets.

```sql
SELECT
    CASE
        WHEN amount >= 10000 THEN 'high'
        WHEN amount >= 5000 THEN 'medium'
        ELSE 'low'
    END AS value_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount >= 10000 THEN 'high'
        WHEN amount >= 5000 THEN 'medium'
        ELSE 'low'
    END;
```

The same classification expression may need to be repeated depending on the database and query structure.

If a classification becomes central to the data model, consider whether it belongs in:

- A view
- A generated/computed representation
- A materialized reporting model
- A dimension/reference table
- An application/domain layer

The correct choice depends on how frequently the classification changes and how widely it is consumed.

---

## CASE in UPDATE

Searched `CASE` can perform controlled transformations during migrations.

```sql
UPDATE customers
SET risk_tier = CASE
    WHEN annual_spend >= 100000 AND chargeback_rate < 0.01
        THEN 'low'
    WHEN annual_spend >= 50000
        THEN 'medium'
    ELSE 'high'
END;
```

For production migrations on large tables, consider:

- Transaction duration
- Lock contention
- WAL/binlog growth
- Replication lag
- Batch size
- Rollback strategy
- Application traffic
- Index impact

A logically correct `CASE` can still create an operationally unsafe migration if millions of rows are updated in one transaction during peak traffic.

---

## CASE in JOIN Conditions

`CASE` can technically be used inside join expressions, but this should be approached carefully.

For example:

```sql
SELECT
    o.order_id,
    p.policy_name
FROM orders AS o
JOIN pricing_policies AS p
    ON p.region_code = CASE
        WHEN o.country_code IN ('IN', 'SG') THEN 'APAC'
        WHEN o.country_code IN ('US', 'CA') THEN 'NA'
        ELSE 'OTHER'
    END;
```

This can be useful for specific transformations, but expressions applied to join keys can complicate optimization.

When the mapping is stable and important, consider normalizing the relationship or using a reference table:

```text
country -> region -> pricing policy
```

This often provides a cleaner data model than embedding large mapping logic into joins.

---

## CASE and Query Performance

`CASE` itself is not inherently a performance problem.

Performance depends on:

- Number of rows evaluated
- Complexity of conditions
- Functions invoked by conditions
- Placement of the expression
- Sorting/grouping requirements
- Index availability
- Query plan
- Data distribution

### Projection

A `CASE` in `SELECT` is usually straightforward:

```sql
SELECT
    order_id,
    CASE
        WHEN status = 'paid' THEN 'processing'
        ELSE 'other'
    END AS state
FROM orders;
```

The database evaluates the expression for rows participating in the result.

### Filtering

Avoid using `CASE` to obscure a direct predicate.

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
WHERE CASE
    WHEN status = 'paid' THEN 1
    ELSE 0
END = 1;
```

The direct predicate is clearer and generally gives the optimizer a more straightforward expression to work with.

### Function Calls

Avoid unnecessarily expensive functions inside every row's `CASE` condition.

For example:

```sql
CASE
    WHEN expensive_function(payload) = 'x' THEN ...
    ...
END
```

may require substantial CPU work on large datasets.

If the derived value is frequently queried, consider whether it should be materialized or computed earlier in the data pipeline.

---

## Short-Circuiting and Side Effects

SQL `CASE` is generally described as evaluating conditions in order and returning the first matching result.

However, do not build correctness around assumptions that an unused branch is completely harmless in every database or context. Optimizers may transform expressions, and constant expressions or planning-time evaluation can introduce surprising behavior in some situations.

Avoid putting error-prone or unnecessarily expensive expressions into branches merely because you expect them never to execute.

For example, instead of relying on conditional evaluation to protect unsafe arithmetic, use the database's safe operation where available:

```sql
SELECT
    amount / NULLIF(quantity, 0) AS unit_price
FROM order_items;
```

This is clearer than making a `CASE` responsible for preventing division by zero.

---

## Result Data Types

All result expressions should have compatible types.

Good:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

Avoid mixing unrelated result types:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    ELSE 0
END
```

Database-specific type-resolution rules may cause implicit conversions or errors.

When precision matters, particularly for financial values, make the intended type explicit rather than relying on implicit coercion.

---

## CASE and Financial Logic

Financial systems require special care because classification rules can affect:

- Pricing
- Discounts
- Taxes
- Fees
- Commission
- Risk tiers
- Revenue reporting
- Billing

For example:

```sql
SELECT
    order_id,
    subtotal,
    CASE
        WHEN subtotal >= 10000 THEN subtotal * 0.90
        WHEN subtotal >= 5000 THEN subtotal * 0.95
        ELSE subtotal
    END AS discounted_subtotal
FROM orders;
```

Production implementations should additionally consider:

- Decimal/numeric types rather than floating-point types
- Currency
- Rounding rules
- Tax jurisdiction
- Effective dates
- Versioned pricing rules
- Auditability

A `CASE` expression can implement the calculation, but it does not automatically make the underlying business rule auditable or versioned.

---

## CASE and Business Rules

A useful senior-level distinction is between **query-local transformation** and **domain policy**.

A query-local transformation might be:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 'disabled'
END
```

This is often appropriate directly in SQL.

A complex pricing policy such as:

```text
customer tier
+ region
+ promotion
+ effective date
+ product category
+ minimum quantity
+ contract override
```

may technically be expressible with `CASE`, but embedding the entire policy into SQL can make it difficult to:

- Version
- Test
- Audit
- Reuse
- Change safely
- Explain to other teams

When rules become substantial domain policy, use an explicit domain model or rule representation rather than allowing a single query to become the source of truth.

---

## CASE in Backend APIs

A REST endpoint may need derived values without requiring application-side processing.

For example:

```sql
SELECT
    id,
    name,
    CASE
        WHEN deleted_at IS NOT NULL THEN 'deleted'
        WHEN suspended_at IS NOT NULL THEN 'suspended'
        WHEN is_active = TRUE THEN 'active'
        ELSE 'inactive'
    END AS api_status
FROM users
WHERE tenant_id = $1;
```

The application can return the derived value directly:

```json
{
  "id": 42,
  "name": "Example User",
  "api_status": "active"
}
```

This can reduce application-side transformation work, but the API contract should remain stable even if the underlying database representation changes.

Do not expose internal database classifications merely because they are convenient to query.

---

## CASE with Django ORM

Django provides conditional expressions through `Case` and `When`.

For example:

```python
from django.db.models import Case, CharField, Value, When

orders = Order.objects.annotate(
    value_band=Case(
        When(amount__gte=10000, then=Value("high")),
        When(amount__gte=5000, then=Value("medium")),
        default=Value("low"),
        output_field=CharField(),
    )
)
```

This is conceptually equivalent to:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount >= 5000 THEN 'medium'
    ELSE 'low'
END
```

For production ORM work:

- Inspect generated SQL for complex expressions.
- Check execution plans for large datasets.
- Specify `output_field` when the result type is not obvious.
- Avoid duplicating important business rules across SQL and Python.
- Test boundary conditions explicitly.

The ORM is an abstraction over SQL, not a replacement for understanding the SQL being executed.

---

## CASE and Data Pipelines

Searched `CASE` is useful in ETL and reporting pipelines.

For example, raw Kafka or application data may eventually land in a warehouse with operational statuses that need reporting categories:

```sql
SELECT
    event_date,
    CASE
        WHEN event_type IN ('payment_failed', 'payment_declined')
            THEN 'payment_failure'
        WHEN event_type IN ('payment_captured', 'payment_settled')
            THEN 'payment_success'
        ELSE 'other'
    END AS event_category,
    COUNT(*) AS event_count
FROM payment_events
GROUP BY
    event_date,
    CASE
        WHEN event_type IN ('payment_failed', 'payment_declined')
            THEN 'payment_failure'
        WHEN event_type IN ('payment_captured', 'payment_settled')
            THEN 'payment_success'
        ELSE 'other'
    END;
```

This is effective for local analytical transformations.

If the classification is shared by many downstream systems, define an authoritative mapping rather than allowing every pipeline to implement its own interpretation.

---

## Production Design Guidelines

### Keep Conditions Readable

Prefer:

```sql
CASE
    WHEN status = 'active'
         AND verified = TRUE
        THEN 'trusted'
    WHEN status = 'active'
        THEN 'unverified'
    ELSE 'inactive'
END
```

over deeply nested expressions that require significant mental parsing.

### Make Precedence Explicit

When conditions overlap, document the intended order through the query structure.

```sql
CASE
    WHEN fraud_confirmed = TRUE THEN 'blocked'
    WHEN fraud_score >= 90 THEN 'review'
    WHEN fraud_score >= 50 THEN 'monitor'
    ELSE 'normal'
END
```

This makes the policy hierarchy visible.

### Handle NULL Deliberately

Do not assume `NULL` behaves like zero, false, empty string, or an ordinary value.

```sql
CASE
    WHEN score IS NULL THEN 'unrated'
    WHEN score >= 90 THEN 'excellent'
    ELSE 'standard'
END
```

### Use Explicit ELSE

For domain classifications:

```sql
ELSE 'unknown'
```

is often safer than silently producing `NULL`.

For strict data-quality workflows, an unexpected value may instead need to surface as an error through validation or monitoring.

### Keep CASE Local When Appropriate

A short projection-specific transformation belongs naturally in SQL.

A large, shared business policy may belong elsewhere.

---

## Common Mistakes

### Overlapping Conditions in the Wrong Order

Incorrect:

```sql
CASE
    WHEN amount > 0 THEN 'positive'
    WHEN amount >= 10000 THEN 'high'
    ELSE 'other'
END
```

Correct:

```sql
CASE
    WHEN amount >= 10000 THEN 'high'
    WHEN amount > 0 THEN 'positive'
    ELSE 'other'
END
```

The broader condition must not consume rows intended for the more specific condition.

### Forgetting NULL

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

Consider a mapping table when the logic is data-driven.

### Duplicating Business Rules

If the same classification is independently implemented in:

- SQL
- Django
- FastAPI
- Kafka consumers
- Reporting jobs

the system can eventually produce inconsistent answers.

Establish a clear owner for important domain rules.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| What does searched `CASE` evaluate? | Boolean conditions in `WHEN` clauses |
| How is it different from simple `CASE`? | Searched `CASE` evaluates arbitrary conditions rather than comparing one expression to fixed values |
| Which `WHEN` wins when multiple conditions are true? | The first matching `WHEN` |
| What happens when no `WHEN` matches? | `ELSE` is returned, or `NULL` if `ELSE` is omitted |
| How should `NULL` be checked? | Use `IS NULL` or `IS NOT NULL` |
| Can searched `CASE` handle ranges? | Yes; this is one of its primary use cases |
| Can it combine multiple columns? | Yes, using boolean expressions such as `AND` and `OR` |
| Does `CASE` filter rows? | No; it produces an expression value. `WHERE` controls row filtering |
| Is `CASE` inherently slow? | No; performance depends on expression complexity, row count, placement, and execution plan |
| When should a `CASE` become a lookup table or domain rule? | When the mapping is large, frequently changing, shared, or configuration-driven |

## Key Takeaways

- Searched `CASE` evaluates boolean conditions and is the right form for ranges, compound predicates, date logic, and explicit `NULL` handling.
- `WHEN` clauses are evaluated in order, so overlapping conditions must be ordered from the most specific rule to the broader fallback.
- SQL uses three-valued logic; `NULL` can produce `UNKNOWN`, so use `IS NULL` or `IS NOT NULL` when `NULL` has explicit meaning.
- `CASE` is an expression, not a filtering mechanism; prefer direct predicates for filtering and inspect execution plans when `CASE` participates in sorting, grouping, joins, or large updates.
- Keep small query-local transformations in SQL, but move large or shared business-rule mappings into an authoritative data or domain model.