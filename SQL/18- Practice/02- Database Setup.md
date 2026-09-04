# 02- Database Setup

## Overview

A database setup for SQL practice should provide a **repeatable, isolated, realistic PostgreSQL environment** that can be destroyed and recreated without manual intervention.

The goal is not merely to install PostgreSQL. A useful practice environment should support:

- Schema creation and evolution.
- Deterministic seed data.
- SQL query exercises.
- Transactions and concurrency experiments.
- Index and execution-plan analysis.
- Database security exercises.
- Python, Django, and FastAPI integration.
- Performance testing with realistic data volumes.
- Reset and rebuild workflows.
- Version-controlled database configuration.

A practical development flow is:

```text
Repository
    ↓
Docker Compose
    ↓
PostgreSQL
    ↓
Schema / Migrations
    ↓
Seed Data
    ↓
SQL Exercises
    ↓
Application Integration
    ↓
Performance / Concurrency Testing
```

For this playbook, PostgreSQL should be the primary database because it provides a strong environment for practicing both standard SQL and production backend database engineering.

---

## Database Setup Goals

A good setup should satisfy five properties:

| Property | Requirement |
|---|---|
| Reproducible | Another machine can recreate the same environment |
| Disposable | The database can be destroyed safely |
| Isolated | Practice cannot affect production |
| Observable | Queries, plans, locks, and resource usage can be inspected |
| Extensible | The environment can support advanced exercises |

Avoid building a playground that depends on undocumented local configuration.

If the environment cannot be recreated from the repository, it is already accumulating configuration drift.

---

## Recommended Technology Stack

For SQL and backend engineering practice:

| Component | Recommendation |
|---|---|
| Database | PostgreSQL |
| Runtime | Docker |
| Orchestration | Docker Compose |
| SQL client | `psql` |
| Optional GUI | DBeaver or another PostgreSQL client |
| Application language | Python |
| ORM | Django / SQLAlchemy |
| API framework | FastAPI |
| Version control | Git |
| Database setup | SQL migrations |
| Data generation | SQL + Python |
| Query analysis | `EXPLAIN (ANALYZE, BUFFERS)` |

Do not introduce Kubernetes, RDS, Aurora, Kafka, or Redis unless the exercise specifically requires those technologies.

Local infrastructure should remain simple enough that SQL experimentation is fast.

---

## Directory Structure

A practical repository layout is:

```text
sql-playground/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── db/
│   ├── migrations/
│   │   ├── 001_create_customers.sql
│   │   ├── 002_create_products.sql
│   │   ├── 003_create_orders.sql
│   │   └── 004_create_order_items.sql
│   ├── seed/
│   │   ├── 001_reference_data.sql
│   │   └── 002_sample_data.sql
│   └── scripts/
│       ├── reset.sql
│       └── analyze.sql
├── queries/
│   ├── fundamentals/
│   ├── joins/
│   ├── aggregation/
│   ├── subqueries/
│   ├── window-functions/
│   ├── transactions/
│   ├── performance/
│   └── troubleshooting/
├── python/
│   └── requirements.txt
└── scripts/
    ├── db-up.sh
    ├── db-reset.sh
    └── db-seed.sh
```

The structure should make the distinction between **schema**, **data**, **practice queries**, and **operational scripts** obvious.

---

## PostgreSQL with Docker

Docker provides an isolated PostgreSQL instance without requiring a host-level database installation.

A minimal Compose configuration:

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

Start PostgreSQL:

```bash
docker compose up -d
```

Check the service:

```bash
docker compose ps
```

Inspect logs:

```bash
docker compose logs postgres
```

Stop it:

```bash
docker compose down
```

This setup is intentionally simple. The persistent volume means that stopping the container does not automatically delete the database.

---

## Database Connection

Connect using `psql`:

```bash
psql \
  --host localhost \
  --port 5432 \
  --username playground \
  --dbname sql_playground
```

If `psql` is not installed on the host, execute it inside the container:

```bash
docker compose exec postgres \
  psql -U playground -d sql_playground
```

Verify the connection:

```sql
SELECT
    current_database(),
    current_user,
    version();
```

