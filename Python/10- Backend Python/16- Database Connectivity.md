# 16- Database Connectivity

## Overview

Database connectivity is the boundary between a Python application and a database system such as PostgreSQL. A production backend must manage more than simply opening a connection and executing SQL: it must handle connection lifecycles, pooling, transactions, timeouts, failures, concurrency, security, observability, and graceful shutdown.

A typical request path is:

```text
HTTP Request
    ↓
Authentication
    ↓
Validation
    ↓
Application Service
    ↓
Repository / Data Access Layer
    ↓
Connection Pool
    ↓
Database Connection
    ↓
PostgreSQL
```

The application should generally acquire a connection for the shortest practical scope, execute the required work, commit or roll back explicitly, and return the connection to the pool.

Database connectivity is therefore both a programming concern and an operational resource-management problem.

---

## Database Connectivity Layers

A Python application can interact with a database through several layers:

```text
Application Code
      ↓
ORM / Query Builder
      ↓
Database Driver
      ↓
Connection Pool
      ↓
TCP / TLS
      ↓
Database Server
```

For PostgreSQL, common Python components include:

- `psycopg`;
- SQLAlchemy;
- Django ORM;
- async database libraries;
- application-specific repositories.

Each layer solves a different problem.

| Layer | Responsibility |
|---|---|
| Application | Business behavior |
| Repository / DAO | Data-access abstraction |
| ORM / Query Builder | Query construction and mapping |
| Driver | Database protocol communication |
| Pool | Connection lifecycle and reuse |
| Database | Query execution and durable state |

---

## Database Drivers

A database driver implements communication between Python and the database protocol.

For PostgreSQL, `psycopg` is a modern PostgreSQL driver.

A low-level example:

```python
import psycopg

with psycopg.connect(
    "postgresql://app_user:password@localhost:5432/orders"
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, status FROM orders WHERE id = %s",
            ("order-123",),
        )
        order = cursor.fetchone()
```

The driver handles:

- network communication;
- protocol encoding;
- parameter binding;
- result decoding;
- transaction interaction;
- database-specific errors.

Application code should generally use parameterized queries rather than constructing SQL strings manually.

---

## Connection Lifecycle

A database connection represents an active client-side relationship with the database server.

Conceptually:

```text
Create
  ↓
Connect
  ↓
Authenticate
  ↓
Execute queries
  ↓
Transaction
  ↓
Commit / Rollback
  ↓
Close
```

Creating a connection can be expensive because it may involve:

- TCP connection establishment;
- TLS negotiation;
- authentication;
- server-side session initialization;
- session configuration.

For request-heavy services, repeatedly creating connections is usually inefficient.

---

## Connection Reuse

Production applications normally reuse database connections through a pool.

```text
                 ┌── Connection 1 ── PostgreSQL
Application ─── Pool ── Connection 2 ── PostgreSQL
                 └── Connection 3 ── PostgreSQL
```

A request:

```text
Request
  ↓
Acquire connection
  ↓
Execute query
  ↓
Commit / rollback
  ↓
Release connection
```

The connection itself remains available for reuse.

---

## Connection Pooling

A connection pool maintains a bounded collection of reusable database connections.

Typical configuration includes:

- minimum pool size;
- maximum pool size;
- connection timeout;
- idle lifetime;
- maximum connection lifetime;
- health checks;
- reset behavior.

Pooling reduces connection establishment overhead and controls database concurrency.

---

## Why Pool Size Matters

Suppose:

```text
8 Kubernetes pods
×
4 application workers
×
10 database connections
=
320 potential connections
```

The database sees the aggregate, not each application's local configuration.

Connection capacity must therefore be designed across:

```text
workers
× replicas
× pool size
```

rather than configured independently by each service.

---

## PostgreSQL Connection Limits

PostgreSQL has a finite connection capacity.

A simplified model is:

```text
PostgreSQL max_connections
        ↓
Application connections
        +
Admin connections
        +
Monitoring
        +
Other services
```

Do not configure application pools to consume the entire database connection budget.

Reserve capacity for:

- migrations;
- administration;
- monitoring;
- operational recovery;
- other workloads.

---

## Connection Pool Sizing

More connections do not necessarily produce more throughput.

If the database can efficiently execute only a bounded number of concurrent queries, excessive connections can cause:

```text
more concurrency
    ↓
CPU contention
    ↓
lock contention
    ↓
memory pressure
    ↓
higher latency
    ↓
lower throughput
```

Pool size should be based on measured workload and database capacity.

---

## Connection Timeout

Applications should not wait indefinitely for a connection.

There are multiple timeout layers:

