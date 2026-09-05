# 09- Functions on Indexed Columns

## Overview

Applying a function, expression, or transformation directly to an indexed column can prevent the database from using a normal index efficiently.

A common example is:

```sql
SELECT *
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

with an ordinary index:

```sql
CREATE INDEX users_email_idx
ON users (email);
```

The index is built on:

```text
email
```

but the query asks for:

```text
LOWER(email)
```

These are different expressions.

Depending on the database and query, the optimizer may be unable to use the ordinary index as an efficient access path and may instead scan many or all rows.

This anti-pattern appears frequently with:

- `LOWER()`
- `UPPER()`
- `CAST()`
- `DATE()`
- `DATE_TRUNC()`
- `COALESCE()`
- `SUBSTRING()`
- String concatenation
- Arithmetic expressions
- JSON extraction
- Timezone conversion

The important distinction is:

> **A function on an indexed column is not automatically bad. The problem is using an expression that the existing index does not support efficiently.**

Sometimes the correct solution is to rewrite the predicate. Sometimes an expression index is exactly the right design.

---

## The Core Problem

Suppose:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    email text NOT NULL
);

CREATE INDEX users_email_idx
ON users (email);
```

This query can naturally use the index:

```sql
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

The indexed expression is:

```text
email
```

Now consider:

```sql
SELECT *
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

The predicate operates on:

```text
LOWER(email)
```

rather than:

```text
email
```

The ordinary index does not contain entries for the transformed expression.

Conceptually:

```text
Index:
email
  ↓
alice@example.com
Bob@example.com
...

Query:
LOWER(email)
  ↓
alice@example.com
```

The database may need to evaluate the function for many rows before determining whether they match.

---

## Why This Happens

A normal B-tree index stores keys derived from its indexed expression.

For:

```sql
CREATE INDEX users_email_idx
ON users (email);
```

the index is ordered by the value of:

```sql
email
```

It is not automatically ordered by:

```sql
LOWER(email)
```

or:

```sql
TRIM(email)
```

or:

```sql
email::text
```

The optimizer therefore needs an index whose expression matches the query semantics closely enough to provide a useful access path.

---

## Example: LOWER()

### Ordinary index

```sql
CREATE INDEX users_email_idx
ON users (email);
```

### Potentially inefficient predicate

```sql
SELECT id
FROM users
WHERE LOWER(email) = LOWER($1);
```

The query transforms the column.

If case-insensitive equality is a core workload, consider an expression index:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

Then:

```sql
SELECT id
FROM users
WHERE LOWER(email) = LOWER($1);
```

can use an index designed for that expression.

The important point is that the index is now built around the actual lookup expression.

---

## Expression Indexes

PostgreSQL supports indexes on expressions.

For example:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

The index stores the result of:

```sql
LOWER(email)
```

for each indexed row.

This changes the design from:

```text
index(email)
```

to:

```text
index(LOWER(email))
```

The query can then use the transformed value as an indexed search key.

### When to Use

Expression indexes are useful when:

- The transformed lookup is common.
- The expression is deterministic/immutable as required by the database.
- The query workload justifies the additional index.
- Rewriting the query is not practical.
- Case-insensitive or normalized lookup is a core requirement.

### Limitations

They introduce:

- Additional storage.
- Additional write cost.
- Additional index maintenance.
- More complex schema.
- Another index that must be monitored and maintained.

Do not create expression indexes for every function appearing in a query.

---

## Query Rewrite vs Expression Index

Consider:

```sql
WHERE LOWER(email) = LOWER($1)
```

There are several possible solutions.

| Approach | When appropriate |
|---|---|
| Normalize application input | When stored values already follow a canonical format |
| Use native case-insensitive type/feature | When supported and semantically appropriate |
| Expression index | When transformed lookup is a core workload |
| Regular index | When exact case-sensitive equality is sufficient |
| Full scan | Only when dataset/workload makes it acceptable |

