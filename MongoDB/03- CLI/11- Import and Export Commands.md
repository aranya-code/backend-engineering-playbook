# 11- Import and Export Commands

## Overview

MongoDB import and export tooling is used to move document data between files and MongoDB deployments.

The main tools are:

| Tool | Primary purpose | Data format |
|---|---|---|
| `mongoimport` | Import documents into MongoDB | JSON, CSV, TSV |
| `mongoexport` | Export documents from MongoDB | JSON, CSV, TSV |
| `mongodump` | Create logical BSON backups | BSON |
| `mongorestore` | Restore BSON dumps | BSON |

The distinction is important:

```text
Data interchange
    ↓
mongoexport / mongoimport

Backup and restore
    ↓
mongodump / mongorestore
```

`mongoexport` and `mongoimport` are primarily data interchange tools. They are not intended to provide a complete backup/restore mechanism with the same characteristics as `mongodump` and `mongorestore`.

A senior engineer should select the tool based on the actual requirement:

- Move JSON or CSV data between systems → `mongoimport` / `mongoexport`
- Transfer a dataset for application or ETL purposes → `mongoimport` / `mongoexport`
- Create a logical MongoDB backup → `mongodump`
- Restore a logical BSON backup → `mongorestore`
- Build a disaster-recovery strategy → managed backups or an appropriate MongoDB backup architecture, not ad-hoc exports

## Import and Export Architecture

A typical workflow is:

```mermaid
flowchart LR
    File[JSON / CSV / TSV]
    Import[mongoimport]
    Mongo[(MongoDB)]
    Export[mongoexport]
    Dump[mongodump]
    Restore[mongorestore]
    Backup[BSON Backup]

    File --> Import
    Import --> Mongo
    Mongo --> Export
    Export --> File

    Mongo --> Dump
    Dump --> Backup
    Backup --> Restore
    Restore --> Mongo
```

The file-based tools operate on serialized data, while `mongodump` preserves MongoDB-specific BSON representations.

## Tool Selection

| Requirement | Recommended tool |
|---|---|
| Import JSON documents | `mongoimport` |
| Import CSV data | `mongoimport` |
| Import TSV data | `mongoimport` |
| Export JSON documents | `mongoexport` |
| Export CSV data | `mongoexport` |
| Export tabular data for analysis | `mongoexport` |
| Logical MongoDB backup | `mongodump` |
| Restore logical MongoDB backup | `mongorestore` |
| Disaster recovery | Managed backup / backup architecture |
| Point-in-time recovery | Deployment-specific backup tooling |
| Cross-system data exchange | `mongoexport` / `mongoimport` |

## `mongoimport`

`mongoimport` loads structured external data into a MongoDB collection.

Basic JSON import:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --file orders.json
```

For newline-delimited JSON:

```json
{"customerId":"C001","status":"pending","amount":1250}
{"customerId":"C002","status":"completed","amount":900}
{"customerId":"C003","status":"cancelled","amount":450}
```

Import:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --file orders.json
```

## JSON Import Modes

MongoDB import workflows commonly encounter two JSON layouts:

### JSON Array

```json
[
  {
    "customerId": "C001",
    "status": "pending"
  },
  {
    "customerId": "C002",
    "status": "completed"
  }
]
```

Use:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --file orders.json \
  --jsonArray
```

### Newline-Delimited JSON

```json
{"customerId":"C001","status":"pending"}
{"customerId":"C002","status":"completed"}
```

Use:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --file orders.json
```

Do not use `--jsonArray` for newline-delimited JSON.

## Importing CSV

Example CSV:

```csv
customerId,status,amount
C001,pending,1250
C002,completed,900
C003,cancelled,450
```

Import:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --type csv \
  --headerline \
  --file orders.csv
```

`--headerline` tells `mongoimport` to use the first row as field names.

Without it, CSV field mapping must be specified appropriately.

## CSV Type Handling

CSV is inherently less expressive than BSON.

For example:

```csv
customerId,amount,active
C001,1250,true
```

A CSV import can require careful type handling because textual input does not naturally preserve MongoDB's full BSON type system.

For production migrations, explicitly validate:

- Numeric fields
- Boolean fields
- Dates
- ObjectIds
- Null values
- Arrays
- Embedded documents

Do not assume that a CSV representation preserves the intended MongoDB schema automatically.

## Importing TSV

Tab-separated data can be imported using the appropriate type option:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --type tsv \
  --headerline \
  --file orders.tsv
```

