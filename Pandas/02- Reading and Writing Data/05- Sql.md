# 05- Sql

## Overview

Pandas integrates closely with SQL databases, making it useful for extracting relational data into DataFrames, transforming bounded datasets, validating results, generating reports, and writing processed data back to database tables.

The key APIs are:

```python
pd.read_sql()
pd.read_sql_query()
pd.read_sql_table()
DataFrame.to_sql()
```

A typical production workflow is:

```text
PostgreSQL / SQL Database
          ↓
     SQL Query
          ↓
      Pandas
          ↓
Validation + Transformation
          ↓
Aggregation / Reporting
          ↓
PostgreSQL / Parquet / API
```

The important architectural principle is that Pandas and SQL solve different problems.

```text
SQL database
→ persistence, transactions, joins, filtering, aggregation

Pandas
→ in-memory transformation, validation, analysis, reporting
```

Do not move data into Pandas simply because Pandas can express an operation. For large relational datasets, push filtering, projection, joins, and aggregations into the database whenever doing so is efficient and semantically appropriate.

## Why Pandas and SQL Work Well Together

SQL databases are optimized for:

- Persistent storage.
- Indexed lookups.
- Relational joins.
- Filtering.
- Aggregation.
- Transactions.
- Concurrent access.
- Constraints.

Pandas is optimized for:

- In-memory tabular transformation.
- Data cleaning.
- Flexible column operations.
- Batch-oriented processing.
- Reporting.
- Data-quality analysis.
- Integration with Python code.

A mature data pipeline chooses the execution layer deliberately.

```text
Can PostgreSQL perform it efficiently?
        ↓
       Yes
        ↓
Push down to SQL

       No / better in Python
        ↓
Load the reduced dataset
        ↓
Process with Pandas
```

This is one of the most important performance decisions in SQL-to-Pandas workflows.

## Reading SQL Query Results

The common API is:

```python
import pandas as pd

orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        status,
        amount,
        created_at
    FROM orders
    WHERE created_at >= %(start_date)s
    """,
    connection,
    params={
        "start_date": start_date,
    },
)
```

The result is a DataFrame.

This is usually preferable to:

```sql
SELECT *
FROM orders;
```

followed by dropping unnecessary columns in Python.

The SQL query can reduce:

```text
Rows transferred
Columns transferred
Database-to-application network traffic
Pandas memory usage
Transformation cost
```

## `read_sql()`

`read_sql()` is a convenience function that can work with either a SQL query or table-oriented input depending on the connection and arguments supplied.

For explicit query workflows:

```python
orders = pd.read_sql_query(
    query,
    connection,
)
```

is often clearer because it communicates that the source is a SQL statement.

## `read_sql_query()`

Use `read_sql_query()` when the source is a SQL query:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        amount
    FROM orders
    WHERE status = %(status)s
    """,
    connection,
    params={
        "status": "completed",
    },
)
```

The SQL engine performs the filtering before the result reaches Pandas.

This is usually preferable for large tables.

## `read_sql_table()`

When supported by the connection backend, `read_sql_table()` can load a database table:

```python
orders = pd.read_sql_table(
    "orders",
    connection,
    columns=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

Use it when table-oriented extraction is appropriate.

For production ETL, explicit SQL is often preferable when the query needs:

- Filters.
- Joins.
- Derived fields.
- Aggregations.
- Window functions.
- Database-specific optimization.

## Query Projection

Project only required columns:

```sql
SELECT
    order_id,
    customer_id,
    amount
FROM orders;
```

Avoid:

```sql
SELECT *
FROM orders;
```

unless all columns are genuinely required.

Projection reduces:

```text
Database output
        ↓
Network transfer
        ↓
DataFrame columns
        ↓
Memory footprint
```

This is especially important when processing large PostgreSQL tables from containerized or cloud workers.

## SQL Filtering vs Pandas Filtering

Compare:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        amount
    FROM orders
    WHERE status = %(status)s
    """,
    connection,
    params={
        "status": "completed",
    },
)
```

with:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        amount,
        status
    FROM orders
    """,
    connection,
)

orders = orders.loc[
    orders["status"].eq("completed")
]
```

The first approach is generally preferable when the filtering condition belongs naturally in SQL and can be efficiently executed there.

