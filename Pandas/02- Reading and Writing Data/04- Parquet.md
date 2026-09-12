# 04- Parquet

## Overview

Parquet is a columnar storage format designed for efficient analytical workloads and is one of the most useful formats for production Pandas pipelines.

Unlike CSV and JSON, Parquet stores typed, structured data in a binary columnar representation. This makes it well suited to:

- ETL pipelines.
- Data lakes.
- Analytical batch processing.
- Intermediate pipeline storage.
- Historical datasets.
- Reporting workloads.
- Partitioned object-storage datasets.

A common backend/data-engineering flow is:

```text
REST API / CSV / Database
          ↓
      Pandas
          ↓
Validation + Transformation
          ↓
       Parquet
          ↓
S3 / Object Storage / Data Lake
          ↓
Pandas / DuckDB / Spark / Warehouse
```

Parquet should generally be viewed as a **machine-oriented analytical storage format**, not as a replacement for PostgreSQL transactional storage.

Its main advantages come from:

```text
Columnar storage
+ Typed schema
+ Compression
+ Encoding
+ Column projection
+ Predicate pushdown support in compatible readers
```

These characteristics can materially reduce I/O and memory usage for selective analytical workloads.

## What Parquet Is

Parquet is a binary columnar file format designed for efficient storage and retrieval of structured data.

A row-oriented representation conceptually stores:

```text
Row 1 → [order_id, customer_id, status, amount]
Row 2 → [order_id, customer_id, status, amount]
Row 3 → [order_id, customer_id, status, amount]
```

A columnar representation groups values by column:

```text
order_id     → [1001, 1002, 1003]
customer_id  → [101, 102, 101]
status       → ["completed", "pending", "completed"]
amount       → [250.0, 175.5, 500.0]
```

Analytical workloads frequently access only a subset of columns, so columnar storage can avoid reading unrelated data.

## Why Parquet Exists

CSV and similar row-oriented interchange formats are convenient but weak for repeated analytical workloads.

CSV:

```text
Text
Weak type preservation
Repeated parsing
Large representation
Column projection is limited
```

Parquet:

```text
Binary
Typed
Compressed
Columnar
Efficient for selective reads
```

The goal is to reduce the cost of repeatedly scanning structured datasets.

## Parquet vs CSV vs JSON

| Characteristic | CSV | JSON | Parquet |
|---|---|---|---|
| Human-readable | Yes | Yes | No |
| Binary | No | No | Yes |
| Columnar | No | No | Yes |
| Strong schema | Limited | Limited | Yes |
| Compression | External/file-level | External/file-level | Built in |
| Efficient column projection | Limited | Limited | Strong |
| Repeated analytics | Weak | Weak | Strong |
| Nested data | Limited | Natural | Supported |
| Typical role | Interchange | APIs / interchange | Analytical storage |

Use the format that matches the workload rather than selecting one format for every stage.

## Writing a DataFrame to Parquet

The basic API is:

