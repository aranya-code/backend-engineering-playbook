# 05- SQL for Backend Engineers

## Overview

SQL is a core backend engineering skill because relational databases usually hold the durable state that applications depend on.

A backend engineer does not interact with SQL in isolation. SQL sits inside a larger request and data lifecycle:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
Django / FastAPI / Service
  ↓
Business Logic
  ↓
ORM / Repository / Database Driver
  ↓
SQL
  ↓
PostgreSQL / MySQL / SQL Server
  ↓
Query Planner / Execution Engine
  ↓
Storage / Indexes / Cache
  ↓
Result
  ↓
Application
  ↓
HTTP / gRPC Response
```

For a backend engineer, SQL proficiency should progress beyond writing CRUD queries.

The practical progression is:

```text
Write SQL
   ↓
Understand relational data
   ↓
Write correct queries
   ↓
Understand transactions
   ↓
Understand indexes
   ↓
Read execution plans
   ↓
Diagnose database performance
   ↓
Design schemas and access patterns
   ↓
Handle concurrency and failures
   ↓
Operate databases in production
```

SQL therefore becomes part of application design, API design, performance engineering, reliability engineering, and system architecture.

---

## Why Backend Engineers Need Strong SQL Skills

Backend services commonly depend on databases for:

- User accounts
- Authentication state
- Orders
- Payments
- Inventory
- Permissions
- Configuration
- Audit records
- Billing
- Application metadata
- Workflow state

Consider an order API:

```http
POST /orders
```

The request may cause the backend to:

1. Validate the authenticated user.
2. Check product availability.
3. Create an order.
4. Create order items.
5. Update inventory.
6. Record payment state.
7. Publish an event.

Several of these operations may involve SQL and transactions.

A simplified data flow is:

```text
API Request
    ↓
Authentication
    ↓
Business Validation
    ↓
Database Transaction
    ├── Read inventory
    ├── Create order
    ├── Create order items
    ├── Update inventory
    └── Record state
    ↓
COMMIT
    ↓
Publish / Trigger downstream work
    ↓
API Response
```

A backend engineer who understands only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` will struggle to reason about the correctness and performance of this system.

---

## SQL Responsibilities in Backend Systems

SQL participates in several layers of backend engineering.

| Area | SQL Responsibility |
|---|---|
| Data access | Retrieve and modify persistent state |
| Data modeling | Represent entities and relationships |
| Integrity | Enforce constraints |
| Transactions | Maintain atomic state changes |
| Concurrency | Coordinate concurrent operations |
| Performance | Efficiently retrieve and modify data |
| Security | Prevent SQL injection and control access |
| Reporting | Aggregate and analyze data |
| Observability | Support query-level diagnostics |
| Scalability | Support increasing data and traffic |
| Reliability | Participate in recovery and failure handling |
| Operations | Support migrations, maintenance, and troubleshooting |

This is why SQL should be treated as an engineering discipline rather than merely a query syntax.

---

## SQL Knowledge Levels

A useful backend-oriented SQL progression is:

| Level | Primary Focus |
|---|---|
| Foundational | Tables, rows, columns, CRUD, basic filtering |
| Querying | Sorting, pagination, operators, aggregation, joins |
| Advanced Querying | Subqueries, CTEs, window functions, set operations |
| Data Management | Constraints, schema design, views, stored procedures, data modification |
| Transactional | Transactions, isolation, locking, concurrency |
| Performance | Indexes, execution plans, cardinality, query optimization |
| Production | Monitoring, connection pools, migrations, backups, replication |
| Senior | Workload design, scalability, reliability, failure modes, architecture |

The objective is not to memorize every SQL feature.

The objective is to understand **how to select the appropriate database mechanism for a backend requirement**.

---

## SQL as Part of the Backend Stack

A typical Python backend might look like:

```text
                         ┌──────────────┐
                         │    Client    │
                         └──────┬───────┘
                                │
                         HTTP / gRPC
                                │
                         ┌──────▼───────┐
                         │ Nginx / LB   │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │ Django /     │
                         │ FastAPI      │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │ Service      │
                         │ Layer        │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │ ORM /        │
                         │ Repository   │
                         └──────┬───────┘
                                │
                               SQL
                                │
                         ┌──────▼───────┐
                         │ PostgreSQL   │
                         └──────────────┘
```

