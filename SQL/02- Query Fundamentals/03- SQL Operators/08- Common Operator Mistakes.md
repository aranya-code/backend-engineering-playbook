# 08- Common Operator Mistakes

## Overview

SQL operators are small syntactic constructs, but incorrect operator selection can cause silent data loss, incorrect authorization decisions, broken reporting, and inefficient execution plans.

The most dangerous mistakes are often not syntax errors. The query executes successfully but produces the wrong result because of:

- `NULL` and three-valued logic
- Incorrect `AND`/`OR` grouping
- Inclusive versus exclusive range boundaries
- `NOT IN` with nullable values
- Confusing equality with pattern matching
- Unexpected implicit type conversion
- Incorrect assumptions about operator precedence
- Large `IN` lists
- Applying functions to indexed columns without an index strategy
- Using joins where existence semantics are more appropriate

A production SQL review should therefore ask two separate questions:

1. **Is the predicate logically correct?**
2. **Can the database execute it efficiently at the expected scale?**

## NULL Comparison Mistakes

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

`NULL` represents an unknown or missing value. It is not equal to any value, including another `NULL`.

### Mistake: `= NULL`

Incorrect:

```sql
SELECT *
FROM users
WHERE deleted_at = NULL;
```

Correct:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

Similarly:

```sql
WHERE deleted_at IS NOT NULL
```

must be used for non-NULL values.

### Why It Happens

Developers often transfer normal programming-language equality semantics directly into SQL.

Conceptually:

```sql
5 = NULL
```

evaluates to `UNKNOWN`, not `FALSE`.

A `WHERE` clause only retains rows for which the predicate evaluates to `TRUE`.

### Production Impact

This mistake is especially dangerous in:

- Soft-delete queries
- Optional relationships
- Data-quality reports
- Filtering nullable business attributes
- Multi-tenant queries

A query can return zero rows without generating any error.

## `NOT IN` and NULL

`NOT IN` is one of the most common SQL operator traps.

Consider:

```sql
SELECT *
FROM users
WHERE id NOT IN (
    SELECT user_id
    FROM blocked_users
);
```

If the subquery can return `NULL`, the predicate can become `UNKNOWN` for candidate rows that do not match a concrete blocked ID.

### Safer Anti-Existence Pattern

Use `NOT EXISTS` when the business requirement is "no matching related row exists":

```sql
SELECT u.*
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_users AS b
    WHERE b.user_id = u.id
);
```

The semantics are explicit and do not suffer from the same `NOT IN`/NULL trap.

### Prevention

If `NOT IN` is genuinely appropriate, understand and control NULLability:

```sql
WHERE id NOT IN (
    SELECT user_id
    FROM blocked_users
    WHERE user_id IS NOT NULL
)
```

Even then, `NOT EXISTS` may communicate the intent better.

## Incorrect `AND` and `OR` Grouping

Consider:

```sql
SELECT *
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'paid'
  OR status = 'pending';
```

This is interpreted according to SQL operator precedence as:

```sql
WHERE (tenant_id = :tenant_id AND status = 'paid')
   OR status = 'pending'
```

That can allow `pending` orders from other tenants.

### Correct Version

If the intended rule is:

> Return paid or pending orders belonging to this tenant.

write:

```sql
SELECT *
FROM orders
WHERE tenant_id = :tenant_id
  AND (status = 'paid' OR status = 'pending');
```

Or, preferably:

```sql
SELECT *
FROM orders
WHERE tenant_id = :tenant_id
  AND status IN ('paid', 'pending');
```

### Production Risk

This is particularly dangerous in multi-tenant and authorization-sensitive queries.

A missing pair of parentheses can become a data-isolation vulnerability rather than merely a correctness bug.

### Rule

When `AND` and `OR` appear in the same predicate, use parentheses to make the intended grouping explicit unless the expression is trivially obvious.

## Incorrect Assumptions About Operator Precedence

SQL evaluates operators according to precedence rules defined by the database dialect.

For example:

