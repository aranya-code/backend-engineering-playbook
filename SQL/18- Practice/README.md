# README

## Overview

The `18- Practice` section is the hands-on SQL training layer of the engineering playbook.

The purpose is to convert SQL knowledge into **repeatable problem-solving ability**. The exercises progress from query construction and relational reasoning to indexing, optimization, transactions, concurrency, backend API design, and production incident scenarios.

The practice sequence is intentionally aligned with backend engineering rather than database syntax alone:

```mermaid
flowchart LR
    A[SQL Fundamentals] --> B[Filtering]
    B --> C[JOINs]
    C --> D[Aggregation]
    D --> E[NULL and CASE]
    E --> F[Subqueries]
    F --> G[CTEs]
    G --> H[Window Functions]
    H --> I[Date and Time]
    I --> J[Indexing]
    J --> K[Query Optimization]
    K --> L[Transactions]
    L --> M[Concurrency]
    M --> N[Database Design]
    N --> O[Pagination]
    O --> P[Backend API Queries]
    P --> Q[Production Scenarios]
```

The target is not simply to complete exercises. The target is to develop the ability to:

- Translate business requirements into SQL.
- Predict result cardinality before executing a query.
- Select the correct SQL construct for a problem.
- Identify correctness and edge-case failures.
- Design indexes around actual access patterns.
- Read and reason about execution plans.
- Handle transactions and concurrent writes safely.
- Build efficient database-backed APIs.
- Diagnose production database problems systematically.

## Navigation

| # | Section | Layer | Description |
|---|---|---|---|
| 01 | [Practice](./README.md) | Applied SQL | Hands-on SQL exercises from basic CRUD through transactions, optimization, and production scenarios |
| 02 | [01- SQL Playground Setup](./01-%20SQL%20Playground%20Setup.md) | Applied SQL | Setting up a local PostgreSQL environment for SQL practice |
| 03 | [02- Database Setup](./02-%20Database%20Setup.md) | Applied SQL | Creating and configuring practice databases and roles |
| 04 | [03- Schema Creation Exercises](./03-%20Schema%20Creation%20Exercises.md) | Applied SQL | Designing and creating relational schemas from scratch |
| 05 | [04- CRUD Exercises](./04-%20CRUD%20Exercises.md) | Applied SQL | INSERT, SELECT, UPDATE, DELETE practice exercises |
| 06 | [05- Filtering Exercises](./05-%20Filtering%20Exercises.md) | Applied SQL | WHERE, LIKE, IN, BETWEEN, and predicate filtering exercises |
| 07 | [06- JOIN Exercises](./06-%20JOIN%20Exercises.md) | Applied SQL | INNER, LEFT, RIGHT, FULL, CROSS, and self JOIN exercises |
| 08 | [07- Aggregation Exercises](./07-%20Aggregation%20Exercises.md) | Applied SQL | GROUP BY, HAVING, COUNT, SUM, AVG, and aggregation exercises |
| 09 | [08- NULL Handling Exercises](./08-%20NULL%20Handling%20Exercises.md) | Applied SQL | NULL semantics, IS NULL, COALESCE, and three-valued logic exercises |
| 10 | [09- CASE Exercises](./09-%20CASE%20Exercises.md) | Applied SQL | Conditional logic and CASE expression exercises |
| 11 | [10- Date and Time Exercises](./10-%20Date%20and%20Time%20Exercises.md) | Applied SQL | Timestamp, interval, timezone, and date arithmetic exercises |
| 12 | [11- Subquery Exercises](./11-%20Subquery%20Exercises.md) | Applied SQL | Correlated and uncorrelated subquery exercises |
| 13 | [12- CTE Exercises](./12-%20CTE%20Exercises.md) | Applied SQL | Common Table Expression and recursive CTE exercises |
| 14 | [13- Window Function Exercises](./13-%20Window%20Function%20Exercises.md) | Applied SQL | ROW_NUMBER, RANK, LAG, LEAD, and window frame exercises |
| 15 | [14- Indexing Exercises](./14-%20Indexing%20Exercises.md) | Applied SQL | Index design, selectivity, and access path exercises |
| 16 | [15- Query Optimization Exercises](./15-%20Query%20Optimization%20Exercises.md) | Applied SQL | Execution plan analysis and query rewriting exercises |
| 17 | [16- Transaction Exercises](./16-%20Transaction%20Exercises.md) | Applied SQL | Transaction control, isolation levels, and rollback exercises |
| 18 | [17- Concurrency Exercises](./17-%20Concurrency%20Exercises.md) | Applied SQL | Lock contention, deadlock, and concurrent write exercises |
| 19 | [18- Database Design Exercises](./18-%20Database%20Design%20Exercises.md) | Applied SQL | Schema modeling, normalization, and design decision exercises |
| 20 | [19- Pagination Exercises](./19-%20Pagination%20Exercises.md) | Applied SQL | Offset and keyset pagination exercises for large datasets |
| 21 | [20- Backend API Query Exercises](./20-%20Backend%20API%20Query%20Exercises.md) | Applied SQL | SQL exercises modeled on real backend API query patterns |
| 22 | [21- Production Scenario Exercises](./21-%20Production%20Scenario%20Exercises.md) | Applied SQL | End-to-end production database problem-solving exercises |
| 23 | [22- SQL Challenge Progress](./22-%20SQL%20Challenge%20Progress.md) | Applied SQL | Progress tracker for completed SQL practice exercises |