Inside `psql`:

```text
\conninfo
```

This should be one of the first checks whenever debugging connection problems.

---

## Connection Architecture

The local application path is:

```mermaid
flowchart LR
    Client[psql / GUI] --> TCP[localhost:5432]
    Python[Python Application] --> TCP
    TCP --> PostgreSQL[(PostgreSQL Container)]
    PostgreSQL --> Volume[(Docker Volume)]
```

For a backend application:

```text
HTTP Request
    ↓
Nginx / Application Server
    ↓
Django / FastAPI
    ↓
Database Driver
    ↓
TCP Connection
    ↓
PostgreSQL
    ↓
SQL Execution
    ↓
Result
    ↓
Application Response
```

This distinction becomes important later when practicing:

- Connection pooling.
- Transaction boundaries.
- Query latency.
- Network latency.
- Database saturation.
- Lock contention.

---

## Environment Variables

Keep environment-specific configuration outside application source code.

Example `.env.example`:

```dotenv
POSTGRES_DB=sql_playground
POSTGRES_USER=playground
POSTGRES_PASSWORD=playground
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

For local Compose configuration:

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

Create a local `.env` from the example:

```bash
cp .env.example .env
```

Do not commit `.env`:

```gitignore
.env
```

Even though the database is local, maintaining correct secret-handling habits is valuable for production work.

---

## PostgreSQL Version

Pin the PostgreSQL major version used by the playground.

For example:

```yaml
image: postgres:17
```

Avoid:

```yaml
image: postgres:latest
```

A moving tag can silently change the database version and make experiments difficult to reproduce.

For interview preparation, the exact PostgreSQL version is usually less important than understanding the underlying SQL and database behavior.

For production-specific exercises, use a version close to the target environment.

---

## Database Initialization

PostgreSQL Docker images support initialization scripts placed under:

```text
/docker-entrypoint-initdb.d/
```

Example:

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: sql_playground
      POSTGRES_USER: playground
      POSTGRES_PASSWORD: playground
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d
```

Directory:

```text
db/
└── init/
    ├── 001_schema.sql
    └── 002_seed.sql
```

The scripts run when PostgreSQL initializes a **new database directory**.

This is an important operational detail:

> Changing an initialization script does not automatically re-run it against an existing Docker volume.

To initialize from scratch:

```bash
docker compose down -v
docker compose up -d
```

The `-v` removes the named database volume.

---

## Schema Management

For simple experiments, a single `schema.sql` is acceptable.

For a long-lived engineering playbook, migrations are preferable.

Example:

```text
db/migrations/
├── 001_create_customers.sql
├── 002_create_products.sql
├── 003_create_orders.sql
├── 004_create_order_items.sql
└── 005_add_indexes.sql
```

Migration ordering should reflect dependencies:

```text
customers
    ↓
orders
    ↓
order_items
    ↓
indexes / constraints
```

This provides a realistic environment for learning database deployment practices.

---

## Practice Schema

A useful SQL playground should model a small backend domain.

Example:

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
```

This supports realistic SQL questions involving:

- Joins.
- Aggregation.
- Foreign keys.
- Constraints.
- Subqueries.
- Window functions.
- Transactions.
- Indexes.
- Data integrity.

---

## Seed Data

A small deterministic seed is useful for correctness exercises.

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

A good seed dataset should deliberately contain edge cases.

For example:

- Customer with no orders.
- Customer with multiple orders.
- Product with no order items.
- Inactive product.
- Multiple order items for one order.
- Duplicate timestamps.
- `NULL` values where appropriate.
- Large and small numeric values.

These cases expose incorrect assumptions in SQL queries.

---

## Data Volume

Small seed data is insufficient for performance exercises.

Generate larger datasets separately.

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
        WHEN random() < 0.70 THEN 'completed'
        WHEN random() < 0.90 THEN 'pending'
        ELSE 'cancelled'
    END,
    round((random() * 1000)::numeric, 2),
    now() - random() * interval '365 days'
FROM generate_series(1, 1000000);
```

Then refresh statistics:

```sql
ANALYZE customers;
ANALYZE orders;
```