```python
import pandas as pd

orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

`index=False` is commonly appropriate when the DataFrame Index is only an internal Pandas label.

The resulting file contains the tabular columns and associated schema information.

## Reading Parquet

Read a file with:

```python
orders = pd.read_parquet(
    "orders.parquet"
)
```

Then inspect:

```python
print(orders.shape)
print(orders.dtypes)
```

Parquet generally preserves type information better than text formats.

However, production code should still validate schema at system boundaries.

## Parquet Engines

Pandas can use different Parquet engines.

Common choices include:

```text
pyarrow
fastparquet
```

A typical environment uses PyArrow:

```bash
pip install pandas pyarrow
```

For reproducible deployments, declare the dependency explicitly in `pyproject.toml`.

Example:

```toml
[project]
dependencies = [
    "pandas",
    "pyarrow",
]
```

Pin versions according to the organization's dependency-management policy and test compatibility across the full pipeline.

## Explicit Engine Selection

When reproducibility matters:

```python
orders.to_parquet(
    "orders.parquet",
    engine="pyarrow",
    index=False,
)
```

and:

```python
orders = pd.read_parquet(
    "orders.parquet",
    engine="pyarrow",
)
```

Explicit engine selection is useful when multiple environments could otherwise resolve different implementations.

## Column Projection

One of Parquet's main advantages is selective column reading:

```python
orders = pd.read_parquet(
    "orders.parquet",
    columns=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

If a dataset contains:

```text
30 columns
```

but the report needs only:

```text
3 columns
```

the reader can avoid materializing unrelated columns.

This is especially valuable for large datasets in:

- AWS S3.
- Data lakes.
- Kubernetes batch workers.
- Celery workers.
- Scheduled ETL jobs.

## Column Projection vs CSV

With CSV:

```python
orders = pd.read_csv(
    "orders.csv",
    usecols=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

Pandas can still restrict the columns it parses, but CSV remains a text-oriented format that generally requires more parsing work.

Parquet is designed around columnar access, making selective analytical reads a central part of its design.

## Predicate Pushdown

Compatible Parquet readers can often avoid reading row groups that cannot satisfy a filter.

For example:

```text
Dataset
 ├── Row Group A → 2026-01-01
 ├── Row Group B → 2026-01-02
 ├── Row Group C → 2026-01-03
 └── Row Group D → 2026-01-04
```

A query for:

```text
2026-01-03
```

can potentially skip unrelated row groups when the storage metadata and reader support the required predicates.

With Pandas, filtering support and pushdown behavior depend on the reader, engine, file layout, and API being used.

The broader principle is:

```text
Store data so readers can avoid unnecessary I/O.
```

## Row Groups

Parquet organizes data into row groups.

Conceptually:

```text
Parquet File
├── Metadata
├── Row Group
│   ├── Column Chunk
│   ├── Column Chunk
│   └── Column Chunk
├── Row Group
│   ├── Column Chunk
│   ├── Column Chunk
│   └── Column Chunk
└── ...
```

A row group is a horizontal partition of the dataset while each column is stored separately inside that group.

Row-group organization affects:

- Read efficiency.
- Predicate skipping.
- Parallelism.
- File size.
- Write performance.

For advanced pipelines, row-group sizing becomes part of storage optimization.

## Column Chunks

Within a row group, each column has its own column chunk.

Conceptually:

```text
Row Group
├── order_id column chunk
├── customer_id column chunk
├── status column chunk
└── amount column chunk
```

This structure enables readers to access only relevant columns and apply column-specific encoding and compression.

## Compression

Parquet supports compression at the columnar storage level.

Common codecs include:

```text
Snappy
GZIP
Zstandard
Brotli
LZ4
```

The best choice depends on:

```text
CPU budget
Storage cost
Read frequency
Write frequency
Compression ratio
Latency requirements
```

For example:

```text
Snappy
→ often a balanced general-purpose choice

Zstandard
→ often stronger compression with configurable trade-offs

GZIP
→ strong compression but potentially higher CPU cost
```

Do not choose a codec purely from theoretical compression ratios. Benchmark representative workloads.

## Writing with Compression

Example:

```python
orders.to_parquet(
    "orders.parquet",
    engine="pyarrow",
    compression="zstd",
    index=False,
)
```

The choice should be standardized for a data platform rather than changed arbitrarily across jobs.

Consistency helps operational tooling and storage-cost analysis.

## Compression Trade-Offs

| Priority | Typical consideration |
|---|---|
| Lowest storage cost | Stronger compression |
| Lowest CPU overhead | Faster compression codec |
| High read throughput | Balanced codec and row-group layout |
| High write throughput | Faster compression |
| Large object-storage datasets | Compression + partitioning |

Compression should be evaluated alongside file size and end-to-end processing time.

## Data Types and Schema Preservation

Parquet stores typed columns.

For example:

```python
orders = pd.DataFrame(
    {
        "order_id": pd.Series(
            [1001, 1002],
            dtype="Int64",
        ),
        "status": pd.Series(
            ["completed", "pending"],
            dtype="string",
        ),
        "amount": pd.Series(
            [250.0, 175.5],
            dtype="Float64",
        ),
    }
)
```

Then:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

The typed representation is generally more reliable for round-tripping than a text format such as CSV.

Still, cross-engine interoperability should be tested because Pandas dtypes, Arrow types, SQL types, and other engines do not all map identically.

## Nullable Dtypes and Parquet

Nullable Pandas dtypes are particularly useful in typed pipelines:

```python
orders = pd.DataFrame(
    {
        "customer_id": pd.Series(
            [101, None, 103],
            dtype="Int64",
        ),
        "status": pd.Series(
            ["completed", None, "pending"],
            dtype="string",
        ),
    }
)
```

Writing to Parquet preserves missing-value semantics more naturally than CSV.

Validate the round-trip for important schemas:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)

loaded = pd.read_parquet(
    "orders.parquet"
)

print(loaded.dtypes)
```

## Schema Evolution

Parquet datasets evolve over time.

Possible changes include:

```text
New column
Removed column
Changed type
Changed nullability
Changed partition structure
```

A production data platform should define compatibility expectations.

For example:

```text
Additive nullable column
→ usually easier to support

Changing string → integer
→ potentially breaking

Changing identifier representation
→ potentially breaking

Changing row grain
→ major semantic change
```

Schema evolution should be managed intentionally rather than discovered through failed jobs.

## Single Parquet File vs Dataset

A single Parquet file is appropriate for a bounded dataset:

```text
orders.parquet
```

Large systems often use a logical dataset composed of many files:

```text
orders/
├── part-0001.parquet
├── part-0002.parquet
├── part-0003.parquet
└── ...
```

or partitioned paths:

```text
orders/
├── date=2026-09-08/
├── date=2026-09-09/
└── date=2026-09-10/
```

The dataset is logically one table even though physically distributed across multiple objects.

## Partitioning

Partitioning separates a dataset into storage paths or file groups based on selected columns.

Example:

```text
orders/
├── year=2026/month=09/day=08/
├── year=2026/month=09/day=09/
└── year=2026/month=09/day=10/
```

A query that only needs:

```text
2026-09-10
```

can potentially avoid unrelated partitions.

This is often called partition pruning.

## Choosing Partition Columns

Good partition columns are usually:

- Frequently filtered.
- Relatively low to moderate cardinality.
- Stable.
- Useful for operational retention.

Typical examples:

```text
event_date
ingestion_date
tenant_group
region
```

Avoid highly unique identifiers such as:

```text
order_id
customer_id
event_id
```

as partition columns because they can create excessive small partitions.

## Partitioning vs Clustering

Partitioning and physical ordering solve different problems.

```text
Partitioning
→ coarse dataset pruning

Column / row-group organization
→ finer read optimization
```

Do not create many partitions simply because the storage system allows them.

Too many small files can become a major performance problem.

## The Small Files Problem

A dataset such as:

```text
10,000,000 files × a few KB each
```

is operationally inefficient.

Problems include:

- Object-store metadata overhead.
- More file-open operations.
- More scheduling overhead.
- Poor scan performance.
- More complicated compaction.
- Higher request costs in some storage systems.

Prefer a reasonable number of appropriately sized files.

In S3-backed systems, file-count growth should be treated as an operational metric.

## Partitioning with Pandas

Pandas can write partitioned datasets with supported engines:

```python
orders.to_parquet(
    "orders_dataset",
    engine="pyarrow",
    partition_cols=[
        "order_date",
    ],
    index=False,
)
```

This can produce a directory structure based on the partition column.

The exact layout and behavior depend on the engine.

## Writing Partitioned Data

For example:

```python
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
)

orders.to_parquet(
    "orders_dataset",
    engine="pyarrow",
    partition_cols=[
        "order_date",
    ],
    index=False,
)
```

For production data lakes, partitioning should normally be based on a carefully chosen low-cardinality date or domain dimension.

Partitioning every row into its own directory is an anti-pattern.

## Reading a Partitioned Dataset

A dataset can often be read as a logical table:

```python
orders = pd.read_parquet(
    "orders_dataset"
)
```

For selective workloads, read only required columns and, where supported by the chosen reader and dataset API, apply filters at the storage layer.

For example, Arrow-oriented workflows can use dataset-level filtering before materialization.

The important principle is to avoid reading unnecessary partitions into memory.

## Parquet and S3

A common AWS architecture is:

```text
Application / API
       ↓
Pandas ETL
       ↓
Parquet
       ↓
Amazon S3
       ↓
Athena / Glue / Spark / Pandas / DuckDB
```

Parquet works particularly well as a durable analytical representation in object storage.

Use:

```text
PostgreSQL
→ transactional workloads

S3 + Parquet
→ analytical / historical workloads
```

This separation prevents analytical workloads from unnecessarily competing with transactional database workloads.

## Parquet and PostgreSQL

A production data pipeline may extract from PostgreSQL:

```python
orders = pd.read_sql_query(
    query,
    connection,
)
```

then write:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

The resulting architecture is:

```text
PostgreSQL
    ↓
Filtered query
    ↓
Pandas
    ↓
Validation
    ↓
Parquet
    ↓
Object Storage
```

Filter and project in PostgreSQL whenever practical before transferring data into Pandas.

## Parquet and REST APIs

API data can be normalized and persisted:

```python
orders = pd.json_normalize(
    payload["orders"]
)

orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

For large APIs:

```text
API page
    ↓
Pandas normalization
    ↓
Validation
    ↓
Parquet batch
    ↓
Next page
```

Avoid accumulating the entire API response in memory when the source can be processed incrementally.

## Parquet and Kafka

For event pipelines:

```text
Kafka
  ↓
Consumer
  ↓
Micro-batch
  ↓
Pandas
  ↓
Validation / Aggregation
  ↓
Parquet
  ↓
S3
```

Pandas can process bounded event batches, but Kafka remains responsible for:

```text
Partitions
Offsets
Consumer groups
Delivery semantics
Retention
Replay
```

Do not use Parquet as a substitute for a streaming transport.

## Incremental Parquet Processing

When a source is too large for one DataFrame:

```text
Batch 1 → Parquet
Batch 2 → Parquet
Batch 3 → Parquet
...
```

can be written as a dataset.

For example:

```text
orders/
├── ingestion_date=2026-09-08/
├── ingestion_date=2026-09-09/
└── ingestion_date=2026-09-10/
```

This supports incremental loading and retention strategies.

## Atomic Dataset Publication

Avoid exposing partially written datasets.

A safer pattern is:

```text
temporary location
       ↓
write all files
       ↓
validate row counts / schema
       ↓
publish dataset marker
       ↓
consumers read published version
```

For example:

```text
s3://bucket/orders/_staging/job-123/
        ↓
validation
        ↓
s3://bucket/orders/version=2026-09-10/
```

The exact publication mechanism depends on the storage architecture.

## Dataset Versioning

For critical analytical pipelines, version outputs:

```text
orders/
├── version=2026-09-08/
├── version=2026-09-09/
└── version=2026-09-10/
```

or use immutable batch identifiers.

This improves:

- Reproducibility.
- Rollback.
- Auditing.
- Disaster recovery.
- Debugging.

Do not overwrite historical data blindly when reproducibility matters.

## Reading and Writing Compression

Parquet compression is part of the file encoding.

Example:

```python
orders.to_parquet(
    "orders.parquet",
    compression="zstd",
    index=False,
)
```

The reader generally detects the compression from the file metadata.

Do not separately gzip a Parquet file unless there is a specific interoperability reason. Parquet already supports internal compression at the columnar level.

## Index Handling

The DataFrame Index is an internal Pandas construct.

For analytical datasets:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

is often preferred.

If the Index is semantically important and must be persisted:

```python
orders.to_parquet(
    "orders.parquet",
    index=True,
)
```

The choice should be part of the schema contract.

Avoid persisting incidental positional indexes.

## Datetime Handling

Datetime columns should be normalized before writing:

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
)
```

This is useful when datasets are consumed by different services and analytical engines.

A canonical UTC representation simplifies:

```text
Filtering
Partitioning
Windowing
Cross-region analysis
```

## String and Decimal Considerations

Parquet can preserve richer types than CSV, but cross-engine support still matters.

For financial values:

```text
Pandas representation
    ↓
Arrow / Parquet representation
    ↓
Athena / Spark / warehouse
```

should be tested end-to-end.

Do not assume that a Pandas floating-point column becomes an exact decimal merely because Parquet is typed.

For accounting-grade data, maintain explicit decimal or integer-minor-unit semantics across the pipeline.

## Parquet and Memory

Reading Parquet is not the same as loading the entire physical file into memory.

Column projection can reduce materialized data:

```python
orders = pd.read_parquet(
    "orders.parquet",
    columns=[
        "order_id",
        "amount",
    ],
)
```

However, selected columns may still be large.

For large datasets:

```text
Storage efficiency
≠
Infinite in-memory capacity
```

Pandas still needs a working set that fits within available memory.

Use partitioning, chunked or bounded processing, database pushdown, or distributed engines as needed.

## Parquet Performance

Performance depends on more than file format.

Important factors include:

```text
File count
Partition layout
Row-group size
Column selection
Predicate pushdown
Compression codec
Data types
Storage backend
Network latency
```

For S3-backed workloads, a dataset with well-sized files and useful partitioning can behave very differently from thousands of tiny files.

## Benchmarking

Benchmark representative workloads rather than relying on generic claims:

```python
from time import perf_counter

start = perf_counter()

orders = pd.read_parquet(
    "orders.parquet",
    columns=[
        "customer_id",
        "amount",
    ],
)

elapsed = perf_counter() - start

print(
    f"read_seconds={elapsed:.3f}"
)
```

Measure alongside:

```text
Rows read
Columns read
Bytes read
Memory usage
CPU time
End-to-end latency
```

For realistic results, benchmark against the actual storage backend and representative file sizes.

## Data Validation Before Writing

Do not use Parquet as a way to permanently store invalid data.

Validate before publishing:

```python
required = {
    "order_id",
    "customer_id",
    "amount",
}

missing = (
    required
    - set(orders.columns)
)

if missing:
    raise ValueError(
        f"Missing columns: {sorted(missing)}"
)

if orders["order_id"].isna().any():
    raise ValueError(
        "order_id contains missing values"
    )
```

Then persist:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)
```

The storage layer should contain data that satisfies the dataset's contract.

## Round-Trip Validation

A useful quality test is:

```python
orders.to_parquet(
    "orders.parquet",
    index=False,
)

