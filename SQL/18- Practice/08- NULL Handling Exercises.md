# 08- NULL Handling Exercises

## Overview

`NULL` handling is one of the most common sources of SQL bugs because `NULL` does not mean zero, an empty string, `false`, or a missing database row. It represents an **unknown or absent value**, and SQL's three-valued logic changes how comparisons, filtering, aggregation, joins, and constraints behave.

These exercises focus on developing the ability to reason about:

- `NULL` comparisons.
- Three-valued logic.
- `IS NULL` and `IS NOT NULL`.
- `COALESCE`.
- `NULLIF`.
- `CASE`.
- Aggregate behavior.
- `LEFT JOIN` semantics.
- `NOT IN` versus `NOT EXISTS`.
- `NULL` in uniqueness and constraints.
- API representation of nullable fields.
- PostgreSQL-specific behavior.
- Production query correctness.

The goal is not to memorize special syntax. The goal is to answer:

> **What does an unknown value mean in this business domain, and how should SQL treat it?**

---

## Practice Schema

Use the following PostgreSQL schema for the exercises:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    phone text,
    organization_id bigint NOT NULL,
    status text NOT NULL
        CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku text NOT NULL UNIQUE,
    name text NOT NULL,
    description text,
    price numeric(12, 2),
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id),
    discount_amount numeric(12, 2),
    shipping_amount numeric(12, 2),
    total_amount numeric(12, 2) NOT NULL,
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    shipped_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL
        REFERENCES orders(id),
    transaction_reference text,
    amount numeric(12, 2),
    refunded_amount numeric(12, 2),
    paid_at timestamptz,
    status text NOT NULL
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded'))
);
```

The nullable columns are intentional. They represent values that may not exist yet or may legitimately be unknown.

---

## What `NULL` Means

`NULL` generally represents an absent, unknown, or inapplicable value.

For example:

```text
phone = NULL
```

could mean:

- The customer did not provide a phone number.
- The phone number is not known.
- The phone number is not applicable.

Those meanings are different from:

```text
phone = ''
```

An empty string is a known string containing zero characters.

Likewise:

```text
discount_amount = 0
```

means a known discount of zero.

```text
discount_amount = NULL
```

means the discount amount is absent or unknown.

The database cannot infer the business meaning for you.

---

## `NULL` Is Not Zero

This expression is not equivalent to:

```sql
discount_amount = 0
```

and:

```sql
discount_amount IS NULL
```

They answer different questions.

Find orders with no recorded discount:

```sql
SELECT *
FROM orders
WHERE discount_amount IS NULL;
```

Find orders with an explicitly recorded zero discount:

```sql
SELECT *
FROM orders
WHERE discount_amount = 0;
```

If the business considers these equivalent, normalize the representation deliberately rather than relying on accidental query behavior.

---

## `NULL` Is Not an Empty String

For text:

```sql
phone IS NULL
```

means there is no value.

This:

```sql
phone = ''
```

means the value is an empty string.

Find either:

```sql
SELECT *
FROM customers
WHERE phone IS NULL
   OR phone = '';
```

However, this is often a sign that the data model has two representations for the same business state.

A cleaner model may normalize blank input to `NULL` at the application boundary.

---

## `NULL` Is Not False

For a nullable boolean:

```text
TRUE
FALSE
NULL
```

there are three possible states.

They can represent:

```text
TRUE  → explicitly enabled
FALSE → explicitly disabled
NULL  → not yet specified
```

Do not automatically treat:

```sql
NULL
```

as:

```sql
FALSE
```

unless the domain explicitly defines that behavior.

For non-null boolean columns, prefer:

```sql
boolean NOT NULL DEFAULT false
```

when the business domain has only two states.

---

## Equality and `NULL`

This is a common mistake:

```sql
SELECT *
FROM customers
WHERE phone = NULL;
```

This does not correctly find NULL values.

Use:

```sql
SELECT *
FROM customers
WHERE phone IS NULL;
```

Similarly:

```sql
WHERE phone <> NULL
```

does not correctly mean "phone is not NULL."

Use:

```sql
WHERE phone IS NOT NULL;
```

---

## Three-Valued Logic

SQL predicates can evaluate to:

| Result | Meaning |
|---|---|
| `TRUE` | Predicate is known to be true |
| `FALSE` | Predicate is known to be false |
| `UNKNOWN` | Predicate cannot be determined |

`NULL` comparisons frequently produce `UNKNOWN`.

For example:

```sql
NULL = 10
```

produces `UNKNOWN`.

```sql
NULL <> 10
```

also produces `UNKNOWN`.

A `WHERE` clause returns rows only when its predicate evaluates to `TRUE`.

Therefore:

```sql
WHERE value = 10
```

does not return rows where `value` is NULL.

---

## `AND` With `NULL`

Three-valued logic matters when combining predicates.

Conceptually:

| A | B | A AND B |
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

Example:

```sql
WHERE discount_amount > 10
  AND status = 'completed'
