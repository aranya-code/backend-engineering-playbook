# README

## Overview

SQL operators define how query predicates compare values, combine conditions, test membership, perform calculations, and express relationships between rows. They are foundational to writing correct `WHERE`, `JOIN`, `HAVING`, `ORDER BY`, and `SELECT` expressions.

This section focuses on both operator syntax and engineering judgment. Correct operator selection affects:

- Query correctness and NULL behavior
- Boolean expression semantics
- Index usability and execution plans
- Query performance at scale
- Multi-tenant data isolation
- Application security
- ORM-generated SQL
- Portability across SQL databases

The goal is not to memorize every operator, but to understand **which operator expresses the required business condition and what database behavior follows from that choice**.

## Operator Categories

| Category | Operators / Constructs | Primary Use |
|---|---|---|
| Arithmetic | `+`, `-`, `*`, `/`, `%` | Numeric calculations |
| Comparison | `=`, `<>`, `!=`, `>`, `<`, `>=`, `<=` | Comparing values |
| Logical | `AND`, `OR`, `NOT` | Combining or negating predicates |
| Membership | `IN`, `NOT IN` | Testing membership in a set |
| Existence | `EXISTS`, `NOT EXISTS` | Testing related-row existence |
| NULL | `IS NULL`, `IS NOT NULL` | Testing NULL state |
| Range | `BETWEEN` | Inclusive range checks |
| Pattern | `LIKE` | Pattern matching |
| Bitwise | `&`, `|`, `^`, `~` and dialect-specific variants | Bit-level operations |
| String | `||`, `CONCAT()`, dialect-specific operators | String construction |

Exact operator availability and behavior can vary by database engine.

## Operator Selection

Operator choice should begin with the business requirement rather than syntax familiarity.

| Requirement | Typical choice |
|---|---|
| Match one known value | `=` |
| Exclude one value | `<>` |
| Match several known values | `IN` |
| Determine whether a related row exists | `EXISTS` |
| Determine whether no related row exists | `NOT EXISTS` |
| Check for NULL | `IS NULL` |
| Check for a non-NULL value | `IS NOT NULL` |
| Test an inclusive range | `BETWEEN` |
| Define a timestamp window | `>= start AND < end` |
| Match a text pattern | `LIKE` |
| Require multiple conditions | `AND` |
| Allow alternative conditions | `OR` |
| Negate a predicate | `NOT` |
| Perform numeric calculation | Arithmetic operators |

A useful engineering sequence is:

```text
Business requirement
       ↓
Choose operator semantics
       ↓
Check NULL behavior
       ↓
Check data types
       ↓
Check cardinality
       ↓
Check indexes
       ↓
Inspect execution plan
       ↓
Validate with representative data
```

## Equality and Comparison Operators

Equality uses:

```sql
WHERE status = 'paid'
```

Inequality is commonly expressed as:

```sql
WHERE status <> 'cancelled'
```

Some databases also support:

```sql
WHERE status != 'cancelled'
```

Comparison operators include:

```sql
=
<>
!=
>
<
>=
<=
```

They are commonly used for filtering, joins, validation, and range queries.

### NULL Consideration

Comparison operators do not behave like ordinary programming-language equality when `NULL` is involved.

This is incorrect for checking NULL:

```sql
WHERE deleted_at = NULL
```

Use:

```sql
WHERE deleted_at IS NULL
```

Likewise:

```sql
WHERE deleted_at IS NOT NULL
```

## Logical Operators

`AND`, `OR`, and `NOT` combine predicates.

```sql
SELECT *
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'paid';
```

Multiple alternatives can be expressed using `OR`:

```sql
WHERE status = 'paid'
   OR status = 'pending'
```

For a finite set of values, `IN` is often clearer:

```sql
WHERE status IN ('paid', 'pending')
```

### Parentheses

When mixing `AND` and `OR`, explicitly group conditions:

```sql
WHERE tenant_id = :tenant_id
  AND (status = 'paid' OR status = 'pending')
```

This is particularly important for authorization and multi-tenant queries.

A missing parenthesis can change:

```sql
tenant_id = :tenant_id
AND (A OR B)
```