loaded = pd.read_parquet(
    "orders.parquet"
)

pd.testing.assert_frame_equal(
    orders,
    loaded,
)
```

For cross-engine datasets, validate not only Pandas round-tripping but also consumption by the actual downstream engine.

## Schema Validation After Read

Reading a Parquet file should still be followed by validation when the data comes from an external or shared dataset:

```python
orders = pd.read_parquet(
    "orders.parquet"
)

expected = {
    "order_id",
    "customer_id",
    "amount",
}

if set(orders.columns) != expected:
    raise ValueError(
        "Unexpected Parquet schema"
    )
```

Do not assume that the presence of a Parquet extension guarantees schema correctness.

## Security Considerations

Parquet files can contain sensitive operational and customer data.

Relevant controls include:

- Encryption at rest.
- TLS for object-storage transfer.
- IAM-based access control.
- Bucket policies.
- Least-privilege service roles.
- Sensitive-column minimization.
- Audit logging.
- Retention policies.
- Dataset-level access controls.

For AWS:

```text
Pandas worker
      ↓
IAM role
      ↓
S3
```

is preferable to embedding static AWS credentials in application code.

Do not store credentials inside Parquet metadata or pipeline configuration.

## Sensitive Column Projection

Before writing:

```python
safe_orders = orders.loc[
    :,
    [
        "order_id",
        "customer_id",
        "amount",
        "status",
    ],
]
```

Do not write:

```text
password
authentication_token
private_notes
payment_secret
```

merely because they happen to exist in the source DataFrame.

Parquet's efficient storage makes it convenient to retain many columns, but convenience is not a security policy.

## Reliability and Disaster Recovery

For important datasets:

```text
Raw source
    ↓