Use TSV when the source system produces tab-delimited records.

## Importing into a Different Collection

The source file does not need to use the same collection name as the source system.

Example:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders_staging \
  --file orders.json
```

A staging collection is often safer for migration validation.

```text
Source file
    ↓
orders_staging
    ↓
Validate
    ↓
Transform
    ↓
Production collection
```

## Importing into a Different Database

The database can be specified through the URI:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce_staging" \
  --collection orders \
  --file orders.json
```

For authenticated deployments:

```bash
mongoimport \
  --uri "mongodb://mongodb.example.com/ecommerce_staging?authSource=admin" \
  --username migration_user \
  --collection orders \
  --file orders.json
```

Avoid embedding passwords directly in shell history or scripts.

## Importing with Authentication

A safer pattern is to provide the username separately and allow the tool to obtain the password through its supported credential mechanism.

Example:

```bash
mongoimport \
  --host mongodb.example.com \
  --port 27017 \
  --username migration_user \
  --authenticationDatabase admin \
  --db ecommerce \
  --collection orders \
  --file orders.json
```

Do not commit credentials into:

- Git repositories
- Dockerfiles
- Shell scripts
- CI/CD YAML
- Terraform source
- Kubernetes manifests

## Importing with TLS

Production MongoDB deployments commonly require TLS.

Example:

```bash
mongoimport \
  --uri "mongodb://mongodb.example.com/ecommerce?authSource=admin" \
  --tls \
  --tlsCAFile /etc/mongodb/ca.pem \
  --username migration_user \
  --collection orders \
  --file orders.json
```

Use the certificate and TLS options required by the deployment.

Do not disable certificate validation merely to bypass a connection problem in production.

## Insert vs Upsert vs Replace

Import workflows can behave differently depending on whether existing documents should be preserved, replaced, or updated.

Before importing production data, explicitly determine:

```text
Should existing documents remain?
Should matching documents be replaced?
Should existing documents be updated?
Should duplicate identifiers fail?
```

A migration should not rely on an implicit assumption about duplicate behavior.

## Dropping a Collection Before Import

Some import workflows can use collection replacement behavior.

A destructive operation such as:

```text
drop existing collection
↓
import replacement dataset
```

must be treated as a migration event.

Before doing this:

- Confirm the target database
- Verify the backup
- Validate the source file
- Confirm document count
- Confirm indexes
- Confirm application compatibility
- Establish rollback steps

Never add destructive flags to an import command casually.

## Import Validation

After importing:

```javascript
use ecommerce

db.orders.countDocuments()
```

Check a sample:

```javascript
db.orders.find().limit(5)
```

Check indexes:

```javascript
db.orders.getIndexes()
```

Check schema or field types:

```javascript
db.orders.aggregate([
  {
    $sample: {
      size: 20
    }
  }
])
```

For production migrations, validation should compare source and destination characteristics.

## Import Validation Checklist

| Check | Example |
|---|---|
| Document count | `countDocuments()` |
| Sample records | `find().limit()` |
| Required fields | Aggregation / validation |
| Data types | Sample inspection |
| Duplicate keys | Unique index validation |
| Indexes | `getIndexes()` |
| Query performance | `explain()` |
| Application compatibility | Integration test |
| Referential assumptions | Application validation |

## `mongoexport`

`mongoexport` exports collection data into JSON, CSV, or TSV.

Basic JSON export:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --out orders.json
```

The exported data is suitable for data interchange and analysis.

It should not automatically be considered a complete MongoDB backup.

## Exporting JSON Arrays

Use:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --jsonArray \
  --out orders.json
```

This produces a JSON array representation.

For large datasets, newline-delimited JSON is often more practical for streaming and processing.

## Exporting CSV

Example:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --type=csv \
  --fields=customerId,status,amount,createdAt \
  --out orders.csv