Large datasets allow you to practice:

- Sequential scans.
- Index scans.
- Bitmap scans.
- Join strategy changes.
- Sorting.
- Aggregation.
- Partitioning.
- Query-plan regressions.

---

## Deterministic Versus Random Data

Both types of data are useful.

| Data type | Best use |
|---|---|
| Deterministic | Query correctness |
| Random | Scale testing |
| Skewed | Cardinality and hot-key behavior |
| Time-distributed | Date queries and partitioning |
| Highly repetitive | Low-selectivity index testing |

Purely random data does not always resemble production.

For example, a real system might have:

```text
1% of customers → 50% of traffic
```

A uniform random distribution would hide this behavior.

---

## Database Reset

A practice database should be disposable.

The simplest full reset is:

```bash
docker compose down -v
docker compose up -d
```

If initialization scripts are configured, they will execute against the new database directory.

For a schema-only reset:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

Then reapply the schema and seed data.

A reset should not require manually remembering dozens of SQL statements.

---

## Reset Script

A shell script can standardize the workflow:

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

The repository must mount `/workspace` if the SQL files are expected at that path.

Automation is valuable because it makes experiments repeatable.

---

## PostgreSQL Configuration

The default PostgreSQL configuration is adequate for most SQL exercises.

Avoid immediately tuning:

- `shared_buffers`.
- `work_mem`.
- `maintenance_work_mem`.
- `effective_cache_size`.
- `max_connections`.

First understand the workload.

Configuration experiments become useful later when studying:

- Memory behavior.
- Query planning.
- Connection scaling.
- Sort/hash operations.
- Production resource constraints.

Do not copy production PostgreSQL configuration blindly into a laptop.

---

## Useful PostgreSQL Extensions

Extensions can be enabled when required by an exercise.

For example:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

This supports query workload analysis.

Verify:

```sql
SELECT *
FROM pg_extension;
```

Other extensions can be added for specialized exercises, but keep the base environment minimal.

---

## Query Analysis

Enable timing in `psql`:

```text
\timing on
```

Run:

```sql
SELECT count(*)
FROM orders;
```

For plan analysis:

```sql
EXPLAIN
SELECT *
FROM orders
WHERE customer_id = 42;
```

For actual execution:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 42;
```

Remember:

> `EXPLAIN` plans a statement; `EXPLAIN ANALYZE` executes it.

Use particular caution with:

```sql
UPDATE
DELETE
INSERT
```

When appropriate, test destructive statements inside a transaction:

```sql
BEGIN;

DELETE FROM orders
WHERE customer_id = 42;

ROLLBACK;
```

The statement still executes inside the transaction, so triggers and other side effects should be understood before using this technique.

---

## Transaction Practice

A database setup should support multiple concurrent sessions.

Open two shells:

```bash
docker compose exec postgres \
    psql -U playground -d sql_playground
```

Then reproduce transaction behavior.

Session A:

```sql
BEGIN;

UPDATE orders
SET status = 'processing'
WHERE id = 1;
```

Session B:

```sql
BEGIN;

UPDATE orders
SET status = 'cancelled'
WHERE id = 1;
```

Session B may wait for Session A depending on the operations and timing.

Commit Session A:

```sql
COMMIT;
```

Then observe Session B.

This provides practical experience with row-level locking and transaction concurrency.

---

## Lock Inspection

During concurrency exercises:

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

Find blocking sessions:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    query
FROM pg_stat_activity
WHERE datname = current_database();
```

These queries should become familiar when preparing for senior backend interviews.

---

## Database Roles

Create separate roles when practicing database security.

Example:

```sql
CREATE ROLE app_runtime
    LOGIN
    PASSWORD 'runtime-password';

CREATE ROLE app_readonly
    LOGIN
    PASSWORD 'readonly-password';

CREATE ROLE app_migration
    LOGIN
    PASSWORD 'migration-password';
```

In a real environment, passwords should come from a proper secret-management system.

Grant only the required permissions:

```sql
GRANT CONNECT ON DATABASE sql_playground
TO app_readonly;

GRANT USAGE ON SCHEMA public
TO app_readonly;

GRANT SELECT ON ALL TABLES IN SCHEMA public
TO app_readonly;
```

