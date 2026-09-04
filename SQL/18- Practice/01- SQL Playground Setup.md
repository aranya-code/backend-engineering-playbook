# 01- SQL Playground Setup

## Overview

A SQL playground is a controlled environment for writing, executing, debugging, and benchmarking SQL without risking production data.

For backend engineering practice, the playground should be more than a database client. It should provide:

- A real PostgreSQL database.
- Repeatable schema and seed data.
- A predictable way to reset the environment.
- Representative relationships and data distributions.
- Query execution and inspection tools.
- `EXPLAIN` and `EXPLAIN ANALYZE` support.
- A workflow that works alongside Python, Django, and FastAPI.
- Version-controlled setup and exercises.

The objective is to make SQL practice reproducible:

```text
Schema
   ↓
Seed Data
   ↓
SQL Query
   ↓
Result
   ↓
EXPLAIN / EXPLAIN ANALYZE
   ↓
Optimization
   ↓
Re-run
```

A good playground should make it easy to answer not only:

> "Does this query work?"

but also:

> "Why does it work, how does PostgreSQL execute it, and how will it behave at production scale?"

---

## Recommended Playground Architecture

For backend-oriented SQL practice, PostgreSQL is the preferred database because it exposes the concepts most relevant to production backend systems.

A simple local architecture is:

```mermaid
flowchart LR
    Developer[Developer] --> Client[psql / DBeaver / IDE]
    Developer --> Python[Python / Django / FastAPI]

    Client --> PostgreSQL[(PostgreSQL)]
    Python --> PostgreSQL

    PostgreSQL --> Data[(Practice Data)]
```

A Docker-based setup keeps the environment isolated from the host operating system:

```mermaid
flowchart TB
    Host[Developer Machine]
    Host --> Docker[Docker]
    Docker --> PG[(PostgreSQL Container)]
    Docker --> Admin[Optional DB Admin UI]
    Host --> SQL[SQL Files]
    Host --> Python[Python Practice Code]
    SQL --> PG
    Python --> PG
```

For most SQL interview preparation, a single PostgreSQL container is sufficient. Kubernetes, replicas, Kafka, Redis, and other infrastructure should only be introduced when practicing the corresponding production scenario.

---

## Why PostgreSQL

PostgreSQL is a strong choice for the playground because it provides:

| Capability | Why it matters |
|---|---|
| Standard SQL | Builds transferable SQL knowledge |
| Advanced SQL | CTEs, window functions, recursive queries, `LATERAL` |
| Transactions | Useful for concurrency practice |
| MVCC | Important for backend architecture |
| Rich indexes | B-tree, GIN, GiST, BRIN, partial and expression indexes |
| `EXPLAIN` | Execution-plan analysis |
| Constraints | Database-enforced correctness |
| Roles and privileges | Security practice |
| JSON/JSONB | Common backend workload |
| Partitioning | Production-scale design practice |
| Replication support | Useful for architecture exercises |

The playground should primarily teach PostgreSQL concepts while keeping SQL knowledge portable where practical.

---

## Directory Structure

Keep the playground version-controlled.

A practical structure is:

```text
sql-playground/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── db/
│   ├── migrations/
│   ├── schema.sql
│   ├── seed.sql
│   └── reset.sql
├── queries/
│   ├── fundamentals/
│   ├── joins/
│   ├── aggregation/
│   ├── subqueries/
│   ├── window-functions/
│   ├── transactions/
│   ├── performance/
│   └── troubleshooting/
├── exercises/
│   ├── beginner/
│   ├── intermediate/
│   └── senior/
└── scripts/
    ├── reset-db.sh
    └── seed-db.sh
```

The exact structure is less important than consistency and reproducibility.

---

## Docker Setup

A local PostgreSQL container is usually the simplest setup.

Example:

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: sql_playground
      POSTGRES_USER: playground
      POSTGRES_PASSWORD: playground
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Start the database:

```bash
docker compose up -d
```

Check the container:

```bash
docker compose ps
```

Connect using `psql`:

```bash
docker compose exec postgres \
  psql -U playground -d sql_playground
```

The exact PostgreSQL image version can be pinned to the version used by the target production environment or interview exercises.

---

## Environment Configuration

For local development, credentials should still be separated from source code conventions.

Example `.env.example`:

```dotenv
POSTGRES_DB=sql_playground
POSTGRES_USER=playground
POSTGRES_PASSWORD=playground
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Do not commit real credentials.

A local playground password is low risk when the database is isolated and contains synthetic data, but maintaining good credential hygiene makes the workflow transferable to real projects.

Add local secrets to `.gitignore`:

```gitignore
.env
*.local
```

---

## Database Connection

A connection has several layers:

```text
SQL Client
    ↓
PostgreSQL Driver / Protocol
    ↓
TCP
    ↓
PostgreSQL Server
    ↓
Session
    ↓
Query
    ↓
Result
```

Using `psql`:

```bash
psql \
  "host=localhost port=5432 dbname=sql_playground user=playground"
```

Inside `psql`, useful commands include:

```text
\conninfo
\dt
\d customers
\di
\timing
\x
```

Examples:

```sql
SELECT version();

SELECT current_database();

SELECT current_user;
```

These commands help establish exactly which database and user are being used before debugging a query.

---

## Create a Practice Schema

A backend-oriented playground should contain more than one isolated table.

A useful initial model is:

```mermaid
erDiagram
    customers ||--o{ orders : places
    orders ||--|{ order_items : contains
    products ||--o{ order_items : included_in
    customers ||--o{ addresses : owns

    customers {
        bigint id PK
        text email UK
        text name
        text status
        timestamptz created_at
    }

    orders {
        bigint id PK
        bigint customer_id FK
        text status
        numeric total_amount
        timestamptz created_at
    }

    order_items {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        integer quantity
        numeric unit_price
    }

    products {
        bigint id PK
        text sku UK
        text name
        numeric price
        boolean active
    }

    addresses {
        bigint id PK
        bigint customer_id FK
        text city
        text country
        boolean is_default
    }
```

This model supports realistic exercises involving:

- One-to-many relationships.
- Many-to-many relationships through `order_items`.
- Aggregation.
- Joins.
- Existence queries.
- Window functions.
- Pagination.
- Constraints.
- Indexing.
- Transactions.
- Concurrency.
- Reporting queries.

---

## Schema Definition

A compact starting schema:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku text NOT NULL UNIQUE,
    name text NOT NULL,
    price numeric(12, 2) NOT NULL CHECK (price >= 0),
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id),
    status text NOT NULL,
    total_amount numeric(12, 2) NOT NULL CHECK (total_amount >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL
        REFERENCES orders(id),
    product_id bigint NOT NULL
        REFERENCES products(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE addresses (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id),
    city text NOT NULL,
    country text NOT NULL,
    is_default boolean NOT NULL DEFAULT false
);
```

This schema intentionally includes constraints so SQL exercises can also demonstrate database-enforced correctness.

---

## Seed Data

Seed data should be deterministic enough that queries can be reproduced.

Example:

```sql
INSERT INTO customers (email, name, status)
VALUES
    ('alice@example.com', 'Alice', 'active'),
    ('bob@example.com', 'Bob', 'active'),
    ('carol@example.com', 'Carol', 'inactive');

INSERT INTO products (sku, name, price, active)
VALUES
    ('SKU-001', 'Keyboard', 80.00, true),
    ('SKU-002', 'Mouse', 35.00, true),
    ('SKU-003', 'Monitor', 250.00, true);

INSERT INTO orders (customer_id, status, total_amount)
VALUES
    (1, 'completed', 115.00),
    (1, 'completed', 250.00),
    (2, 'pending', 35.00);

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
VALUES
    (1, 1, 1, 80.00),
    (1, 2, 1, 35.00),
    (2, 3, 1, 250.00),
    (3, 2, 1, 35.00);
```

Seed data should eventually include:

- Customers with no orders.
- Customers with many orders.
- Duplicate timestamps.
- `NULL` values where semantically valid.
- Multiple products per order.
- Inactive records.
- Large tenants or high-volume customers.
- Different statuses.
- Historical records.

These cases make exercises more realistic.

---

## Resettable Environment

A practice database should be easy to destroy and recreate.

For Docker:

```bash
docker compose down -v
docker compose up -d
```

This removes the database volume and starts from a clean state.

For a SQL-level reset:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

Then reload the schema and seed data.

Do not depend on manually modifying the database into a desired state. Reproducibility is more valuable than preserving local state.

---

## Migration-Based Setup

For larger exercises, use migrations instead of one enormous schema file.

A migration sequence might be:

```text
001_create_customers.sql
002_create_products.sql
003_create_orders.sql
004_create_order_items.sql
005_create_addresses.sql
006_add_indexes.sql
```

This allows you to practice:

- Migration ordering.
- Backward-compatible schema changes.
- Index deployment.
- Constraint deployment.
- Data backfills.
- Rollback planning.

This becomes especially useful when the playground is used for production migration exercises.

---

## Useful `psql` Commands

| Command | Purpose |
|---|---|
| `\l` | List databases |
| `\c database` | Connect to database |
| `\dt` | List tables |
| `\d table` | Describe table |
| `\di` | List indexes |
| `\du` | List roles |
| `\dn` | List schemas |
| `\timing` | Toggle query timing |
| `\x` | Toggle expanded output |
| `\q` | Quit |
| `\i file.sql` | Execute SQL file |
| `\copy` | Import/export through client |

For example:

```text
\i db/schema.sql
\i db/seed.sql
```

---

## Query Timing

Enable timing when practicing performance:

```text
\timing on
```

Then:

```sql
SELECT count(*)
FROM orders;
```

You can compare query execution time before and after an optimization.

However, wall-clock time from a small local database is not enough to prove scalability.

For serious performance analysis, inspect the execution plan.

---

## EXPLAIN

`EXPLAIN` shows the planned execution strategy without executing the query.

```sql
EXPLAIN
SELECT *
FROM orders
WHERE customer_id = 1;
```

For actual execution:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 1;
```

Use `ANALYZE` carefully because it actually executes the statement.

For read queries this is usually straightforward. For `UPDATE` or `DELETE`, use transactions when experimenting:

```sql
BEGIN;

EXPLAIN (ANALYZE, BUFFERS)
DELETE FROM orders
WHERE customer_id = 1;

ROLLBACK;
```

This still executes the statement inside the transaction, so the database workload and side effects of triggers or other operations must be considered.

---

## Generate Representative Data

A tiny dataset can hide important performance behavior.

For example:

```sql
INSERT INTO customers (email, name)
SELECT
    'customer-' || n || '@example.com',
    'Customer ' || n
FROM generate_series(1, 100000) AS n;
```

Generate orders:

```sql
INSERT INTO orders (
    customer_id,
    status,
    total_amount,
    created_at
)
SELECT
    floor(random() * 100000 + 1)::bigint,
    CASE
        WHEN random() < 0.7 THEN 'completed'
        WHEN random() < 0.9 THEN 'pending'
        ELSE 'cancelled'
    END,
    round((random() * 1000)::numeric, 2),
    now() - (random() * interval '365 days')
FROM generate_series(1, 1000000);
```

The exact distribution matters.

Random data is useful for scale, but realistic distributions are better for studying:

- Selectivity.
- Skew.
- Hot customers.
- Common statuses.
- Recent-vs-historical access patterns.
- Index usefulness.

---

## Statistics

PostgreSQL's planner relies on statistics.

After generating substantial data:

```sql
ANALYZE customers;
ANALYZE orders;
ANALYZE products;
ANALYZE order_items;
```

Inspect statistics:

```sql
SELECT
    tablename,
    attname,
    n_distinct,
    most_common_vals,
    histogram_bounds
FROM pg_stats
WHERE tablename = 'orders';
```

Understanding statistics is essential when practicing:

- Cardinality estimation.
- Index selection.
- Join strategy.
- Query-plan changes.

---

## Index Practice

Start without unnecessary indexes.

Then create indexes based on actual query patterns.

Example:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

Test:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 42;
```

Then consider composite access patterns:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

Use the playground to learn that an index is not automatically beneficial.

The planner considers:

- Selectivity.
- Estimated row count.
- Table size.
- Random versus sequential I/O.
- Cache behavior.
- Ordering requirements.
- Query cost.

---

## Transaction Practice

The playground should allow multiple PostgreSQL sessions.

Open two terminals:

```bash
docker compose exec postgres \
  psql -U playground -d sql_playground
```

Then reproduce concurrency scenarios:

```text
Session A                 Session B
---------                 ---------
BEGIN                     BEGIN
UPDATE ...                UPDATE ...
       ↓
lock acquired             waits
COMMIT                    continues
```

Practice:

- Lost updates.
- Row locks.
- Deadlocks.
- Isolation levels.
- `NOWAIT`.
- `SKIP LOCKED`.
- Serialization failures.

Example:

```sql
BEGIN;

SELECT id, quantity
FROM inventory
WHERE id = 1
FOR UPDATE;
```

The value of the playground is that concurrency can be observed rather than merely discussed.

---

## Lock Inspection

During concurrency exercises, inspect PostgreSQL:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE datname = current_database();
```

Inspect locks:

```sql
SELECT
    pid,
    locktype,
    mode,
    granted,
    relation::regclass
FROM pg_locks
WHERE pid <> pg_backend_pid();
```

For blocking relationships:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    query
FROM pg_stat_activity
WHERE datname = current_database();
```

These queries are useful for learning how database-level behavior maps to backend symptoms.

---

## SQL Security Practice

The playground can safely include security exercises using separate roles.

Example:

```sql
CREATE ROLE app_readonly LOGIN PASSWORD 'readonly-password';

GRANT CONNECT ON DATABASE sql_playground
TO app_readonly;

GRANT USAGE ON SCHEMA public
TO app_readonly;

GRANT SELECT ON ALL TABLES IN SCHEMA public
TO app_readonly;
```

Test the role:

```sql
SET ROLE app_readonly;

SELECT *
FROM customers;

RESET ROLE;
```

Practice:

- `GRANT`.
- `REVOKE`.
- Read-only roles.
- Least privilege.
- Schema privileges.
- RLS.
- SQL injection prevention.
- Parameterized queries.

Never use production credentials in the playground.

---

## Python Integration

A lightweight Python client can be useful when practicing SQL outside an ORM.

For example, with `psycopg`:

```python
import psycopg

with psycopg.connect(
    "host=localhost port=5432 dbname=sql_playground user=playground password=playground"
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, email
            FROM customers
            WHERE status = %s
            ORDER BY id
            """,
            ("active",),
        )

        for row in cursor:
            print(row)
```

This is useful for understanding the boundary between:

```text
Python
  ↓
Database Driver
  ↓
PostgreSQL Protocol
  ↓
SQL
  ↓
Execution Plan
  ↓
Rows
```

Values should be passed as parameters rather than interpolated into SQL.

---

## Django Integration

When SQL practice needs ORM context, create a separate Django project or connect Django to the playground database.

Typical configuration:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sql_playground",
        "USER": "playground",
        "PASSWORD": "playground",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

Practice mapping ORM operations to SQL:

```python
orders = (
    Order.objects
    .filter(customer_id=customer_id)
    .order_by("-created_at")
)
```

Inspect generated SQL:

```python
print(orders.query)
```

For performance exercises, compare:

```python
Order.objects.select_related("customer")
```

with:

```python
Order.objects.all()
```

and inspect query counts.

The purpose is to understand that ORM abstractions ultimately produce database operations that must still be analyzed.

---

## FastAPI and SQLAlchemy Integration

A separate FastAPI exercise can use SQLAlchemy with PostgreSQL.

The important concepts are:

- Engine configuration.
- Connection pooling.
- Session lifecycle.
- Transactions.
- Query construction.
- Eager versus lazy loading.
- Exception handling.

Example engine configuration:

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://playground:playground@localhost:5432/sql_playground",
    pool_size=5,
    max_overflow=5,
    pool_timeout=10,
    pool_pre_ping=True,
)
```

The playground can then be used to compare ORM behavior with direct SQL.

---

## Query Organization

Store important queries in version control.

For example:

```text
queries/
├── joins/
│   ├── customers_with_orders.sql
│   ├── customers_without_orders.sql
│   └── latest_order_per_customer.sql
├── aggregation/
│   ├── revenue_by_customer.sql
│   └── monthly_revenue.sql
├── window-functions/
│   ├── ranked_orders.sql
│   └── running_revenue.sql
└── performance/
    ├── before_index.sql
    └── after_index.sql
```

Keep performance experiments paired with their explanation.

For example:

```text
before_index.sql
after_index.sql
README.md
```

The README can document:

- Original query.
- Original plan.
- Problem.
- Index or rewrite.
- New plan.
- Measured result.
- Trade-offs.

---

## Query Practice Workflow

Use a consistent workflow for every exercise.

```text
Read requirement
      ↓
Inspect schema
      ↓
Define result grain
      ↓
Write query
      ↓
Test expected results
      ↓
Test edge cases
      ↓
Inspect generated SQL if using ORM
      ↓
EXPLAIN
      ↓
Consider indexes
      ↓
Test representative data
      ↓
Evaluate concurrency
      ↓
Document trade-offs
```

This turns SQL exercises into engineering practice rather than syntax drills.

---

## Exercises by Difficulty

### Beginner

Practice:

- `SELECT`.
- `WHERE`.
- `ORDER BY`.
- `LIMIT`.
- `DISTINCT`.
- Basic joins.
- Basic aggregation.
- `CASE`.
- `NULL`.

Example:

> Find all active customers created in the last 30 days.

### Intermediate

Practice:

- Multi-table joins.
- `EXISTS`.
- Subqueries.
- CTEs.
- Window functions.
- Conditional aggregation.
- Pagination.
- Upserts.

Example:

> Return the latest order for every customer.

### Advanced

Practice:

- Query optimization.
- Locking.
- Transaction isolation.
- Deadlocks.
- Large-table operations.
- Partial indexes.
- Complex reporting queries.
- RLS.
- Concurrent workloads.

Example:

> Design a query that safely reserves inventory when multiple requests can purchase the same product concurrently.

### Senior

Practice:

- Production incidents.
- Query-plan regressions.
- Replica lag.
- Connection exhaustion.
- Hot rows.
- Large migrations.
- Multi-tenant isolation.
- OLTP/OLAP separation.
- Sharding decisions.

Example:

> A Django API endpoint became five times slower after the customer table grew from one million to one hundred million rows. Diagnose the problem and propose a production-safe solution.

---

## Performance Benchmarking

Local benchmarking should be treated as directional rather than production proof.

A useful experiment records:

| Metric | Purpose |
|---|---|
| Planning time | Planning overhead |
| Execution time | Query execution |
| Rows | Result cardinality |
| Buffers | Cache/I/O behavior |
| Query frequency | Aggregate workload |
| CPU | Compute pressure |
| WAL | Write amplification |
| Lock waits | Concurrency impact |

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

When comparing alternatives, keep the following controlled where possible:

- Same dataset.
- Same schema.
- Same indexes.
- Same PostgreSQL version.
- Same query parameters.
- Similar cache state.
- Similar system load.

Avoid concluding that one query is universally faster from a single local measurement.

---

## Cache Effects

PostgreSQL can serve data from memory rather than storage.

Therefore:

```text
First execution
    ↓
May require storage reads

Later execution
    ↓
May benefit from cache
```

Run repeated measurements carefully.

`EXPLAIN (ANALYZE, BUFFERS)` can help identify buffer behavior.

The playground is useful for understanding why a query can appear fast after repeated execution while behaving differently under production workloads.

---

## Data Distribution

Production data is rarely perfectly uniform.

For example:

```text
Customer A → 2 orders
Customer B → 3 orders
Customer C → 50,000 orders
```

The last customer may create a very different execution pattern.

Practice skewed datasets to understand:

- Cardinality estimation.
- Hot partitions.
- Large result sets.
- Index usefulness.
- Query latency variance.

Senior SQL reasoning should consider distribution, not just average behavior.

---

## Query Safety

The playground should also be a place to practice safe SQL.

Unsafe:

```python
query = f"""
SELECT *
FROM customers
WHERE email = '{email}'
"""
```

Safe:

```python
cursor.execute(
    """
    SELECT *
    FROM customers
    WHERE email = %s
    """,
    (email,),
)
```

Parameterized queries protect values from being interpreted as SQL syntax.

Dynamic SQL identifiers require a different strategy, such as controlled allowlists and driver-supported identifier composition.

---

## Destructive Query Practice

Be careful when experimenting with:

```sql
UPDATE
DELETE
DROP
ALTER
TRUNCATE
```

Use transactions where appropriate:

```sql
BEGIN;

UPDATE customers
SET status = 'inactive'
WHERE status = 'active';

SELECT count(*)
FROM customers
WHERE status = 'inactive';

ROLLBACK;
```

Remember that some operations cannot simply be "undone" through a rollback once external effects are involved.

Practice destructive operations only against synthetic data.

---

## Production-Like Scenarios

Once fundamentals are comfortable, introduce realistic constraints.

Examples:

### Slow Query

```text
API latency increased
       ↓
Find database query
       ↓
EXPLAIN ANALYZE
       ↓
Inspect cardinality
       ↓
Inspect indexes
       ↓
Check locks
       ↓
Check query frequency
```

### Connection Pool Exhaustion

```text
API instances
      ↓
Connection pools
      ↓
Too many active connections
      ↓
Database saturation
      ↓
Request failures
```

### Replica Lag

```text
Primary
  ↓ WAL
Replica
  ↓ replay
Read request
  ↓
Possibly stale result
```

### Deadlock

```text
Transaction A
locks Row 1
    ↓
waits for Row 2

Transaction B
locks Row 2
    ↓
waits for Row 1
```

The playground should support reproducing these scenarios with multiple sessions and controlled workloads.

---

## Optional Load Testing

For larger performance exercises, use a load-testing tool rather than manually running queries.

The exact tool is less important than understanding:

- Concurrent clients.
- Requests per second.
- Query latency.
- Error rate.
- Connection utilization.
- CPU.
- I/O.
- Lock waits.

The objective is to understand the difference between:

```text
Single-query optimization
```

and:

```text
Workload optimization
```

A query that is acceptable at one execution per second may be problematic at ten thousand executions per second.

---

## Observability Practice

A useful playground should teach database observability.

Practice inspecting:

```sql
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity;
```

For query statistics, PostgreSQL's `pg_stat_statements` extension is highly useful when enabled.

It allows analysis of:

- Query frequency.
- Total execution time.
- Mean execution time.
- Calls.
- Shared buffer activity.

This bridges the gap between:

```text
"This query is slow."
```

and:

```text
"This query consumes a significant portion of database workload."
```

---

## Reset and Rebuild Workflow

A reliable workflow should make rebuilding cheap.

Example:

```bash
docker compose down -v
docker compose up -d
```

Then:

```bash
docker compose exec postgres \
  psql -U playground -d sql_playground \
  -f /path/to/schema.sql
```

For a container-mounted SQL directory, the process can be automated through Docker initialization scripts or a dedicated setup script.

The important principle is:

> If rebuilding the playground is painful, the environment will eventually become inconsistent.

---

## Automation

A simple reset script:

```bash
#!/usr/bin/env bash

set -euo pipefail

docker compose down -v
docker compose up -d

until docker compose exec -T postgres \
    pg_isready -U playground -d sql_playground >/dev/null 2>&1
do
    sleep 1
done

docker compose exec -T postgres \
    psql -U playground -d sql_playground \
    -f /workspace/db/schema.sql

docker compose exec -T postgres \
    psql -U playground -d sql_playground \
    -f /workspace/db/seed.sql
```

Mount the repository into the container if the SQL files need to be available at `/workspace`.

Automation should make setup deterministic rather than hiding important database behavior.

---

## CI Validation

SQL exercises can also be validated in CI.

A basic pipeline can:

```text
CI Runner
   ↓
Start PostgreSQL
   ↓
Apply schema
   ↓
Load seed data
   ↓
Execute tests
   ↓
Validate query results
```

For a repository containing SQL exercises, CI can detect:

- Broken schema.
- Invalid SQL.
- Migration failures.
- Incorrect expected results.
- Dependency-order problems.

Do not rely only on syntax checks. A query can be syntactically valid and semantically wrong.

---

## Security Considerations

Even a local playground should establish good habits.

- Never use production credentials.
- Never copy production secrets into `.env`.
- Prefer synthetic data.
- Do not store sensitive customer information in Git.
- Avoid committing database dumps containing real personal data.
- Use separate database roles for security exercises.
- Practice parameterized queries.
- Practice least privilege.
- Keep exposed PostgreSQL ports limited to the local machine.

If production data is required for a debugging exercise, use an approved sanitized dataset rather than an unrestricted production dump.

---

## Reliability Considerations

A good playground should be disposable.

The database should be treated as rebuildable infrastructure:

```text
Code
 +
Schema
 +
Seed data
 =
Reproducible environment
```

Do not depend on manually accumulated database state.

For advanced exercises, version:

- Schema.
- Migrations.
- Seed data.
- Benchmark queries.
- Expected results.
- Setup scripts.

This makes experiments repeatable months later.

---

## Cost Considerations

A local Docker PostgreSQL instance is usually sufficient for SQL interview preparation and avoids unnecessary cloud cost.

AWS-hosted PostgreSQL can be useful when practicing:

- RDS operations.
- Cloud networking.
- Backups.
- Monitoring.
- Read replicas.
- IAM integration.
- Production-like resource constraints.

Do not introduce AWS infrastructure simply because the query itself requires PostgreSQL.

For most SQL exercises:

```text
Local PostgreSQL
    >
Cloud database
```

in terms of simplicity, speed, cost, and iteration time.

Use cloud infrastructure when the infrastructure behavior itself is part of the exercise.

---

## Common Mistakes

### Practicing Only Against Tiny Data

A query can look excellent against ten rows and fail at ten million.

**Avoid it:** generate representative datasets.

### Never Looking at Execution Plans

Correct SQL can still perform poorly.

**Avoid it:** use `EXPLAIN` and `EXPLAIN (ANALYZE, BUFFERS)` when performance matters.

### Adding Indexes Everywhere

Indexes have storage and write-maintenance costs.

**Avoid it:** design indexes from actual access patterns.

### Treating ORM Output as a Black Box

ORMs can generate unexpected queries.

**Avoid it:** inspect generated SQL and query counts.

### Ignoring Concurrency

A single SQL session does not expose race conditions.

**Avoid it:** use multiple sessions for transaction and locking exercises.

### Using Production Data

Real customer data introduces security and privacy risks.

**Avoid it:** use synthetic or approved sanitized datasets.

### Manual Database Setup

Manually creating tables produces configuration drift.

**Avoid it:** keep schema and seed data version-controlled.

### Benchmarking Without Context

One local timing measurement does not represent production performance.

**Avoid it:** evaluate plans, workload, data distribution, concurrency, and resource usage.

---

## Practical Playground Checklist

Before starting serious SQL practice:

- [ ] PostgreSQL is running.
- [ ] Database connection is verified.
- [ ] Schema is version-controlled.
- [ ] Seed data is reproducible.
- [ ] Reset workflow works.
- [ ] `psql` is available.
- [ ] Query files are version-controlled.
- [ ] `EXPLAIN` is available.
- [ ] Multiple database sessions can be opened.
- [ ] Python connectivity works if required.
- [ ] Django connectivity works if required.
- [ ] FastAPI/SQLAlchemy connectivity works if required.
- [ ] Synthetic data generation is available.
- [ ] PostgreSQL logs can be inspected when needed.
- [ ] Security exercises use separate roles.
- [ ] No production credentials or sensitive data are present.

---

## Recommended Practice Environment

For backend interview preparation, the following setup is sufficient:

| Component | Recommendation |
|---|---|
| Database | PostgreSQL |
| Local runtime | Docker Compose |
| SQL client | `psql` plus an optional GUI |
| Language integration | Python |
| ORM practice | Django |
| API practice | FastAPI |
| Query analysis | `EXPLAIN (ANALYZE, BUFFERS)` |
| Version control | Git |
| Data | Synthetic |
| Reset strategy | Disposable/reproducible |
| CI | Optional but valuable |
| AWS | Use only for infrastructure-specific practice |

The important capability is not the number of tools. It is the ability to repeatedly move from:

```text
Requirement
→ SQL
→ Result
→ Execution Plan
→ Performance
→ Concurrency
→ Production Decision
```

---

## Interview Practice Standard

For every query-writing exercise, do not stop when the result is correct.

Be able to explain:

```text
What does one output row represent?
Why is the query correct?
What relationships are traversed?
Can joins multiply rows?
How does NULL affect the result?
What happens with duplicate timestamps?
What happens with an empty dataset?
What index supports the query?
What would EXPLAIN likely show?
What happens when the table becomes large?
What happens under concurrent requests?
Could the query cause excessive connection usage?
Should the result come from a replica?
Should the result be cached?
Should the operation be asynchronous?
What security constraints apply?
```

This is the standard that turns SQL practice into senior backend interview preparation.

---

## Key Takeaways

- **Use PostgreSQL as the primary playground:** it provides the SQL, transaction, indexing, execution-plan, security, and concurrency capabilities most relevant to backend engineering.
- **Make the environment reproducible:** version-control schema, seed data, queries, migrations, and reset scripts so every experiment can be recreated reliably.
- **Practice beyond query correctness:** inspect execution plans, generate realistic data, test concurrency, and understand how SQL behaves as workload and dataset size increase.
- **Connect SQL to backend systems:** use Python, Django, FastAPI, transactions, connection pools, and production scenarios to understand how database behavior affects applications.
- **Treat the playground as an engineering laboratory:** use it to move from requirement to query, result, plan, optimization, concurrency analysis, and production decision.