```text
Pool acquisition timeout
        ↓
Connection establishment timeout
        ↓
Query execution timeout
        ↓
Transaction / statement timeout
        ↓
HTTP request deadline
```

These should be coordinated.

A request with a two-second deadline should not contain a database operation capable of waiting indefinitely.

---

## Query Timeout

Database queries should have appropriate execution limits.

For PostgreSQL, server-side mechanisms such as `statement_timeout` can protect against unexpectedly long-running queries.

Example:

```sql
SET statement_timeout = '2s';
```

The exact timeout should depend on the operation.

Do not apply an extremely low global timeout to operations that legitimately require longer execution.

---

## Connection Timeout vs Query Timeout

These solve different problems.

| Timeout | Controls |
|---|---|
| Connection timeout | Establishing database connection |
| Pool timeout | Waiting for an available pooled connection |
| Query timeout | Executing a statement |
| Transaction timeout | Overall transaction duration |
| HTTP timeout | End-to-end request |
| Shutdown timeout | Graceful resource termination |

A robust service defines these boundaries deliberately.

---

## Transactions

A transaction groups database operations into an atomic unit.

```text
BEGIN
  ↓
Operation A
  ↓
Operation B
  ↓
COMMIT
```

If an error occurs:

```text
BEGIN
  ↓
Operation A
  ↓
Operation B fails
  ↓
ROLLBACK
```

Transactions are essential when multiple changes must maintain a consistent database state.

---

## Python Transaction Example

Using `psycopg`:

```python
import psycopg


def create_order(
    connection: psycopg.Connection,
    customer_id: str,
    amount: int,
) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO orders (customer_id, amount)
                VALUES (%s, %s)
                """,
                (customer_id, amount),
            )

            cursor.execute(
                """
                UPDATE customers
                SET order_count = order_count + 1
                WHERE id = %s
                """,
                (customer_id,),
            )
```

If an exception escapes the transaction context, the transaction is rolled back.

---

## Transaction Scope

Keep transactions as short as practical.

Good:

```text
BEGIN
 ↓
Read required state
 ↓
Write changes
 ↓
COMMIT
```

Avoid:

```text
BEGIN
 ↓
Database query
 ↓
HTTP request
 ↓
User interaction
 ↓
Long computation
 ↓
COMMIT
```

Long transactions can:

- hold locks;
- retain database resources;
- increase contention;
- delay vacuum cleanup in PostgreSQL;
- increase failure impact.

External network calls should generally not occur inside database transactions unless there is a deliberate transactional design.

---

## Autocommit

Autocommit means individual statements are committed automatically unless explicitly grouped into a transaction.

It can be appropriate for:

- isolated read operations;
- simple administrative operations;
- operations where each statement is independently atomic.

Explicit transactions are required when multiple statements must succeed or fail together.

---

## Transaction Isolation

PostgreSQL provides transaction isolation levels such as:

- Read Committed;
- Repeatable Read;
- Serializable.

The isolation level determines which concurrent changes a transaction can observe and what anomalies are prevented.

A simplified progression is:

```text
Read Committed
    ↓
Repeatable Read
    ↓
Serializable
```

Higher isolation can increase contention or require retry handling.

Use the weakest isolation level that correctly satisfies the business invariant rather than automatically selecting the strongest one.

---

## Concurrency Control

Consider inventory:

```text
Stock = 1

Transaction A → buy 1
Transaction B → buy 1
```

A naive read-modify-write sequence can produce incorrect results.

Possible approaches include:

- atomic SQL updates;
- row-level locks;
- optimistic concurrency;
- appropriate transaction isolation;
- unique constraints.

Prefer expressing invariants close to the database when possible.

---

## Parameterized Queries

Never construct SQL by interpolating untrusted values.

Unsafe:

```python
query = f"""
SELECT *
FROM users
WHERE email = '{email}'
"""
```

Safe:

```python
cursor.execute(
    """
    SELECT id, email
    FROM users
    WHERE email = %s
    """,
    (email,),
)
```

Parameterization separates SQL structure from data and is a primary defense against SQL injection.

---

## SQL Injection

SQL injection occurs when attacker-controlled input changes SQL semantics.

```text
Untrusted input
      ↓
SQL string construction
      ↓
Modified SQL syntax
      ↓
Unauthorized query behavior
```

Parameterized queries prevent values from being interpreted as SQL syntax.

ORMs reduce the risk but do not eliminate it. Raw SQL, dynamic SQL fragments, identifiers, and unsafe query-building APIs still require care.

---

## Dynamic SQL

Parameters generally represent values, not arbitrary SQL identifiers.

For example, dynamically choosing a column requires an allowlist:

