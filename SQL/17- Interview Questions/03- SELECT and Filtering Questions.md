# 03- SELECT and Filtering Questions

## Overview

`SELECT` and filtering are the foundation of SQL query construction. Interviewers use them to test whether you understand not only syntax, but also:

- How rows are selected
- How predicates behave
- SQL's three-valued logic
- `NULL` semantics
- Boolean operator precedence
- Pattern matching
- Ordering and pagination
- Expressions and aliases
- Type conversion
- Date/time filtering
- PostgreSQL-specific behavior
- Sargability and index usage
- Query correctness under production data volumes

For backend engineers, filtering is particularly important because API endpoints frequently translate request parameters into database predicates:

```text
HTTP request
    ↓
Django / FastAPI
    ↓
Validation
    ↓
Query construction
    ↓
Parameterized SQL
    ↓
PostgreSQL planner
    ↓
Execution
    ↓
Filtered result
```

A strong interview answer should distinguish **logical correctness** from **performance**. A predicate can return the correct rows while still being expensive to execute.

---

## What `SELECT` Does

A `SELECT` statement retrieves a result set from one or more relations.

Basic form:

```sql
SELECT
    id,
    email,
    name
FROM customers;
```

The selected expressions determine the columns in the result.

A query does not necessarily return physical rows exactly as they exist on disk. PostgreSQL evaluates the relational expression and produces a result according to the query semantics.

---

## Selecting Specific Columns

Prefer explicit projections in production application queries:

```sql
SELECT
    id,
    email,
    created_at
FROM customers;
```

instead of:

```sql
SELECT *
FROM customers;
```

Explicit projections provide several benefits:

- Less data transferred
- Lower application memory usage
- Less serialization work
- More stable API/query contracts
- Easier code review
- Reduced exposure of sensitive columns

### Interview question

**Is `SELECT *` always bad?**

No.

It can be reasonable for:

- Interactive exploration
- Administrative investigation
- Small internal queries
- Some controlled scripts

The concern is using it indiscriminately in high-volume application paths.

---

## Column Aliases

Aliases rename result columns:

```sql
SELECT
    id AS customer_id,
    email AS customer_email
FROM customers;
```

Aliases are especially useful when joining tables containing similarly named columns.

```sql
SELECT
    c.id AS customer_id,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Clear aliases reduce ambiguity in application code and result processing.

---

## Expressions in `SELECT`

The projection can contain expressions.

```sql
SELECT
    id,
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items;
```

The database evaluates the expression for each qualifying row.

Common expressions include:

- Arithmetic
- `CASE`
- `COALESCE`
- String functions
- Date functions
- Type casts
- JSON operators

---

## `SELECT DISTINCT`

`DISTINCT` removes duplicate result rows.

```sql
SELECT DISTINCT
    customer_id
FROM orders;
```

If the result contains:

```text
1
1
2
2
3
```

the result becomes:

```text
1
2
3
```

### Important interview distinction

`DISTINCT` operates on the selected result columns.

These are different:

```sql
SELECT DISTINCT customer_id
FROM orders;
```

and:

```sql
SELECT DISTINCT customer_id, status
FROM orders;
```

The second query removes duplicates based on the combination:

```text
customer_id + status
```

---

## `DISTINCT` Is Not a Join Fix

Suppose:

```sql
SELECT DISTINCT c.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

This may return one customer ID per customer, but the join still creates potentially many intermediate matches.

If the requirement is simply:

> Find customers who have at least one order.

then:

```sql
SELECT c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

may communicate the requirement more directly.

Do not use `DISTINCT` merely to hide unexpected row multiplication.

---

## `WHERE`

`WHERE` filters rows according to a predicate.

```sql
SELECT
    id,
    email
FROM customers
WHERE status = 'active';
```

Only rows for which the predicate evaluates to `TRUE` are returned.

The predicate can contain:

```text
comparison
AND
OR
NOT
IN
BETWEEN
LIKE
IS NULL
EXISTS
subqueries
functions
```

---

## Boolean Expressions

Multiple predicates can be combined.

```sql
SELECT *
FROM orders
WHERE status = 'paid'
  AND amount >= 100;
```

Both conditions must be true.

With `OR`:

```sql
SELECT *
FROM orders
WHERE status = 'paid'
   OR status = 'shipped';
```

At least one condition must be true.

---

## `AND` vs `OR` Precedence

Consider:

```sql
WHERE status = 'paid'
   OR status = 'pending'
  AND priority = 'high'
