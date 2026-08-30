# 06- NULL with Logical Operators

## Overview

SQL uses **three-valued logic** when `NULL` participates in a predicate:

- `TRUE`
- `FALSE`
- `UNKNOWN`

This becomes especially important with logical operators such as:

```sql
AND
OR
NOT
```

Unlike application languages, SQL does not treat a nullable condition as simply `true` or `false`. A predicate involving `NULL` can evaluate to `UNKNOWN`, and `WHERE` clauses retain only rows for which the final predicate is `TRUE`.

This affects filtering, joins, authorization queries, reporting, `CASE` expressions, and repository-layer code in applications such as Django and FastAPI services backed by PostgreSQL.

The most important mental model is:

```text
NULL does not mean FALSE.
NULL usually makes a comparison UNKNOWN.
WHERE keeps TRUE and rejects both FALSE and UNKNOWN.
```

## Three-Valued Logic

A predicate can have three possible results:

| Result | Meaning | `WHERE` |
|---|---|---|
| `TRUE` | Predicate is definitely satisfied | Row retained |
| `FALSE` | Predicate is definitely not satisfied | Row rejected |
| `UNKNOWN` | Predicate cannot be determined | Row rejected |

For example:

```sql
SELECT *
FROM users
WHERE age > 18;
```

If the data contains:

| `age` | `age > 18` |
|---:|---|
| `25` | `TRUE` |
| `18` | `FALSE` |
| `NULL` | `UNKNOWN` |

The row with `age = NULL` is excluded.

## Why Logical Operators Matter

Logical operators combine predicates rather than values directly.

Consider:

```sql
WHERE status = 'active'
  AND last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
```

If:

```text
status = 'active'       → TRUE
last_login_at = NULL    → UNKNOWN
```

then:

```text
TRUE AND UNKNOWN → UNKNOWN
```

The row is therefore excluded.

This is often the source of unexpected results in production queries: adding a condition involving a nullable column can remove rows that previously matched.

## `AND` With NULL

The behavior of `AND` can be represented as:

| A | B | `A AND B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | TRUE | FALSE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | TRUE | UNKNOWN |
| UNKNOWN | FALSE | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

The key rule is:

> `AND` returns `FALSE` when either side is definitely false; otherwise an `UNKNOWN` operand can propagate into the result.

### Practical Example

```sql
SELECT *
FROM orders
WHERE status = 'pending'
  AND shipped_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
```

Suppose:

```text
status = 'pending' → TRUE
shipped_at = NULL  → UNKNOWN
```

Then:

```text
TRUE AND UNKNOWN → UNKNOWN
```

The order is excluded.

If the business rule requires unshipped orders to be included, the query must explicitly express that:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
  AND (
      shipped_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
      OR shipped_at IS NULL
  );
```

## `OR` With NULL

The truth table for `OR` is:

| A | B | `A OR B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | TRUE |
| TRUE | UNKNOWN | TRUE |
| FALSE | TRUE | TRUE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | UNKNOWN |
| UNKNOWN | TRUE | TRUE |
| UNKNOWN | FALSE | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN |

The key rule is:

> `OR` returns `TRUE` when either side is definitely true. Otherwise `UNKNOWN` can propagate.

For example:

```sql
SELECT *
FROM users
WHERE status = 'active'
   OR last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days';
```

For a row where:

```text
status = 'active' → TRUE
last_login_at = NULL → UNKNOWN
```

the result is:

```text
TRUE OR UNKNOWN → TRUE
```

The row is retained.

But if:

```text
status = 'inactive' → FALSE
last_login_at = NULL → UNKNOWN
```

then:

```text
FALSE OR UNKNOWN → UNKNOWN
```

and the row is rejected.

## `NOT` With NULL

`NOT` reverses `TRUE` and `FALSE`, but `UNKNOWN` remains `UNKNOWN`.

| A | `NOT A` |
|---|---|
| TRUE | FALSE |
| FALSE | TRUE |
| UNKNOWN | UNKNOWN |

Therefore:

```text
NOT UNKNOWN → UNKNOWN
```

This is why the following does not identify null values:

```sql
SELECT *
FROM users
WHERE NOT (email = NULL);
```

The inner comparison is:

```text
email = NULL → UNKNOWN
```

and therefore:

```text
NOT UNKNOWN → UNKNOWN
```

The correct expression is:

```sql
SELECT *
FROM users
WHERE email IS NULL;
```

## Operator Precedence

Logical operators also interact with SQL operator precedence.

Consider:

```sql
WHERE status = 'active'
   OR status = 'pending'
  AND deleted_at IS NULL;
