# 10- View vs CTE

## Overview

SQL `VIEW`s and Common Table Expressions (`CTE`s) both allow complex SQL logic to be expressed in named, composable query structures, but they solve different engineering problems.

A **CTE** is primarily a query-local construct:

```sql
WITH recent_orders AS (
    SELECT ...
)
SELECT ...
FROM recent_orders;
```

A **view** is a persistent database object:

```sql
CREATE VIEW recent_orders AS
SELECT ...;
```

The practical distinction is:

> A CTE organizes logic for one SQL statement; a view creates a reusable database-level interface.

This distinction affects:

- Reusability.
- Ownership.
- Security.
- Query optimization.
- Schema evolution.
- Deployment.
- Permissions.
- Application coupling.
- Performance.
- Operational maintenance.

For PostgreSQL-backed backend systems, choosing between a view and a CTE should be based on whether the logic is **query-local composition** or a **stable reusable database abstraction**.

---

## CTE

A Common Table Expression is a named query expression defined with `WITH`.

Example:

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE created_at >= now() - interval '30 days'
)
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM recent_orders
GROUP BY customer_id;
```

The CTE exists only for the duration of that statement.

It is not a persistent database object.

---

## Why CTEs Exist

CTEs primarily improve query composition.

They are useful when a query naturally has multiple logical stages:

```text
Base data
   ↓
Filter
   ↓
Rank
   ↓
Aggregate
   ↓
Final result
```

For example:

```sql
WITH ranked_orders AS (
    SELECT
        customer_id,
        id,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
)
SELECT
    customer_id,
    id AS latest_order_id,
    total_amount
FROM ranked_orders
WHERE rn = 1;
```

The CTE makes the intermediate relational operation explicit.

---

## CTE Characteristics

| Property | CTE |
|---|---|
| Lifetime | One statement |
| Persistent object | No |
| Reusable by other queries | No |
| Defined with | `WITH` |
| Has database object permissions | No |
| Useful for query composition | Yes |
| Can be recursive | Yes |
| Can contain data-modifying statements in PostgreSQL | Yes |
| Can be materialized/inlined depending on PostgreSQL and query shape | Yes |

---

## View

A view is a named database object containing a query definition.

Example:

```sql
CREATE VIEW customer_order_summary AS
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue
FROM orders
GROUP BY customer_id;
```

Applications can then query it:

```sql
SELECT *
FROM customer_order_summary
WHERE customer_id = $1;
```

The view persists until it is altered or dropped.

---

## Why Views Exist

Views provide a reusable database-level interface over underlying tables.

They can:

- Hide complex joins.
- Standardize commonly used queries.
- Restrict exposed columns.
- Provide a stable logical interface.
- Encapsulate database relationships.
- Simplify reporting queries.
- Support database-level access control.

A view can therefore act somewhat like a database API:

```text
Underlying tables
       ↓
      View
       ↓
Applications / reports / services
```

---

## View Characteristics

| Property | View |
|---|---|
| Lifetime | Persistent |
| Persistent database object | Yes |
| Reusable by multiple statements | Yes |
| Defined with | `CREATE VIEW` |
| Can have permissions | Yes |
| Automatically stores result data | No |
| Usually executes underlying query when referenced | Yes |
| Can encapsulate joins and business-facing projections | Yes |
| Can be replaced/altered through migrations | Yes |

A normal view should not be confused with a materialized view.

---

## Normal View vs Materialized View

A normal view stores the query definition, not a materialized copy of its result.

```text
Normal VIEW

Application
    ↓
VIEW
    ↓
Underlying tables
    ↓
Query execution
```

A materialized view stores the query result:

```text
Underlying tables
    ↓
Materialized VIEW
    ↓
Stored result
    ↓
Application
```

Materialized views have different refresh, freshness, indexing, and operational considerations.

Use a materialized view when the workload benefits from persisted derived results rather than simply reusable query logic.

---

## CTE vs View: Core Difference

The simplest comparison is:

```text
CTE
----
One query
    ↓
WITH named_query
    ↓
Final result

VIEW
----
Database object
    ↓
Reusable query interface
    ↓
