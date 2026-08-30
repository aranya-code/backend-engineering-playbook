# 12- Common Set Operator Mistakes

## Overview

SQL set operators are simple syntactically but frequently produce incorrect results when their **set semantics, duplicate behavior, column compatibility, NULL handling, ordering, or performance characteristics** are misunderstood.

The most common operators are:

| Operator | Meaning | Duplicate Behavior |
| --- | --- | --- |
| `UNION` | Rows in A or B | Removes duplicates |
| `UNION ALL` | Rows from A and B | Preserves duplicates |
| `INTERSECT` | Rows in both A and B | Removes duplicates |
| `EXCEPT` | Rows in A but not B | Removes duplicates |

Most production mistakes fall into a few categories:

- Choosing an operator based on syntax rather than business semantics.
- Using `UNION` when `UNION ALL` is required.
- Reversing `EXCEPT`.
- Comparing incompatible columns.
- Misunderstanding how duplicates are evaluated.
- Mishandling `NULL`.
- Assuming branch ordering is preserved.
- Applying security predicates to only one branch.
- Ignoring the execution plan.
- Replacing a join or existence check with a set operator unnecessarily.

The key engineering principle is:

> Treat a set operator as a statement about populations, not merely as a way to concatenate SQL queries.

## Mistaking `UNION` for `UNION ALL`

One of the most common mistakes is using `UNION` whenever two query results need to be combined.

```sql
SELECT user_id
FROM mobile_users

UNION

SELECT user_id
FROM web_users;
```

This removes duplicate `user_id` values.

If the requirement is to preserve every row:

```sql
SELECT user_id
FROM mobile_users

UNION ALL

SELECT user_id
FROM web_users;
```

### Why This Matters

Consider:

```text
mobile_users = 101, 102, 103
web_users    = 103, 104
```

`UNION` produces:

```text
101
102
103
104
```

`UNION ALL` produces:

```text
101
102
103
103
104
```

The duplicate `103` may be:

- Undesired duplication of an entity.
- A legitimate occurrence.
- Evidence that the same user uses multiple channels.
- A duplicate event that must be retained.
- A data-quality problem.

The database cannot determine which interpretation is correct. The application or data model must define the semantics.

### Better Decision

Ask:

> Does each row represent an entity or an occurrence?

For entities, deduplication may be required.

For events, logs, transactions, or measurements, duplicates may be meaningful.

## Assuming Duplicates Are Always Bad

Consider:

```sql
SELECT customer_id, order_id
FROM current_orders

UNION ALL

SELECT customer_id, order_id
FROM archived_orders;
```

Suppose the same `customer_id` appears several times.

That is not necessarily duplication. A customer can legitimately have many orders.

The important question is what constitutes row identity.

```text
customer_id
     ↓
one customer

customer_id + order_id
     ↓
one order
```

If the query projects only `customer_id`, multiple orders collapse into duplicate-looking values.

```sql
SELECT customer_id
FROM orders;
```

This does not mean the underlying orders are duplicates.

If the requirement is to find unique customers, make that semantic requirement explicit:

```sql
SELECT DISTINCT customer_id
FROM orders;
```

or, when combining independent sources:

```sql
SELECT customer_id
FROM current_orders

UNION

SELECT customer_id
FROM archived_orders;
```

### Production Rule

Never decide whether duplicates are valid by looking only at the projected values. Determine what one row represents in the business domain.

## Reversing `EXCEPT`

`EXCEPT` is directional.

```sql
SELECT customer_id
FROM source_customers

EXCEPT

SELECT customer_id
FROM destination_customers;
```

means:

> Customers present in the source but absent from the destination.

Reversing the queries changes the question:

```sql
SELECT customer_id
FROM destination_customers

EXCEPT

SELECT customer_id
FROM source_customers;
```

Now it means:

> Customers present in the destination but absent from the source.

### Reconciliation Example

Suppose:

```text
Source       = {1, 2, 3, 4}
Destination  = {3, 4, 5}
```

Then:

```text
Source EXCEPT Destination
= {1, 2}
```

while:

```text
Destination EXCEPT Source
= {5}
```

For migration validation, explicitly name the direction:

```sql
-- Records that still need to reach the destination.
SELECT customer_id
FROM legacy_customers

EXCEPT

SELECT customer_id
FROM customers;
```

This makes the business meaning easier to review.