```

`AND` is evaluated before `OR`, so this is interpreted as:

```sql
WHERE status = 'active'
   OR (
       status = 'pending'
       AND deleted_at IS NULL
   );
```

It is **not** equivalent to:

```sql
WHERE (
    status = 'active'
    OR status = 'pending'
)
AND deleted_at IS NULL;
```

When `NULL` is involved, ambiguity becomes particularly dangerous.

Prefer explicit parentheses:

```sql
WHERE (
    status = 'active'
    OR status = 'pending'
)
AND deleted_at IS NULL;
```

The additional parentheses make the intended business rule visible to reviewers and future maintainers.

## Combining Multiple NULL Conditions

Consider:

```sql
SELECT *
FROM subscriptions
WHERE cancelled_at IS NULL
  AND expires_at > CURRENT_TIMESTAMP;
```

Here the first predicate is explicitly null-safe:

```text
cancelled_at IS NULL → TRUE/FALSE
```

The second predicate can still produce `UNKNOWN`:

```text
expires_at > CURRENT_TIMESTAMP
```

if `expires_at` is nullable.

Therefore:

```text
cancelled_at IS NULL → TRUE
expires_at = NULL    → UNKNOWN

TRUE AND UNKNOWN     → UNKNOWN
```

The subscription is excluded.

If missing expiration means "never expires", the business rule might instead be:

```sql
SELECT *
FROM subscriptions
WHERE cancelled_at IS NULL
  AND (
      expires_at > CURRENT_TIMESTAMP
      OR expires_at IS NULL
  );
```

This illustrates an important engineering principle:

> SQL cannot determine what `NULL` means for your business domain. The query must encode that meaning explicitly.

## `AND` and `OR` With Nullable Status Flags

Suppose a table contains:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    is_verified BOOLEAN,
    is_suspended BOOLEAN
);
```

A query might be:

```sql
SELECT *
FROM users
WHERE is_verified = TRUE
  AND is_suspended = FALSE;
```

This does **not** mean:

> verified users who are not suspended, including users whose suspension state is unknown.

For:

```text
is_verified = TRUE
is_suspended = NULL
```

the result is:

```text
TRUE AND UNKNOWN → UNKNOWN
```

The row is excluded.

If the domain defines `NULL` as "not suspended":

```sql
SELECT *
FROM users
WHERE is_verified = TRUE
  AND (
      is_suspended = FALSE
      OR is_suspended IS NULL
  );
```

However, if every user must have a definitive suspension state, a better design may be:

```sql
is_suspended BOOLEAN NOT NULL
```

Schema constraints are often preferable to compensating for ambiguous data in every query.

## `NULL` and `WHERE`

A `WHERE` clause does not keep rows where the predicate is `UNKNOWN`.

Consider:

```sql
SELECT *
FROM products
WHERE price >= 100
   OR discount_percent > 20;
```

For:

```text
price = NULL
discount_percent = NULL
```

both predicates evaluate to `UNKNOWN`:

```text
UNKNOWN OR UNKNOWN → UNKNOWN
```

The row is excluded.

For:

```text
price = 80
discount_percent = NULL
```

the result is:

```text
FALSE OR UNKNOWN → UNKNOWN
```

The row is still excluded.

For:

```text
price = 150
discount_percent = NULL
```

the result is:

```text
TRUE OR UNKNOWN → TRUE
```

The row is retained.