```

Explicitly specify fields for production exports rather than exporting every field by default.

This is particularly important when documents contain:

- Credentials
- Tokens
- Personal information
- Internal metadata
- Large embedded structures

## Exporting TSV

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --type=tsv \
  --fields=customerId,status,amount \
  --out orders.tsv
```

Use the format expected by the consuming system.

## Exporting Selected Documents

Use a query filter:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --query='{"status":"completed"}' \
  --out completed-orders.json
```

This is useful for:

- Data analysis
- Migration subsets
- Reporting
- Debugging
- Environment seeding

Do not export sensitive production data simply because it is convenient for local development.

## Exporting a Date Range

Example:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --query='{"createdAt":{"$gte":{"$date":"2026-01-01T00:00:00Z"}}}' \
  --out orders-2026.json
```

The exact extended JSON syntax should match the MongoDB tooling version in use.

For large date-range exports, ensure the filter is supported by an appropriate index.

## Exporting with Projection

Export only required fields:

```bash
mongoexport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --type=csv \
  --fields=customerId,status,amount \
  --out orders.csv
```

This reduces:

- File size
- Data exposure
- Downstream processing cost
- Transfer time

## Exporting from a Secondary

For workloads where operational architecture and read preferences permit it, exports may be directed at an appropriate replica-set member.

However, do not assume that exporting from a secondary is always free.

Large exports can still:

- Consume I/O
- Consume CPU
- Affect replication resources
- Compete with application workloads
- Increase operational pressure

Plan large exports as production workloads.

## Exporting Large Collections

For large datasets:

```text
MongoDB
   ↓
Read workload
   ↓
Serialization
   ↓
File
   ↓
Disk / object storage
```

Potential bottlenecks include:

- MongoDB read throughput
- Disk I/O
- Network bandwidth
- Serialization
- Destination disk space

For very large datasets, consider:

- Exporting during lower traffic periods
- Filtering by time ranges
- Partitioning exports
- Writing directly to controlled storage workflows
- Using MongoDB's supported backup mechanisms instead of ad-hoc exports

## `mongoexport` vs `mongodump`

This distinction is critical.

| Feature | `mongoexport` | `mongodump` |
|---|---|---|
| Primary purpose | Data interchange | Logical backup |
| JSON | Yes | No |
| CSV | Yes | No |
| BSON | No | Yes |
| MongoDB-specific types | Less complete interchange representation | Preserved in BSON |
| Index definitions | Not a complete backup representation | Included in dump metadata |
| Restore tool | `mongoimport` | `mongorestore` |
| Backup strategy | Not ideal | Appropriate for logical backups |
| Human-readable output | Yes | No |

If the requirement is:

```text
"Give me these records as CSV"
```

use `mongoexport`.

If the requirement is:

```text
"Back up this MongoDB database so it can be restored"
```

use `mongodump` or the deployment's supported backup system.

## `mongodump`

Create a logical dump:

```bash
mongodump \
  --uri "mongodb://localhost:27017/ecommerce" \
  --out ./backup
```

A dump can contain BSON data and metadata required for restoration.

## Dumping a Specific Database

```bash
mongodump \
  --uri "mongodb://localhost:27017" \
  --db ecommerce \
  --out ./backup
```

The resulting directory structure can contain database and collection dump artifacts.

## Dumping a Specific Collection

```bash
mongodump \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders \
  --out ./backup
```

This is useful for targeted migration or recovery workflows.

## Compressed Dumps

Use compression where appropriate:

```bash
mongodump \
  --uri "mongodb://localhost:27017/ecommerce" \
  --gzip \
  --archive=./ecommerce.archive.gz
```

This can reduce storage and transfer requirements.

Compression introduces CPU overhead, so evaluate the trade-off for very high-throughput environments.

## Archive Format

A single archive can simplify movement of a logical dump:

```bash
mongodump \
  --uri "mongodb://localhost:27017/ecommerce" \
  --archive=./ecommerce.archive
```

Compressed archive:

```bash
mongodump \
  --uri "mongodb://localhost:27017/ecommerce" \
  --archive=./ecommerce.archive.gz \
  --gzip
```

