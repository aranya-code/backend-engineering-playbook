# 05- Duplicate Rows from JOINs

## Overview

Duplicate rows from `JOIN`s are one of the most common SQL correctness problems in production systems.

The important point is that duplicate rows are not necessarily caused by incorrect SQL. A join can legitimately return multiple rows when the underlying relationship is one-to-many or many-to-many.

The problem occurs when the query returns more rows than the intended **result grain**.

For example:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

If a customer has five orders, that customer appears five times.

The SQL is correct if the intended result is:

```text
one row per order
```

but incorrect if the intended result is:

```text
one row per customer
```

The core principle is:

> **Never fix duplicate JOIN results until you understand why the rows are duplicated and what the intended result grain is.**

Using `DISTINCT` without understanding the cause is one of the most common mistakes.

---

## What Duplicate Rows From JOINs Mean

A join combines matching rows.

Suppose:

```text
customers

id
--
1
```

and:

```text
orders

id | customer_id
---+------------
10 | 1
11 | 1
12 | 1
```

Then:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

produces:

```text
customer_id | order_id
------------+---------
1           | 10
1           | 11
1           | 12
```

The customer row is repeated because it has three related orders.

This is expected relational behavior.

The question is whether the application expects:

```text
3 rows
```

or:

```text
1 row
```

---

## Result Grain

The most important concept for diagnosing duplicate rows is **result grain**.

Result grain answers:

> **What does one output row represent?**

Examples:

```text
one row per customer
one row per order
one row per order item
one row per customer/month
one row per product
```

Consider:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

The result grain is:

```text
one row per order
```

not:

```text
one row per customer
```

because each matching order produces a row.

If the API requires one row per customer, the query needs a different shape.

---

## Why JOINs Create Multiple Rows

The number of output rows depends on join cardinality.

Common relationships include:

| Relationship | Typical result |
|---|---|
| One-to-one | One matching row |
| Many-to-one | Multiple left rows can map to one right row |
| One-to-many | One left row can produce multiple output rows |
| Many-to-many | Multiple combinations can be produced |

For example:

```text
Customer
   |
   +---- Order 1
   +---- Order 2
   +---- Order 3
```

Joining customer to orders naturally creates three rows for that customer.

---

## One-to-Many Example

Schema:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text NOT NULL
);

CREATE TABLE orders (
    id bigint PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    total_amount numeric(12, 2) NOT NULL
);
```

Query:

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

If customer `1` has three orders:

```text
1 | customer@example.com | 101
1 | customer@example.com | 102
1 | customer@example.com | 103
```

Nothing is wrong with the join.

The output is at order grain.

---

## When Repeated Parent Columns Are a Problem

Suppose the application wants:

```text
customer_id
email
```

only.

The query:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

may return:

```text
1 | customer@example.com
1 | customer@example.com
1 | customer@example.com
```

The repeated rows may now be undesirable.

This is a signal that the query may be expressing:

```text
customer has orders
```

using a join when the actual requirement is:

```text
customer exists with at least one order
```

---

## Use EXISTS for Existence

If the requirement is:

> Return customers who have at least one order.

prefer:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This expresses the requirement directly.

The query asks:

```text
Does a matching order exist?
```

rather than:

```text
Return every customer-order relationship.
```

The optimizer may transform equivalent forms into similar semi-join plans, so `EXISTS` should not be presented as universally faster.

Its primary advantage here is semantic correctness.

---

## DISTINCT as a Symptom Fix

A common response to duplicate rows is:

```sql
SELECT DISTINCT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

This may produce one row per customer.

But it is important to ask:

> Why did the join produce multiple rows in the first place?

If the requirement is only existence, this is often clearer:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

`DISTINCT` can be valid, but it should not automatically be used to hide incorrect query shape.

---

## When DISTINCT Is Appropriate

`DISTINCT` is legitimate when duplicate elimination is part of the actual requirement.

For example:

```sql
SELECT DISTINCT
    country_code
FROM customers;
```

The requirement is explicitly:

```text
unique country codes
```

Likewise:

```sql
SELECT DISTINCT
    c.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'pending';
```

can be valid if the desired result is a set of unique customers.

However, if the query is performance-sensitive, consider whether `EXISTS` better represents the operation.

---

## DISTINCT Does Not Fix Incorrect Relationships