```python
SORT_COLUMNS = {
    "created": "created_at",
    "name": "name",
}

column = SORT_COLUMNS.get(sort)
if column is None:
    raise ValueError("Invalid sort field")

query = f"""
SELECT id, name
FROM users
ORDER BY {column}
"""
```

The important property is that the SQL fragment comes from a trusted allowlist rather than arbitrary client input.

---

## ORM Connectivity

An ORM maps database concepts to application objects.

Django commonly uses its ORM directly:

```python
orders = Order.objects.filter(
    customer_id=customer_id,
).order_by("-created_at")
```

SQLAlchemy provides both ORM and SQL-oriented APIs.

ORMs can improve:

- productivity;
- consistency;
- model mapping;
- transaction management;
- query composition.

They can also hide SQL behavior, making query inspection and performance analysis essential.

---

## ORM Does Not Eliminate SQL Knowledge

Senior backend engineers should understand the SQL generated by their ORM.

For example:

```python
orders = Order.objects.filter(customer_id=customer_id)
```

may translate conceptually to:

```sql
SELECT ...
FROM orders
WHERE customer_id = %s;
```

Understanding:

- indexes;
- joins;
- query plans;
- locks;
- transactions;
- cardinality;

remains necessary.

---

## SQLAlchemy Engine and Pool

A typical SQLAlchemy application creates an engine once and reuses it.

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://app_user:password@localhost/orders",
    pool_size=10,
    max_overflow=5,
    pool_timeout=5,
    pool_pre_ping=True,
)
```

The engine owns the connection pool.

Do not create a new engine per request.

---

## SQLAlchemy Session

The SQLAlchemy `Session` provides a unit-of-work abstraction around ORM operations.

A common pattern is:

```text
Request
  ↓
Session
  ↓
Query / mutate objects
  ↓
Commit or rollback
  ↓
Close session
```

The session should normally have a bounded lifecycle.

It should not become a global mutable object shared across requests.

---

## Session Is Not a Connection

These concepts are related but different:

```text
Engine
  ↓
Connection Pool
  ↓
Database Connection

Session
  ↓
Unit of Work
  ↓
Uses connections when needed
```

A SQLAlchemy session is not itself a database connection.

Confusing the two can lead to incorrect lifecycle and concurrency designs.

---

## Async Database Connectivity

Async Python applications require async-compatible database access when database operations are expected to participate in the event loop without blocking it.

Conceptually:

```text
FastAPI event loop
      ↓
Async DB driver
      ↓
await query
      ↓
PostgreSQL
```

Using synchronous database operations directly in an event-loop thread can block unrelated requests.

---

## Async Does Not Make PostgreSQL Queries Faster

Async primarily improves resource utilization while waiting for I/O.

```text
Request A
   └── await DB ───────────────┐
                               │
Request B                      │
   └── await DB ───────────────┤
                               ↓
                         PostgreSQL
```

The database still executes the query.

Slow SQL remains slow SQL.

---

## Async Connection Pools

Async pools should also be bounded.

Example architecture:

```text
FastAPI
  ↓
Async SQLAlchemy
  ↓
Async Pool
  ↓
PostgreSQL
```

Pool sizing must account for:

- worker count;
- pod count;
- database capacity;
- request concurrency;
- query duration.

---

## Blocking Calls in Async Applications

Avoid:

```python
async def endpoint():
    result = synchronous_db_query()
    return result
```

if the synchronous call executes on the event-loop thread.

Options include:

- use an async driver;
- use an appropriate async ORM integration;
- deliberately offload blocking work to a thread when justified.

The correct choice depends on the application's architecture and workload.

---

## Django Database Connections

Django manages database connections through its database configuration and request lifecycle.

A typical configuration includes:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "orders",
        "USER": "app_user",
        "PASSWORD": "...",
        "HOST": "postgres",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
    }
}
```

Production configuration should use environment or secret-management mechanisms rather than embedding credentials in source code.

---

## Persistent Connections in Django

Django's `CONN_MAX_AGE` controls connection persistence.

Long-lived connections can reduce connection establishment overhead but increase the number of connections held by workers.

The resulting database connection count still scales with:

```text
workers × replicas × connection behavior
```

Tune it with actual workload and PostgreSQL capacity.

---

## Database URLs

A database URL is convenient for configuration:

```text
postgresql://user:password@host:5432/database
```

For production:

- inject it through configuration;
- avoid committing credentials;
- avoid logging it;
- handle special characters in credentials correctly;
- prefer secret references where supported.

A database URL is configuration, not a secret-management strategy by itself.

---

## TLS Database Connections

Applications may connect to PostgreSQL using TLS.

A production connection may require:

```text
application
    ↓ TLS
PostgreSQL
```

