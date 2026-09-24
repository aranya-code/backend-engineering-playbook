# 10- Import and Export Issues

## Overview

MongoDB import and export operations move data between MongoDB and external representations such as JSON, CSV, BSON dump archives, and database backup artifacts.

In production, import/export problems are rarely limited to a malformed command. Failures can involve:

- Incorrect file formats
- BSON type loss
- Schema mismatches
- Duplicate `_id` values
- Invalid documents
- Authentication and authorization
- TLS and network connectivity
- Collection naming
- Namespace mismatches
- Large-file performance
- Memory pressure
- Index overhead
- Partial imports
- Encoding problems
- Data validation
- Application compatibility
- Backup and recovery requirements

MongoDB Database Tools commonly used for these workflows include:

| Tool | Primary purpose |
|---|---|
| `mongoimport` | Import JSON or CSV into MongoDB |
| `mongoexport` | Export MongoDB data to JSON or CSV |
| `mongodump` | Create a logical BSON backup |
| `mongorestore` | Restore a `mongodump` backup |
| `mongosh` | Inspect and validate MongoDB state |

A critical distinction is:

```text
Data interchange
    ├── mongoimport
    └── mongoexport

Database backup / restore
    ├── mongodump
    └── mongorestore
```

`mongoexport` and `mongoimport` are primarily data interchange tools. They should not automatically be treated as equivalent to backup and restore.

## Import and Export Architecture

A typical production workflow looks like:

```mermaid
flowchart LR
    Source[Source File / Database] --> Validate[Validate Format and Schema]
    Validate --> Import[mongoimport]
    Import --> MongoDB[(MongoDB)]
    MongoDB --> Verify[Validate Imported Data]

    MongoDB --> Export[mongoexport]
    Export --> Artifact[JSON / CSV]

    MongoDB --> Dump[mongodump]
    Dump --> Backup[BSON Backup]
    Backup --> Restore[mongorestore]
    Restore --> MongoDB
```

The correct tool depends on the required fidelity.

## Choose the Correct Tool

| Requirement | Recommended tool |
|---|---|
| Import CSV | `mongoimport` |
| Import JSON | `mongoimport` |
| Export simple JSON/CSV | `mongoexport` |
| Preserve BSON types accurately | `mongodump` / `mongorestore` |
| Logical backup | `mongodump` |
| Logical restore | `mongorestore` |
| Inspect imported data | `mongosh` / Compass |
| Application-level migration | Purpose-built migration script |
| Large production backup | Managed/physical backup solution where appropriate |

For example, exporting a collection to CSV can be useful for analytics or interoperability:

```bash
mongoexport \
  --uri="mongodb://..." \
  --db=application \
  --collection=orders \
  --type=csv \
  --fields=_id,customer_id,status,total \
  --out=orders.csv
```

For backup fidelity, prefer:

```bash
mongodump \
  --uri="mongodb://..." \
  --db=application \
  --out=backup/
```

## JSON Import Issues

JSON import commonly fails because the input is not in the structure expected by `mongoimport`.

MongoDB tools can work with:

- JSON arrays
- JSON Lines / newline-delimited JSON
- Extended JSON

For large datasets, newline-delimited JSON is usually much easier to stream than one enormous JSON array.

Example:

```json
{"customer_id":"c001","status":"active"}
{"customer_id":"c002","status":"inactive"}
{"customer_id":"c003","status":"active"}
```

Import:

```bash
mongoimport \
  --uri="mongodb://localhost:27017" \
  --db=application \
  --collection=customers \
  --file=customers.json
```

When the input contains an outer JSON array, specify the appropriate array mode supported by the installed Database Tools version.

## Extended JSON

Standard JSON cannot represent every BSON type directly.

MongoDB Extended JSON can represent types such as:

- `ObjectId`
- `Date`
- Decimal128
- Binary
- Int64

Example:

```json
{
  "_id": {
    "$oid": "65f123456789abcdef012345"
  },
  "created_at": {
    "$date": "2026-09-20T10:30:00Z"
  }
}
```

This is important when data needs to retain MongoDB-specific types.

## JSON Type Loss

A common mistake is assuming JSON export/import preserves BSON types automatically.

For example:

```json
{
  "order_id": "12345"
}
```

is not equivalent to:

```json
{
  "order_id": 12345
}
```

Likewise:

