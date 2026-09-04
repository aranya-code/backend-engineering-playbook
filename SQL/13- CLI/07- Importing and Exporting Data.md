# 07- Importing and Exporting Data

## Overview

Importing and exporting data is a fundamental PostgreSQL operational skill. It is used for migrations, backups, data movement, environment setup, analytics, bulk loading, troubleshooting, and disaster recovery.

PostgreSQL provides two major mechanisms:

```text
COPY
\copy
```

and logical dump/restore tools:

```text
pg_dump
pg_restore
pg_dumpall
```

They solve different problems.

```mermaid
flowchart LR
    Source[Source Data] --> Import[Import]
    Import --> DB[(PostgreSQL)]

    DB --> Export[Export]
    Export --> Target[Target File / Database]

    DB --> Dump[pg_dump]
    Dump --> Archive[Logical Backup]
    Archive --> Restore[pg_restore]
    Restore --> DB2[(PostgreSQL)]
```

A senior backend engineer should understand not only how to move data, but also:

- Where the data is read from and written to
- Whether the operation runs on the client or server
- Transaction behavior
- Locking and concurrency
- Throughput and resource consumption
- Data integrity
- Security and sensitive-data exposure
- Failure and retry behavior
- Backup and recovery implications
- Production deployment strategy

---

## Import vs Export

| Operation | Direction | Common use |
|---|---|---|
| Import | External source → PostgreSQL | Bulk loading |
| Export | PostgreSQL → external destination | Reporting/extracts |
| `COPY` | Server-side data movement | High-throughput loading/export |
| `\copy` | Client-side data movement | Local files |
| `pg_dump` | Database → logical backup | Backup/migration |
| `pg_restore` | Logical backup → database | Restore |
| `pg_dumpall` | Cluster-wide logical SQL | Roles/globals + databases |

The correct tool depends on whether you are moving **data**, **database structure**, or an entire logical database.

---

## `COPY`

`COPY` is PostgreSQL's native bulk data movement command.

Example:

```sql
COPY app.orders
FROM '/data/orders.csv'
WITH (
    FORMAT csv,
    HEADER true
);
```

Export:

```sql
COPY app.orders
TO '/data/orders.csv'
WITH (
    FORMAT csv,
    HEADER true
);
```

`COPY` is substantially more appropriate for large data movement than issuing millions of individual `INSERT` statements.

---

## Server-Side `COPY`

With SQL `COPY`, the file path is interpreted from the PostgreSQL server's perspective.

```sql
COPY app.orders
FROM '/data/orders.csv'
WITH (FORMAT csv, HEADER true);
```

The file must therefore:

- Exist where the PostgreSQL server can access it
- Be readable/writable by the appropriate PostgreSQL operating context
- Satisfy PostgreSQL's server-side file access restrictions

This is different from `\copy`.

---

## Client-Side `\copy`

`psql` provides:

```text
\copy
```

which performs data transfer through the client.

Example:

```text
\copy app.orders FROM 'orders.csv' WITH (FORMAT csv, HEADER true)
```

The file is read from the machine running `psql`.

This is often much more convenient for:

```text
Developer workstations
Bastion hosts
Operational scripts
Local CSV files
Controlled data transfers
```

---

## `COPY` vs `\copy`

| Characteristic | `COPY` | `\copy` |
|---|---|---|
| Implemented by | PostgreSQL | `psql` client |
| File location | Database server | Client machine |
| Network path | Server handles file | Data passes through client |
| Local workstation file | Usually unsuitable | Excellent |
| Server-side bulk loading | Excellent | Possible through client |
| Requires server file access | Yes | No |
| Typical CLI usage | Advanced/server-side | Common |

The distinction is frequently tested in PostgreSQL interviews.

---

## CSV Import

Example CSV:

```text
id,customer_id,status,total
1001,42,pending,125.50
1002,51,paid,300.00
```

Import:

```text
\copy app.orders (
    id,
    customer_id,
    status,
    total
) FROM 'orders.csv'
WITH (
    FORMAT csv,
    HEADER true
)
```