Practice:

```sql
SET ROLE app_readonly;

SELECT *
FROM customers;

RESET ROLE;
```

This environment can later support exercises on:

- `GRANT`.
- `REVOKE`.
- Least privilege.
- RLS.
- Application users.
- Migration roles.

---

## Python Connectivity

Install the PostgreSQL driver:

```bash
pip install "psycopg[binary]"
```

Connect:

```python
import psycopg

with psycopg.connect(
    "host=localhost port=5432 dbname=sql_playground "
    "user=playground password=playground"
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

This demonstrates the boundary between application code and SQL.

The application should pass values as parameters rather than constructing SQL through string interpolation.

---

## Django Connectivity

A Django project can use the same PostgreSQL instance.

Example:

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

Inspect the generated SQL:

```python
print(orders.query)
```

For more advanced analysis, compare query counts and execution plans.

The purpose is not to replace SQL with ORM knowledge. It is to understand the SQL generated by the application.

---

## FastAPI and SQLAlchemy

A FastAPI application can connect using SQLAlchemy:

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

This provides a useful environment for practicing:

- Connection pooling.
- Transaction boundaries.
- Query construction.
- ORM behavior.
- Eager loading.
- Lazy loading.
- Exception handling.

The database setup remains the same; only the application layer changes.

---

## SQL Client Options

`psql` should remain part of the workflow even if a GUI is preferred.

| Client | Strength |
|---|---|
| `psql` | Automation and direct database interaction |
| DBeaver | Rich database exploration |
| IDE database tools | Convenient development workflow |
| Python | Application-level experiments |
| Django shell | ORM-to-SQL investigation |

A senior backend engineer should be comfortable working without a GUI.

---

## Database Introspection

Useful commands:

```text
\dt
\d customers
\di
\dn
\du
```

Useful SQL:

```sql
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;
```

List indexes:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

Introspection is an important part of debugging because you should verify the database state instead of assuming it.

---

## Practice Indexes

Create indexes based on query patterns.

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

Then experiment with composite indexes:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

Use these exercises to understand:

- Selectivity.
- Composite-index column order.
- Index-only scans.
- Bitmap scans.
- Partial indexes.
- Expression indexes.
- Write amplification.

Do not treat "add an index" as the universal performance solution.

---

## Query Exercise Workflow

Every exercise should follow a consistent process:

1. Read the requirement.
2. Inspect the schema.
3. Define the result grain.
4. Identify table relationships.
5. Write the query.
6. Test normal cases.
7. Test edge cases.
8. Inspect the generated SQL if using an ORM.
9. Run `EXPLAIN`.
10. Add or modify indexes only when justified.
11. Test with representative data.
12. Consider concurrency and production behavior.

This process is more valuable than memorizing SQL patterns.

---

## Production-Like Exercises

The setup should eventually support scenarios such as:

### Slow Query

```text
API latency increases
        ↓
Identify database query
        ↓
Inspect pg_stat_statements
        ↓
Run EXPLAIN ANALYZE
        ↓
Check cardinality
        ↓
Check indexes
        ↓
Check locks
        ↓
Optimize
```

### Connection Exhaustion

```text
Multiple application instances
        ↓
Connection pools
        ↓
Too many database sessions
        ↓
Memory / CPU pressure
        ↓
Request failures
```

### Deadlock

```text
Transaction A
    ↓
Locks Row 1
    ↓
Waits for Row 2

Transaction B
    ↓
Locks Row 2
    ↓
Waits for Row 1
```

### Replica Lag

```text
Primary
   ↓ WAL
Replica
   ↓ replay
Read request
   ↓