```json
{
  "created_at": "2026-09-20T10:30:00Z"
}
```

may be interpreted as a string rather than a BSON date unless the import format explicitly represents the date type.

This can affect:

- Sorting
- Range queries
- Index usage
- Aggregations
- Application serialization
- Schema validation

## CSV Import Issues

CSV is inherently less expressive than BSON.

A CSV file represents tabular values:

```csv
customer_id,status,total
c001,active,125.50
c002,inactive,90.00
```

MongoDB must interpret these values when importing them.

Potential problems include:

- Numeric values imported as strings
- Dates imported as strings
- Empty fields becoming unexpected values
- Arrays not being represented naturally
- Nested documents being flattened incorrectly
- Duplicate column names
- Incorrect delimiters
- Quoting problems

For example:

```text
total = "125.50"
```

is materially different from:

```text
total = 125.50
```

Applications expecting numeric aggregation can fail or produce incorrect results.

## CSV Type Conversion

When importing CSV, explicitly configure field types when supported by the installed Database Tools version.

For example:

```bash
mongoimport \
  --uri="mongodb://localhost:27017" \
  --db=application \
  --collection=orders \
  --type=csv \
  --headerline \
  --file=orders.csv
```

Do not assume that CSV is an authoritative representation of the MongoDB schema.

For complex documents, prefer JSON/Extended JSON or BSON backups.

## CSV and Nested Data

Consider this MongoDB document:

```json
{
  "customer": {
    "name": "Aranya",
    "address": {
      "city": "Kolkata"
    }
  },
  "items": [
    {
      "sku": "SKU-001",
      "quantity": 2
    }
  ]
}
```

Representing this accurately in CSV is difficult.

You might produce:

```csv
customer_name,customer_city,items
Aranya,Kolkata,"[{""sku"":""SKU-001"",""quantity"":2}]"
```

This creates additional parsing requirements.

For operational MongoDB migrations, CSV should generally be treated as an interchange format rather than a full-fidelity database representation.

## BSON Backup vs JSON Export

BSON-based dump/restore preserves MongoDB-specific data much more accurately.

Conceptually:

```text
MongoDB
   ↓
mongodump
   ↓
BSON + metadata
   ↓
mongorestore
   ↓
MongoDB
```

Whereas:

```text
MongoDB
   ↓
mongoexport
   ↓
JSON / CSV
   ↓
mongoimport
   ↓
MongoDB
```

The second workflow can involve type transformations and is therefore not equivalent to a backup/restore cycle.

## File Encoding Problems

Import failures can originate from encoding.

Typical sources include:

- UTF-8
- UTF-8 with BOM
- Windows-1252
- Legacy regional encodings

Prefer UTF-8 for interchange files.

Inspect problematic files before importing:

```text
Encoding
Delimiter
Line endings
Quotation
Escaping
Header
Field count
```

A file that opens correctly in Excel or a text editor may still fail under `mongoimport`.

## Delimiter Problems

CSV files may use:

```text
,
;
\t
```

The producer and importer must agree on the delimiter.

For example:

```csv
id;status;amount
1;active;100
```

is not a comma-separated file.

Incorrect delimiter interpretation can result in one large field instead of multiple fields.

## Header Problems

For CSV import, the header determines field names when using the header-line option.

Example:

```csv
customer_id,status,total
c001,active,100
```

The resulting document should resemble:

```json
{
  "customer_id": "c001",
  "status": "active",
  "total": "100"
}
```

Notice that type interpretation still matters.

Validate:

```text
Column names
Column count
Column ordering
Duplicate columns
Unexpected whitespace
Reserved application assumptions
```

## Duplicate `_id` Errors

A frequent import failure is duplicate `_id`.

Example:

```text
E11000 duplicate key error
```

This usually means the target collection already contains a document with the same unique key.

Investigate:

```javascript
db.orders.findOne({
  _id: ObjectId("65f123456789abcdef012345")
})
```

Do not blindly delete the existing document.

Determine whether the import is:

- Initial population
- Replay
- Migration
- Synchronization
- Recovery
- Test-data loading

The correct resolution depends on the workflow.

## Importing into a New Collection

For a clean migration, importing into a newly created collection can reduce ambiguity.

Example:

```bash
mongoimport \
  --uri="mongodb://localhost:27017" \
  --db=application \
  --collection=orders_import \
  --file=orders.json
```