```

SQL evaluates `AND` before `OR`, so this means:

```text
status = 'paid'
OR
(status = 'pending' AND priority = 'high')
```

If the intended logic is:

```text
(status = 'paid' OR status = 'pending')
AND priority = 'high'
```

write it explicitly:

```sql
WHERE (
    status = 'paid'
    OR status = 'pending'
)
AND priority = 'high';
```

### Interview recommendation

Use parentheses when business logic involves mixed `AND` and `OR`, even when precedence technically makes the expression unambiguous.

It improves maintainability and reduces review mistakes.

---

## `NOT`

`NOT` negates a predicate.

```sql
SELECT *
FROM orders
WHERE NOT status = 'cancelled';
```

This is often clearer as:

```sql
WHERE status <> 'cancelled';
```

However, `NULL` changes the semantics.

If:

```text
status = NULL
```

then:

```sql
status <> 'cancelled'
```

does not evaluate to `TRUE`.

It evaluates to `UNKNOWN`.

---

## SQL Three-Valued Logic

SQL predicates can produce:

```text
TRUE
FALSE
UNKNOWN
```

This is critical when `NULL` is involved.

For example:

```sql
SELECT
    NULL = NULL;
```

does not produce `TRUE`.

The comparison is `UNKNOWN`.

Because `WHERE` keeps only rows where the predicate is `TRUE`, rows with an unknown predicate result are excluded.

---

## `NULL` Filtering

Incorrect:

```sql
SELECT *
FROM customers
WHERE deleted_at = NULL;
```

Correct:

```sql
SELECT *
FROM customers
WHERE deleted_at IS NULL;
```

And:

```sql
SELECT *
FROM customers
WHERE deleted_at IS NOT NULL;
```

### Interview question

**Why is `= NULL` incorrect?**

Because `NULL` is not an ordinary value that can be compared using equality. SQL provides `IS NULL` and `IS NOT NULL` specifically for null testing.

---

## `NULL` With `AND`

Consider:

```text
TRUE AND UNKNOWN
```

The result is:

```text
UNKNOWN
```

But:

```text
FALSE AND UNKNOWN
```

is:

```text
FALSE
```

This matters when combining optional database fields with boolean predicates.

---

## `NULL` With `OR`

Consider:

```text
TRUE OR UNKNOWN
```

The result is:

```text
TRUE
```

while:

```text
FALSE OR UNKNOWN
```

is:

```text
UNKNOWN
```

These rules explain why apparently intuitive boolean expressions can behave differently when nullable columns are involved.

---

## `IS DISTINCT FROM`

PostgreSQL provides `IS DISTINCT FROM`, which treats `NULL` as a comparable value.

```sql
SELECT *
FROM users
WHERE last_login IS DISTINCT FROM $1;
```

Unlike ordinary `<>`, this provides a deterministic true/false comparison even when one or both values are `NULL`.

There is also:

```sql
IS NOT DISTINCT FROM
```

which provides null-safe equality semantics.

These operators are useful when `NULL` itself is part of the business meaning.

---

## Equality

Basic equality:

```sql
SELECT *
FROM customers
WHERE id = $1;
```

The use of a parameter placeholder is important in application code.

Avoid:

```python
query = f"SELECT * FROM customers WHERE id = {customer_id}"
```

Use parameter binding through the database driver or ORM.

---

## Inequality

SQL commonly uses:

```sql
<>
```

PostgreSQL also supports:

```sql
!=
```

Example:

```sql
SELECT *
FROM orders
WHERE status <> 'cancelled';
```

Remember that this does not automatically include rows where `status` is `NULL`.

If `NULL` should also qualify, express that explicitly:

```sql
WHERE status <> 'cancelled'
   OR status IS NULL;
```

---

## Comparison Operators

Common operators:

| Operator | Meaning |
|---|---|
| `=` | Equal |
| `<>` | Not equal |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `<` | Less than |
| `<=` | Less than or equal |

Example:

```sql
SELECT *
FROM orders
WHERE amount >= 100
  AND amount < 500;
```

---

## `IN`

`IN` tests membership in a set.

```sql
SELECT *
FROM orders
WHERE status IN (
    'pending',
    'paid',
    'shipped'
);
```

It is useful for small, known sets.

Application-generated lists should still use parameter binding rather than interpolating raw values into SQL.

---

## `NOT IN`

```sql
SELECT *
FROM orders
WHERE status NOT IN (
    'cancelled',
    'refunded'
);
```

`NOT IN` becomes dangerous when the comparison set contains `NULL`.

For example:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
);
```