The senior decision is not:

```text
"Never use functions on indexed columns."
```

It is:

```text
"Make the access path match the actual query semantics."
```

---

## Example: DATE() on a Timestamp

Suppose:

```sql
CREATE INDEX orders_created_at_idx
ON orders (created_at);
```

A common anti-pattern is:

```sql
SELECT *
FROM orders
WHERE created_at::date = DATE '2026-09-05';
```

The query transforms:

```text
created_at
```

into:

```text
created_at::date
```

A better approach for a normal timestamp index is a range:

```sql
SELECT *
FROM orders
WHERE created_at >= TIMESTAMP '2026-09-05 00:00:00'
  AND created_at <  TIMESTAMP '2026-09-06 00:00:00';
```

Now the database can search the existing ordering of:

```text
created_at
```

directly.

---

## Why Range Predicates Are Often Better

Suppose:

```text
created_at
```

is indexed.

This:

```sql
WHERE created_at::date = DATE '2026-09-05'
```

asks the database to derive a date from each timestamp.

This:

```sql
WHERE created_at >= TIMESTAMP '2026-09-05 00:00:00'
  AND created_at <  TIMESTAMP '2026-09-06 00:00:00'
```

asks for a range in the indexed timestamp domain.

Conceptually:

```text
Index ordered by created_at

2026-09-04 ──────┬──────────────────
2026-09-05       │ ← matching range
2026-09-06 ──────┴──────────────────
```

This is particularly important for large tables.

---

## Time Zones Require Care

For `timestamptz`, do not construct date ranges without considering the intended timezone.

For example:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

is often preferable when the application calculates explicit timezone-aware boundaries.

The business requirement might be:

```text
all orders created on September 5 in Asia/Kolkata
```

That is not necessarily the same as:

```text
all timestamps whose UTC date is September 5
```

Avoid fixing an indexing problem by introducing a timezone correctness problem.

---

## Example: CAST()

Suppose:

```sql
CREATE INDEX orders_customer_id_idx
ON orders (customer_id);
```

Avoid unnecessarily transforming the indexed column:

```sql
WHERE customer_id::text = $1;
```

If the incoming value is text but represents a bigint:

```sql
WHERE customer_id = $1::bigint;
```

may preserve the indexed column expression.

The preferred solution is even earlier in the stack:

```text
API input
    ↓
validation
    ↓
Python int
    ↓
typed database parameter
    ↓
customer_id = parameter
```

Database casts should not compensate for a permanently weak application type contract.

---

## Example: COALESCE()

Consider:

```sql
CREATE INDEX users_status_idx
ON users (status);
```

A query such as:

```sql
SELECT *
FROM users
WHERE COALESCE(status, 'active') = 'active';
```

does not have the same expression as:

```sql
status
```

The query is effectively defining:

```text
NULL → active
```

before comparison.

Do not blindly replace it with:

```sql
WHERE status = 'active';
```

because that changes semantics.

If the intended requirement is:

```text
status is active OR status is NULL
```

write it explicitly:

```sql
WHERE status = 'active'
   OR status IS NULL;
```

Then evaluate the plan and data distribution.

---

## Expression Index for COALESCE

If the normalized expression is intentional and frequently queried:

```sql
CREATE INDEX users_effective_status_idx
ON users (COALESCE(status, 'active'));
```

The query:

```sql
WHERE COALESCE(status, 'active') = 'active'
```

can then use an index designed around that expression.

But ask whether this is the right data model.

If NULL should actually mean `"active"`, consider whether storing the canonical state and enforcing it with:

```sql
NOT NULL
DEFAULT 'active'
```

would be a cleaner design.

---

## Example: UPPER()

This pattern:

```sql
WHERE UPPER(country_code) = 'IN'
```

may be unnecessary if the application stores canonical uppercase values.

Instead:

```text
Write:
IN

Read:
IN
```

rather than:

```text
Write:
in
In
IN
iN

Read:
UPPER(country_code)
```