into:

```sql
(tenant_id = :tenant_id AND A)
OR B
```

potentially exposing rows belonging to another tenant.

## Membership Operators

`IN` expresses membership in a finite set:

```sql
WHERE country_code IN ('IN', 'US', 'GB')
```

It is generally preferable to repeating the same equality predicate:

```sql
WHERE country_code = 'IN'
   OR country_code = 'US'
   OR country_code = 'GB'
```

`NOT IN` expresses exclusion:

```sql
WHERE country_code NOT IN ('IN', 'US')
```

However, `NOT IN` has important NULL semantics. When a subquery can produce NULL values, `NOT EXISTS` is often the safer expression for anti-join logic.

For example:

```sql
SELECT u.id
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_users AS b
    WHERE b.user_id = u.id
);
```

## Existence Operators

Use `EXISTS` when the requirement is:

> Does at least one related row satisfy this condition?

Example:

```sql
SELECT c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

Use `NOT EXISTS` when the requirement is:

> Does no related row satisfy this condition?

```sql
SELECT c.id
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'refunded'
);
```

The database optimizer may transform `EXISTS` into a semi-join and `NOT EXISTS` into an anti-join. Do not assume that `EXISTS` is universally faster than an equivalent join; validate important queries with execution plans.

## Range Operators

`BETWEEN` is inclusive:

```sql
WHERE price BETWEEN 100 AND 500
```

is equivalent to:

```sql
WHERE price >= 100
  AND price <= 500
```

For timestamp windows, half-open intervals are generally easier to compose:

```sql
WHERE created_at >= :start_time
  AND created_at < :end_time
```

This avoids precision problems associated with trying to represent the last instant of a time period.

For example:

```text
[2026-08-30 00:00, 2026-08-31 00:00)
```

includes the start boundary and excludes the end boundary.

This pattern works well for:

- API date filters
- Daily reports
- Billing windows
- Event processing
- Incremental jobs
- Analytics queries

## Pattern Matching

`LIKE` performs pattern matching:

```sql
WHERE name LIKE 'Aranya%'
```

Common patterns include:

| Pattern | Meaning |
|---|---|
| `'abc'` | Exact pattern |
| `'abc%'` | Starts with `abc` |
| `'%abc'` | Ends with `abc` |
| `'%abc%'` | Contains `abc` |
| `'a_c'` | `_` matches one character |

A leading wildcard can make ordinary B-tree index usage ineffective for the pattern search:

```sql
WHERE name LIKE '%arya%'
```

If arbitrary substring search is a major production requirement, use an indexing/search strategy designed for that workload rather than assuming a conventional B-tree index is sufficient.

## Arithmetic Operators

Arithmetic operators perform database-side calculations:

```sql
SELECT
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items;
```

Common arithmetic operators include:

```text
+    Addition
-    Subtraction
*    Multiplication
/    Division
%    Modulo, where supported
```

Database-side arithmetic is useful when calculations participate in:

- Filtering
- Aggregation
- Sorting
- Reporting
- Transactional calculations

For frequently executed business calculations, consider whether the value should instead be represented through schema design, generated data, or application logic.

## Bitwise Operators

Bitwise operators manipulate individual bits of integer values.

They can be useful for:

- Compact permission masks
- Feature flags
- Protocol fields
- Packed status values
- Low-level data processing

Example concept:

```text
Permission mask
00000101
   ↑ ↑
   │ └── Permission B
   └──── Permission A
```

A database-specific expression such as:

```sql
permissions & 4
```

can test whether a particular bit is set, depending on the database dialect.

Bitwise operators are powerful but reduce readability when used as a general-purpose application authorization model. For complex permissions, explicit relational structures are usually easier to audit and maintain.

## String Operators

String concatenation is database-specific.

PostgreSQL commonly uses:

```sql
SELECT first_name || ' ' || last_name AS full_name
FROM users;
```

Other databases may use functions such as:

```sql
CONCAT(first_name, ' ', last_name)
```

Do not assume that string operators are portable across database engines.

For presentation-heavy formatting, application-layer formatting may be preferable. Database-side string operations are appropriate when the computed value is required by the query itself, such as filtering, sorting, or returning a derived database value.

## Operator Precedence

SQL operators have precedence rules. In common SQL expressions:

```sql
WHERE a = 1
   OR b = 2
  AND c = 3