Immutable ingestion artifact
    ↓
Validated Parquet dataset
    ↓
Replicated / durable object storage
    ↓
Downstream consumers
```

Use:

- Durable object storage.
- Versioning where appropriate.
- Backups or replication.
- Immutable historical partitions when required.
- Reproducible processing jobs.
- Dataset checksums or manifests where useful.

Do not treat a single local Parquet file on a worker disk as a durable backup.

## Data Quality and Observability

Track dataset-level metrics:

| Metric | Purpose |
|---|---|
| File count | Detect small-file growth |
| Total rows | Detect volume anomalies |
| Bytes written | Detect storage changes |
| Null rate | Detect quality regressions |
| Duplicate count | Detect upstream replay |
| Partition count | Detect layout changes |
| File size distribution | Detect fragmentation |
| Read latency | Detect performance changes |
| Write latency | Detect bottlenecks |
| Schema version | Track evolution |

For object-storage datasets, file-size distribution is particularly useful for identifying unhealthy partitioning.

## Idempotent Parquet Writes

A batch-processing job should not create duplicate datasets when retried.

Use a stable batch identity:

```text
source_file
source_partition
processing_date
job_id
checksum
```

Then write into a deterministic destination:

```text
orders/
    ingestion_date=2026-09-10/
        batch_id=abc123/