Depending on requirements, configure:

- certificate verification;
- trusted CA;
- client certificates;
- hostname validation.

Do not disable certificate verification merely to fix development connection errors.

---

## Network Connectivity

Database access depends on network configuration:

```text
Application Pod
     ↓
Service / DNS
     ↓
Network
     ↓
PostgreSQL
```

In AWS, this may involve:

```text
EKS / ECS / EC2
     ↓
VPC
     ↓
Security Groups
     ↓
Private subnet
     ↓
RDS PostgreSQL
```

Database endpoints should generally remain private unless a public endpoint is explicitly required and adequately secured.

---

## DNS and Database Failover

Applications should normally connect using the database service endpoint rather than a hard-coded database IP.

For managed PostgreSQL systems such as Amazon RDS, failover can change the underlying endpoint target.

Applications should therefore support:

- DNS resolution;
- connection retry;
- connection recycling;
- handling stale connections.

Do not assume a database connection remains valid forever.

---

## Stale Connections

Connections can become invalid because of:

- database restart;
- failover;
- network interruption;
- idle connection termination;
- infrastructure changes.

Pooling implementations often provide mechanisms such as connection health checks or recycling.

For example, SQLAlchemy can use:

```python
create_engine(
    url,
    pool_pre_ping=True,
)
```

This can detect stale connections before handing them to application code.

Health checks add overhead, so use them according to operational requirements.

---

## Database Errors

Database drivers expose database-specific exceptions.

Application code should distinguish:

```text
Connection failure
Query failure
Constraint violation
Serialization failure
Deadlock
Timeout
Authentication failure
```

Do not catch every database exception and return a generic success response.

---

## Constraint Violations

Suppose PostgreSQL enforces:

```sql
UNIQUE (email)
```

Two concurrent requests may attempt the same email.

The database is the final authority.

Application logic can translate the constraint violation into an appropriate API response.

Do not rely solely on:

```text
SELECT first
IF not exists:
    INSERT
```

because concurrent requests can race.

---

## Retryable Database Errors

Some failures may be safely retried, depending on transaction semantics.

Examples can include:

- serialization failures;
- deadlocks;
- transient connection failures.

Retrying blindly is dangerous.

A retry policy should consider:

```text
Was the operation committed?
Is the operation idempotent?
Is the transaction safe to replay?
How many attempts?
Backoff?
Jitter?
Deadline?
```

---

## Database Transactions and Retries

A transaction that fails with a serialization error may need to be retried from the beginning.

Conceptually:

```text
BEGIN
 ↓
Read
 ↓
Write
 ↓
COMMIT
 ↓
serialization failure
 ↓
ROLLBACK
 ↓
retry entire transaction
```

Retrying only the failed statement may not preserve the transaction's correctness.

---

## Deadlocks

Deadlocks can occur when transactions acquire locks in incompatible orders.

```text
Transaction A
  locks Row 1
  waits for Row 2

Transaction B
  locks Row 2
  waits for Row 1
```

PostgreSQL can detect the deadlock and abort one transaction.

Reduce risk by:

- consistent lock ordering;
- short transactions;
- appropriate indexes;
- avoiding unnecessary locks;
- bounded retries where safe.

---

## Connection Leaks

A connection leak occurs when application code acquires a connection but fails to return it.

Symptoms include:

```text
pool exhausted
requests waiting for connections
latency increases
database connection count rises
timeouts
```

Use context managers or framework-managed lifecycles.

---

## Connection Pool Exhaustion

A pool can become exhausted even when the database is healthy.

Example:

```text
Pool size = 10
10 requests hold connections
11th request
    ↓
waits for connection
    ↓
pool timeout
```

This can happen because of:

- long queries;
- long transactions;
- leaked connections;
- excessive concurrency;
- connection pool too small;
- database contention.

---

## N+1 Queries

An N+1 query pattern performs one query to obtain a collection and then one query per item.

```text
1 query → users

N queries → orders for each user
```

For 1,000 users:

```text
1 + 1,000 = 1,001 queries
```

ORM abstractions can make this easy to introduce accidentally.

Use:

- joins;
- eager loading;
- `select_related`;
- `prefetch_related`;
- explicit batch queries;

where appropriate.

---

## Query Performance

Database performance should be measured at the database layer.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status
FROM orders
WHERE customer_id = 'customer-123';
```

Inspect:

- execution time;
- row estimates;
- actual rows;
- scans;
- joins;
- buffer activity;
- sort operations.

Do not optimize database code based solely on Python-level profiling.

---

## Database Connectivity and Time Complexity

Python-level complexity does not capture database cost.

This:

```python
for order in orders:
    repository.get_customer(order.customer_id)