If the subquery can return `NULL`, SQL's three-valued logic can produce surprising results.

For anti-existence requirements, prefer:

```sql
WHERE NOT EXISTS (...)
```

when appropriate.

---

## `ANY` and Arrays in PostgreSQL

PostgreSQL can compare a value against an array:

```sql
SELECT *
FROM orders
WHERE status = ANY($1::text[]);
```

This can be useful when an application passes a collection as one parameter.

It can also be useful for ID lists:

```sql
SELECT *
FROM customers
WHERE id = ANY($1::bigint[]);
```

This keeps values parameterized without constructing a variable-length SQL string.

---

## `ALL`

`ALL` compares a value against every value in a set or array.

For example:

```sql
SELECT *
FROM products
WHERE price > ALL($1::numeric[]);
```

This means the price must be greater than every value in the supplied array.

`ANY` and `ALL` are useful when expressing quantified comparisons directly.

---

## `BETWEEN`

`BETWEEN` is inclusive on both boundaries.

```sql
SELECT *
FROM products
WHERE price BETWEEN 100 AND 500;
```

This means:

```sql
price >= 100
AND price <= 500
```

### Timestamp warning

For time ranges, inclusive upper bounds often create boundary problems.

Prefer:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

For example:

```text
[start, end)
```

This is easier to compose for adjacent time periods.

---

## Date Range Filtering

For an API that receives:

```text
from = 2026-09-01
to   = 2026-10-01
```

prefer an explicit range:

```sql
SELECT *
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

Avoid:

```sql
WHERE DATE(created_at) BETWEEN $1 AND $2;
```

The range form generally provides a better opportunity for ordinary index usage.

---

## `LIKE`

`LIKE` performs pattern matching.

```sql
SELECT *
FROM customers
WHERE email LIKE 'admin%';
```

Patterns:

| Pattern | Meaning |
|---|---|
| `'abc%'` | Starts with `abc` |
| `'%abc'` | Ends with `abc` |
| `'%abc%'` | Contains `abc` |
| `'a_c'` | `a`, any one character, `c` |

---

## `LIKE` and Indexes

A prefix search:

```sql
WHERE email LIKE 'admin%'
```

can be compatible with certain B-tree index strategies.

A leading wildcard:

```sql
WHERE email LIKE '%admin%'
```

usually cannot use a normal B-tree index for the same straightforward prefix-search purpose.

For substring search at scale, PostgreSQL trigram indexes or a dedicated search engine may be more appropriate.

---

## `ILIKE`

PostgreSQL provides case-insensitive pattern matching through `ILIKE`.

```sql
SELECT *
FROM customers
WHERE email ILIKE 'admin%';
```

As with `LIKE`, performance depends on the pattern and index strategy.

Do not assume that case-insensitive search automatically uses a conventional B-tree index.

---

## Escaping Pattern Characters

`LIKE` treats:

```text
%
_
```

as wildcard characters.

If user input is used in a search pattern, applications may need to escape wildcard characters when the intended semantics are literal text matching.

For example, searching for:

```text
50%
```

should not accidentally mean:

```text
"starts with 50"
```

when the application intends to search for a literal percent sign.

---

## `ILIKE` vs Normalized Data

If an application frequently performs case-insensitive equality:

```sql
WHERE lower(email) = lower($1)
```

consider whether the system should:

- Store normalized values
- Use an expression index
- Use PostgreSQL's `citext` where appropriate
- Enforce a suitable uniqueness rule

For example:

```sql
CREATE UNIQUE INDEX idx_users_email_lower
ON users (lower(email));
```

This makes the access pattern explicit.

---

## `IS NULL`

Use:

```sql
WHERE deleted_at IS NULL
```

for null checks.

This is common with soft-delete models:

```sql
SELECT
    id,
    email
FROM users
WHERE deleted_at IS NULL;
```

If active rows are queried frequently, a partial index can sometimes help:

```sql
CREATE INDEX idx_users_active
ON users (created_at)
WHERE deleted_at IS NULL;
```

---

## `IS TRUE` and `IS FALSE`

For nullable booleans:

```sql
WHERE is_active IS TRUE
```

and:

```sql
WHERE is_active IS FALSE
```

can be clearer than relying on ordinary equality.

If `is_active` is `NULL`, it is neither `TRUE` nor `FALSE`.

Whether `NULL` should be possible is a schema-design decision.

---

## Boolean Filtering

For a non-null boolean column:

```sql
SELECT *
FROM users
WHERE is_active;
```

can be concise.

Explicit form:

```sql
WHERE is_active IS TRUE;
```

is often clearer when nullability exists or when the codebase prefers explicit predicates.

---

## Filtering With `CASE`

`CASE` can implement conditional logic:

```sql
SELECT *
FROM orders
WHERE CASE
    WHEN priority = 'high' THEN amount >= 100
    ELSE amount >= 500