Data normalization can sometimes eliminate the need for runtime transformations.

---

## Data Normalization vs Query-Time Transformation

A useful design question is:

> Should normalization happen when data is written or every time it is queried?

### Write-time normalization

```text
Client input
    ↓
Application normalization
    ↓
Canonical database value
    ↓
Normal index
```

### Query-time normalization

```text
Client input
    ↓
Query transformation
    ↓
Function on indexed column
    ↓
Expression index or expensive scan
```

For high-volume equality lookups, canonical storage can be simpler and cheaper.

However, write-time normalization is not appropriate when preserving the original representation is itself a business requirement.

---

## Example: TRIM()

Consider:

```sql
WHERE TRIM(email) = $1;
```

If whitespace should never be stored in the database, fix the data at ingestion.

For example:

```text
" alice@example.com "
        ↓
"alice@example.com"
```

Then use:

```sql
WHERE email = $1;
```

If legacy data cannot immediately be normalized and trimmed lookup is a real workload, an expression index can be considered:

```sql
CREATE INDEX users_trimmed_email_idx
ON users (TRIM(email));
```

But this should be a deliberate compatibility strategy, not a default workaround.

---

## Example: SUBSTRING()

Consider:

```sql
WHERE SUBSTRING(phone_number FROM 1 FOR 3) = '+91';
```

A normal index on:

```sql
phone_number
```

does not automatically provide an index on:

```sql
SUBSTRING(phone_number FROM 1 FOR 3)
```

If the actual requirement is prefix search, a different query/index strategy may be more appropriate.

For example:

```sql
WHERE phone_number LIKE '+91%';
```

Whether this can use an index efficiently depends on PostgreSQL operator class, collation, pattern, and index definition.

Do not blindly replace one expression with another without checking the actual plan.

---

## Example: JSON Extraction

Suppose:

```sql
CREATE TABLE events (
    id bigint PRIMARY KEY,
    payload jsonb NOT NULL
);
```

A query might use:

```sql
WHERE payload->>'customer_id' = '42';
```

A normal index on:

```sql
payload
```

does not mean every extracted JSON field automatically has an efficient scalar lookup.

If this query is common, consider an expression index:

```sql
CREATE INDEX events_customer_id_idx
ON events ((payload->>'customer_id'));
```

The query and index expression should align.

For high-value relational fields, however, repeatedly extracting them from JSON may indicate that the field belongs in a dedicated typed column.

---

## JSONB GIN vs Expression Index

PostgreSQL offers multiple indexing strategies for JSONB.

For example:

```sql
CREATE INDEX events_payload_gin_idx
ON events
USING GIN (payload);
```

is useful for supported JSONB containment/query patterns.

An expression index such as:

```sql
CREATE INDEX events_customer_id_idx
ON events ((payload->>'customer_id'));
```

targets a specific extracted value.

These indexes solve different workloads.

| Requirement | Possible strategy |
|---|---|
| General JSONB containment | GIN |
| Frequently queried scalar JSON field | Expression index |
| Core relational attribute | Dedicated typed column |
| Rare JSON filtering | Query without specialized index |

Index design should follow query patterns rather than the fact that the column happens to contain JSON.

---

## Functions in JOIN Conditions

Functions on indexed columns can also affect joins.

For example:

```sql
SELECT *
FROM users AS u
JOIN orders AS o
    ON LOWER(u.email) = LOWER(o.customer_email);
```

This is problematic for several reasons:

- Both sides are transformed.
- The relationship is based on derived values.
- Indexes on raw columns may not directly support the expression.
- The join can become expensive at scale.
- Email should generally have a well-defined canonical representation.

If case-insensitive email equality is a core requirement, design the schema and indexes around that requirement rather than repeatedly normalizing both sides during joins.

---

## Functions in ORDER BY

Functions can also affect ordering:

```sql
SELECT *
FROM users
ORDER BY LOWER(last_name);
```