```

If `discount_amount` is NULL, the first predicate is `UNKNOWN`.

The combined result is not `TRUE`, so the row is filtered out.

---

## `OR` With `NULL`

| A | B | A OR B |
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

This matters for conditions such as:

```sql
WHERE status = 'completed'
   OR completed_at IS NULL;
```

The `IS NULL` expression returns a definite boolean, unlike a normal comparison with NULL.

---

## `NOT` With `NULL`

A common misconception is:

```sql
NOT (value = 10)
```

is equivalent to:

```sql
value <> 10
```

For non-NULL values, they usually behave similarly.

For NULL:

```sql
value = 10
```

is `UNKNOWN`.

Therefore:

```sql
NOT UNKNOWN
```

is still `UNKNOWN`.

Neither expression returns the NULL row from a `WHERE` clause.

If NULL needs explicit treatment, write it explicitly.

---

## `IS NULL`

Use `IS NULL` for null detection:

```sql
SELECT *
FROM orders
WHERE shipped_at IS NULL;
```

This can identify orders that have not yet received a shipping timestamp.

However, be careful about business semantics.

For example:

```sql
shipped_at IS NULL
```

does not necessarily mean:

```text
order has not shipped
```

unless the schema contract guarantees that `shipped_at` is populated whenever shipping occurs.

---

## `IS NOT NULL`

Find orders with a recorded completion timestamp:

```sql
SELECT *
FROM orders
WHERE completed_at IS NOT NULL;
```

This is different from checking:

```sql
status = 'completed'
```

A production system should define which field is authoritative.

If both fields are supposed to represent the same state, consider a constraint or state-transition design that prevents contradictions.

---

## Exercise: Basic NULL Filtering

Write queries to:

1. Find customers without phone numbers.
2. Find customers with phone numbers.
3. Find products without descriptions.
4. Find products with prices.
5. Find orders without discounts.
6. Find orders with shipping timestamps.
7. Find orders without shipping timestamps.
8. Find orders without completion timestamps.
9. Find payments without transaction references.
10. Find payments without payment timestamps.

---

## `COALESCE`

`COALESCE` returns the first non-NULL expression.

```sql
SELECT
    id,
    COALESCE(phone, 'not provided') AS phone
FROM customers;
```

For numeric values:

```sql
SELECT
    id,
    COALESCE(discount_amount, 0) AS discount_amount
FROM orders;
```

This is useful when converting database NULL semantics into an API representation.

---

## `COALESCE` Does Not Modify the Stored Data

This:

```sql
SELECT COALESCE(discount_amount, 0)
FROM orders;
```

does not change the column.

It changes only the returned expression.

The stored value remains NULL.

To persist a value, use an explicit update:

```sql
UPDATE orders
SET discount_amount = 0
WHERE discount_amount IS NULL;
```

Do this only if changing the business meaning from "unknown/absent" to "zero" is correct.

---

## `COALESCE` and Aggregation

Consider:

```sql
SELECT
    SUM(discount_amount)
FROM orders;
```

If all input values are NULL, or there are no input rows, the result can be NULL.

If the API contract requires zero:

```sql
SELECT
    COALESCE(SUM(discount_amount), 0) AS total_discount
FROM orders;
```

This is a common reporting pattern.

---

## `COUNT` and NULL

These expressions differ:

```sql
COUNT(*)
```

```sql
COUNT(phone)
```

`COUNT(*)` counts rows.

`COUNT(phone)` counts rows where `phone` is not NULL.

Example:

```sql
SELECT
    COUNT(*) AS total_customers,
    COUNT(phone) AS customers_with_phone
FROM customers;
```

The number of customers without a phone is:

```sql
SELECT
    COUNT(*) - COUNT(phone) AS customers_without_phone
FROM customers;
```

---

## `COUNT(DISTINCT ...)` and NULL

Consider:

```sql
SELECT COUNT(DISTINCT phone)
FROM customers;
```

The count of distinct non-NULL phone values is returned; NULL does not become a distinct counted value.

If the business needs to report "customers with missing phone numbers" separately, calculate that explicitly.

---

## Aggregates and NULL

Most standard aggregates ignore NULL inputs.

For example:

```sql
SELECT
    AVG(price),
    MIN(price),
    MAX(price),
    SUM(price)
