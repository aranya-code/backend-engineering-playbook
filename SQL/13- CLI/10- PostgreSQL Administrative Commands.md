# 10- PostgreSQL Administrative Commands

## Overview

PostgreSQL administration from the CLI is the operational layer between SQL development and database engineering. While application developers usually interact with PostgreSQL through Django, FastAPI, SQLAlchemy, or another driver, production engineers frequently need direct CLI access to inspect state, diagnose incidents, manage sessions, verify configuration, and perform controlled administrative operations.

The primary CLI tool is `psql`, supplemented by PostgreSQL utilities such as:

| Tool | Primary purpose |
|---|---|
| `psql` | Interactive SQL and PostgreSQL administration |
| `createdb` | Create databases |
| `dropdb` | Drop databases |
| `createuser` | Create roles |
| `dropuser` | Drop roles |
| `pg_dump` | Logical database backup |
| `pg_restore` | Restore `pg_dump` archives |
| `pg_dumpall` | Dump cluster-wide logical objects |
| `vacuumdb` | Run `VACUUM`, `ANALYZE`, and related maintenance |
| `reindexdb` | Rebuild indexes |
| `clusterdb` | Cluster tables using indexes |
| `pg_isready` | Check server connection readiness |

A senior backend engineer should know not only the commands, but also their operational consequences.

---

## Administrative CLI Architecture

The PostgreSQL CLI is a client of the database server.

```mermaid
flowchart LR
    Engineer[Engineer / Operator] --> PSQL[psql / PostgreSQL Utilities]
    PSQL --> TLS[TLS / Network]
    TLS --> Server[PostgreSQL Server]

    Server --> Auth[Authentication]
    Server --> SQL[SQL Engine]
    Server --> Catalog[System Catalogs]
    Server --> Storage[(Database Storage)]
    Server --> WAL[WAL]
```

The CLI does not directly manipulate PostgreSQL's data files.

Commands such as:

```text
VACUUM
CREATE DATABASE
ALTER ROLE
REINDEX
```

are requests sent to the PostgreSQL server, which performs the operation according to its permissions and internal execution rules.

---

## Verify the Connection Before Administration

Before executing administrative commands, verify where the session is connected.

```sql
\conninfo
```

Also run:

```sql
SELECT
    current_database(),
    current_user,
    session_user,
    inet_server_addr(),
    inet_server_port(),
    pg_is_in_recovery();
```

This helps answer:

```text
Which database?
Which role?
Which server?
Which port?
Primary or replica?
```

This is one of the most important production safety checks.

A destructive command executed against the wrong database can be technically correct and operationally catastrophic.

---

## Inspect PostgreSQL Version

Use:

```sql
SELECT version();
```

or:

```sql
SHOW server_version;
```

From the shell:

```bash
psql --version
```

These are different checks.

```text
psql --version
    ↓
Client version

SELECT version()
    ↓
Server version
```

Client and server versions do not necessarily need to be identical, but compatibility should be considered for administrative tooling.

---

## List Databases

Inside `psql`:

```text
\l
```

For additional information:

```text
\l+
```

Equivalent SQL:

```sql
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
```

Useful database metadata includes:

- Database name
- Owner
- Encoding
- Locale
- Size
- Tablespace
- Connection restrictions

---

## Connect to Another Database

Use:

```text
\c appdb
```

or:

```text
\connect appdb
```

You can also change user:

```text
\c appdb app_runtime
```

Verify afterward:

```sql
SELECT current_database(), current_user;
```

Never assume `\c` succeeded merely because the command was issued.

---

## Inspect Schemas

List schemas:

```text
\dn
```

Detailed output:

```text
\dn+
```

SQL:

```sql
SELECT
    nspname AS schema_name,
    pg_get_userbyid(nspowner) AS owner
FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%'
  AND nspname <> 'information_schema'
ORDER BY nspname;
```

Schemas are authorization and organization boundaries, not merely folders.

---

## Inspect Tables

List tables:

```text
\dt
```

All visible schemas:

```text
\dt *.*
```

Inspect a specific table:

```text
\d app.orders
```

Detailed information:

```text
\d+ app.orders
```

This can expose:

```text
Columns
Types
Nullable status
Defaults
Indexes
Constraints
Foreign keys
Triggers
Storage information
```

---

## Inspect Views and Materialized Views

Views:

```text
\dv
```

Materialized views:

```text
\dm
```

Detailed inspection:

```text
\d+ app.customer_summary
```

Views are logical query definitions.

Materialized views store results physically and therefore require refresh management.

---

## Inspect Indexes

List indexes:

```text
\di
```

Across schemas:

```text
\di *.*
```

SQL:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
ORDER BY
    schemaname,
    tablename,
    indexname;
```

For a specific table:

```text
\d app.orders
```

Indexes are critical for query performance but also add:

```text
Storage
Write amplification
Vacuum work
Maintenance cost
```

Do not create indexes solely because a column appears in a query.

---

## Inspect Constraints

The `\d` command displays important constraints.

For example:

```text
\d app.orders
```

Look for:

```text
PRIMARY KEY
UNIQUE
FOREIGN KEY
CHECK
NOT NULL
```

SQL can also inspect constraints:

```sql
SELECT
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'app'
  AND table_name = 'orders'
ORDER BY constraint_name;
```

Constraints are part of the database's correctness model and should be considered before administrative data changes.

---

## Inspect Sequences

List sequences:

```text
\ds
```

Inspect a sequence:

```text
\d app.orders_id_seq
```

Sequences are commonly associated with:

```text
SERIAL
BIGSERIAL
Identity columns
```

Check sequence state:

```sql
SELECT
    last_value,
    is_called
FROM app.orders_id_seq;
```

Be careful when manually modifying sequence state. Incorrect sequence values can cause future inserts to collide with existing primary keys.

---

## Inspect Functions and Procedures

List functions:

```text
\df
```

Detailed function information:

```text
\df+ app.*
```

Inspect a specific function:

```text
\df+ app.calculate_order_total
```

Functions may contain business logic, security-sensitive operations, or `SECURITY DEFINER` behavior.

Administrative changes to functions should therefore consider:

```text
Ownership
Privileges
search_path
Dependencies
Application callers
```

---

## Inspect Roles

List roles:

```text
\du
```

Detailed role information:

```text
\du+
```

SQL:

```sql
SELECT
    rolname,
    rolsuper,
    rolcreatedb,
    rolcreaterole,
    rolcanlogin,
    rolreplication,
    rolbypassrls
FROM pg_roles
ORDER BY rolname;
```

Role inspection is essential before changing permissions or ownership.

---

## Inspect Role Membership

Role membership can determine effective privileges.

Use:

```sql
SELECT
    member.rolname AS member,
    parent.rolname AS granted_role
FROM pg_auth_members m
JOIN pg_roles parent
    ON parent.oid = m.roleid
JOIN pg_roles member
    ON member.oid = m.member
ORDER BY member.rolname, parent.rolname;
```

Do not evaluate access based only on direct `GRANT` statements.

Effective access can come from:

```text
Ownership
Role membership
PUBLIC
Direct privileges
Default privileges
RLS behavior
```

---

## Inspect Permissions

Use:

```text
\dp
```

or:

```text
\z
```

for table and sequence access privileges.

For a schema:

```text
\dn+
```

For a specific table:

```text
\dp app.orders
```

SQL privilege functions can provide precise answers:

```sql
SELECT
    has_table_privilege(
        current_user,
        'app.orders',
        'SELECT'
    );
```

This is useful when troubleshooting:

```text
permission denied
```

rather than guessing which grant is missing.

---

## Inspect RLS Policies

List policies using SQL:

```sql
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
ORDER BY schemaname, tablename, policyname;
```

For a multi-tenant application, verify:

```text
RLS enabled?
Correct policies?
Correct role?
Correct tenant context?
```

Remember that table privileges and RLS are separate security layers.

---

## Inspect Extensions

List extensions:

```text
\dx
```

SQL:

```sql
SELECT
    extname,
    extversion