Validate first:

```javascript
db.orders_import.countDocuments()
```

Then perform controlled cutover or migration logic.

This is often safer than modifying the production collection directly.

## Dropping Existing Data

Some import workflows support replacing existing collection data through drop-related options.

Use destructive options only after validating:

- Database name
- Collection name
- Environment
- Backup availability
- Input file
- Restore point

A dangerous production failure is:

```text
Wrong database
      ↓
Import with destructive option
      ↓
Existing collection removed
```

Always verify the target before destructive operations.

## Importing into a Different Namespace

`mongorestore` supports namespace transformation and selective restoration.

This is useful for:

```text
production.orders
        ↓
staging.orders
```

or:

```text
production.orders
        ↓
recovery.orders
```

This allows recovery testing without overwriting the production collection.

## Namespace Troubleshooting

When restoring a backup, verify:

```text
Source database
Source collection
Target database
Target collection
Namespace filters
Namespace rewrite rules
```

An apparently successful restore can still be operationally incorrect if the data was restored into the wrong database.

## Authentication Problems

Typical errors include:

```text
Authentication failed
Unauthorized
Command not permitted
```

Verify:

- Username
- Password
- Authentication database
- Roles
- Target database
- TLS configuration
- Connection URI

For example:

```text
mongodb://user:password@host:27017/application?authSource=admin
```

`authSource` is particularly important when the user is defined in a database different from the target database.

## Least Privilege for Import and Export

Do not use unrestricted administrative credentials for routine data movement.

Create an operational identity with only the permissions required.

Example conceptual separation:

```text
Application User
    ↓
Application CRUD

Migration User
    ↓
Required migration permissions

Backup User
    ↓
Backup-specific permissions
```

This reduces blast radius.

## TLS Problems

Production MongoDB deployments commonly require TLS.

A CLI command may need TLS-specific options or a connection URI containing the appropriate configuration.

When troubleshooting:

```text
Certificate validity
↓
CA trust
↓
Hostname verification
↓
TLS protocol compatibility
↓
MongoDB server configuration
↓
Client configuration
```

Do not disable TLS verification as a permanent fix.

## Network Connectivity

Before investigating MongoDB-specific import problems, establish basic connectivity.

For example:

```bash
mongosh "mongodb://..."
```

If `mongosh` cannot connect, `mongoimport` is unlikely to work.

Investigate:

- DNS
- Firewall
- Security groups
- Network policies
- VPN/private connectivity
- Kubernetes services
- TLS
- Authentication

## MongoDB Atlas Import Issues

For Atlas deployments, verify:

```text
Client IP / network access
Database user
Authentication
TLS
Connection string
Database permissions
```

A common mistake is testing from one machine while running `mongoimport` from another machine with a different public IP.

Network access must permit the actual import source.

## Docker Import Issues

When MongoDB runs in Docker, distinguish:

```text
Host machine
localhost:27017
```

from:

```text
Docker network
mongo:27017
```

From the host:

```text
mongodb://localhost:27017
```

may be correct.

From another container:

```text
mongodb://mongo:27017
```

may be correct.

Using the wrong address is a common source of connection failures.

## Kubernetes Import Issues

For Kubernetes, determine where the import command runs.

If the command runs inside a pod:

```text
mongodb-service:27017
```

may be appropriate.

If it runs outside the cluster:

```text
External endpoint
```

may be required.

Also verify:

- Network policies
- DNS
- TLS
- Service configuration
- Authentication
- Database permissions

## Large Import Performance

Large imports can generate substantial load.

Potential bottlenecks include:

- CPU
- Disk I/O
- Network
- Index maintenance
- Document validation
- Replication
- Journal activity
- Connection limits

A useful model is:

```text
Input File
   ↓
Parsing
   ↓
Network
   ↓
MongoDB Write
   ↓
Validation
   ↓
Index Maintenance
   ↓
Replication
   ↓
Storage
```

The slowest stage determines overall throughput.

## Batch Size

Bulk import performance depends on batching and workload characteristics.

Very small batches can increase:

- Network round trips
- Command overhead
- CPU overhead

Very large batches can increase:

- Memory usage
- Failure recovery cost
- Operation latency

Tune import behavior based on measured workload rather than choosing arbitrary maximum values.

## Index Impact During Imports

Indexes must be maintained as documents are inserted.