FROM products;
```

NULL prices are not included in these calculations.

This can be useful, but it can also hide data quality problems.

If product prices are required for selling products, a better schema may be:

```sql
price numeric(12, 2) NOT NULL
```

rather than relying on every query to interpret NULL correctly.

---

## Exercise: Aggregate NULL Handling

Write queries to:

1. Count customers with phone numbers.
2. Count customers without phone numbers.
3. Calculate average product price ignoring NULL prices.
4. Return zero when there are no product prices.
5. Calculate total discount treating missing discounts as zero.
6. Count orders with shipping timestamps.
7. Count orders without shipping timestamps.
8. Calculate the percentage of orders with completion timestamps.

---

## `NULLIF`

`NULLIF(a, b)` returns NULL when `a = b`; otherwise it returns `a`.

Example:

```sql
SELECT NULLIF(0, 0);
```

returns NULL.

A common use is avoiding division by zero:

```sql
SELECT
    total_amount / NULLIF(quantity, 0)
FROM ...
```

If quantity is zero, the denominator becomes NULL rather than producing a division-by-zero error.

---

## `NULLIF` for Empty Strings

You may encounter legacy data where empty strings mean "missing":

```sql
NULLIF(phone, '')
```

This converts:

```text
'' → NULL
```

while leaving non-empty values unchanged.

For example:

```sql
SELECT
    NULLIF(TRIM(phone), '') AS normalized_phone
FROM customers;
```

This is useful for querying inconsistent legacy data, but normalization at ingestion is usually preferable.

---

## `COALESCE` and `NULLIF` Together

A useful pattern is:

```sql
COALESCE(NULLIF(TRIM(phone), ''), 'not provided')
```

The processing is:

```text
phone
  ↓
TRIM
  ↓
empty string → NULL
  ↓
COALESCE
  ↓
fallback value
```

Do not use this pattern blindly. If empty string and NULL have distinct business meanings, collapsing them destroys information.

---

## `CASE` and NULL

Explicit NULL handling with `CASE`:

```sql
SELECT
    id,
    CASE
        WHEN phone IS NULL THEN 'missing'
        ELSE 'provided'
    END AS phone_status
FROM customers;
```

This is useful for classification and reporting.

---

## Simple CASE Versus Searched CASE

Simple CASE:

```sql
CASE status
    WHEN 'completed' THEN 'done'
    WHEN 'cancelled' THEN 'failed'
    ELSE 'open'
END
```

Searched CASE:

```sql
CASE
    WHEN completed_at IS NULL THEN 'incomplete'
    WHEN status = 'completed' THEN 'done'
    ELSE 'other'
END
```

For NULL-related conditions, searched `CASE` is generally clearer.

---

## `CASE` Does Not Make `NULL = NULL` True

This is still incorrect:

```sql
CASE
    WHEN phone = NULL THEN 'missing'
    ELSE 'provided'
END
```

Use:

```sql
CASE
    WHEN phone IS NULL THEN 'missing'
    ELSE 'provided'
END
```

---

## Exercise: CASE and NULL

Write queries to:

1. Classify customers as `has_phone` or `missing_phone`.
2. Classify products as `priced` or `unpriced`.
3. Classify orders as `shipped` or `not_shipped`.
4. Classify orders as `completed_timestamp_present` or `missing`.
5. Classify payments as `has_reference` or `missing_reference`.
6. Display a fallback description for products with NULL descriptions.
7. Display a fallback shipping amount when it is NULL.

---

## NULL and `LEFT JOIN`

This is one of the most important areas to practice.

Suppose:

```sql
customers
    ↓ LEFT JOIN
orders
```

A customer without an order still appears in the result.

The order columns become NULL.

For example:

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

For a customer with no order:

```text
customer_id | name | order_id
------------+------+---------
42          | Alex | NULL
```

The NULL represents the absence of a matching order row.

---

## Counting Children Correctly

To count orders per customer:

```sql
SELECT
    c.id,
    c.name,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.name;
```

Use:

```sql
COUNT(o.id)
```

rather than:

```sql
COUNT(*)
```

because the left join creates a preserved customer row even when no order exists.

---

## Filtering a LEFT JOIN

Compare:

```sql
SELECT
    c.id,
    COUNT(o.id)
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
GROUP BY c.id;
```

with:

```sql
SELECT
    c.id,
    COUNT(o.id)
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed'
GROUP BY c.id;
```

The first query removes customers without completed orders.

The second preserves them with:

```text
completed_order_count = 0
```

Predicate placement changes the semantics of an outer join.

---

## Exercise: LEFT JOIN and NULL

Write queries to:

1. Find customers with no orders.
2. Find customers with at least one order.
3. Count orders per customer including zero.
4. Count completed orders per customer including zero.
5. Find customers with no completed orders.
6. Find customers whose latest order is NULL.
7. Find products never included in an order.
8. Find products that have at least one order item.

---

## `NOT IN` and NULL

This is a classic SQL trap.

Suppose:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
)
```