```

or use a controlled overwrite of the exact logical partition when that behavior is explicitly supported by the pipeline design.

## Common Mistakes

### Treating Parquet as a Database

Parquet is a storage format, not a transactional database.

**Better:** use PostgreSQL for transactional integrity and Parquet for analytical storage.

### Writing One File Per Record

This creates the small-files problem.

**Better:** batch records into reasonably sized files.

### Over-Partitioning

Partitioning by highly unique fields creates excessive directories and files.

**Better:** partition using commonly filtered, relatively low-cardinality dimensions such as dates.

### Reading Every Column

```python
pd.read_parquet(
    "orders.parquet"
)
```

may materialize much more data than needed.

**Better:** use `columns=` for projection.

### Assuming Parquet Means Zero Memory Pressure

A compressed Parquet file can still expand substantially when materialized.

**Better:** measure the working set and use partitioned or bounded processing.

### Choosing Compression Without Benchmarking

Compression changes CPU, storage, and I/O trade-offs.

**Better:** benchmark representative workloads.

### Ignoring Schema Evolution

Parquet does not automatically solve schema compatibility across a growing data platform.

**Better:** version and validate schemas explicitly.

### Treating Any Parquet File as Trustworthy

A file can have the wrong schema, wrong row grain, duplicated records, or invalid values.

**Better:** validate datasets at ingestion and publication boundaries.

### Persisting Incidental Indexes

Writing a default Pandas index can create unwanted columns when consumed elsewhere.

**Better:** use `index=False` unless the Index is part of the external contract.

### Writing Directly to Published Locations

Consumers can observe incomplete datasets if a job fails midway.

**Better:** write to a staging location and publish a validated version atomically or transactionally according to the storage architecture.

### Creating Tiny Files in Parallel Workers

Hundreds of workers can produce thousands of tiny Parquet files.

**Better:** design batching and compaction explicitly.

### Assuming Cross-Engine Dtype Equivalence

Pandas, Arrow, Spark, SQL engines, and query engines can represent types differently.

**Better:** test the complete producer-consumer path.

### Storing Sensitive Columns by Default

Parquet is efficient, but that does not justify retaining unnecessary confidential data.

**Better:** project only required fields before writing.

## Interview Traps

### Why Is Parquet Usually Better Than CSV for Analytics?

Because it uses columnar storage, typed representations, compression, and efficient selective reads.

### What Is Column Projection?

Reading only the required columns:

```python
pd.read_parquet(
    "orders.parquet",
    columns=[
        "customer_id",
        "amount",
    ],
)
```

This can reduce I/O and materialized memory.

### What Is Predicate Pushdown?

It is the ability of a compatible reader or query engine to apply filters close to the storage layer so unnecessary data can be skipped.

### What Is a Row Group?

A horizontal grouping of rows inside a Parquet file. Columns within the group are stored separately as column chunks.

### Why Does Partitioning Matter?

It can allow readers to skip entire dataset partitions that do not match a query.

### Why Is Over-Partitioning Bad?

It creates too many directories/files, increasing metadata and file-management overhead and often reducing query performance.

### What Is the Small-Files Problem?

Creating too many tiny Parquet objects increases file-open, metadata, scheduling, and object-storage overhead.

### Is Parquet a Database?

No. It is a storage format. It does not provide the transactional concurrency, constraints, and database execution semantics of PostgreSQL.

### Can Pandas Process a Dataset Larger Than Memory if It Is Stored in Parquet?

Storage size does not remove Pandas' in-memory processing limits. Use selective reads, partitioning, bounded processing, or another execution engine for larger workloads.

### Why Use `index=False`?

The DataFrame Index is often an internal Pandas label rather than part of the analytical dataset schema.

### Why Can Parquet Preserve Types Better Than CSV?

Parquet stores typed column metadata and values, while CSV primarily stores textual field representations.

### Why Might a Parquet Round Trip Still Change Types?

Different Pandas dtypes, Arrow types, and downstream engines may have different representations or compatibility rules.

### How Should a Parquet Dataset Be Published Reliably?

Write the complete batch to an isolated staging location, validate it, and then publish the finalized dataset or version so consumers do not observe partially written output.

## Production Architecture

A production Pandas-to-Parquet pipeline often looks like:

```mermaid
flowchart LR
    A[REST API / CSV / PostgreSQL / Kafka] --> B[Ingestion Worker]
    B --> C[Pandas Normalization]
    C --> D[Schema + Data Quality Validation]
    D --> E[Batch Transformation]
    E --> F[Parquet Dataset]
    F --> G[S3 / Object Storage]
    G --> H[Athena / Spark / DuckDB / Pandas]