## `HAVING` and NULL

Three-valued logic also applies to `HAVING`.

For example:

```sql
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING MAX(cancelled_at) < CURRENT_TIMESTAMP;
```

If all `cancelled_at` values for a customer are `NULL`, then:

```text
MAX(cancelled_at) → NULL
NULL < CURRENT_TIMESTAMP → UNKNOWN
```

and the group is excluded.

If the business rule says customers with no cancellation timestamp should also qualify, the condition must account for that explicitly.

## `JOIN` Conditions and NULL

Logical and comparison semantics also affect joins.

Consider:

```sql
SELECT o.id, o.customer_id
FROM orders AS o
JOIN customers AS c
  ON o.customer_id = c.id;
```

If:

```text
o.customer_id = NULL
```

then:

```text
o.customer_id = c.id → UNKNOWN
```

so the row does not satisfy the join condition.

With an `INNER JOIN`, the order is excluded.

With a `LEFT JOIN`:

```sql
SELECT o.id, c.id
FROM orders AS o
LEFT JOIN customers AS c
  ON o.customer_id = c.id;
```

the order remains in the result, but the customer columns are `NULL`.

This distinction is critical when moving predicates between `ON` and `WHERE`.

### `ON` vs `WHERE`

Consider:

```sql
SELECT o.id, c.id
FROM orders AS o
LEFT JOIN customers AS c
  ON o.customer_id = c.id
WHERE c.status = 'active';
```

The `WHERE` condition removes rows where the joined customer is absent because:

```text
c.status = 'active'
```

evaluates to `UNKNOWN` when `c.status` is `NULL`.

This can make the query behave similarly to an inner join.

If the intended rule is to preserve orders without customers while restricting matching customers, the predicate may belong in the join condition:

```sql
SELECT o.id, c.id
FROM orders AS o
LEFT JOIN customers AS c
  ON o.customer_id = c.id
 AND c.status = 'active';
```

This is a common production and interview trap.

## De Morgan's Laws With UNKNOWN

In classical Boolean logic:

```text
NOT (A AND B) = (NOT A) OR (NOT B)
NOT (A OR B)  = (NOT A) AND (NOT B)
```

These transformations remain valid under standard SQL three-valued logic, but the presence of `UNKNOWN` means you must reason about all three states.

For example:

```sql
NOT (
    status = 'active'
    AND deleted_at IS NULL
)
```

is logically equivalent to:

```sql
status <> 'active'
OR deleted_at IS NOT NULL
```

However, this does **not** mean the result includes rows where:

```text
status = NULL
```

because:

```text
status <> 'active' → UNKNOWN
```

If the business meaning requires null status values to be treated as non-active, that must be stated explicitly.

## `NOT` Is Not the Same as `IS NOT NULL`

These expressions have fundamentally different meanings:

```sql
NOT (column = 'active')
```

and:

```sql
column IS NOT NULL
```

The first asks:

> Is it definitely not equal to `'active'`?

The second asks:

> Does a value exist?

For:

```text
column = NULL
```

the first expression becomes:

```text
NOT UNKNOWN → UNKNOWN
```

while:

```sql
column IS NOT NULL
```

returns:

```text
FALSE
```

Never substitute one for the other.

## Practical Example: Soft Deletes

A common backend schema is:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL,
    deleted_at TIMESTAMPTZ
);
```

Active users are defined by:

```sql
deleted_at IS NULL
```

A typical query:

```sql
SELECT id, email
FROM users
WHERE deleted_at IS NULL
  AND email LIKE '%@example.com';