If the subquery contains a NULL, the comparison can produce UNKNOWN for candidate rows, leading to unexpected results.

The issue comes from SQL's three-valued logic.

For exclusion queries, `NOT EXISTS` is usually safer and more explicit.

---

## Prefer `NOT EXISTS` for Anti-Joins

Find customers with no orders:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This expresses the business requirement directly:

> Return customers for whom no matching order exists.

It also avoids the classic NULL trap associated with `NOT IN`.

---

## `IN` Versus `EXISTS`

For inclusion:

```sql
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
)
```

can be valid.

Equivalent business intent can often be expressed as:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = customers.id
)
```

Do not choose solely based on simplistic rules such as "EXISTS is always faster."

The optimizer, data distribution, indexes, and query structure determine actual performance.

---

## Exercise: NOT EXISTS

Write queries to:

1. Find customers without orders.
2. Find customers without completed orders.
3. Find products never ordered.
4. Find products never included in completed orders.
5. Find orders without payments.
6. Find orders without successful payments.
7. Find customers without any successful payment.
8. Find organizations with no orders.

---

## PostgreSQL `IS DISTINCT FROM`

PostgreSQL provides:

```sql
IS DISTINCT FROM
```

and:

```sql
IS NOT DISTINCT FROM
```

These provide NULL-safe comparison semantics.

For example:

```sql
NULL IS DISTINCT FROM NULL
```

is:

```text
FALSE
```

while:

```sql
NULL IS DISTINCT FROM 10
```

is:

```text
TRUE
```

This differs from:

```sql
NULL = NULL
```

which evaluates to UNKNOWN.

---

## When `IS DISTINCT FROM` Is Useful

Suppose you need to detect whether a nullable value actually changed:

```sql
WHERE old_value IS DISTINCT FROM new_value
```

This correctly treats:

```text
NULL → NULL
```

as unchanged.

And:

```text
NULL → value
```

as changed.

This is particularly useful in:

- Synchronization jobs.
- Change detection.
- ETL pipelines.
- Data reconciliation.
- CDC processing.
- Conditional updates.

---

## Exercise: NULL-Safe Comparisons

Write queries to:

1. Find products where `price` differs from a supplied value, including NULL-safe semantics.
2. Detect changed nullable descriptions.
3. Detect orders whose shipping timestamp changed.
4. Compare nullable payment amounts.
5. Find rows where two nullable fields have different values.

---

## NULL and Unique Constraints

A PostgreSQL unique constraint normally allows multiple NULL values because NULL values are not treated as equal for ordinary uniqueness enforcement.

For example:

```sql
CREATE TABLE user_profiles (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id text UNIQUE
);
```

Multiple rows can have:

```text
external_id = NULL
```

This is usually correct because NULL represents absence rather than a duplicated known identifier.

If the business requirement is:

> At most one row may have a missing value

that requires a different constraint design.

---

## Nullable Business Keys

Be careful with nullable identifiers.

For example:

```text
external_customer_id = NULL
```

may be valid before an external system assigns an identifier.

But if the identifier is required after synchronization, the lifecycle should make that transition explicit.

Possible approaches include:

- Nullable during initial creation.
- Backfill from the external system.
- Validate before activation.
- Add stronger constraints after migration.

---

## NULL and Foreign Keys

A nullable foreign key can represent an optional relationship.

For example:

```sql
manager_id bigint REFERENCES employees(id)
```

may be NULL for an employee without a manager.

A NULL foreign key does not violate the foreign-key constraint because there is no referenced value to validate.

If every employee must have a manager, use:

```sql
manager_id bigint NOT NULL REFERENCES employees(id)
```

unless there is a deliberate exception such as a top-level executive.

---

## NULL and CHECK Constraints

A subtle point:

```sql
CHECK (price > 0)
```

does not reject NULL because:

```sql
NULL > 0
```

is UNKNOWN.

A CHECK constraint rejects rows when its expression evaluates to FALSE; UNKNOWN does not fail the check.

Therefore, if NULL is invalid:

```sql
price numeric(12, 2) NOT NULL
    CHECK (price > 0)