An ordinary index on:

```sql
last_name
```

does not automatically mean the database has an index ordered by:

```sql
LOWER(last_name)
```

If this ordering is common and latency-sensitive, an expression index may help:

```sql
CREATE INDEX users_lower_last_name_idx
ON users (LOWER(last_name));
```

However, the complete `ORDER BY` matters.

For deterministic API ordering, a unique tie-breaker may also be required:

```sql
ORDER BY
    LOWER(last_name),
    id;
```

The corresponding index design should reflect the complete access pattern when justified.

---

## Functions in GROUP BY

Consider:

```sql
SELECT
    DATE(created_at) AS order_date,
    COUNT(*)
FROM orders
GROUP BY DATE(created_at);
```

The function changes the grouping key.

An ordinary index on:

```sql
created_at
```

does not automatically become an index on:

```sql
DATE(created_at)
```

For large reporting workloads, consider whether:

- A date range is more appropriate.
- A generated/stored column is useful.
- An expression index is justified.
- A materialized reporting structure is more appropriate.

Do not create indexes solely because a function appears in a query.

---

## Functions and Partial Indexes

Sometimes the better solution is a partial index.

Suppose most application queries access active users:

```sql
SELECT *
FROM users
WHERE status = 'active';
```

Instead of transforming the column, a partial index may be more appropriate:

```sql
CREATE INDEX users_active_idx
ON users (id)
WHERE status = 'active';
```

This is different from an expression index.

### Expression index

```sql
CREATE INDEX ...
ON users (LOWER(email));
```

### Partial index

```sql
CREATE INDEX ...
ON users (id)
WHERE status = 'active';
```

One changes the indexed expression; the other restricts which rows are indexed.

They can also be combined when the workload requires it.

---

## Generated Columns

A generated column can sometimes provide a cleaner representation of a frequently used derived value.

Conceptually:

```text
raw value
   ↓
generated normalized value
   ↓
ordinary index
```

For example, a schema may maintain a normalized search representation separately from the original value.

This can make application queries simpler:

```sql
WHERE normalized_email = $1
```

instead of:

```sql
WHERE LOWER(email) = LOWER($1)
```

Whether generated columns are appropriate depends on PostgreSQL version, expression requirements, write cost, and schema design.

Do not introduce them solely to avoid learning how indexes work.

---

## Expression Index vs Generated Column

| Approach | Advantages | Limitations |
|---|---|---|
| Function in query | No schema change | May be expensive |
| Expression index | Directly supports expression | Extra index maintenance |
| Generated column | Explicit derived value | Additional schema complexity/storage |
| Application normalization | Simple reads | Requires consistent write path |
| Data model redesign | Strongest long-term semantics | Migration effort |

Choose the smallest design that correctly supports the workload.

---

## Functions and Selectivity

Even when an expression index exists, performance depends on selectivity.

Suppose:

```sql
WHERE LOWER(country_code) = 'in'
```

matches:

```text
40% of the table
```

An index may not be the best plan.

The optimizer considers:

- Estimated selectivity.
- Table size.
- Random I/O cost.
- Cache state.
- Statistics.
- Correlation.
- Query cost.
- Available access paths.

Therefore:

```text
Expression index exists
        ≠
Index will always be used
```

---

## Statistics Matter

The optimizer needs accurate statistics to estimate query costs.

After significant data changes, PostgreSQL's statistics may need to be refreshed automatically through autovacuum/analyze or explicitly when appropriate.

For diagnostics:

```sql
ANALYZE users;
```

Then inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

If the plan looks wrong, investigate estimates before creating another index.

---

## EXPLAIN Is the Source of Truth

Never determine index usability by looking only at SQL syntax.

Run:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

Look for:

```text
Index Scan
Bitmap Index Scan
Index Only Scan
Seq Scan
```

Also inspect:

```text
actual rows
estimated rows
execution time
buffer reads
```