Explicitly specifying columns is safer than depending on physical table column order.

---

## Why Specify Columns?

Avoid relying on:

```text
\copy app.orders FROM 'orders.csv'
```

when the file has an application-defined column order.

Prefer:

```text
\copy app.orders (
    id,
    customer_id,
    status,
    total
) FROM 'orders.csv'
WITH (FORMAT csv, HEADER true)
```

This makes the import contract explicit.

It also protects the process against unrelated column additions.

---

## Exporting Selected Columns

Do not export entire tables unnecessarily.

Use:

```text
\copy (
    SELECT
        id,
        customer_id,
        status,
        created_at
    FROM app.orders
    WHERE created_at >= current_date - interval '7 days'
) TO 'orders.csv'
WITH (
    FORMAT csv,
    HEADER true
)
```

This reduces:

- Data volume
- Network traffic
- Local storage
- Processing time
- Sensitive-data exposure

---

## CSV Options

Common options include:

```text
FORMAT csv
HEADER true
DELIMITER ','
QUOTE '"'
ESCAPE '"'
NULL ''
```

Example:

```sql
COPY app.orders
TO STDOUT
WITH (
    FORMAT csv,
    HEADER true,
    NULL ''
);
```

CSV has edge cases involving:

```text
Commas
Quotes
Newlines
NULL values
Encoding
```

Use PostgreSQL's CSV implementation rather than writing custom CSV parsing logic for database exports.

---

## NULL Handling

A CSV file must distinguish between:

```text
NULL
empty string
actual text
```

PostgreSQL's `COPY` supports explicit `NULL` representation.

For example:

```sql
COPY app.customers
TO STDOUT
WITH (
    FORMAT csv,
    HEADER true,
    NULL '\N'
);
```

The import and export formats should agree on how missing values are represented.

---

## Delimiters

CSV normally uses:

```text
,
```

but other delimiters can be configured.

Example:

```sql
COPY app.orders
TO STDOUT
WITH (
    FORMAT csv,
    DELIMITER E'\t',
    HEADER true
);
```

For TSV-style data, a tab delimiter is often convenient.

---

## Encoding

Production data movement should account for encoding.

PostgreSQL databases commonly use:

```text
UTF-8
```

Verify the database encoding:

```sql
SHOW server_encoding;
```

Character encoding mismatches can corrupt:

```text
Names
Addresses
International text
JSON
Free-form content
```

Validate encoding when exchanging files with external systems.

---

## Importing into a Staging Table

For production data pipelines, avoid loading untrusted or externally sourced data directly into business tables.

Prefer:

```mermaid
flowchart LR
    File[External File] --> Stage[Staging Table]
    Stage --> Validate[Validate / Transform]
    Validate --> Target[Business Tables]
```

Example:

```sql
CREATE TABLE app.orders_staging (
    customer_id bigint,
    status text,
    total numeric(12,2),
    created_at timestamptz
);
```

Import:

```text
\copy app.orders_staging FROM 'orders.csv' WITH (FORMAT csv, HEADER true)
```

Then validate before moving data into the production schema.

---

## Why Staging Tables Matter

Staging separates:

```text
Raw input
```

from:

```text
Trusted application data
```

This allows validation of:

- Data types
- Required fields
- Duplicate records
- Referential integrity
- Business rules
- Invalid values
- Unexpected row counts

It also provides a safer rollback boundary for complex imports.

---

## Validating Imported Data

Example:

```sql
SELECT count(*)
FROM app.orders_staging;
```

Check missing customer IDs:

```sql
SELECT count(*)
FROM app.orders_staging
WHERE customer_id IS NULL;
```

Check invalid totals:

```sql
SELECT count(*)
FROM app.orders_staging
WHERE total < 0;
```

Check duplicates:

```sql
SELECT
    customer_id,
    created_at,
    count(*)
FROM app.orders_staging
GROUP BY customer_id, created_at
HAVING count(*) > 1;
```

Validation should happen before modifying trusted business tables.

---

## Loading from Staging

After validation, data can be inserted into the target table.