---

## Practice Structure

The section is organized into progressively harder categories.

| Category | Focus | Primary Outcome |
|---|---|---|
| Query Fundamentals | SQL syntax and filtering | Write correct SQL |
| Relational Queries | JOINs and cardinality | Reason about relationships |
| Data Transformation | Aggregation, `CASE`, `NULL` | Produce correct derived results |
| Advanced Queries | Subqueries, CTEs, windows | Compose complex SQL |
| Temporal Queries | Date and time | Handle production time semantics |
| Performance | Indexing and optimization | Understand query cost |
| Transactions | Atomicity and boundaries | Preserve correctness |
| Concurrency | Locks and races | Handle simultaneous operations |
| Design | Schema and data modeling | Design durable relational structures |
| API Queries | Pagination and application integration | Build scalable backend queries |
| Production | Incident and architecture scenarios | Apply SQL under real constraints |

---

## Exercise Index

| File | Topic | Level |
|---|---|---|
| `01- Core SQL Exercises.md` | Core SQL operations | Beginner |
| `02- SELECT and Filtering Exercises.md` | Projection and filtering | Beginner |
| `03- JOIN Exercises.md` | JOINs and relationships | Intermediate |
| `04- Aggregation Exercises.md` | Aggregation and grouping | Intermediate |
| `05- NULL Handling Exercises.md` | `NULL` and three-valued logic | Intermediate |
| `06- CASE Exercises.md` | Conditional expressions | Intermediate |
| `07- Subquery Exercises.md` | Subqueries and existence checks | Intermediate |
| `08- CTE Exercises.md` | Common table expressions | Intermediate |
| `09- Window Function Exercises.md` | Window functions | Advanced |
| `10- Date and Time Exercises.md` | Temporal SQL | Intermediate |
| `11- Subquery Exercises.md` | Advanced subqueries | Advanced |
| `12- CTE Exercises.md` | Advanced CTE patterns | Advanced |
| `13- Window Function Exercises.md` | Advanced window functions | Advanced |
| `14- Indexing Exercises.md` | Index design | Advanced |
| `15- Query Optimization Exercises.md` | Query performance | Advanced |
| `16- Transaction Exercises.md` | Transaction semantics | Advanced |
| `17- Concurrency Exercises.md` | Concurrent database operations | Advanced |
| `18- Database Design Exercises.md` | Relational database design | Advanced |
| `19- Pagination Exercises.md` | Pagination strategies | Advanced |
| `20- Backend API Query Exercises.md` | SQL-backed APIs | Advanced |
| `21- Production Scenario Exercises.md` | Production troubleshooting and architecture | Senior |
| `22- SQL Challenge Progress.md` | Progress and mastery tracking | Reference |