The SQL layer should not be considered independent of the application.

Changes in application behavior can change database workload dramatically.

For example:

```text
API endpoint
    ↓
More requests
    ↓
More SQL executions
    ↓
Higher connection usage
    ↓
Higher database CPU / I/O
    ↓
Higher latency
```

A query that is acceptable at 10 requests per second may become a bottleneck at 5,000 requests per second.

---

## Writing Correct Queries

Correctness comes before optimization.

A query should produce exactly the intended result.

For example:

```sql
SELECT
    id,
    email
FROM users
WHERE is_active = TRUE;
```

This is straightforward.

More complex queries require careful reasoning about:

- Join cardinality
- NULL behavior
- Duplicate rows
- Aggregation
- Filtering order
- Ordering
- Pagination
- Transaction boundaries

For example, a join can unexpectedly multiply rows:

```text
users
  1
  │
  └──────< orders
             N
```

Joining users to orders produces one result row per matching order, not one row per user.

This becomes important when adding aggregation or pagination.

---

## Set-Based Thinking

Backend developers coming from imperative programming often initially think in terms of individual records.

SQL is designed around sets.

Instead of:

```python
for user in users:
    if user.is_inactive:
        user.disable()
```

a database can perform the operation as a set:

```sql
UPDATE users
SET is_active = FALSE
WHERE last_login_at < CURRENT_TIMESTAMP - INTERVAL '365 days';
```

Set-based operations can allow the database to optimize work internally.

This does not mean all business logic should move into SQL.

Use application code for:

- Business workflows
- External service calls
- Complex orchestration
- Domain logic
- API behavior

Use the database for operations where relational processing and data integrity are appropriate.

---

## Query Design for APIs

SQL should be designed around the application's access patterns.

Suppose an API provides:

```http
GET /users/42/orders
```

A reasonable query might be:

```sql
SELECT
    id,
    status,
    total_amount,
    created_at
FROM orders
WHERE user_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The query:

- Filters by user
- Selects only required columns
- Defines deterministic ordering
- Limits the result size

This is preferable to:

```sql
SELECT *
FROM orders;
```

followed by filtering and slicing in Python.

The database should generally perform work that it is designed to perform efficiently.

---

## SQL and Pagination

Pagination is a common backend requirement.

Offset pagination:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC
LIMIT 20 OFFSET 1000;
```

is simple and useful for many applications.

However, large offsets can become increasingly expensive because the database may need to process or skip many preceding rows.

Keyset or cursor pagination can be more efficient for large datasets.

Example:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE (created_at, id) < ('2026-08-30T10:00:00+00:00', 5000)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The exact implementation depends on the database and schema.

The backend engineer should choose pagination based on:

- Dataset size
- Access pattern
- Required navigation behavior
- Index design
- Consistency expectations

---

## SQL and Joins

Joins are fundamental to relational backend development.

Example:

```sql
SELECT
    o.id AS order_id,
    u.email,
    o.total_amount
FROM orders AS o
JOIN users AS u
    ON u.id = o.user_id
WHERE o.status = 'paid';
```

The backend engineer should understand:

- `INNER JOIN`
- `LEFT JOIN`
- `RIGHT JOIN`
- `FULL OUTER JOIN`
- Join predicates
- Join cardinality
- Join execution strategies

The most important practical issue is not memorizing syntax.

It is understanding:

> How many rows will this join produce?

For example:

```text
1 user
  ×
100 orders
  =
100 joined rows
```

Adding another one-to-many relationship can multiply the result further.

---

## SQL and Aggregation

Backend systems frequently need aggregated information.

For example:

```sql
SELECT
    user_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spend
FROM orders
WHERE status = 'paid'
GROUP BY user_id;
```

Aggregation is useful for:

- Reporting
- Dashboards
- Metrics
- Billing
- Business analytics
- API summaries

But large aggregations can be expensive.

The engineer should consider:

- Number of rows scanned
- Filtering
- Indexes
- Group cardinality
- Memory requirements
- Query frequency

A frequently requested expensive aggregation may eventually need:

- Precomputed data
- Materialized views
- Caching
- Summary tables
- Asynchronous processing

---

## Advanced SQL for Backend Engineers

