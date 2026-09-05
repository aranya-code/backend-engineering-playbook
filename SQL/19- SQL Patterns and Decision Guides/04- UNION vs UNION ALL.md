# 04- UNION vs UNION ALL

## Overview

`UNION` and `UNION ALL` combine the result sets of multiple `SELECT` statements into a single result set.

The critical difference is duplicate handling:

- `UNION` combines results and removes duplicate rows.
- `UNION ALL` combines results without removing duplicates.

For example:

```sql
SELECT customer_id
FROM orders
WHERE status = 'completed'

UNION

SELECT customer_id
FROM orders
WHERE status = 'pending';
```

returns each matching `customer_id` once.

With:

```sql
SELECT customer_id
FROM orders
WHERE status = 'completed'

UNION ALL

SELECT customer_id
FROM orders
WHERE status = 'pending';
```

duplicate rows are retained.

This is not merely a performance choice. It is a **data-semantics decision**.

If duplicate rows represent distinct events, `UNION` can silently destroy information. If duplicates are invalid for the intended result, `UNION ALL` can produce incorrect data.

---

## Why Set Operations Exist

SQL queries commonly need to combine independently filtered result sets.

Typical backend requirements include:

- Combining current and archived records.
- Combining multiple event sources.
- Combining different types of users into one feed.
- Combining regional datasets.
- Combining success and failure events.
- Building reporting datasets from different tables.
- Combining partition-like tables when a unified table is not available.
- Returning heterogeneous business entities through a common API representation.

Set operations allow the database to perform this combination without forcing the application to retrieve and merge the data in Python.

The major set operations are:

| Operation | Behavior |
|---|---|
| `UNION` | Combine and remove duplicates |
| `UNION ALL` | Combine and preserve duplicates |
| `INTERSECT` | Return rows present in both results |
| `EXCEPT` | Return rows present in the first result but not the second |

This document focuses on `UNION` and `UNION ALL`.

---

## UNION

`UNION` combines two or more compatible result sets and removes duplicate rows.

```sql
SELECT customer_id
FROM orders
WHERE status = 'completed'

UNION

SELECT customer_id
FROM orders
WHERE status = 'pending';
```

Conceptually:

```text
Result A
  +
Result B
  ↓
Combine
  ↓
Remove duplicate rows
  ↓
Final result
```

If both result sets contain:

```text
1
2
3
```

and:

```text
2
3
4
```

the final result is:

```text
1
2
3
4
```

---

## UNION ALL

`UNION ALL` concatenates result sets and preserves duplicates.

```sql
SELECT customer_id
FROM orders
WHERE status = 'completed'

UNION ALL

SELECT customer_id
FROM orders
WHERE status = 'pending';
```

Given:

```text
Result A
1
2
3

Result B
2
3
4
```

the result is:

```text
1
2
3
2
3
4
```

Every input row remains represented in the output.

---

## The Core Semantic Difference

Consider two event tables:

```sql
CREATE TABLE payment_events (
    event_id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    event_type text NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE refund_events (
    event_id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    event_type text NOT NULL,
    created_at timestamptz NOT NULL
);
```

Suppose a customer has:

```text
payment event → customer 42
refund event  → customer 42
```

This query:

```sql
SELECT customer_id
FROM payment_events

UNION

SELECT customer_id
FROM refund_events;
```

returns:

```text
42
```

That is correct if the requirement is:

> Which customers have either payment or refund activity?

But this query:

```sql
SELECT customer_id
FROM payment_events

UNION ALL

SELECT customer_id
FROM refund_events;
```

returns:

```text
42
42
```

That is correct if the requirement is:

> Return every payment and refund event's customer association.

The choice therefore depends on what a row represents.

---

## UNION vs UNION ALL

| Characteristic | `UNION` | `UNION ALL` |
|---|---|---|
| Combines result sets | Yes | Yes |
| Removes duplicates | Yes | No |
| Preserves every input row | No | Yes |
| Usually more expensive | Yes | Usually |
| Useful for deduplicated sets | Yes | No |
| Useful for event streams | Sometimes | Usually |
| Useful for append-style operations | Sometimes | Usually |
| Can hide duplicate-producing bugs | Yes | No |
| Requires duplicate elimination work | Yes | No |