END;
```

However, complicated conditional predicates can be harder to optimize and maintain.

When possible, express business rules directly:

```sql
WHERE (
    priority = 'high'
    AND amount >= 100
)
OR (
    priority <> 'high'
    AND amount >= 500
);
```

Then validate both correctness and performance.

---

## `COALESCE` in Filtering

Consider:

```sql
WHERE COALESCE(status, 'unknown') = 'pending';
```

This treats `NULL` as `'unknown'`.

But if the intention is simply:

```text
status must equal pending
```

then:

```sql
WHERE status = 'pending';
```

is clearer.

Wrapping a column in an expression can also affect available index access paths unless the index matches the expression.

---

## Sargability

A predicate is often described as **sargable** when the database can efficiently use an index or access path based on the predicate.

Prefer:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

over:

```sql
WHERE DATE(created_at) = $1
```

The second expression transforms the indexed column before comparison.

This does not mean every function-wrapped predicate is always slow, but it should trigger an execution-plan review.

---

## Functions in Predicates

Consider:

```sql
WHERE lower(email) = lower($1)
```

This can be efficient if an appropriate expression index exists:

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

Without the matching access path, the database may need to perform more work.

The principle is:

> Design the index and predicate together around the real access pattern.

---

## Type Conversion and Filtering

Suppose:

```sql
customer_id bigint
```

and the application supplies a correctly typed parameter.

Prefer:

```sql
WHERE customer_id = $1
```

Be cautious with:

```sql
WHERE customer_id::text = $1
```

because casting the indexed column can change the available execution strategies.

Type correctness should be established at the application/database boundary where possible.

---

## Filtering JSONB

PostgreSQL supports filtering structured JSONB data.

Example:

```sql
SELECT *
FROM events
WHERE payload @> '{"event_type": "payment"}';
```

For frequent JSONB queries, an appropriate GIN index may help:

```sql
CREATE INDEX idx_events_payload
ON events
USING gin (payload);
```

Do not automatically move relational attributes into JSONB merely because the database supports it.

Frequently queried and constrained fields often belong in ordinary columns.

---

## Filtering by Tenant

In multi-tenant applications, filtering usually includes tenant scope:

```sql
SELECT
    id,
    status,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND status = $2;
```

The tenant predicate is part of correctness and security.

Indexes should reflect common access paths:

```sql
CREATE INDEX idx_orders_tenant_status
ON orders (tenant_id, status);
```

Depending on the architecture, PostgreSQL Row Level Security can provide an additional database-level enforcement layer.

---

## Authorization Is Not Just Filtering

Consider:

```sql
SELECT *
FROM documents
WHERE id = $1;
```

Finding the row does not prove the requesting user is allowed to access it.

A secure query might require:

```sql
SELECT d.*
FROM documents AS d
JOIN memberships AS m
    ON m.organization_id = d.organization_id
WHERE d.id = $1
  AND m.user_id = $2;
```

Authorization should be tied to the resource relationship rather than trusting a client-provided tenant or organization identifier.

---

## Filtering and Row Level Security

With PostgreSQL RLS, an application query may appear to be:

```sql
SELECT *
FROM orders
WHERE status = 'paid';
```

while the database additionally applies policies controlling which rows the current role can see.

This means:

```text
Application predicate
        +
RLS policy
        ↓
Effective visible rows
```

When debugging missing data, verify both application filters and database security policies.

---

## `ORDER BY`

Filtering determines which rows qualify.

`ORDER BY` determines their output order.

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC;
```

Ordering is not guaranteed unless explicitly requested.

Do not rely on:

```text
primary key order
insertion order
physical table order
```

as implicit ordering.

---

## Deterministic Ordering

If multiple rows have the same timestamp:

```sql
ORDER BY created_at DESC;
```

their relative order is not guaranteed.

Prefer:

```sql
ORDER BY created_at DESC, id DESC;
```

This is especially important for pagination.

---

## `NULLS FIRST` and `NULLS LAST`