```

may look like:

```text
O(n)
```

at the Python level but actually generate:

```text
O(n) database round trips
```

The external-call cost can dominate total latency.

---

## Bulk Operations

Prefer batching when the database supports it.

Instead of:

```text
1,000 individual INSERTs
```

use an appropriate bulk operation:

```text
1 batch
    ↓
database
```

Benefits can include:

- fewer network round trips;
- lower transaction overhead;
- better throughput.

But extremely large batches can increase:

- memory usage;
- transaction duration;
- lock duration;
- replication lag.

Choose a bounded batch size.

---

## Streaming Results

Loading millions of rows into Python memory is dangerous.

Avoid:

```python
rows = cursor.fetchall()
```

for unbounded datasets.

Prefer:

```text
database cursor
    ↓
bounded batches
    ↓
processing
    ↓
next batch
```

Streaming and server-side cursors can be useful for exports and ETL workloads.

---

## Pagination

APIs should generally avoid returning arbitrarily large result sets.

Offset pagination:

```sql
LIMIT 100 OFFSET 10000
```

can become expensive at large offsets.

Keyset pagination can use a stable ordering key:

```sql
SELECT id, created_at
FROM orders
WHERE created_at < %s
ORDER BY created_at DESC
LIMIT 100;
```

The appropriate strategy depends on the access pattern and index design.

---

## Read Replicas

Read-heavy systems may use PostgreSQL read replicas:

```text
                  ┌── Primary
Application ──────┤
                  └── Read Replica
```

Writes go to the primary.

Reads may go to replicas.

However, replicas introduce replication lag.

A request that writes data and immediately reads it may require primary routing to guarantee read-after-write behavior.

---

## Read/Write Splitting

Application-level routing can conceptually be:

```text
Write
  ↓
Primary

Read
  ↓
Replica
```

The routing decision must account for:

- transaction context;
- consistency requirements;
- replication lag;
- failover;
- operational complexity.

Do not route every read to replicas merely because replicas exist.

---

## Database Connectivity in Microservices

Each service should generally own its database boundary.

```text
Order Service
    ↓
Orders DB

Billing Service
    ↓
Billing DB
```

Avoid direct cross-service database access:

```text
Service A ───────→ Service B's database
```

because it creates hidden coupling and bypasses service contracts.

Prefer:

```text
Service A
   ↓ API / event
Service B
   ↓
Service B database
```

---

## Redis vs PostgreSQL

Redis and PostgreSQL serve different roles.

| Requirement | PostgreSQL | Redis |
|---|---|---|
| Durable relational data | Excellent | No |
| Transactions | Strong relational transactions | Different transactional model |
| Complex queries | Excellent | Limited |
| Primary system of record | Common | Usually not |
| Cache | Possible | Excellent |
| Low-latency ephemeral state | Good | Excellent |
| Distributed locks | Possible | Common use |
| Session storage | Possible | Common use |

Do not use Redis as a replacement for PostgreSQL merely because it is faster.

---

## Database Connectivity and Kafka

Kafka should not be treated as a database connection mechanism.

A common architecture is:

```text
PostgreSQL
    ↓
Outbox / application transaction
    ↓
Kafka
    ↓
Consumer
```

When database state and event publication must remain consistent, patterns such as the transactional outbox can prevent dual-write inconsistencies.

---

## Database Connectivity and Celery

Celery workers need their own database connection lifecycle.

```text
Celery Worker
    ↓
Connection Pool / Worker DB lifecycle
    ↓
PostgreSQL
```

Do not assume a connection opened by an HTTP request can safely be reused by a background worker.

Workers may be long-lived and execute many tasks, so stale-connection handling and cleanup are important.

---

## Forking and Database Connections

Database connections should generally not be inherited and shared across forked worker processes.

The safer model is:

```text
Parent process
    ↓
fork
    ↓
Worker A → own DB connections
Worker B → own DB connections
```

This is particularly important with process-based servers and background workers.

Frameworks and connection pools should be configured according to their documented multiprocessing lifecycle.

---

## Threads and Database Connections

Database drivers and sessions have different thread-safety guarantees.

Do not assume a single connection or ORM session can safely be shared across threads.

Prefer:

```text
Thread A → its appropriate DB/session context
Thread B → its appropriate DB/session context
```

Connection pools are designed to coordinate reusable connections safely according to the driver's contract.

---

## Async Tasks and Database Sessions

Do not share mutable database session objects across unrelated asyncio tasks.

Prefer:

```text
Task A → session A
Task B → session B
```

or framework-supported request/task-local session management.

A session represents mutable state and a unit of work, not a globally shared application resource.

---

## Graceful Shutdown

A backend should close database resources during shutdown.

```mermaid
sequenceDiagram
    participant K as Kubernetes
    participant API as Python Application
    participant DB as PostgreSQL

    K->>API: SIGTERM
    API->>API: Stop accepting new work
    API->>API: Drain active requests
    API->>DB: Complete/rollback transactions
    API->>DB: Close pool
    API-->>K: Process exits