The second may be useful when the filter is dynamic, complex, or part of a transformation that genuinely belongs in the Pandas layer.

## SQL Aggregation vs Pandas Aggregation

Suppose a report requires customer revenue.

SQL:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

Pandas equivalent:

```python
summary = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        order_count=("order_id", "count"),
        revenue=("amount", "sum"),
    )
)
```

For large source tables, the SQL version will often be preferable because it reduces the amount of data transferred to the application.

The Pandas version is useful when the data is already in memory or when additional Python-side transformation is required.

## Pushdown Principle

A useful rule is:

```text
Filter in SQL
Project in SQL
Join in SQL when efficient
Aggregate in SQL when appropriate
Transform in Pandas when Python adds value
```

For example:

```text
10 billion database rows
        ↓
SQL filter
        ↓
10 million relevant rows
        ↓
SQL projection
        ↓
5 columns
        ↓
Pandas
```

This is usually much more practical than moving billions of rows into memory.

## Database-to-DataFrame Flow

```mermaid
flowchart LR
    A[PostgreSQL] --> B[SQL Query]
    B --> C[Filter / Projection / Join]
    C --> D[Result Set]
    D --> E[Pandas DataFrame]
    E --> F[Validation]
    F --> G[Transformation]
    G --> H[Reporting / Parquet / Database]
```

The boundary between SQL and Pandas should be intentional.

## Parameterized SQL

Never build queries by string interpolation with untrusted values:

```python
query = (
    "SELECT * FROM orders "
    f"WHERE customer_id = {customer_id}"
)
```

Instead use parameters supported by the DB-API driver:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        amount
    FROM orders
    WHERE customer_id = %(customer_id)s
    """,
    connection,
    params={
        "customer_id": customer_id,
    },
)
```

Parameterization protects against SQL injection and separates query structure from user-provided values.

## SQL Injection

Pandas does not make unsafe SQL safe.

The SQL execution layer remains responsible for:

```text
Authentication
Authorization
Parameterization
Connection security
SQL injection prevention
```

Use trusted SQL text and bound parameters.

Do not concatenate:

```text
User input
File input
API input
```

directly into SQL.

## Database Connection Management

Pandas should receive a properly managed database connection.

A production application should define:

```text
Connection acquisition
      ↓
Query execution
      ↓
Result processing
      ↓
Connection release
```

For SQLAlchemy-based environments:

```python
from sqlalchemy import create_engine, text

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

with engine.begin() as connection:
    orders = pd.read_sql_query(
        text(
            """
            SELECT
                order_id,
                amount
            FROM orders
            WHERE status = :status
            """
        ),
        connection,
        params={
            "status": "completed",
        },
    )
```

Use the application's established connection-pooling and credential-management strategy rather than creating a new database connection for every row or batch.

## Connection Pooling

In backend systems, database connections are expensive resources.

Do not do:

```python
for partition in partitions:
    connection = create_connection()
    process(partition)
    connection.close()
```

unless there is a very specific reason.

Prefer a managed pool:

```text
Application / Worker
        ↓
SQLAlchemy pool
        ↓
PostgreSQL
```

This is particularly important for Kubernetes deployments where multiple worker replicas can otherwise exhaust PostgreSQL connection limits.

## Transaction Boundaries

Reading data generally does not need a long application-level transaction.

Writing processed data does.

For example:

```text
Read source
   ↓
Process outside transaction
   ↓
Open transaction
   ↓
Persist validated batch
   ↓
Commit
```

Avoid holding a database transaction open while performing expensive Pandas transformations.

Long transactions can cause:

- Lock retention.
- Bloat.
- Resource consumption.
- Increased contention.

## Reading Large Query Results

Do not assume a SQL query returning millions of rows is safe simply because PostgreSQL can execute it.

The result still has to be materialized or processed by the application.

For large results, use bounded reads where supported:

```python
for chunk in pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        amount
    FROM orders
    WHERE created_at >= %(start_date)s
    """,
    connection,
    params={
        "start_date": start_date,
    },
    chunksize=100_000,
):
    process_chunk(chunk)
```

This changes the flow from:

```text
Entire result
    ↓
One DataFrame
```

to:

```text
100K-row batch
    ↓
Process
    ↓