```

Both predicates are well-defined:

```text
deleted_at IS NULL → TRUE/FALSE
email LIKE ...     → TRUE/FALSE/UNKNOWN
```

Because `email` is `NOT NULL`, the second predicate cannot produce `UNKNOWN` because of a missing email.

This demonstrates why good schema design simplifies query reasoning.

## Practical Example: Optional Filters

Suppose an API supports an optional status filter.

A tempting query is:

```sql
SELECT *
FROM orders
WHERE status = :status;
```

If the application passes `NULL` to mean "do not filter by status", this does not work:

```text
status = NULL → UNKNOWN
```

A common pattern is:

```sql
SELECT *
FROM orders
WHERE (:status IS NULL OR status = :status);
```

When `:status` is `NULL`:

```text
:status IS NULL → TRUE
TRUE OR UNKNOWN → TRUE
```

When `:status` has a value:

```text
:status IS NULL → FALSE
status = :status → TRUE/FALSE
```

This expresses optional filtering correctly.

However, for high-volume production queries, dynamically constructing parameterized predicates or using separate query shapes may produce better plans than a generic optional-filter predicate. Always validate with `EXPLAIN (ANALYZE, BUFFERS)` for the actual workload.

## Practical Example: Optional Date Filter

Suppose an API optionally accepts `created_after`.

A parameterized query can be expressed as:

```sql
SELECT id, created_at
FROM orders
WHERE (:created_after IS NULL OR created_at >= :created_after);
```

The semantics are:

| `created_after` | `created_at` | Result |
|---|---|---|
| `NULL` | any value | TRUE |
| timestamp | newer | TRUE |
| timestamp | older | FALSE |
| timestamp | `NULL` | UNKNOWN |

If `created_at` is defined as:

```sql
created_at TIMESTAMPTZ NOT NULL
```

the last case cannot occur.

Again, schema constraints reduce the number of states query logic must handle.

## Performance Considerations

Three-valued logic does not inherently make SQL queries slow. Performance problems usually arise from the query shape, indexes, selectivity, statistics, and optimizer decisions.

For example:

```sql
WHERE (:status IS NULL OR status = :status)
```

can be convenient but may produce less predictable plans on some workloads than separate query shapes.

For a performance-sensitive endpoint:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM orders
WHERE status = 'pending';
```

Compare the actual execution plan with the optional-filter version.

Look for:

- sequential scans;
- index scans;
- estimated vs actual row counts;
- rows removed by filter;
- buffer reads;
- execution time.

Do not rewrite correct NULL logic solely to force index usage. First establish the required semantics, then optimize the implementation.

## Application and ORM Considerations

### Django

Django exposes explicit null checks:

```python
Order.objects.filter(deleted_at__isnull=True)
```

and:

```python
Order.objects.filter(deleted_at__isnull=False)
```

For compound logic:

```python
from django.db.models import Q

Order.objects.filter(
    Q(status="pending"),
    Q(shipped_at__gt=cutoff) | Q(shipped_at__isnull=True),
)
```

This maps the business rule directly into SQL predicates.

Be careful when combining `Q` objects because Python's `&` and `|` composition should reflect the intended SQL grouping:

```python
Q(status="active") & (
    Q(deleted_at__isnull=True) |
    Q(deleted_at__gt=cutoff)
)
```

Explicit grouping is preferable to relying on a reader to infer precedence.

### SQLAlchemy

SQLAlchemy provides explicit null predicates:

```python
from sqlalchemy import select

stmt = select(Order).where(Order.deleted_at.is_(None))
```

For compound conditions:

```python
from sqlalchemy import and_, or_

stmt = select(Order).where(
    and_(
        Order.status == "pending",
        or_(
            Order.shipped_at > cutoff,
            Order.shipped_at.is_(None),
        ),
    )
)
```

Use ORM expressions that map clearly to SQL rather than attempting to reproduce SQL's null behavior in application code.

## Common Mistakes

