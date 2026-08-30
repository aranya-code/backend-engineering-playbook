# 06- Comparison Operators

## Overview

SQL comparison operators evaluate relationships between values and produce a Boolean-like result used primarily in predicates such as `WHERE`, `JOIN ... ON`, and `HAVING`.

The core comparison operators are:

| Operator | Meaning | Example |
|---|---|---|
| `=` | Equal to | `status = 'active'` |
| `<>` | Not equal to | `status <> 'deleted'` |
| `!=` | Not equal to | `status != 'deleted'` |
| `>` | Greater than | `total > 1000` |
| `>=` | Greater than or equal | `total >= 1000` |
| `<` | Less than | `total < 1000` |
| `<=` | Less than or equal | `total <= 1000` |

Comparison operators look simple, but production SQL depends heavily on understanding **data types, `NULL`, three-valued logic, implicit conversions, collation, precision, and index behavior**.

For backend engineers, the goal is not simply to know the operators. It is to choose comparisons that correctly represent business semantics while remaining predictable and efficient at scale.

## Basic Comparison

A comparison evaluates a value against another value:

```sql
SELECT
    id,
    email,
    status
FROM users
WHERE status = 'active';
```

For each row, the database evaluates:

```text
status = 'active'
       ↓
TRUE / FALSE / UNKNOWN
```

Only rows for which the `WHERE` predicate evaluates to `TRUE` are retained.

Comparison operators can be used against:

- Numeric values
- Strings
- Dates
- Timestamps
- Boolean values
- Expressions
- Columns from joined tables
- Scalar subqueries
- Parameters

Example:

```sql
SELECT
    id,
    total
FROM orders
WHERE total >= 1000;
```

## Equality Operator

The equality operator is `=`.

```sql
SELECT
    id,
    email
FROM users
WHERE id = 123;
```

It is commonly used for:

- Primary-key lookups
- Foreign-key filtering
- Status filtering
- Exact identifiers
- Configuration values
- Equality joins

Example join:

```sql
SELECT
    u.id,
    u.email,
    o.id AS order_id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

For equality predicates on indexed columns, databases can often perform efficient index lookups.

## Inequality Operators

SQL standard syntax uses:

```sql
<>
```

Example:

```sql
SELECT
    id,
    status
FROM orders
WHERE status <> 'cancelled';
```

Many databases also support:

```sql
WHERE status != 'cancelled';
```

`!=` is widely supported, but `<>` is the standard SQL operator and is preferable when portability matters.

### Important NULL Behavior

Neither form means:

> "Return every row whose value is not cancelled, including rows where status is NULL."

If `status` is `NULL`:

```sql
status <> 'cancelled'
```

evaluates to `UNKNOWN`, not `TRUE`.

If `NULL` should be included, make the requirement explicit:

```sql
WHERE status <> 'cancelled'
   OR status IS NULL;
```

Whether this is correct depends on the domain semantics.

## Greater Than and Less Than

Numeric comparison:

```sql
SELECT
    id,
    total
FROM orders
WHERE total > 5000;
```

Inclusive comparison:

```sql
SELECT
    id,
    total
FROM orders
WHERE total >= 5000;
```

Similarly:

```sql
WHERE total < 5000;
```

and:

```sql
WHERE total <= 5000;
```

These operators are common for:

- Prices
- Quantities
- Scores
- Limits
- Counters
- Dates
- Timestamps
- Version numbers

## Comparison Operator Reference

| Expression | Interpretation |
|---|---|
| `a = b` | `a` and `b` represent equal values |
| `a <> b` | `a` and `b` represent different values |
| `a > b` | `a` is greater than `b` |
| `a >= b` | `a` is greater than or equal to `b` |
| `a < b` | `a` is less than `b` |
| `a <= b` | `a` is less than or equal to `b` |

The exact comparison semantics can depend on the data types involved.

## Three-Valued Logic

SQL does not use only `TRUE` and `FALSE`.

Comparisons can produce:

- `TRUE`
- `FALSE`
- `UNKNOWN`

`NULL` is the primary reason for `UNKNOWN`.

Consider:

```sql
SELECT
    id,
    email
FROM users
WHERE email = 'user@example.com';
```

If `email` is `NULL`, then:

```text
NULL = 'user@example.com'
        ↓
     UNKNOWN