Next batch
```

## Chunk Size

There is no universal optimal `chunksize`.

The useful size depends on:

```text
Row width
Dtypes
Transformation complexity
Database throughput
Network bandwidth
Worker memory
Target write batch size
```

Too small:

```text
More round trips
More Python overhead
More database writes
```

Too large:

```text
Higher peak memory
Longer retries
Larger failure units
```

Benchmark using representative production-like data.

## Chunked Query Architecture

```text
PostgreSQL
    ↓
Bounded result batch
    ↓
Pandas
    ↓
Validate
    ↓
Transform
    ↓
Persist
    ↓
Next batch
```

This is useful for:

- Celery workers.
- Kubernetes Jobs.
- Scheduled ETL.
- AWS batch workloads.
- Large report generation.

## Pagination vs Chunked SQL Reads

These solve related but different problems.

| Technique | Typical boundary | Useful for |
|---|---|---|
| SQL `chunksize` | Database result stream/batch | Large query results |
| API pagination | HTTP response page | REST APIs |
| Keyset pagination | Database query boundary | Very large ordered datasets |
| Offset pagination | Database page offset | Simpler but less scalable pagination |
| Partitioned processing | Storage/data boundary | Large historical datasets |

Choose based on the source and workload.

## Avoid Offset Pagination for Large Tables When Possible

For large ordered tables, repeatedly using:

```sql
OFFSET 10000000
LIMIT 100000;
```

can become increasingly expensive.

A keyset-style approach is often better:

```sql
SELECT
    order_id,
    customer_id,
    amount
FROM orders
WHERE order_id > %(last_order_id)s
ORDER BY order_id
LIMIT %(batch_size)s;
```

Then process:

```python
last_order_id = 0

while True:
    batch = pd.read_sql_query(
        query,
        connection,
        params={
            "last_order_id": last_order_id,
            "batch_size": 100_000,
        },
    )

    if batch.empty:
        break

    process_batch(batch)

    last_order_id = int(
        batch["order_id"].max()
    )
```

This requires a stable ordering key and careful handling of inserts, deletes, and business semantics.

## Database Indexes

SQL-side filtering should be supported by appropriate database indexing when needed.

For example:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

Pandas cannot compensate for an inefficient database access path.

When investigating a slow extraction:

```text
Pandas code
    ↓
SQL query
    ↓
Execution plan
    ↓
Indexes / statistics / joins
```

Inspect the database query plan rather than optimizing only Python code.

## Explain Plans

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    order_id,
    customer_id,
    amount
FROM orders
WHERE created_at >= '2026-09-01';
```

This helps determine whether the database is performing:

```text
Index scan
Sequential scan
Expensive join
Sort
Hash aggregation
```

Do not assume that moving computation into SQL automatically makes it faster.

Measure the query plan.

## SQL Join vs Pandas Merge

Suppose:

```text
orders → millions of rows
customers → millions of rows
```

A relational join can often be executed efficiently in PostgreSQL:

```sql
SELECT
    o.order_id,
    o.amount,
    c.segment
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id;
```

The equivalent Pandas merge:

```python
orders.merge(
    customers,
    on="customer_id",
    how="inner",
)
```

requires the relevant datasets to be materialized in the application.

Prefer database-side joins when:

- Both datasets already live in the same database.
- The database can execute the join efficiently.
- The output is much smaller than the inputs.
- Network transfer would otherwise be large.

Pandas merges are appropriate when the inputs are already in memory or when one source is outside the database.

## Cross-System Joins

Pandas becomes especially useful when data comes from different systems:

```text
PostgreSQL
      ↓
Orders DataFrame

REST API
      ↓
Customer DataFrame

      ↓
Pandas merge
      ↓
Unified dataset
```

For example:

```python
orders = pd.read_sql_query(
    orders_query,
    connection,
)

customer_profiles = pd.json_normalize(
    api_payload["customers"]
)

result = orders.merge(
    customer_profiles,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

This is a strong use case because the join cannot be performed entirely inside one database.

## Join Cardinality

Always understand the relationship:

```text
one-to-one
one-to-many
many-to-one
many-to-many
```

For example:

```python
result = orders.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

If the customer table unexpectedly contains duplicate keys, the merge should fail rather than silently multiplying rows.