Suppose a collection has:

```text
10 million documents
+
8 indexes
```

An import may spend substantial resources maintaining those indexes.

For a controlled bulk-load workflow, consider whether indexes can be created after the data load.

However, this is workload-dependent and must account for:

- Production traffic
- Unique constraints
- Available disk
- Build duration
- Failure recovery
- Required query availability

Do not drop production indexes simply to make an import faster.

## Unique Index Problems

Suppose:

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

The import contains:

```text
alice@example.com
alice@example.com
```

The second document cannot satisfy the unique constraint.

The correct response is usually to identify and clean the source data rather than disable the uniqueness requirement.

## Schema Validation During Import

A collection can have a validator.

For example:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["order_id", "status"],
      properties: {
        order_id: {
          bsonType: "string"
        },
        status: {
          enum: ["pending", "confirmed", "cancelled"]
        }
      }
    }
  }
})
```

Importing incompatible documents can then fail validation.

Before importing into a validated collection:

```text
Inspect validator
        ↓
Validate source schema
        ↓
Test representative records
        ↓
Import
        ↓
Validate result
```

## Partial Import Problems

An import can fail after successfully inserting some documents.

Therefore:

```text
Import command failed
≠
Zero documents imported
```

Always determine the final state.

For example:

```javascript
db.orders.countDocuments()
```

Then inspect:

```javascript
db.orders.find().limit(5)
```

For production migrations, design the process so that partial completion is detectable and recoverable.

## Idempotent Imports

A production migration should ideally be restartable.

Consider an import keyed by:

```text
external_id
```

A migration can use deterministic identifiers and upsert semantics where appropriate.

Conceptually:

```text
Source Record
    ↓
Stable Business Key
    ↓
Find Existing
    ↓
Insert or Update
```

This is often safer than blindly inserting duplicate documents.

## Import Validation Workflow

Use:

```text
Source File
    ↓
Format Validation
    ↓
Schema Validation
    ↓
Sample Import
    ↓
Count Validation
    ↓
Field-Type Validation
    ↓
Constraint Validation
    ↓
Full Import
    ↓
Post-Import Verification
```

Sample validation should include:

- Document count
- Required fields
- BSON types
- Unique identifiers
- Dates
- Numeric fields
- Nested documents
- Arrays
- Null handling

## Data Reconciliation

For migration workloads, compare source and target.

Useful metrics include:

```text
Source record count
Target document count
Inserted count
Updated count
Rejected count
Duplicate count
Validation failures
```

For example:

```text
Source:
1,000,000 records

Target:
999,982 documents

Rejected:
18
```

Do not declare the migration successful until the discrepancy is understood.

## Export Issues

Export failures can occur because of:

- Incorrect credentials
- Insufficient permissions
- Invalid query
- Unsupported data representation
- Network interruption
- Disk-full conditions
- Incorrect database/collection
- Large result size
- File permission problems

Test connectivity first:

```bash
mongosh "mongodb://..."
```

Then test a small export.

## Exporting a Subset

`mongoexport` can export selected documents using a query.

Conceptually:

```bash
mongoexport \
  --uri="mongodb://..." \
  --db=application \
  --collection=orders \
  --query='{"status":"completed"}' \
  --out=completed-orders.json
```

For production workflows, make sure the query itself is efficient.

An export query can become a large production read workload.

## Export Query Performance

An export is still a database query.

For example:

```text
mongoexport
    ↓
Query
    ↓
Query Planner
    ↓
Index / Collection Scan
    ↓
Documents
    ↓
Serialization
    ↓