Suppose:

```sql
JOIN customers AS c
    ON c.email = o.customer_email
```

incorrectly matches multiple customers.

Adding:

```sql
DISTINCT
```

does not fix the relationship.

It only removes identical selected rows.

If different customer IDs are returned:

```text
order 100 → customer 1
order 100 → customer 2
```

then:

```sql
SELECT DISTINCT
    o.id,
    c.id
```

still returns both rows.

The underlying join is still wrong.

---

## JOINing Multiple One-to-Many Relationships

A particularly dangerous pattern is joining multiple independent child relationships.

Suppose:

```text
Customer
 ├── Orders
 └── Support Tickets
```

A customer has:

```text
3 orders
4 tickets
```

Consider:

```sql
SELECT
    c.id,
    o.id AS order_id,
    t.id AS ticket_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id;
```

The intermediate result can contain:

```text
3 × 4 = 12 rows
```

The query does not contain a missing join condition.

The multiplication occurs because two independent one-to-many relationships are being combined.

---

## Why Independent JOINs Multiply Rows

The relational shape is effectively:

```text
Customer
   ↓
3 Orders

Customer
   ↓
4 Tickets
```

When both are joined to the same customer:

```text
Orders × Tickets
```

for that customer.

Conceptually:

```text
Order 1 × Ticket 1
Order 1 × Ticket 2
Order 1 × Ticket 3
Order 1 × Ticket 4
Order 2 × Ticket 1
...
Order 3 × Ticket 4
```

This produces 12 combinations.

---

## Aggregation Double Counting

The most serious consequence is often incorrect aggregates.

Consider:

```sql
SELECT
    c.id,
    SUM(o.total_amount) AS revenue,
    COUNT(t.id) AS ticket_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

If a customer has:

```text
3 orders
4 tickets
```

each order can appear four times.

Therefore:

```sql
SUM(o.total_amount)
```

may be multiplied by four.

Likewise,:

```sql
COUNT(t.id)
```

may count each ticket multiple times.

The query can return plausible-looking numbers that are completely wrong.

---

## Safer Aggregation

Aggregate each independent relationship separately.

```sql
WITH order_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
),
ticket_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    COALESCE(o.revenue, 0) AS revenue,
    COALESCE(t.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_totals AS o
    ON o.customer_id = c.id
LEFT JOIN ticket_totals AS t
    ON t.customer_id = c.id;
```

Now both derived relations have:

```text
one row per customer
```

before they are joined.

The final result therefore remains:

```text
one row per customer
```

---

## COUNT(DISTINCT) as a Targeted Tool

Sometimes distinct counting is exactly what is required.

For example:

```sql
SELECT
    c.id,
    COUNT(DISTINCT o.id) AS order_count,
    COUNT(DISTINCT t.id) AS ticket_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

This can correctly count distinct orders and tickets despite row multiplication.

However, it is not automatically the best solution for every aggregation.

For large datasets, compare:

```text
COUNT(DISTINCT ...)
```

with:

```text
pre-aggregation
```

based on actual execution plans and workload.

---

## One-to-One Relationships

A join is less likely to duplicate rows when the relationship is truly one-to-one.

Suppose:

```sql
CREATE TABLE customer_profiles (
    customer_id bigint PRIMARY KEY
        REFERENCES customers(id),
    profile_data jsonb NOT NULL
);
```

The primary key guarantees at most one profile per customer.

Then:

```sql
SELECT
    c.id,
    cp.profile_data
FROM customers AS c
LEFT JOIN customer_profiles AS cp
    ON cp.customer_id = c.id;
```

does not multiply customer rows through multiple profiles.

Database constraints therefore help make join cardinality predictable.

---

## Missing Uniqueness Constraints

Suppose application logic assumes:

```text
one customer → one profile
```

but the database allows:

```text
customer_id = 1
profile A
profile B
```

Then:

```sql
JOIN customer_profiles AS cp
    ON cp.customer_id = c.id
```

creates multiple rows.

If the relationship is supposed to be one-to-one, encode it:

```sql
ALTER TABLE customer_profiles
ADD CONSTRAINT customer_profiles_customer_unique
UNIQUE (customer_id);
```

Constraints turn application assumptions into database guarantees.

---

## Duplicate Rows From Non-Unique JOIN Keys

Consider:

```sql
JOIN customers AS c
    ON c.email = o.customer_email
```

If email is not unique, an order can match multiple customers.

Diagnose this with:

```sql
SELECT
    email,
    COUNT(*)
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;
```

If the business model requires unique email addresses, use a unique constraint rather than relying on application assumptions.

---

## Composite Key Duplication

Suppose:

```text
tenant_id + external_id
```

defines unique identity.

The correct join is:

```sql
ON a.tenant_id = b.tenant_id
AND a.external_id = b.external_id
```

An incomplete join:

```sql
ON a.external_id = b.external_id
```

can produce multiple matches.

This can cause:

- Duplicate rows.
- Cross-tenant data access.
- Incorrect updates.
- Incorrect aggregates.

Composite relationships must use the complete logical key.

---

## Many-to-Many Relationships

Many-to-many relationships naturally produce multiple rows.

Suppose:

```text
students
courses
student_courses
```

A student can enroll in many courses and a course can contain many students.

Query:

```sql
SELECT
    s.id AS student_id,
    c.id AS course_id
FROM students AS s
JOIN student_courses AS sc
    ON sc.student_id = s.id
JOIN courses AS c
    ON c.id = sc.course_id;
```

The result grain is:

```text
one row per student-course relationship
```

Trying to force this into one row per student without defining the desired representation is a query-design problem, not a duplicate-row problem.

---

## Aggregating Many-to-Many Data

If the requirement is:

```text
one row per student
```

with the number of courses:

```sql
SELECT
    s.id,
    COUNT(sc.course_id) AS course_count
FROM students AS s
LEFT JOIN student_courses AS sc
    ON sc.student_id = s.id
GROUP BY s.id;
```

The join creates multiple rows internally, but aggregation deliberately converts the result back to:

```text
one row per student
```

This is an intentional grain transformation.

---

## Window Functions Instead of GROUP BY

Sometimes the requirement is:

```text
retain detail rows
+
show an aggregate
```

A window function can be appropriate:

```sql
SELECT
    o.id,
    o.customer_id,
    o.total_amount,
    SUM(o.total_amount) OVER (
        PARTITION BY o.customer_id
    ) AS customer_revenue
FROM orders AS o;
```

The result remains:

```text
one row per order
```

rather than collapsing to one row per customer.

This is important when diagnosing "duplicates" because sometimes repeated parent information is intentional.

---

## Latest Related Row

Suppose each customer has many orders, but the API needs only the latest order.

A direct join:

```sql
SELECT
    c.id,
    o.id AS order_id,
    o.created_at
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

returns every order.

Instead, rank the child rows:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM (
    SELECT
        o.id,
        o.customer_id,
        o.created_at,
        ROW_NUMBER() OVER (
            PARTITION BY o.customer_id
            ORDER BY o.created_at DESC, o.id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn = 1;
```

Then join the single selected order per customer.

The key is to reduce the child relation to the required cardinality before joining.

---

## LEFT JOIN and Duplicate Children

Consider:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

Customers without orders appear once with:

```text
o.id = NULL
```

Customers with multiple orders appear multiple times.

This is correct `LEFT JOIN` behavior.

Do not interpret every repeated parent row as an error.

---

## LEFT JOIN With Filters

Suppose the requirement is:

> Return every customer and their pending orders.

Use:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'pending';
```

Moving the condition into `WHERE`:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'pending';
```

removes customers without matching pending orders.

This does not directly create duplicates, but misunderstanding outer-join semantics often leads developers to add additional joins or `DISTINCT` to compensate for incorrect query shape.

---

## Detecting Duplicate Entities

If the expected result is:

```text
one row per order
```

test:

```sql
SELECT
    COUNT(*) AS result_rows,
    COUNT(DISTINCT order_id) AS distinct_orders
FROM (
    SELECT
        o.id AS order_id
    FROM orders AS o
    JOIN customers AS c
        ON c.id = o.customer_id
) AS result;
```

If:

```text
result_rows > distinct_orders
```

the query is producing duplicate order IDs.

Whether that is a problem depends on the intended grain.

---

## Finding Which Rows Are Duplicated

Use:

```sql
SELECT
    o.id AS order_id,
    COUNT(*) AS occurrences
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
GROUP BY o.id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;
```

This identifies orders appearing multiple times.

For a complex query, perform the same check after each join to locate the point where cardinality changes.

---

## Incremental Join Debugging

When a query returns too many rows, do not immediately add `DISTINCT`.

Instead:

```text
Base table
    ↓
Count
    ↓
First JOIN
    ↓
Count
    ↓
Second JOIN
    ↓
Count
    ↓
Aggregation
```

Example:

```sql
SELECT COUNT(*)
FROM customers;
```

Then:

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Then:

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN payments AS p
    ON p.order_id = o.id;
```

The join where the count changes unexpectedly is a strong debugging signal.

---

## EXPLAIN and Cardinality

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Inspect:

- Estimated rows.
- Actual rows.
- Join conditions.
- Join algorithm.
- Rows removed by filters.
- Buffer usage.
- Sort/hash operations.
- Execution time.

A large estimated-vs-actual difference can indicate:

- Stale statistics.
- Data skew.
- Correlated columns.
- Incorrect cardinality assumptions.
- Query-shape problems.

---

## JOIN Algorithm Is Not the Problem

PostgreSQL may use:

```text
Nested Loop
Hash Join
Merge Join
```

A `Nested Loop` does not mean duplicate rows are being generated incorrectly.

Likewise, a `Hash Join` does not guarantee correct cardinality.

The join algorithm is an execution detail.

The logical relationship determines the result.

Always separate:

```text
correctness
```

from:

```text
execution strategy
```

---

## Performance Impact of Duplicate Rows

Unintended row multiplication can increase:

- CPU usage.
- Memory consumption.
- Hash table size.
- Sort size.
- Temporary disk usage.
- Network traffic.
- Python object creation.
- JSON serialization.
- Redis payload size.
- Kafka event volume.

For example:

```text
Expected:
10,000 rows

Actual:
10,000,000 rows
```

Even if the final query applies:

```sql
DISTINCT
```

the database may need to process a much larger intermediate relation before eliminating duplicates.

---

## DISTINCT and Sort/Hash Cost

Depending on the query and PostgreSQL plan, duplicate elimination can require significant work.

Possible operations include:

```text
Sort
    ↓
Unique
```

or:

```text
HashAggregate
```

Large datasets can cause memory pressure or temporary-file spills.

Therefore:

```sql
SELECT DISTINCT ...
```

should not automatically be considered a cheap cleanup operation.

---

## Application Memory

Suppose a FastAPI endpoint executes a query that accidentally returns 500,000 rows instead of 5,000.

The database may successfully produce the result, but the application can then experience:

```text
PostgreSQL
    ↓
500k rows
    ↓
Python driver
    ↓
ORM/Python objects
    ↓
Pydantic serialization
    ↓
JSON response
```

This can cause:

- High memory usage.
- Garbage collection pressure.
- Long response times.
- Worker termination.
- Connection pool exhaustion.

Fix the query cardinality before trying to optimize application serialization.

---

## Django ORM

Django can produce duplicate rows through relationship traversal.

For example:

```python
customers = Customer.objects.filter(
    orders__status="pending"
)
```

A customer with multiple pending orders can appear multiple times in the SQL result.

If the requirement is unique customers:

```python
customers = (
    Customer.objects
    .filter(orders__status="pending")
    .distinct()
)
```

may be appropriate.

However, if the requirement is simply:

```text
customer has a pending order
```

understanding the generated SQL and considering an existence-oriented query can produce clearer semantics.

For complex querysets, inspect the SQL:

```python
print(customers.query)
```

Use this for development/debugging rather than as application logging.

---

## Django Aggregation

Be careful when annotating multiple independent relationships.

For example:

```python
Customer.objects.annotate(
    order_count=Count("orders"),
    ticket_count=Count("support_tickets"),
)
```

can involve joins that multiply rows before aggregation.

Sometimes:

```python
Count("orders", distinct=True)
```

is appropriate.

But `distinct=True` should not be treated as a universal fix. For complex metrics, separate subqueries or pre-aggregation may better represent the intended semantics.

---

## SQLAlchemy

SQLAlchemy can explicitly represent joins:

```python
stmt = (
    select(Order.id, Customer.email)
    .join(Customer, Customer.id == Order.customer_id)
)
```

When querying ORM entities with one-to-many relationships, the result may contain repeated parent entities at the SQL level.

Understand whether the API expects:

```text
rows
```

or:

```text
unique entities
```

and shape the query accordingly.

For complex ORM queries, inspect generated SQL and execution plans.

---

## REST API Design

Suppose an endpoint requires:

```text
GET /customers?has_orders=true
```

Do not implement the semantics as:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

and then rely on application code to deduplicate customers.

Prefer:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The database query now directly matches the API's semantic requirement.

---

## gRPC and DTOs

The same principle applies to gRPC services.

If a protobuf response expects:

```text
Customer
    id
    email
```

then returning multiple copies of the same customer because of child joins is usually a query-shape problem.

If the service actually needs:

```text
Customer
    +
Orders[]
```

then the application should deliberately model that one-to-many relationship rather than treating repeated SQL rows as unexpected duplicates.

---

## Redis Caching

Duplicate rows can also pollute caches.

For example:

```text
Database
   ↓
duplicate rows
   ↓
Python serialization
   ↓
Redis
```

This creates larger cache values and may cause incorrect cache semantics.

If a cached object is intended to represent:

```text
one customer
```

ensure the query produces or is transformed into that intended representation.

---

## Kafka and Event Generation

A join used to create events can accidentally duplicate messages.

Example:

```sql
SELECT
    o.id,
    c.segment
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id;
```

If the customer relationship is not actually one-to-one, the same order can appear multiple times.

A downstream system may receive:

```text
order.created
order.created
order.created
```

for one logical order.

Idempotent consumers are useful, but duplicate event production should still be fixed at the source.

---

## Security Considerations

Duplicate rows can become a security problem when they result from incorrect tenant joins.

Suppose:

```text
tenant_id + external_id
```

defines identity.

Incorrect:

```sql
JOIN customers AS c
    ON c.external_id = o.external_id
```

Correct:

```sql
JOIN customers AS c
    ON c.tenant_id = o.tenant_id
   AND c.external_id = o.external_id
```

An incomplete join can match another tenant's row.

This can cause:

- Cross-tenant data exposure.
- Incorrect authorization.
- Incorrect billing.
- Incorrect audit records.

For sensitive multi-tenant systems, combine correct join predicates with appropriate database-level authorization controls.

---

## Reliability and Data Integrity

Duplicate rows can silently corrupt business metrics.

Examples:

```text
Revenue report
    ↓
duplicate orders
    ↓
inflated revenue
```

```text
Usage report
    ↓
duplicate events
    ↓
inflated usage
```

```text
Billing query
    ↓
duplicate line items
    ↓
incorrect invoice
```

A query that executes successfully is not necessarily a correct query.

---

## High Availability and Operational Impact

Unexpected row multiplication can create production pressure on:

- Primary databases.
- Read replicas.
- Connection pools.
- Application workers.
- Caches.
- Message brokers.

A reporting query with incorrect joins can consume enough database resources to affect unrelated transactional workloads.

For production analytics, consider:

- Read replicas.
- Dedicated reporting infrastructure.
- Pre-aggregated data.
- Materialized views.
- Appropriate workload isolation.

These do not replace correct query logic.

---

## Monitoring

Monitor high-value queries for:

- Execution duration.
- Rows returned.
- Rows affected.
- Buffer usage.
- Temporary file usage.
- CPU.
- Query frequency.

For APIs, monitor:

```text
endpoint
response rows
response size
latency
database time
```

Unexpected changes in result cardinality can indicate:

- Data growth.
- Schema changes.
- New relationships.
- Incorrect joins.
- Missing constraints.

---

## Production Query Review

Before approving a query with multiple joins, ask:

### Result Grain

```text
What does one output row represent?
```

### Cardinality

```text
How many rows can each joined table contribute?
```

### Relationship

```text
Is the join key correct?
```

### Uniqueness

```text
Is the joined column unique?
```

### Multiplication

```text
Can two one-to-many relationships multiply each other?
```

### Aggregation

```text
Are SUM/COUNT/AVG values calculated at the correct grain?
```

### Security

```text
Are tenant and ownership boundaries preserved?
```

### Performance

```text
What does EXPLAIN show?
```

---

## Common Mistakes

### Adding DISTINCT Immediately

```sql
SELECT DISTINCT ...
```

may hide the symptom without fixing the query shape.

### Assuming Repeated Parent Rows Are Always Wrong

One-to-many joins naturally repeat parent columns.

### Joining Multiple One-to-Many Relations

This can produce multiplicative intermediate rows.

### Joining on Non-Unique Columns

Email, names, external identifiers, or incomplete composite keys can produce multiple matches.

### Counting Without Understanding Grain

```sql
COUNT(*)
```

may count join combinations rather than business entities.

### Summing After Multiplicative JOINs

```sql
SUM(order_amount)
```

can be inflated.

### Trusting ORM Abstractions

The ORM may generate joins with the same cardinality behavior as handwritten SQL.

### Using LIMIT to Hide Duplicates

`LIMIT` restricts output but does not make the underlying result correct.

### Using DISTINCT for Authorization

Deduplicating rows does not repair an incorrect tenant or ownership join.

### Assuming Good Performance Means Correctness

A query can be extremely fast and still return the wrong data.

---

## Production Debugging Workflow

When duplicate rows are reported:

1. Define the expected result grain.
2. Identify the entity that should be unique.
3. Count total rows.
4. Count distinct entity IDs.
5. Inspect each join relationship.
6. Check uniqueness constraints.
7. Add joins incrementally.
8. Identify the first cardinality explosion.
9. Check independent one-to-many relationships.
10. Validate aggregates independently.
11. Inspect the execution plan.
12. Add a regression test.

A useful diagnostic query is:

```sql
SELECT
    COUNT(*) AS rows_returned,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM (
    SELECT
        c.id AS customer_id
    FROM customers AS c
    JOIN orders AS o
        ON o.customer_id = c.id
) AS result;
```

If the expected grain is one row per customer and:

```text
rows_returned > unique_customers
```

investigate why.

---

## Choosing the Correct Technique

| Requirement | Preferred approach |
|---|---|
| Need one row per parent plus child detail | Normal `JOIN` |
| Need only to know whether a child exists | `EXISTS` |
| Need only parents without children | `NOT EXISTS` |
| Need one aggregate per parent | `GROUP BY` / pre-aggregation |
| Need multiple independent aggregates | Aggregate each relation separately |
| Need latest child | `ROW_NUMBER()` or another deterministic top-1 pattern |
| Need unique values | `DISTINCT` |
| Need every combination intentionally | `CROSS JOIN` |
| Need detail rows plus aggregate | Window function |

The technique should follow the required result grain.

---

## Senior Mental Model

A senior engineer does not ask:

> "How do I remove duplicate rows?"

The better question is:

> **"Why does the relational operation produce multiple rows, and what should one output row represent?"**

Use this reasoning model:

```text
Expected result grain
        ↓
Relationship cardinality
        ↓
Join predicate
        ↓
Intermediate row count
        ↓
Aggregation / projection
        ↓
Final result grain
```

If the query changes grain intentionally, make that transformation explicit.

If it changes grain unintentionally, fix the query rather than masking the result.

---

## Practical Rule

Before using `DISTINCT`, identify:

```text
What entity should be unique?
Why is it repeated?
Which JOIN introduced the repetition?
Is the repetition intentional?
```

Then choose the appropriate solution:

```text
Need existence?
    → EXISTS

Need aggregation?
    → GROUP BY / pre-aggregate

Need one child?
    → ROW_NUMBER() / deterministic top-1

Need unique values?
    → DISTINCT

Need child details?
    → Keep the one-to-many rows

Multiple independent one-to-many relations?
    → Aggregate separately
```

The goal is not to eliminate every repeated value.

The goal is to ensure that the query's **result grain matches the business requirement**.

---

## Key Takeaways

- **Duplicate rows from JOINs are often a cardinality issue, not a SQL syntax error; always define the intended result grain before deciding whether repetition is actually wrong.**
- **One-to-many and many-to-many joins naturally produce multiple rows, while independent one-to-many joins can multiply each other and corrupt aggregates.**
- **Do not use `DISTINCT` as the default fix; use `EXISTS` for existence checks, pre-aggregate independent relationships, and use deterministic ranking when only one related row is required.**
- **Enforce uniqueness assumptions with primary keys and unique constraints, and use complete composite keys and tenant predicates when required for correctness and isolation.**
- **Validate duplicate-row problems with distinct-entity counts, incremental join analysis, expected cardinality, and `EXPLAIN (ANALYZE, BUFFERS)` rather than relying only on the final result.**