FROM pg_extension
ORDER BY extname;
```

Extensions can affect:

```text
Indexes
Functions
Data types
Query behavior
Operational dependencies
```

Common examples include:

```text
pg_stat_statements
pgcrypto
PostGIS
```

Treat extensions as part of the database's deployment and upgrade model.

---

## Inspect Server Configuration

Show a specific setting:

```sql
SHOW work_mem;
```

Show all settings:

```text
SHOW ALL;
```

Filter settings:

```sql
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'max_connections',
    'shared_buffers',
    'work_mem',
    'maintenance_work_mem',
    'statement_timeout',
    'lock_timeout'
)
ORDER BY name;
```

`pg_settings` is particularly useful because it exposes configuration source information.

---

## Configuration Sources

PostgreSQL settings can originate from different sources, including:

```text
Configuration files
Command-line startup parameters
Database-level settings
Role-level settings
Session settings
```

For example:

```sql
SELECT
    name,
    setting,
    source,
    sourcefile
FROM pg_settings
WHERE name = 'work_mem';
```

This helps determine why a session has a particular configuration.

---

## Session-Level Configuration

Inspect:

```sql
SHOW statement_timeout;
```

Change for the current session:

```sql
SET statement_timeout = '30s';
```

For transaction-local behavior:

```sql
BEGIN;

SET LOCAL statement_timeout = '30s';

SELECT ...;

COMMIT;
```

`SET LOCAL` is often preferable for controlled operations because the setting is scoped to the current transaction.

---

## Inspect Active Sessions

One of the most important administrative queries:

```sql
SELECT
    pid,
    usename,
    datname,
    application_name,
    client_addr,
    state,
    xact_start,
    query_start,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
ORDER BY query_start NULLS LAST;
```

This helps identify:

```text
Active queries
Idle sessions
Long-running transactions
Blocked sessions
Application sources
Client addresses
```

---

## Find Long-Running Queries

```sql
SELECT
    pid,
    usename,
    application_name,
    now() - query_start AS duration,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE query_start IS NOT NULL
  AND state <> 'idle'
ORDER BY query_start;
```

A long-running query is not automatically a problem.

Investigate:

```text
What is it doing?
Is it expected?
Is it blocking others?
Is it consuming excessive resources?
Is it part of an OLAP/reporting workload?
```

---

## Find Long-Running Transactions

```sql
SELECT
    pid,
    usename,
    application_name,
    now() - xact_start AS transaction_age,
    state,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

Pay particular attention to:

```text
idle in transaction
```

Long-running transactions can interfere with:

```text
Vacuum
MVCC cleanup
Storage usage
Locks
Replication
```

---

## Inspect Locks

Use:

```sql
SELECT
    pid,
    locktype,
    mode,
    granted,
    relation::regclass AS relation,
    transactionid,
    waitstart
FROM pg_locks
ORDER BY granted, waitstart;
```

A lock being present does not mean a problem exists.

The important questions are:

```text
Is it granted?
Is another session waiting?
How long?
What relation is involved?
Which transaction owns it?
```

---

## Find Blocking Sessions

Use:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

A practical incident workflow is:

```text
Blocked PID
    ↓
Blocking PID
    ↓
Blocking query
    ↓
Transaction start
    ↓
Root cause
```

Do not immediately terminate the blocking session without understanding what it is doing.

---

## Terminate a Backend

PostgreSQL provides:

```sql
SELECT pg_cancel_backend(12345);
```

and:

```sql
SELECT pg_terminate_backend(12345);
```

They have different semantics.

| Function | Purpose |
|---|---|
| `pg_cancel_backend()` | Request cancellation of the current query |
| `pg_terminate_backend()` | Terminate the backend session |

Prefer cancellation when the query itself is the problem and the session should remain usable.

Termination is more disruptive.

---

## Operational Termination Workflow

A safer approach:

```text
Identify PID
    ↓
Identify role
    ↓
Identify application
    ↓
Identify query
    ↓
Check transaction age
    ↓
Check blocking impact
    ↓
Attempt cancellation
    ↓
Terminate only when justified
```

Never copy a PID from an old monitoring output and assume it still refers to the same workload.

PIDs can be reused.

---

## Check Database Size

For the current database:

```sql
SELECT pg_size_pretty(
    pg_database_size(current_database())
);
```

For all databases:

```sql
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
```

Database size is an important capacity-planning metric.

---

## Check Table Sizes

```sql
SELECT
    schemaname,
    relname,
    pg_size_pretty(
        pg_total_relation_size(relid)
    ) AS total_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;
```

`pg_total_relation_size()` includes the table's associated indexes and TOAST storage.

For a more detailed breakdown:

```sql
SELECT
    pg_size_pretty(pg_relation_size('app.orders')) AS table_size,
    pg_size_pretty(pg_indexes_size('app.orders')) AS index_size,
    pg_size_pretty(pg_total_relation_size('app.orders')) AS total_size;
```

---

## `VACUUM`

Run:

```sql
VACUUM app.orders;
```

`VACUUM` helps PostgreSQL reclaim space for reuse and maintain MVCC-related storage health.

It is fundamentally different from:

```sql
DELETE
```

A delete marks row versions as obsolete; vacuum processes dead tuples according to PostgreSQL's MVCC mechanisms.

---

## `VACUUM ANALYZE`

Use:

```sql
VACUUM (ANALYZE) app.orders;
```

This performs maintenance and updates planner statistics.

It can be useful after significant data changes.

However, autovacuum normally handles routine maintenance automatically.

Manual vacuuming should be based on an operational reason rather than habit.

---

## `VACUUM FULL`

```sql
VACUUM FULL app.orders;
```

`VACUUM FULL` rewrites the table and can substantially reclaim disk space.

It is much more disruptive than normal `VACUUM` because it requires a strong lock and can block concurrent access.

Do not use it casually on a busy production table.

Before choosing it, investigate alternatives such as:

```text
Normal VACUUM
Autovacuum tuning
REINDEX
Table rewrite strategy
Partition lifecycle
Online migration techniques
```

---

## `ANALYZE`

Update planner statistics:

```sql
ANALYZE app.orders;
```

For specific columns:

```sql
ANALYZE app.orders (customer_id, status);
```

This can help after significant changes in data distribution.

The goal is not to make queries faster directly. It provides the planner with better information for selecting execution plans.

---

## `REINDEX`

Rebuild an index:

```sql
REINDEX INDEX app.orders_customer_id_idx;
```

A table:

```sql
REINDEX TABLE app.orders;
```

A schema:

```sql
REINDEX SCHEMA app;
```

Reindexing can be useful for certain forms of index corruption or bloat.

For production systems, understand the locking and availability characteristics of the specific operation and PostgreSQL version.

---

## Concurrent Index Rebuilds

For suitable indexes, PostgreSQL supports:

```sql
REINDEX INDEX CONCURRENTLY app.orders_customer_id_idx;
```

This is designed to reduce blocking of normal operations compared with a standard index rebuild.

It has additional operational requirements and limitations.

Use it when availability matters and the specific index qualifies.

---

## Create Index Concurrently

For production tables:

```sql
CREATE INDEX CONCURRENTLY orders_customer_id_idx
ON app.orders (customer_id);
```

This can reduce blocking of normal reads and writes compared with a standard index build.

However:

```text
More work
Longer execution
Additional I/O
Possible invalid index state after failure
Cannot run inside a transaction block
```

After a failed concurrent index build, inspect the resulting index state before retrying blindly.

---

## Drop Index Concurrently

For an index that is confirmed unnecessary:

```sql
DROP INDEX CONCURRENTLY app.orders_old_idx;
```

This is useful when removing indexes from busy production systems with minimal blocking.

Before dropping:

```text
Check query usage
Check dependent constraints
Check application behavior
Check recent query plans
Check deployment history
```

Never delete an index solely because its name looks obsolete.

---

## Database Maintenance Commands

The PostgreSQL client utilities provide shell-level wrappers for common operations.

Examples:

```bash
vacuumdb --analyze appdb
```

```bash
reindexdb appdb
```

```bash
createdb appdb
```

```bash
createuser app_runtime
```

These utilities still connect to PostgreSQL and execute database operations.

They are not direct file manipulation tools.

---