PostgreSQL allows explicit null ordering.

```sql
ORDER BY last_login DESC NULLS LAST;
```

This makes the desired behavior explicit.

Without an explicit choice, the database has defined default null ordering based on sort direction, which may not match the business requirement.

---

## `LIMIT` and Filtering

A typical API query:

```sql
SELECT
    id,
    email
FROM customers
WHERE status = 'active'
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

`LIMIT` restricts the final number of returned rows.

With an appropriate index and plan, PostgreSQL may be able to stop processing early.

But `LIMIT` does not guarantee low cost.

The database may still need to perform substantial filtering, joining, or sorting first.

---

## `OFFSET`

Example:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 10000;
```

Deep offsets can require processing and discarding many rows.

For large datasets, keyset pagination is usually a better production strategy.

---

## Keyset Pagination

Use the last row from the previous page as a cursor.

```sql
SELECT
    id,
    created_at
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

This can remain efficient as the dataset grows when the access path is indexed appropriately.

A common index for this access pattern is:

```sql
CREATE INDEX idx_orders_created_id
ON orders (created_at DESC, id DESC);
```

The exact index should still be validated against the query and workload.

---

## Filtering Before Sorting

Conceptually:

```text
FROM
 ↓
WHERE
 ↓
ORDER BY
 ↓
LIMIT
```

This means filtering can reduce the rows that need to be sorted.

For example:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

An index matching the filtering and ordering pattern can potentially make this substantially more efficient.

---

## Filtering and Joins

Consider:

```sql
SELECT
    c.id,
    c.email,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.status = 'active';
```

The optimizer determines how to execute the join and filter.

Do not rely on the textual order of clauses as a direct representation of physical execution order.

The planner may reorder operations when semantics allow it.

---

## Filtering in `ON` vs `WHERE`

Compare:

```sql
SELECT c.id, o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'paid';
```

with:

```sql
SELECT c.id, o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

The first preserves customers with no paid orders.

The second filters out rows where the right side is `NULL`, effectively changing the result semantics toward an inner join for that condition.

This is one of the most common `SELECT` interview traps.

---

## Filtering With `EXISTS`

When the requirement is existence:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

This avoids returning order rows when the application only needs customers.

The optimizer may choose different physical strategies depending on statistics and indexes.

---

## Filtering With `NOT EXISTS`

For non-existence:

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This is a common and reliable anti-join pattern.

---

## Filtering With Subqueries

Example:

```sql
SELECT *
FROM products
WHERE price > (
    SELECT AVG(price)
    FROM products
);
```

This returns products whose price is greater than the average.

The subquery produces a scalar value used by the outer predicate.

For complex queries, compare alternative formulations with execution plans rather than assuming one syntax is universally faster.

---

## Filtering With Aggregate Results

Aggregates cannot generally be used directly in `WHERE`.

Incorrect:

```sql
SELECT customer_id
FROM orders
WHERE COUNT(*) > 5
GROUP BY customer_id;
```

Use:

```sql
SELECT customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 5;
```

The distinction is based on the logical stage at which filtering occurs.

---

## Filtering Window Function Results

A window function result generally cannot be referenced directly in the same query block's `WHERE` clause.

Use a subquery or CTE:

```sql
SELECT *
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn = 1;
```

This creates a query level where `rn` is available for filtering.

---

## Filtering by Date in PostgreSQL

For time-based APIs:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

This is preferable to extracting the date from every row:

```sql
WHERE created_at::date = $1;
```

when the column has a suitable index and the application can provide proper range boundaries.

---

## Time Zone Considerations

Filtering timestamps requires a clear timezone model.

For example:

```text
"Orders created today"
```

is ambiguous unless "today" is defined in a timezone.

A production API should establish whether the business period is based on:

- UTC
- Customer timezone
- Tenant timezone
- Region
- A fixed business timezone

Then convert the requested period into explicit timestamp boundaries.

---

## Filtering Numeric Ranges

For numeric values:

```sql
SELECT *
FROM products
WHERE price >= $1
  AND price < $2;
```

Use the boundary semantics that match the business requirement.

For money, use exact numeric types rather than floating-point types when exact decimal arithmetic is required.

---

## Filtering Text

For exact matching:

```sql
WHERE email = $1
```

For prefix search:

```sql
WHERE email LIKE $1
```

For substring search:

```sql
WHERE name ILIKE $1
```

The indexing strategy should correspond to the search requirement.

Do not assume that one index can efficiently support every type of text search.

---

