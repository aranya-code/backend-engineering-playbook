# 07- JSON and CSV Import Export

## Overview

MongoDB stores documents as BSON, while JSON and CSV are commonly used for data interchange. Import and export workflows therefore require careful handling of document structure, BSON types, encoding, validation, and operational safety.

MongoDB provides several tools and workflows for moving data:

| Tool / Workflow | Primary use |
|---|---|
| `mongoimport` | Import JSON or CSV into MongoDB |
| `mongoexport` | Export MongoDB collections to JSON or CSV |
| `mongodump` | Logical BSON backup |
| `mongorestore` | Restore `mongodump` output |
| MongoDB Compass | Interactive JSON/CSV import and export |
| PyMongo | Application-controlled data movement |
| Atlas backup | Managed backup and recovery |

The most important distinction is:

```text
JSON / CSV import-export
        ≠
MongoDB backup and recovery
```

JSON and CSV are interchange formats. They are useful for migrations, data exchange, development fixtures, reporting, and controlled data loading. They are not a complete replacement for MongoDB backup systems.

## JSON, Extended JSON, BSON, and CSV

MongoDB internally stores BSON.

```text
Application
    ↓
BSON-compatible Python values
    ↓
MongoDB
```

JSON is a text interchange format and cannot represent every BSON type directly.

For example, an ObjectId is not native JSON:

```json
{
  "_id": {
    "$oid": "507f1f77bcf86cd799439011"
  }
}
```

Likewise, a MongoDB date can be represented using Extended JSON:

```json
{
  "created_at": {
    "$date": "2026-09-21T10:00:00Z"
  }
}
```

This is why MongoDB provides Extended JSON representations for BSON types.

### Format Comparison

| Format | Nested documents | Arrays | BSON type preservation | Human readable | Typical use |
|---|---:|---:|---:|---:|---|
| JSON | Yes | Yes | Limited | Yes | Data interchange |
| Extended JSON | Yes | Yes | Strong | Yes | MongoDB-aware interchange |
| CSV | No | Limited | Weak | Yes | Flat/tabular data |
| BSON | Yes | Yes | Native | No | MongoDB backup/data movement |

For MongoDB-to-MongoDB migration where BSON semantics matter, BSON-oriented tooling is usually preferable to CSV.

## JSON Import

JSON import is useful when the source data is already document-oriented.

Example:

```json
{"customer_id":"cust-1001","status":"pending","total":149.99}
{"customer_id":"cust-1002","status":"confirmed","total":250.00}
```

This newline-delimited format is commonly used with MongoDB import tooling.

A basic import:

```bash
mongoimport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --file=orders.json
```

For production workflows, prefer supplying credentials through secure mechanisms rather than embedding passwords directly in shell history or scripts.

## JSON Array Import

A JSON file may also contain an array:

```json
[
  {
    "customer_id": "cust-1001",
    "status": "pending"
  },
  {
    "customer_id": "cust-1002",
    "status": "confirmed"
  }
]
```

When using `mongoimport`, specify the JSON array format:

```bash
mongoimport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --file=orders.json \
  --jsonArray
```

Without the appropriate option, an array-formatted input can be interpreted incorrectly.

## Newline-Delimited JSON

For large datasets, newline-delimited JSON is often more operationally convenient:

```json
{"customer_id":"cust-1001","status":"pending"}
{"customer_id":"cust-1002","status":"confirmed"}
{"customer_id":"cust-1003","status":"cancelled"}
```

Each line represents one MongoDB document.

Advantages include:

- Streaming-friendly processing
- Easier line-level troubleshooting
- Simple generation from Python
- Convenient command-line processing
- No need to load one giant JSON array into memory

## Extended JSON

Extended JSON represents BSON-specific types in JSON-compatible syntax.

Example:

```json
{
  "_id": {
    "$oid": "507f1f77bcf86cd799439011"
  },
  "created_at": {
    "$date": "2026-09-21T10:00:00Z"
  },
  "balance": {
    "$numberDecimal": "149.99"
  }
}
```

This matters because converting:

```json
{
  "created_at": "2026-09-21T10:00:00Z"
}
```

does not necessarily produce the same BSON type as:

```json
{
  "created_at": {
    "$date": "2026-09-21T10:00:00Z"
  }
}
```

The first may become a string, while the second represents a BSON date.

## JSON Type Preservation

Common BSON types that require attention include:

| BSON type | Extended JSON representation |
|---|---|
| ObjectId | `$oid` |
| Date | `$date` |
| Decimal128 | `$numberDecimal` |
| Int32 | `$numberInt` |
| Int64 | `$numberLong` |
| Binary | `$binary` |
| Timestamp | `$timestamp` |
| Regular expression | `$regularExpression` |

For migrations where type fidelity matters, verify the generated representation before importing.