A sequential scan is not automatically bad.

For a small table or a low-selectivity predicate, it may be the optimal plan.

---

## Example Plan Reasoning

Suppose:

```text
users: 50 million rows
```

and:

```sql
WHERE LOWER(email) = 'alice@example.com'
```

returns:

```text
1 row
```

Without an appropriate expression index, the database may have to evaluate the function across a large portion of the table.

With:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

the optimizer may be able to perform an index lookup.

The performance difference can be substantial.

The actual result must still be verified with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

---

## Write Performance Cost

An expression index is maintained whenever the indexed expression's underlying row values change.

For:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

an email insert or update requires index maintenance.

This adds:

- CPU.
- I/O.
- WAL.
- Storage.
- Vacuum/index maintenance work.

On write-heavy systems, every additional index deserves justification.

---

## Read-Heavy vs Write-Heavy Systems

### Read-heavy workload

Expression indexes can be highly valuable when:

- The lookup is frequent.
- The result set is small.
- Latency matters.
- The underlying table is large.

### Write-heavy workload

Be more selective because every additional index increases write amplification.

For high-throughput event ingestion:

```text
Kafka
  ↓
Consumers
  ↓
PostgreSQL
  ↓
many indexes
```

can become expensive.

Index only the access paths required by production workloads.

---

## Connection Pool and Database Load

A bad query can become much more expensive under concurrency.

For example:

```text
200 API requests
        ↓
LOWER(email) without suitable index
        ↓
many row evaluations
        ↓
high CPU
        ↓
connection pool saturation
        ↓
API latency increases
```

Increasing the connection pool may make the problem worse because more expensive queries execute concurrently.

Fix the query/access path before increasing database concurrency.

---

## Microservices Considerations

In a microservice architecture, a type or normalization mismatch can originate in one service and create database performance problems elsewhere.

For example:

```text
Service A
  stores email with inconsistent casing
        ↓
Service B
  performs LOWER(email)
        ↓
PostgreSQL
  expression scan
```

A better architecture defines a shared contract:

```text
Service boundary
    ↓
canonical representation
    ↓
database column
    ↓
native index
```

When multiple services depend on the same lookup semantics, document and enforce the canonical representation.

---

## Redis Is Not a Substitute for a Bad Index

A common response to a slow database lookup is:

```text
Put the result in Redis.
```

Caching can reduce database traffic, but it does not correct an inefficient primary query.

Redis introduces:

- Cache invalidation.
- Staleness.
- Memory cost.
- Operational complexity.
- Failure modes.

If the database lookup is fundamental to correctness or authorization, first make the database access path correct.

Use Redis when caching is justified by the workload.

---

## Security Considerations

Functions on indexed columns are primarily a performance concern, but they can indirectly create security and availability problems.

An expensive query used in an authenticated API can become a resource-exhaustion vector.

For example:

```text
unauthenticated/high-volume endpoint
        ↓
function-heavy query
        ↓
large scans
        ↓
database CPU exhaustion
```

Protect critical endpoints with:

- Authentication where appropriate.
- Rate limiting.
- Query timeouts.
- Pagination.
- Input validation.
- Appropriate indexes.
- Resource controls.

Do not assume an authenticated endpoint is safe from expensive-query abuse.

---

## High Availability and Replication

Inefficient scans increase database resource consumption on the primary and can affect replicas through increased workload and WAL generation from related write activity.

Monitor:

- CPU.
- I/O.
- Query latency.
- Connection utilization.
- Replica lag.
- Checkpoint behavior.
- Autovacuum activity.

For critical expression indexes, deploy them carefully.

In PostgreSQL, consider:

```sql
CREATE INDEX CONCURRENTLY users_lower_email_idx
ON users (LOWER(email));
```

when reducing index-build blocking is important.

`CREATE INDEX CONCURRENTLY` has operational trade-offs and cannot run inside a transaction block.

---

## Deployment Considerations