## Filtering Enumerated States

Suppose an order has:

```text
pending
paid
shipped
cancelled
```

An API can filter:

```sql
SELECT *
FROM orders
WHERE status IN ('pending', 'paid');
```

At schema level, the allowed states can also be represented using:

- Check constraints
- PostgreSQL enum types
- Reference tables
- Application state machines

The appropriate choice depends on how frequently the state model changes and whether database-level enforcement is required.

---

## Filtering Soft-Deleted Records

A common pattern:

```sql
SELECT *
FROM customers
WHERE deleted_at IS NULL;
```

The application must consistently apply the visibility rule.

Possible strategies include:

- ORM managers/querysets
- Database views
- RLS
- Explicit query predicates
- Separate archival tables

Each has trade-offs.

A hidden ORM default should not make engineers forget that the database still contains deleted records.

---

## Filtering and Partial Indexes

If almost every query filters:

```sql
WHERE deleted_at IS NULL
```

a partial index may be useful:

```sql
CREATE INDEX idx_customers_active_created
ON customers (created_at DESC, id DESC)
WHERE deleted_at IS NULL;
```

The index covers only active rows.

This can reduce index size and write overhead compared with indexing every row, depending on the data distribution.

---

## Filtering and Composite Indexes

Suppose the common query is:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

A candidate index might be:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC
);
```

The exact ordering should be based on the broader workload.

Index design is not simply:

> One `WHERE` condition = one index.

The complete filtering and ordering pattern matters.

---

## Filtering and Low-Cardinality Columns

Suppose:

```text
status = 'active'
```

matches 95% of a table.

An index on only:

```sql
(status)
```

may not provide much benefit for that query.

The optimizer may correctly choose a sequential scan.

Low cardinality does not mean an index is never useful; it means selectivity and complete access patterns must be considered.

---

## Filtering and Statistics

PostgreSQL uses statistics to estimate how many rows a predicate will match.

For:

```sql
WHERE status = 'pending'
```

the optimizer estimates selectivity based on statistics.

If estimates are substantially wrong, PostgreSQL may choose a poor plan.

Possible causes include:

- Stale statistics
- Data skew
- Correlated columns
- Complex predicates

The solution is not automatically adding an index.

---

## Filtering and Execution Plans

For important production queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

Inspect:

- Estimated rows
- Actual rows
- Scan type
- Sorts
- Join operations
- Buffer activity
- Execution time

A filtering question can therefore become an execution-plan question at senior level.

---

## Filtering and Query Frequency

Consider two queries:

```text
Query A:
500 ms
10 times/hour

Query B:
10 ms
100,000 times/hour
```

Query B can have a larger production impact.

Filtering optimization should therefore consider:

```text
latency
×
frequency
×
concurrency
```

This is why query statistics such as `pg_stat_statements` are valuable.

---

## Filtering and Connection Pools

An inefficient filtering query can cause connection pressure:

```text
Expensive filter
      ↓
Longer query execution
      ↓
Connection held longer
      ↓
Pool exhaustion
      ↓
Requests wait
      ↓
Latency increases
```

Therefore a filtering optimization can have system-wide effects beyond the query itself.

---

## Filtering in Django

Django ORM filtering:

```python
orders = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="paid",
    )
    .order_by("-created_at", "-id")[:50]
)
```

Conceptually produces SQL similar to:

```sql
SELECT ...
FROM orders
WHERE tenant_id = %s
  AND status = %s
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

The exact generated SQL depends on the model and query construction.

The backend engineer should understand both layers.

---

## Django `Q` Objects

Complex boolean conditions can be represented using `Q`.

```python
from django.db.models import Q

orders = Order.objects.filter(
    Q(status="paid") | Q(status="shipped"),
    customer_id=customer_id,
)
```

The resulting logic is conceptually:

```sql
WHERE (
    status = 'paid'
    OR status = 'shipped'
)
AND customer_id = ...
```

Use explicit grouping when the business condition is complex.

---

## Django `isnull`

Django translates:

```python
Customer.objects.filter(deleted_at__isnull=True)
```

to a null check conceptually equivalent to:

```sql
WHERE deleted_at IS NULL
```

This is preferable to trying to compare nullable fields against Python `None` using ordinary equality semantics in a way that obscures intent.

---

## Django `__in`

Example:

```python
Order.objects.filter(
    status__in=["pending", "paid"]
)
```

Conceptually:

```sql
WHERE status IN (...)
```