## JSON Import Workflow

A production-oriented import should follow:

```mermaid
flowchart TD
    Source[JSON Source]
    Validate[Validate Format]
    Sample[Inspect Sample]
    Import[mongoimport]
    Verify[Verify Documents]
    Indexes[Verify Indexes]
    App[Validate Application]

    Source --> Validate
    Validate --> Sample
    Sample --> Import
    Import --> Verify
    Verify --> Indexes
    Indexes --> App
```

Do not consider an import successful merely because `mongoimport` exits successfully.

Validate:

- Document count
- BSON types
- Required fields
- Duplicate identifiers
- Indexes
- Application behavior
- Referential assumptions

## JSON Export

A basic export:

```bash
mongoexport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --out=orders.json
```

JSON export is useful for:

- Data interchange
- Debugging
- Small migrations
- Development fixtures
- Ad-hoc analysis

It should not be treated as a complete MongoDB backup.

## Exporting Selected Fields

Use field selection when only specific fields are required.

Conceptually:

```text
MongoDB
   ↓
Selected fields
   ↓
JSON
```

This is useful when preparing data for another system and also reduces unnecessary data exposure.

For example, an export used for analytics might need:

```text
customer_id
status
created_at
total
```

but not:

```text
password_hash
access_token
internal_secret
```

## Exporting Filtered Data

`mongoexport` supports query-based filtering.

Example:

```bash
mongoexport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --query='{"status":"confirmed"}' \
  --out=confirmed-orders.json
```

For more complex filters, carefully validate shell quoting and JSON syntax.

A safer operational workflow is:

```text
Write filter
    ↓
Test filter in Compass / mongosh
    ↓
Count expected records
    ↓
Export
    ↓
Validate exported records
```

## CSV Import

CSV is appropriate when the source is tabular.

Example:

```csv
customer_id,status,total
cust-1001,pending,149.99
cust-1002,confirmed,250.00
cust-1003,cancelled,75.50
```

A basic import:

```bash
mongoimport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --type=csv \
  --headerline \
  --file=orders.csv
```

The `--headerline` option tells the importer to use the first row as field names.

## CSV Type Handling

CSV values are textual by nature, so type conversion requires particular attention.

For example:

```csv
customer_id,total,active
cust-1001,149.99,true
```

The intended MongoDB document may be:

```json
{
  "customer_id": "cust-1001",
  "total": 149.99,
  "active": true
}
```

but blindly importing textual values can produce incorrect types.

Always verify:

```text
String
Number
Boolean
Date
Null
```

after import.

Type correctness matters because MongoDB query behavior and index usage depend on BSON types.

## CSV Field Names

When CSV headers contain unusual characters or whitespace, normalize them before importing.

Prefer:

```csv
customer_id,created_at,total
```

over:

```csv
Customer ID,Created At,Order Total
```

Stable field naming simplifies:

- Query construction
- Application serialization
- Index definitions
- Schema validation
- Migration scripts

## CSV Arrays and Nested Documents

CSV is fundamentally flat.

A document such as:

```json
{
  "customer_id": "cust-1001",
  "items": [
    {
      "product_id": "prod-101",
      "quantity": 2
    },
    {
      "product_id": "prod-102",
      "quantity": 1
    }
  ]
}
```

does not map naturally to CSV.

You might flatten it:

```csv
customer_id,product_id,quantity
cust-1001,prod-101,2
cust-1001,prod-102,1
```

but this changes the document structure.

Reconstructing MongoDB documents then becomes an ETL problem.

For complex MongoDB data, JSON or BSON-aware tooling is usually a better fit.

## CSV Export

A basic export:

```bash
mongoexport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --type=csv \
  --fields=customer_id,status,total \
  --out=orders.csv
```

CSV is useful for:

- Excel
- BI tools
- Data analysis
- Flat reporting
- External systems requiring tabular data

It is not appropriate when preserving complex BSON structure is important.

## JSON vs CSV

| Requirement | JSON | CSV |
|---|---:|---:|
| Nested documents | Excellent | Poor |
| Arrays | Excellent | Poor |
| BSON types | Good with Extended JSON | Limited |
| Spreadsheet workflows | Moderate | Excellent |
| API interchange | Excellent | Moderate |
| MongoDB migration | Good | Usually poor for complex data |
| Human inspection | Good | Excellent |
| Large flat datasets | Good | Good |
| Schema fidelity | Stronger | Weak |

Choose the format based on the target system, not simply on which format is easier to open.

## `mongoimport`

`mongoimport` is part of the MongoDB Database Tools and is designed to load JSON, CSV, and related supported formats into MongoDB.

General structure:

```bash
mongoimport \
  --uri="<connection-string>" \
  --db="<database>" \
  --collection="<collection>" \
  --file="<file>"
```