Many queries
```

A CTE answers:

> How should I structure this query?

A view answers:

> What reusable database-level result or interface should multiple consumers use?

---

## Same Logic Implemented Both Ways

Suppose the system frequently needs active customers.

A CTE could be:

```sql
WITH active_customers AS (
    SELECT
        id,
        email,
        created_at
    FROM customers
    WHERE status = 'active'
)
SELECT *
FROM active_customers
WHERE created_at >= $1;
```

A view could be:

```sql
CREATE VIEW active_customers AS
SELECT
    id,
    email,
    created_at
FROM customers
WHERE status = 'active';
```

Then:

```sql
SELECT *
FROM active_customers
WHERE created_at >= $1;
```

The SQL may look similar, but the lifecycle is different.

The CTE belongs to one query.

The view becomes part of the database schema.

---

## When to Use a CTE

Use a CTE when:

- The logic is specific to one query.
- The query has multiple logical stages.
- You need to reference an intermediate result.
- You need recursive traversal.
- You need to improve complex query readability.
- You want to separate window-function computation from filtering.
- You need PostgreSQL data-modifying CTE behavior.

Example:

```sql
WITH ranked_products AS (
    SELECT
        id,
        category_id,
        price,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY price DESC, id
        ) AS rn
    FROM products
    WHERE active = true
)
SELECT
    id,
    category_id,
    price
FROM ranked_products
WHERE rn <= 5;
```

Creating a permanent view for this query would often be unnecessary if the logic is only needed by one operation.

---

## When to Use a View

Use a view when:

- Multiple queries need the same relational definition.
- Multiple services or reporting consumers need a common interface.
- You want to expose selected columns instead of the entire underlying table.
- Complex joins should be standardized.
- Database permissions should apply to a reusable object.
- You want to isolate consumers from underlying table relationships.

Example:

```sql
CREATE VIEW customer_account_status AS
SELECT
    c.id AS customer_id,
    c.email,
    c.status,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email,
    c.status;
```

Multiple consumers can now query the same logical representation.

---

## Views as Database APIs

A mature backend system can treat selected views as database-level interfaces.

```text
                 ┌─────────────────┐
                 │   Base Tables   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │      Views      │
                 │ stable logical  │
                 │    interface    │
                 └───────┬─────────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Django      FastAPI     Reporting
```

This can reduce coupling to physical table structure.

For example, an application might consume:

```sql
SELECT
    customer_id,
    account_status,
    last_order_at
FROM customer_account_status
WHERE customer_id = $1;
```

The view can hide the underlying joins.

However, this abstraction should be intentional. Views can also create hidden database coupling if poorly governed.

---

## Query Composition With CTEs

CTEs are particularly useful for multi-stage SQL.

Example:

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE created_at >= now() - interval '90 days'
),
ranked_orders AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM recent_orders
)
SELECT
    customer_id,
    id AS latest_order_id,
    total_amount
FROM ranked_orders
WHERE rn = 1;
```

The query reads as a pipeline:

```text
recent_orders
      ↓
ranked_orders
      ↓
latest order per customer
```

This is one of the strongest reasons to use CTEs.

---

## CTE Materialization in PostgreSQL

A common misconception is:

> Every CTE creates a temporary materialized table.

That is not generally true in modern PostgreSQL.

PostgreSQL can inline eligible CTEs into the surrounding query.

You can explicitly influence this behavior:

```sql
WITH recent_orders AS MATERIALIZED (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= now() - interval '30 days'
)
SELECT *
FROM recent_orders;
```

Or:

```sql
WITH recent_orders AS NOT MATERIALIZED (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= now() - interval '30 days'
)
SELECT *
FROM recent_orders;
```

These options should be used based on query behavior, not as default style.

Inspect the execution plan before making materialization decisions.

---

## Why Materialization Matters

Materialization can be useful when an intermediate result is expensive to compute and reused multiple times within the statement.

But forced materialization can also prevent useful optimization such as pushing outer predicates into the underlying query.

Therefore:

```text
MATERIALIZED
```

is not synonymous with:

```text
faster
```

and:

```text
NOT MATERIALIZED
```

is not synonymous with:

```text
faster
```

The correct choice depends on the query and workload.

---

## View Performance

A normal view does not automatically make an expensive query cheap.

Consider:

```sql
CREATE VIEW expensive_customer_report AS
SELECT
    ...
FROM orders
JOIN customers ...
JOIN payments ...
GROUP BY ...;
```

Then:

```sql
SELECT *
FROM expensive_customer_report
WHERE customer_id = $1;
```

The optimizer can often optimize through the view definition, but the underlying relational work still matters.