## `mongorestore`

Restore a dump:

```bash
mongorestore \
  --uri "mongodb://localhost:27017" \
  ./backup
```

Restore a compressed archive:

```bash
mongorestore \
  --uri "mongodb://localhost:27017" \
  --gzip \
  --archive=./ecommerce.archive.gz
```

## Restoring a Specific Database

Example:

```bash
mongorestore \
  --uri "mongodb://localhost:27017" \
  --db ecommerce \
  ./backup/ecommerce
```

For current MongoDB tooling, review the version-specific behavior of database and namespace options before using them in automated restore scripts.

## Restore to a Different Database

Namespace remapping can be useful for testing restores.

Conceptually:

```text
production database
        ↓
logical backup
        ↓
restore
        ↓
ecommerce_restore
```

Use appropriate namespace mapping options when restoring.

This is useful for:

- Disaster-recovery testing
- Data validation
- Migration testing
- Development environment reconstruction

## Restore Testing

A backup is not validated merely because `mongodump` completed successfully.

A proper restore test should include:

```text
Backup
  ↓
Restore into isolated environment
  ↓
Verify database
  ↓
Verify collection counts
  ↓
Verify indexes
  ↓
Run representative queries
  ↓
Run application smoke tests
  ↓
Measure recovery time
```

## Backup vs Export

A common mistake is:

```bash
mongoexport ... > backup.json
```

and then considering the JSON file a complete MongoDB backup.

This can omit important database characteristics.

For example:

- Index definitions
- MongoDB-specific metadata
- Exact BSON representation
- Collection configuration
- Deployment-level state

Use a real backup strategy for disaster recovery.

## Extended JSON

MongoDB's BSON type system includes values that JSON does not represent natively.

Examples:

- `ObjectId`
- `Date`
- Binary data
- Decimal128
- Int32 / Int64 distinctions

Extended JSON provides representations for BSON-specific values.

Example:

```json
{
  "_id": {
    "$oid": "64f000000000000000000001"
  },
  "createdAt": {
    "$date": "2026-09-20T10:00:00Z"
  }
}
```

This is particularly important when moving data between systems.

## BSON Type Preservation

Suppose a MongoDB document contains:

```javascript
{
  _id: ObjectId("64f000000000000000000001"),
  amount: NumberDecimal("1250.50"),
  createdAt: ISODate("2026-09-20T10:00:00Z")
}
```

A naïve JSON representation can lose important type information.

When type fidelity matters, use BSON-based backup tooling rather than treating JSON as a transparent backup format.

## ObjectId During Import

An identifier such as:

```json
{
  "_id": "64f000000000000000000001"
}
```

is a string.

It is not equivalent to:

```javascript
{
  _id: ObjectId("64f000000000000000000001")
}
```

This distinction can affect:

- Queries
- Indexes
- Joins
- Application serialization
- Referential relationships

Validate identifier types after imports.

## Date Handling

A JSON string:

```json
{
  "createdAt": "2026-09-20T10:00:00Z"
}
```

is not automatically equivalent to a BSON Date.

A BSON Date is represented in Extended JSON as:

```json
{
  "createdAt": {
    "$date": "2026-09-20T10:00:00Z"
  }
}
```

If application code expects BSON dates, validate the imported field type.

## CSV Limitations

CSV is useful for flat tabular data but is a poor representation for deeply nested MongoDB documents.

For example:

```javascript
{
  customer: {
    name: "Aranya",
    address: {
      city: "Kolkata"
    }
  },
  items: [
    {
      sku: "SKU-001",
      quantity: 2
    }
  ]
}
```

does not naturally map to a simple CSV row.

CSV imports and exports should therefore be used when the source and target data models are sufficiently tabular.

For complex document structures, JSON or BSON is generally more appropriate.

## Staging Imports

For production migrations, use a staging collection:

```text
orders.json
    ↓
mongoimport
    ↓
orders_staging
    ↓
Validation
    ↓
Transformation
    ↓
Production collection
```

Example:

```bash
mongoimport \
  --uri "mongodb://localhost:27017/ecommerce" \
  --collection orders_staging \
  --file orders.json
```