Once the fundamentals are understood, several advanced query concepts become important.

### Subqueries

Use subqueries when one query depends on the result of another query.

Example:

```sql
SELECT
    id,
    email
FROM users
WHERE id IN (
    SELECT user_id
    FROM orders
    WHERE status = 'paid'
);
```

Subqueries can be useful for:

- Existence checks
- Filtering based on another relation
- Derived values
- Correlated conditions

They should not be treated as automatically slower or faster than joins.

The optimizer may transform equivalent query forms.

---

### Common Table Expressions

CTEs use the `WITH` clause:

```sql
WITH paid_orders AS (
    SELECT
        user_id,
        total_amount
    FROM orders
    WHERE status = 'paid'
)
SELECT
    user_id,
    SUM(total_amount) AS total_spend
FROM paid_orders
GROUP BY user_id;
```

CTEs are particularly useful for:

- Structuring complex queries
- Reusing intermediate query results
- Recursive queries
- Improving readability
- Breaking complicated logic into named stages

A CTE should not automatically be assumed to be a temporary table or optimization mechanism.

Materialization behavior is database- and version-dependent.

---

### Window Functions

Window functions calculate values across related rows without collapsing them into one row per group.

Example:

```sql
SELECT
    user_id,
    id AS order_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY created_at DESC
    ) AS order_rank
FROM orders;
```

Window functions are useful for:

- Ranking
- Running totals
- Previous/next row comparisons
- Top-N-per-group queries
- Percentiles
- Analytical calculations

They are especially valuable for backend reporting and data-heavy APIs.

---

### Set Operators

Set operators combine query results.

Common operators include:

```sql
UNION
UNION ALL
INTERSECT
EXCEPT
```

For example:

```sql
SELECT email
FROM customers

UNION

SELECT email
FROM subscribers;
```

`UNION` removes duplicates.

`UNION ALL` preserves duplicates and generally avoids the additional duplicate-elimination work.

The distinction matters for both correctness and performance.

---

## SQL and Data Modification

Backend services constantly modify persistent state.

Common operations include:

```sql
INSERT
UPDATE
DELETE
```

Modern systems may also use database-specific upsert mechanisms.

For example, PostgreSQL provides:

```sql
INSERT INTO users (
    email
)
VALUES (
    'alice@example.com'
)
ON CONFLICT (email)
DO UPDATE
SET updated_at = CURRENT_TIMESTAMP;
```

Data modification must be considered together with:

- Constraints
- Transactions
- Locks
- Triggers where applicable
- Cascading behavior
- Audit requirements
- Retry semantics

A write query is not simply "SQL that changes a row."

It participates in the database's consistency and concurrency model.

---

## SQL and Constraints

Critical data invariants should generally be enforced at the database level.

Example:

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    sku VARCHAR(64) NOT NULL UNIQUE,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0)
);
```

The database now protects:

```text
id
 └── unique identity

sku
 ├── required
 └── unique

price
 ├── required
 └── non-negative
```

This is important in distributed systems where multiple components can write to the same database.

For example:

```text
Django API
Celery Worker
Admin Tool
Migration
Batch Job
    │
    ▼
PostgreSQL
    │
    ▼
Database Constraints
```

The constraint protects the data regardless of which component performs the write.

---

## SQL and Transactions

Backend operations frequently require multiple changes to succeed or fail together.

Example:

```sql
BEGIN;

UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 100
  AND quantity > 0;

INSERT INTO orders (
    user_id,
    status
)
VALUES (
    42,
    'pending'
);

COMMIT;
```

The exact design should verify that the inventory update actually affected the expected row before treating the operation as successful.

Transactions are important for:

- Atomicity
- Consistency
- Isolation
- Durability

They should be scoped around a meaningful unit of work.

Avoid unnecessarily long transactions because they can increase:

- Lock contention
- Resource usage
- Blocking
- Deadlock risk
- Recovery complexity

---

## SQL and Concurrency

Production databases execute many transactions concurrently.

Consider two workers attempting to purchase the final unit of inventory:

```text
Worker A ───────┐
                │
                ▼
             Database
                ▲
                │