File
```

A poorly indexed export can scan millions of documents and compete with application traffic.

Use `explain()` on the underlying query when necessary.

## Exporting Large Collections

For very large collections:

- Export during controlled windows.
- Monitor disk usage.
- Monitor MongoDB read load.
- Avoid unnecessary fields.
- Use selective queries where appropriate.
- Ensure the destination filesystem has sufficient capacity.
- Prefer appropriate backup tooling for backup requirements.

Do not assume exporting a large collection is operationally free.

## File System Issues

Import/export problems may occur before MongoDB is involved.

Check:

```text
File exists
File readable
Destination writable
Disk capacity
File ownership
Path correctness
```

On Linux:

```bash
ls -lh orders.json
df -h
```

On Windows PowerShell:

```powershell
Get-Item .\orders.json
Get-PSDrive
```

## ObjectId Issues

MongoDB `_id` values are commonly `ObjectId` values.

Extended JSON:

```json
{
  "_id": {
    "$oid": "65f123456789abcdef012345"
  }
}
```

Plain JSON:

```json
{
  "_id": "65f123456789abcdef012345"
}
```

can result in a string rather than an `ObjectId`.

This matters because:

```javascript
db.orders.find({
  _id: ObjectId("65f123456789abcdef012345")
})
```

is different from:

```javascript
db.orders.find({
  _id: "65f123456789abcdef012345"
})
```

An import that changes `_id` types can break application behavior.

## Date Import Issues

Dates have the same problem.

Preferred BSON date representation:

```json
{
  "created_at": {
    "$date": "2026-09-20T10:30:00Z"
  }
}
```

Potentially problematic representation:

```json
{
  "created_at": "2026-09-20T10:30:00Z"
}
```

The latter is a string.

That affects:

- Sorting
- Range filters
- TTL indexes
- Aggregation
- Date expressions
- Application models

## Numeric Type Issues

MongoDB supports multiple numeric BSON types.

An import can unintentionally change:

```text
int
long
double
decimal
```

This matters for:

- Financial values
- Aggregations
- Comparisons
- Precision

For monetary data, avoid using floating-point representations when exact decimal semantics are required.

## Validation After Import

A successful exit code is not sufficient.

Validate:

### Count

```javascript
db.orders.countDocuments()
```

### Sample Documents

```javascript
db.orders.find().limit(10)
```

### Required Fields

```javascript
db.orders.countDocuments({
  order_id: { $exists: false }
})
```

### Type

```javascript
db.orders.countDocuments({
  created_at: { $not: { $type: "date" } }
})
```

### Indexes

```javascript
db.orders.getIndexes()
```

### Query Behavior

```javascript
db.orders
  .find({ status: "completed" })
  .explain("executionStats")
```

## Import into Staging Before Production

For high-risk migrations:

```mermaid
flowchart LR
    A[Source Data] --> B[Staging Import]
    B --> C[Validation]
    C --> D[Application Tests]
    D --> E[Performance Tests]
    E --> F[Production Migration]
    F --> G[Post-Migration Validation]
```

Staging should validate:

- Data shape
- Application compatibility
- Index requirements
- Query performance
- Constraints
- Serialization
- Business rules

## Production Migration Pattern

A safer migration can follow:

```text
Prepare
  ↓
Backup
  ↓
Validate Source
  ↓
Dry Run
  ↓
Import Staging
  ↓
Validate
  ↓
Schedule Production Window
  ↓
Import / Migrate
  ↓
Reconcile
  ↓
Application Verification
  ↓
Monitor
```

Do not make production import a one-command operation without verification.

## Python-Based Import Validation

For complex migrations, Python can validate records before MongoDB insertion.

Example:

```python
from datetime import datetime
from decimal import Decimal

REQUIRED_FIELDS = {"order_id", "status", "total"}


def validate_record(record: dict) -> None:
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")

    if record["status"] not in {"pending", "confirmed", "cancelled"}:
        raise ValueError(f"Invalid status: {record['status']}")

    if not isinstance(record["total"], Decimal):
        raise TypeError("total must use Decimal semantics")

    if not isinstance(record["created_at"], datetime):
        raise TypeError("created_at must be a datetime")
```

This is useful when import rules are more complex than database-level validation.

## FastAPI Migration Workflow

For a FastAPI application, avoid embedding large import jobs directly inside HTTP request handlers.

Prefer:

```text
POST /admin/import
       ↓
Create Import Job
       ↓
Celery / Worker
       ↓
Read Source
       ↓
Validate
       ↓
Bulk Write
       ↓
Record Progress
       ↓
Reconcile
```

The HTTP API should initiate and monitor the job rather than hold a request open for hours.

## Celery-Based Import

A background worker can process large imports:

```python
from celery import shared_task
from pymongo import MongoClient


@shared_task
def import_orders(records: list[dict]) -> int:
    client = MongoClient(
        "mongodb://mongo1:27017,mongo2:27017/?replicaSet=rs0"
    )

    collection = client["application"]["orders"]

    if not records:
        return 0

    result = collection.insert_many(records, ordered=False)
    return len(result.inserted_ids)