Then validate:

```javascript
db.orders_staging.countDocuments()
```

and inspect:

```javascript
db.orders_staging.find().limit(10)
```

## Migration Validation

A migration should validate more than document count.

Example validation dimensions:

| Dimension | Validation |
|---|---|
| Count | Source vs target |
| IDs | Duplicate / missing IDs |
| Types | BSON type comparison |
| Required fields | Schema checks |
| Dates | Range and timezone checks |
| Numeric values | Aggregate comparisons |
| Indexes | Target index verification |
| Queries | Explain representative queries |
| Application | Smoke tests |

## Importing into a Production Collection

Direct imports can be appropriate for controlled operational tasks, but they should be treated as deployment changes.

Before execution:

```text
Source validated
↓
Target verified
↓
Backup / rollback confirmed
↓
Indexes reviewed
↓
Application compatibility verified
↓
Maintenance window / workload impact assessed
↓
Import executed
↓
Validation
↓
Application verification
```

## Bulk Import Performance

Large imports can generate substantial database workload.

Factors include:

- Batch size
- Index count
- Network throughput
- Disk throughput
- Write concern
- Document size
- Validation rules
- Replica-set replication
- Target hardware

A common performance consideration is that every maintained index can increase write cost.

If the target is an empty collection, a controlled migration may use an index strategy that avoids unnecessary index maintenance during bulk loading, followed by index creation afterward.

This must be planned carefully because building indexes afterward also consumes substantial resources.

## Import into Replica Sets

In a replica set:

```text
mongoimport
    ↓
Primary
    ↓
Replication
 ┌──┴─────────┐
 ↓            ↓
Secondary   Secondary
```

Large imports therefore affect not only the primary but also replication.

Potential consequences:

- Increased replication lag
- Increased disk usage
- Higher I/O
- Longer recovery windows
- Application latency changes

Monitor replica health during large production imports.

## Import into Sharded Clusters

In a sharded deployment:

```text
mongoimport
    ↓
mongos / target endpoint
    ↓
Query routing
    ↓
Shard key distribution
 ┌────┼────┐
 ↓    ↓    ↓
S1   S2   S3
```

Large imports should account for shard-key distribution.

A poor shard key can cause:

- Hot shards
- Uneven write distribution
- Reduced parallelism
- Storage imbalance

Bulk migration should therefore be tested against the actual sharding topology.

## Import and Unique Indexes

Suppose the target collection has:

```javascript
{
  email: 1
}
```

with:

```text
unique: true
```

An import containing duplicate email addresses can fail.

Before importing into a uniquely indexed collection:

```text
Validate source uniqueness
        ↓
Import
        ↓
Monitor errors
        ↓
Validate target uniqueness
```

Do not remove a unique index merely to make a migration succeed unless the data model and migration plan explicitly require it.

## Import Error Handling

For production imports, capture:

- Exit code
- Standard output
- Standard error
- Imported document count
- Failed document count where reported
- Duplicate key errors
- Parsing errors
- Validation errors

Example shell workflow:

```bash
mongoimport \
  --uri "$MONGODB_URI" \
  --collection orders_staging \
  --file orders.json \
  > import.log 2>&1

status=$?

if [ "$status" -ne 0 ]; then
  echo "MongoDB import failed"
  exit "$status"
fi
```

Do not treat the existence of an output file as proof of successful migration.

## CI/CD Data Imports

Data imports should generally not be hidden inside application deployment steps.

Prefer explicit migration workflows:

```text
CI/CD
  ↓
Validate input
  ↓
Backup / recovery verification
  ↓
Import job
  ↓
Validation job
  ↓
Application deployment
```

For Kubernetes, this can be implemented through a controlled Job or migration workflow rather than putting large imports into container startup scripts.

## Docker Import Example

If MongoDB runs in Docker:

```bash
docker exec -i mongodb \
  mongoimport \
  --db ecommerce \
  --collection orders \
  --file /imports/orders.json
```

The file must exist inside the container.

A more explicit workflow is to mount a directory:

```text
./imports
    ↓
Container volume
    ↓
/imports
    ↓
mongoimport
```