Example:

```sql
INSERT INTO app.orders (
    customer_id,
    status,
    total,
    created_at
)
SELECT
    customer_id,
    status,
    total,
    created_at
FROM app.orders_staging;
```

For more complex migrations, use explicit transformations and idempotency controls.

---

## Conflict Handling

PostgreSQL supports:

```sql
INSERT ... ON CONFLICT
```

For example:

```sql
INSERT INTO app.customers (
    external_id,
    email
)
SELECT
    external_id,
    email
FROM app.customers_staging
ON CONFLICT (external_id)
DO UPDATE
SET email = EXCLUDED.email;
```

This is useful for:

```text
Synchronization
Upserts
Incremental imports
Idempotent loading
```

However, conflict handling should reflect the business semantics. Blindly overwriting existing rows can cause data loss.

---

## Importing Data with `INSERT`

For small datasets:

```sql
INSERT INTO app.customers (
    external_id,
    email
)
VALUES
    ('cust-1001', 'a@example.com'),
    ('cust-1002', 'b@example.com');
```

This is straightforward but is generally not the preferred mechanism for very large datasets.

For large imports, use bulk-loading mechanisms such as `COPY`.

---

## Why `COPY` Is Faster

Individual inserts incur substantial overhead:

```text
Application
    ↓
SQL statement
    ↓
Network round trip
    ↓
Parse/plan/execute
    ↓
Transaction/WAL work
```

Bulk loading reduces per-row protocol and statement overhead.

Conceptually:

```text
Millions of INSERT statements
        ↓
High statement overhead

COPY
        ↓
Bulk data stream
        ↓
Lower per-row overhead
```

This makes `COPY` particularly valuable for large data ingestion.

---

## `COPY` and Transactions

`COPY` can participate in a transaction.

Example:

```sql
BEGIN;

COPY app.orders_staging
FROM '/data/orders.csv'
WITH (FORMAT csv, HEADER true);

COMMIT;
```

If the transaction is rolled back, the imported rows are rolled back as part of that transaction.

For very large loads, however, transaction duration and WAL/resource consumption must be considered.

---

## Large Imports and Transaction Size

A massive single transaction can cause:

```text
Long transaction lifetime
Large WAL generation
Long rollback time
Replication lag
Vacuum interference
Lock retention
High disk usage
```

For very large data migrations, design the import process around controlled batches or staged loading when appropriate.

Do not blindly split every import into arbitrary batches: transactional semantics and consistency requirements should determine the boundary.

---

## Importing into Production

A safe production workflow is:

```text
Prepare source
    ↓
Validate format
    ↓
Estimate volume
    ↓
Load staging data
    ↓
Validate staging data
    ↓
Check constraints / relationships
    ↓
Transform or merge
    ↓
Validate target
    ↓
Monitor replication and resources
```

Production imports should be treated as workload events, not simple file operations.

---

## Import Performance Factors

Bulk import performance depends on:

- Row count
- Row width
- Index count
- Constraint count
- Triggers
- WAL volume
- Disk throughput
- CPU
- Network bandwidth
- Replication
- Concurrent workload
- Transaction size

An import that is fast on a development database can be disruptive on a busy production system.

---

## Indexes During Large Loads

Indexes make reads faster but increase write work.

For a large initial load, index strategy can significantly affect performance.

Possible approaches include:

```text
Load data
    ↓
Create indexes
```

when the table is being populated from scratch and operational constraints allow it.

For an existing production table, dropping indexes simply to accelerate a load is risky because it:

- Changes query performance
- Removes integrity guarantees from unique indexes/constraints
- Requires rebuilding
- Can increase operational risk

Use workload-specific analysis before changing index strategy.

---

## Constraints During Import

Constraints protect data integrity.

Examples:

```text
PRIMARY KEY
UNIQUE
FOREIGN KEY
CHECK
NOT NULL
```

Do not disable constraints merely because they slow an import unless there is a carefully designed migration strategy and a reliable validation/recovery plan.

Invalid data introduced during bulk loading can be much harder to repair than a slower import.