```

For production workloads, large datasets should generally be streamed or chunked rather than loading the entire source file into memory.

## Streaming Large Files

Avoid:

```python
records = list(load_everything())
```

for very large datasets.

Prefer:

```text
File
 ↓
Chunk
 ↓
Validate
 ↓
Bulk Write
 ↓
Record Progress
 ↓
Next Chunk
```

This limits memory usage and improves recovery behavior.

## Ordered vs Unordered Writes

Bulk operations can be ordered or unordered.

Conceptually:

```text
Ordered
A → B → C → D
       ↓
      Error
       ↓
   Stop/alter progression
```

versus:

```text
Unordered
A ─┐
B ─┼→ Process independently where possible
C ─┤
D ─┘
```

Unordered writes can improve throughput when records are independent, but error handling and reconciliation must be designed accordingly.

## Duplicate Handling Strategy

Choose explicitly between:

| Strategy | Appropriate when |
|---|---|
| Fail on duplicate | Duplicates indicate invalid source data |
| Ignore duplicate | Duplicate is expected and harmless |
| Upsert | Source represents desired final state |
| Replace | Source is authoritative |
| Merge | Multiple sources contribute fields |
| Quarantine | Invalid records require manual review |

Do not let the database's duplicate-key error become the migration strategy.

## Import Error Quarantine

For large migrations, isolate invalid records:

```text
Input
 ├── Valid ──────→ MongoDB
 │
 └── Invalid ────→ Error / Quarantine File
```

A quarantine record should include:

```text
Source identifier
Validation error
Original payload
Timestamp
Migration version
```

This makes failed records reproducible and auditable.

## Import Observability

Track:

- Records processed
- Records inserted
- Records updated
- Records rejected
- Duplicate records
- Validation failures
- Throughput
- Batch duration
- Database latency
- Retry count
- Current offset/progress
- Final reconciliation result

Example:

```text
Migration: orders-2026-09-20
Processed: 8,500,000
Inserted: 8,492,100
Updated: 7,850
Rejected: 50
Duplicates: 0
Status: FAILED
```

A migration should not report success solely because the process exited without an exception.

## Resumable Imports

For large imports, maintain progress.

For example:

```text
Source offset
    ↓
Batch identifier
    ↓
Last successful batch
    ↓
Restart from checkpoint
```

A robust migration should be restartable without duplicating successful work.

This requires deterministic identifiers or idempotent writes.

## Transactions and Imports

Do not assume an entire multi-million-document import should be wrapped in one MongoDB transaction.

Large transactions can create:

- Resource pressure
- Long-running locks or conflicts
- Increased replication work
- Larger failure domains
- Difficult recovery

Prefer appropriately sized batches.

Transactions are useful when a small set of related changes must be atomic, not as a generic wrapper around an entire migration.

## Import and Replica Sets

Large imports generate replication traffic:

```text
Import
  ↓
Primary Writes
  ↓
Oplog
  ├── Secondary A
  └── Secondary B
```

Monitor:

- Replication lag
- Oplog growth
- Oplog window
- Secondary health
- Disk utilization

A large import can temporarily reduce replica-set recovery margin.

## Import and Sharded Clusters

In a sharded deployment, bulk imports should account for shard-key distribution.

Poor shard-key distribution can create:

```text
Import
   ↓
Most writes → One shard
   ↓
Hot shard
   ↓