The performance difference is important, but **correctness comes first**.

---

## Column Compatibility

Each `SELECT` participating in a `UNION` must return the same number of columns.

This is valid:

```sql
SELECT
    id,
    customer_id
FROM orders

UNION ALL

SELECT
    id,
    customer_id
FROM archived_orders;
```

This is invalid because the column counts differ:

```sql
SELECT
    id,
    customer_id
FROM orders

UNION ALL

SELECT
    id
FROM archived_orders;
```

---

## Compatible Data Types

Corresponding columns must have compatible data types.

For example:

```sql
SELECT
    customer_id
FROM orders

UNION ALL

SELECT
    customer_id
FROM archived_orders;
```

is straightforward when both columns are `bigint`.

Explicit casting may be appropriate when source schemas differ:

```sql
SELECT
    customer_id::bigint
FROM orders

UNION ALL

SELECT
    customer_id::bigint
FROM archived_orders;
```

Avoid relying on accidental or implicit type conversions when designing production queries.

Explicit types make intent clearer and reduce surprises during schema evolution.

---

## Column Names

The output column names come from the first `SELECT`.

```sql
SELECT
    customer_id AS id
FROM orders

UNION ALL

SELECT
    customer_id AS customer_identifier
FROM archived_orders;
```

The resulting column is named:

```text
id
```

The alias in the second query does not rename the final output column.

This matters when the result is consumed by:

- Django.
- FastAPI.
- SQLAlchemy.
- Reporting tools.
- ETL pipelines.
- Raw SQL clients.

---

## Ordering UNION Results

An `ORDER BY` applies to the combined result.

Use:

```sql
SELECT
    id,
    created_at
FROM orders

UNION ALL

SELECT
    id,
    created_at
FROM archived_orders

ORDER BY created_at DESC;
```

Do not assume the result order of individual branches is preserved.

If you need a particular ordering for the final dataset, order the final set.

---

## Ordering Individual Branches

Branch-specific ordering generally requires a subquery if the branch itself needs ordering semantics.

For example:

```sql
(
    SELECT
        id,
        created_at
    FROM orders
    ORDER BY created_at DESC
    LIMIT 100
)

UNION ALL

(
    SELECT
        id,
        created_at
    FROM archived_orders
    ORDER BY created_at DESC
    LIMIT 100
)

ORDER BY created_at DESC;
```

This can be useful when each branch should contribute only its own top-N rows before being combined.

Without the branch-level `LIMIT`, ordering individual branches usually does not provide useful final-result semantics.

---

## DISTINCT Semantics of UNION

`UNION` removes duplicate **rows**, not duplicates based on one selected column unless only that column is selected.

For example:

```sql
SELECT
    customer_id,
    status
FROM orders

UNION

SELECT
    customer_id,
    status
FROM archived_orders;
```

These rows are different:

```text
42 | completed
42 | pending
```

because the complete rows differ.

If the requirement is:

> Return unique customers.

then select only the customer identity:

```sql
SELECT customer_id
FROM orders

UNION

SELECT customer_id
FROM archived_orders;
```

The shape of the query determines what constitutes a duplicate.

---

## UNION Is Similar to DISTINCT

Conceptually:

```sql
SELECT customer_id
FROM orders

UNION

SELECT customer_id
FROM archived_orders;
```

is similar to:

```sql
SELECT DISTINCT customer_id
FROM (
    SELECT customer_id
    FROM orders

    UNION ALL

    SELECT customer_id
    FROM archived_orders
) AS combined;
```

The important insight is:

```text
UNION
≈ UNION ALL + duplicate elimination
```

This is useful when reasoning about performance and semantics.

---

## Performance Characteristics

`UNION ALL` can usually append the input result sets directly:

```text
Query A ──┐
          ├── Append ──> Result
Query B ──┘
```

`UNION` needs an additional duplicate-elimination phase:

```text
Query A ──┐
          ├── Combine ──> Duplicate elimination ──> Result
Query B ──┘
```

PostgreSQL may use mechanisms such as:

- Sorting.
- Hash-based duplicate elimination.
- Other optimizer-selected strategies.

The exact plan depends on the query and PostgreSQL version.

---

## Execution Plan Example

Inspect the difference with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id
FROM orders

UNION ALL

SELECT customer_id
FROM archived_orders;
```

and:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id
FROM orders

UNION

SELECT customer_id
FROM archived_orders;
```

The important question is not:

> "Which syntax is faster?"

It is:

> "Does the application require duplicate elimination?"

If not, paying for duplicate elimination is unnecessary work.

---

## Why UNION ALL Is Usually Faster

Suppose two branches produce:

```text
10 million rows
+
10 million rows
```

`UNION ALL` can return the combined 20 million rows without needing to determine whether rows duplicate one another.

`UNION` must establish the distinct result.

That may require substantial:

- CPU.
- Memory.
- Sorting.
- Hashing.
- Temporary disk I/O.

At large scale, this difference can become significant.

However, a `UNION ALL` query may still be expensive because both underlying queries must execute.

---

## Memory and Temporary Storage

Duplicate elimination can consume significant memory.

For large `UNION` queries, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

and monitor:

- Execution time.
- Temporary reads/writes.
- Sort operations.
- Memory usage.
- CPU.
- Disk I/O.

Do not blindly increase `work_mem` to make a query faster.

`work_mem` applies to individual query operations, so increasing it globally can create substantial memory pressure under concurrent workloads.

---

## When UNION Is Appropriate

Use `UNION` when duplicate elimination is part of the business requirement.

Typical examples:

### Unique Customer Population

```sql
SELECT customer_id
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'

UNION

SELECT customer_id
FROM support_tickets
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

Requirement:

> Customers who interacted with either the ordering or support system during the last 30 days.

The same customer appearing in both systems should occur once.

### Combining Multiple Membership Sources

```sql
SELECT user_id
FROM administrators

UNION

SELECT user_id
FROM support_agents;
```

If the result represents:

> Users who have either administrative or support privileges.

duplicates should normally be removed.

---

## When UNION ALL Is Appropriate

Use `UNION ALL` when every source row represents meaningful data that should survive.

### Event Aggregation

```sql
SELECT
    event_id,
    customer_id,
    event_type,
    created_at
FROM payment_events

UNION ALL

SELECT
    event_id,
    customer_id,
    event_type,
    created_at
FROM refund_events;
```

A payment and refund are different events even if they belong to the same customer.

### Current and Historical Tables

Suppose an older system stores historical orders separately:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM orders

UNION ALL

SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM archived_orders;
```

If the tables are guaranteed to represent disjoint records, `UNION ALL` is the natural choice.

---

## Current + Archive Pattern

This pattern appears in legacy systems and retention architectures:

```text
                    ┌──────────────┐
                    │ Current Data │
                    └──────┬───────┘
                           │
                           ├── UNION ALL ──> Unified Query
                           │
                    ┌──────┴───────┐
                    │ Archive Data │
                    └──────────────┘
```

The design is safe only when the two sources do not unintentionally overlap.

If records can exist in both tables, `UNION ALL` can double-count them.

If overlap is possible and duplicate semantics matter, the query must explicitly define which record wins.

---

## Deduplicating Overlapping Current and Archive Data

Suppose records can temporarily exist in both:

```text
orders
archived_orders
```

Blindly using:

```sql
SELECT ...
FROM orders

UNION ALL

SELECT ...
FROM archived_orders;
```

can produce duplicate business records.

One approach is to define source precedence:

```sql
WITH combined AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at,
        1 AS source_priority
    FROM orders

    UNION ALL

    SELECT
        id,
        customer_id,
        total_amount,
        created_at,
        2 AS source_priority
    FROM archived_orders
),
ranked AS (
    SELECT
        combined.*,
        ROW_NUMBER() OVER (
            PARTITION BY id
            ORDER BY source_priority
        ) AS row_number
    FROM combined
)
SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM ranked
WHERE row_number = 1;
```