Common options include:

| Option | Purpose |
|---|---|
| `--uri` | MongoDB connection URI |
| `--db` | Target database |
| `--collection` | Target collection |
| `--file` | Input file |
| `--type` | Input type such as JSON or CSV |
| `--headerline` | Use CSV first row as field names |
| `--jsonArray` | Treat JSON input as one array |
| `--mode` | Control duplicate handling |
| `--upsertFields` | Fields used for upsert matching |
| `--maintainInsertionOrder` | Preserve input ordering where supported |
| `--numInsertionWorkers` | Control parallel import workers |

Always verify the installed Database Tools version because available options and behavior can change between releases.

## Import Modes

Import behavior matters when documents may already exist.

Conceptually, import strategies include:

```text
Insert
Replace
Upsert
```

For example:

```text
Source document
       ↓
Match existing identifier?
      / \
    No   Yes
    ↓     ↓
 Insert  Replace/Upsert
```

Choose the mode intentionally.

Do not use upsert semantics merely to make an import "idempotent" without understanding the matching fields.

## Upsert Matching

Suppose:

```json
{
  "customer_id": "cust-1001",
  "status": "confirmed"
}
```

If the import matches on:

```text
customer_id
```

then the import may update the existing customer.

If the matching field is not unique, multiple logical records can conflict.

The match key should therefore normally have a corresponding uniqueness guarantee when business semantics require it.

## Duplicate Key Handling

A common failure is:

```text
DuplicateKey
```

Possible causes:

- Existing `_id`
- Existing unique field
- Re-imported dataset
- Incorrect upsert configuration
- Duplicate source records

Isolation:

```text
Duplicate error
    ↓
Identify conflicting key
    ↓
Check target collection
    ↓
Check source data
    ↓
Choose insert / replace / upsert strategy
```

Do not solve duplicate-key errors by dropping useful uniqueness constraints.

## `mongoexport`

General structure:

```bash
mongoexport \
  --uri="<connection-string>" \
  --collection="<collection>" \
  --out="<output-file>"
```

Common options include:

| Option | Purpose |
|---|---|
| `--uri` | MongoDB connection URI |
| `--db` | Database |
| `--collection` | Collection |
| `--out` | Output file |
| `--type` | JSON or CSV |
| `--fields` | Selected fields for CSV |
| `--query` | Filter documents |
| `--jsonFormat` | JSON representation format |
| `--queryFile` | Query supplied through a file |

Use `--help` against the installed version when building automation:

```bash
mongoexport --help
```

## `mongoimport` vs `mongoexport`

| Operation | Tool |
|---|---|
| JSON → MongoDB | `mongoimport` |
| CSV → MongoDB | `mongoimport` |
| MongoDB → JSON | `mongoexport` |
| MongoDB → CSV | `mongoexport` |
| MongoDB → BSON backup | `mongodump` |
| BSON backup → MongoDB | `mongorestore` |

This distinction is fundamental.

## Import/Export vs Backup

```mermaid
flowchart LR
    Mongo[(MongoDB)]

    Mongo --> Export[mongoexport]
    Export --> JSON[JSON / CSV]

    Dump[mongodump] --> BSON[BSON Backup]
    BSON --> Restore[mongorestore]
    Restore --> Mongo
```

JSON/CSV workflows are generally intended for interchange.

`mongodump`/`mongorestore` are intended for logical backup and restoration.

For production disaster recovery, managed backup and point-in-time recovery capabilities may be more appropriate depending on the MongoDB deployment.

## Compass Import

Compass provides an interactive import workflow for JSON and CSV.

Typical workflow:

```text
Connect to MongoDB
       ↓
Select database
       ↓
Select collection
       ↓
Add Data
       ↓
Import JSON / CSV
       ↓
Configure format
       ↓
Review types
       ↓
Import
       ↓
Verify
```

Compass is particularly useful for:

- Small datasets
- Development data
- Manual inspection
- One-off controlled imports

For repeatable production migrations, command-line tools or application-controlled migration scripts are generally easier to automate and audit.

## Compass Export

Compass can export collection data into supported JSON and CSV representations.

Use it for:

- Small data extracts
- Debugging
- Analysis
- Development fixtures
- Manual data interchange

Do not use Compass export as your disaster-recovery strategy.

## `mongodump` and `mongorestore`

A logical backup:

```bash
mongodump \
  --uri="mongodb://localhost:27017/orders" \
  --out=backup/
```

Restore:

```bash
mongorestore \
  --uri="mongodb://localhost:27017/orders" \
  backup/
```

These tools preserve MongoDB-oriented BSON data more faithfully than JSON/CSV export.

For production backup systems, consider:

- Encryption
- Retention
- Backup frequency
- Point-in-time recovery
- Restore testing
- Off-site storage
- Access controls
- RPO
- RTO

## Backup Validation

A backup is not proven usable merely because the backup command completed.

Use:

```text
Backup
  ↓
Restore into isolated environment
  ↓
Validate collections
  ↓
Validate document counts
  ↓
Validate indexes
  ↓
Validate representative documents
  ↓
Run application smoke tests
```

A restore test is part of backup engineering.

## Large Dataset Imports

Large imports require planning.

Consider:

- Input file size
- Network throughput
- Disk throughput
- Available memory
- Number of insertion workers
- Index overhead
- Write concern
- Replica-set replication
- Secondary lag
- Application traffic
- Import duration

A large import can create substantial write pressure.

## Indexes During Large Imports

Indexes make writes more expensive because index entries must be maintained.

For bulk loading into an empty collection, a common strategy may be:

```text
Create collection
    ↓
Load data
    ↓
Validate data
    ↓
Create required indexes
    ↓
Validate query plans
```

However, this strategy is workload-dependent.

If the collection is serving live traffic or the import is incremental, dropping indexes may be unsafe.

Do not apply a generic "drop all indexes before import" rule to production systems.

## Import Performance

For a large import:

```text
Input
  ↓
Parsing
  ↓
Batch insertion
  ↓
Index maintenance
  ↓
Journal / replication
  ↓
Storage
```

Potential bottlenecks include:

- CPU
- Disk I/O
- Network
- Index writes
- Replication
- Storage latency

Measure before optimizing.

## Streaming Large Exports

Do not load massive datasets into application memory just to create JSON or CSV.

Avoid:

```python
documents = list(collection.find({}))
```

for an arbitrarily large collection.

Prefer cursor-based processing:

```python
import csv

cursor = collection.find(
    {},
    {
        "_id": 1,
        "customer_id": 1,
        "status": 1,
    },
    batch_size=1000,
)

with open("orders.csv", "w", newline="", encoding="utf-8") as output:
    writer = csv.DictWriter(
        output,
        fieldnames=["_id", "customer_id", "status"],
    )
    writer.writeheader()

    for document in cursor:
        writer.writerow(document)
```

The cursor allows incremental processing rather than materializing the entire collection in memory.

## Python JSON Export

For application-controlled exports, use a streaming approach.

```python
import json

cursor = collection.find(
    {"status": "confirmed"},
    {"_id": 1, "customer_id": 1, "total": 1},
    batch_size=1000,
)

with open("confirmed-orders.jsonl", "w", encoding="utf-8") as output:
    for document in cursor:
        output.write(
            json.dumps(
                document,
                default=str,
                separators=(",", ":"),
            )
            + "\n"
        )
```

`default=str` is convenient for development but is not necessarily appropriate for MongoDB-aware interchange because it can convert BSON types into ambiguous strings.

For type-preserving exports, use BSON-aware serialization.

## Python Extended JSON

PyMongo provides BSON JSON utilities for MongoDB-compatible JSON representations.

Example:

```python
from bson import json_util
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
collection = client["orders"]["orders"]

with open("orders.json", "w", encoding="utf-8") as output:
    for document in collection.find({}, batch_size=1000):
        output.write(
            json_util.dumps(document, separators=(",", ":"))
            + "\n"
        )
```

This preserves MongoDB-specific types using Extended JSON representations.

## Python Extended JSON Import

A corresponding import can deserialize Extended JSON:

```python
from bson import json_util
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
collection = client["orders"]["orders"]

with open("orders.json", encoding="utf-8") as source:
    documents = (
        json_util.loads(line)
        for line in source
        if line.strip()
    )

    collection.insert_many(
        documents,
        ordered=False,
    )
```

For very large imports, avoid accumulating all documents into one list.

Use controlled batching.

## Batch Import Pattern

```python
from bson import json_util
from pymongo import MongoClient

BATCH_SIZE = 1000

client = MongoClient("mongodb://localhost:27017")
collection = client["orders"]["orders"]

batch = []

with open("orders.jsonl", encoding="utf-8") as source:
    for line in source:
        if not line.strip():
            continue

        batch.append(json_util.loads(line))

        if len(batch) >= BATCH_SIZE:
            collection.insert_many(batch, ordered=False)
            batch.clear()

if batch:
    collection.insert_many(batch, ordered=False)
```

This limits memory usage while retaining efficient batch writes.

## CSV Processing with Python

For complex CSV transformations, Python can be used as an ETL layer.

```mermaid
flowchart LR
    CSV[CSV File]
    Parse[Python CSV Parser]
    Validate[Validation]
    Transform[Transformation]
    Batch[Batch Documents]
    Mongo[(MongoDB)]

    CSV --> Parse
    Parse --> Validate
    Validate --> Transform
    Transform --> Batch
    Batch --> Mongo
```