## Using `EXCEPT` as a Generic Inequality Operator

This is incorrect reasoning:

```sql
A EXCEPT B
```

does not mean:

```sql
A != B
```

`EXCEPT` is a **set difference** operation.

For example:

```sql
SELECT customer_id
FROM customers

EXCEPT

SELECT customer_id
FROM blocked_customers;
```

means:

> Return customer IDs in the first result that do not occur in the second result.

It is not a row-by-row comparison.

For value comparison, use an appropriate predicate:

```sql
WHERE status <> 'blocked'
```

For existence comparison, use:

```sql
WHERE NOT EXISTS (...)
```

## Confusing `INTERSECT` with `JOIN`

`INTERSECT` answers:

> Which rows occur in both result sets?

Example:

```sql
SELECT user_id
FROM premium_users

INTERSECT

SELECT user_id
FROM active_users;
```

A `JOIN` answers a relationship-oriented question:

```sql
SELECT
    u.user_id,
    u.email,
    s.plan_id
FROM users AS u
JOIN subscriptions AS s
    ON s.user_id = u.user_id;
```

Use `INTERSECT` when common membership is the actual requirement.

Use a `JOIN` when you need attributes from related rows.

### Common Bad Pattern

Developers sometimes use:

```sql
SELECT user_id
FROM users

INTERSECT

SELECT user_id
FROM subscriptions;
```

and later discover that they also need:

- User email.
- Subscription status.
- Plan.
- Subscription start date.

At that point the query is expressing the wrong abstraction.

### Better Rule

| Requirement | Prefer |
| --- | --- |
| Find common population | `INTERSECT` |
| Retrieve related attributes | `JOIN` |
| Test whether a related row exists | `EXISTS` |
| Test whether no related row exists | `NOT EXISTS` |

## Confusing `EXCEPT` with `NOT EXISTS`

These can express similar business logic:

```sql
SELECT customer_id
FROM customers

EXCEPT

SELECT customer_id
FROM orders;
```

and:

```sql
SELECT c.customer_id
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
);
```

But their semantics and flexibility differ.

`EXCEPT` naturally expresses:

> Population A minus population B.

`NOT EXISTS` naturally expresses:

> Return rows from this outer relation for which no matching related row exists.

When the application needs customer attributes, `NOT EXISTS` is often more natural:

```sql
SELECT
    c.customer_id,
    c.email,
    c.created_at
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
);
```

Do not choose between them based solely on which query is shorter. Start from the required result shape and business semantics.

## Ignoring Column Compatibility

Set operators require compatible query structures.

This is invalid:

```sql
SELECT
    user_id,
    email
FROM users

UNION

SELECT
    customer_id
FROM customers;
```

The branches return different numbers of columns.

This can also be problematic:

```sql
SELECT
    user_id
FROM users

UNION

SELECT
    email
FROM customers;
```

Even though both queries return one column, their data types may be incompatible or may trigger implicit conversion.

### Better Practice

Make the corresponding columns semantically equivalent:

```sql
SELECT
    user_id::text AS identifier
FROM users

UNION

SELECT
    email AS identifier
FROM customers;
```

Only do this when comparing different identifier representations is actually intended.

### Production Rule

For each column position, verify:

1. Same semantic meaning.
2. Compatible data type.
3. Appropriate precision and scale.
4. Appropriate collation or character semantics where relevant.
5. Explicit casts when implicit conversion could be ambiguous or expensive.

## Assuming Column Names Must Match

The column names do not necessarily need to be identical.

For example:

```sql
SELECT
    user_id AS customer_id
FROM users

UNION ALL

SELECT
    id AS customer_id
FROM customers;
```

The aliases make the intended output contract clear.

The output column names are generally determined by the first query.

Therefore, this:

```sql
SELECT
    user_id AS customer_id
FROM users

UNION ALL

SELECT
    id AS customer_identifier
FROM customers;
```

will generally produce an output column named `customer_id`.

### Best Practice

Use consistent aliases in every branch:

```sql
SELECT
    user_id AS customer_id
FROM users

UNION ALL

SELECT
    id AS customer_id
FROM customers;
```

This improves readability and prevents confusion for application developers consuming the result.

## Forgetting That `UNION` Deduplicates Complete Rows

`UNION` does not deduplicate based on one column unless only that column is selected.

Consider:

```sql
SELECT user_id, source
FROM mobile_users

UNION

SELECT user_id, source
FROM web_users;
```