This is more explicit than blindly using `UNION`.

It defines:

```text
If duplicate IDs exist:
prefer current orders
```

The correct rule depends on the data lifecycle.

---

## UNION vs JOIN

A common mistake is confusing `UNION` with `JOIN`.

`UNION`:

```text
Rows
  ↓
Append vertically
```

`JOIN`:

```text
Columns
  ↓
Combine horizontally based on relationships
```

Example:

```sql
SELECT id FROM customers
UNION ALL
SELECT id FROM suppliers;
```

produces more rows.

Whereas:

```sql
SELECT
    customers.id,
    orders.id
FROM customers
JOIN orders
    ON orders.customer_id = customers.id;
```

combines columns from related rows.

---

## UNION vs JOIN Comparison

| Requirement | Use |
|---|---|
| Stack compatible result sets | `UNION` / `UNION ALL` |
| Combine related tables by key | `JOIN` |
| Remove duplicate combined rows | `UNION` |
| Preserve all input rows | `UNION ALL` |
| Add columns from another table | `JOIN` |
| Merge two event streams | Usually `UNION ALL` |
| Build a unique population from multiple sources | Often `UNION` |

---

## UNION ALL and Event Pipelines

`UNION ALL` is particularly useful for event-oriented systems.

Suppose Kafka-backed services persist different event types:

```text
payment_events
refund_events
shipment_events
```

A reporting query can normalize them:

```sql
SELECT
    event_id,
    customer_id,
    'payment' AS event_category,
    created_at
FROM payment_events

UNION ALL

SELECT
    event_id,
    customer_id,
    'refund' AS event_category,
    created_at
FROM refund_events

UNION ALL

SELECT
    event_id,
    customer_id,
    'shipment' AS event_category,
    created_at
FROM shipment_events;
```

The application receives a unified event-shaped dataset.

This is often better than retrieving each dataset separately and merging large result sets in Python.

---

## Normalizing Different Schemas

Set operations are useful when different source schemas can be mapped to a common contract.

For example:

```sql
SELECT
    id,
    customer_id,
    'order' AS resource_type,
    created_at
FROM orders

UNION ALL

SELECT
    id,
    customer_id,
    'refund' AS resource_type,
    created_at
FROM refunds;
```

The output becomes:

```text
id | customer_id | resource_type | created_at
```

This can support a unified activity feed.

The important requirement is that each branch maps its source data into the same semantic schema.

---

## REST API Example

Suppose:

```text
GET /customers/{id}/activity
```

needs a unified activity feed.

SQL:

```sql
SELECT
    id,
    'order' AS activity_type,
    created_at
FROM orders
WHERE customer_id = $1

UNION ALL

SELECT
    id,
    'refund' AS activity_type,
    created_at
FROM refunds
WHERE customer_id = $1

ORDER BY created_at DESC, id DESC
LIMIT $2;
```

The backend can expose:

```json
[
  {
    "id": 9001,
    "activity_type": "refund",
    "created_at": "2026-09-05T12:10:00Z"
  },
  {
    "id": 8102,
    "activity_type": "order",
    "created_at": "2026-09-05T11:40:00Z"
  }
]
```

This is a good production use of `UNION ALL` because each activity record is meaningful and should not disappear merely because another source contains a similar row.

---

## Pagination Considerations

A unified feed requires careful pagination.

This is preferable:

```sql
SELECT
    id,
    'order' AS activity_type,
    created_at
FROM orders
WHERE customer_id = $1

UNION ALL

SELECT
    id,
    'refund' AS activity_type,
    created_at
FROM refunds
WHERE customer_id = $1

ORDER BY created_at DESC, activity_type, id DESC
LIMIT $2;
```

For high-volume feeds, keyset pagination is generally preferable to large offsets.

The cursor should contain enough information to establish a deterministic position.

For example:

```text
(created_at, activity_type, id)
```

The cursor design must also account for IDs from different source tables.

---

## UNION and Pagination Pitfall