```

The row is not returned.

Likewise:

```sql
NULL = NULL
```

does not evaluate to `TRUE`.

Use:

```sql
IS NULL
```

instead:

```sql
WHERE email IS NULL;
```

### Why This Matters

A query such as:

```sql
WHERE deleted_at <> CURRENT_TIMESTAMP
```

does not mean:

> "All users who have not been deleted."

For soft deletes, the correct predicate is usually:

```sql
WHERE deleted_at IS NULL;
```

The distinction is fundamental to writing correct SQL.

## Equality vs NULL-Safe Equality

Different databases provide different mechanisms for comparing nullable values.

For PostgreSQL, the null-safe comparison operator is:

```sql
IS NOT DISTINCT FROM
```

Example:

```sql
SELECT
    id
FROM users
WHERE email IS NOT DISTINCT FROM $1;
```

This treats two `NULL` values as equivalent for comparison purposes.

Conceptually:

| `a` | `b` | `a = b` | `a IS NOT DISTINCT FROM b` |
|---|---|---|---|
| `x` | `x` | `TRUE` | `TRUE` |
| `x` | `y` | `FALSE` | `FALSE` |
| `NULL` | `x` | `UNKNOWN` | `FALSE` |
| `NULL` | `NULL` | `UNKNOWN` | `TRUE` |

This is useful when `NULL` itself is meaningful and should participate in equality semantics.

Database-specific null-safe operators differ, so portability should be considered.

## Comparing Numeric Values

Numeric comparisons are straightforward when compatible numeric types are used:

```sql
SELECT
    id,
    price
FROM products
WHERE price >= 1000;
```

For monetary values, use an appropriate exact numeric representation such as `NUMERIC`/`DECIMAL` rather than binary floating-point types when exact decimal arithmetic is required.

Example:

```sql
SELECT
    id,
    amount
FROM payments
WHERE amount >= 100.00;
```

Do not build financial correctness around approximate floating-point equality.

## Floating-Point Equality

Avoid assumptions such as:

```sql
WHERE calculated_value = 0.1;
```

when `calculated_value` is stored or computed using approximate floating-point representation.

For approximate numeric values, domain-appropriate tolerance logic may be necessary:

```sql
WHERE ABS(calculated_value - 0.1) < 0.000001;
```

However, this is a business/data-model decision, not a universal SQL rule.

For financial amounts, the better solution is generally to use an exact numeric type rather than compensating for floating-point representation with arbitrary tolerances.

## String Comparisons

String comparison semantics depend on:

- Database engine
- Collation
- Character set
- Data type
- Locale
- Operator

Exact equality:

```sql
SELECT
    id
FROM users
WHERE email = 'user@example.com';
```

Do not assume that:

```text
'User@example.com'
```

and:

```text
'user@example.com'
```

are equal.

If email addresses are application-defined as case-insensitive identifiers, model that requirement explicitly.

For PostgreSQL, one possible approach is `citext` or normalized storage, depending on the application's requirements.

## String Ordering

Comparison operators can also compare strings:

```sql
SELECT
    name
FROM products
WHERE name >= 'M';
```

The result depends on the database's collation and sorting rules.

Therefore, avoid using lexical comparison as a substitute for domain-specific ordering unless the collation behavior is explicitly understood.

This matters for:

- User-visible alphabetical ordering
- Internationalized applications
- Case-sensitive identifiers
- Unicode text
- Locale-aware search

## Date Comparison

Dates can be compared directly:

```sql
SELECT
    id,
    order_date
FROM orders
WHERE order_date >= DATE '2026-08-01';
```

This is useful for reporting and business rules.

Example:

```sql
SELECT
    id,
    expires_at
FROM subscriptions
WHERE expires_at < CURRENT_TIMESTAMP;
```

This identifies subscriptions that have expired.

The column type should represent the domain correctly. Do not store timestamps as arbitrary strings merely because they can be compared lexically.

## Timestamp Range Comparisons

For time ranges, prefer explicit lower and upper bounds:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= TIMESTAMP '2026-08-01 00:00:00'
  AND created_at <  TIMESTAMP '2026-08-02 00:00:00';
```

This represents:

```text
[2026-08-01 00:00:00, 2026-08-02 00:00:00)
```

The lower bound is inclusive and the upper bound is exclusive.

This half-open interval pattern avoids problems involving:

- Fractional seconds
- End-of-day calculations
- Timestamp precision
- Adjacent time windows