---

## Triggers During Import

Triggers can execute additional work for each imported row.

For example:

```text
COPY
  ↓
INSERT row
  ↓
Trigger
  ↓
Audit row
  ↓
Additional index/WAL work
```

This can significantly increase import cost.

Before a large import, inspect:

```text
Triggers
Audit behavior
Foreign keys
Indexes
RLS
```

Do not assume `COPY` bypasses normal table semantics.

---

## Row-Level Security and Import

RLS can affect data access and modification depending on the executing role and policies.

Before importing into an RLS-protected table, understand:

```text
Current role
Table ownership
BYPASSRLS
FORCE ROW LEVEL SECURITY
INSERT policies
WITH CHECK conditions
```

A bulk import that works under an administrative role may fail under the application role.

---

## Exporting from a Read Replica

Large read-only exports can sometimes be executed against a read replica.

Architecture:

```text
Application
     ↓
Primary
     ↓
Read Replicas

Analytics / Export
     ↓
Read Replica
```

Benefits:

- Reduces primary read load
- Separates analytical workloads
- Protects application latency

Tradeoff:

- Replica data may lag
- Recent rows may be missing
- Long-running queries can interfere with replication

Always determine whether replica freshness is acceptable.

---

## Export Consistency

A large export should have a defined consistency model.

For example:

```text
Export as-of a consistent snapshot
```

is different from:

```text
Export rows while data continuously changes
```

A transaction can provide a consistent snapshot:

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;

SELECT ...
;

COMMIT;
```

However, long-running snapshots can prevent cleanup of old row versions and increase storage pressure.

Consistency requirements must therefore be balanced against transaction duration.

---

## Streaming Export

For very large exports, avoid accumulating the complete result set in application memory.

Prefer streaming-oriented approaches.

Example with `psql`:

```bash
psql "$DATABASE_URL" \
  -c "COPY (
        SELECT id, status, created_at
        FROM app.orders
      ) TO STDOUT WITH (FORMAT csv, HEADER true)" \
  > orders.csv
```

The data flows through:

```text
PostgreSQL
   ↓
psql stdout
   ↓
File
```

rather than requiring the entire result set to be held in memory.

---

## Compression

Large exports are often compressed.

Example:

```bash
psql "$DATABASE_URL" \
  -c "COPY (
        SELECT id, status, created_at
        FROM app.orders
      ) TO STDOUT WITH (FORMAT csv, HEADER true)" \
  | gzip > orders.csv.gz
```

This can substantially reduce:

```text
Storage
Network transfer
Object storage cost
```

at the cost of CPU for compression/decompression.

---

## Importing Compressed Data

A compressed file can be streamed into `psql`.

For example:

```bash
gzip -dc orders.csv.gz | \
psql "$DATABASE_URL" \
  -c "\copy app.orders FROM STDIN WITH (FORMAT csv, HEADER true)"
```

This avoids creating an intermediate uncompressed file.

---

## Object Storage Pipelines

A common AWS architecture is:

```mermaid
flowchart LR
    Source[External Source] --> S3[(Amazon S3)]
    S3 --> Worker[Import Worker]
    Worker --> Stage[(PostgreSQL Staging)]
    Stage --> Validate[Validation]
    Validate --> DB[(Production Tables)]
```

The worker might be:

```text
Celery
ECS task
Kubernetes Job
AWS Batch
Lambda for small control-plane tasks
```

For very large files, avoid designs where a single application request synchronously uploads and processes the entire dataset.

---

## Asynchronous Imports

A production API should generally not keep an HTTP request open for a large import.

Prefer:

```text
POST /imports
       ↓
Create import job
       ↓
Store file
       ↓
Queue job
       ↓
Celery / worker
       ↓
Load staging table
       ↓
Validate
       ↓
Promote data
       ↓
Update job status
```

This architecture provides:

- Retries
- Progress tracking
- Backpressure
- Failure isolation
- Operational visibility

---

## Import Job State

A useful import workflow can use states such as:

```text
PENDING
  ↓
UPLOADED
  ↓