Do not independently paginate each branch and then assume the result is globally ordered.

For example:

```sql
SELECT ...
FROM orders
ORDER BY created_at DESC
LIMIT 50

UNION ALL

SELECT ...
FROM refunds
ORDER BY created_at DESC
LIMIT 50;
```

is not equivalent to:

> Give me the 50 newest activities across both tables.

Each branch can independently contribute 50 rows.

The correct approach depends on the desired semantics and may require branch-level candidate selection followed by a global merge.

---

## Filtering Before UNION

Push selective predicates into each branch when possible.

Prefer:

```sql
SELECT
    id,
    customer_id
FROM orders
WHERE tenant_id = $1
  AND created_at >= $2

UNION ALL

SELECT
    id,
    customer_id
FROM archived_orders
WHERE tenant_id = $1
  AND created_at >= $2;
```

over combining huge datasets and filtering afterward when equivalent predicate pushdown is possible.

This reduces:

- Rows processed.
- Memory pressure.
- Network transfer.
- CPU.
- Temporary work.

The optimizer may perform predicate pushdown itself, but writing semantically clear branch filters can make the intended access scope explicit.

---

## Security and Multi-Tenancy

Every branch of a set operation must enforce the correct security boundary.

For example:

```sql
SELECT
    id,
    customer_id
FROM orders
WHERE tenant_id = $1

UNION ALL

SELECT
    id,
    customer_id
FROM archived_orders
WHERE tenant_id = $1;
```

Do not rely on one branch's tenant filter to protect another branch.

For PostgreSQL Row Level Security, remember that each referenced table has its own policy behavior.

Application-level authorization and database-level controls should be designed consistently.

---

## SQL Injection Considerations

Set operations do not change SQL injection fundamentals.

Use parameters:

```python
cursor.execute(
    """
    SELECT id, customer_id
    FROM orders
    WHERE tenant_id = %s

    UNION ALL

    SELECT id, customer_id
    FROM archived_orders
    WHERE tenant_id = %s
    """,
    [tenant_id, tenant_id],
)
```

Do not construct tenant IDs, dates, or user-supplied filters through string concatenation.

Parameterization protects values, not arbitrary SQL identifiers or syntax.

---

## Schema Evolution

`UNION` queries can become fragile when source schemas evolve independently.

For example:

```text
orders
archived_orders
```

may initially share:

```text
id
customer_id
total_amount
created_at
```

Later, one source gains:

```text
currency
```

The union query does not automatically gain that column.

You must explicitly define the common output contract:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    currency,
    created_at
FROM orders

UNION ALL

SELECT
    id,
    customer_id,
    total_amount,
    NULL::text AS currency,
    created_at
FROM archived_orders;
```

This should be managed carefully during migrations.

---

## Materialized Views and UNION

If a complex union query is executed frequently for reporting, consider whether it should be materialized.

For example:

```sql
CREATE MATERIALIZED VIEW customer_activity AS
SELECT
    id,
    customer_id,
    'order' AS activity_type,
    created_at
FROM orders

UNION ALL

SELECT
    id,
    customer_id,
    'refund' AS activity_type,
    created_at
FROM refunds;
```

A materialized view can reduce repeated computation at query time.

The trade-off is freshness and refresh cost.

Possible architecture:

```text
Transactional tables
        ↓
UNION ALL transformation
        ↓
Materialized view / reporting table
        ↓
API / dashboard
```

Use this when query frequency and analytical workload justify maintaining derived state.

---

## UNION in PostgreSQL Partitioning

Modern PostgreSQL declarative partitioning generally provides a better abstraction than manually maintaining:

```text
table_2025
table_2026
table_2027
```

and querying them with:

```sql
SELECT ...
FROM table_2025

UNION ALL