```

The `NOT NULL` constraint is required.

---

## Exercise: Constraints and NULL

Determine whether each design correctly enforces its intended rule:

1. Product price must always exist.
2. Product description is optional.
3. Customer phone is optional.
4. External ID may be absent before synchronization.
5. Completed orders must have `completed_at`.
6. Shipped orders must have `shipped_at`.
7. Discount may be absent but must never be negative.
8. Payment amount must always exist for successful payments.

For each case, decide whether `NOT NULL`, `CHECK`, application validation, or a combination is appropriate.

---

## NULL and State Machines

Consider:

```text
status = completed
completed_at = NULL
```

Is that valid?

The answer depends on the state model.

A robust design might enforce:

```text
completed → completed_at required
non-completed → completed_at absent
```

This can be represented with a check constraint:

```sql
ALTER TABLE orders
ADD CONSTRAINT orders_completed_at_consistency
CHECK (
    (status = 'completed' AND completed_at IS NOT NULL)
    OR
    (status <> 'completed' AND completed_at IS NULL)
);
```

Before adding such a constraint to production, verify that existing data already satisfies the invariant or plan a cleanup migration.

---

## NULL and API Design

Database NULL semantics should not leak into API contracts accidentally.

For example, an API may intentionally expose:

```json
{
  "phone": null
}
```

or:

```json
{
  "phone": ""
}
```

or omit the field entirely.

These can represent different meanings.

For PATCH-style APIs, distinguish:

```json
{}
```

from:

```json
{
  "phone": null
}
```

The first may mean:

```text
do not modify phone
```

while the second may mean:

```text
clear phone
```

The database representation should support the intended API semantics.

---

## NULL in Django

Django model fields map database NULL behavior through options such as:

```python
class Customer(models.Model):
    phone = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
```

`null=True` controls database NULL behavior.

`blank=True` controls validation behavior.

They are not identical.

For string fields, Django applications often prefer empty strings rather than database NULL, depending on the model design. The important requirement is consistency across the application and database rather than blindly choosing one representation.

---

## NULL in FastAPI and Pydantic

API schemas can explicitly represent nullable values:

```python
from pydantic import BaseModel


class CustomerResponse(BaseModel):
    id: int
    phone: str | None
```

This makes the API contract explicit.

For update operations, distinguish between:

- Field omitted.
- Field supplied as `null`.
- Field supplied as an empty string.

The service layer should translate those states deliberately.

---

## NULL and SQLAlchemy

SQLAlchemy comparisons should use SQL NULL semantics.

For example:

```python
statement = select(Customer).where(
    Customer.phone.is_(None)
)
```

For non-NULL:

```python
statement = select(Customer).where(
    Customer.phone.is_not(None)
)
```

Do not rely on Python's:

```python
Customer.phone == None
```

style when writing modern SQLAlchemy code; use explicit `.is_(None)` and `.is_not(None)` expressions.

---

## NULL and Search APIs

Suppose an API accepts an optional filter:

```text
?phone=
```

Do not automatically generate:

```sql
WHERE phone = NULL
```

Instead, define the API behavior.

Possible semantics:

```text
phone omitted → do not filter
phone=null     → find NULL values
phone=""       → search empty strings
phone=value    → exact value
```

The query builder should represent those states explicitly.

---

## NULL and Dynamic SQL

Parameterized queries protect values but do not automatically define NULL semantics.

For example:

```sql
WHERE phone = $1
```

with `$1 = NULL` does not become:

```sql
WHERE phone IS NULL
```

It produces UNKNOWN.

If an API supports nullable search parameters, query generation may need separate branches:

```text
parameter absent
    ↓
no predicate

parameter is NULL
    ↓
IS NULL

parameter has value
    ↓
= parameter
```

This is a correctness concern, not merely a syntax issue.

---

## NULL and Indexes

An index can contain NULL values.

Whether a query benefits from an index depends on the predicate, selectivity, statistics, and query plan.

For example:

```sql
CREATE INDEX orders_shipped_at_idx
ON orders (shipped_at);
```

may support certain queries involving:

```sql
WHERE shipped_at IS NULL
```

but the planner decides whether using it is cheaper than another access path.

Do not assume every NULL predicate automatically requires or uses an index.

---

## Partial Indexes and NULL

A partial index can target non-NULL or NULL rows.

For example:

```sql
CREATE INDEX orders_unshipped_idx
ON orders (customer_id)
WHERE shipped_at IS NULL;
```

This can be useful when:

- Unshipped orders are queried frequently.
- The unshipped subset is relatively small.
- The query predicate matches the index predicate.
- The workload justifies maintaining the index.

This is particularly useful for queue-like operational queries.

---

## NULL and Sorting

PostgreSQL supports explicit NULL ordering:

```sql
ORDER BY shipped_at ASC NULLS LAST;
```

or:

```sql
ORDER BY shipped_at DESC NULLS FIRST;
```

Do not rely on implicit ordering when NULL placement is part of business behavior.

For API pagination, deterministic ordering is especially important.

---

## NULL and Pagination

Suppose:

```sql
ORDER BY completed_at DESC
```

contains NULL values.

Keyset pagination must account for NULL ordering explicitly.

A robust pagination design should:

- Define NULL placement.
- Use deterministic tie-breaking.
- Match the ordering index where possible.
- Test transitions between NULL and non-NULL values.

Avoid implementing pagination logic that assumes every ordering column is non-NULL when the schema permits NULL.

---

## NULL and Window Functions

Window functions also have NULL semantics.

For example:

```sql
SELECT
    customer_id,
    completed_at,
    LAG(completed_at) OVER (
        PARTITION BY customer_id
        ORDER BY completed_at
    ) AS previous_completion
