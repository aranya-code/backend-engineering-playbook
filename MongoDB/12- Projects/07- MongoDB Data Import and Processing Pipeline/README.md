# README

## Overview

This directory contains processed data produced by the MongoDB Data Import and Processing Pipeline.

The pipeline supports importing source data from CSV or JSON, transforming and validating documents, and loading the resulting records into MongoDB. Files generated here are considered pipeline artifacts rather than source-controlled application code.

Typical flow:

```text
Raw Input
   ↓
CSV / JSON Processor
   ↓
Transformation
   ↓
Validation
   ↓
MongoDB Bulk Write
   ↓
Processed Data / Artifacts
```

The `processed` directory is intentionally kept separate from source input data so that generated artifacts do not overwrite or become confused with original datasets.

## Directory Purpose

| Directory | Purpose |
|---|---|
| `data/processed/` | Stores generated or processed pipeline output |
| `.env.example` | Documents supported environment configuration |
| `.gitignore` | Prevents secrets, generated artifacts, caches, and local data from being committed |
| `requirements.txt` | Defines Python dependencies for the project |

## Processed Data Guidelines

Processed files should be treated as derived artifacts.

Use this directory for:

- Transformed CSV or JSON output
- Exported pipeline results
- Intermediate datasets required for local processing
- Locally generated import/export artifacts
- Debugging artifacts when explicitly required

Do not use this directory for:

- Application source code
- Environment secrets
- Production database backups
- Permanent credentials
- Large datasets that should be stored in object storage
- Original source datasets that must remain immutable

## Environment Configuration

The project uses environment variables for MongoDB connectivity and pipeline configuration.

A typical local configuration is:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=mongodb_data_pipeline

MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=30000

MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=5

MONGODB_RETRY_READS=true
MONGODB_RETRY_WRITES=true

IMPORT_BATCH_SIZE=1000
PROCESS_BATCH_SIZE=1000