SELECT ...
FROM table_2026;
```

Partition pruning allows PostgreSQL to exclude irrelevant partitions when predicates permit.

If a system already has independently managed tables, `UNION ALL` may still be useful, but do not mistake manual table unions for a replacement for proper partitioning.

---

## Operational Considerations

Monitor frequently executed union queries for:

- Execution latency.
- Rows processed.
- Rows returned.
- Temporary file usage.
- CPU consumption.
- Buffer reads.
- Query frequency.
- Locking behavior.
- Connection usage.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

is the first diagnostic tool for individual queries.

For recurring production workloads, database statistics and application-level metrics should be correlated.

---

## High Availability and Disaster Recovery

`UNION` and `UNION ALL` do not themselves introduce special HA requirements.

However, their workload characteristics matter.

Large reporting unions can consume resources on the primary database and affect transactional traffic.

Potential architectures include:

```text
                    ┌── Primary PostgreSQL
Application ────────┤
                    │
                    └── Read Replica
                            ↓
                       Reporting UNION
```

For heavier workloads:

```text
PostgreSQL
    ↓
CDC / Kafka
    ↓
Analytical Store
    ↓
Reporting Queries
```

The choice depends on:

- Freshness requirements.
- Data volume.
- Query frequency.
- Operational complexity.
- Cost.
- Recovery requirements.

---

## Reliability Considerations

A `UNION ALL` query over multiple sources can expose partial data if one source has a different availability or replication state.

For example:

```text
orders → primary
refunds → replica
```

can result in inconsistent snapshots if the sources are read from different transactional contexts.

In distributed architectures, define whether the API requires:

- Strong consistency.
- Read-after-write consistency.
- Eventually consistent activity feeds.
- Best-effort reporting.

Do not assume a unified SQL result automatically means the underlying data is globally consistent.

---

## Cost Considerations

The cost of a set operation includes both the branches and the combination step.

For example:

```text
Cost =
    branch A
  + branch B
  + combination / deduplication cost
  + sorting / hashing where required
```

`UNION ALL` generally avoids the duplicate-elimination phase.

`UNION` may be substantially more expensive for large datasets.

Before optimizing, determine whether the duplicate elimination is actually required.

Removing `UNION` merely to improve latency can introduce silent data corruption.

---

## Common Mistakes

### Using UNION When UNION ALL Is Semantically Correct

This introduces unnecessary duplicate elimination.

Example:

```sql
SELECT ...
FROM payment_events

UNION

SELECT ...
FROM refund_events;
```

If every event must remain, this is incorrect.

### Using UNION ALL When Duplicates Are Invalid

This can produce:

- Double-counted revenue.
- Duplicate customers.
- Duplicate notifications.
- Incorrect dashboard metrics.
- Duplicate API results.

### Deduplicating the Wrong Columns

If uniqueness is based on `customer_id`, selecting additional columns changes the duplicate definition.

### Assuming UNION Removes Business Duplicates

`UNION` removes identical result rows.

It does not understand business identity.

Two rows with different timestamps may represent the same business entity and will both remain.

### Using UNION Instead of JOIN

Set operations append rows; joins combine related columns.

### Merging Data in Python Unnecessarily

Fetching large datasets from multiple queries and combining them in application code can increase:

- Network traffic.
- Application memory.
- CPU usage.
- Latency.

When the database can safely perform the operation, SQL is often the better place to combine datasets.

### Ignoring Ordering

The final result has no guaranteed order unless an `ORDER BY` is specified.

### Assuming UNION ALL Is Always Fast

`UNION ALL` avoids deduplication, but the underlying queries may still scan huge tables or perform expensive joins and aggregations.

---

## Production Decision Framework

Use this sequence when choosing between the two:

```text
Do the result sets need to be combined?
            ↓
          Yes
            ↓
Should identical result rows be removed?
        /           \
      Yes            No
       ↓              ↓
    UNION          UNION ALL
       ↓              ↓
Validate that     Confirm every
row-level         source row is
duplicates        meaningful
represent the
same result
```

Then evaluate:

```text
Result semantics
      ↓
Result grain
      ↓
Duplicate definition
      ↓
Data volume
      ↓
Indexes / filtering
      ↓
Execution plan
      ↓
API / reporting workload
      ↓