```

The responsibilities are separated:

```text
Source systems
→ data acquisition

Pandas
→ normalization / transformation

Parquet
→ durable analytical representation

Object storage
→ scalable persistence

Query engines
→ large-scale analytical execution
```

This architecture is common for data-lake and batch-processing workflows.

## Recommended Dataset Layout

A practical S3 layout might be:

```text
s3://company-data/
└── orders/
    ├── ingestion_date=2026-09-08/
    │   ├── part-0001.parquet
    │   └── part-0002.parquet
    ├── ingestion_date=2026-09-09/
    │   ├── part-0001.parquet
    │   └── part-0002.parquet
    └── ingestion_date=2026-09-10/
        ├── part-0001.parquet
        └── part-0002.parquet
```

This layout supports:

- Incremental ingestion.
- Date-based pruning.
- Retention policies.
- Reprocessing by partition.
- Operational isolation.

Partition choice should follow actual query and lifecycle patterns rather than arbitrary hierarchy design.

## Production Checklist

```text
[ ] Is Parquet appropriate for the workload?
[ ] Is the logical row grain defined?
[ ] Is the schema explicitly defined?
[ ] Are critical dtypes validated before writing?
[ ] Are nullable fields represented appropriately?
[ ] Are only required columns persisted?
[ ] Is the Index intentionally included or excluded?
[ ] Is the Parquet engine pinned and tested?
[ ] Is the compression codec standardized?
[ ] Are file sizes appropriate for the workload?
[ ] Is the dataset over-partitioned?
[ ] Are tiny files being created by parallel jobs?
[ ] Are commonly filtered partition columns chosen deliberately?
[ ] Can readers project only required columns?
[ ] Can compatible readers use predicate pushdown?
[ ] Is schema evolution managed?
[ ] Is cross-engine compatibility tested?
[ ] Are writes idempotent?
[ ] Are datasets published atomically or through a controlled versioning process?
[ ] Are row counts and quality metrics monitored?
[ ] Is peak memory measured during reads?
[ ] Are sensitive columns excluded?
[ ] Are S3 / object-storage permissions least-privilege?
[ ] Are important datasets versioned or retained for recovery?
[ ] Is the original source retained where auditability requires it?
[ ] Are representative round-trip and integration tests automated?
```

## Key Takeaways

- Parquet is a typed columnar storage format designed for efficient analytical workloads, making it a strong fit for Pandas ETL pipelines and object-storage data lakes.
- Column projection, compression, row groups, partitioning, and predicate pushdown can substantially reduce I/O and processing cost, but benefits depend on file layout and the capabilities of the reader.
- Avoid over-partitioning and tiny files; storage layout is an operational design concern that directly affects query performance, object-storage overhead, and scalability.
- Treat Parquet as durable analytical storage rather than a transactional database, and validate schemas, row grain, dtypes, data quality, idempotency, and cross-engine compatibility before publishing datasets.
- Production Parquet pipelines should use controlled publication, versioning or immutable partitions where appropriate, least-privilege storage access, sensitive-column minimization, and monitoring for volume, schema, file-size, and performance drift.