Potentially stale result
```

These scenarios bridge SQL knowledge with backend architecture.

---

## Performance Data

A production-oriented playground should provide several data scales.

| Dataset | Purpose |
|---|---|
| 10–100 rows | Query correctness |
| 10K rows | Basic performance |
| 100K rows | Index and join experiments |
| 1M+ rows | Execution-plan behavior |
| Highly skewed data | Cardinality and hot-key analysis |

The exact volume depends on available hardware.

Do not assume that local execution time represents production performance.

Instead, focus on:

- Execution plans.
- Buffer activity.
- Row estimates.
- Actual rows.
- CPU.
- I/O.
- Query frequency.
- Concurrency.

---

## Security Considerations

The playground should reinforce production security habits.

### Never Use Production Credentials

Do not connect the playground to production databases.

### Do Not Commit Secrets

Avoid:

```text
.env
database dumps
private certificates
production connection strings
```

### Use Synthetic Data

Synthetic data is preferred for exercises.

If production-derived data is absolutely required, it should be properly sanitized and approved.

### Practice Least Privilege

Use different roles for:

- Application runtime.
- Read-only access.
- Migrations.
- Administration.

### Practice Parameterized Queries

Unsafe:

```python
query = f"SELECT * FROM customers WHERE email = '{email}'"
```

Safe:

```python
cursor.execute(
    "SELECT * FROM customers WHERE email = %s",
    (email,),
)
```

---

## Reliability Considerations

The database should be treated as disposable infrastructure.

The source of truth should be:

```text
Git
├── Database schema
├── Migrations
├── Seed data
├── Query exercises
└── Automation
```

Not:

```text
Developer's local PostgreSQL instance
```

This distinction matters because manual database state becomes impossible to reproduce reliably.

---

## CI Validation

A SQL repository can validate database setup automatically.

A typical CI workflow is:

```mermaid
flowchart LR
    Commit[Git Commit] --> CI[CI Runner]
    CI --> Start[Start PostgreSQL]
    Start --> Schema[Apply Schema]
    Schema --> Seed[Load Seed Data]
    Seed --> Tests[Execute SQL Tests]
    Tests --> Result[Validate Results]
```

CI can detect:

- Invalid migrations.
- Broken schema dependencies.
- Incorrect seed data.
- Invalid SQL.
- Changed query results.

For advanced exercises, CI can also run selected performance or regression checks.

Do not make CI depend on a developer's local PostgreSQL installation.

---

## Health Checks

Docker Compose can include a PostgreSQL health check:

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
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U playground -d sql_playground"
        ]
      interval: 5s
      timeout: 5s
      retries: 5
```

This is useful when another service depends on PostgreSQL during local integration testing.

A container being "running" does not necessarily mean PostgreSQL is ready to accept connections.

---

## Backup and Recovery Practice

A local playground does not require elaborate backup infrastructure, but learning the mechanics is useful.

Logical backup:

```bash
pg_dump \
  -h localhost \
  -U playground \
  -d sql_playground \
  > sql_playground.sql
```

Restore into another database:

```bash
createdb \
  -h localhost \
  -U playground \
  sql_playground_restore

psql \
  -h localhost \
  -U playground \
  -d sql_playground_restore \
  < sql_playground.sql
```

Practice backups to understand:

- Logical versus physical backups.
- Restore procedures.
- Recovery validation.
- Data portability.

A backup that has never been restored is an assumption, not a proven recovery mechanism.

---

## Docker Volume Management

List volumes:

```bash
docker volume ls
```

Inspect the PostgreSQL volume:

```bash
docker volume inspect sql-playground_postgres_data
```

Remove it:

```bash
docker compose down -v
```

Be careful with:

```bash
docker system prune
```

It can remove unrelated local Docker resources depending on the options used.

For a dedicated playground, explicitly removing the Compose volume is safer.

---

## Common Setup Mistakes

### Using `latest`

```yaml
image: postgres:latest
```

**Problem:** the environment can change unexpectedly.

**Better:** pin a major version.

### Assuming Initialization Scripts Always Re-run

**Problem:** PostgreSQL initialization scripts run when the database directory is initialized.

**Better:** reset the volume or use migrations.

### Manual Schema Changes

**Problem:** local environments diverge.

**Better:** version-control migrations.

### Using Production Data

**Problem:** privacy and security risk.

**Better:** generate synthetic data.

### Only Testing with Tiny Data

**Problem:** performance characteristics remain hidden.

**Better:** create larger and skewed datasets.

### Only Using a GUI