---

## Recommended Learning Order

Complete the exercises in order unless a specific interview or project requirement justifies skipping ahead.

### Query Construction

Start with:

- Core SQL
- `SELECT`
- filtering
- ordering
- limiting
- basic expressions

The objective is to make basic query construction automatic.

### Relational Reasoning

Then focus on:

- `JOIN`
- one-to-many relationships
- many-to-many relationships
- aggregation
- `GROUP BY`
- `HAVING`
- `NULL`
- `CASE`

At this stage, **cardinality** becomes more important than syntax.

### Advanced Query Composition

Continue with:

- subqueries
- `EXISTS`
- `NOT EXISTS`
- CTEs
- recursive CTEs
- window functions
- advanced date/time operations

The goal is to choose query structures based on the required result, not based on whichever syntax is most familiar.

### Performance

Move into:

- index design
- composite indexes
- partial indexes
- expression indexes
- covering indexes
- execution plans
- cardinality estimates
- join algorithms
- sorting
- aggregation
- query workload analysis

The goal is to understand **why a query is fast or slow**.

### Backend Engineering

Then practice:

- transactions
- concurrent updates
- locks
- deadlocks
- pagination
- API query design
- ORM-generated SQL
- connection pools
- read replicas
- caching

This connects SQL knowledge to Django, FastAPI, and production services.

### Production Scenarios

Finish with:

- database incidents
- high CPU
- high memory
- slow queries
- missing indexes
- lock contention
- migration problems
- replication issues
- API performance
- scaling decisions

The objective is senior-level database reasoning.

---

## Core Practice Principles

### Solve Before Looking at the Answer

For every exercise:

1. Read the requirements carefully.
2. Identify the expected result grain.
3. Identify relevant tables and relationships.
4. Write the query independently.
5. Execute it against realistic data.
6. Test edge cases.
7. Review the execution plan when performance matters.
8. Compare against an alternative solution.

Do not optimize a query that is not yet known to be correct.

---

## Result Grain First

Before writing SQL, explicitly state:

> "The query should return one row per ______."

Examples:

- One row per customer.
- One row per order.
- One row per customer per month.
- One row per product.
- One row per account and currency.

This prevents many common SQL errors involving joins and aggregation.

For example, if the desired grain is one row per customer, joining directly to multiple child tables can unintentionally multiply rows.

---

## Cardinality Is a Core Skill

For every `JOIN`, ask:

| Question | Example |
|---|---|
| What is the left-side grain? | One row per customer |
| What is the right-side grain? | Many rows per customer |
| What is the relationship? | One-to-many |
| Can the join multiply rows? | Yes |
| Is multiplication intended? | Depends |
| Should `EXISTS` be used instead? | Sometimes |

A senior SQL engineer should be able to reason about cardinality before executing the query.

---

## Correctness Before Performance

Use this order:

```text
Requirements
    ↓
Expected result grain
    ↓
SQL correctness
    ↓
Edge cases
    ↓
Security / authorization
    ↓
Execution plan
    ↓
Indexing
    ↓
Workload optimization
    ↓
Operational behavior
```

An efficient query returning the wrong data is still a failed query.

---

## Production Dataset Thinking

Exercises should eventually move beyond tiny datasets.

Consider realistic distributions such as:

- Millions of users.
- Millions of orders.
- Many orders per customer.
- Highly active tenants.
- Large historical tables.
- Sparse optional relationships.
- Hot rows.
- Recent records representing a small percentage of the total table.

A query that performs well on 100 rows can behave completely differently on 100 million rows.

---

## Recommended PostgreSQL Environment

PostgreSQL is the primary reference database for this practice section.