Uneven throughput
```

Before importing into a sharded collection, understand:

- Shard key
- Cardinality
- Frequency
- Distribution
- Targeting behavior
- Existing chunks/ranges

## Security Considerations

Import/export files can contain sensitive production data.

Protect:

- JSON files
- CSV files
- BSON dumps
- Temporary files
- Logs
- Error/quarantine files

Do not store production exports in:

- Public Git repositories
- Unencrypted shared folders
- Developer laptops without appropriate controls
- Public object storage

For cloud storage, use appropriate:

- Encryption
- IAM policies
- Bucket policies
- Access logging
- Lifecycle rules
- Retention controls

## Sensitive Data in Logs

Avoid logging entire failed documents.

Bad:

```python
logger.error("Failed document: %s", record)
```

if the document contains:

- Passwords
- Tokens
- Personal information
- Payment information
- Internal secrets

Prefer:

```python
logger.error(
    "Import validation failed",
    extra={"record_id": record.get("order_id")},
)
```

Log only what is required for diagnosis.

## Cost Considerations

Large imports can increase:

- Compute usage
- Storage consumption
- Network transfer
- Backup size
- Replication workload
- Temporary storage
- Cloud I/O costs

For Atlas or cloud-hosted MongoDB, consider whether the import is best performed:

```text
From local machine
```

or:

```text
From compute close to MongoDB
```

Moving large datasets across geographic regions can be expensive and slow.

## Import/Export Troubleshooting Methodology

Use the following workflow:

```text
Symptom
↓
Possible causes
↓
Isolation strategy
↓
Diagnostic commands
↓
Root cause
↓
Corrective action
↓
Prevention
```

### Connection Failure

**Symptom**

```text
Server selection timeout
Authentication failed
TLS error
```

**Possible causes**

- Wrong URI
- DNS failure
- Network restriction
- TLS mismatch
- Invalid credentials
- Incorrect `authSource`

**Isolation strategy**

Test:

```bash
mongosh "mongodb://..."
```

**Diagnostic commands**

```bash
mongosh "mongodb://..."
```

Then verify:

```javascript
db.hello()
```

**Root cause**

Identify whether the failure is:

```text
Network
Authentication
TLS
MongoDB topology
```

**Corrective action**

Fix the specific layer rather than changing unrelated MongoDB settings.

**Prevention**

Store validated connection configuration and test connectivity in deployment pipelines.

### Invalid JSON

**Symptom**

```text
JSON parse error
```

**Possible causes**

- Invalid JSON syntax
- Incorrect array/JSONL mode
- Encoding
- Unescaped quotes

**Isolation strategy**

Validate the source file independently.

**Diagnostic approach**

Test a small sample before importing the full dataset.

**Corrective action**

Normalize the source format.

**Prevention**

Validate files automatically before migration.

### Duplicate Key

**Symptom**

```text
E11000 duplicate key error
```

**Possible causes**

- Existing target document
- Duplicate source records
- Unique index
- Re-running a non-idempotent import

**Isolation strategy**

Identify the conflicting key and target document.

**Corrective action**

Choose explicitly between deduplication, upsert, merge, replacement, or rejection.

**Prevention**

Design imports to be idempotent.

### Incorrect BSON Types

**Symptom**

Queries return unexpected results.

**Possible causes**

- Dates imported as strings
- Numeric fields imported as strings
- ObjectIds imported as strings

**Isolation strategy**

Inspect:

```javascript
db.collection.findOne()
```

and query types explicitly.

**Corrective action**

Transform the source and re-import or run a controlled data migration.

**Prevention**

Validate BSON types before production import.

### Partial Import

**Symptom**

Import command fails but some records exist.

**Possible causes**

- Duplicate keys
- Validation failures
- Network interruption
- Disk failure
- Process termination

**Isolation strategy**

Compare source and target counts and inspect logs.

**Corrective action**

Determine the successful range and resume using an idempotent strategy.

**Prevention**

Use checkpoints and deterministic identifiers.

## Common Beginner Mistakes

### Treating CSV as a Full MongoDB Backup

CSV does not preserve MongoDB's complete document model or BSON type system.

### Importing Directly into Production

Always validate the data and migration process first.

### Ignoring Partial Success

A failed command can still have modified the database.

### Using Strings for Dates

This breaks date comparisons and date-specific operations.

### Ignoring `_id` Types

A string identifier and `ObjectId` are different BSON values.

### Loading Entire Files into Memory

Large imports should be streamed or chunked.

### Using Application HTTP Requests for Long Imports

Use background workers for long-running operations.

## Production Pitfalls

### Importing During Peak Traffic

Bulk writes can compete with application traffic.

### Ignoring Replication Lag

A large import can overwhelm secondaries.

### Dropping Indexes Without a Recovery Plan

The import may become faster while application queries become unusable.

### Using Administrative Credentials

Migration tools should use dedicated least-privileged credentials.

### Storing Export Files Permanently

Exports may contain sensitive production data and should have defined retention.

### Assuming Exit Code Means Data Correctness

Technical command success does not guarantee business-level correctness.

## Recommended Production Import Checklist

### Before Import

- [ ] Confirm source file format.
- [ ] Confirm encoding.
- [ ] Validate schema.
- [ ] Validate BSON types.
- [ ] Check duplicate identifiers.
- [ ] Verify target database.
- [ ] Verify target collection.
- [ ] Review indexes.
- [ ] Review schema validation.
- [ ] Confirm authentication and permissions.
- [ ] Confirm network connectivity.
- [ ] Confirm sufficient storage.
- [ ] Confirm backup/recovery capability.
- [ ] Test in staging.

### During Import

- [ ] Monitor throughput.
- [ ] Monitor CPU.
- [ ] Monitor memory.
- [ ] Monitor disk.
- [ ] Monitor replication lag.
- [ ] Monitor database latency.
- [ ] Record rejected records.
- [ ] Record progress.
- [ ] Avoid uncontrolled retries.

### After Import

- [ ] Reconcile counts.
- [ ] Validate BSON types.
- [ ] Validate required fields.
- [ ] Validate unique constraints.
- [ ] Validate indexes.
- [ ] Run representative queries.
- [ ] Run application tests.
- [ ] Check replication health.
- [ ] Check monitoring.
- [ ] Archive or securely delete temporary files according to retention policy.
- [ ] Record migration results.

## Command Reference

| Task | Example |
|---|---|
| Test connection | `mongosh "mongodb://..."` |
| Import JSON | `mongoimport --uri="..." --db=app --collection=orders --file=orders.json` |
| Import CSV | `mongoimport --uri="..." --db=app --collection=orders --type=csv --headerline --file=orders.csv` |
| Export JSON | `mongoexport --uri="..." --db=app --collection=orders --out=orders.json` |
| Export CSV | `mongoexport --uri="..." --db=app --collection=orders --type=csv --fields=_id,status,total --out=orders.csv` |
| Logical backup | `mongodump --uri="..." --db=app --out=backup/` |
| Logical restore | `mongorestore --uri="..." backup/` |
| Inspect indexes | `db.orders.getIndexes()` |
| Count documents | `db.orders.countDocuments()` |
| Inspect sample | `db.orders.find().limit(10)` |
| Explain query | `db.orders.find({status:"completed"}).explain("executionStats")` |

Always verify the exact options supported by the installed MongoDB Database Tools version before using a command in production.

## Import vs Restore Decision Matrix

| Scenario | Import/Export | Dump/Restore |
|---|---:|---:|
| CSV interoperability | Yes | No |
| Simple JSON interchange | Yes | No |
| Preserve BSON types | Limited by format | Yes |
| Full logical backup | No | Yes |
| Selective data migration | Yes | Yes |
| Application data migration | Often | Sometimes |
| Disaster recovery | No | Yes |
| Human-readable artifact | Yes | No |
| Large production backup | No | Usually more appropriate |
| Cross-system data exchange | Yes | Usually no |

## Interview Traps

### "Can `mongoexport` replace `mongodump`?"

Not generally.

`mongoexport` is primarily an interchange/export utility, while `mongodump` is designed for logical backup.

### "If `mongoimport` fails, no data was inserted."

Not necessarily.

Imports can partially succeed before an error occurs.

### "CSV preserves MongoDB types."

No.

CSV is a limited tabular representation and requires careful type handling.

### "A JSON date string is automatically a MongoDB Date."

Not necessarily.

A plain JSON string can remain a BSON string. Extended JSON provides explicit BSON type representation.

### "Disabling indexes always makes imports faster."

It may improve bulk-load throughput, but dropping indexes can create unacceptable query impact and may violate uniqueness requirements.

### "The fastest way to migrate is to load everything into Python first."

For large datasets, this can exhaust application memory. Streaming and bounded batching are safer.

### "A successful import means the migration succeeded."

No.

Migration correctness requires reconciliation, type validation, constraint validation, and application-level verification.

## Key Takeaways

- **Choose `mongoimport`/`mongoexport` for controlled data interchange and `mongodump`/`mongorestore` when MongoDB-aware logical backup and restoration fidelity is required.**
- **Treat BSON types as a first-class migration concern; strings representing dates, numbers, or `ObjectId` values can produce valid documents that behave incorrectly in production.**
- **Production imports should be validated, bounded, observable, resumable, and preferably idempotent; a failed command can still leave partially imported data.**
- **Large imports are database workloads: monitor indexes, storage, CPU, network, replication lag, oplog window, and application latency while they run.**
- **Never consider an import successful based only on the command exit status; reconcile counts, validate types and constraints, test representative queries, and verify application behavior.**