**Problem:** automation and troubleshooting become harder.

**Better:** become comfortable with `psql`.

### Ignoring Transactions

**Problem:** SQL appears correct in one session but fails under concurrency.

**Better:** use multiple sessions.

### Adding Indexes Without Evidence

**Problem:** indexes consume storage and increase write overhead.

**Better:** inspect query plans and workload first.

### Treating ORM as SQL

**Problem:** the developer may not understand generated queries.

**Better:** inspect ORM-generated SQL and database plans.

---

## Setup Validation Checklist

Before beginning SQL exercises:

- [ ] PostgreSQL starts successfully.
- [ ] PostgreSQL version is pinned.
- [ ] Database connection works.
- [ ] `psql` is available.
- [ ] Schema can be recreated.
- [ ] Seed data can be recreated.
- [ ] Reset workflow works.
- [ ] Database configuration is version-controlled.
- [ ] Local secrets are excluded from Git.
- [ ] Synthetic data is available.
- [ ] Multiple sessions can connect.
- [ ] `EXPLAIN` works.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` works.
- [ ] PostgreSQL logs can be inspected.
- [ ] Python can connect.
- [ ] Django can connect if required.
- [ ] FastAPI/SQLAlchemy can connect if required.
- [ ] Database roles can be created for security exercises.

---

## Recommended Setup Progression

Do not build the most complicated environment first.

Use this progression:

```text
PostgreSQL
   ↓
Docker
   ↓
Schema
   ↓
Seed Data
   ↓
SQL Exercises
   ↓
Python
   ↓
Django / FastAPI
   ↓
Indexes and EXPLAIN
   ↓
Transactions and Locks
   ↓
Large Data
   ↓
Security
   ↓
Production Scenarios
```

Each layer should be added because it enables a new category of learning.

---

## Production Perspective

The local database is intentionally simpler than production.

A production architecture may look like:

```mermaid
flowchart TB
    Client[Clients] --> LB[Load Balancer]
    LB --> API[Django / FastAPI]

    API --> Pool[Connection Pool]
    Pool --> Primary[(PostgreSQL Primary)]
    Pool --> Replica[(Read Replica)]

    API --> Redis[(Redis)]
    API --> Kafka[(Kafka)]

    Worker[Celery Workers] --> Primary
    Worker --> Kafka

    Primary --> Backup[Backup / PITR]
```

The local playground should not attempt to reproduce all of this infrastructure immediately.

Instead, use the local PostgreSQL environment to understand the database behavior that eventually appears inside this architecture:

- Queries.
- Transactions.
- Locks.
- Indexes.
- Connection pools.
- Replication.
- Backups.
- Security.
- Performance.

This keeps the learning environment manageable while preserving production relevance.

---

## Interview Preparation Standard

A database setup is successful when it lets you answer more than:

> "What query produces this result?"

For important exercises, be able to explain:

```text
What is the result grain?
Why is the query correct?
What joins are involved?
Can the joins multiply rows?
How does NULL affect the result?
What indexes are relevant?
What execution plan would PostgreSQL choose?
What happens as data grows?
What happens under concurrency?
Could this query cause excessive database load?
Should it run on a replica?
Should the result be cached?
Should the operation be asynchronous?
What authorization rules apply?
What happens if the transaction fails?
How would you observe the query in production?
```

This is the difference between practicing SQL syntax and developing senior backend SQL judgment.

---

## Key Takeaways

- **Make PostgreSQL reproducible and disposable:** Docker, version-controlled schema, migrations, seed data, and reset scripts should make the database easy to recreate.
- **Separate correctness from performance practice:** use deterministic data for query correctness and larger, skewed datasets for execution-plan and workload analysis.
- **Practice the database as part of the backend:** connect SQL to Python, Django, FastAPI, transactions, connection pools, security, and concurrency.
- **Use observability and evidence:** `psql`, `EXPLAIN (ANALYZE, BUFFERS)`, PostgreSQL statistics, locks, and logs should be part of the normal workflow.
- **Keep the playground production-oriented without making it unnecessarily complex:** start with local PostgreSQL and progressively introduce the behaviors needed for advanced backend scenarios.