This approach is useful when the input schema differs significantly from the MongoDB document model.

## CSV ETL Example

```python
import csv

from pymongo import MongoClient

BATCH_SIZE = 1000

client = MongoClient("mongodb://localhost:27017")
collection = client["orders"]["orders"]

batch = []

with open("orders.csv", newline="", encoding="utf-8") as source:
    reader = csv.DictReader(source)

    for row in reader:
        document = {
            "customer_id": row["customer_id"],
            "status": row["status"],
            "total": float(row["total"]),
        }

        batch.append(document)

        if len(batch) >= BATCH_SIZE:
            collection.insert_many(batch, ordered=False)
            batch.clear()

if batch:
    collection.insert_many(batch, ordered=False)
```

For financial or high-precision monetary values, avoid blindly using binary floating-point `float`. Use an appropriate Decimal128 strategy when exact decimal semantics are required.

## Validation Before Import

A robust import should validate:

```text
File format
 ↓
Encoding
 ↓
Required fields
 ↓
BSON types
 ↓
Allowed values
 ↓
Duplicate identifiers
 ↓
Business rules
 ↓
Document size
 ↓
Target indexes
```

Application-level validation alone is insufficient when data may be imported through multiple channels.

## Staging Imports

Never use production as the first environment for a complicated migration.

Prefer:

```text
Raw file
  ↓
Development
  ↓
Staging
  ↓
Production
```

At each stage validate:

- Record count
- Error count
- Type correctness
- Schema correctness
- Duplicate behavior
- Index behavior
- Application compatibility

## Idempotent Imports

A production migration should ideally be restartable.

For example:

```text
Input record
    ↓
Stable business key
    ↓
Existing document?
   / \
 No   Yes
 ↓     ↓
Insert Update
```

A unique index can enforce the business key:

```javascript
db.orders.createIndex(
  { external_order_id: 1 },
  { unique: true }
)
```

This makes duplicate handling explicit.

## Import Checkpointing

For very large imports, checkpointing can reduce restart cost.

Conceptually:

```text
File
 ↓
Batch 1 → success
Batch 2 → success
Batch 3 → failure
             ↓
        Resume strategy
```

Possible checkpoint keys include:

- Source line number
- Stable source identifier
- ObjectId
- External record identifier

The checkpoint mechanism should be designed so that retrying a completed batch does not corrupt the target dataset.

## Error Handling

An import should capture:

- Failed record
- Failure reason
- Source location
- Target identifier
- Batch number
- Timestamp

Example operational output:

```text
Imported: 9,950
Failed:      50
Skipped:      0
```

Do not report an import as successful merely because most records were inserted.

## Data Reconciliation

After an import, compare source and destination.

Useful checks include:

```text
Source record count
Destination document count

Source unique IDs
Destination unique IDs

Source status distribution
Destination status distribution

Source numeric totals
Destination numeric totals
```

For financial or transactional data, reconciliation should use business-level invariants rather than only document counts.

## Schema Validation After Import

Check representative documents:

```javascript
db.orders.findOne({
  customer_id: "cust-1001"
})
```

Then inspect:

- Field presence
- BSON types
- Nested structure
- Dates
- Numeric precision
- Identifier types

Also test important application queries.

## Document Size

MongoDB has a maximum BSON document size of 16 MiB.

Imports that transform flat data into nested documents must account for this limit.

A migration can fail even when the source file itself is valid if the generated MongoDB document becomes too large.

Avoid creating unbounded arrays during ETL.

## Security During Export

Exports frequently create copies of production data.

Every copy expands the security surface:

```text
MongoDB
  ↓
Export
  ↓
Local disk
  ↓
Cloud storage
  ↓
Analyst workstation
```

Protect exported data using:

- Access control
- Encryption at rest
- Encryption in transit
- Short retention periods
- Data minimization
- Audit logging
- Approved storage locations

Delete temporary exports when no longer required.

## Credentials

Avoid:

```bash
mongoexport --uri="mongodb://admin:SuperSecretPassword@..."
```

because credentials can leak through:

- Shell history
- Process listings
- CI logs
- Documentation
- Screenshots

Prefer an approved secret-management strategy and consult the Database Tools version documentation for supported authentication mechanisms.

## TLS

Production exports/imports should use TLS when connecting over networks.

Conceptually:

```text
mongoimport
    ↓
TLS
    ↓
MongoDB
```

Do not disable TLS verification merely to make an import work.

Investigate:

- CA configuration
- Hostname validation
- Certificate expiration
- Server certificate chain
- Client certificate requirements

## Network Security

MongoDB should not be made publicly reachable merely because an engineer needs to run:

```bash
mongoimport
```

Preferred architecture:

```text
Developer / CI Runner
        ↓
VPN / Private Network / Bastion
        ↓
MongoDB Private Endpoint
```

Apply the same network security principles to imports and exports as to application traffic.

## Production Migration Strategy

A larger migration should be treated as a production change.

```mermaid
flowchart TD
    Plan[Migration Plan]
    Sample[Sample Data]
    Dev[Development Test]
    Stage[Staging Test]
    Backup[Backup / Recovery Point]
    DryRun[Dry Run]
    Prod[Production Import]
    Verify[Reconciliation]
    Monitor[Monitor Application]

    Plan --> Sample
    Sample --> Dev
    Dev --> Stage
    Stage --> Backup
    Backup --> DryRun
    DryRun --> Prod
    Prod --> Verify
    Verify --> Monitor
```

Define before execution:

- Source
- Destination
- Mapping
- Transformation rules
- Expected volume
- Duration
- Failure behavior
- Rollback strategy
- RPO
- RTO
- Validation criteria
- Ownership

## Rollback

Import rollback is not always equivalent to reversing the import command.

If an import inserted:

```text
1,000,000 documents
```

then "rollback" may require deleting exactly those documents without affecting pre-existing data.

This is why migrations should use:

- Stable source identifiers
- Migration markers
- Dedicated collections where appropriate
- Backups
- Versioned scripts

For example:

```json
{
  "external_id": "source-123",
  "migration_id": "migration-2026-09-21"
}
```

A migration marker can make controlled rollback or reconciliation easier.

## Collection Replacement Strategy

For some migrations, a safer strategy is:

```text
orders
orders_new
     ↓
validate
     ↓
controlled cutover
```

This can reduce the risk of partially transformed production data.

The exact cutover strategy depends on:

- Traffic
- Dataset size
- Application compatibility
- Index creation time
- Downtime requirements
- Consistency requirements

## Import During Live Traffic

Importing into an active collection can affect:

- CPU
- Memory
- Disk I/O
- Replication
- Query latency
- Index maintenance
- Connection utilization

Monitor the deployment during the migration.

If import traffic competes with latency-sensitive API traffic, consider:

- Throttling
- Batch sizing
- Scheduling
- Dedicated migration workers
- Staging and cutover
- Temporary workload isolation

## Monitoring an Import

Track:

```text
Documents processed
Documents failed
Throughput
Latency
CPU
Memory
Disk I/O
Replication lag
Connections
Errors
Storage growth
```

A useful operational metric is:

```text
records / second
```

but throughput alone is insufficient.

A migration that inserts 50,000 records/second while causing severe replication lag may not be healthy.

## Import and Replication

On a replica set:

```text
Import
  ↓
Primary
  ↓
Oplog
  ↓
Secondaries
```

Large imports can generate significant oplog traffic.

Monitor:

- Secondary lag
- Oplog window
- Disk usage
- Replication throughput

Do not assume that successful primary writes mean the cluster is healthy.

## Import and Sharding

In a sharded cluster, import performance depends on shard-key distribution.

A poor shard key can create:

```text
Importer
   ↓
Single hot shard
   ↓
Bottleneck
```

A well-distributed shard key can allow:

```text
Importer
   ↓
mongos
   ↓
Shard 1
Shard 2
Shard 3
Shard 4
```

Before large imports into a sharded cluster, validate shard-key distribution.

## Encoding

Always explicitly consider text encoding.

UTF-8 is generally the safest choice for modern data interchange.

Example Python:

```python
open(
    "orders.csv",
    "r",
    encoding="utf-8",
    newline="",
)
```

Encoding problems may appear as:

- Invalid characters
- Import failures
- Corrupted names
- Incorrect CSV parsing

## CSV Delimiters and Quoting

CSV files may use:

```text
,
;
\t
```

and values may contain delimiters themselves.

Example:

```csv
customer_id,address
cust-1001,"12, Park Street, Kolkata"
```

Use a proper CSV parser rather than manually splitting on commas.

Incorrect:

```python
line.split(",")
```

Correct:

```python
csv.DictReader(source)
```

## Date Handling

Dates are a frequent import problem.

Avoid inconsistent representations such as:

```text
2026-09-21
21/09/2026
09-21-2026
September 21 2026
```

Prefer an explicit ISO-style representation where text is unavoidable:

```text
2026-09-21T10:30:00Z
```

Then convert it to a BSON Date during ingestion.

## Numeric Handling

For ordinary counters:

```text
integer
```

may be sufficient.

For monetary values, consider:

```text
Decimal128
```

rather than binary floating-point.

Example Extended JSON:

```json
{
  "amount": {
    "$numberDecimal": "149.99"
  }
}
```

This preserves decimal semantics more appropriately for financial data.

## Null vs Missing Fields

These are different MongoDB states.