These rows are distinct:

```text
101 | mobile
101 | web
```

because the complete rows differ.

Therefore, `UNION` does not mean:

> Keep one row per `user_id`.

It means:

> Remove duplicate rows from the complete result projection.

### If One Row Per User Is Required

The query must define that requirement explicitly.

For example:

```sql
SELECT DISTINCT user_id
FROM (
    SELECT user_id
    FROM mobile_users

    UNION ALL

    SELECT user_id
    FROM web_users
) AS users;
```

Or simply:

```sql
SELECT user_id
FROM mobile_users

UNION

SELECT user_id
FROM web_users;
```

The correct form depends on whether additional columns must be retained.

## Misunderstanding `NULL`

`NULL` is not an ordinary value.

Set operations use SQL row-comparison semantics that can make `NULL` behavior surprising if developers reason about it like ordinary equality.

Consider:

```sql
SELECT NULL::integer AS value

UNION

SELECT NULL::integer AS value;
```

The duplicate result is removed, so a single `NULL` row remains.

This differs from ordinary predicate reasoning such as:

```sql
NULL = NULL
```

which does not evaluate to `TRUE` in SQL's three-valued logic.

### Why This Matters

Set operators are comparing result rows as sets, while predicates such as `=` operate under SQL's `TRUE`, `FALSE`, and `UNKNOWN` logic.

Do not transfer intuition from:

```sql
WHERE a = b
```

directly to set operations.

### Production Guidance

When set membership involving nullable business keys matters, explicitly understand:

- Whether the key can be `NULL`.
- Whether `NULL` should represent "unknown."
- Whether two `NULL` values should be treated as the same logical state.
- Whether a nullable column is appropriate as the reconciliation key.

For critical data reconciliation, prefer stable, non-null identifiers.

## Assuming Row Order Is Preserved

This is unsafe:

```sql
SELECT user_id
FROM mobile_users

UNION ALL

SELECT user_id
FROM web_users;
```

and then assuming mobile users will always appear before web users.

SQL does not guarantee result ordering without an `ORDER BY`.

Use:

```sql
SELECT
    user_id,
    source
FROM (
    SELECT user_id, 'mobile' AS source
    FROM mobile_users

    UNION ALL

    SELECT user_id, 'web' AS source
    FROM web_users
) AS users
ORDER BY source, user_id;
```

### API Implication

If a Django or FastAPI endpoint requires deterministic pagination:

```sql
ORDER BY created_at DESC, user_id DESC
LIMIT 100;
```

Do not rely on:

- Table insertion order.
- Index order.
- Branch order.
- Current execution-plan behavior.
- Previous query output order.

These are implementation details, not SQL ordering guarantees.

## Applying `ORDER BY` to Individual Branches Incorrectly

A common pattern is:

```sql
SELECT user_id
FROM mobile_users
ORDER BY user_id

UNION ALL

SELECT user_id
FROM web_users
ORDER BY user_id;
```

This is generally not the correct way to express ordering of the final result.

If the requirement is global ordering:

```sql
SELECT user_id
FROM mobile_users

UNION ALL

SELECT user_id
FROM web_users

ORDER BY user_id;
```

If each branch independently requires ordering before a branch-level operation such as `LIMIT`, isolate the branch:

```sql
(
    SELECT user_id
    FROM mobile_users
    ORDER BY user_id
    LIMIT 100
)

UNION ALL

(
    SELECT user_id
    FROM web_users
    ORDER BY user_id
    LIMIT 100
);
```

The distinction matters because:

```text
branch ordering
```

and:

```text
final result ordering
```

are different requirements.

## Applying `LIMIT` at the Wrong Level

Consider:

```sql
SELECT user_id
FROM mobile_users

UNION ALL

SELECT user_id
FROM web_users

LIMIT 100;
```

This limits the combined result.

If the requirement is:

> Take 100 users from each source.

then the branches need independent limits:

```sql
(
    SELECT user_id
    FROM mobile_users
    ORDER BY user_id
    LIMIT 100
)

UNION ALL

(
    SELECT user_id
    FROM web_users
    ORDER BY user_id
    LIMIT 100
);
```

The two queries have different semantics.

This is especially important for feed generation and multi-source APIs.

## Using `UNION` to Hide Data-Quality Problems

Suppose a migration accidentally writes the same record to both the source and destination.