For very large ID lists, reconsider whether a giant `IN` predicate is the best architecture. Depending on the workload, temporary tables, staging relations, arrays, or batch processing may be more appropriate.

---

## FastAPI and SQLAlchemy Filtering

With SQLAlchemy:

```python
stmt = (
    select(Order)
    .where(
        Order.tenant_id == tenant_id,
        Order.status == "paid",
    )
    .order_by(
        Order.created_at.desc(),
        Order.id.desc(),
    )
    .limit(50)
)
```

SQLAlchemy handles value binding.

The database still determines:

- Access path
- Join strategy
- Filtering execution
- Sorting
- Resource consumption

---

## REST API Filtering

A typical endpoint might accept:

```text
GET /orders?status=paid&limit=50
```

The backend should:

1. Validate the request.
2. Convert API parameters into known query semantics.
3. Apply authorization and tenant scope.
4. Bind values safely.
5. Apply bounded pagination.
6. Execute the query.
7. Return only required columns.

Do not blindly translate arbitrary query parameters into SQL expressions.

---

## Dynamic Filtering Security

This pattern is dangerous:

```text
GET /orders?sort=<arbitrary SQL>
```

or an implementation such as:

```python
query = f"SELECT * FROM orders ORDER BY {sort}"
```

Instead, map known API values:

```python
allowed_sort_fields = {
    "created": "created_at",
    "amount": "total_amount",
    "id": "id",
}
```

Then use only the mapped SQL identifier.

Values should still use parameter binding.

---

## Filtering and SQL Injection

Safe:

```python
cursor.execute(
    """
    SELECT id, email
    FROM customers
    WHERE email = %s
    """,
    (email,),
)
```

Unsafe:

```python
query = f"""
SELECT id, email
FROM customers
WHERE email = '{email}'
"""
```

The difference is that parameterized execution keeps user-controlled values separate from SQL structure.

---

## Filtering and Search APIs

Search endpoints can become database-heavy quickly.

For example:

```text
GET /customers?search=abc
```

may translate into:

```sql
WHERE name ILIKE '%abc%'
   OR email ILIKE '%abc%';
```

At scale, this can be expensive.

Possible strategies include:

- Specialized indexes
- PostgreSQL trigram search
- Full-text search
- Search engines
- Prefix search
- Precomputed search fields

Choose based on actual requirements rather than prematurely adding infrastructure.

---

## Common Filtering Mistakes

### Comparing With `NULL`

Wrong:

```sql
WHERE column = NULL
```

Correct:

```sql
WHERE column IS NULL
```

### Mixing `AND` and `OR` Without Parentheses

Ambiguous:

```sql
WHERE a = 1 OR b = 2 AND c = 3
```

Prefer explicit grouping when required:

```sql
WHERE (a = 1 OR b = 2)
  AND c = 3;
```

### Using `DISTINCT` to Hide Duplicates

Unexpected duplicates usually indicate a cardinality or join problem.

### Applying Functions to Indexed Columns

Potentially problematic:

```sql
WHERE DATE(created_at) = $1
```

Prefer a range when appropriate.

### Deep `OFFSET`

Large offsets can become increasingly expensive.

Use keyset pagination for large datasets when appropriate.

### Returning Too Many Columns

Avoid unnecessary:

```sql
SELECT *
```

in high-volume API paths.

### Trusting Client Tenant IDs

A request parameter such as:

```text
tenant_id=123
```

is not itself authorization.

Derive access from authenticated identity and authorization relationships.

---

## Interview Traps

### Is `WHERE` evaluated before `SELECT`?

Logically, `WHERE` is evaluated before the final `SELECT` projection in the conceptual query-processing model.

This explains why a `SELECT` alias generally cannot be referenced directly in the same query block's `WHERE`.

For example:

```sql
SELECT
    amount * 1.18 AS total
FROM orders
WHERE total > 100;
```

is not valid in the usual SQL semantics because `total` is a select-list alias.

Use a subquery/CTE or repeat the expression where appropriate.

---

### Does SQL Guarantee Row Order?

No.

Without `ORDER BY`, row order is not guaranteed.

Even if a query appears to return rows in primary-key order today, relying on that behavior is incorrect.

---

### Is `BETWEEN` Inclusive?

Yes.

For ordinary scalar comparisons:

```sql
x BETWEEN a AND b
```

means:

```sql
x >= a
AND x <= b
```

For timestamp ranges, half-open intervals are often safer.

---

### Is `LIKE '%abc%'` Fast?

Not necessarily.