## SQL Nulls and Pandas Missing Values

SQL `NULL` becomes a Pandas missing value representation.

For example:

```sql
SELECT
    order_id,
    discount
FROM orders;
```

may produce:

```python
orders["discount"].isna()
```

Use explicit missing-value semantics after ingestion.

Do not assume:

```text
NULL = 0
```

unless the domain contract says so.

## SQL `COALESCE` vs Pandas `fillna`

SQL:

```sql
SELECT
    COALESCE(discount, 0) AS discount
FROM orders;
```

Pandas:

```python
orders["discount"] = (
    orders["discount"]
    .fillna(0)
)
```

Both can implement the same logical rule, but the correct location depends on where the business rule belongs.

Use SQL when:

- The default is part of database/reporting logic.
- Reducing transferred data matters.
- The same rule is needed by multiple consumers.

Use Pandas when:

- The rule is specific to the processing pipeline.
- The source should remain semantically nullable.
- Additional Python-side validation determines the final behavior.

## SQL Types and Pandas Dtypes

Database schemas and Pandas dtypes do not map one-to-one.

Examples:

| PostgreSQL type | Typical Pandas representation |
|---|---|
| `BIGINT` | `int64` / `Int64` |
| `INTEGER` | `int64` / `Int64` |
| `NUMERIC` | Decimal-like representation depending on driver and conversion |
| `BOOLEAN` | `bool` / `boolean` |
| `TEXT` | `string` |
| `TIMESTAMP` | `datetime64[ns]` or timezone-aware datetime |
| `TIMESTAMPTZ` | Timezone-aware datetime |

The actual result can depend on the DB driver and SQLAlchemy configuration.

For critical pipelines, inspect and normalize dtypes rather than assuming an exact mapping.

## Decimal and Financial Data

PostgreSQL `NUMERIC` is designed for exact decimal semantics.

Do not casually convert financial values into binary floating point:

```python
orders["amount"] = (
    orders["amount"]
    .astype(float)
)
```

when exact accounting semantics matter.

Depending on the workflow, preserve decimal values or convert to an integer minor-unit representation.

The important principle is:

```text
Database precision contract
        ↓
Pandas representation
        ↓
Output precision contract
```

should remain consistent.

## Timezones

PostgreSQL can store timezone-aware timestamps using `TIMESTAMPTZ`.

When they enter Pandas:

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
)
```

Canonical UTC processing is generally easier for distributed ETL.

Be careful when converting timezone-naive timestamps because assigning a timezone is different from converting an already timezone-aware timestamp.

## Writing DataFrames to SQL

Use:

```python
orders.to_sql(
    "staging_orders",
    connection,
    if_exists="append",
    index=False,
)
```

This is useful for:

- Staging tables.
- Batch imports.
- Temporary analysis tables.
- Controlled ETL outputs.

It should not automatically be used as the final database-write strategy for all production workloads.

## `if_exists`

Common options include:

| Value | Behavior | Production consideration |
|---|---|---|
| `fail` | Error if table exists | Safest default when accidental overwrite is unacceptable |
| `replace` | Drop and recreate table | Dangerous for production tables |
| `append` | Add rows | Common for staging/batch ingestion |

Avoid:

```python
if_exists="replace"
```

for production tables unless destructive replacement is explicitly part of the workflow and is fully controlled.

## Batch Size with `to_sql`

For large inserts:

```python
orders.to_sql(
    "staging_orders",
    connection,
    if_exists="append",
    index=False,
    chunksize=10_000,
)
```

This can reduce the size of individual database operations.

The optimal batch size depends on:

```text
Row width
Database configuration
Driver behavior
Transaction size
Network latency
Target table indexes
```

Benchmark against representative workloads.

## Transactions During Writes

A production write should have a deliberate transaction boundary.

For example:

```python
from sqlalchemy import create_engine

engine = create_engine(
    database_url,
)

with engine.begin() as connection:
    orders.to_sql(
        "staging_orders",
        connection,
        if_exists="append",
        index=False,
        chunksize=10_000,
    )
```

If the operation fails, the transaction context can roll back the work performed within that transaction boundary.

Transaction behavior can vary with driver and database configuration, so test the exact write path.

## Staging Tables

A robust database ingestion workflow often uses:

```text
Pandas
   ↓