```

The exact shutdown behavior depends on the server and framework.

The important property is that active work is given a bounded opportunity to finish and connections are released cleanly.

---

## Health Checks

Database health should be distinguished from application liveness.

A readiness check might verify that the service can access required dependencies.

For example:

```text
Kubernetes
   ↓
Readiness probe
   ↓
Application
   ↓
Database connectivity
```

Avoid making an expensive database query for every health endpoint request.

Health checks should be lightweight and bounded.

---

## Liveness vs Readiness

| Check | Purpose |
|---|---|
| Liveness | Is the process functioning? |
| Readiness | Can it safely receive traffic? |
| Startup | Has initialization completed? |

A temporary PostgreSQL outage does not necessarily mean the application process is dead.

If readiness fails:

```text
Pod remains alive
but
traffic is removed
```

This is often preferable to restarting healthy processes unnecessarily.

---

## Observability

Database connectivity should expose metrics such as:

```text
db_connection_pool_size
db_connections_in_use
db_pool_wait_time
db_query_duration
db_query_errors
db_transaction_duration
db_connection_errors
```

Track latency distributions rather than only averages:

```text
p50
p95
p99
```

High pool wait time can indicate application-side saturation even when database query execution itself is fast.

---

## Tracing

Distributed tracing can expose:

```text
HTTP request
    ↓
application service
    ↓
SQL query
    ↓
PostgreSQL
```

Useful attributes include:

- database system;
- operation;
- query duration;
- service;
- transaction context.

Do not include raw credentials or sensitive query parameters in traces.

---

## Logging Database Errors

Logs should include useful operational context:

```text
service
environment
operation
database host/cluster identifier
error class
duration
trace_id
```

Avoid logging:

- passwords;
- connection URLs containing credentials;
- access tokens;
- sensitive query parameters;
- complete sensitive row contents.

---

## Slow Query Monitoring

A production system should identify slow queries through:

- PostgreSQL statistics;
- application metrics;
- tracing;
- database logs;
- query analysis tools.

The goal is to distinguish:

```text
Python overhead
vs
network latency
vs
pool wait
vs
database execution
vs
lock wait
```

Without that decomposition, optimization efforts often target the wrong layer.

---

## Connection Pool Metrics

A useful saturation model is:

```text
Pool capacity
    ↓
Connections available
    ↓
Requests waiting
    ↓
Pool acquisition latency
```

If pool wait time increases while database execution time remains stable, the bottleneck may be pool capacity or application concurrency rather than SQL execution.

---

## Security Considerations

Database connectivity is a high-value security boundary.

Use:

- TLS;
- least-privilege database users;
- separate credentials per service where practical;
- secret management;
- credential rotation;
- parameterized queries;
- network restrictions;
- database auditing where required.

Avoid using a superuser account from the application.

---

## Least-Privilege Database Users

A production service should have only the permissions it requires.

For example:

```text
order_service_user
 ├── SELECT orders
 ├── INSERT orders
 ├── UPDATE orders
 └── no DROP DATABASE
```

Migrations may use a different identity with broader privileges.

Separating runtime and migration credentials reduces blast radius.

---

## Secrets

Do not commit:

```python
DATABASE_URL = "postgresql://admin:password@..."
```

Use:

```text
AWS Secrets Manager
Kubernetes Secret
Parameter Store
CI/CD secret injection
```

The application should receive the secret through a controlled configuration mechanism.

---

## SQL Logging

SQL logging can be valuable during development but dangerous in production.

Queries may contain:

- sensitive identifiers;
- personal information;
- financial information;
- business data.

Prefer structured query metadata and controlled sampling rather than indiscriminately logging complete SQL and parameter values.

---

## Database Credentials Rotation

Credential rotation should not require rebuilding application code.

A production process should support:

```text
New credential
      ↓
Configuration update
      ↓
New connections use new credential
      ↓
Old connections drain
      ↓
Old credential revoked
```

Connection pools make lifecycle planning important during rotation.

---

## Availability

Database connectivity is usually a critical dependency.

For production:

- use managed PostgreSQL where appropriate;
- deploy with high availability;
- monitor replication and failover;
- configure application timeouts;
- handle stale connections;
- retry only safe transient failures;
- avoid connection storms during recovery.

---

## Connection Storms

After a database outage, many application workers may simultaneously reconnect:

```text
Database recovers
       ↓