FROM orders;
```

If the value itself is NULL, the window function does not magically infer a replacement.

Use explicit expressions when NULL should be normalized or excluded.

---

## NULL and `ORDER BY`

Exercises:

1. Sort customers with missing phone numbers last.
2. Sort products with missing prices first.
3. Sort orders by completion timestamp with NULL values last.
4. Sort payments by payment timestamp with unpaid records first.
5. Create deterministic ordering when timestamps contain duplicates and NULLs.

---

## NULL and Aggregation Joins

Consider:

```sql
SELECT
    c.id,
    SUM(o.total_amount)
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Customers without orders receive:

```text
SUM = NULL
```

If the API expects zero:

```sql
SELECT
    c.id,
    COALESCE(SUM(o.total_amount), 0) AS total_revenue
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This is a common distinction between:

```text
no rows
```

and:

```text
sum of zero-valued rows
```

---

## NULL and Business Semantics

Do not automatically replace every NULL with zero.

Consider:

```text
average_delivery_time = NULL
```

This may mean:

```text
No deliveries have occurred yet.
```

Replacing it with:

```text
0
```

would incorrectly imply:

```text
Delivery time was zero.
```

Similarly:

```text
revenue = NULL
```

may mean:

```text
No observations.
```

while:

```text
revenue = 0
```

means:

```text
Observed revenue was zero.
```

The correct representation depends on the metric contract.

---

## Exercise: Semantic NULL Handling

For each field, decide whether NULL should be converted to zero, empty string, false, or left as NULL:

| Field | Possible meaning |
|---|---|
| Discount amount | No discount / unknown discount |
| Shipping amount | Free shipping / not calculated |
| Phone | Not provided |
| Product price | Not priced yet |
| Completion timestamp | Not completed |
| Refund amount | No refund / not processed |
| Average order value | No orders |
| Last login | Never logged in |

There is no universal correct answer. The correct answer comes from the domain contract.

---

## NULL and Data Quality

NULL-heavy columns can indicate legitimate optionality or poor data quality.

Monitor:

- NULL percentage.
- Unexpected NULL growth.
- NULL values in lifecycle states where values should exist.
- NULL foreign keys.
- Missing timestamps.
- Missing identifiers.
- NULL values introduced by failed migrations.

For example:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE completed_at IS NULL
    ) AS missing_completion_timestamp
FROM orders
WHERE status = 'completed';
```

This can detect an integrity problem if completed orders are expected to have completion timestamps.

---

## NULL and Data Migration

Suppose a new column is introduced:

```sql
ALTER TABLE orders
ADD COLUMN external_reference text;
```

Existing rows initially contain NULL.

A safe migration may be:

```text
add nullable column
        ↓
deploy compatible application
        ↓
backfill existing rows
        ↓
validate
        ↓
enforce NOT NULL if required
```

Do not immediately add `NOT NULL` to a large production table without considering lock behavior, existing data, deployment compatibility, and backfill strategy.

---

## NULL During Backfills

A backfill often uses NULL as a marker:

```text
processed_at IS NULL
```

For example:

```sql
UPDATE orders
SET external_reference = ...
WHERE external_reference IS NULL
  AND id > $1
  AND id <= $2;
```

This can work as a migration strategy, but NULL as a processing marker should not be confused with a legitimate business state.

For large tables, use:

- Bounded batches.
- Idempotent updates.
- Progress tracking.
- Indexes supporting the selection predicate.
- Monitoring.
- Safe retry behavior.

---

## NULL and Concurrency

Consider:

```sql
SELECT *
FROM orders
WHERE external_reference IS NULL
LIMIT 100;
```

A worker may select rows while another worker processes them.

For queue-like processing, PostgreSQL can use:

```sql
SELECT id
FROM orders
WHERE external_reference IS NULL
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

This is useful when NULL represents "not processed yet" and multiple workers need to claim work.

The transaction must remain short, and the update should be idempotent.

---

## NULL and Redis

Redis does not have identical NULL semantics to PostgreSQL.

Do not assume that:

```text
Redis missing key
```

and:

```text
PostgreSQL column = NULL
```

have exactly the same business meaning.

A cache miss can mean:

- Value has never been cached.
- Value was evicted.
- Value expired.
- Source value is NULL.

If the distinction matters, encode it explicitly.

---

## NULL and Kafka

Events may represent nullable fields as:

```json
{
  "phone": null
}
```

or omit the field entirely:

```json
{}
```

These can have different meanings in an event contract.

For event-driven systems, define:

- Field optionality.
- Nullability.
- Omission semantics.
- Backward compatibility.
- Schema evolution behavior.

Do not let database NULL behavior accidentally become an undocumented Kafka contract.

---

## NULL and Microservices

A service may store:

```text
external_customer_id = NULL
```

until another service or external provider assigns an identifier.

Other services should not assume NULL means:

```text
record does not exist
```

The record can exist perfectly well while one attribute is unknown.

Use explicit resource state where necessary rather than overloading nullable fields to represent entire lifecycle states.

---

## Common NULL Mistakes

| Mistake | Why it fails | Better approach |
|---|---|---|
| `column = NULL` | Produces UNKNOWN | Use `IS NULL` |
| `column <> NULL` | Also produces UNKNOWN | Use `IS NOT NULL` |
| Treating NULL as zero | Changes business meaning | Define metric semantics |
| `COUNT(*)` after `LEFT JOIN` | Counts preserved parent row | Count child key |
| `NOT IN` with nullable subquery | UNKNOWN can eliminate matches | Prefer `NOT EXISTS` |
| Assuming CHECK rejects NULL | UNKNOWN does not fail CHECK | Add `NOT NULL` |
| Assuming NULL equals empty string | They represent different values | Normalize deliberately |
| Replacing every NULL with `COALESCE` | Can hide missing data | Apply only where semantics require |
| Using NULL for multiple meanings | Makes queries ambiguous | Define explicit domain states |
| Ignoring NULL in pagination | Can produce unstable ordering | Define NULL ordering |
| Assuming NULL means record absence | Attribute absence differs from row absence | Use explicit existence/state |
| Treating cache miss as database NULL | Cache and source have different semantics | Define cache-state contract |
| Passing NULL blindly to `=` | Does not become `IS NULL` | Generate correct predicate |
| Assuming nullable FK means invalid relationship | NULL can represent optional relationship | Define relationship optionality |

---

## Production Debugging Workflow

When a query involving NULL returns unexpected results:

### Verify the Data

```sql
SELECT
    COUNT(*) AS total,
    COUNT(phone) AS non_null,
    COUNT(*) FILTER (WHERE phone IS NULL) AS null_count
FROM customers;
```

### Inspect Actual Values

```sql
SELECT
    id,
    phone,
    length(phone) AS phone_length
FROM customers
WHERE phone IS NULL
   OR phone = '';
```

### Simplify the Predicate

Test:

```sql
SELECT *
FROM customers
WHERE phone IS NULL;
```

before combining it with multiple conditions.

### Check Joins

Determine whether NULL is caused by:

```text
actual stored NULL
```

or:

```text
no matching row from LEFT JOIN
```

These are not the same thing.

### Check Application Semantics

Verify whether:

- Django converts blank strings.
- FastAPI/Pydantic treats omitted fields differently from NULL.
- SQLAlchemy generated the expected predicate.
- API filters distinguish missing parameters from explicit null.
- Background workers interpret NULL consistently.

---

## Performance Considerations

NULL handling is usually inexpensive compared with the larger query workload, but poor design can still affect performance.

Consider:

- Index selectivity.
- Partial indexes.
- Query frequency.
- Large NULL-heavy datasets.
- Sort operations involving NULL.
- Aggregation over nullable columns.
- Join cardinality.
- Predicate transformations such as `COALESCE(column, ...)`.

For example, transforming an indexed column inside a predicate can change index usability:

```sql
WHERE COALESCE(phone, '') = $1
```

may have different planning characteristics from a direct predicate.

If this is a critical query, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

rather than assuming the index will be used.

---

## Security Considerations

NULL handling can affect authorization.

Suppose:

```sql
WHERE organization_id = $1
```

is used for tenant isolation.

A NULL organization ID does not mean the row should be globally visible.

Similarly, avoid logic such as:

```sql
WHERE organization_id = $1
   OR organization_id IS NULL