A view is an abstraction mechanism, not a cache.

If the underlying query is expensive, the view can still be expensive.

---

## View Predicate Pushdown

PostgreSQL can often push predicates from a query using a view into the underlying relation when the query structure permits it.

For example:

```sql
SELECT *
FROM active_customers
WHERE id = $1;
```

may be optimized similarly to applying the condition directly to the underlying table.

However, complex constructs can restrict optimization.

Examples that may affect optimization include:

- Aggregation.
- Window functions.
- Set operations.
- Security barriers.
- Complex expressions.

Never assume that a view boundary always prevents optimization or always preserves it. Use `EXPLAIN`.

---

## View Security

Views can provide a controlled projection of data.

Suppose the base table contains:

```text
id
email
password_hash
internal_notes
status
```

A view can expose only appropriate fields:

```sql
CREATE VIEW public_customer_profile AS
SELECT
    id,
    email,
    status
FROM customers;
```

The application can be granted access to the view rather than the underlying table, depending on the overall privilege model.

This supports least-privilege designs.

However, a view should not be treated as an automatic security boundary in every situation. Understand ownership, privileges, row-level security, security-barrier behavior, and the database roles involved.

---

## Security Barrier Views

PostgreSQL supports security-barrier views:

```sql
CREATE VIEW customer_public_data
WITH (security_barrier = true)
AS
SELECT
    id,
    email,
    status
FROM customers
WHERE status = 'active';
```

Security-barrier behavior can be relevant when a view is part of a security policy and user-supplied predicates must not be able to interfere with the intended filtering semantics through leaky functions.

There can be performance trade-offs.

Do not use `security_barrier` simply because a view contains sensitive information. Design the complete privilege and row-security model first.

---

## Views and Row Level Security

Views and PostgreSQL Row Level Security solve different layers of the security problem.

```text
View
 ↓
What columns/relationships are exposed

RLS
 ↓
Which rows a role can access
```

For multi-tenant systems, RLS can enforce tenant boundaries at the database level.

A view can then expose a convenient representation of those rows.

Do not assume that creating a view automatically implements tenant isolation.

---

## Views and Application Permissions

A least-privilege architecture can look like:

```text
Application role
      |
      +── SELECT on approved views
      |
      └── No direct access to sensitive base tables
```

For example:

```sql
REVOKE ALL ON customers FROM app_readonly;

GRANT SELECT
ON public_customer_profile
TO app_readonly;
```

The exact privilege model should account for ownership, role membership, RLS, sequences, functions, and other database objects.

A security design should be tested using the actual application role.

---

## View Lifecycle and Schema Evolution

A view creates schema-level coupling.

Suppose:

```sql
CREATE VIEW customer_summary AS
SELECT
    id,
    email,
    status
FROM customers;
```

Changing the underlying schema can affect the view.

Before a migration:

```text
Application
    ↓
View
    ↓
Base table
```

the deployment must consider all dependencies.

A safe migration may require:

1. Introduce new schema elements.
2. Update the view if necessary.
3. Deploy compatible application code.
4. Validate consumers.
5. Remove obsolete elements only after dependencies are gone.

Views should therefore be treated as first-class schema dependencies during migrations.

---

## View Dependencies

Before changing a production table, identify dependent views, functions, triggers, and other objects.

PostgreSQL dependency metadata can help investigate relationships.

For example:

```sql
SELECT
    dependent_ns.nspname AS dependent_schema,
    dependent_view.relname AS dependent_object
FROM pg_depend
JOIN pg_rewrite
    ON pg_depend.objid = pg_rewrite.oid
JOIN pg_class AS dependent_view
    ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_namespace AS dependent_ns
    ON dependent_view.relnamespace = dependent_ns.oid
WHERE pg_depend.refobjid = 'public.customers'::regclass;
```

For large production databases, use dependency-aware migration tooling rather than relying solely on manual inspection.

---

## CREATE OR REPLACE VIEW

PostgreSQL supports replacing an existing view definition:

```sql
CREATE OR REPLACE VIEW customer_summary AS
SELECT
    id,
    email,
    status,
    created_at
FROM customers;
```

There are restrictions around changing the structure of an existing view, particularly when removing or reordering existing columns.

Treat view changes like API changes.

If many consumers depend on a view, adding a column is generally less disruptive than changing the meaning or removing an existing column.

---

## CTEs and Data-Modifying Statements