## Create a Database

From the shell:

```bash
createdb appdb
```

Equivalent SQL:

```sql
CREATE DATABASE appdb;
```

The shell utility is convenient for scripting and automation.

Production database creation should consider:

```text
Owner
Encoding
Locale
Tablespace
Connection policy
Application deployment
Backup strategy
Monitoring
```

---

## Drop a Database

Shell:

```bash
dropdb appdb
```

SQL:

```sql
DROP DATABASE appdb;
```

This is destructive.

Before dropping a production database, verify:

```text
Correct environment
Correct endpoint
Correct database
Active sessions
Backup availability
Business approval
Recovery procedure
```

A database drop should be treated as a high-risk administrative operation.

---

## Create a Role

Shell:

```bash
createuser app_runtime
```

SQL:

```sql
CREATE ROLE app_runtime LOGIN;
```

Production role design should normally separate:

```text
Runtime
Migration
Read-only
Administrative
Break-glass
```

rather than giving application processes broad privileges.

---

## Alter a Role

Example:

```sql
ALTER ROLE app_runtime
SET statement_timeout = '30s';
```

Password changes should use controlled credential management rather than embedding secrets into shell history or source code.

For login behavior:

```sql
ALTER ROLE app_runtime NOLOGIN;
```

Be careful: changing role attributes can immediately affect running applications and operational access.

---

## Backup Utilities

Logical backup:

```bash
pg_dump appdb > appdb.sql
```

Custom-format backup:

```bash
pg_dump -Fc appdb -f appdb.dump
```

Restore custom format:

```bash
pg_restore -d appdb appdb.dump
```

Cluster-wide roles and other global objects:

```bash
pg_dumpall --globals-only > globals.sql
```

Logical backups are important but are not substitutes for a complete physical backup and WAL/PITR strategy when recovery requirements demand it.

---

## `pg_isready`

Check whether PostgreSQL is accepting connections:

```bash
pg_isready -h db.example.internal -p 5432
```

Typical use cases:

```text
Kubernetes probes
Deployment scripts
Startup checks
Operational troubleshooting
```

Important distinction:

```text
pg_isready
    ↓
Server connectivity/readiness

SELECT ...
    ↓
Database/application-level functionality
```

A server can be reachable while the application still has authorization, schema, locking, or query problems.

---

## Docker Administration

When PostgreSQL runs in Docker:

```bash
docker exec -it postgres \
    psql -U postgres -d appdb
```

Check the container:

```bash
docker ps
```

Inspect logs:

```bash
docker logs postgres
```

Avoid treating Docker container access as a production authorization model.

Production access should still follow:

```text
Least privilege
Audit
Credential management
Network controls
Approval
```

---

## Kubernetes Administration

For a PostgreSQL pod:

```bash
kubectl get pods -n database
```

Execute `psql`:

```bash
kubectl exec -it postgres-0 -n database -- \
    psql -U app_runtime -d appdb
```

Inspect logs:

```bash
kubectl logs postgres-0 -n database
```

However, direct pod access should not become the normal production database administration workflow.

Prefer controlled administrative access and managed PostgreSQL services where appropriate.

---

## AWS Considerations

For managed PostgreSQL such as Amazon RDS or Aurora PostgreSQL, many operating-system-level administrative actions are unavailable because AWS manages the underlying host.

You generally interact through:

```text
psql
SQL
AWS management APIs
CloudWatch
AWS backup/recovery mechanisms
```

Do not assume that self-managed PostgreSQL procedures such as:

```text
Edit postgresql.conf directly
Restart systemd service
Access database files
```

apply to managed PostgreSQL.

---

## Primary vs Replica

Before executing administrative SQL:

```sql
SELECT pg_is_in_recovery();
```

Interpretation:

```text
false → primary
true  → recovery/standby
```

A diagnostic read may be appropriate on a replica.

A write intended for the primary will fail on a read-only standby.

More importantly, some administrative actions should never be performed simply because the command is syntactically valid.

---

## Administrative Command Decision Flow