100 pods reconnect
       ↓
Thousands of connection attempts
       ↓
Database overload
```

Mitigations include:

- bounded pool sizes;
- exponential backoff;
- jitter;
- connection recycling;
- controlled startup;
- database-side connection management.

Recovery behavior must be designed, not assumed.

---

## PgBouncer

PgBouncer is a lightweight PostgreSQL connection pooler.

Conceptually:

```text
Many application connections
          ↓
      PgBouncer
          ↓
Fewer PostgreSQL connections
          ↓
      PostgreSQL
```

Pooling modes have different transaction/session semantics.

Connection poolers can be useful when many application processes or services would otherwise create excessive PostgreSQL connections.

However, they add infrastructure and operational complexity.

---

## Managed PostgreSQL

AWS RDS or Aurora PostgreSQL can provide managed database capabilities such as:

- automated backups;
- high availability;
- monitoring;
- failover;
- storage management;
- replication options.

The application still needs correct:

- connection pooling;
- timeouts;
- retry behavior;
- credential management;
- schema migration;
- observability.

Managed infrastructure does not eliminate application-level database engineering.

---

## Disaster Recovery

Database connectivity design should account for:

```text
primary failure
replica failure
region failure
credential loss
network partition
backup restoration
```

Disaster recovery planning should define:

- RPO;
- RTO;
- backup retention;
- restore procedures;
- failover behavior;
- application reconnection behavior.

A database backup is useful only if restoration is tested.

---

## Cost Considerations

Database connections consume resources.

Excessive:

- connections;
- idle sessions;
- queries;
- transaction duration;
- result materialization;

can increase database compute and memory requirements.

Performance optimization should consider:

```text
query cost
+
connection cost
+
application CPU
+
memory
+
network
+
operational cost
```

The fastest query is not always the cheapest architecture if it requires unnecessary infrastructure.

---

## Testing Database Connectivity

Database code should be tested at multiple levels.

### Unit Tests

Unit tests can validate:

- repository behavior;
- query construction;
- transaction decisions;
- error mapping.

Avoid mocking every database interaction if the behavior depends heavily on actual SQL semantics.

### Integration Tests

Integration tests should use a real PostgreSQL instance where practical.

They can validate:

- schema;
- constraints;
- transactions;
- indexes;
- SQL behavior;
- isolation;
- migrations.

Containers are commonly useful for isolated integration environments.

---

## Test Database Isolation

Tests should avoid sharing mutable state unintentionally.

Common strategies include:

- transaction rollback;
- isolated test databases;
- database containers;
- fixture cleanup;
- deterministic seed data.

The correct approach depends on the framework and test suite architecture.

---

## Migration Testing

Database connectivity is tightly coupled to schema migrations.

CI should validate:

```text
empty database
    ↓
all migrations
    ↓
application starts
    ↓
integration tests
```

Also test upgrades from realistic previous schema versions for critical systems.

---

## Connection Failure Testing

Production systems should test failures such as:

```text
database unavailable
connection timeout
query timeout
connection reset
deadlock
serialization failure
constraint violation
pool exhaustion
database failover
```

Failure testing reveals whether retry and recovery logic is actually safe.

---

## Common Mistakes

### Opening a Connection Per Query

This adds connection establishment overhead and can exhaust database capacity.

Use a bounded connection pool.

### Creating a Pool Per Request

A pool is a long-lived application resource, not a request-scoped object.

### Sharing Sessions Globally

ORM sessions contain mutable state and should not be treated as globally shared objects.

### Forgetting Transactions

Multiple dependent writes without a transaction can leave partially applied state.

### Holding Transactions Open Too Long

Long transactions increase lock contention and database resource usage.

### Building SQL with String Interpolation

This creates SQL injection risk.

Use parameterized queries.

### Fetching Everything

Unbounded `fetchall()` can exhaust application memory.

Use pagination or streaming.

### Increasing Pool Size to Fix Latency

A larger pool can increase database contention and make latency worse.

Measure pool wait, query latency, and database saturation first.

---

## Production Pitfalls

### Database Connections Multiply Across Workers

A pool of 10 connections on one worker can become hundreds or thousands across a Kubernetes deployment.

### Retry Storms

Aggressive database retries can overload a recovering database.

Use bounded retries, exponential backoff, jitter, and deadlines.

### Hidden N+1 Queries

ORM abstractions can make dozens or thousands of database round trips look like ordinary Python iteration.

Inspect generated SQL and query counts.

### Replica Read-After-Write Problems

A successful write followed by a replica read may return stale data because replication is asynchronous.

### Stale Connections After Failover

Existing connections may become invalid after database failover.

The application must reconnect safely.

### Long-Lived Idle Transactions

An application that leaves transactions open can interfere with PostgreSQL vacuuming and lock management.

### Using the Database as a Queue

Database polling can be appropriate in limited designs, but high-throughput asynchronous workloads often need purpose-built systems such as Kafka or a task queue.

### Logging Sensitive SQL

Full SQL and parameters can leak application data.

### Application Superuser

Running the application as a database superuser greatly increases the impact of a compromise.

---

## Recommended Backend Architecture

A maintainable Python backend can separate database responsibilities:

```text
FastAPI / Django
       ↓