Explicit null:

```json
{
  "phone": null
}
```

Missing field:

```json
{
  "customer_id": "cust-1001"
}
```

Queries can distinguish them.

Therefore, an import transformation should explicitly define how empty CSV values are mapped.

Do not automatically convert every empty string into:

```json
null
```

without understanding application semantics.

## Empty Strings

These are also distinct:

```json
{
  "phone": ""
}
```

and:

```json
{
  "phone": null
}
```

and:

```json
{}
```

These differences affect:

- `$exists`
- Equality filters
- Validation
- Application serialization
- Index behavior

Define missing/null/empty-string semantics before migration.

## Common Mistakes

### Using CSV for Complex MongoDB Documents

CSV cannot naturally represent nested documents and arrays.

Use JSON or BSON-oriented tooling when document structure matters.

### Treating JSON Strings as BSON Dates

This:

```json
{
  "created_at": "2026-09-21T10:00:00Z"
}
```

is not equivalent to an Extended JSON date representation.

Validate the BSON type after import.

### Using `float` for Financial Data

Binary floating-point can introduce representation issues.

Use Decimal128-oriented representations when exact decimal semantics are required.

### Importing Directly into Production

Always test the import first.

A successful development import does not prove production safety.

### Dropping Indexes Blindly

Index removal can improve bulk-load throughput but can severely damage application performance.

Only change indexes after understanding workload and traffic requirements.

### Assuming Counts Prove Correctness

Equal counts do not guarantee equal data.

A migration can have:

```text
Source count = Destination count
```

while still having incorrect:

- IDs
- types
- statuses
- amounts
- dates

Use reconciliation.

### Treating `mongoexport` as Backup

`mongoexport` produces interchange data.

Use MongoDB backup mechanisms for disaster recovery.

### Hard-Coding Credentials

Never commit or document database passwords.

Use approved secret management.

### Running Unbounded Exports

An unrestricted production export can:

- Generate huge files
- Consume disk
- Increase database load
- Expose sensitive data

Filter and project where appropriate.

## Troubleshooting

### Import Fails Immediately

```text
Symptom
↓
mongoimport exits with an error
↓
Possible causes
    - Invalid connection string
    - Authentication failure
    - TLS failure
    - Invalid file path
    - Invalid JSON
    - Unsupported import option
↓
Isolation strategy
↓
Run mongoimport --help
↓
Validate file syntax
↓
Test connection with mongosh
↓
Import a small sample
↓
Root cause
↓
Corrective action
↓
Prevention
    - Pin/document Database Tools version
    - Validate input before import
    - Test connection independently
```

### Invalid JSON

```text
Symptom
↓
JSON parser/importer rejects file
↓
Possible causes
    - Malformed JSON
    - Incorrect array structure
    - Invalid quoting
    - Incorrect Extended JSON
↓
Isolation strategy
↓
Validate a small sample
↓
Check JSON structure
↓
Check --jsonArray requirement
↓
Root cause
↓
Corrective action
↓
Prevention
    - Automated JSON validation
    - CI validation
    - Representative fixtures
```

### Incorrect BSON Types

```text
Symptom
↓
Imported query does not match expected documents
↓
Possible causes
    - Numeric value imported as string
    - Date imported as string
    - ObjectId imported as string
    - Boolean imported as string
↓
Isolation strategy
↓
Inspect document
↓
Check BSON types
↓
Compare source representation
↓
Root cause
↓
Corrective action
    - Extended JSON
    - Explicit transformation
    - Correct CSV type configuration
↓
Prevention
    - Type validation
    - Schema validation
    - Post-import verification
```

### Duplicate Key Errors

```text
Symptom
↓
Import reports duplicate-key failures
↓
Possible causes
    - Existing _id
    - Unique index collision
    - Duplicate source records
    - Incorrect upsert key
↓
Isolation strategy
↓
Identify conflicting field
↓
Inspect source
↓
Inspect target
↓
Root cause
↓
Corrective action
    - Clean source
    - Choose correct import mode
    - Correct matching key
↓
Prevention
    - Unique constraints
    - Migration design
    - Idempotency testing
```

### Import Is Too Slow

```text
Symptom
↓
Import throughput is below target
↓
Possible causes
    - Disk I/O
    - Network
    - Index maintenance
    - Small batches
    - Too few workers
    - Replica-set pressure
    - Shard-key hotspot
↓
Isolation strategy
↓
Measure throughput
↓
Inspect CPU / disk / network
↓
Check replication lag
↓
Check indexes
↓
Check shard distribution
↓
Root cause
↓
Corrective action
    - Tune batching
    - Tune workers
    - Optimize indexes
    - Throttle or schedule workload
↓
Prevention
    - Performance test
    - Capacity planning
    - Migration runbook
```