Worker B ───────┘
```

A naive sequence can create a race:

```text
A reads quantity = 1
B reads quantity = 1
A decrements
B decrements
```

The backend must design the operation so that concurrent requests cannot violate the inventory invariant.

Possible approaches include:

- Atomic updates
- Row locking
- Appropriate transaction isolation
- Optimistic concurrency
- Constraints

For example:

```sql
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 100
  AND quantity > 0;
```

The application can then inspect the affected-row count.

Concurrency control should be designed according to the invariant that must be protected.

---

## SQL and Indexes

Indexes are one of the most important database performance mechanisms.

For example:

```sql
CREATE INDEX idx_orders_user_created
ON orders(user_id, created_at DESC);
```

This may support a query such as:

```sql
SELECT
    id,
    status,
    created_at
FROM orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;
```

The index is aligned with the query's access pattern.

But indexes have costs:

- Additional storage
- Write overhead
- Maintenance overhead
- Memory pressure
- Increased schema complexity

The correct question is not:

> "Should this column have an index?"

The better question is:

> "Which production queries need an efficient access path, and what index best supports those queries?"

---

## SQL and Query Optimization

When a query is slow, do not immediately rewrite it.

First determine what the database is doing.

For PostgreSQL:

```sql
EXPLAIN
SELECT
    id,
    email
FROM users
WHERE email = 'alice@example.com';
```

For runtime information:

```sql
EXPLAIN ANALYZE
SELECT
    id,
    email
FROM users
WHERE email = 'alice@example.com';
```

Look for:

- Sequential scans
- Index scans
- Large row estimates
- Actual vs estimated rows
- Expensive joins
- Sort operations
- Hash operations
- Temporary I/O
- Parallel operations

A useful diagnostic flow is:

```text
Slow API
   ↓
Identify database query
   ↓
Measure frequency and latency
   ↓
Inspect generated SQL
   ↓
EXPLAIN
   ↓
EXPLAIN ANALYZE
   ↓
Understand execution plan
   ↓
Change query / index / schema
   ↓
Measure again
```

Optimization should be evidence-driven.

---

## SQL and ORMs

ORMs provide valuable abstraction.

For example, Django:

```python
orders = (
    Order.objects
    .filter(user_id=42)
    .order_by("-created_at")[:20]
)
```

can generate SQL similar to:

```sql
SELECT
    id,
    user_id,
    status,
    total_amount,
    created_at
FROM orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;
```

The ORM improves developer productivity, but the database still executes the resulting query.

Backend engineers should understand:

- Generated SQL
- Query count
- Join behavior
- Lazy vs eager loading
- Transactions
- Locking
- Indexes
- Query plans

---

## N+1 Queries

One of the most common ORM-related database problems is the N+1 query pattern.

For example:

```text
1 query
    ↓
Fetch 100 orders

100 additional queries
    ↓
Fetch customer for each order

Total = 101 queries
```

This can create significant latency.

The application may instead use appropriate eager loading or a join strategy.

Conceptually:

```text
Orders
   +
Customers
   ↓
Single optimized access pattern
```

The correct solution depends on the ORM and access pattern.

The key engineering principle is:

> Always understand how many database round trips an application operation causes.

---

## SQL and Connection Pooling

Database connections are expensive and finite resources.

A production backend generally uses connection pooling:

```text
Application Workers
        │
        ▼
 Connection Pool
 ┌──────┼──────┐
 ▼      ▼      ▼
Conn 1  Conn 2  Conn 3
 └──────┼──────┘
        ▼
    PostgreSQL
```

Without appropriate pooling:

```text
High traffic
    ↓
Many connection attempts
    ↓
Database connection exhaustion
    ↓
Request failures
```

Connection pool sizing should consider:

- Application concurrency
- Number of application instances
- Database connection limits
- Query duration
- Background workers
- Administrative connections

A common mistake is configuring a large pool independently on every Kubernetes pod.

For example:

```text
20 pods
×
20 connections per pod
=
400 potential connections
```

The database must be able to support the aggregate workload.

---

## SQL in Microservices

Microservice architectures introduce additional database considerations.

A common design principle is:

```text
Service A
   ↓
Database A

Service B
   ↓
Database B
```

rather than:

```text
Service A ──┐
Service B ──┼──→ Shared Database
Service C ──┘
```

A service-owned database can improve autonomy, but introduces distributed-system complexity.

Cross-service operations may no longer be handled by a single database transaction.

Instead, systems may require:

- Events
- Outbox patterns
- Sagas
- Idempotency
- Eventual consistency

For example:

```text
Order Service
    ↓