```sql
WHERE a = 1 OR b = 2 AND c = 3
```

is generally interpreted as:

```sql
WHERE a = 1
   OR (b = 2 AND c = 3)
```

not:

```sql
WHERE (a = 1 OR b = 2)
  AND c = 3
```

Do not rely on readers remembering precedence rules.

Prefer:

```sql
WHERE (a = 1 OR b = 2)
  AND c = 3
```

or:

```sql
WHERE a = 1
   OR (b = 2 AND c = 3)
```

depending on the business requirement.

Explicit grouping improves:

- Code review
- Maintenance
- ORM translation
- Refactoring safety
- Security analysis

## Incorrect Range Boundaries

A common mistake is treating a timestamp range as if timestamps only had second-level precision.

Avoid:

```sql
WHERE created_at BETWEEN
    '2026-08-30 00:00:00'
    AND '2026-08-30 23:59:59'
```

This can exclude rows occurring after `23:59:59` but still within the intended day when higher timestamp precision is stored.

Prefer:

```sql
WHERE created_at >= '2026-08-30 00:00:00'
  AND created_at <  '2026-08-31 00:00:00'
```

This defines:

```text
[start, end)
```

and works cleanly for adjacent time windows.

### Why This Matters

The same pattern works for:

- Daily reports
- Monthly billing
- Event processing
- Audit queries
- API date filters
- Incremental data processing

For example:

```sql
WHERE created_at >= :window_start
  AND created_at < :window_end
```

is generally safer than trying to manufacture the final timestamp inside the window.

## Misusing `BETWEEN`

`BETWEEN` is inclusive on both boundaries.

```sql
WHERE price BETWEEN 100 AND 500
```

means:

```sql
WHERE price >= 100
  AND price <= 500
```

For numeric ranges, this may be exactly what is wanted.

For adjacent temporal ranges, however, half-open intervals are usually easier to reason about:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

### Boundary Checklist

Before using `BETWEEN`, ask:

- Should the lower boundary be included?
- Should the upper boundary be included?
- Can adjacent ranges overlap?
- What precision does the column use?
- Is the value continuous, such as a timestamp?

## Using Equality for Pattern Matching

Incorrect when prefix matching is required:

```sql
WHERE email = '%@example.com'
```

`=` does not interpret `%` as a wildcard.

Use:

```sql
WHERE email LIKE '%@example.com'
```

Similarly:

```sql
WHERE name LIKE 'Aranya%'
```

means the value starts with `Aranya`.

### Common Pattern Mistake

Developers sometimes use:

```sql
WHERE email LIKE 'user@example.com'
```

when exact equality is intended.

Prefer:

```sql
WHERE email = 'user@example.com'
```

when there is no wildcard requirement.

This communicates intent and avoids unnecessary pattern-matching semantics.

## Leading Wildcard Performance Problems

This query:

```sql
WHERE name LIKE '%arya%'
```

usually cannot use a normal B-tree index for efficient prefix lookup.

A normal B-tree index is much more naturally suited to:

```sql
WHERE name LIKE 'arya%'
```

under the relevant database and collation/index configuration.

### Production Guidance

If arbitrary substring search is a core requirement, design for it explicitly.

Depending on the database and workload, consider:

- Trigram indexes
- Full-text search
- Specialized search engines
- Search-oriented database features

Do not assume that adding a conventional B-tree index automatically makes every `LIKE` query fast.

## Replacing `EXISTS` With a Join

Suppose the requirement is:

> Return customers who have at least one paid order.

A common implementation is:

```sql
SELECT DISTINCT c.id
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.id
WHERE o.status = 'paid';
```

This is valid, but the join can produce multiple rows per customer before `DISTINCT` removes duplicates.

The existence semantics can be expressed directly:

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

The optimizer may transform both queries into efficient equivalent strategies, so this is not a universal performance rule. The important point is to express the required cardinality clearly and verify performance with an execution plan.

## Using `JOIN` When `EXISTS` Is Required

The opposite mistake is also possible.

If the application only needs customers:

```sql
SELECT c.*
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.id
WHERE o.status = 'paid';
```

can return the same customer multiple times when multiple paid orders exist.

If duplicates are not intended, either use:

```sql
SELECT DISTINCT c.*
```

or, often more naturally:

```sql
WHERE EXISTS (...)
```

Do not use `DISTINCT` as a reflexive fix for a query whose join cardinality was never understood.

## Huge `IN` Lists

This is acceptable for a small, controlled set:

```sql
WHERE status IN ('pending', 'processing', 'paid')
```

It becomes problematic when an application dynamically generates thousands or tens of thousands of values:

```sql
WHERE id IN (?, ?, ?, ?, ...);
```

Potential problems include:

- Large SQL statements
- Parameter limits
- Increased parsing/planning overhead
- Network overhead
- Memory consumption
- Difficult query observability

### Better Alternatives

For large dynamic collections, consider representing the values as relational data.

Examples include:

```sql
CREATE TEMPORARY TABLE requested_ids (
    id BIGINT PRIMARY KEY
);
```

Then:

```sql
SELECT u.*
FROM users AS u
JOIN requested_ids AS r
  ON r.id = u.id;
```

Other database-specific options include:

- `VALUES` relations
- Array parameters
- Temporary tables
- Staging tables
- Permanent lookup tables

Choose based on workload, transaction boundaries, database capabilities, and operational requirements.

## Implicit Type Conversion

Avoid relying on the database to reconcile mismatched types.

For example, if:

```sql
user_id BIGINT
```

the application should bind an integer-compatible value rather than deliberately passing a string representation.

Potential consequences of implicit conversion include:

- Unexpected semantics
- Reduced portability
- Hidden application bugs
- Additional conversion work
- In some cases, reduced index effectiveness

The exact behavior is database-specific.

### Production Rule

Align:

```text
API input
    ↓
Application type
    ↓
Driver parameter type
    ↓
Database column type
```

Use explicit conversions when conversion is intentional and understood.

## Applying Functions to Indexed Columns

Consider:

```sql
WHERE LOWER(email) = LOWER(:email)
```

The expression is logically reasonable for case-insensitive matching, but a normal index on:

```sql
email
```

may not be sufficient for the transformed expression.

A database such as PostgreSQL can support an appropriate functional index:

```sql
CREATE INDEX idx_users_lower_email
ON users (LOWER(email));
```

Then the query and index are aligned.

### Mistake

Adding an index on:

```sql
email
```

and assuming it automatically optimizes:

```sql
LOWER(email)
```

is unsafe.

### Better Approach

Design the lookup semantics and index together:

```text
Business lookup requirement
        ↓
Predicate expression
        ↓
Data normalization / type
        ↓
Matching index strategy
        ↓
Execution plan validation
```

## Confusing `COUNT(*)` With Operator Semantics

When checking existence, avoid unnecessarily counting all matching rows:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = :customer_id
  AND status = 'paid';
```

if the only question is:

> Does at least one row exist?

Prefer:

```sql
SELECT EXISTS (
    SELECT 1
    FROM orders
    WHERE customer_id = :customer_id
      AND status = 'paid'
);
```

The existence query communicates the requirement directly and can avoid work after a qualifying row is found, depending on the execution plan.

## Incorrect Negation

Negation can become difficult to reason about when combined with `NULL` and Boolean operators.

For example:

```sql
WHERE NOT (status = 'cancelled')
```

does not necessarily mean:

```text
status is any value except cancelled
```

A NULL status produces an `UNKNOWN` comparison, and negating `UNKNOWN` remains `UNKNOWN`.

If NULL should be included:

```sql
WHERE status <> 'cancelled'
   OR status IS NULL
```

Always define whether NULL represents:

- Unknown
- Not applicable
- Missing
- A default state

before writing negative predicates.

## Operator Mistakes in Multi-Tenant Queries

Tenant isolation should be explicit in every applicable query.

Risky:

```sql
SELECT *
FROM orders
WHERE status = 'paid'
   OR status = 'pending'
  AND tenant_id = :tenant_id;