## Kubernetes Import Example

A migration Job can mount the import file and execute:

```bash
mongoimport \
  --uri "$MONGODB_URI" \
  --collection orders \
  --file /imports/orders.json
```

Production considerations include:

- Job retry behavior
- Idempotency
- Secret access
- Network policy
- Resource limits
- Timeout handling
- Migration observability

## Idempotent Import Design

A migration should ideally be safe to retry or have an explicit recovery strategy.

For example:

```text
Input records
    ↓
Stable business identifier
    ↓
Upsert
    ↓
Retry-safe migration
```

Conceptually:

```javascript
db.orders.updateOne(
  {
    externalId: "ERP-10001"
  },
  {
    $set: {
      status: "completed",
      amount: 1250
    }
  },
  {
    upsert: true
  }
)
```

For complex migrations, application-level scripts using PyMongo can provide more control than a direct `mongoimport`.

## When to Use PyMongo Instead

Use PyMongo when the migration requires:

- Complex transformations
- Conditional writes
- API calls
- Cross-collection logic
- Validation
- Custom retry behavior
- Idempotency
- Detailed error reporting
- Transactional workflows

Example architecture:

```text
Input
  ↓
Python migration
  ↓
Validation
  ↓
Transformation
  ↓
MongoDB
  ↓
Verification
```

`mongoimport` is preferable when the transformation requirements are simple and the source format already matches the target document model.

## Export for Analytics

A common backend workflow is:

```text
MongoDB
    ↓
mongoexport
    ↓
JSON / CSV
    ↓
Object storage
    ↓
Analytics / ETL
```

For large analytics pipelines, however, repeatedly exporting full collections can become expensive.

Consider:

- Incremental extraction
- Change streams
- Managed analytics integrations
- Data warehouse pipelines
- Event-driven architectures

Use the simplest mechanism that meets the freshness and scale requirements.

## Security Considerations

Import/export operations can expose entire datasets.

Treat exported files as sensitive assets.

Protect:

- Export files
- Temporary files
- Backup archives
- Logs
- Command history
- CI/CD artifacts
- Object-storage buckets

Never upload production exports containing sensitive data to public storage.

## Exported Data Lifecycle

A secure export workflow is:

```text
MongoDB
    ↓
Restricted export identity
    ↓
Temporary encrypted storage
    ↓
Transfer
    ↓
Controlled destination
    ↓
Validation
    ↓
Retention expiration
    ↓
Secure deletion
```

Do not allow temporary exports to accumulate indefinitely.

## Encryption

For sensitive datasets:

```text
MongoDB
    ↓
Encrypted transport
    ↓
Export process
    ↓
Encrypted storage
```

Use TLS for MongoDB connections and appropriate encryption for the destination storage.

For AWS-based workflows, use appropriate encryption and access controls for S3 or other storage services.

## Credential Security

Avoid:

```bash
mongoexport \
  --uri "mongodb://user:password@host/db" \
  ...
```

when the command may be recorded in:

- Shell history
- Process listings
- CI/CD logs
- Terminal recordings

Prefer supported credential mechanisms and secret-management infrastructure.

## Backup Security

A backup archive can contain an entire production database.

Treat:

```text
ecommerce.archive.gz
```

as highly sensitive.

Protect it with:

- Encryption
- Access controls
- Restricted network access
- Retention policies
- Audit logging
- Integrity validation

## Disaster Recovery

Exports are not automatically a disaster-recovery solution.

A real DR strategy should define:

```text
RPO
↓
How much data can be lost?

RTO
↓
How quickly must service recover?

Backup
↓
Where is it stored?

Restore
↓
How is recovery performed?

Validation
↓
How is restore correctness proven?

Testing
↓
How often is recovery tested?
```

## Backup Validation

A successful dump command is not enough.

Validate:

```text
Dump completed
↓
Archive exists
↓
Archive is readable
↓
Restore succeeds
↓
Collections exist
↓
Document counts are reasonable
↓
Indexes exist
↓
Representative queries work
↓
Application smoke test succeeds
```

## Disaster Recovery Runbook