PostgreSQL supports data-modifying statements inside CTEs.

For example:

```sql
WITH inserted_order AS (
    INSERT INTO orders (
        customer_id,
        total_amount
    )
    VALUES ($1, $2)
    RETURNING id, customer_id
)
INSERT INTO order_events (
    order_id,
    event_type
)
SELECT
    id,
    'created'
FROM inserted_order;
```

This allows related database operations to be expressed as one statement.

Use this deliberately.

It is particularly useful when the operations need statement-level atomicity.

Do not confuse this with application transaction management. A larger business workflow may still require an explicit transaction spanning multiple statements.

---

## Recursive CTEs

Recursive CTEs are another capability that distinguishes CTEs from ordinary views.

Example:

```sql
WITH RECURSIVE category_tree AS (
    SELECT
        id,
        parent_id,
        name,
        0 AS depth
    FROM categories
    WHERE id = $1

    UNION ALL

    SELECT
        c.id,
        c.parent_id,
        c.name,
        ct.depth + 1
    FROM categories AS c
    JOIN category_tree AS ct
        ON c.parent_id = ct.id
)
SELECT
    id,
    parent_id,
    name,
    depth
FROM category_tree
ORDER BY depth, id;
```

This is useful for:

- Organizational hierarchies.
- Category trees.
- Dependency graphs.
- Parent-child structures.

A normal view can contain a recursive query definition, but the recursive execution behavior belongs to the query represented by the view. The key distinction remains that the CTE is a query construct, while the view is a persistent object.

---

## CTE vs Temporary Table

A CTE should also be distinguished from a temporary table.

| Property | CTE | Temporary Table |
|---|---|---|
| Lifetime | Statement | Session/transaction depending configuration |
| Persistent object | No | Temporary database object |
| Can be indexed separately | No | Yes |
| Can be analyzed separately | No | Yes |
| Useful for multi-step batch processing | Sometimes | Often |
| Query-local composition | Excellent | Less direct |
| Requires cleanup | No | Usually lifecycle-managed |

For very large intermediate datasets that need indexes, statistics, or reuse across multiple statements, a temporary table may be more appropriate.

Do not introduce a temporary table merely because a CTE is syntactically long.

---

## View vs CTE vs Temporary Table

| Requirement | CTE | View | Temporary Table |
|---|---:|---:|---:|
| One-query composition | Excellent | Poor | Possible |
| Reuse across queries | No | Excellent | Yes within lifecycle |
| Persistent schema interface | No | Yes | No |
| Recursive query | Yes | Can encapsulate one | Possible but indirect |
| Explicit indexes on intermediate data | No | No | Yes |
| Persistent result data | No | No | No |
| Statement-local logic | Excellent | Overkill | Often overkill |
| Database-level permissions | No | Yes | Yes |
| Complex ETL workflow | Sometimes | Rarely | Often useful |

---

## Views in Django

Django migrations can create database views using `RunSQL`.