Operational impact
```

---

## Practical Decision Matrix

| Scenario | Choice | Reason |
|---|---|---|
| Unique customers across two sources | `UNION` | Duplicate customers should appear once |
| Combine payment and refund events | `UNION ALL` | Events are distinct |
| Current + archive with guaranteed disjoint rows | `UNION ALL` | No deduplication needed |
| Current + archive with possible overlap | Depends | Define source precedence or identity |
| Unified activity feed | `UNION ALL` | Preserve every activity |
| Unique users with either role | `UNION` | Same user should appear once |
| Large ETL append | `UNION ALL` | Preserve source records and avoid unnecessary deduplication |
| Deduplicated reporting dataset | `UNION` | Duplicate result rows are unwanted |
| Combining monthly partitions manually | Usually `UNION ALL` | Rows are normally distinct, but declarative partitioning is preferable |
| Performance-sensitive query with guaranteed unique branches | `UNION ALL` | Avoid unnecessary duplicate elimination |

---

## Testing UNION Queries

Set-operation queries should be tested for both correctness and cardinality.

Useful checks include:

### Compare Row Counts

```sql
SELECT COUNT(*)
FROM (
    SELECT id FROM orders
    UNION ALL
    SELECT id FROM archived_orders
) AS combined;
```

### Detect Duplicates

```sql
SELECT
    id,
    COUNT(*)
FROM (
    SELECT id FROM orders
    UNION ALL
    SELECT id FROM archived_orders
) AS combined
GROUP BY id
HAVING COUNT(*) > 1;
```

### Compare Deduplicated Results

```sql
SELECT COUNT(*)
FROM (
    SELECT id FROM orders
    UNION
    SELECT id FROM archived_orders
) AS combined;
```

These checks are particularly useful during archive migrations and schema transitions.

---

## Interview Traps

### "UNION and UNION ALL return the same data."

False.

`UNION` removes duplicate result rows; `UNION ALL` preserves them.

### "UNION is always safer."

Not necessarily.

If duplicates represent distinct events, `UNION` is incorrect because it can remove legitimate rows.

### "UNION removes duplicate IDs."

Only if `id` is the only selected column or the complete selected rows are otherwise identical.

### "UNION ALL is just an optimization."

No.

It has different semantics.

### "UNION automatically understands business identity."

It does not.

Duplicate elimination is based on the complete selected row.

### "ORDER BY belongs to each SELECT."

The final ordering of a combined result is defined by the final `ORDER BY`.

### "UNION is always slow."

No.

The cost depends on input size, duplicate cardinality, query plans, and execution strategy.

### "UNION ALL guarantees no duplicate business entities."

No.

It simply preserves all rows. Business-level uniqueness must come from the data model or explicit query logic.

---

## Senior-Level Design Principles

A senior engineer should not begin with:

> "Which one is faster?"

Start with:

> "What does a row represent?"

Then determine:

1. Whether source rows represent distinct business facts.
2. Whether duplicates are valid.
3. What defines business identity.
4. Whether sources can overlap.
5. Whether deduplication is required.
6. Whether the workload is OLTP or analytical.
7. Whether the result must be globally ordered.
8. Whether the operation belongs in PostgreSQL or an analytical system.

The ideal query is therefore not necessarily the one with the shortest syntax.

It is the query whose semantics match the business model while keeping unnecessary database work out of the critical path.

---

## Key Takeaways

- **`UNION` removes duplicate result rows, while `UNION ALL` preserves every input row:** this is primarily a correctness decision, not merely a performance optimization.
- **Prefer `UNION ALL` when source rows represent distinct events or guaranteed-disjoint datasets:** it avoids unnecessary duplicate-elimination work.
- **Use `UNION` only when duplicate result rows genuinely represent the same desired output:** remember that SQL deduplicates complete result rows, not business entities.
- **For production systems, validate result grain, overlap rules, ordering, tenant boundaries, and execution plans:** large set operations can materially affect CPU, memory, temporary I/O, and API latency.
- **At senior level, treat set operations as part of data architecture:** current/archive models, activity feeds, partitioning, reporting workloads, and analytical systems all influence the correct design.