staging_orders
   ↓
Validation / SQL transformation
   ↓
target_orders
```

This separates:

```text
Raw ingestion
```

from:

```text
Canonical production state
```

Staging tables are particularly useful when:

- Data requires further SQL validation.
- Loads need auditing.
- Upserts are required.
- Source batches need replay.
- Raw records should be preserved.

## Upserts

`to_sql()` is not inherently a complete upsert framework.

For production upsert behavior, use database-specific SQL or a SQLAlchemy-based strategy.

For PostgreSQL:

```sql
INSERT INTO orders (
    order_id,
    customer_id,
    amount
)
VALUES
    (...)
ON CONFLICT (order_id)
DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    amount = EXCLUDED.amount;
```

Pandas can prepare the data, but PostgreSQL should usually enforce the final uniqueness and conflict semantics.

## DataFrame-to-Database Architecture

```mermaid
flowchart LR
    A[API / CSV / Parquet] --> B[Pandas]
    B --> C[Normalize]
    C --> D[Validate]
    D --> E[Staging Table]
    E --> F[SQL Constraints / Transform]
    F --> G[Production Table]
```

This architecture keeps the DataFrame layer focused on preparation while the database maintains durable integrity.

## Indexes and Bulk Loading

Database indexes improve query performance but can also increase write cost.

If loading a very large batch:

```text
Insert rows
    ↓
Maintain indexes
    ↓
Write amplification
```

may become expensive.

Use an ingestion architecture appropriate to the database and workload, such as:

```text
COPY
staging tables
batch inserts
partitioned tables
```

when scale requires it.

For very large PostgreSQL loads, `COPY` is often more appropriate than row-oriented insert generation through `to_sql()`.

## When `to_sql()` Is Appropriate

`to_sql()` is useful for:

- Moderate-sized staging loads.
- Internal data-processing jobs.
- Controlled batch exports.
- Temporary analytical tables.
- Prototypes that can later be replaced with specialized loaders.

Consider a lower-level database-native loading mechanism when:

```text
Dataset is very large
Write throughput is critical
Target table has complex constraints
Upsert semantics are required
Exact transaction behavior is important
```

## SQL and Pandas Validation

Pandas can validate before persistence:

```python
required = [
    "order_id",
    "customer_id",
    "amount",
]

invalid = (
    orders[required]
    .isna()
    .any(axis=1)
)

if invalid.any():
    raise ValueError(
        "Required fields are missing"
    )
```

The database should still enforce:

```text
NOT NULL
UNIQUE
PRIMARY KEY
FOREIGN KEY
CHECK
```

where applicable.

Do not depend on application-level validation alone.

## Database Constraints as Final Authority

Consider:

```sql
ALTER TABLE orders
ADD CONSTRAINT orders_amount_non_negative
CHECK (amount >= 0);
```

Pandas can validate the same rule:

```python
if orders["amount"].lt(0).any():
    raise ValueError(
        "Negative order amount detected"
    )
```

This redundancy can be useful.

```text
Pandas validation
→ fail early

Database constraint
→ protect durable state
```

The two layers serve different purposes.

## Incremental Processing

A practical incremental workflow is:

```text
Last successful watermark
        ↓
SQL query
        ↓
New records only
        ↓
Pandas processing
        ↓
Output
        ↓
Commit watermark
```

For example:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    updated_at
FROM orders
WHERE updated_at > %(last_watermark)s
ORDER BY updated_at, order_id;
```

A robust implementation may use both:

```text
updated_at
+
order_id
```

to establish a deterministic ordering when timestamps are not unique.

## Watermarks

A watermark records how far a pipeline has successfully processed.

Example:

```text
last_processed_updated_at
```

However, timestamp-only watermarks can be unsafe when multiple records share the same timestamp.

A compound checkpoint can be more robust:

```text
(updated_at, order_id)
```

The implementation should ensure that records at the boundary cannot be skipped during retries.

## Idempotent Database Loads

Retries are normal in:

- Celery.
- Kubernetes Jobs.
- AWS batch pipelines.
- Scheduled ETL.

Use database uniqueness and deterministic processing:

```text
Read batch
    ↓
Normalize
    ↓
Validate
    ↓
Upsert
    ↓
Commit
    ↓
Advance watermark
```