```

is interpreted as:

```sql
WHERE a = 1
   OR (b = 2 AND c = 3)
```

Do not depend on implicit precedence when the business rule is important.

Prefer:

```sql
WHERE (a = 1 OR b = 2)
  AND c = 3
```

when that is the intended condition.

Explicit grouping improves readability, reviewability, and safety.

## NULL and Three-Valued Logic

SQL predicates can evaluate to:

```text
TRUE
FALSE
UNKNOWN
```

For example:

```sql
5 = NULL
```

does not evaluate to `TRUE` or ordinary `FALSE`; it evaluates to `UNKNOWN`.

A `WHERE` clause returns rows only when its predicate evaluates to `TRUE`.

This affects:

- Comparisons
- `NOT`
- `AND`
- `OR`
- `IN`
- `NOT IN`
- Joins
- Aggregation filters

For production SQL, always ask:

> What happens if one of the participating values is NULL?

This question prevents many silent correctness bugs.

## Operators and Indexes

Operator selection can influence index access.

Typical examples:

```sql
WHERE user_id = :user_id
```

and:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

are natural candidates for B-tree index access when appropriate indexes exist.

By contrast:

```sql
WHERE LOWER(email) = LOWER(:email)
```

may require an expression/functional index.

A query such as:

```sql
WHERE name LIKE '%search%'
```

usually requires a specialized search/indexing strategy for efficient large-scale substring lookup.

The engineering workflow should be:

1. Preserve correct semantics.
2. Identify the expected access pattern.
3. Create or adjust the appropriate index.
4. Run `EXPLAIN` or the database-specific execution-plan tool.
5. Test against production-like cardinality.

Do not change a correct predicate into an incorrect one merely to force an index.

## Operators in Backend Applications

### Django

Django exposes SQL operators through ORM expressions.

Membership:

```python
orders = Order.objects.filter(
    status__in=["paid", "pending"],
)
```

NULL:

```python
orders = Order.objects.filter(
    deleted_at__isnull=True,
)
```

Explicit Boolean grouping:

```python
from django.db.models import Q

orders = Order.objects.filter(
    tenant_id=tenant_id,
).filter(
    Q(status="paid") | Q(status="pending"),
)
```

The ORM simplifies query construction but does not remove SQL semantics.

### SQLAlchemy and FastAPI

FastAPI does not define SQL operator behavior; the database layer does. With SQLAlchemy:

```python
from sqlalchemy import select

stmt = select(Order).where(
    Order.tenant_id == tenant_id,
    Order.status.in_(["paid", "pending"]),
)
```

For NULL:

```python
stmt = select(Order).where(
    Order.deleted_at.is_(None),
)
```

Prefer expression APIs over manually concatenating SQL strings.

## Security Considerations

Operators themselves are not a substitute for parameterized queries.

Unsafe:

```python
query = f"""
SELECT *
FROM payments
WHERE amount {operator} {value}
"""
```

If the application allows users to choose an operator, map only approved application values to trusted SQL syntax:

```python
ALLOWED_OPERATORS = {
    "eq": "=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
}

sql_operator = ALLOWED_OPERATORS[user_operator]
```

Values should remain parameterized.

This distinction is important:

```text
User value       → parameterized
SQL syntax       → trusted allowlist
```

Never treat unrestricted user input as SQL syntax.

## Production Considerations

### Performance

Review:

- Predicate selectivity
- Available indexes
- Query cardinality
- Execution plans
- Large `IN` lists
- Leading wildcard searches
- Functions applied to columns
- Implicit type conversions
- Complex `OR` predicates

### Scalability

Avoid designs that require:

- Huge SQL statements
- Repeated full-table scans
- Application-side filtering of large result sets
- Massive dynamic `IN` lists

Represent large collections as relational data where appropriate.

### Reliability

Use explicit range boundaries and deterministic predicates for:

- Batch processing
- Incremental synchronization
- Reporting
- Event consumers
- Scheduled jobs

For example:

```sql
WHERE created_at >= :last_checkpoint
  AND created_at < :current_checkpoint