```text
Failure detected
↓
Declare recovery event
↓
Identify recovery point
↓
Provision target MongoDB environment
↓
Restore backup
↓
Validate collections and indexes
↓
Validate application connectivity
↓
Run application smoke tests
↓
Redirect application traffic
↓
Monitor
↓
Record recovery time and issues
```

The runbook should be tested before a real disaster.

## Common Mistakes

### Using `mongoexport` as a Full Backup

Why it happens:

```text
Export succeeded
↓
JSON file exists
↓
Assumed to be a backup
```

Why it is incorrect:

JSON/CSV export is primarily data interchange and does not preserve all MongoDB deployment and BSON characteristics required for a complete backup strategy.

Use `mongodump` or supported managed backup mechanisms for logical recovery.

### Importing JSON Without Checking BSON Types

Example:

```json
{
  "_id": "64f000000000000000000001"
}
```

may become a string rather than an `ObjectId`.

Always validate critical field types.

### Importing Directly into Production

A malformed file can create:

- Invalid documents
- Duplicate-key failures
- Schema violations
- Unexpected data growth
- Application errors

Prefer staging and validation.

### Forgetting Indexes

A data migration may succeed while application performance degrades because target indexes were not created.

After migration:

```javascript
db.orders.getIndexes()
```

Then test representative queries:

```javascript
db.orders.find({
  customerId: ObjectId("64f000000000000000000001")
}).explain("executionStats")
```

### Ignoring Replica Lag

Large imports can create significant replication pressure.

Monitor:

```javascript
rs.status()
```

during high-volume writes.

### Exporting Sensitive Fields

Do not export every field by default when a downstream system only needs a subset.

Prefer explicit field selection.

## Production Pitfalls

| Pitfall | Impact | Prevention |
|---|---|---|
| Export used as backup | Recovery failure | Use proper backup tooling |
| Wrong `authSource` | Authentication failure | Validate connection configuration |
| Wrong JSON mode | Import failure | Distinguish array vs NDJSON |
| BSON types lost | Application bugs | Validate types |
| Missing indexes | Query regression | Recreate and verify indexes |
| Large import during peak traffic | Latency increase | Schedule and monitor |
| Import into wrong database | Data corruption | Verify target explicitly |
| Duplicate unique keys | Import failure | Validate source |
| Export files left on disk | Data exposure | Encrypt and expire |
| No restore test | Unknown recovery capability | Perform recovery drills |

## Import and Export Troubleshooting

### Import Fails with Parse Errors

```text
Symptom
↓
mongoimport rejects input
↓
Possible causes
    - Invalid JSON
    - Wrong --jsonArray setting
    - Incorrect CSV headers
    - Malformed CSV
    - Unsupported data representation
↓
Isolation strategy
↓
Validate source file
↓
Inspect first records
↓
Confirm format
↓
Run small staging import
↓
Root cause
↓
Corrective action
↓
Prevention
    - Input validation
    - Schema checks
    - Migration testing
```

### Duplicate Key Errors

```text
Symptom
↓
Import fails with duplicate key error
↓
Possible causes
    - Duplicate _id values
    - Unique application field
    - Existing target documents
↓
Isolation strategy
↓
Inspect target indexes
↓
Identify duplicate field
↓
Compare source and target
↓
Root cause
↓
Corrective action
    - Clean source
    - Correct migration strategy
    - Use controlled upsert logic where appropriate
↓
Prevention
    - Pre-import uniqueness validation
```

### Imported Data Has Wrong Types

```text
Symptom
↓
Queries or application logic behave incorrectly
↓
Possible causes
    - CSV conversion
    - Stringified ObjectId
    - Stringified dates
    - Numeric values imported incorrectly
↓
Isolation strategy
↓
Inspect BSON types
↓
Compare source representation
↓
Check migration transformation
↓
Root cause
↓
Corrective action
    - Re-import or transform
↓
Prevention
    - Type validation
    - Staging imports
```

### Import Is Too Slow