PROCESSING
  ↓
VALIDATING
  ↓
COMPLETED

or

FAILED
```

Persisting job state allows the API to report progress without depending on an active worker process.

---

## Idempotent Imports

Imports should ideally be retryable.

For example, use an external identifier:

```sql
UNIQUE (external_id)
```

and:

```sql
INSERT ...
ON CONFLICT ...
```

or maintain an import batch identifier.

The goal is:

```text
Retry import
    ↓
Do not create unintended duplicates
```

This is particularly important when imports are executed through:

```text
Celery
Kafka consumers
Kubernetes Jobs
CI/CD
Scheduled pipelines
```

---

## Export Jobs

Large exports should also be asynchronous.

Architecture:

```text
Client
  ↓
POST /exports
  ↓
Create export job
  ↓
Worker
  ↓
PostgreSQL
  ↓
Compressed file
  ↓
Object storage
  ↓
Short-lived download URL
```

Do not stream millions of database rows through a normal synchronous REST endpoint unless the architecture explicitly supports it.

---

## Security of Exported Data

Exports can contain highly sensitive information.

Potential risks include:

```text
PII
Financial information
Authentication-related data
Internal identifiers
Business data
Audit records
```

Apply:

- Least-privilege database roles
- Column-level selection
- Data minimization
- Encryption at rest
- Encryption in transit
- Restricted object storage access
- Short-lived download URLs
- Retention policies
- Audit logging

Do not create a full database export when only a small subset of fields is required.

---

## Protecting Export Files

For object storage such as S3, a typical pattern is:

```text
Private bucket
    ↓
Encrypted object
    ↓
Restricted IAM access
    ↓
Short-lived signed download
```

Avoid:

```text
Public bucket
```

or long-lived public URLs for sensitive exports.

---

## Credentials and Connection Security

Never embed credentials in commands such as:

```bash
psql postgresql://user:password@host/db
```

because credentials can become visible through:

```text
Shell history
Process listings
CI logs
Terminal recordings
Monitoring
```

Use:

```text
Secret manager
Environment injection
IAM/workload identity
Approved credential mechanisms
```

depending on the environment.

---

## Data Masking

Production exports used for development should generally be sanitized.

Example:

```text
Production
    ↓
Restricted export
    ↓
Mask / anonymize
    ↓
Development
```

Do not copy production customer data directly into developer environments simply because it makes debugging easier.

---

## `pg_dump`

`pg_dump` creates a logical backup of a PostgreSQL database.

Basic SQL-format dump:

```bash
pg_dump \
  -h db.example.com \
  -U backup_user \
  -d application \
  > application.sql
```

This contains SQL statements that can recreate database objects and data.

---

## Custom Format

For larger or more flexible backups:

```bash
pg_dump \
  -Fc \
  -h db.example.com \
  -U backup_user \
  -d application \
  -f application.dump
```

Custom format works well with:

```text
pg_restore
```

and provides more restore flexibility than a plain SQL script.

---

## Directory Format

For parallel dump/restore workflows:

```bash
pg_dump \
  -Fd \
  -j 4 \
  -h db.example.com \
  -U backup_user \
  -d application \
  -f application.dumpdir
```

Directory format supports parallel dump operations.

The appropriate degree of parallelism depends on:

```text
CPU
Disk
Network
Database workload
Target environment
```

---

## `pg_restore`

Restore a custom-format dump:

```bash
pg_restore \
  -h localhost \
  -U app_owner \
  -d application \
  application.dump
```

For a clean rebuild:

```bash
pg_restore \
  --clean \
  --if-exists \
  -h localhost \
  -U app_owner \
  -d application \
  application.dump
```

Use destructive restore options only when the target environment is known and the consequences are understood.

---

## Parallel Restore

With a directory or custom-format archive where supported:

```bash
pg_restore \
  -j 4 \
  -h localhost \
  -U app_owner \
  -d application \
  application.dump