For timezone-aware systems, convert API-level date/time requirements into well-defined timestamps before constructing the SQL predicate.

## BETWEEN vs Explicit Comparisons

`BETWEEN` is inclusive:

```sql
WHERE amount BETWEEN 100 AND 500
```

is equivalent to:

```sql
WHERE amount >= 100
  AND amount <= 500
```

For timestamp windows, explicit comparisons are often preferable:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

This makes the boundary semantics explicit and avoids end-of-day timestamp hacks.

## Comparison with Expressions

Comparisons do not have to be between two simple columns.

Example:

```sql
SELECT
    id,
    price,
    quantity
FROM order_items
WHERE price * quantity >= 1000;
```

The database evaluates the expression and then compares the result.

This is useful, but expressions involving columns can affect index usage.

If this is a high-frequency query, evaluate whether the expression should be:

- Materialized
- Generated
- Indexed through an expression index
- Replaced with a more index-friendly predicate

## Column-to-Column Comparison

Columns can be compared directly:

```sql
SELECT
    id,
    shipped_at,
    delivered_at
FROM orders
WHERE delivered_at > shipped_at;
```

This can enforce business rules at query time.

Another example:

```sql
SELECT
    id
FROM accounts
WHERE current_balance < credit_limit;
```

Column-to-column comparisons can be useful, but ordinary indexes on individual columns may not directly optimize arbitrary relationships between two columns.

## Comparison with Subqueries

A comparison can involve a scalar subquery:

```sql
SELECT
    id,
    total
FROM orders
WHERE total > (
    SELECT AVG(total)
    FROM orders
);
```

This returns orders whose total exceeds the average order value.

For more complex queries, consider whether a CTE, window function, join, or precomputed aggregate is more appropriate.

The key production concern is to inspect the execution plan rather than assuming the subquery is cheap.

## Comparison Operators with JOINs

Comparison operators are fundamental to join predicates:

```sql
SELECT
    u.id,
    u.email,
    o.id AS order_id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

Range-based joins are also possible:

```sql
SELECT
    o.id,
    t.tax_rate
FROM orders AS o
JOIN tax_rates AS t
    ON o.total >= t.minimum_amount
   AND o.total < t.maximum_amount;
```

Range joins can be substantially more expensive than simple equality joins, so they should be designed and tested carefully for high-volume workloads.

## Comparison Operators and Boolean Logic

Comparison operators are often combined with `AND`, `OR`, and `NOT`.

Example:

```sql
SELECT
    id,
    total,
    status
FROM orders
WHERE status = 'completed'
  AND total >= 1000;
```

Multiple alternatives:

```sql
SELECT
    id,
    status
FROM orders
WHERE status = 'pending'
   OR status = 'processing';
```

When mixing `AND` and `OR`, use parentheses:

```sql
SELECT
    id,
    status,
    country
FROM users
WHERE (
    status = 'active'
    AND country = 'IN'
)
OR is_admin = TRUE;
```

This makes business logic explicit.

## Comparison Operators and `IN`

For equality against a known set, `IN` is often more readable:

```sql
SELECT
    id,
    status
FROM orders
WHERE status IN ('pending', 'processing', 'shipped');
```

Instead of:

```sql
WHERE status = 'pending'
   OR status = 'processing'
   OR status = 'shipped';
```

`IN` is conceptually a set-membership operation rather than a distinct comparison operator, but it belongs closely with equality-based filtering.

For very large dynamic sets, evaluate query planning and parameterization rather than generating unnecessarily large SQL statements.

## Comparison Operators and `LIKE`

Pattern matching is provided by `LIKE`:

```sql
SELECT
    id,
    name