```text
Symptom
↓
Large import takes unexpectedly long
↓
Possible causes
    - Network bottleneck
    - Disk bottleneck
    - Many indexes
    - Validation overhead
    - Replica-set replication
    - Large documents
    - Resource contention
↓
Isolation strategy
↓
Measure import throughput
↓
Inspect MongoDB resource usage
↓
Check index count
↓
Check replication lag
↓
Check network and storage
↓
Root cause
↓
Corrective action
↓
Prevention
    - Capacity testing
    - Controlled migration windows
    - Batch planning
```

### Restore Fails

```text
Symptom
↓
mongorestore fails
↓
Possible causes
    - Corrupt/incomplete backup
    - Version incompatibility
    - Authentication failure
    - Network issue
    - Target configuration
    - Duplicate existing data
↓
Isolation strategy
↓
Validate archive
↓
Test restore in isolated environment
↓
Check MongoDB versions
↓
Check target state
↓
Root cause
↓
Corrective action
↓
Prevention
    - Automated restore testing
    - Version compatibility checks
    - Backup integrity validation
```

## Operational Best Practices

- Use `mongoimport` and `mongoexport` for controlled data interchange.
- Use `mongodump` and `mongorestore` for logical MongoDB backup and restore workflows.
- Do not treat JSON or CSV exports as equivalent to a complete backup.
- Validate BSON types after imports, especially `ObjectId`, dates, numeric values, and decimals.
- Prefer staging collections for significant production migrations.
- Verify document counts, data types, indexes, and representative queries after import.
- Account for replica-set replication pressure during large imports.
- Explicitly select exported fields when sensitive or unnecessary data exists.
- Protect exports and backup archives with encryption and access controls.
- Use secret-management systems for MongoDB credentials.
- Test restores regularly rather than assuming backups are recoverable.
- Make migration workflows observable, repeatable, and as idempotent as practical.
- Measure RPO and RTO during recovery exercises.
- Review MongoDB and database-tool versions before automating backup or migration workflows.
- Treat large imports and exports as production workloads with capacity and scheduling considerations.

## Interview Considerations

### What is the difference between `mongoimport` and `mongorestore`?

`mongoimport` imports data from interchange formats such as JSON and CSV.

`mongorestore` restores MongoDB logical backups produced by `mongodump`, using BSON and dump metadata.

### Is `mongoexport` a backup tool?

It is primarily a data-export/interchange tool. It should not be treated as a complete MongoDB backup mechanism.

### Why can CSV imports cause type problems?

CSV represents values as tabular text and does not naturally preserve MongoDB's complete BSON type system.

### When should you use `mongoimport` instead of a Python migration?

Use `mongoimport` when the source data already closely matches the target MongoDB document structure.

Use PyMongo when the migration requires complex validation, transformation, conditional logic, custom retries, or cross-system operations.

### Why use a staging collection?

It separates:

```text
Data ingestion
```

from:

```text
Production mutation
```

allowing validation before the production dataset is changed.

### Why can a large import affect replica-set health?

Writes are replicated to secondary members. A high-volume import can increase replication workload and produce secondary lag.

### What should be verified after a migration?

At minimum:

```text
Document counts
BSON types
Required fields
Indexes
Representative queries
Application behavior
```

### How would you design a production MongoDB backup strategy?

Start with:

```text
RPO / RTO
↓
Backup mechanism
↓
Backup storage
↓
Retention
↓
Encryption
↓
Restore procedure
↓
Validation
↓
Regular recovery testing
```

The strategy should use the backup capabilities appropriate for the MongoDB deployment rather than relying only on ad-hoc exports.

## Key Takeaways

- **Use `mongoimport` and `mongoexport` for data interchange, while `mongodump` and `mongorestore` are designed for logical MongoDB backup and restore workflows.**
- **Treat BSON type preservation as a migration concern; JSON and especially CSV can change the representation of `ObjectId`, dates, decimals, and other MongoDB-specific types.**
- **For production migrations, prefer staging, explicit validation, index verification, representative query testing, and controlled rollback procedures.**
- **Large imports and exports are production workloads that can consume CPU, storage, network, and replication capacity; schedule and monitor them accordingly.**
- **A backup is only operationally useful when it can be restored: validate backup integrity and perform regular recovery tests against defined RPO and RTO targets.**