Before adding an expression index:

1. Confirm the query is production-important.
2. Measure current latency.
3. Check query frequency.
4. Inspect the current execution plan.
5. Estimate index size.
6. Assess write amplification.
7. Consider replication impact.
8. Test on production-scale data.
9. Deploy using an appropriate migration strategy.
10. Verify the resulting plan.

After deployment:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

and monitor real workload behavior.

Do not consider an index deployment complete merely because the migration succeeded.

---

## CI/CD and Migration Safety

A migration adding an expression index should be reviewed as a production infrastructure change.

For large PostgreSQL tables:

```sql
CREATE INDEX CONCURRENTLY users_lower_email_idx
ON users (LOWER(email));
```

may be preferable when supported by the deployment strategy.

Because concurrent index creation has transaction restrictions, ensure the migration framework does not incorrectly wrap the operation in a transaction.

Test the migration against realistic data volumes.

---

## Failed Concurrent Indexes

If a concurrent index build fails, PostgreSQL can leave an invalid index behind.

Inspect:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisvalid,
    indisready
FROM pg_index
WHERE NOT indisvalid
   OR NOT indisready;
```

Clean up failed artifacts according to the migration procedure before attempting the deployment again.

Do not blindly rerun a failed index migration without checking database state.

---

## Monitoring Index Effectiveness

After adding an expression index, verify:

- Query latency decreased.
- Index scans occur where expected.
- Database CPU decreased.
- Buffer reads changed appropriately.
- Write overhead remains acceptable.
- The index is actually used.

Index usage statistics can provide evidence, but low usage alone does not automatically mean an index should be dropped.

Some indexes serve rare but critical queries.

---

## Common Anti-Patterns

| Anti-pattern | Problem | Better approach |
|---|---|---|
| `LOWER(email)` with only index on `email` | May prevent efficient use of normal index | Normalize, native case-insensitive design, or expression index |
| `created_at::date = ...` | May prevent timestamp index range access | Use a timestamp range |
| `customer_id::text = ...` | Changes indexed expression | Bind/cast parameter appropriately |
| `TRIM(column) = ...` | Runtime transformation | Normalize data or expression index |
| Function in JOIN predicate | Expensive join expression | Compatible canonical columns/indexes |
| Function in ORDER BY | May require sorting | Expression index when workload justifies it |
| Index every function used | Excessive write/storage cost | Index only important access paths |
| Add Redis immediately | Hides query problem | Fix database access path first |
| Assume index guarantees usage | Optimizer may choose another plan | Validate with `EXPLAIN` |
| Ignore selectivity | Index may be worse than scan | Evaluate actual data distribution |

---

## Common Mistakes

### Mistake: "Functions on indexed columns are always bad"

False.

The real issue is whether the database has an efficient access path for the resulting expression.

An expression index can make:

```sql
LOWER(email)
```

efficient.

### Mistake: Automatically Creating Expression Indexes

Not every query needs one.

If the table has 10,000 rows and the query runs once per day, an additional index may provide little value.

### Mistake: Casting the Column Instead of the Parameter

Prefer:

```sql
WHERE customer_id = $1::bigint
```

over unnecessarily transforming:

```sql
WHERE customer_id::text = $1
```

when the requirement is numeric equality.

### Mistake: Using DATE() for Daily Filtering

Avoid:

```sql
WHERE created_at::date = $1
```

when a timestamp range can express the same requirement:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

### Mistake: Assuming a Sequential Scan Is a Bug

For small tables or low-selectivity predicates, a sequential scan can be optimal.

The execution plan is the authority.

---

## Troubleshooting Workflow

When a query containing a function is slow:

1. Identify every function applied to a column.
2. Check whether that column has an ordinary index.
3. Compare the query expression with the index expression.
4. Run `EXPLAIN (ANALYZE, BUFFERS)`.
5. Check estimated versus actual rows.
6. Determine whether the predicate can be rewritten.
7. Check whether data normalization can eliminate the function.
8. Consider an expression index.
9. Measure write/storage cost.
10. Re-test under realistic concurrency.

A useful comparison is:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE created_at::date = DATE '2026-09-05';
```