FROM products
WHERE name LIKE 'Mac%';
```

A prefix pattern such as:

```sql
LIKE 'Mac%'
```

can potentially use a suitable index depending on the database and collation.

A leading wildcard:

```sql
LIKE '%Mac%'
```

usually cannot use a conventional B-tree index effectively.

For large-scale substring or relevance search, use appropriate database search capabilities or a dedicated search system rather than assuming comparison-based filtering will scale.

## Implicit Type Conversion

Comparisons between incompatible types can trigger implicit conversion depending on the database.

For example, an application might accidentally send a string where a numeric parameter is expected.

Avoid relying on implicit conversion.

Prefer:

- Correct database types
- Correct application parameter types
- Explicit casts when conversion is intentional

Example:

```sql
WHERE user_id = $1
```

with the application binding `$1` using the expected integer type is preferable to constructing SQL around textual representations.

Implicit conversions can affect:

- Correctness
- Index usage
- Query performance
- Portability
- Error behavior

## Sargability

Comparison predicates often determine whether an index can be used efficiently.

A sargable predicate preserves a form that allows the optimizer to search an indexed access path.

Good:

```sql
WHERE created_at >= $1;
```

Potentially problematic:

```sql
WHERE DATE(created_at) = $1;
```

The second form applies a function to the indexed column.

Prefer:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

If a transformation is genuinely required, a database-specific expression/function index may be appropriate.

## Index Selectivity

An index is most useful when the predicate can substantially reduce the candidate rows.

For example:

```sql
SELECT
    id
FROM users
WHERE email = $1;
```

is often highly selective if email is unique.

By contrast:

```sql
SELECT
    id
FROM users
WHERE is_active = TRUE;
```

may return a large fraction of the table.

A low-cardinality column is not automatically useless as an index, but the usefulness depends on:

- Table size
- Value distribution
- Query workload
- Additional predicates
- Index design
- Database optimizer

Do not choose indexes based solely on the presence of comparison operators.

## Composite Indexes

Suppose the common query is:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
  AND created_at >= $2
ORDER BY created_at DESC
LIMIT 50;
```

A composite index may be appropriate:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

The equality predicate on `customer_id` and range predicate on `created_at` align with the index structure.

The correct index still depends on the broader workload and should be validated with execution plans.

## Comparison Operators in Backend APIs

A REST endpoint may expose filters such as:

```text
GET /orders?min_total=1000&status=completed
```

The backend might translate this into:

```sql
SELECT
    id,
    total,
    status
FROM orders
WHERE status = $1
  AND total >= $2;
```

Parameters should be bound separately:

```python
query = """
    SELECT id, total, status
    FROM orders
    WHERE status = %s
      AND total >= %s
"""

cursor.execute(query, ("completed", 1000))
```

Never construct SQL by concatenating request parameters:

```python
query = (
    "SELECT id FROM orders "
    f"WHERE total >= {request.query_params['min_total']}"
)
```

Parameterized SQL protects values from SQL injection and gives the database driver control over value encoding.

## Comparison Operators in Django

Django's ORM expresses comparisons through lookup operators:

```python
Order.objects.filter(total__gte=1000)
```

Common mappings include:

| SQL | Django ORM |
|---|---|
| `=` | `field=value` |
| `>` | `field__gt=value` |
| `>=` | `field__gte=value` |
| `<` | `field__lt=value` |
| `<=` | `field__lte=value` |
| `<>` / `!=` | `exclude(field=value)` |

Example:

```python
orders = (
    Order.objects
    .filter(status="completed", total__gte=1000)
    .order_by("-created_at")
)
```

The ORM does not remove the need to understand SQL. For production performance, engineers should still inspect the generated query and execution plan when necessary.

## Comparison Operators and Security

Comparison predicates can enforce data-access boundaries.

For example, a multi-tenant system should not simply query:

```sql
SELECT
    id,
    total
FROM invoices
WHERE id = $1;
```

If ownership matters, the predicate may need to include tenant scope:

```sql
SELECT
    id,
    total
FROM invoices
WHERE id = $1
  AND tenant_id = $2;
```

The tenant identifier should come from trusted authentication context rather than blindly accepting a client-supplied value.

Comparison predicates can therefore be part of the application's security model.

They should not, however, be treated as a substitute for stronger database authorization mechanisms when those are required.

## Production Performance Considerations

For frequently executed comparison queries:

- Use the correct data types.
- Keep predicates sargable where practical.
- Avoid unnecessary functions around indexed columns.
- Use parameterized queries.
- Inspect execution plans.
- Test with production-scale data volumes.
- Consider selectivity when designing indexes.
- Use composite indexes for common multi-column access patterns.
- Avoid unbounded API queries.
- Monitor query latency and database resource consumption.

For PostgreSQL, a useful diagnostic command is:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    total
FROM orders
WHERE customer_id = 123
  AND created_at >= TIMESTAMP '2026-08-01 00:00:00';