PostgreSQL
    ↓
Outbox Event
    ↓
Kafka
    ↓
Payment Service
    ↓
Payment Database
```

SQL knowledge therefore remains relevant even in event-driven architectures.

---

## SQL and Redis

Redis can reduce database load by caching frequently accessed data.

A common pattern is:

```text
Request
   ↓
Redis
   │
   ├── Cache hit → Response
   │
   └── Cache miss
          ↓
      PostgreSQL
          ↓
      Redis
          ↓
      Response
```

However, Redis should not automatically replace relational persistence.

A typical division is:

| System | Typical Responsibility |
|---|---|
| PostgreSQL | Authoritative persistent state |
| Redis | Cache / ephemeral state |
| Kafka | Event streaming |
| Object storage | Large files / blobs |

Caching introduces consistency and invalidation concerns.

The database remains the source of truth unless the architecture explicitly defines otherwise.

---

## SQL and Background Workers

Celery and similar workers frequently interact with SQL databases.

For example:

```text
API
 ↓
Create job state in PostgreSQL
 ↓
Publish / enqueue task
 ↓
Celery Worker
 ↓
Read database state
 ↓
Perform operation
 ↓
Update database
```

Background workers can create substantial database load because they run independently of API traffic.

Database capacity planning should therefore include:

- API requests
- Celery workers
- Scheduled jobs
- Batch processes
- Migrations
- Administrative operations

---

## SQL and Security

SQL security begins with parameterized queries.

Unsafe:

```python
query = f"""
SELECT id
FROM users
WHERE email = '{email}'
"""
```

Safe:

```python
cursor.execute(
    """
    SELECT id
    FROM users
    WHERE email = %s
    """,
    (email,),
)
```

Parameterization prevents user input from being interpreted as SQL syntax.

Additional security practices include:

- Least-privilege database roles
- Secret management
- Encrypted connections
- Restricted network access
- Auditing
- Controlled administrative access
- Safe query logging

Do not expose a production database directly to untrusted clients.

---

## SQL and Observability

SQL should be observable in production.

Important metrics include:

| Metric | Why It Matters |
|---|---|
| Query latency | Detects slow operations |
| Query frequency | Identifies high-volume queries |
| Rows returned | Detects excessive result sets |
| CPU | Detects expensive execution |
| I/O | Detects storage pressure |
| Connections | Detects pool exhaustion |
| Lock waits | Detects contention |
| Deadlocks | Detects concurrency problems |
| Replication lag | Detects replica pressure |
| Temporary storage | Detects expensive sorts/hashes |

Application and database telemetry should be correlated.

For example:

```text
API latency ↑
     ↓
Database latency ↑
     ↓
Specific query identified
     ↓
Execution plan analyzed
     ↓
Root cause found
```

Monitoring only API latency makes database-related diagnosis much harder.

---

## SQL and Reliability

Database failures can occur even when SQL is correct.

Production applications need to account for:

- Connection failures
- Network failures
- Timeouts
- Deadlocks
- Lock contention
- Database failover
- Replication issues
- Transaction rollback
- Capacity exhaustion

Retry behavior requires particular care.

For example:

```text
Application
    ↓
INSERT payment
    ↓
Database commits
    ↓
Network response lost
    ↓
Application assumes failure
    ↓
Retry
    ↓
Potential duplicate payment
```

Idempotency keys, unique constraints, and appropriate transaction design can help protect against these situations.

---

## SQL and Schema Migrations

Schema changes are part of backend deployment.

Examples include:

```sql
ALTER TABLE users
ADD COLUMN last_login_at TIMESTAMPTZ;
```

Production migrations must consider:

- Table size
- Lock duration
- Existing traffic
- Index creation cost
- Backfill strategy
- Rollback strategy
- Application compatibility

A safe migration may require multiple deployments.

For example:

```text
Deployment A
    ↓
Add nullable column
    ↓
Deploy application that can use old + new schema
    ↓
Backfill data
    ↓
Deploy application requiring new field
    ↓