```

The precedence can allow paid rows from other tenants.

Safer:

```sql
SELECT *
FROM orders
WHERE tenant_id = :tenant_id
  AND status IN ('paid', 'pending');
```

The tenant predicate should not depend on a developer correctly remembering precedence.

### Production Recommendation

For multi-tenant systems:

- Make tenant filtering explicit.
- Centralize query construction where appropriate.
- Test cross-tenant access.
- Review `OR` predicates carefully.
- Consider database-level isolation mechanisms where the architecture requires stronger guarantees.

SQL correctness is part of the security boundary.

## Dynamic Operator Injection

Values should always be parameterized:

```python
cursor.execute(
    """
    SELECT id, amount
    FROM payments
    WHERE amount >= %s
    """,
    (minimum_amount,),
)
```

Do not directly concatenate user-controlled SQL fragments.

Unsafe:

```python
query = f"""
SELECT *
FROM payments
WHERE amount {operator} {value}
"""
```

If the application needs selectable operators, use an allowlist:

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

The SQL fragment is selected from trusted application code, while values remain parameterized.

## ORM-Specific Operator Mistakes

ORM abstractions do not eliminate SQL semantics.

### Django

Use `Q` objects when explicit Boolean grouping is required:

```python
from django.db.models import Q

orders = Order.objects.filter(
    tenant_id=tenant_id,
).filter(
    Q(status="paid") | Q(status="pending")
)
```

This corresponds to:

```sql
tenant_id = ?
AND (status = 'paid' OR status = 'pending')
```

For NULL:

```python
orders = Order.objects.filter(
    deleted_at__isnull=True
)
```

For membership:

```python
orders = Order.objects.filter(
    status__in=["paid", "pending"]
)
```

### SQLAlchemy

Use SQL expression operators rather than constructing SQL fragments manually:

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
    Order.deleted_at.is_(None)
)
```

The ORM generates SQL, but the database still applies SQL's comparison, NULL, and Boolean semantics.

## Operator Mistakes That Affect Indexes

An operator can be logically correct but operationally expensive.

| Query pattern | Potential concern |
|---|---|
| `column = :value` | Usually straightforward for a compatible B-tree index |
| `column >= :value` | Often suitable for range access |
| `column LIKE 'prefix%'` | May support indexed prefix lookup depending on database/configuration |
| `column LIKE '%text%'` | Usually unsuitable for ordinary B-tree prefix lookup |
| `LOWER(column) = ...` | May require a functional index |
| `column + 1 = :value` | Transformation may prevent straightforward index use |
| Huge `IN (...)` | Large statement and planning overhead |
| `OR` across unrelated columns | May produce less efficient plans depending on data and indexes |
| Implicit casts | Can complicate planning/index usage depending on database |

The correct response is not to avoid operators that may be expensive. Instead:

1. Confirm the required semantics.
2. Inspect the schema.
3. Check indexes.
4. Examine the execution plan.
5. Test representative data volumes.

## Common Mistake Matrix

| Mistake | Why it happens | Correct approach |
|---|---|---|
| `column = NULL` | Treating NULL like a normal value | `IS NULL` |
| `NOT IN` with nullable subquery | Ignoring three-valued logic | Prefer `NOT EXISTS` or explicitly handle NULL |
| Missing parentheses around `OR` | Assuming natural-language grouping | Explicitly group conditions |
| Timestamp `BETWEEN` to `23:59:59` | Assuming second precision | Use `>= start AND < end` |
| `=` for wildcard matching | Confusing equality with pattern matching | Use `LIKE` |
| `LIKE '%value%'` with B-tree expectation | Assuming all LIKE patterns are indexable | Use suitable search/index strategy |
| Huge `IN` list | Treating large collections as scalar values | Use a relation/table/array mechanism |
| `JOIN` + `DISTINCT` for existence | Ignoring cardinality | Consider `EXISTS` |
| Function on indexed column | Ignoring expression-level indexing | Use matching functional index or normalize data |
| Implicit type conversion | Ignoring schema types | Bind compatible parameter types |
| Dynamic SQL operators from input | Treating SQL syntax as a normal value | Allowlist operators |
| `NOT` without NULL analysis | Forgetting `UNKNOWN` | Explicitly define NULL behavior |