```

Look at:

- Actual execution time
- Estimated versus actual rows
- Scan type
- Index usage
- Rows removed by filters
- Buffer hits
- Buffer reads

An index scan is not automatically better than a sequential scan. The optimizer may correctly choose a sequential scan when a large portion of the table qualifies.

## Common Mistakes

### Using `= NULL`

Incorrect:

```sql
WHERE deleted_at = NULL
```

Correct:

```sql
WHERE deleted_at IS NULL
```

### Assuming `<>` Includes NULL

This:

```sql
WHERE status <> 'deleted'
```

does not include rows where `status` is `NULL`.

Explicitly define the desired behavior.

### Using Floating-Point Equality for Financial Data

Avoid:

```sql
WHERE amount = 100.10
```

when `amount` uses an approximate floating-point representation and exact equality is required.

Use an appropriate exact numeric type for financial values.

### Comparing Incompatible Types

Avoid relying on implicit casts between application values and database columns.

Type mismatches can cause:

- Runtime errors
- Unexpected semantics
- Poor query plans
- Index access problems

### Applying Functions to Indexed Columns

Potentially problematic:

```sql
WHERE DATE(created_at) = $1
```

Prefer a range:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

### Forgetting Parentheses

Ambiguous:

```sql
WHERE status = 'active'
   OR status = 'pending'
  AND country = 'IN';
```

Explicit:

```sql
WHERE (
    status = 'active'
    OR status = 'pending'
)
AND country = 'IN';
```

### Assuming `=` Means Semantic Equality

Equality is defined by the database's type and comparison semantics.

Case sensitivity, collation, timezone handling, numeric representation, and `NULL` behavior all matter.

### Assuming an Index Guarantees Performance

The optimizer may choose a different access path based on:

- Selectivity
- Table size
- Statistics
- Cost estimates
- Query shape

Always validate important queries with execution plans.

### Building SQL with Request Values

Never interpolate request parameters directly into SQL.

Use parameterized queries or framework query APIs.

## Interview Traps

| Question | Strong answer |
|---|---|
| What comparison operators does SQL provide? | Common operators are `=`, `<>`, `!=`, `>`, `>=`, `<`, and `<=`; exact support varies by database. |
| Why doesn't `column = NULL` work? | `NULL` represents an unknown/absent value, so ordinary comparison produces `UNKNOWN`; use `IS NULL`. |
| What happens when a comparison returns `UNKNOWN` in `WHERE`? | The row is filtered out because `WHERE` retains only predicates evaluating to `TRUE`. |
| Is `NULL = NULL` true? | No. It evaluates to `UNKNOWN` under standard SQL semantics. |
| What is the difference between `<>` and `!=`? | Both commonly mean not-equal, but `<>` is the standard SQL operator and is preferable for portability. |
| Why can timestamp comparisons using `BETWEEN` be problematic? | `BETWEEN` is inclusive on both ends; explicit half-open ranges avoid precision and boundary issues. |
| What is a sargable predicate? | A predicate whose structure allows the database to efficiently use an index or other search access path. |
| Why can `DATE(created_at) = ...` hurt performance? | Applying a function to the indexed column can prevent efficient use of a normal index. |
| Does an index guarantee that a comparison query uses the index? | No. The optimizer chooses the access path based on cost, statistics, selectivity, and query shape. |
| Why does data type matter when comparing values? | Types determine comparison semantics and can affect correctness, implicit conversion, index usage, and query performance. |
| How should API comparison filters be implemented? | Validate input and use parameterized queries or ORM APIs rather than concatenating request values into SQL. |
| How should nullable equality be handled when `NULL` itself should compare equal? | Use database-specific null-safe comparison semantics, such as PostgreSQL's `IS NOT DISTINCT FROM`, when appropriate. |

## Key Takeaways

- Comparison operators define relational predicates, but their behavior depends on data types, `NULL`, collation, precision, and database-specific semantics.
- SQL uses three-valued logic, so `NULL` must be handled explicitly with `IS NULL`, `IS NOT NULL`, or appropriate null-safe comparison operators.
- For production performance, preserve sargability, use appropriate indexes, avoid unnecessary functions or implicit conversions, and verify important queries with execution plans.
- Use explicit range boundaries for timestamps, especially half-open intervals such as `>= start AND < end`, to avoid precision and end-of-day bugs.
- In backend systems, comparison predicates should be parameterized, validated, and designed together with authorization, tenant isolation, pagination, and data-access requirements.