### Imported Data Is Correct but Application Fails

```text
Symptom
↓
Import completes but API behavior is incorrect
↓
Possible causes
    - Wrong BSON types
    - Missing fields
    - Unexpected nulls
    - Incorrect indexes
    - Schema mismatch
↓
Isolation strategy
↓
Run application queries
↓
Inspect representative documents
↓
Compare expected schema
↓
Check query plans
↓
Root cause
↓
Corrective action
    - Transform data
    - Add validation
    - Update migration
↓
Prevention
    - Integration tests
    - Schema contracts
    - Staging migration
```

## Operational Checklist

### Before Import

- [ ] Confirm source and destination.
- [ ] Confirm database and collection.
- [ ] Validate input syntax.
- [ ] Validate encoding.
- [ ] Validate BSON type requirements.
- [ ] Estimate dataset size.
- [ ] Review indexes.
- [ ] Review unique constraints.
- [ ] Define duplicate behavior.
- [ ] Test in development.
- [ ] Test in staging.
- [ ] Define rollback strategy.
- [ ] Confirm backup/recovery point.
- [ ] Define reconciliation checks.

### During Import

- [ ] Monitor throughput.
- [ ] Monitor CPU.
- [ ] Monitor memory.
- [ ] Monitor disk.
- [ ] Monitor replication lag.
- [ ] Monitor errors.
- [ ] Monitor storage growth.
- [ ] Track processed records.
- [ ] Track failed records.
- [ ] Avoid uncontrolled application impact.

### After Import

- [ ] Compare record counts.
- [ ] Reconcile business identifiers.
- [ ] Validate BSON types.
- [ ] Validate required fields.
- [ ] Validate indexes.
- [ ] Run application smoke tests.
- [ ] Run critical queries.
- [ ] Review performance.
- [ ] Archive migration logs.
- [ ] Remove temporary files.
- [ ] Confirm sensitive exports are deleted or secured.

## Interview Considerations

### What is the difference between `mongoexport` and `mongodump`?

`mongoexport` creates JSON or CSV representations for data interchange.

`mongodump` creates BSON-oriented logical backups that are intended to be restored with `mongorestore`.

They solve different problems.

### Why is Extended JSON important?

JSON cannot natively represent all MongoDB BSON types.

Extended JSON provides representations for types such as:

- ObjectId
- Date
- Decimal128
- Binary

This prevents important type information from being lost during interchange.

### Why can CSV be dangerous for MongoDB migrations?

CSV is flat and weakly typed.

MongoDB documents can contain:

```text
Nested documents
Arrays
ObjectIds
Dates
Decimal128
Binary data
```

A CSV conversion can therefore lose structure or type information.

### How would you migrate a large JSON dataset safely?

A strong answer should include:

```text
Validate source
    ↓
Sample import
    ↓
Development
    ↓
Staging
    ↓
Backup
    ↓
Production import
    ↓
Monitor
    ↓
Reconcile
    ↓
Application validation
```

Also discuss:

- Batch size
- Idempotency
- Duplicate handling
- Indexes
- Replication lag
- Rollback
- RPO/RTO

### How do you make an import idempotent?

Use a stable business identifier or migration identifier and define deterministic upsert behavior.

For example:

```javascript
{
  "external_order_id": 1
}
```

with:

```javascript
db.orders.createIndex(
  { external_order_id: 1 },
  { unique: true }
)
```

Then the import can use that field as its identity boundary.

### Why should you not use `mongoexport` as a backup?

Because JSON/CSV export is primarily an interchange representation and does not provide the complete backup and recovery semantics expected from a production disaster-recovery system.

### How would you troubleshoot an import that succeeds but produces incorrect application behavior?

Check:

1. BSON types.
2. Required fields.
3. Null vs missing fields.
4. Identifier types.
5. Date representation.
6. Numeric precision.
7. Indexes.
8. Application query filters.
9. Schema validation.
10. Representative application requests.

## Key Takeaways

- **Use JSON for document-oriented interchange and Extended JSON when MongoDB-specific BSON types such as ObjectId, Date, and Decimal128 must be preserved.**
- **Use CSV primarily for flat, tabular data; complex MongoDB documents containing nested structures and arrays generally require JSON or BSON-aware workflows.**
- **Treat `mongoimport`/`mongoexport` as data interchange tools and `mongodump`/`mongorestore` or managed backup capabilities as backup and recovery mechanisms.**
- **Production imports should be repeatable and validated: test in lower environments, control batching and indexing, monitor resource and replication impact, reconcile source and destination, and define rollback behavior.**
- **The most dangerous import/export failures are often semantic rather than syntactic: incorrect BSON types, duplicate identities, lost nesting, null-vs-missing differences, precision loss, and uncontrolled exposure of production data.**