| Mistake | Why it fails | Better approach |
|---|---|---|
| Assuming `UNKNOWN` means `FALSE` | They are logically different states | Reason about `TRUE`, `FALSE`, and `UNKNOWN` |
| Assuming `NOT UNKNOWN` is `TRUE` | `NOT UNKNOWN` is `UNKNOWN` | Use explicit `IS NULL` / `IS NOT NULL` |
| Assuming `FALSE OR UNKNOWN` is `FALSE` | Result is `UNKNOWN` | Evaluate the full three-valued expression |
| Forgetting parentheses | `AND` has higher precedence than `OR` | Group business logic explicitly |
| Assuming `column <> value` includes NULL | Comparison with NULL is `UNKNOWN` | Add `OR column IS NULL` when required |
| Moving a `LEFT JOIN` predicate into `WHERE` | Can eliminate unmatched rows | Decide whether the predicate belongs in `ON` or `WHERE` |
| Using nullable booleans without defining semantics | `TRUE`, `FALSE`, and `NULL` become three states | Use `NOT NULL` when a binary state is required |
| Treating `NULL` as a default value | Changes business semantics | Use explicit `COALESCE` or schema defaults where appropriate |
| Testing only populated data | NULL-specific bugs remain hidden | Include NULL cases in integration tests |
| Optimizing before defining NULL semantics | Can produce fast but incorrect results | Establish correctness first, then inspect execution plans |

## Testing Nullable Logic

Queries involving logical operators should be tested against representative combinations.

For example:

| `status` | `deleted_at` | Expected |
|---|---|---|
| `active` | `NULL` | depends on business rule |
| `active` | timestamp | depends on business rule |
| `inactive` | `NULL` | depends on business rule |
| `inactive` | timestamp | depends on business rule |
| `NULL` | `NULL` | depends on business rule |
| `NULL` | timestamp | depends on business rule |

For a production repository, tests should cover:

- both operands populated;
- either operand `NULL`;
- both operands `NULL`;
- `TRUE` combined with `UNKNOWN`;
- `FALSE` combined with `UNKNOWN`;
- `UNKNOWN` combined with `UNKNOWN`;
- parenthesized `AND`/`OR` combinations;
- `LEFT JOIN` behavior where joined columns are `NULL`.

The goal is not to test SQL syntax. The goal is to verify the application's intended treatment of missing data.

## Interview Traps

### What is the result of `TRUE AND NULL`?

Conceptually:

```text
TRUE AND UNKNOWN → UNKNOWN
```

### What is the result of `FALSE AND NULL`?

```text
FALSE AND UNKNOWN → FALSE
```

### What is the result of `TRUE OR NULL`?

```text
TRUE OR UNKNOWN → TRUE
```

### What is the result of `FALSE OR NULL`?

```text
FALSE OR UNKNOWN → UNKNOWN
```

### What is `NOT NULL`?

In SQL, `NULL` is not a Boolean value, so:

```sql
NOT NULL
```

is not a null check. It evaluates conceptually as:

```text
NOT UNKNOWN → UNKNOWN
```

Use:

```sql
IS NOT NULL
```

### Why does a nullable column disappear from a `WHERE` clause?

Because a comparison involving the `NULL` value generally evaluates to `UNKNOWN`, and `WHERE` keeps only `TRUE`.

### Why can a `LEFT JOIN` behave like an `INNER JOIN`?

A predicate on the nullable side placed in `WHERE` can reject the generated `NULL` values:

```sql
LEFT JOIN customers AS c
    ON c.id = o.customer_id
WHERE c.status = 'active'
```

For an unmatched customer:

```text
c.status = 'active' → UNKNOWN
```

so the row is removed.

Placing the condition in the `ON` clause can preserve the unmatched left-side row when that is the intended semantics.

## Key Takeaways

- **SQL has three-valued logic: `TRUE`, `FALSE`, and `UNKNOWN`; `NULL` commonly causes predicates to become `UNKNOWN`.**
- **`AND`, `OR`, and `NOT` propagate `UNKNOWN` according to three-valued truth tables, so logical expressions must be evaluated with all three states in mind.**
- **Use explicit parentheses around mixed `AND`/`OR` conditions, especially when nullable predicates are involved.**
- **A predicate on the nullable side of a `LEFT JOIN` in `WHERE` can eliminate unmatched rows and effectively turn the result into an inner-join-like query.**
- **Define the business meaning of `NULL` explicitly and prefer `NOT NULL` constraints when the domain does not require a third state.**