Never advance a checkpoint before the corresponding database transaction succeeds.

## Failure and Retry Ordering

A dangerous sequence is:

```text
Process batch
    ↓
Advance watermark
    ↓
Database write fails
```

The next retry may skip the failed records.

Safer:

```text
Read batch
    ↓
Process
    ↓
Write transaction
    ↓
Commit
    ↓
Advance checkpoint
```

The checkpoint must represent successfully persisted work.

## SQL and Parquet

A useful hybrid architecture is:

```text
PostgreSQL
    ↓
Filtered / aggregated SQL
    ↓
Pandas
    ↓
Validation
    ↓
Parquet
    ↓
S3
```

This is useful when:

- PostgreSQL is the source of transactional truth.
- Historical data needs analytical storage.
- Query workloads should not compete with production transactions.
- Downstream systems use object storage.

## Large Dataset Architecture

For very large relational datasets:

```text
PostgreSQL
    ↓
SQL pushdown
    ↓
Bounded result
    ↓
Pandas chunk
    ↓
Transformation
    ↓
Parquet partition
    ↓
S3
```

This architecture combines:

```text
Database execution
+
bounded in-memory processing
+
columnar storage
```

rather than treating Pandas as the only processing engine.

## Read Replicas

Analytical extraction can place load on transactional databases.

Where appropriate:

```text
Application writes
     ↓
Primary PostgreSQL

Pandas ETL
     ↓
Read replica
```

This can reduce interference with transactional workloads.

The replica must be sufficiently current for the ETL's freshness requirements.

Do not assume replication lag is irrelevant.

## Resource Isolation

For scheduled reporting or large ETL:

```text
Production API workers
        ↓
PostgreSQL primary

Data worker
        ↓
Read replica / analytics database
```

This is often preferable to running large Pandas queries directly from request-serving processes.

Docker and Kubernetes resource requests/limits should reflect expected:

```text
CPU
Memory
I/O
Concurrency
```

## Security Considerations

SQL-to-Pandas pipelines can expose sensitive data.

Use least privilege:

```text
ETL read role
    ↓
SELECT only required tables/columns
```

For writes:

```text
ETL write role
    ↓
staging schema only
```

Avoid giving a batch worker unrestricted database administrator privileges.

Also:

- Store credentials in a secrets manager.
- Use encrypted database connections.
- Avoid logging SQL parameters containing secrets.
- Avoid writing sensitive columns to Parquet unnecessarily.
- Minimize data transferred into Pandas.
- Apply row-level access controls where required.

## Credential Management

Do not hard-code:

```python
connection_url = (
    "postgresql://user:password@host/db"
)
```

Use environment-based or secret-manager-backed configuration:

```python
import os

database_url = os.environ[
    "DATABASE_URL"
]
```

In AWS, use appropriate managed secret mechanisms and workload identities rather than storing long-lived credentials in source control.

## SQL Query Logging

Avoid logging full SQL with sensitive parameters:

```python
logger.debug(
    "query=%s params=%s",
    query,
    params,
)
```

when parameters may contain confidential data.

Prefer metadata:

```python
logger.info(
    "orders_query_completed rows=%d",
    len(orders),
)
```

## Performance Monitoring

Monitor both database and Pandas stages.

Useful metrics include:

| Metric | Layer |
|---|---|
| Query duration | Database |
| Rows returned | Database / ETL |
| Bytes transferred | Database / network |
| DataFrame creation time | Pandas |
| Transformation time | Pandas |
| Peak memory | Worker |
| Rows written | Database |
| Insert duration | Database |
| Rejected records | Validation |
| Retry count | Workflow |
| Replication lag | Database |

This helps determine where the real bottleneck exists.

## Common Mistakes

### Loading Entire Tables into Pandas

```python
pd.read_sql(
    "SELECT * FROM orders",
    connection,
)
```

can exhaust worker memory.

**Better:** filter, project, aggregate, or chunk at the database boundary.

### Using Pandas for Work PostgreSQL Can Do Better

Moving a large join or aggregation into Python may increase network and memory costs.

**Better:** benchmark SQL pushdown versus Pandas processing.

### Building SQL with String Interpolation

```python
f"WHERE customer_id = {customer_id}"
```