A developer may use:

```sql
SELECT customer_id
FROM source_customers

UNION

SELECT customer_id
FROM destination_customers;
```

and conclude that the populations contain no duplicates.

That conclusion is invalid.

`UNION` intentionally hides duplicate membership.

For reconciliation, use the operator that answers the actual question.

To identify missing destination records:

```sql
SELECT customer_id
FROM source_customers

EXCEPT

SELECT customer_id
FROM destination_customers;
```

To identify common records:

```sql
SELECT customer_id
FROM source_customers

INTERSECT

SELECT customer_id
FROM destination_customers;
```

If duplicate counts themselves matter, use aggregation rather than a deduplicating set operator.

## Using `UNION ALL` Without Understanding Multiplicity

`UNION ALL` can dramatically increase result size.

Suppose each branch returns 10 million rows:

```sql
SELECT ...
FROM table_a

UNION ALL

SELECT ...
FROM table_b;
```

The combined result can contain up to 20 million rows.

This can increase:

- Network transfer.
- Database memory pressure.
- Application memory usage.
- Serialization time.
- API response time.
- Downstream processing cost.

A Python service that materializes the entire result can make the problem worse:

```python
rows = cursor.fetchall()
```

For large datasets, use pagination, streaming, batching, or server-side processing where appropriate.

## Adding `DISTINCT` Redundantly

This is often unnecessary:

```sql
SELECT DISTINCT user_id
FROM users

UNION

SELECT DISTINCT user_id
FROM archived_users;
```

The final `UNION` already removes duplicate complete rows.

The branch-level `DISTINCT` operations may add unnecessary work.

Prefer:

```sql
SELECT user_id
FROM users

UNION

SELECT user_id
FROM archived_users;
```

However, this is not an absolute rule. A branch-level `DISTINCT` can sometimes reduce intermediate cardinality enough to improve execution cost, depending on the query plan.

The correct approach is:

> Remove redundant operations unless the execution plan demonstrates that they provide a measurable benefit.

## Assuming `UNION ALL` Is Always Faster

`UNION ALL` usually avoids the duplicate-elimination work required by `UNION`.

However, performance depends on the complete execution plan.

Factors include:

- Number of rows.
- Row width.
- Data distribution.
- Available memory.
- Parallel execution.
- Disk spills.
- Existing indexes.
- Predicate selectivity.

Therefore, avoid interview-style claims such as:

> "`UNION ALL` is always faster."

A better statement is:

> "`UNION ALL` avoids duplicate elimination, so it is generally cheaper when duplicate removal is unnecessary."

## Ignoring Intermediate Result Size

A query can be logically correct but operationally dangerous.

For example:

```sql
SELECT *
FROM current_events

UNION ALL

SELECT *
FROM archived_events;
```

If both tables contain hundreds of millions of rows, the result may be enormous.

Avoid using `SELECT *` in production set operations.

Prefer the exact columns required:

```sql
SELECT
    event_id,
    user_id,
    event_type,
    created_at
FROM current_events

UNION ALL

SELECT
    event_id,
    user_id,
    event_type,
    created_at
FROM archived_events;
```

This reduces:

- Row width.
- Network transfer.
- Serialization cost.
- Memory consumption.
- Downstream processing cost.

## Filtering Only After the Set Operation

This can be less efficient or less clear:

```sql
SELECT user_id
FROM (
    SELECT user_id, status
    FROM current_users

    UNION ALL

    SELECT user_id, status
    FROM archived_users
) AS users
WHERE status = 'active';
```

When semantically equivalent, filtering within each branch can reduce intermediate rows:

```sql
SELECT user_id
FROM current_users
WHERE status = 'active'

UNION ALL

SELECT user_id
FROM archived_users
WHERE status = 'active';
```

The optimizer may push predicates down automatically, but explicit branch predicates can make the intended data flow clearer.

Always verify with the execution plan for performance-sensitive queries.

## Forgetting Security Predicates in Every Branch

This is a serious production mistake in multi-tenant systems.

Consider:

```sql
SELECT user_id
FROM users
WHERE tenant_id = $1

UNION ALL

SELECT user_id
FROM imported_users;
```

The first branch is tenant-scoped, but the second is not.

This can expose another tenant's data.

The safer pattern is:

```sql
SELECT user_id
FROM users
WHERE tenant_id = $1

UNION ALL

SELECT user_id
FROM imported_users
WHERE tenant_id = $1;
```