Add stricter constraint if appropriate
```

This is often safer than making a large incompatible schema change in a single deployment.

---

## SQL and High Availability

A production relational database may use replication and failover mechanisms.

A simplified architecture is:

```text
                  ┌───────────────┐
                  │   Application │
                  └───────┬───────┘
                          │
                    Read / Write
                          │
                   ┌──────▼───────┐
                   │   Primary    │
                   └──────┬───────┘
                          │
                     Replication
                    ┌─────┴─────┐
                    ▼           ▼
              Read Replica  Read Replica
```

The exact topology depends on the database and infrastructure.

Backend engineers should understand:

- Replication lag
- Read-after-write consistency
- Failover
- Connection routing
- Replica availability
- Backup strategy

For example, immediately reading from a replica after writing to the primary can return stale data if replication has not caught up.

---

## SQL and Disaster Recovery

High availability and disaster recovery are different concerns.

Replication can improve availability but does not replace backups.

A production database strategy should define:

- Recovery Point Objective (RPO)
- Recovery Time Objective (RTO)
- Backup retention
- Point-in-time recovery where supported
- Restore procedures
- Disaster recovery testing

A useful distinction is:

```text
Replication
    ↓
Helps maintain availability

Backups
    ↓
Help recover historical state

Disaster Recovery
    ↓
Defines how the system returns to service
```

Backups should be periodically restored and verified.

---

## SQL and AWS

In AWS environments, relational databases are commonly operated through managed services such as Amazon RDS and Amazon Aurora.

A typical architecture might be:

```text
Internet
   ↓
ALB
   ↓
ECS / EKS / EC2
   ↓
Connection Pool
   ↓
RDS / Aurora
   ↓
Storage
```

The managed database removes some infrastructure responsibilities but does not remove SQL responsibilities.

Backend engineers still need to understand:

- Query performance
- Indexing
- Connection limits
- Transactions
- Locks
- Replication
- Backups
- Monitoring
- Failover
- Capacity planning

AWS infrastructure and SQL expertise therefore complement rather than replace each other.

---

## Production SQL Checklist

Before shipping an important database operation, consider:

### Correctness

- Does the query return exactly the intended rows?
- Are duplicates possible?
- Is NULL handled correctly?
- Are relationships correct?
- Are constraints protecting critical invariants?

### Performance

- What happens as the table grows?
- Can the query use an appropriate index?
- How many rows are scanned?
- How many rows are returned?
- Is sorting expensive?
- Are joins producing large intermediate results?

### Transactions

- Does the operation require atomicity?
- What should happen if one statement fails?
- Could concurrent requests race?
- What locks are acquired?
- Could the transaction remain open too long?

### Application Integration

- How many database round trips occur?
- Is the ORM generating efficient SQL?
- Could this create an N+1 query?
- Is connection pooling configured appropriately?

### Security

- Are parameters bound safely?
- Does the database role have minimal privileges?
- Could logs expose sensitive information?

### Operations

- Can the query be monitored?
- Can it be cancelled safely?
- What happens during database failover?
- How will migrations affect production traffic?

---

## Common Mistakes

### Treating SQL as CRUD Only

CRUD is the starting point, not the destination.

Backend engineers eventually need:

- Joins
- Aggregations
- CTEs
- Window functions
- Transactions
- Indexes
- Execution plans
- Concurrency control

### Using `SELECT *` in Production APIs

It retrieves columns that may not be required and creates unnecessary coupling between database schema and API behavior.

Prefer explicit projections.

### Returning Unbounded Results

A query returning millions of rows can exhaust database, application, and network resources.

Use appropriate filtering and pagination.

### Ignoring N+1 Queries

An ORM can make inefficient database access look like clean application code.

Always understand the number of queries generated.

### Adding Indexes Without Evidence

Indexes have write and storage costs.

Design them around real access patterns.

### Assuming Every Slow Query Needs an Index

A slow query can be caused by:

- Poor cardinality estimates
- Expensive joins
- Sorting
- Lock waits
- Large result sets
- Poor query shape
- Insufficient resources

### Holding Transactions Too Long

Long transactions can increase contention and operational problems.

Keep transactional scopes intentional.

### Blindly Retrying Writes

A timeout does not necessarily mean that the database operation failed.

Design write operations with idempotency and transactional correctness.

### Testing Only Against SQLite

SQLite differs from PostgreSQL and other server databases in architecture and behavior.

Important integration tests should use the actual production database engine.

### Moving Business Logic Entirely Into SQL

Stored procedures and database-side logic can be useful, but putting all domain behavior into the database can increase coupling and make application evolution harder.

Choose the appropriate execution layer deliberately.

---

## Interview Perspective

A backend SQL interview should progress beyond syntax questions.

Important areas include:

### Querying

- How do joins work?
- What is the difference between `WHERE` and `HAVING`?
- How does `GROUP BY` work?
- What are CTEs?
- What are window functions?
- How do subqueries work?

### Performance

- What is an index?
- When will an index help?
- Why might a database ignore an index?
- What is an execution plan?
- How would you debug a slow query?
- What is cardinality estimation?

### Transactions

- What is a transaction?
- What are isolation levels?
- What is a deadlock?
- What is MVCC?
- How do you prevent race conditions?

### Backend Architecture

- How do ORMs generate SQL?
- What is the N+1 query problem?
- How should connection pools be sized?
- How do read replicas affect consistency?
- How would you design database access for microservices?

### Production

- How do you safely migrate a large table?
- How do you diagnose database saturation?
- What happens when the primary database fails?
- How do backups and replication differ?
- How do you handle retries after ambiguous database failures?

A strong answer should connect SQL syntax to database behavior and application architecture.

---

## Senior-Level Mental Model

The most useful mental model for backend SQL is:

```text
Business Requirement
        ↓