A local Docker environment is sufficient for most exercises.

Example:

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: sql_practice
      POSTGRES_USER: sql_user
      POSTGRES_PASSWORD: sql_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Connect with:

```bash
psql postgresql://sql_user:sql_password@localhost:5432/sql_practice
```

For production-like exercises, use a dataset large enough to make query plans and indexing decisions meaningful.

---

## Practice Schema

A consistent business domain makes it easier to compare different SQL techniques.

A representative schema can contain:

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : included_in
    CUSTOMER ||--o{ PAYMENT : makes
    CUSTOMER ||--o{ ADDRESS : has
    ORDER ||--o{ ORDER_STATUS_HISTORY : records

    CUSTOMER {
        bigint id PK
        text email
        text name
        timestamptz created_at
        boolean active
    }

    ORDER {
        bigint id PK
        bigint customer_id FK
        text status
        numeric total_amount
        timestamptz created_at
    }

    ORDER_ITEM {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        integer quantity
        numeric unit_price
    }

    PRODUCT {
        bigint id PK
        text name
        numeric price
        boolean active
    }

    PAYMENT {
        bigint id PK
        bigint customer_id FK
        bigint order_id FK
        numeric amount
        text status
        timestamptz created_at
    }

    ADDRESS {
        bigint id PK
        bigint customer_id FK
        text city
        text country
    }

    ORDER_STATUS_HISTORY {
        bigint id PK
        bigint order_id FK
        text status
        timestamptz changed_at
    }
```

The actual exercise schemas may vary. The important principle is to practice against relationships that resemble real backend systems.

---

## SQL Problem-Solving Framework

Use the following framework for unfamiliar SQL problems.

### Identify the Entities

Determine which business entities participate.

Example:

```text
Customer
Order
Payment
Product
```

### Identify Relationships

Determine:

- one-to-one
- one-to-many
- many-to-many

### Define Result Grain

State exactly what one output row represents.

### Identify Required Operations

Determine whether the problem requires:

- filtering
- joining
- aggregation
- conditional logic
- existence checking
- ranking
- temporal calculations
- pagination

### Validate Edge Cases

Check:

- no related rows
- multiple related rows
- `NULL`
- duplicate relationships
- ties
- empty input
- boundary dates

### Evaluate Performance

Ask:

- How many rows are scanned?
- Which indexes can support the query?
- Is the filter selective?
- Are joins multiplying rows?
- Is sorting expensive?
- Is aggregation memory-intensive?

---

## Exercise Review Template

Use the following template for each completed problem.

```markdown
### Exercise

**Status:** ⬜ Not Started
**Attempts:** 0
**Independent Solve:** No
**Reviewed:** No
**Optimized:** No
**Production Ready:** No

#### Requirement

Describe the business requirement.

#### Expected Grain

One row per ...

#### First Attempt

```sql
-- SQL
```

#### Result

- Correct: Yes/No
- Expected rows: ...
- Actual rows: ...

#### Problem

Describe any incorrect reasoning.

#### Correct Solution

```sql
-- SQL
```

#### Alternative Approach

```sql
-- Alternative SQL
```

#### Performance Review

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

#### Production Considerations

- ...
- ...
- ...

#### Reusable Pattern

Describe the SQL pattern learned.
```

---

## Progress Tracking

Use `22- SQL Challenge Progress.md` as the central progress tracker.

Track more than completion.

| Metric | Purpose |
|---|---|
| Attempt count | Measures difficulty |
| Independent solve | Measures actual understanding |
| Hint required | Identifies weak concepts |
| Solution viewed | Identifies problems requiring review |
| Re-solve | Measures retention |
| Execution plan reviewed | Measures performance maturity |
| Production review | Measures backend readiness |

A completed exercise should not automatically be considered mastered.

---

## Mastery Levels

| Level | Capability |
|---|---|
| Syntax | Can write common SQL syntax |
| Query | Can solve relational SQL problems |
| Reasoning | Understands cardinality and SQL semantics |
| Performance | Can inspect plans and indexes |
| Backend | Can integrate SQL into production APIs |
| Production | Can diagnose SQL behavior under load |
| Senior | Can make database architecture decisions |

The final goal is not maximum syntax coverage.

The final goal is reliable engineering judgment.

---

## Skill Areas

Track these capabilities independently.

| Skill | Target |
|---|---|
| `SELECT` and filtering | Fluent |
| JOINs | Fluent |
| Cardinality | Strong |
| Aggregation | Strong |
| `NULL` semantics | Strong |
| `CASE` | Strong |
| Subqueries | Strong |
| CTEs | Strong |
| Window functions | Strong |
| Date/time | Strong |
| Index design | Strong |
| Query optimization | Strong |
| Transactions | Strong |
| Concurrency | Strong |
| Database design | Strong |
| Pagination | Strong |
| Backend API queries | Strong |
| Production diagnosis | Strong |

---

## SQL and Backend Integration

SQL practice should eventually connect directly to application code.

### Django

Understand what ORM operations generate.

For example:

```python
orders = (
    Order.objects
    .filter(customer_id=customer_id)
    .select_related("customer")
    .order_by("-created_at")
)
```

The exercise should include reviewing the SQL generated by the ORM when query behavior matters.

Important Django concepts include:

- `select_related`
- `prefetch_related`
- `annotate`
- `Subquery`
- `Exists`
- `F`
- `Q`
- `transaction.atomic`
- `select_for_update`

### FastAPI and SQLAlchemy

The same SQL reasoning applies when using SQLAlchemy.

Focus on:

- query construction
- transaction boundaries
- connection lifecycle
- eager loading
- pagination
- parameter binding
- execution plans

The framework changes. The database behavior does not.

---

## API Query Exercises

When SQL becomes part of an API, add application-level constraints.

A production endpoint should consider:

- bounded result size
- deterministic ordering
- pagination
- authorization
- tenant isolation
- query timeouts
- connection pool capacity
- serialization cost
- response size

For example:

```text
GET /customers/{id}/orders
```

should not implicitly mean:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

without considering how many rows can exist for that customer.

A production design might require:

```sql
SELECT id, status, total_amount, created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
LIMIT $2;
```

The SQL exercise should therefore test both **query correctness** and **API scalability**.

---

## Performance Practice

Use `EXPLAIN` when learning plan behavior:

```sql
EXPLAIN
SELECT id, status
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC;
```

Use `EXPLAIN ANALYZE` carefully on appropriate datasets:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC
LIMIT 50;
```

Practice answering:

- Why did PostgreSQL choose this scan?
- Are estimated rows close to actual rows?
- Is an index being used?
- Is sorting required?
- Are buffers mostly hits or reads?
- Is the query CPU-bound or I/O-bound?
- Is the query actually waiting on a lock rather than executing slowly?

---

## Indexing Practice

Index exercises should not become a game of adding indexes until the query becomes faster.

For every proposed index, consider:

| Question | Reason |
|---|---|
| What query does it support? | Establishes purpose |
| What predicates does it support? | Determines key order |
| What ordering does it support? | Can avoid sorting |
| How selective is it? | Determines usefulness |
| How large is the index? | Determines storage cost |
| How often is the query executed? | Determines ROI |
| What write cost does it introduce? | Determines operational impact |
| Is another index already sufficient? | Prevents redundancy |

Indexes are workload decisions, not decorations on tables.

---

## Transaction Practice

Transaction exercises should eventually model business invariants.

Examples:

- Transfer funds between accounts.
- Reserve inventory.
- Create an order and its items.
- Update a state machine.
- Consume a job exactly once.
- Record an audit event with a state change.

Practice identifying whether the operation requires:

- atomic SQL
- an explicit transaction
- row locking
- optimistic concurrency
- unique constraints
- retry logic
- idempotency

A transaction should be scoped around the **database invariant**, not automatically around an entire HTTP request.

---

## Concurrency Practice

Concurrency exercises should use multiple sessions or application workers.

Important scenarios include:

- lost updates
- overselling inventory
- duplicate job processing
- concurrent state transitions
- hot-row contention
- deadlocks
- serialization failures
- lock timeouts

Practice both:

```sql
SELECT ...
FOR UPDATE;
```

and atomic operations such as:

```sql
UPDATE inventory
SET available = available - 1
WHERE product_id = $1
  AND available > 0;
```

The second approach can often reduce lock duration and simplify correctness because the invariant is enforced directly by the database operation.

---

## Pagination Practice

Practice both offset and keyset pagination.

### Offset

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 50000;
```

Advantages:

- Simple API model.
- Easy page-number navigation.

Limitations:

- Increasing offset can become expensive.
- Results can shift under concurrent inserts/deletes.
- Deep pagination is often inefficient.

### Keyset

```sql
SELECT id, created_at
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Advantages:

- Stable traversal.
- Efficient deep pagination with an appropriate index.
- Better suited to large datasets.

Production APIs should generally prefer keyset pagination when users do not require arbitrary page-number navigation.

---

## Production Scenario Practice

The final exercises should simulate incidents rather than isolated SQL questions.

Example scenarios:

| Scenario | Skills Tested |
|---|---|
| API latency suddenly increases | Query plans, indexes, workload |
| Database CPU reaches saturation | Query frequency, scans, concurrency |
| Connections are exhausted | Pooling, transactions, slow queries |
| Orders are duplicated | Transactions, idempotency, constraints |
| Inventory becomes negative | Concurrency and atomic updates |
| Queries block each other | Locks and transaction duration |
| Deadlocks appear | Lock ordering and retry |
| Read API returns stale data | Replication and consistency |
| Migration causes latency spike | DDL, locks, backfills |
| Reporting slows production DB | OLTP/OLAP separation |
| Tenant sees another tenant's data | Authorization and RLS |
| Deep pagination becomes slow | Keyset pagination and indexes |

The expected answer should explain not only the SQL fix but also:

- root cause
- immediate mitigation
- permanent fix
- monitoring
- rollback strategy
- failure modes
- scalability implications

---

## Common Practice Mistakes

### Memorizing Queries

Recognizing a familiar query is not the same as understanding it.

**Better approach:** change the schema, requirements, or edge cases and solve the problem again.

### Ignoring Result Grain

Many incorrect queries look plausible because the output contains expected columns.

**Better approach:** define the grain before writing the query.

### Using `DISTINCT` to Hide Duplicates

`DISTINCT` can conceal an incorrect join.

**Better approach:** determine why the join multiplies rows.

### Using `LIMIT 1` Without Deterministic Ordering

This can return an arbitrary qualifying row.

Prefer:

```sql
SELECT ...
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 1;
```

### Adding Indexes Without Evidence

An index can improve one query while increasing write cost and storage.

**Better approach:** inspect workload and execution plans.

### Testing Only Small Data

Small datasets can hide:

- bad join strategies
- expensive sorts
- sequential scans
- poor pagination
- memory pressure

### Ignoring Application Behavior

A correct SQL query can still create a production problem through:

- N+1 queries
- excessive concurrency
- large result sets
- connection leaks
- retry storms

---

## Security Practice

SQL exercises should eventually include security requirements.

Practice:

- parameterized queries
- safe dynamic SQL
- least-privilege roles
- tenant filtering
- row-level security
- authorization checks
- sensitive-column minimization

Never use string interpolation for SQL values.

Unsafe:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

Safe parameter binding:

```python
cursor.execute(
    "SELECT id, email FROM users WHERE email = %s",
    (email,),
)
```

Security is part of query correctness in a production backend.

---

## Reliability Practice

For production-oriented exercises, ask:

- What happens if the query times out?
- What happens if the transaction is retried?
- What happens if the connection fails after commit?
- What happens if the primary database fails?
- What happens if the replica is behind?
- What happens if the worker executes the operation twice?
- What happens if two requests modify the same row?

This develops the habit of designing SQL for failure rather than only for the successful path.

---

## Observability Practice

Relevant PostgreSQL tools include:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query_start,
    query
FROM pg_stat_activity
WHERE state <> 'idle';
```

For lock diagnosis:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

For query workload analysis, practice using `pg_stat_statements` where available.

Track:

- query latency
- execution count
- total execution time
- rows returned
- database CPU
- I/O
- lock waits
- connection utilization
- replica lag
- temporary-file activity

---

## Production Architecture Thinking

SQL should be evaluated as one component in the complete request path.

```mermaid
flowchart LR
    Client --> Nginx
    Nginx --> API[Backend API]
    API --> Pool[Connection Pool]
    Pool --> PostgreSQL
    API --> Redis
    API --> Kafka
    Kafka --> Worker[Celery / Workers]
    Worker --> PostgreSQL
    PostgreSQL --> Replica[Read Replica]
    PostgreSQL --> Analytics[OLAP / Warehouse]
```

A query optimization problem can therefore originate outside the SQL statement itself.

For example:

```text
Slow API
  ↓
Many concurrent requests
  ↓
Connection pool saturation
  ↓
More active database sessions
  ↓
Lock contention
  ↓
Higher query latency
  ↓
Retries
  ↓
More database load
```

Senior troubleshooting requires recognizing this feedback loop.

---

## SQL Exercise Review Questions

For every advanced exercise, ask:

### Correctness

- What exactly should one row represent?
- Can the query duplicate rows?
- What happens with `NULL`?
- What happens when there are no related records?
- Are ties handled correctly?

### Performance

- What is the expected cardinality?
- Which access path should PostgreSQL use?
- What indexes support the query?
- Could the query become expensive as data grows?
- Is the result unnecessarily large?

### Concurrency

- Can multiple requests execute this simultaneously?
- Is there a race condition?
- Does the transaction protect the invariant?
- Can locks be held longer than necessary?
- Can retries safely repeat the operation?

### Security

- Are parameters bound safely?
- Is authorization enforced?
- Is tenant isolation correct?
- Are sensitive columns unnecessarily exposed?

### Operations

- What happens under database load?
- What happens during failover?
- Is replica lag relevant?
- Are timeouts defined?
- Can the operation be safely retried?

---

## Interview Preparation

The exercises should prepare for questions such as:

- Explain why this JOIN returns duplicate rows.
- Rewrite this query using `EXISTS`.
- Find the latest record per customer.
- Calculate a running total.
- Find the top N records per group.
- Explain `WHERE` versus `HAVING`.
- Explain `ROW_NUMBER()` versus `RANK()`.
- Explain `NOT IN` and `NULL`.
- Design an index for this API query.
- Explain why PostgreSQL chooses a sequential scan.
- Optimize a slow query using `EXPLAIN ANALYZE`.
- Implement safe pagination for millions of rows.
- Prevent an inventory race condition.
- Explain how a deadlock can occur.
- Decide whether a read replica solves a performance problem.
- Design a transaction for a business operation.
- Diagnose a production database with high CPU.
- Explain how connection pools affect database capacity.
- Design tenant isolation.
- Decide when to use PostgreSQL versus Redis or an analytical system.

A strong interview answer should explain **why**, not only provide SQL syntax.

---

## Recommended Practice Loop

Use the following loop consistently:

```text
Read requirement
      ↓
Define result grain
      ↓
Identify relationships
      ↓
Write SQL independently
      ↓
Test normal cases
      ↓
Test edge cases
      ↓
Review correctness
      ↓
Inspect execution plan
      ↓
Evaluate indexes
      ↓
Consider concurrency
      ↓
Consider security
      ↓
Consider backend integration
      ↓
Re-solve later
```

The same workflow applies whether the problem is a five-line SQL question or a production incident.

---

## Definition of Mastery

A SQL exercise is considered mastered when the engineer can:

- Solve it independently.
- Explain why the query works.
- Explain why plausible alternatives may fail.
- Identify relevant edge cases.
- Predict cardinality.
- Discuss performance.
- Explain required indexes.
- Identify concurrency concerns where applicable.
- Explain security implications.
- Integrate the query safely into a backend service.

For production scenarios, mastery additionally requires explaining:

- failure modes
- observability
- mitigation
- recovery
- scaling
- deployment implications

---

## Practice Environment Guidelines

Keep development and practice environments isolated from production credentials and data.

Recommended approach:

- PostgreSQL in Docker for local exercises.
- Synthetic or sanitized datasets.
- Separate database users for application and administrative work.
- Version-controlled schema and seed data.
- Repeatable database setup.
- Explicit migrations.
- Query plans captured for important optimization exercises.

Avoid copying production credentials or sensitive production datasets into a local practice environment.

---

## Production Readiness Checklist

Before considering the practice section complete:

### SQL

- [ ] Core SQL is fluent.
- [ ] JOINs and cardinality are understood.
- [ ] Aggregation is reliable.
- [ ] `NULL` semantics are understood.
- [ ] Subqueries and CTEs are comfortable.
- [ ] Window functions are comfortable.
- [ ] Date/time behavior is understood.

### Performance

- [ ] Indexes can be designed from query patterns.
- [ ] `EXPLAIN` can be interpreted.
- [ ] `EXPLAIN ANALYZE` can be used safely.
- [ ] Cardinality estimation is understood.
- [ ] Slow-query diagnosis is systematic.

### Backend

- [ ] Transactions are designed around invariants.
- [ ] Concurrency races can be identified.
- [ ] Pagination is implemented correctly.
- [ ] ORM-generated SQL can be inspected.
- [ ] Connection pool behavior is understood.
- [ ] Replica consistency is understood.

### Production

- [ ] Lock contention can be diagnosed.
- [ ] Deadlocks can be explained and mitigated.
- [ ] High CPU can be investigated.
- [ ] Connection exhaustion can be investigated.
- [ ] Large migrations can be reasoned about.
- [ ] Database scaling decisions can be justified.
- [ ] Security and tenant isolation are considered.
- [ ] Recovery and failure scenarios are considered.

---

## Architecture Decision Heuristic

When solving a production SQL problem, use this decision sequence:

```text
Can PostgreSQL solve it efficiently?
        |
       Yes
        ↓
Can the query be made correct and bounded?
        |
       Yes
        ↓
Can indexes / schema / query design support it?
        |
       Yes
        ↓
Can the workload fit within database capacity?
        |
       Yes
        ↓
Keep it in PostgreSQL

       No
        ↓
Can caching reduce repeated reads?
        |
       Yes → Redis / application cache

       No
        ↓
Can workload be separated?
        |
       Yes → Replica / read model / OLAP

       No
        ↓
Can data be partitioned?
        |
       Yes → Partitioning

       No
        ↓
Can data be distributed?
        |
       Yes → Sharding / service decomposition

       No
        ↓
Reconsider workload architecture
```

The preferred architecture is generally the **simplest architecture that safely satisfies the workload**.

---

## Key Takeaways

- **Practice should build reasoning, not syntax memory:** define result grain, understand cardinality, validate edge cases, and select SQL constructs based on semantics.
- **Progress from queries to systems:** indexing, execution plans, transactions, concurrency, pagination, connection pools, replicas, and backend integration turn SQL knowledge into production capability.
- **Measure mastery through independent problem solving:** re-solving difficult exercises and explaining alternative approaches provides a stronger signal than simply marking exercises complete.
- **Treat production SQL as a systems problem:** query behavior interacts with application concurrency, infrastructure, caching, workers, replication, security, and workload growth.
- **The final objective is engineering judgment:** know when to optimize PostgreSQL, when to change the schema or query, and when the workload requires a different architectural component.