### Security Rule

Treat every branch as an independent query boundary.

For every set-operation branch, verify:

- Tenant filtering.
- Authorization constraints.
- Soft-delete filtering.
- Data classification restrictions.
- Row-level security assumptions.

Do not assume a predicate in one branch protects the combined result.

## Ignoring Soft-Deleted Rows

Applications frequently use soft deletion:

```sql
deleted_at TIMESTAMP NULL
```

A set operation can accidentally include deleted records in one branch:

```sql
SELECT user_id
FROM active_users
WHERE deleted_at IS NULL

UNION ALL

SELECT user_id
FROM imported_users;
```

If both sources follow the same logical lifecycle, the deletion predicate should be applied consistently:

```sql
SELECT user_id
FROM active_users
WHERE deleted_at IS NULL

UNION ALL

SELECT user_id
FROM imported_users
WHERE deleted_at IS NULL;
```

Whether this is correct depends on the source schema, but the important point is to make lifecycle rules explicit for every branch.

## Comparing Unstable Business Fields

Using mutable fields for set comparison can produce incorrect reconciliation.

For example:

```sql
SELECT email
FROM legacy_customers

EXCEPT

SELECT email
FROM customers;
```

This may report a customer as missing because their email address changed.

Prefer stable identifiers:

```sql
SELECT legacy_customer_id
FROM legacy_customers

EXCEPT

SELECT legacy_customer_id
FROM customers;
```

When stable identifiers are unavailable, reconciliation may require normalization or a dedicated mapping table.

### Senior-Level Rule

Set operators are only as reliable as the identity represented by the projected columns.

## Ignoring Type Conversion Costs

Implicit conversions can make set operations more difficult to reason about and may affect execution.

For example:

```sql
SELECT user_id
FROM users

UNION

SELECT user_id::text
FROM imported_users;
```

Explicit casting is often clearer when schemas genuinely differ.

However, converting large datasets can itself be expensive.

Before introducing a cast across millions of rows, evaluate:

- Whether the schemas should be standardized.
- Whether the cast can be performed during ingestion.
- Whether the data type is semantically correct.
- Whether an index can still be used effectively.
- Whether the conversion causes memory or CPU overhead.

For long-term systems, fixing schema inconsistency is usually preferable to repeatedly converting data at query time.

## Using Set Operators When a `JOIN` Is Required

A set operator can become awkward when the application needs attributes from multiple tables.

Instead of:

```sql
SELECT user_id
FROM users

INTERSECT

SELECT user_id
FROM subscriptions;
```

followed by another query to retrieve user data, use the relationship directly:

```sql
SELECT
    u.user_id,
    u.email,
    s.plan_id
FROM users AS u
JOIN subscriptions AS s
    ON s.user_id = u.user_id;
```

This reduces unnecessary query stages and better expresses the data relationship.

## Using `JOIN` When Set Semantics Are Clearer

The opposite mistake also occurs.

Developers sometimes write:

```sql
SELECT DISTINCT
    a.user_id
FROM source_a AS a
JOIN source_b AS b
    ON b.user_id = a.user_id;
```

when the actual requirement is simply:

> Which IDs are present in both datasets?

If the database supports it and the result is naturally set-based:

```sql
SELECT user_id
FROM source_a

INTERSECT

SELECT user_id
FROM source_b;
```

can communicate the intent more directly.

Do not blindly replace joins with set operators, or vice versa. Choose based on the required result and data relationship.

## Ignoring Database-Specific Support

SQL is standardized, but database implementations differ.

Before using advanced forms such as:

```sql
INTERSECT ALL
```

or:

```sql
EXCEPT ALL
```

verify support and semantics in the target database.

This matters when deploying the same application across:

- PostgreSQL.
- MySQL.
- SQL Server.
- Oracle.
- Cloud-managed database variants.

Do not assume that syntax supported by one database engine is portable to another.

## Failing to Test With Boundary Cases

Set-operator tests should include more than the happy path.

At minimum, test:

| Case | Why It Matters |
| --- | --- |
| Empty A | Validates empty input behavior |
| Empty B | Validates operator identity |
| Identical A and B | Tests duplicate/intersection semantics |
| Completely disjoint sets | Tests difference behavior |
| Duplicate rows | Validates `UNION` vs `UNION ALL` |
| `NULL` values | Exposes nullable-key behavior |
| Large datasets | Validates performance |
| Different data types | Validates compatibility |
| Multiple branches | Tests chained operator semantics |