Application Service
       ↓
Repository
       ↓
ORM / SQLAlchemy / Driver
       ↓
Connection Pool
       ↓
PostgreSQL
```

For example:

```python
class OrderRepository:
    def __init__(self, session):
        self.session = session

    async def get_for_customer(
        self,
        order_id: str,
        customer_id: str,
    ):
        ...
```

The service layer owns business behavior while the repository owns database interaction.

---

## Database Connectivity Decision Matrix

| Requirement | Typical approach |
|---|---|
| Simple PostgreSQL application | `psycopg` |
| ORM-based application | SQLAlchemy / Django ORM |
| FastAPI async backend | Async SQLAlchemy + async PostgreSQL driver |
| Django application | Django ORM |
| High connection count | Pooling / PgBouncer |
| Large export | Streaming / server-side cursor |
| Read-heavy system | Read replicas |
| Strong tenant isolation | Application checks + PostgreSQL RLS where appropriate |
| Background jobs | Worker-specific DB lifecycle |
| High availability | Managed PostgreSQL + reconnect handling |
| Secrets | AWS Secrets Manager / Kubernetes Secrets / equivalent |
| Query optimization | PostgreSQL `EXPLAIN ANALYZE` + tracing |
| High-throughput events | Kafka rather than database polling where appropriate |

---

## Production Workflow

A practical database connectivity workflow is:

```text
Design
  ↓
Choose driver / ORM
  ↓
Define connection lifecycle
  ↓
Configure bounded pool
  ↓
Define transaction boundaries
  ↓
Add timeouts
  ↓
Use parameterized queries
  ↓
Add indexes and constraints
  ↓
Measure query performance
  ↓
Add observability
  ↓
Test failures
  ↓
Validate failover and recovery
```

The database should be treated as a constrained shared resource rather than an infinitely scalable dependency.

---

## Best Practices

- Create database engines and pools once per process rather than per request.
- Keep connection pools bounded.
- Calculate aggregate connection capacity across workers and replicas.
- Leave database connection headroom for operations and recovery.
- Use explicit connection and query timeouts.
- Keep transactions short and intentional.
- Never hold a transaction open across external network calls without a strong reason.
- Use parameterized SQL for values.
- Use allowlists for dynamic SQL identifiers.
- Understand SQL generated by ORMs.
- Monitor and eliminate N+1 queries.
- Use indexes based on actual query patterns.
- Use `EXPLAIN ANALYZE` for database performance investigation.
- Stream or paginate large result sets.
- Use bounded batch sizes for bulk operations.
- Treat sessions and connections as lifecycle-managed resources.
- Do not share mutable sessions across unrelated threads or async tasks.
- Handle stale connections and database failover.
- Retry only failures that are safe to retry.
- Use exponential backoff and jitter during transient failures.
- Use least-privilege database credentials.
- Separate runtime and migration privileges where practical.
- Keep database credentials in managed secret systems.
- Encrypt database traffic with TLS where required.
- Monitor pool saturation, query latency, connection failures, and transaction duration.
- Test real PostgreSQL behavior through integration tests.
- Test database outages, failovers, deadlocks, serialization failures, and pool exhaustion.
- Close pools during graceful application shutdown.

## Key Takeaways

- **Database connectivity is resource management:** connection pools, transaction scope, timeouts, and aggregate connection counts directly affect backend reliability and database capacity.
- **Use the database deliberately:** parameterized queries, explicit transactions, constraints, indexes, appropriate isolation, and query-plan analysis are more important than simply choosing an ORM.
- **Concurrency changes the design:** pool sizes multiply across workers and replicas, transactions can contend for locks, and retries must account for idempotency and transaction semantics.
- **Treat PostgreSQL as a critical distributed dependency:** handle stale connections, failover, timeouts, connection storms, replication lag, observability, and graceful shutdown explicitly.
- **Optimize end to end:** distinguish pool wait, network latency, Python overhead, and database execution time; use profiling, tracing, query analysis, and realistic integration/load tests to identify the actual bottleneck.