```mermaid
flowchart TD
    A[Need to administer PostgreSQL] --> B[Verify Endpoint]
    B --> C[Verify Database]
    C --> D[Verify Role]
    D --> E[Check Primary / Replica]
    E --> F[Assess Impact]
    F --> G{Read-only diagnostic?}

    G -->|Yes| H[Run bounded diagnostic]
    G -->|No| I[Backup / Approval / Rollback Plan]

    I --> J[Set Timeouts]
    J --> K[Execute Controlled Operation]
    K --> L[Verify Result]
    L --> M[Monitor System]
```

This workflow prevents many operator errors that cannot be solved by SQL syntax knowledge alone.

---

## Monitoring Administrative Operations

During significant maintenance, monitor:

```text
CPU
Memory
Disk I/O
Disk space
Locks
Active connections
Transaction age
Replication lag
WAL generation
Query latency
Error rate
```

For example:

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

Database administration is a production workload and should be observable.

---

## Administrative Operations and Replication

Maintenance can affect replicas.

For example:

```text
Large UPDATE
    ↓
Large WAL generation
    ↓
Primary I/O
    ↓
Replica receives WAL
    ↓
Replica replay
    ↓
Potential replication lag
```

Before large operations, understand:

```text
Replica capacity
WAL volume
Recovery requirements
Read traffic
Failover requirements
```

---

## Administrative Operations and HA

High availability does not mean:

```text
Every administrative command is safe
```

For example:

```text
Failover
REINDEX
VACUUM FULL
Schema changes
Role changes
Connection termination
```

can have different effects depending on:

```text
Primary/standby topology
Failover tooling
Replication mode
Connection routing
Managed service behavior
```

Administrative procedures should be tested as part of the HA runbook.

---

## Security Considerations

Administrative commands require elevated privileges and therefore deserve stronger controls.

Recommended practices:

- Use dedicated administrative roles.
- Avoid using `SUPERUSER` for routine application operations.
- Use read-only roles for diagnostics.
- Require MFA at the surrounding access layer where supported.
- Use short-lived or centrally managed credentials.
- Audit privileged operations.
- Use TLS.
- Restrict network access.
- Avoid production credentials in shell history.
- Do not expose database endpoints publicly unless explicitly required and securely designed.

A database administrator's CLI session should be considered a privileged security boundary.

---

## Secrets and Shell History

Avoid commands that place credentials directly into shell history.

For example, do not casually use:

```bash
psql postgresql://user:password@host:5432/appdb
```

where the password may become visible through:

```text
Shell history
Process inspection
Terminal logs
CI logs
Monitoring systems
```

Prefer secure authentication mechanisms such as:

```text
.pgpass with appropriate permissions
Environment-specific secret injection
AWS-managed credentials/secrets
IAM authentication where supported
```

and follow the organization's credential-management policy.

---

## Operational Best Practices

Before administrative operations:

```text
Verify endpoint
Verify database
Verify role
Verify primary/replica state
Understand expected impact
Set appropriate timeouts
Check backups where relevant
```

During operations:

```text
Keep the operation bounded
Monitor resource usage
Watch locks
Watch replication
Avoid unnecessary concurrency
Record the change
```

After operations:

```text
Verify database state
Check application health
Check query latency
Check replication
Check errors
Record the outcome
```

---

## Common Mistakes

### Running Commands Against the Wrong Database

Always verify:

```sql
SELECT current_database();
```

### Assuming `psql` Client Version Is the Server Version

Check both client and server versions.

### Using `VACUUM FULL` as Routine Maintenance

It can require strong locks and rewrite the table.

### Killing a Blocking Session Immediately

First identify the transaction and understand the business operation.

### Using Superuser for Everything

Broad privileges increase blast radius.

### Ignoring Replica Lag

Large writes and maintenance can affect WAL generation and replay.

### Treating `pg_isready` as a Complete Health Check

Connectivity does not prove application correctness.

### Running `EXPLAIN ANALYZE` on Destructive SQL

`ANALYZE` executes the statement.

### Running Large Maintenance During Peak Traffic

Maintenance consumes shared database resources.

### Changing Configuration Without Knowing Scope

A setting can apply at:

```text
Session
Transaction
Role
Database
Server
```