can introduce SQL injection.

**Better:** use bound parameters.

### Holding Transactions Open During Pandas Processing

This can create locks and resource pressure.

**Better:** process outside the transaction and keep database transactions focused on persistence.

### Using `to_sql(if_exists="replace")` on Production Tables

This can destroy the existing table and schema.

**Better:** use staging tables and controlled migrations/upserts.

### Assuming `to_sql()` Is the Fastest Loader

For very large PostgreSQL loads, database-native bulk loading may be more efficient.

**Better:** evaluate `COPY`, staging, or specialized loaders.

### Ignoring Database Constraints

Application validation can contain bugs.

**Better:** enforce durable integrity in PostgreSQL as well.

### Advancing Watermarks Before Commit

This can cause data loss during retries.

**Better:** commit the output first, then advance the checkpoint.

### Ignoring Join Cardinality

A Pandas merge can multiply rows unexpectedly.

**Better:** use `validate=` and inspect source uniqueness.

### Reading from the Primary Database for Heavy Analytics

Large queries can interfere with transactional traffic.

**Better:** use read replicas or an analytical store where appropriate.

### Ignoring Replication Lag

A read replica may not contain the newest rows.

**Better:** define freshness requirements and monitor lag.

### Converting Exact Database Numerics to Float

This can introduce precision problems for financial values.

**Better:** preserve decimal semantics or use an exact business representation.

### Creating a New Database Connection for Every Batch

This adds connection overhead and can exhaust PostgreSQL connection capacity.

**Better:** use managed pooling.

### Logging Raw DataFrames or Sensitive SQL Parameters

This can expose customer or financial information.

**Better:** log counts, timing, schema, and safe operational metadata.

### Treating Pandas as the Transaction Boundary

Pandas transformations are not database transactions.

**Better:** use explicit database transactions for durable state changes.

## Interview Traps

### Should Filtering Be Done in SQL or Pandas?

Usually push filtering into SQL when the database can execute it efficiently and doing so reduces transferred data. Use Pandas when the transformation belongs in Python or the data is already materialized.

### Why Should `SELECT *` Usually Be Avoided?

It transfers unnecessary columns, increasing network traffic, DataFrame memory, parsing work, and downstream processing cost.

### What Is SQL Pushdown?

Executing a filtering, joining, projection, or aggregation operation in the source database instead of moving all raw data into Pandas first.

### How Do You Process a SQL Result Larger Than Memory?

Use bounded extraction such as:

```python
for chunk in pd.read_sql_query(
    query,
    connection,
    chunksize=100_000,
):
    process_chunk(chunk)
```

and persist or aggregate each batch.

### When Is a Pandas Merge Better Than a SQL Join?

When data comes from different systems, such as PostgreSQL plus an external API, or when the datasets are already in memory and Python-side transformation is appropriate.

### How Do You Prevent Pandas Merge Row Explosion?

Validate the expected relationship:

```python
df.merge(
    other,
    on="customer_id",
    validate="many_to_one",
)
```

### How Do SQL `NULL` and Pandas Missing Values Relate?

Database `NULL` values are generally represented as Pandas missing values after ingestion, but the exact dtype and representation depend on the database driver and Pandas dtype.

### Should `NULL` Always Become Zero?

No. The correct treatment depends on business semantics.

### Why Are Parameterized Queries Important?

They separate SQL structure from external values and protect against SQL injection.

### Why Use Staging Tables?

They provide a controlled boundary between raw or transformed batch data and production tables, making validation, auditing, retries, and upserts easier.

### Why Might `COPY` Be Better Than `to_sql()`?

For large PostgreSQL loads, `COPY` is designed for high-throughput bulk ingestion and can be substantially more efficient than generating many row-oriented inserts.

### How Should Incremental Processing Be Implemented?

Use a deterministic source watermark or keyset boundary, process the batch, persist successfully, commit, and only then advance the checkpoint.

### Should Heavy Pandas Queries Run Against the Primary Database?

Not necessarily. For operational systems, consider read replicas or analytical stores to isolate large extraction workloads.

### Does Pandas Provide Transaction Semantics?

No. Database transactions are provided by the database and its connection/transaction layer.

## Production ETL Pattern

A practical relational-to-Pandas pipeline is:

```python
import pandas as pd


def extract_orders(
    connection,
    start_date,
) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            order_id,
            customer_id,
            status,
            amount,
            created_at
        FROM orders
        WHERE created_at >= %(start_date)s
        """,
        connection,
        params={
            "start_date": start_date,
        },
    )


def normalize_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    result["status"] = (
        result["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    result["amount"] = (
        pd.to_numeric(
            result["amount"],
            errors="coerce",
        )
        .astype("Float64")
    )

    result["created_at"] = pd.to_datetime(
        result["created_at"],
        utc=True,
    )

    return result


def validate_orders(
    orders: pd.DataFrame,
) -> None:
    required = [
        "order_id",
        "customer_id",
        "amount",
    ]

    invalid = (
        orders[required]
        .isna()
        .any(axis=1)
    )

    if invalid.any():
        raise ValueError(
            "Required order fields are invalid"
        )

    if orders["amount"].lt(0).any():
        raise ValueError(
            "Order amount cannot be negative"
        )
```

Orchestrate explicitly:

```python
orders = extract_orders(
    connection,
    start_date,
)

orders = normalize_orders(
    orders
)

validate_orders(
    orders
)

persist_orders(
    orders
)
```

The responsibilities remain separated:

```text
SQL
→ extraction and source-side reduction

Pandas
→ normalization and transformation

Validation
→ schema and business rules

Database
→ durable integrity and persistence
```

## Production Chunk Processing Pattern

For larger datasets:

```python
for chunk in pd.read_sql_query(
    query,
    connection,
    params=params,
    chunksize=100_000,
):
    normalized = normalize_orders(
        chunk
    )

    validate_orders(
        normalized
    )

    persist_orders(
        normalized
    )
```

Before using this architecture in production, verify:

```text
Chunk transaction boundaries
Idempotency
Checkpointing
Duplicate handling
Database write throughput
Peak memory
Failure recovery
```

## Production Checklist

```text
[ ] Is SQL the right execution layer for filtering?
[ ] Are only required columns selected?
[ ] Are large aggregations pushed to PostgreSQL when appropriate?
[ ] Are SQL parameters bound safely?
[ ] Is the database connection pooled?
[ ] Is the ETL worker isolated from request-serving traffic?
[ ] Is a read replica appropriate for heavy extraction?
[ ] Is replication lag monitored?
[ ] Are large results processed in bounded batches?
[ ] Is chunksize appropriate for the worker memory budget?
[ ] Are join cardinalities validated?
[ ] Are SQL and Pandas dtypes normalized intentionally?
[ ] Are financial values protected from accidental float conversion?
[ ] Are required fields validated before persistence?
[ ] Are database constraints enforcing durable integrity?
[ ] Is data written through a staging or controlled ingestion path?
[ ] Is the write transaction boundary explicit?
[ ] Is `to_sql()` appropriate for the dataset size?
[ ] Should PostgreSQL COPY or another bulk loader be used?
[ ] Is incremental processing based on a reliable watermark?
[ ] Is the checkpoint advanced only after successful persistence?
[ ] Is processing idempotent under retries?
[ ] Are sensitive columns minimized?
[ ] Are credentials managed through secrets rather than source code?
[ ] Are query, transfer, transformation, and write durations monitored?
[ ] Are raw DataFrames and sensitive SQL parameters excluded from logs?
[ ] Is validated output stored in Parquet when repeated analytical access is expected?
```

## Key Takeaways

- Pandas and SQL are complementary: use PostgreSQL for persistence, relational execution, transactions, and source-side reduction, and use Pandas for bounded in-memory normalization, transformation, validation, and reporting.
- Push filtering, projection, joins, and aggregations into SQL when the database can perform them efficiently and doing so reduces network transfer and Pandas memory usage.
- For large datasets, use chunked or incremental extraction, explicit transaction boundaries, reliable watermarks, and idempotent writes rather than loading entire tables into memory.
- `to_sql()` is useful for controlled batch and staging workloads, but large PostgreSQL loads may require database-native bulk loading, staging tables, explicit upserts, and database constraints.
- Production SQL-to-Pandas pipelines should enforce parameterized queries, least-privilege database access, schema and dtype validation, observability, sensitive-data minimization, and recovery-safe checkpointing.