A leading wildcard makes ordinary B-tree prefix matching ineffective for that pattern.

At scale, use an appropriate search/indexing strategy.

---

### Does `LIMIT` Make Any Query Fast?

No.

The database may still need to perform expensive filtering, sorting, joins, or aggregation before returning the limited result.

---

### Does `DISTINCT` Always Make Queries Slow?

No.

It can introduce additional work for deduplication, but the cost depends on the plan, number of rows, memory, and data distribution.

The correct answer is to measure.

---

### Is `IN` Always Worse Than `EXISTS`?

No.

Modern optimizers can transform semantically equivalent queries, and actual performance depends on the query shape and data.

Choose based on semantics first and verify performance with an execution plan.

---

### Is a Sequential Scan Bad?

No.

A sequential scan is often the correct plan for:

- Small tables
- Low-selectivity predicates
- Large portions of a table
- Some analytical workloads

The question is whether the chosen plan is appropriate for the workload.

---

## Production Filtering Checklist

Before shipping a filtered query:

- [ ] Predicate semantics are correct.
- [ ] `NULL` behavior is intentional.
- [ ] `AND`/`OR` grouping is explicit.
- [ ] Tenant scope is enforced.
- [ ] Authorization is enforced.
- [ ] User values are parameterized.
- [ ] Dynamic identifiers are allowlisted.
- [ ] Date/time boundaries are explicit.
- [ ] Ordering is deterministic where pagination requires it.
- [ ] Result size is bounded.
- [ ] Large pagination uses an appropriate strategy.
- [ ] Functions on indexed columns are intentional.
- [ ] Indexes match important access patterns.
- [ ] Query plans have been reviewed for critical paths.
- [ ] Query frequency and concurrency are understood.
- [ ] Connection-pool impact is acceptable.

---

## Senior Interview Reasoning Framework

When an interviewer gives you a filtering problem, reason in this order:

```text
What rows are required?
        ↓
What is the result grain?
        ↓
What predicates define eligibility?
        ↓
How does NULL behave?
        ↓
Are joins required?
        ↓
What ordering is required?
        ↓
How many rows can match?
        ↓
How will pagination work?
        ↓
What indexes support the access pattern?
        ↓
What does EXPLAIN show?
        ↓
What happens under production concurrency?
```

This approach prevents premature optimization.

---

## Practical Example

Suppose an API needs:

> Return the latest 50 paid orders for a tenant created after a given timestamp.

A reasonable query is:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM orders
WHERE tenant_id = $1
  AND status = 'paid'
  AND created_at >= $2
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Potential index:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC,
    id DESC
);
```

But this is only a candidate.

A production review should verify:

- Actual cardinality
- Tenant distribution
- Status distribution
- Query frequency
- Insert/update workload
- Index size
- Execution plan
- Replica behavior
- Connection impact

The correct index is determined by the workload, not the SQL text alone.

---

## Filtering Decision Matrix

| Requirement | Typical SQL |
|---|---|
| Exact value | `=` |
| Multiple allowed values | `IN` |
| Range | `>=` / `<` |
| Nullable field | `IS NULL` / `IS NOT NULL` |
| Prefix search | `LIKE 'abc%'` |
| Case-insensitive PostgreSQL search | `ILIKE` |
| Existence | `EXISTS` |
| Non-existence | `NOT EXISTS` |
| Group filtering | `HAVING` |
| Ranking filter | Subquery/CTE around window function |
| Large pagination | Keyset/cursor |
| Tenant isolation | Tenant predicate + authorization/RLS where appropriate |
| Dynamic sort | Allowlisted identifiers |
| Large analytical filtering | Workload-appropriate OLAP strategy |

---

## Key Takeaways

- **Correct filtering starts with semantics:** define the required rows, result grain, `NULL` behavior, boolean grouping, and relationship boundaries before optimizing the query.
- **Production predicates must be safe and scalable:** parameterize values, allowlist dynamic SQL structure, enforce tenant authorization, bound result sizes, and use appropriate pagination.
- **Sargability and access paths matter:** avoid unnecessary transformations of indexed columns, design indexes around complete filtering and ordering patterns, and validate decisions with execution plans.
- **`SELECT` performance is workload-dependent:** projections, filtering, sorting, pagination, query frequency, concurrency, and connection pools all contribute to production impact.
- **Senior SQL reasoning connects correctness to architecture:** filtering decisions should account for authorization, ORM-generated SQL, replicas, caching, concurrency, observability, and long-term data growth.