## Production Review Strategy

When reviewing an operator-heavy query, evaluate it in layers.

### Semantic Review

Ask:

- What exact business condition is being represented?
- What happens when values are NULL?
- Are range boundaries correct?
- Are duplicates possible?
- Does the predicate preserve tenant isolation?
- Is case sensitivity intentional?

### SQL Review

Ask:

- Are `AND` and `OR` grouped explicitly?
- Is `IN` appropriate for the collection size?
- Would `EXISTS` better represent existence?
- Is `NOT EXISTS` safer than `NOT IN`?
- Are timestamps using appropriate boundaries?
- Are parameter values bound rather than concatenated?

### Performance Review

Ask:

- Which indexes can support the predicate?
- Are functions applied to indexed columns?
- Is there a leading wildcard?
- Could `OR` produce an expensive plan?
- Is the query processing far more rows than required?
- Has the execution plan been tested with realistic data?

### Security Review

For sensitive or multi-tenant data:

- Can an `OR` branch bypass a tenant predicate?
- Can user input influence SQL syntax?
- Are all values parameterized?
- Are negative predicates correctly handling NULL?
- Are authorization predicates applied consistently?

## Testing Operator Semantics

Operator-heavy queries should be tested against boundary cases rather than only normal data.

For a nullable status field:

| Input | Expected behavior |
|---|---|
| `paid` | Matches `status = 'paid'` |
| `pending` | Does not match `status = 'paid'` |
| `NULL` | Does not match `status = 'paid'` |
| `NULL` | Matches `status IS NULL` |

For a timestamp range:

```text
start ─────────────── end
  ↑                    ↑
included             excluded
```

Test at least:

- Exactly at the start.
- Just after the start.
- Just before the end.
- Exactly at the end.
- NULL timestamp.
- Adjacent windows.

For Boolean predicates, test each branch independently and together:

```text
A = TRUE,  B = TRUE
A = TRUE,  B = FALSE
A = FALSE, B = TRUE
A = FALSE, B = FALSE
NULL combinations where applicable
```

This catches precedence and three-valued-logic bugs that ordinary happy-path tests miss.

## Interview Traps

### Is `NOT IN` always equivalent to `NOT EXISTS`?

No.

NULL semantics can make them behave differently.

### Is `BETWEEN` inclusive?

Yes. Both boundaries are included.

### Is `= NULL` valid?

It is syntactically valid in many SQL dialects but does not perform a NULL equality check. Use `IS NULL`.

### Is `EXISTS` always faster than `JOIN`?

No.

The optimizer can transform queries into similar execution strategies. Choose based on semantics first and validate performance using the execution plan.

### Does an index make every `LIKE` query fast?

No.

A leading wildcard such as:

```sql
LIKE '%abc%'
```

usually cannot use a conventional B-tree index for efficient prefix lookup.

### Does `AND` always execute before `OR`?

In common SQL dialects, `AND` has higher precedence than `OR`, but production code should use parentheses when grouping matters.

## Key Takeaways

- Most dangerous operator mistakes are **silent semantic bugs**, especially around `NULL`, `NOT IN`, Boolean grouping, and range boundaries.
- Use `IS NULL`, `NOT EXISTS`, explicit parentheses, and half-open timestamp ranges when their semantics match the requirement.
- Choose `IN`, `EXISTS`, `JOIN`, and `LIKE` based on the required cardinality and matching semantics rather than assumed performance characteristics.
- Validate operator-heavy queries against **realistic data, indexes, and execution plans**; logically correct SQL can still be operationally expensive.
- Treat SQL predicates as part of the **security boundary**, especially for multi-tenant authorization and dynamically constructed queries.