```

unless NULL explicitly represents globally accessible data.

Authorization predicates should be based on an explicit security model rather than convenient NULL semantics.

---

## High Availability and Replication

Read replicas can expose another NULL-related consistency issue.

A write may change:

```text
completed_at: NULL → timestamp
```

on the primary.

Immediately querying a replica may still return:

```text
completed_at = NULL
```

because replication is asynchronous.

For workflows requiring read-after-write consistency:

- Read from the primary.
- Use an LSN-aware routing strategy.
- Delay the dependent read.
- Or design the workflow around eventual consistency.

Do not interpret replica staleness as a database NULL correctness problem.

---

## Production Design Checklist

Before introducing or changing nullable fields:

- Define exactly what NULL means.
- Decide whether empty string should also be possible.
- Decide whether zero and NULL are distinct.
- Decide whether false and NULL are distinct.
- Define API serialization semantics.
- Define PATCH/update semantics.
- Define event-schema semantics.
- Decide whether `NOT NULL` is possible.
- Add constraints for lifecycle invariants.
- Review indexes and partial indexes.
- Test joins involving missing related rows.
- Test aggregation behavior.
- Test `NOT EXISTS` and exclusion queries.
- Test pagination with NULL values.
- Test replicas if read-after-write matters.
- Validate existing data before tightening constraints.
- Monitor NULL rates after deployment.

---

## Interview-Level Exercises

Answer these without writing code first:

1. Why does `column = NULL` not work?
2. What are SQL's three logical predicate states?
3. Why does `WHERE` remove UNKNOWN results?
4. What is the difference between `COUNT(*)` and `COUNT(column)`?
5. Why can `NOT IN` behave unexpectedly with NULL?
6. Why is `NOT EXISTS` often preferable for anti-joins?
7. Why does `CHECK (price > 0)` permit NULL?
8. Why might `LEFT JOIN` produce NULL values even when the base table has no NULL?
9. What is the difference between NULL and an empty string?
10. What does `COALESCE` do?
11. What does `NULLIF` do?
12. When should NULL become zero?
13. When should NULL remain NULL?
14. What problem does `IS DISTINCT FROM` solve?
15. How does NULL affect unique constraints in PostgreSQL?
16. How does NULL affect a nullable foreign key?
17. How does NULL affect API PATCH semantics?
18. How can NULL affect keyset pagination?
19. How can NULL be used as a backfill marker?
20. How can multiple workers safely process rows where a nullable marker is NULL?

---

## Senior-Level Challenge

Design a customer reporting query that returns:

- Customer ID.
- Customer name.
- Total orders.
- Completed orders.
- Completed revenue.
- Last completed timestamp.
- Number of orders that have not shipped.

Requirements:

- Customers with no orders must remain visible.
- Customers with no completed orders must receive zero completed orders.
- Customers with no completed revenue must receive zero revenue.
- Missing timestamps must remain semantically distinct from actual timestamps.
- The query must not double-count orders.
- Tenant scope must be enforced.
- Ordering must be deterministic.

Before writing SQL, define:

1. Result grain.
2. Tenant boundary.
3. Meaning of zero versus NULL.
4. Which status is authoritative.
5. Whether `completed_at` or `status` defines completion.
6. How missing shipping timestamps are counted.
7. Whether order items are required.
8. Index requirements.
9. Replica consistency requirements.
10. API representation of NULL and zero values.

A production-quality solution should be judged on semantics first and SQL syntax second.

---

## Practice Method

For every NULL exercise:

1. Identify whether the value is known, absent, or inapplicable.
2. Determine whether NULL has a distinct business meaning.
3. Identify whether the query needs `IS NULL`, `IS NOT NULL`, or a normal comparison.
4. Consider three-valued logic.
5. Check aggregate behavior.
6. Check `LEFT JOIN` behavior.
7. Check for `NOT IN` NULL hazards.
8. Decide whether `COALESCE` changes the intended meaning.
9. Test zero-row and all-NULL cases.
10. Consider API, cache, event, and migration semantics.
11. Validate important queries with execution plans.
12. Consider tenant isolation and authorization.
13. Consider concurrent workers when NULL is used as a processing marker.

The objective is not merely to make NULL disappear from the result. The objective is to preserve the **meaning of absence, uncertainty, and zero** throughout the entire backend system.

---

## Key Takeaways

- **NULL represents absence or unknown state, not zero, false, or an empty string:** its meaning must be defined by the domain before query logic is written.
- **SQL uses three-valued logic:** comparisons involving NULL commonly produce UNKNOWN, which explains many filtering, `NOT IN`, and conditional-expression surprises.
- **Use NULL-aware operators deliberately:** `IS NULL`, `IS NOT NULL`, `COALESCE`, `NULLIF`, and PostgreSQL's `IS DISTINCT FROM` solve different problems and should not be interchangeable.
- **NULL affects the entire backend lifecycle:** joins, aggregates, constraints, pagination, APIs, Django/FastAPI models, Redis caches, Kafka events, migrations, and replicas can all interpret absence differently.
- **Senior SQL design preserves semantics:** do not hide missing data with blanket defaults; define when NULL should remain NULL, when it should become zero, and which invariants the database must enforce.