For example:

```text
A = {}
B = {1, 2}

A UNION B       → {1, 2}
A UNION ALL B   → {1, 2}
A INTERSECT B   → {}
A EXCEPT B      → {}
```

Boundary testing is particularly important for reconciliation jobs and migration validation.

## Production Performance Investigation

When a set operation becomes slow, inspect the actual plan rather than immediately rewriting the query.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id
FROM current_users

UNION

SELECT user_id
FROM archived_users;
```

Look for:

- Large sequential scans.
- Expensive sorts.
- Hash operations.
- Memory pressure.
- Temporary file usage.
- Incorrect cardinality estimates.
- Excessive row counts.
- Expensive casts.
- Missing selective predicates.

The objective is to determine **where the cost occurs**, not to optimize the SQL keyword in isolation.

## A Practical Review Checklist

Before approving a production query using set operators, check:

### Semantics

- Does the operator match the business relationship?
- Should duplicates be preserved?
- Is `EXCEPT` direction correct?
- Is the query comparing entities, events, or attributes?

### Schema

- Do all branches return the same number of columns?
- Are corresponding columns semantically compatible?
- Are aliases clear?
- Are explicit casts required?

### Correctness

- Has `NULL` behavior been considered?
- Is the identity key stable?
- Are duplicate rows meaningful?
- Are boundary cases tested?

### Security

- Does every branch enforce tenant isolation?
- Are authorization filters applied consistently?
- Are soft-deleted or restricted rows excluded where required?

### Performance

- Is `UNION` doing unnecessary deduplication?
- Is `UNION ALL` producing excessive intermediate data?
- Are predicates selective?
- Is `SELECT *` avoided?
- Has the execution plan been inspected?
- Could the result exceed practical application memory?

### API and Application Layer

- Is deterministic ordering required?
- Is pagination applied at the correct level?
- Can the application stream or batch large results?
- Is the result shape stable for Django/FastAPI consumers?

## Common Mistake Matrix

| Mistake | Risk | Correct Approach |
| --- | --- | --- |
| `UNION` used automatically | Unnecessary deduplication or lost multiplicity | Choose based on duplicate semantics |
| `UNION ALL` used for entities | Duplicate entities | Use `UNION` when uniqueness is required |
| `EXCEPT` reversed | Incorrect reconciliation result | Define A and B explicitly |
| `INTERSECT` used instead of `JOIN` | Missing related attributes | Use `JOIN` for relationship data |
| `EXCEPT` used instead of `NOT EXISTS` | Awkward or incomplete row filtering | Use `NOT EXISTS` for correlated existence logic |
| Different column counts | Query failure | Align result schemas |
| Incompatible data types | Query failure or expensive conversion | Use compatible types and explicit casts |
| Assuming one row per key | Incorrect uniqueness assumptions | Understand complete-row semantics |
| Assuming ordering | Nondeterministic API results | Add final `ORDER BY` |
| Global `LIMIT` mistaken for per-source limit | Incorrect result distribution | Isolate branches when independent limits are required |
| `UNION` hides duplicate data | Data-quality issue remains undetected | Use reconciliation/counting queries |
| Security predicate on one branch | Possible data leak | Secure every branch |
| `SELECT *` in set operations | Large rows and unstable schemas | Project only required columns |
| Optimizing without `EXPLAIN` | Wrong optimization target | Inspect the actual execution plan |
| Relying on database-specific behavior | Portability failures | Verify target-engine support |

## Key Takeaways

- **Set-operator correctness starts with business semantics: choose `UNION`, `UNION ALL`, `INTERSECT`, or `EXCEPT` based on the population relationship and duplicate meaning.**
- **`EXCEPT` is directional, `UNION` deduplicates complete rows, and set compatibility depends on column count and compatible corresponding types.**
- **Do not confuse set operations with `JOIN`, `EXISTS`, or `NOT EXISTS`; choose the construct that matches whether the requirement is population comparison, relationship retrieval, or existence testing.**
- **Treat every set-operation branch as an independent production query boundary for security, tenant isolation, filtering, lifecycle rules, and performance.**
- **For performance-sensitive or reconciliation workloads, test boundary cases and inspect the actual execution plan rather than relying on assumptions about operator speed.**