Understand the scope before changing it.

### Assuming Managed PostgreSQL Behaves Like a VM

RDS/Aurora abstracts operating-system administration.

### Executing SQL From an Untrusted Environment

Administrative credentials used from developer laptops or uncontrolled CI environments can create a major security risk.

---

## Production Administrative Checklist

| Area | Checks |
|---|---|
| Connection | Database, host, port, role |
| Topology | Primary or replica |
| Security | Least privilege, TLS, approved access |
| Impact | Locking, CPU, I/O, storage |
| Transactions | Existing long-running transactions |
| Replication | Lag and WAL impact |
| Maintenance | Vacuum/reindex operation characteristics |
| Backup | Recovery path available when needed |
| Monitoring | Metrics and logs visible |
| Rollback | Reversal or recovery procedure understood |
| Change management | Approval and audit requirements satisfied |

---

## Senior Engineering Perspective

The important distinction is:

```text
Knowing the command
```

versus:

```text
Knowing when the command is safe
```

For example:

```sql
VACUUM FULL app.orders;
```

is syntactically simple.

The senior-level questions are:

```text
How large is the table?
Is it production traffic?
What lock does the operation require?
How much free disk exists?
What is the replication topology?
What is the expected duration?
Can the operation be performed online?
What happens if it fails?
How will we monitor the impact?
```

That reasoning is what separates database administration from command memorization.

---

## Interview Traps

### What is the difference between `pg_cancel_backend()` and `pg_terminate_backend()`?

`pg_cancel_backend()` requests cancellation of the current query, while `pg_terminate_backend()` terminates the backend session.

### How do you identify a blocking query?

Use `pg_stat_activity` together with `pg_blocking_pids(pid)` and inspect the blocking session's transaction and query.

### What is the difference between `VACUUM` and `VACUUM FULL`?

Normal `VACUUM` performs routine MVCC cleanup and makes space reusable without rewriting the entire table. `VACUUM FULL` rewrites the table to compact it and has substantially stronger locking and operational impact.

### Why run `ANALYZE`?

It updates planner statistics so PostgreSQL can make better cardinality and execution-plan decisions.

### How do you determine whether a server is a PostgreSQL standby?

Run:

```sql
SELECT pg_is_in_recovery();
```

`true` indicates the server is in recovery/standby mode.

### How do you inspect active PostgreSQL sessions?

Query:

```sql
SELECT *
FROM pg_stat_activity;
```

and focus on state, transaction age, query age, wait events, application name, and client information.

### Why should you verify the connection before a production command?

Because the same valid SQL command can have completely different consequences depending on whether it is executed against development, staging, a primary, a replica, or the wrong production database.

### Is `VACUUM` a backup operation?

No. Vacuum is maintenance for PostgreSQL storage and MVCC behavior. Backups and point-in-time recovery require separate backup and WAL/recovery mechanisms.

### Can `REINDEX` affect production availability?

Yes. The exact impact depends on the reindex operation and PostgreSQL version. Concurrent variants exist for suitable cases when minimizing blocking is important.

### Why is administrative SQL different from application SQL?

Administrative SQL can affect database-wide resources, sessions, locks, configuration, security, maintenance, and availability. Its blast radius is often much larger than an ordinary application query.

---

## Key Takeaways

- **Always verify the PostgreSQL target before administration:** confirm database, role, server address, port, and primary/replica state before executing impactful commands.
- **Use PostgreSQL system views as operational tools:** `pg_stat_activity`, `pg_locks`, `pg_settings`, catalog views, and `pg_stat_user_tables` provide the evidence needed for safe diagnosis.
- **Treat maintenance as a workload:** `VACUUM`, `REINDEX`, large updates, and other administrative operations consume CPU, I/O, locks, storage, and replication capacity.
- **Prefer least-privileged, observable administration:** use dedicated roles, secure credentials, TLS, auditing, bounded operations, and controlled production access rather than relying on unrestricted superuser sessions.
- **Senior database administration is about impact analysis, not command memorization:** understand locking, transactions, replication, HA, recovery, application traffic, and rollback implications before running an otherwise valid command.