Data Model
        ↓
Access Pattern
        ↓
SQL
        ↓
Query Plan
        ↓
Indexes / Storage / Memory
        ↓
Transaction / Concurrency
        ↓
Database Resources
        ↓
Application Latency
        ↓
System Reliability
```

For example:

```text
Requirement:
"Return a user's 20 latest orders."

        ↓

Access pattern:
Filter by user_id
Sort by created_at
Limit to 20

        ↓

SQL:
WHERE user_id = ?
ORDER BY created_at DESC
LIMIT 20

        ↓

Index:
(user_id, created_at DESC)

        ↓

Execution:
Efficient index access

        ↓

Application:
Low database latency
```

This is the level of reasoning expected from experienced backend engineers.

---

## Recommended SQL Learning Order

A practical learning sequence for backend engineering is:

```text
SQL Fundamentals
    ↓
SELECT and Filtering
    ↓
Sorting, Pagination, Result Control
    ↓
SQL Operators
    ↓
Aggregate Functions
    ↓
String Functions
    ↓
Date and Time
    ↓
NULL Handling
    ↓
CASE WHEN
    ↓
Type Casting and Conversion
    ↓
Set Operators
    ↓
JOINs
    ↓
Subqueries
    ↓
Common Table Expressions
    ↓
Window Functions
    ↓
Views
    ↓
Stored Procedures
    ↓
Data Modification
    ↓
Constraints and Data Integrity
    ↓
Transactions
    ↓
Concurrency and Isolation
    ↓
Indexes
    ↓
Execution Plans
    ↓
Query Optimization
    ↓
Database Performance
    ↓
Production Operations
```

The progression should be practical rather than purely theoretical.

For each SQL concept, ask:

```text
What is it?
   ↓
Why does it exist?
   ↓
When should I use it?
   ↓
When should I avoid it?
   ↓
How does the database execute it?
   ↓
What does it cost?
   ↓
How does it behave under concurrency?
   ↓
How does it behave at production scale?
```

That mindset turns SQL knowledge into backend engineering capability.

---

## Key Takeaways

- **SQL is a backend engineering skill, not merely a database syntax skill**; it affects API design, data modeling, transactions, performance, security, and reliability.
- **Understand what the database actually executes**, including generated SQL, execution plans, indexes, joins, transactions, locks, and resource usage.
- **Design SQL around production access patterns**, with explicit projections, appropriate filtering, deterministic ordering, bounded results, and indexes that support real queries.
- **ORMs, Redis, Kafka, Celery, and AWS infrastructure do not remove the need for SQL knowledge**; they change how SQL participates in the overall backend architecture.
- **Senior-level SQL means reasoning about correctness, concurrency, performance, scalability, observability, and failure behavior—not simply writing queries that return the right rows.**