versus:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE created_at >= TIMESTAMP '2026-09-05 00:00:00'
  AND created_at <  TIMESTAMP '2026-09-06 00:00:00';
```

The difference in plan and buffer usage often makes the access-path problem obvious.

---

## Senior Query Review Framework

When reviewing:

```sql
WHERE FUNCTION(column) = value
```

ask:

```text
Why is the function necessary?
        │
        ├── Data should already be normalized
        │       └── Fix write/application boundary
        │
        ├── Predicate can be rewritten
        │       └── Preserve indexed column
        │
        └── Function is business semantics
                └── Consider expression index
```

Then ask:

```text
Is this query performance-sensitive?
        │
        ├── No → keep design simple
        │
        └── Yes
             ↓
        Measure actual plan
             ↓
        Evaluate selectivity
             ↓
        Evaluate read/write trade-off
             ↓
        Deploy and monitor
```

This prevents premature indexing while still addressing real production bottlenecks.

---

## Decision Matrix

| Situation | Preferred approach |
|---|---|
| Exact equality on canonical data | Normal indexed column |
| Case-insensitive lookup | Canonical storage, appropriate type/index, or expression index |
| Daily timestamp filtering | Timestamp range |
| Parameter has wrong application type | Validate/normalize before query |
| Legacy data requires transformation | Expression index or migration |
| Frequently queried JSON field | Expression index or dedicated column |
| Rare transformation query | Accept scan if workload permits |
| Function-based sorting | Expression index if frequently required |
| Function-based join | Redesign/normalize join keys where possible |
| Derived value is a core domain attribute | Consider explicit/generated representation |
| High-write workload | Minimize additional indexes |
| Performance uncertainty | `EXPLAIN (ANALYZE, BUFFERS)` |

---

## Interview Traps

### Does using a function on a column always prevent index usage?

No.

The database may support the expression through:

- An expression index.
- A specialized index.
- An optimizer transformation.
- Another compatible access path.

Always inspect the plan.

### Why can `created_at::date` be problematic?

Because the predicate transforms the indexed timestamp into a date. A normal index on `created_at` is naturally suited to timestamp ranges, so:

```sql
created_at >= start
AND created_at < end
```

often provides a better access path.

### What is an expression index?

An index whose key is an expression rather than simply a column:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

### Is an expression index free after creation?

No.

It consumes storage and must be maintained on relevant writes.

### Which is generally better?

```sql
customer_id::text = $1
```

or:

```sql
customer_id = $1::bigint
```

When numeric equality is intended, preserving the native indexed column and converting the parameter is generally preferable.

### Should every slow function-based query get an expression index?

No.

First determine whether:

- The query can be rewritten.
- Data can be normalized.
- The query is actually important.
- The expression is selective.
- The index's maintenance cost is justified.

### How do you prove an index is helping?

Use the actual execution plan and production metrics:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and observe latency, I/O, CPU, and index usage under realistic workload.

## Key Takeaways

- **A function on an indexed column can prevent the ordinary index from being an efficient access path because the query operates on a transformed expression rather than the indexed value.**
- **Prefer rewriting predicates to preserve the indexed column when possible, such as using timestamp ranges instead of `created_at::date` and casting parameters rather than indexed columns.**
- **Expression indexes are a valid production solution when transformed lookups are intentional, frequent, and performance-sensitive, but they add storage and write-maintenance cost.**
- **Data normalization at the application or schema boundary can eliminate repeated query-time transformations and often provides a simpler long-term design.**
- **Never judge index effectiveness from SQL syntax alone; validate with `EXPLAIN (ANALYZE, BUFFERS)` and evaluate selectivity, concurrency, write amplification, replication, and operational cost.**