```

This is easier to reason about than timestamp logic based on approximate final values.

### Multi-Tenant Systems

Tenant predicates must remain logically connected to every relevant condition:

```sql
WHERE tenant_id = :tenant_id
  AND status IN ('paid', 'pending')
```

Be particularly careful with `OR`:

```sql
WHERE tenant_id = :tenant_id
  AND (condition_a OR condition_b)
```

SQL predicate correctness is part of the application's data-isolation boundary.

## Common Mistakes

| Mistake | Risk | Preferred approach |
|---|---|---|
| `column = NULL` | Predicate does not perform NULL checking | `IS NULL` |
| `NOT IN` with nullable data | Unexpected three-valued logic | Prefer `NOT EXISTS` where appropriate |
| Missing `AND`/`OR` parentheses | Incorrect result set or data exposure | Explicitly group conditions |
| Timestamp `BETWEEN` to `23:59:59` | Precision gaps | `>= start AND < end` |
| `LIKE` for exact matching | Unnecessary pattern semantics | `=` |
| Leading wildcard with B-tree assumption | Poor search performance | Use suitable search/index strategy |
| Huge `IN` lists | Large statements and planning overhead | Use relational representations |
| `JOIN` when only existence is needed | Duplicate intermediate rows | Consider `EXISTS` |
| Function on indexed column | Index may not support expression | Use functional index or normalize data |
| Implicit type conversion | Unexpected semantics/performance | Use compatible parameter types |
| Dynamic SQL operators | SQL injection risk | Allowlist SQL syntax |
| Assuming ORM removes SQL complexity | Hidden semantic bugs | Understand generated SQL |

## Interview-Focused Rules

### `IN` vs `EXISTS`

Use `IN` for membership in a known set and `EXISTS` when the question is whether a related row exists.

Do not claim that one is always faster. Query optimization is database- and data-dependent.

### `NOT IN` vs `NOT EXISTS`

`NOT EXISTS` is often safer for anti-join semantics because `NOT IN` interacts with NULL values in unintuitive ways.

### `BETWEEN`

`BETWEEN` is inclusive on both sides.

For timestamp windows, prefer:

```sql
WHERE timestamp_column >= :start
  AND timestamp_column < :end
```

when the application uses adjacent intervals.

### `NULL`

`NULL` is not compared using `=` or `<>`.

Use:

```sql
IS NULL
IS NOT NULL
```

### `AND` vs `OR`

`AND` generally has higher precedence than `OR`, but production SQL should use explicit parentheses when mixed Boolean conditions affect correctness.

### Indexes

An operator being logically valid does not mean the query is efficient. Validate important predicates using the actual execution plan and representative data.

## Navigation

- [01- Arithmetic Operators](./01-%20Arithmetic%20Operators.md)
- [02- Comparison Operators](./02-%20Comparison%20Operators.md)
- [03- Logical Operators](./03-%20Logical%20Operators.md)
- [04- Bitwise Operators](./04-%20Bitwise%20Operators.md)
- [05- String Operators](./05-%20String%20Operators.md)
- [06- Operator Precedence](./06-%20Operator%20Precedence.md)
- [07- Operator Selection Rules](./07-%20Operator%20Selection%20Rules.md)
- [08- Common Operator Mistakes](./08-%20Common%20Operator%20Mistakes.md)

---

## Key Takeaways

- Select operators based on **business semantics first**, then validate NULL behavior, cardinality, indexability, and execution plans.
- Treat `NULL` as a distinct SQL concern: use `IS NULL`, understand three-valued logic, and be especially careful with `NOT IN`.
- Explicitly group mixed `AND`/`OR` predicates and use half-open timestamp ranges to avoid silent correctness and data-isolation bugs.
- Use `IN`, `EXISTS`, `NOT EXISTS`, `LIKE`, and arithmetic operators according to their intended semantics rather than assuming one construct is universally faster.
- Keep SQL syntax trusted and values parameterized; operator selection is simultaneously a **correctness, performance, and security** concern.