```

Parallelism can significantly improve restore speed for large databases.

It also increases resource consumption, so more workers are not always better.

---

## `pg_dump` vs Physical Backups

`pg_dump` is a **logical backup**.

It differs from physical PostgreSQL backup mechanisms.

| Characteristic | Logical dump | Physical backup |
|---|---|---|
| Tool | `pg_dump` | Base backup/WAL mechanisms |
| Granularity | Database/object | Cluster/storage |
| Portability | High | Lower |
| Selective restore | Strong | Limited |
| PITR | Not by itself | Supports PITR with WAL |
| Large database restore | Usually slower | Often faster |
| Schema migration | Useful | Not primary purpose |

For serious disaster recovery, logical dumps and physical backups often serve different purposes.

---

## `pg_dumpall`

`pg_dumpall` can dump cluster-level information, including global objects such as roles.

Example:

```bash
pg_dumpall \
  --globals-only \
  -h db.example.com \
  -U backup_user \
  > globals.sql
```

This is useful for preserving:

```text
Roles
Tablespaces
Other cluster-wide global definitions
```

Do not confuse database-level `pg_dump` with cluster-wide logical metadata.

---

## Schema-Only Dumps

To export only database structure:

```bash
pg_dump \
  --schema-only \
  -h db.example.com \
  -U backup_user \
  -d application \
  > schema.sql
```

Useful for:

```text
Schema review
Environment comparison
Migration investigation
Documentation
Rebuilding empty environments
```

---

## Data-Only Dumps

To export data without schema definitions:

```bash
pg_dump \
  --data-only \
  -h db.example.com \
  -U backup_user \
  -d application \
  > data.sql
```

This can be useful for controlled migrations, but dependencies and load ordering must be considered.

---

## Selecting Specific Tables

Export selected tables:

```bash
pg_dump \
  -t app.customers \
  -t app.orders \
  -h db.example.com \
  -U backup_user \
  -d application \
  > selected.sql
```

This is useful when migrating a subset of a database.

However, related dependencies may not be included automatically in the way you expect. Verify the resulting dump before relying on it.

---

## Excluding Tables

Example:

```bash
pg_dump \
  --exclude-table=app.audit_events \
  -h db.example.com \
  -U backup_user \
  -d application \
  > application.sql
```

This can reduce dump size, but excluded data may be required for application correctness or recovery.

Document intentional exclusions.

---

## Dumping Large Databases

Large database dumps can create substantial:

```text
CPU usage
Disk I/O
Network traffic
Storage usage
Backup duration
Replica impact
```

Use appropriate:

```text
Compression
Parallelism
Replica/offload strategies
Storage capacity
Monitoring
```

and test actual restore times.

A backup that cannot be restored within the required RTO is not an adequate recovery strategy.

---

## Restore Testing

A backup should be periodically restored into an isolated environment.

Workflow:

```mermaid
flowchart LR
    Backup[Backup] --> Restore[Restore Test]
    Restore --> Validate[Validate Schema]
    Validate --> ValidateData[Validate Critical Data]
    ValidateData --> Measure[Measure Restore Time]
    Measure --> Report[Recovery Evidence]
```

Validate:

- Database starts
- Roles are present where required
- Schema exists
- Critical tables exist
- Indexes exist
- Constraints exist
- Application can connect
- Critical queries work
- Restore duration meets RTO

Backup success alone is not proof of recoverability.

---

## Import/Export and Replication

Large imports generate WAL.

That WAL can increase:

```text
Replica traffic
Replica lag
Archive storage
Recovery workload
```

Monitor:

```sql
SELECT
    application_name,
    state,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication;
```

The exact columns available depend on PostgreSQL version.

A bulk load can therefore affect the entire replication topology.

---

## Import/Export and HA

If a primary database is under heavy import load:

```text
CPU ↑
I/O ↑
WAL ↑
Replication traffic ↑
Replica lag ↑
Application latency ↑
```

Use:

```text
Rate limiting
Scheduling
Staging
Batching
Dedicated workers
Read replicas for exports
```

when appropriate.

---

## Import/Export and Kafka

Kafka can be used as an ingestion layer:

```text
External producer
       ↓