LOG_LEVEL=INFO
```

Do not commit an actual `.env` file. The `.env.example` file contains configuration names and safe development defaults without production credentials.

For production deployments, inject secrets through the deployment platform or secret-management system rather than storing them in the repository.

## Pipeline Data Contract

The pipeline expects source documents to be converted into dictionary-like MongoDB documents.

For JSON input, the current processor expects a top-level array:

```json
[
  {
    "_id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  },
  {
    "_id": 2,
    "name": "Bob",
    "email": "bob@example.com"
  }
]
```

For CSV input, the first row is treated as the header:

```csv
_id,name,email
1,Alice,alice@example.com
2,Bob,bob@example.com
```

CSV values remain strings during parsing. This avoids unsafe automatic conversion of identifiers, dates, and business-specific values.

## Processing Behavior

The pipeline follows an ETL-style flow:

```mermaid
flowchart LR
    A[CSV / JSON Input] --> B[Processor]
    B --> C[Transform]
    C --> D[Validate]
    D -->|Valid| E[Batch Loader]
    D -->|Invalid| F[Log / Reject]
    E --> G[(MongoDB)]
    G --> H[Processed Data / Results]
```

### Extraction

Source documents are read through iterators where possible so that downstream processing can operate incrementally.

CSV processing is streamed row-by-row.

JSON processing currently parses the complete JSON array before exposing its objects through an iterator. For very large JSON datasets, a streaming JSON parser should be considered.

### Transformation

The transformation stage currently:

- Trims surrounding whitespace from string values.
- Normalizes an `email` field to lowercase when present.
- Adds a UTC `processed_at` timestamp.
- Does not mutate the original source document.

Example:

```text
Input:
{
    "_id": 1,
    "name": " Alice ",
    "email": " ALICE@EXAMPLE.COM "
}

Output:
{
    "_id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "processed_at": "<UTC timestamp>"
}
```

### Validation

The validation stage currently checks:

- The document is not empty.
- `_id` is present.
- `email`, when supplied, is a non-empty string.
- `processed_at`, when supplied, behaves like a datetime value.

Invalid documents are not silently inserted into MongoDB.

### Loading

Valid documents are loaded using MongoDB bulk writes.

Batching provides two important controls:

1. Limits application memory consumption.
2. Prevents extremely large MongoDB write requests.

Unordered bulk writes are used by default because input ordering is not a stated business requirement.

## Batch Processing

The project uses bounded batches rather than loading an entire dataset into memory.

Relevant configuration:

| Variable | Purpose | Default |
|---|---|---:|
| `PROCESS_BATCH_SIZE` | Number of validated documents handled by a processing batch | `1000` |
| `IMPORT_BATCH_SIZE` | Maximum number of documents in one MongoDB bulk write | `1000` |

These values should be tuned using measurements rather than arbitrary increases.

Larger batches can improve throughput by reducing network round trips, but they also increase:

- Memory usage
- Individual request size
- Failure scope
- Retry cost
- MongoDB write pressure

For production workloads, benchmark representative data before changing batch sizes.

## MongoDB Connection Management

The application uses a shared `MongoClient`.

```python
from database.connection import get_database, ping_database

ping_database()

database = get_database()
collection = database["records"]
```

A process-wide client is preferred over creating a new client for every operation because `MongoClient` maintains its own connection pool.

Relevant settings include:

- Server selection timeout
- Connection timeout
- Socket timeout
- Maximum pool size
- Minimum pool size
- Retryable reads
- Retryable writes

Do not create one `MongoClient` per document or per request.

## Reliability Considerations

The pipeline is designed around bounded processing and bulk writes, but production reliability requires additional controls.

Recommended practices include:

- Make imports idempotent when possible.
- Use stable business identifiers or deterministic `_id` values when duplicate imports are possible.
- Track rejected records separately from successfully processed records.
- Record import metrics such as read, transformed, rejected, inserted, and failed counts.
- Retry transient MongoDB failures according to an explicit policy.
- Avoid retrying non-transient validation or schema errors.
- Preserve source files when an import must be audited or replayed.
- Validate backups independently from normal application testing.

For high-value production imports, an import run should have a unique identifier and auditable status.

Example:

```text
import_id
source_file
started_at
completed_at
records_read
records_valid
records_rejected
records_inserted
status
error_count
```

## Data Integrity

MongoDB provides atomicity for operations on individual documents.

Bulk writes provide batching, but they do not automatically make an entire multi-batch import one atomic transaction.

For example:

```text
Batch 1 → committed
Batch 2 → committed
Batch 3 → failure
Batch 4 → not processed
```

The pipeline should therefore be designed so that a partially completed import can be identified and safely resumed or rolled back.

For imports requiring cross-document atomicity, MongoDB transactions may be appropriate, but transaction scope should remain small. Large ETL jobs should generally avoid wrapping the entire import in one transaction.

## Security

Never commit:

- MongoDB usernames
- MongoDB passwords
- Atlas credentials
- Connection strings containing credentials
- TLS private keys
- Production configuration
- API keys

Use:

- Environment variables for local development.
- Docker/Kubernetes secrets where applicable.
- AWS Secrets Manager or another dedicated secret-management system in production.
- TLS for connections to remote MongoDB deployments.
- Least-privilege MongoDB users.
- Network restrictions in addition to authentication.

A connection string such as:

```text
mongodb+srv://username:password@cluster.example.mongodb.net/database
```

must never be committed with real credentials.

## Local Development

Install project dependencies:

```bash
python -m pip install -r requirements.txt
```

Set up local configuration from `.env.example`.

For a local MongoDB server:

```text
mongodb://localhost:27017
```

Verify connectivity through the project application or `mongosh`:

```bash
mongosh "mongodb://localhost:27017"
```

The application performs an explicit MongoDB `ping` before starting the import operation.

## Running the Pipeline

The CLI entry point is:

```bash
python -m processors.main <input> --format <csv|json> --collection <collection>
```

CSV example:

```bash
python -m processors.main data/input/customers.csv \
  --format csv \
  --collection customers
```

JSON example:

```bash
python -m processors.main data/input/customers.json \
  --format json \
  --collection customers
```

The command exits with a non-zero status when the import fails.

This makes the application suitable for CI/CD jobs, scheduled workers, Docker containers, and orchestration systems.

## Testing

Run the test suite with:

```bash
pytest
```

The tests cover:

- CSV processing
- JSON processing
- Input validation
- Transformation
- MongoDB extraction behavior
- Batch processing
- Bulk loading
- Pipeline composition
- Error handling

MongoDB interactions are mocked in unit tests where database connectivity is not required.

Integration tests should be added separately when validating:

- Real MongoDB queries
- Index behavior
- Aggregation pipelines
- Transactions
- Replica-set behavior
- MongoDB-specific validation rules

Do not rely exclusively on mocks for MongoDB-heavy applications because mocks cannot reproduce query-planner behavior, indexes, transaction semantics, or server-side constraints.

## Production Considerations

For production deployment, treat the pipeline as a data-processing workload rather than a simple file-upload script.

Important concerns include:

| Area | Recommendation |
|---|---|
| Idempotency | Use deterministic identifiers and safe upsert strategies where appropriate |
| Memory | Stream input and use bounded batches |
| Database | Reuse connection pools |
| Indexes | Create only indexes required by actual access patterns |
| Monitoring | Track throughput, failures, latency, and rejected records |
| Security | Use TLS, least privilege, and managed secrets |
| Recovery | Preserve source data and define replay procedures |
| Scalability | Partition large workloads when appropriate |
| Reliability | Handle transient MongoDB failures explicitly |
| Testing | Use both unit and integration tests |
| Operations | Record import metadata and execution status |

## Common Pitfalls

### Loading the Entire Dataset

A common mistake is:

```python
documents = list(load_all_documents())
```

For large datasets, this can cause excessive memory consumption.

Prefer iterator-based processing and bounded batches.

### Creating MongoClient Repeatedly

Avoid:

```python
for document in documents:
    client = MongoClient(uri)
    ...
```

Create and reuse a shared client.

### Using Excessively Large Batches

Increasing batch size indefinitely does not guarantee higher throughput. Network payload size, server load, memory pressure, and retry cost can increase.

Benchmark with realistic datasets.

### Treating Bulk Writes as Fully Atomic

A bulk operation is not equivalent to making an entire multi-batch import transactional.

Design imports to tolerate partial completion.

### Silently Dropping Invalid Records

Invalid documents should produce observable metrics and logs. Silent data loss makes production reconciliation difficult.

### Committing Generated Data

Processed datasets can become large and may contain sensitive information. Keep generated artifacts out of Git unless there is a specific reason to version them.

## Troubleshooting Workflow

For a failed import, use the following sequence:

```text
Symptom
↓
Identify whether failure is input, application, or MongoDB related
↓
Check application logs and exit status
↓
Verify MongoDB connectivity
↓
Validate source format and schema
↓
Inspect rejected records
↓
Check MongoDB server errors and write results
↓
Check indexes, constraints, and permissions
↓
Identify root cause
↓
Correct the failure
↓
Replay safely using an idempotent strategy
↓
Record the incident and prevention measure
```

Useful connectivity check:

```bash
mongosh "$MONGODB_URI" --eval 'db.runCommand({ ping: 1 })'
```

Useful collection inspection:

```javascript
db.customers.countDocuments({})
db.customers.getIndexes()
```

For slow queries, inspect the execution plan:

```javascript
db.customers
  .find({ email: "alice@example.com" })
  .explain("executionStats")
```

Focus on:

- `nReturned`
- `totalKeysExamined`
- `totalDocsExamined`
- Execution time
- `COLLSCAN`
- `IXSCAN`
- Unexpected `SORT` stages

## Architecture Direction

The project intentionally separates responsibilities:

```text
processors/
    Input format handling
        ↓
pipeline/
    Extract
        ↓
    Transform
        ↓
    Validate
        ↓
    Load
        ↓
database/
    MongoDB connection management
```

This separation allows the input format, transformation rules, validation rules, and persistence implementation to evolve independently.

It also makes the core pipeline easier to test without requiring a running MongoDB instance for every unit test.

## Key Takeaways

- Keep processed data separate from source code, secrets, and immutable source datasets.
- Use streaming interfaces and bounded batches to control memory usage and MongoDB write pressure.
- Reuse a process-wide `MongoClient` and configure connection timeouts, pooling, and retry behavior deliberately.
- Design imports for validation, observability, idempotency, and safe recovery from partial failures.
- Use unit tests for pipeline logic and integration tests for MongoDB-specific behavior such as indexes, aggregation, and transactions.