Example:

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0012_previous"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE VIEW customer_order_summary AS
                SELECT
                    customer_id,
                    COUNT(*) AS order_count,
                    SUM(total_amount) AS total_revenue
                FROM orders
                GROUP BY customer_id;
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS customer_order_summary;
            """,
        ),
    ]
```

A view can then be mapped to an unmanaged Django model if appropriate:

```python
from django.db import models


class CustomerOrderSummary(models.Model):
    customer_id = models.BigIntegerField(primary_key=True)
    order_count = models.IntegerField()
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        managed = False
        db_table = "customer_order_summary"
```

The model does not own the database object.

The migration or database deployment process remains responsible for creating and evolving the view.

---

## Views in FastAPI and SQLAlchemy

A FastAPI service can query a view like a table:

```sql
SELECT
    customer_id,
    order_count,
    total_revenue
FROM customer_order_summary
WHERE customer_id = $1;
```

With SQLAlchemy, the view can be represented as a selectable object or mapped appropriately.

The architectural benefit is that the API does not need to know the full join and aggregation logic.

However, this also introduces database coupling:

```text
FastAPI
   ↓
View contract
   ↓
PostgreSQL schema
```

Therefore view definitions should be version-controlled and deployed through CI/CD like application schema changes.

---

## Microservices Considerations

Views become more complicated when multiple services access the same database.

Suppose:

```text
Service A ─┐
Service B ─┼── PostgreSQL View ── Base Tables
Service C ─┘
```

The view becomes a shared contract.

This can be useful for read-heavy reporting but can also create tight coupling between independently deployed services.

For microservices architectures, consider whether the shared view is:

- A deliberate shared read model.
- A reporting interface.
- A temporary migration bridge.
- An accidental shared database dependency.

If independent service ownership is important, a dedicated API or replicated read model may be more appropriate.

---

## Views and CQRS

A view can be useful for the read side of a CQRS-style architecture:

```text
Write Model
    ↓
Events / CDC
    ↓
Read Model
    ↓
PostgreSQL View
    ↓
Read API
```

A normal view is still computed from underlying data at query time.

If the read model itself is expensive to construct, consider:

- Materialized views.
- Denormalized tables.
- Redis read models.
- Dedicated search indexes.
- OLAP systems.

The decision should be driven by latency and workload requirements rather than by the desire to hide SQL complexity.

---

## Operational Considerations

### Version Control

Views should be managed through:

- Migration files.
- Database deployment scripts.
- Schema repositories.
- CI/CD pipelines.

Avoid manually changing production views without recording the change.

### Testing

Test:

- Columns.
- Data types.
- NULL behavior.
- Join cardinality.
- Authorization.
- Tenant isolation.
- Query performance.
- Schema compatibility.

### Observability

Monitor queries against expensive views just like any other SQL workload.

Useful PostgreSQL tools include:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM customer_order_summary
WHERE customer_id = $1;
```

and query statistics through PostgreSQL monitoring facilities such as `pg_stat_statements`.

A view name appearing in application SQL does not mean the underlying work is inexpensive.

---

## High Availability and Disaster Recovery

Views themselves generally require little storage because a normal view stores a definition rather than result data.

However, the **view definition is part of the database schema**.

Therefore:

- Include views in schema migrations.
- Ensure they are recreated correctly during disaster recovery.
- Test restore procedures.
- Verify dependencies after restoration.
- Include view changes in deployment versioning.

For materialized views, the situation is different because their stored data and refresh strategy become operational concerns.

---

## Cost Considerations

Normal views do not eliminate compute cost.

If thousands of API requests repeatedly execute an expensive view:

```text
1000 requests
     ↓
1000 executions of expensive query
```

the database still pays the compute and I/O cost.

Potential solutions include:

- Better indexes.
- Query optimization.
- Result caching.
- Redis.
- Materialized views.
- Precomputed read models.
- Request-level batching.
- Dedicated reporting infrastructure.

A view improves abstraction and reuse; it does not inherently improve scalability.

---

## Production Decision Framework

Use a CTE when:

```text
Is the logic needed only inside one SQL statement?
        |
       Yes
        ↓
       CTE
```

Use a view when:

```text
Do multiple consumers need the same database-level definition?
        |
       Yes
        ↓
       VIEW
```

Consider a temporary table when:

```text
Does intermediate data need:
- multiple statements?
- indexes?
- statistics?
- substantial reuse?
        |
       Yes
        ↓
Temporary Table
```

Consider a materialized view or read model when:

```text
Is the query expensive and can data be slightly stale?
        |
       Yes
        ↓
Materialized View / Precomputed Read Model
```

---

## Practical Decision Matrix

| Scenario | Recommended approach |
|---|---|
| Complex one-off query | CTE |
| Multi-stage analytical query | CTE |
| Recursive hierarchy traversal | CTE |
| Reusable database abstraction | View |
| Standardized reporting projection | View |
| Expose restricted columns | View + appropriate privileges |
| Multiple large intermediate transformations | Temporary table may fit |
| Expensive reusable query with acceptable staleness | Materialized view |
| Low-latency API read model | Denormalized table / Redis / specialized read model |
| Shared cross-service database contract | View only with deliberate ownership |

---

## Common Mistakes

### Treating a View as a Cache

A normal view does not store query results.

If the underlying query is expensive, querying the view can still be expensive.

### Creating Views for Every Complex Query

A query used once does not usually justify creating a permanent schema object.

Use a CTE when the abstraction is query-local.

### Assuming CTEs Are Always Materialized

Modern PostgreSQL can inline eligible CTEs.

Use `MATERIALIZED` or `NOT MATERIALIZED` intentionally and validate the plan.

### Assuming CTEs Are Always Faster

A CTE is primarily a query-structuring tool. Performance depends on the resulting execution plan.

### Hiding Security Problems Behind a View

A view that exposes fewer columns does not automatically provide complete tenant isolation or authorization.

Use the correct combination of:

- Roles.
- Privileges.
- RLS.
- Security-barrier behavior where appropriate.
- Application authorization.

### Ignoring View Dependencies During Migrations

Changing a base table can break dependent views.

Treat views as schema dependencies.

### Manually Modifying Production Views

Manual changes create drift between environments.

Manage view definitions through version-controlled migrations.

### Using Views to Hide Poor Query Design

A view can make an inefficient query easier to call without making it more efficient.

Always inspect execution plans for important workloads.

### Creating Shared Views Without Ownership

A view used by multiple services becomes a shared contract.

Define ownership and compatibility expectations.

### Assuming Views Improve Scalability

Views improve abstraction, not necessarily latency or database throughput.

---

## Interview Traps

### "A view stores the result of its query."

False for a normal view.

A normal view stores the query definition.

### "A CTE is a temporary table."

Not exactly.

A CTE is a query-scoped named relation. It does not provide the same lifecycle, indexing, statistics, or independent storage characteristics as a temporary table.

### "Every CTE is materialized."

False in modern PostgreSQL.

Eligible CTEs can be inlined.

### "A view is always faster because the query is precompiled."

False.

A view is not inherently a cache or precomputed result.

### "Use a view whenever SQL is complicated."

Not necessarily.

If the logic is local to one statement, a CTE is often the cleaner choice.

### "Views automatically protect sensitive data."

Not completely.

Security depends on privileges, ownership, RLS, view properties, and the broader database security model.

### "A view removes coupling to the database."

It changes the form of coupling.

Consumers become coupled to the view contract instead of directly to the underlying tables.

### "CTEs and views are interchangeable."

They can contain similar SQL, but their lifecycle and architectural role are fundamentally different.

### "Materialized view and view are the same."

No.

A materialized view stores derived data and requires refresh management; a normal view evaluates its underlying query when referenced.

---

## Senior Engineering Perspective

The decision should be based on **scope and ownership**.

```text
Query-local abstraction
        ↓
       CTE

Database-level reusable abstraction
        ↓
       VIEW

Reusable intermediate state with indexes/statistics
        ↓
Temporary Table

Persisted derived result
        ↓
Materialized View / Read Model
```

A senior engineer should additionally ask:

- Who owns this SQL?
- How many consumers depend on it?
- Is it part of the public database contract?
- Does it need independent permissions?
- How will schema changes affect consumers?
- Is the underlying query expensive?
- Does freshness matter?
- Does the workload require precomputation?
- Can the database optimize through the abstraction?
- How will it be deployed and tested?

The right abstraction is therefore determined by lifecycle, performance, ownership, and operational requirements—not merely by query readability.

---

## Production Checklist

Before introducing a view:

- Confirm that the logic is genuinely reused.
- Define the view's ownership.
- Document its columns and semantics.
- Review permissions.
- Check tenant and authorization boundaries.
- Identify dependent objects and consumers.
- Add migration coverage.
- Test schema evolution.
- Run representative execution plans.
- Monitor query performance.
- Avoid treating the view as a cache.
- Establish compatibility expectations if multiple services consume it.

Before introducing a CTE:

- Confirm that it improves query composition.
- Keep intermediate stages logically meaningful.
- Check whether PostgreSQL can inline it.
- Use `MATERIALIZED` only when justified.
- Use `NOT MATERIALIZED` only when it improves the intended plan.
- Filter data early when semantically valid.
- Inspect execution plans for expensive queries.
- Consider a temporary table for large intermediate data that needs independent indexing or statistics.

---

## Key Takeaways

- **A CTE is query-scoped while a view is a persistent database object:** use CTEs for composing one statement and views for intentionally reusable database-level interfaces.
- **A normal view is not a cache:** it stores a query definition, so expensive underlying joins, aggregations, and window operations can remain expensive.
- **Modern PostgreSQL can inline eligible CTEs:** do not assume every CTE is materialized; use `MATERIALIZED` or `NOT MATERIALIZED` deliberately and validate execution plans.
- **Views introduce schema-level contracts and dependencies:** manage them through migrations, permissions, testing, and compatibility practices just like other production database interfaces.
- **Choose based on lifecycle, ownership, performance, and reuse:** consider temporary tables for indexed intermediate state and materialized views or read models when persisted derived results are required.