Kafka
       ↓
Consumer
       ↓
PostgreSQL staging
       ↓
Validation
       ↓
Business tables
```

This provides:

- Buffering
- Replay
- Backpressure
- Decoupling

But it does not automatically provide database transactionality. Consumer idempotency and database transaction boundaries still matter.

---

## Import/Export and Celery

Celery is useful for asynchronous imports and exports.

Example:

```text
REST API
   ↓
Create import record
   ↓
Celery task
   ↓
Download/read source
   ↓
COPY into staging
   ↓
Validate
   ↓
Promote
   ↓
Update status
```

The task should be:

```text
Retryable
Idempotent
Observable
Bounded
```

Avoid a task that loads an unbounded file into Python memory.

---

## Application-Level CSV Processing

Python can process CSV files, but avoid row-by-row ORM inserts for large datasets.

Inefficient:

```text
CSV
 ↓
Python loop
 ↓
Django ORM create()
 ↓
One database operation per row
```

Prefer:

```text
CSV
 ↓
Validated batch
 ↓
COPY / bulk operation
 ↓
PostgreSQL
```

The ORM remains useful for business-level operations, while PostgreSQL bulk-loading mechanisms are better suited to large data movement.

---

## Monitoring Import Jobs

Track:

```text
Rows processed
Rows rejected
Rows inserted
Rows updated
Rows duplicated
Duration
Throughput
Errors
Database latency
WAL generation
Replication lag
Disk usage
Worker state
```

For an import of one million rows, knowing only:

```text
"job failed"
```

is insufficient.

Operational metadata should explain where and why it failed.

---

## Failure Handling

An import can fail because of:

```text
Invalid data
Constraint violation
Connection failure
Disk exhaustion
Timeout
Deadlock
Replication pressure
Network interruption
Worker termination
Malformed CSV
Unexpected schema
```

A robust pipeline should define:

```text
Retry policy
Rollback behavior
Partial-load behavior
Dead-letter/rejection handling
Operator visibility
Cleanup strategy
```

Do not automatically retry every database failure.

A retry of a non-idempotent import can create duplicates or amplify database load.

---

## Operational Checkpoints

For large imports, record checkpoints such as:

```text
File received
File validated
Rows staged
Validation completed
Promotion started
Promotion completed
Export generated
Artifact uploaded
```

This makes failures easier to diagnose and allows operators to determine whether work needs to be repeated.

---

## Data Validation Strategy

A strong import pipeline validates at multiple levels.

### File-Level

```text
Expected format
Encoding
Header
File size
Checksum
Expected columns
```

### Row-Level

```text
Types
Required fields
Value ranges
Formats
```

### Relational

```text
Foreign keys
Uniqueness
References
```

### Business-Level

```text
Allowed states
Cross-field rules
Domain invariants
```

### Post-Load

```text
Row counts
Aggregates
Checksums
Expected relationships
```

This layered validation reduces the chance of silently corrupting production data.

---

## Checksums and File Integrity

For large transfers, verify file integrity.

Example:

```bash
sha256sum orders.csv
```

Record the checksum alongside the import metadata.

After transfer:

```bash
sha256sum orders.csv
```

Compare the values.

This does not prove the data is semantically correct, but it verifies that the file content did not change during transfer.

---

## Cost Considerations

Data movement can be expensive because of:

- Database I/O
- Network transfer
- Object storage
- Compression CPU
- Backup storage
- Cross-region traffic
- Worker compute
- Replica capacity

For AWS architectures, consider where data is moving:

```text
PostgreSQL
   ↓
EC2 / ECS / EKS
   ↓
S3
```

versus:

```text
PostgreSQL
   ↓
Cross-region transfer
   ↓
S3
```

Network topology can materially affect both cost and performance.

---

## Production Best Practices

- Prefer `COPY` for large PostgreSQL bulk loads.
- Use `\copy` when the source/destination file exists on the client.
- Explicitly specify import columns.
- Use staging tables for untrusted or complex imports.
- Validate before promoting data.
- Make imports idempotent where retries are possible.
- Monitor WAL and replica lag during large loads.
- Use asynchronous workers for large API-driven imports/exports.
- Keep sensitive exports encrypted and access-controlled.
- Test logical backup restoration regularly.
- Measure actual restore time against RTO.
- Version and review reusable operational SQL.
- Keep production data out of development environments unless appropriately sanitized.

---

## Common Mistakes

### Using `COPY` When the File Is on the Laptop

Server-side `COPY` expects the file from the PostgreSQL server's perspective.

Use:

```text
\copy
```

when the file is on the client.

### Loading Millions of Rows Through ORM `.save()`

This introduces substantial per-row overhead.

Use PostgreSQL bulk loading where appropriate.

### Exporting `SELECT *`

This can unnecessarily expose sensitive data and generate large files.

Select only required columns.

### Importing Directly Into Business Tables

External data can violate domain assumptions.

Use staging and validation for complex or untrusted data.

### Ignoring Replica Lag

A large import generates WAL and can delay replicas.

Monitor replication during bulk operations.

### Running Huge Exports on the Primary

Large scans can compete with application traffic.

Use an appropriate read replica when consistency requirements permit.

### Assuming a Successful Dump Means Successful Recovery

A dump can exist while the restore process remains untested.

Regularly perform restore tests.

### Retrying Non-Idempotent Imports

A worker retry can duplicate data.

Design imports around stable identifiers, unique constraints, or batch-level idempotency.

### Keeping Large Imports Inside HTTP Requests

Large database operations can exceed:

```text
HTTP timeout
Load balancer timeout
Application worker timeout
Client timeout
```

Use asynchronous jobs.

### Disabling Constraints Without a Recovery Plan

This can introduce invalid production data that is difficult to repair.

Preserve database integrity whenever possible.

### Ignoring Export Security

A CSV containing production customer data is sensitive even if the database itself is protected.

Secure the exported artifact with the same seriousness as the source data.

---

## Interview Traps

### What is the difference between `COPY` and `\copy`?

`COPY` is a PostgreSQL SQL command whose file access is server-side. `\copy` is a `psql` command that transfers data through the client.

### Why is `COPY` faster than individual inserts?

It reduces per-row statement and protocol overhead and uses PostgreSQL's bulk data-loading path.

### Should you always disable indexes before a large import?

No. Removing indexes can improve loading performance in some controlled scenarios, but it changes query performance, may remove integrity protections, and can create expensive rebuild operations.

### Does `COPY` bypass constraints?

No. Normal table constraints and other database behavior still matter.

### Why use a staging table?

It separates raw external data from trusted business data and provides a place to validate and transform records before promotion.

### Why can a large export affect PostgreSQL even though it is read-only?

Large reads consume CPU, memory, I/O, network bandwidth, and potentially long-lived snapshots that can interfere with maintenance.

### Why is a logical dump not the same as a physical backup?

A logical dump represents database objects and data logically and is portable/selective. Physical backup operates at the PostgreSQL storage/cluster level and can support physical recovery and PITR workflows.

### Why should imports be idempotent?

Distributed workers can retry after uncertain failures. Without idempotency, a retry can duplicate or corrupt data.

---

## Key Takeaways

- **Use the right PostgreSQL data-movement mechanism:** `COPY` is the native bulk path, while `\copy` is the client-side mechanism for files accessible to `psql`; `pg_dump` and `pg_restore` serve logical backup and restore workflows.
- **Treat imports as controlled data pipelines:** stage external data when appropriate, validate file/row/relational/business rules, preserve constraints, and promote only validated records.
- **Design large transfers around production workload behavior:** monitor CPU, I/O, WAL, transaction duration, disk usage, and replica lag rather than measuring only import/export throughput.
- **Make asynchronous data movement retryable and secure:** use Celery/Kubernetes workers where appropriate, design idempotent operations, protect exported data, and avoid exposing production datasets unnecessarily.
- **A backup is only useful if it can be recovered:** test `pg_dump`/`pg_restore` workflows and measure real restore times against disaster-recovery requirements.