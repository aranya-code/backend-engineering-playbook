# 01- MongoDB Shell Basics

## Overview

`mongosh` is MongoDB's modern interactive shell for connecting to MongoDB deployments, inspecting databases, executing queries, managing indexes, troubleshooting operations, and performing administrative tasks.

For backend engineers, `mongosh` is primarily an operational and diagnostic tool. Application code should normally use a driver such as PyMongo, while `mongosh` is useful for:

- Verifying connectivity
- Inspecting databases and collections
- Testing query behavior
- Validating indexes
- Running aggregation pipelines
- Inspecting execution plans
- Investigating production incidents
- Performing controlled administrative operations
- Validating authentication and authorization
- Inspecting replica-set state

The shell should be treated as an operational interface to MongoDB rather than as a replacement for application code.

## MongoDB Shell Architecture

The basic interaction model is:

```mermaid
flowchart LR
    Engineer[Backend Engineer]
    Shell[mongosh]
    Driver[MongoDB Driver Protocol]
    Server[MongoDB Server / mongos]
    Replica[(Replica Set / Sharded Cluster)]

    Engineer --> Shell
    Shell --> Driver
    Driver --> Server
    Server --> Replica
```

`mongosh` connects to MongoDB using the same underlying database protocols used by MongoDB drivers.

The shell itself is a JavaScript-based environment, which makes it useful for interactive database operations and scripting.

## `mongosh` vs Application Drivers

| Tool | Primary purpose | Typical usage |
|---|---|---|
| `mongosh` | Interactive administration and diagnostics | Debugging, inspection, operations |
| PyMongo | Python application integration | FastAPI, Django, workers |
| Node.js driver | Node.js application integration | Node services |
| MongoDB Compass | GUI inspection and development | Visual exploration |
| `mongodump` | Logical backup | Backup operations |
| `mongorestore` | Logical restore | Recovery |
| `mongoimport` | Import structured data | JSON/CSV ingestion |
| `mongoexport` | Export documents | Data extraction |

Do not use `mongosh` as the database access layer of a Python application.

Application code should use an appropriate MongoDB driver.

## Installing and Verifying `mongosh`

After installing MongoDB Shell, verify the installation:

```bash
mongosh --version
```

Display command-line help:

```bash
mongosh --help
```

Check available options:

```bash
mongosh --help
```

A working shell should return its installed version rather than a command-not-found error.

## Connecting to MongoDB

### Local MongoDB

For a local MongoDB instance:

```bash
mongosh
```

Explicit host and port:

```bash
mongosh "mongodb://localhost:27017"
```

Connect directly to a database:

```bash
mongosh "mongodb://localhost:27017/commerce"
```

The database name in the URI determines the default database context after connection.

### MongoDB Atlas

A connection string typically resembles:

```bash
mongosh "mongodb+srv://<username>:<password>@<cluster-host>/<database>"
```

Do not place production credentials directly into shell history or shared scripts.

Prefer a secure credential mechanism and avoid pasting credentials into tickets, terminals shared with others, or source control.

## Connection Options

A MongoDB URI may include options such as:

```text
mongodb://host:27017/database?tls=true
```

Common connection concerns include:

| Concern | Example |
|---|---|
| Host | `localhost` |
| Port | `27017` |
| Database | `commerce` |
| Authentication | Username/password or another supported mechanism |
| TLS | `tls=true` |
| Replica set | `replicaSet=rs0` |
| Read preference | `readPreference=secondaryPreferred` |
| Authentication database | `authSource=admin` |

Use only the options required by the deployment.

## Verify the Connection

After connecting:

```javascript
db.runCommand({ ping: 1 })
```

Expected result:

```javascript
{
  ok: 1
}
```

This is a useful first diagnostic because it separates basic connectivity from application-level query problems.

## Inspect the Current Connection

The shell provides connection-related helpers and methods through the shell environment.

For example:

```javascript
db.getMongo()
```

Use this when investigating which MongoDB connection the current shell is using.

For more detailed topology and deployment information, use:

```javascript
db.hello()
```

## Database Context

Display the current database:

```javascript
db
```

or:

```javascript
db.getName()
```

Switch databases:

```javascript
use commerce
```

The `use` command changes the shell's current database context.

It does not necessarily create the database immediately.

MongoDB creates databases and collections as data is written or explicitly created.

## List Databases

```javascript
show dbs
```

or:

```javascript
db.getMongo().getDBNames()
```

A database may not appear in the database list if it does not contain persisted data.

## Database Statistics

For database-level statistics:

```javascript
db.stats()
```

Useful information includes:

- Collection count
- Object count
- Data size
- Storage size
- Index size
- Average object size

For a compact result:

```javascript
db.stats({
  scale: 1024 * 1024
})
```

This can make size values easier to interpret as MiB.

## Collections

List collections:

```javascript
show collections
```

Programmatically:

```javascript
db.getCollectionNames()
```

Create a collection explicitly:

```javascript
db.createCollection("orders")
```

However, MongoDB commonly creates collections implicitly when documents are inserted.

## Inspect Collection Information

```javascript
db.orders.getCollectionInfos()
```

Collection statistics:

```javascript
db.orders.stats()
```

Collection statistics are useful for investigating:

- Number of documents
- Data size
- Storage size
- Average document size
- Index size
- Index count

## MongoDB Naming Model

The basic hierarchy is:

```text
MongoDB deployment
    ↓
Database
    ↓
Collection
    ↓
Document
    ↓
Field
```

For example:

```text
commerce
    └── orders
          ├── _id
          ├── customer_id
          ├── status
          └── items
```

## Insert a Document

Insert one document:

```javascript
db.orders.insertOne({
  customer_id: "customer-1001",
  status: "pending",
  total: 1499,
  created_at: new Date()
})
```

MongoDB generates an `_id` if one is not supplied.

The result contains information about the inserted document.

## Insert Multiple Documents

```javascript
db.orders.insertMany([
  {
    customer_id: "customer-1001",
    status: "pending",
    total: 1499,
    created_at: new Date()
  },
  {
    customer_id: "customer-1002",
    status: "confirmed",
    total: 2999,
    created_at: new Date()
  }
])
```

Use `insertMany()` when multiple independent documents need to be inserted.

For large operational workloads, consider batching and appropriate write settings rather than inserting an unbounded number of documents in one operation.

## Inspect Documents

Find all matching documents:

```javascript
db.orders.find({
  status: "pending"
})
```

Find one document:

```javascript
db.orders.findOne({
  status: "pending"
})
```

For a readable shell representation:

```javascript
db.orders.findOne({
  status: "pending"
})
```

The shell's display formatting is generally sufficient for interactive inspection.

## Query Filters

Equality:

```javascript
db.orders.find({
  status: "confirmed"
})
```

Comparison:

```javascript
db.orders.find({
  total: {
    $gte: 1000
  }
})
```

Multiple predicates:

```javascript
db.orders.find({
  status: "confirmed",
  total: {
    $gte: 1000
  }
})
```

MongoDB treats these fields as an implicit logical AND.

## Comparison Operators

Common operators:

| Operator | Meaning |
|---|---|
| `$eq` | Equal |
| `$ne` | Not equal |
| `$gt` | Greater than |
| `$gte` | Greater than or equal |
| `$lt` | Less than |
| `$lte` | Less than or equal |
| `$in` | Matches any value in an array |
| `$nin` | Matches none of the values |

Example:

```javascript
db.orders.find({
  total: {
    $gte: 1000,
    $lt: 5000
  }
})
```

## Logical Operators

Explicit AND:

```javascript
db.orders.find({
  $and: [
    { status: "confirmed" },
    { total: { $gte: 1000 } }
  ]
})
```

OR:

```javascript
db.orders.find({
  $or: [
    { status: "pending" },
    { status: "processing" }
  ]
})
```

NOT:

```javascript
db.orders.find({
  status: {
    $not: {
      $eq: "cancelled"
    }
  }
})
```

NOR:

```javascript
db.orders.find({
  $nor: [
    { status: "cancelled" },
    { status: "failed" }
  ]
})
```

Use implicit AND where possible because it is usually simpler.

## Array Queries

Suppose a document contains:

```javascript
{
  items: [
    {
      product_id: "product-1",
      quantity: 3
    }
  ]
}
```

Find documents containing an item with a specific product:

```javascript
db.orders.find({
  "items.product_id": "product-1"
})
```

Use `$elemMatch` when multiple conditions must apply to the same array element:

```javascript
db.orders.find({
  items: {
    $elemMatch: {
      product_id: "product-1",
      quantity: {
        $gte: 2
      }
    }
  }
})
```

This distinction is important when querying arrays of documents.

## Embedded Documents

Query nested fields using dot notation:

```javascript
db.customers.find({
  "address.city": "Kolkata"
})
```

Nested field projection:

```javascript
db.customers.find(
  {
    "address.city": "Kolkata"
  },
  {
    name: 1,
    "address.city": 1
  }
)
```

## Projection

Projection controls which fields are returned.

Include fields:

```javascript
db.orders.find(
  {
    status: "confirmed"
  },
  {
    customer_id: 1,
    total: 1
  }
)
```

Exclude fields:

```javascript
db.orders.find(
  {
    status: "confirmed"
  },
  {
    internal_notes: 0
  }
)
```

Avoid mixing inclusion and exclusion projections except for the special handling of `_id`.

## Sorting

Ascending:

```javascript
db.orders.find({
  status: "confirmed"
}).sort({
  created_at: 1
})
```

Descending:

```javascript
db.orders.find({
  status: "confirmed"
}).sort({
  created_at: -1
})
```

For production queries, sorting should be evaluated together with indexes.

An unindexed sort can become expensive for large result sets.

## Limit

```javascript
db.orders.find({
  status: "confirmed"
}).limit(50)
```

Always consider a reasonable limit for operational queries.

Avoid accidentally executing:

```javascript
db.orders.find({}).toArray()
```

against a very large collection.

## Skip

```javascript
db.orders.find({
  status: "confirmed"
})
.sort({
  created_at: -1
})
.skip(100)
.limit(50)
```

`skip()` is convenient for small datasets and administrative inspection, but deep offset pagination can become inefficient for large collections.

For high-scale APIs, prefer range or cursor-based pagination.

## Cursor Behavior

`find()` returns a cursor rather than necessarily materializing the complete result set immediately.

Example:

```javascript
const cursor = db.orders.find({
  status: "confirmed"
})

cursor.next()
```

You can iterate through results:

```javascript
for (const order of db.orders.find({
  status: "confirmed"
}).limit(100)) {
  printjson(order)
}
```

Cursors are important for operational inspection and large-result processing.

## Update One

```javascript
db.orders.updateOne(
  {
    _id: ObjectId("65f000000000000000000001")
  },
  {
    $set: {
      status: "confirmed"
    }
  }
)
```

The `$set` operator changes only the specified field.

## Update Many

```javascript
db.orders.updateMany(
  {
    status: "pending"
  },
  {
    $set: {
      review_required: true
    }
  }
)
```

Be careful with broad filters.

Before running a large update, inspect the matching documents:

```javascript
db.orders.countDocuments({
  status: "pending"
})
```

Then verify the filter:

```javascript
db.orders.find({
  status: "pending"
}).limit(10)
```

## Replace One

`replaceOne()` replaces the complete document except for the immutable `_id`.

```javascript
db.orders.replaceOne(
  {
    _id: "order-1001"
  },
  {
    _id: "order-1001",
    customer_id: "customer-1001",
    status: "confirmed",
    total: 1499
  }
)
```

This differs from `$set`.

A replacement operation can unintentionally remove fields that were not included in the replacement document.

## Upsert

An upsert inserts a document when no matching document exists.

```javascript
db.customers.updateOne(
  {
    external_id: "crm-1001"
  },
  {
    $set: {
      name: "Alice",
      updated_at: new Date()
    }
  },
  {
    upsert: true
  }
)
```

Upserts are useful for synchronization and idempotent writes.

They should generally be backed by appropriate unique indexes when uniqueness is required.

## Delete One

```javascript
db.orders.deleteOne({
  _id: "order-1001"
})
```

Deletion is permanent unless another recovery mechanism exists.

For production systems, consider whether a status transition or soft-delete model is more appropriate.

## Delete Many

```javascript
db.orders.deleteMany({
  status: "test"
})
```

Always inspect the filter before executing destructive operations.

A safer workflow is:

```javascript
db.orders.countDocuments({
  status: "test"
})
```

Then:

```javascript
db.orders.find({
  status: "test"
}).limit(10)
```

Then execute the delete.

## Write Results

MongoDB write operations return structured results.

For example:

```javascript
db.orders.updateOne(
  {
    _id: "order-1001"
  },
  {
    $set: {
      status: "confirmed"
    }
  }
)
```

The result provides information such as:

- Whether the operation was acknowledged
- Number of matched documents
- Number of modified documents
- Upsert information where applicable

Do not assume:

```text
matchedCount == modifiedCount
```

A document can match a filter without requiring a data modification.

## ObjectId

MongoDB commonly uses `ObjectId` for `_id` values.

Create one:

```javascript
ObjectId()
```

Create from a known hexadecimal string:

```javascript
ObjectId("65f000000000000000000001")
```

Query:

```javascript
db.orders.findOne({
  _id: ObjectId("65f000000000000000000001")
})
```

A string and an `ObjectId` are different BSON types.

This query:

```javascript
db.orders.findOne({
  _id: "65f000000000000000000001"
})
```

does not match a document whose `_id` is an `ObjectId`.

## Date Values

Use BSON dates rather than arbitrary date strings when date queries are required.

Current date:

```javascript
new Date()
```

Example:

```javascript
db.orders.find({
  created_at: {
    $gte: ISODate("2026-01-01T00:00:00Z")
  }
})
```

Date types allow proper date comparison and indexing.

## Inspect Indexes

List indexes:

```javascript
db.orders.getIndexes()
```

Create a single-field index:

```javascript
db.orders.createIndex({
  customer_id: 1
})
```

Create a compound index:

```javascript
db.orders.createIndex({
  customer_id: 1,
  created_at: -1
})
```

Create a unique index:

```javascript
db.customers.createIndex(
  {
    email: 1
  },
  {
    unique: true
  }
)
```

## Index Naming

You can explicitly name an index:

```javascript
db.orders.createIndex(
  {
    customer_id: 1,
    created_at: -1
  },
  {
    name: "customer_created_at_desc"
  }
)
```

Explicit names can make operational inspection easier.

## Drop an Index

List indexes first:

```javascript
db.orders.getIndexes()
```

Then drop a specific index:

```javascript
db.orders.dropIndex(
  "customer_created_at_desc"
)
```

Do not remove indexes from production without understanding their workload impact.

An index can support:

- Application queries
- Sort operations
- Unique constraints
- TTL behavior
- Operational jobs

## Explain Plans

`explain()` is one of the most important MongoDB diagnostic tools.

Basic example:

```javascript
db.orders.find({
  customer_id: "customer-1001"
}).explain()
```

Execution statistics:

```javascript
db.orders.find({
  customer_id: "customer-1001"
}).explain("executionStats")
```

Query planning information:

```javascript
db.orders.find({
  customer_id: "customer-1001"
}).explain("queryPlanner")
```

## Important Explain Metrics

Pay particular attention to:

| Metric | Meaning |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index keys examined |
| `totalDocsExamined` | Documents examined |
| Execution time | Query execution duration |
| `COLLSCAN` | Collection scan |
| `IXSCAN` | Index scan |
| `FETCH` | Document fetch |
| `SORT` | Sorting stage |

A query returning 10 documents after examining hundreds of thousands of documents deserves investigation.

## Example Query Diagnosis

Suppose:

```javascript
db.orders.find({
  customer_id: "customer-1001",
  status: "confirmed"
}).sort({
  created_at: -1
}).limit(50)
```

Run:

```javascript
db.orders.find({
  customer_id: "customer-1001",
  status: "confirmed"
}).sort({
  created_at: -1
}).limit(50).explain("executionStats")
```

A potential supporting index is:

```javascript
db.orders.createIndex({
  customer_id: 1,
  status: 1,
  created_at: -1
})
```

Then rerun `explain("executionStats")` and compare the execution statistics.

The objective is not merely to see `IXSCAN`.

The objective is to determine whether the query examines an efficient amount of data for its workload.

## Aggregation Basics

MongoDB aggregation uses a pipeline.

Example:

```javascript
db.orders.aggregate([
  {
    $match: {
      status: "confirmed"
    }
  },
  {
    $group: {
      _id: "$customer_id",
      total_orders: {
        $sum: 1
      },
      revenue: {
        $sum: "$total"
      }
    }
  },
  {
    $sort: {
      revenue: -1
    }
  }
])
```

The data flows through:

```text
Documents
   ↓
$match
   ↓
$group
   ↓
$sort
   ↓
Results
```

## Common Aggregation Stages

| Stage | Purpose |
|---|---|
| `$match` | Filter documents |
| `$project` | Select/reshape fields |
| `$set` | Add or modify fields |
| `$unset` | Remove fields |
| `$group` | Group and aggregate |
| `$sort` | Sort results |
| `$limit` | Limit results |
| `$skip` | Skip results |
| `$unwind` | Expand arrays |
| `$lookup` | Join collections |
| `$facet` | Run multiple pipelines |
| `$count` | Count documents |
| `$bucket` | Group values into ranges |
| `$unionWith` | Combine collections |
| `$merge` | Write pipeline results into a collection |
| `$out` | Replace a collection with pipeline output |

Place selective `$match` stages early when appropriate so later stages process fewer documents.

## Aggregation Explain

Aggregation performance can be investigated with:

```javascript
db.orders.explain("executionStats").aggregate([
  {
    $match: {
      status: "confirmed"
    }
  },
  {
    $group: {
      _id: "$customer_id",
      revenue: {
        $sum: "$total"
      }
    }
  }
])
```

For large aggregations, investigate:

- Number of documents entering the pipeline
- Index usage
- Memory consumption
- Blocking stages
- `$sort`
- `$group`
- `$lookup`
- Pipeline ordering

## Collection Statistics

Inspect collection statistics:

```javascript
db.orders.stats()
```

Useful fields include:

```text
count
size
storageSize
totalIndexSize
avgObjSize
nindexes
```

These values help establish collection growth and storage characteristics.

## Index Statistics

MongoDB can expose index usage statistics:

```javascript
db.orders.aggregate([
  {
    $indexStats: {}
  }
])
```

This can help identify indexes that appear unused during the observed measurement period.

Do not automatically drop an apparently unused index.

Consider:

- Measurement window
- Batch jobs
- Rare production workflows
- Administrative queries
- Failover behavior
- Unique constraints
- TTL requirements

## Server Status

For broad server statistics:

```javascript
db.serverStatus()
```

This can expose substantial operational information.

For example, connection information can be inspected through the returned structure.

For targeted operational diagnostics, prefer extracting the relevant subsection instead of dumping the entire result repeatedly.

## Current Operations

Inspect currently running operations where permitted:

```javascript
db.currentOp()
```

Use this carefully in production.

Investigating current operations is useful when diagnosing:

- Long-running operations
- Blocked workloads
- Unexpected scans
- Operational contention

Do not repeatedly poll expensive diagnostic commands during an incident without considering their impact.

## Replica Set Inspection

Inspect replica-set topology:

```javascript
rs.status()
```

This is one of the primary operational commands for replica-set health.

Inspect configuration:

```javascript
rs.conf()
```

Basic deployment information:

```javascript
db.hello()
```

Important things to investigate include:

- Primary availability
- Secondary state
- Replication lag
- Member health
- Election events
- Reachability

## Replica Set Concepts

A typical topology:

```mermaid
flowchart LR
    Primary[(Primary)]
    Secondary1[(Secondary)]
    Secondary2[(Secondary)]

    Primary --> Secondary1
    Primary --> Secondary2
```

Applications generally write to the primary under normal replica-set operation.

Secondaries replicate the primary's operations and can be used for supported read workloads depending on read preference.

## Replica-Set Health Checklist

During an incident inspect:

```javascript
rs.status()
```

Then evaluate:

- Which member is primary?
- Are secondaries healthy?
- Is any member in `RECOVERING` or another unexpected state?
- Is replication lag increasing?
- Are members reachable?
- Has an election recently occurred?

Avoid changing replica-set configuration during an incident without understanding the topology and consequences.

## Sharded Cluster Inspection

A sharded deployment typically contains:

```text
Application
    ↓
mongos
    ↓
 ┌──┴──────────┐
Shard 1      Shard 2
```

Connect through `mongos` for normal sharded-cluster application operations.

Inspect sharding information with supported administrative commands, for example:

```javascript
sh.status()
```

The exact output depends on the MongoDB deployment and version.

Important operational concepts include:

- Shards
- Config servers
- `mongos`
- Shard keys
- Balancing
- Query targeting

## Authentication

Connect with credentials:

```bash
mongosh \
  "mongodb://username:password@localhost:27017/admin"
```

A safer operational approach is to avoid placing passwords directly in shell commands because command-line arguments can be exposed through shell history or process inspection.

Authentication database matters.

For example:

```text
Application database: commerce
Authentication database: admin
```

is different from:

```text
Authentication database: commerce
```

depending on how the MongoDB user was created.

## Verify Current User

The exact command depends on the deployment and authentication configuration, but a useful diagnostic is:

```javascript
db.runCommand({
  connectionStatus: 1
})
```

This can provide information about authenticated users and roles associated with the connection.

## Role Inspection

MongoDB provides built-in and custom roles.

For administrative inspection:

```javascript
use admin

db.getUsers()
```

Inspect roles:

```javascript
db.getRoles({
  showBuiltinRoles: true
})
```

Avoid using administrative accounts for routine application access.

## Least Privilege

An application user should normally have only the permissions it needs.

For example:

```text
Order API
    ↓
orders database
    ↓
read/write required collections
```

rather than:

```text
Application
    ↓
cluster-wide administrative privileges
```

Use separate credentials for:

- Application services
- Reporting
- Operations
- Migration jobs
- CI/CD automation

## MongoDB Shell and Secrets

Avoid:

```bash
mongosh "mongodb://admin:SuperSecretPassword@host/admin"
```

when the command may be captured in shell history or process listings.

Prefer secure authentication mechanisms supported by the environment and MongoDB deployment.

At minimum:

- Do not commit credentials.
- Do not place credentials in scripts.
- Do not paste secrets into documentation.
- Avoid printing connection strings in logs.
- Rotate credentials when exposure is suspected.

## TLS Verification

For TLS-enabled deployments:

```bash
mongosh \
  "mongodb://mongo.example.internal:27017/?tls=true"
```

For production deployments, certificate validation should be configured according to the organization's PKI and MongoDB deployment.

Avoid disabling certificate validation simply to make a connection work.

## Import and Export Tooling

`mongosh` itself is not the primary tool for bulk JSON/CSV import or logical backup.

Use:

```text
mongoimport
mongoexport
mongodump
mongorestore
```

Examples:

```bash
mongoimport \
  --uri "$MONGODB_URI" \
  --collection orders \
  --file orders.json \
  --jsonArray
```

Export:

```bash
mongoexport \
  --uri "$MONGODB_URI" \
  --collection orders \
  --out orders.json
```

Backup:

```bash
mongodump \
  --uri "$MONGODB_URI" \
  --out ./backup
```

Restore:

```bash
mongorestore \
  --uri "$MONGODB_URI" \
  ./backup
```

For production backup and recovery, use the organization's approved backup strategy rather than treating ad-hoc shell commands as a complete disaster-recovery solution.

## Output Formatting

For large shell results, avoid printing unnecessary fields.

Use projection:

```javascript
db.orders.find(
  {
    status: "pending"
  },
  {
    _id: 1,
    customer_id: 1,
    status: 1
  }
).limit(20)
```

For diagnostic work, smaller outputs are easier to inspect and less likely to overwhelm the terminal.

## Shell Variables

`mongosh` supports JavaScript variables.

```javascript
const customerId = "customer-1001"

db.orders.find({
  customer_id: customerId
})
```

This is useful for repeated investigative queries.

Example:

```javascript
const orderId = "order-1001"

db.orders.findOne({
  _id: orderId
})
```

Variables also make repeatable operational scripts easier to construct.

## Reusable Shell Scripts

For repeatable operations, use a JavaScript file.

Example:

```javascript
const database = db.getSiblingDB("commerce")

const result = database.orders.updateMany(
  {
    status: "pending",
    review_required: {
      $exists: false
    }
  },
  {
    $set: {
      review_required: true
    }
  }
)

printjson(result)
```

Execute:

```bash
mongosh "$MONGODB_URI" ./update-orders.js
```

For production operations, scripts should be:

- Reviewed
- Version controlled
- Idempotent where possible
- Explicit about environment
- Safe against broad filters
- Tested before execution

## Idempotent Operational Scripts

Prefer:

```javascript
db.orders.updateMany(
  {
    status: "pending",
    review_required: {
      $ne: true
    }
  },
  {
    $set: {
      review_required: true
    }
  }
)
```

over scripts that blindly perform the same mutation repeatedly.

Idempotency makes retries and operational recovery safer.

## Dry-Run Pattern

Before a destructive operation:

```javascript
const filter = {
  status: "test"
}

print(`Matched: ${db.orders.countDocuments(filter)}`)

db.orders.find(
  filter,
  {
    _id: 1
  }
).limit(10)
```

Only after verifying the result should the actual mutation be executed.

This pattern is especially important for:

- `deleteMany()`
- `updateMany()`
- Large migrations
- Index changes
- Administrative scripts

## Production Safety Rules

Before executing a mutation in production:

1. Confirm the environment.
2. Confirm the database.
3. Confirm the collection.
4. Inspect the filter.
5. Count matching documents.
6. Inspect a sample.
7. Confirm the intended write.
8. Verify backup/recovery requirements.
9. Execute with the minimum required privileges.
10. Verify the result.

A simple environment check can be useful:

```javascript
print(`Database: ${db.getName()}`)
```

## Query Performance Workflow

When a query is slow:

```text
Slow operation
      ↓
Capture exact query
      ↓
Run explain("executionStats")
      ↓
Inspect query plan
      ↓
Check indexes
      ↓
Check documents/keys examined
      ↓
Optimize query or index
      ↓
Re-run explain
      ↓
Monitor production behavior
```

Example:

```javascript
db.orders.find({
  customer_id: "customer-1001",
  status: "confirmed"
}).sort({
  created_at: -1
}).limit(50).explain("executionStats")
```

Do not assume that adding an index automatically solves the problem.

## Common `mongosh` Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Wrong database selected | `use` changes context | Check `db.getName()` |
| Wrong `_id` type | String vs `ObjectId` confusion | Inspect the stored BSON type |
| Broad `updateMany()` | Filter was not validated | Count and sample first |
| Broad `deleteMany()` | Destructive command executed too quickly | Dry-run the filter |
| Missing projection | Too much data printed | Select required fields |
| Deep `skip()` pagination | Convenient offset model | Use range/cursor pagination |
| Ignoring indexes | Query works on small data | Run `explain()` |
| Creating duplicate indexes | Index lifecycle not checked | Run `getIndexes()` first |
| Running admin commands without authorization | Privilege assumptions | Use appropriate roles |
| Storing credentials in scripts | Convenience | Use secret management |
| Disabling TLS validation | Connection troubleshooting | Fix certificate configuration |
| Using shell for application access | Tooling confusion | Use the appropriate driver |

## Operational Pitfalls

### Running a Broad Update

Dangerous:

```javascript
db.orders.updateMany(
  {},
  {
    $set: {
      status: "processed"
    }
  }
)
```

The empty filter matches all documents.

For production operations, explicitly define and validate the target set.

### Running a Broad Delete

Dangerous:

```javascript
db.orders.deleteMany({})
```

This can delete the entire collection.

Do not use destructive commands casually, especially against production databases.

### Ignoring Environment Context

Before running commands:

```javascript
db.getName()
```

Confirm:

```text
Development?
Staging?
Production?
```

A valid MongoDB command against the wrong environment is still an operational failure.

## MongoDB Shell in Docker

If `mongosh` is available in a MongoDB container:

```bash
docker exec -it mongodb mongosh
```

Connect to a specific database:

```bash
docker exec -it mongodb mongosh \
  "mongodb://localhost:27017/commerce"
```

The exact command depends on the container name and network configuration.

When the application runs in another Docker container, `localhost` refers to the current container, not the MongoDB container.

For Docker Compose, the MongoDB service name is commonly used as the hostname:

```text
mongodb://mongodb:27017/commerce
```

## MongoDB Shell in Kubernetes

For a Kubernetes deployment, shell access may involve:

```bash
kubectl exec -it <pod-name> -- mongosh
```

If the MongoDB client is not installed inside the target container, use an approved administrative/debug container instead.

Avoid modifying production containers merely to install troubleshooting tools unless that is part of the operational process.

## Local Development Workflow

A practical local workflow is:

```text
Start MongoDB
    ↓
Connect with mongosh
    ↓
Verify ping
    ↓
Inspect database
    ↓
Create test data
    ↓
Run application queries
    ↓
Inspect indexes
    ↓
Run explain()
    ↓
Validate behavior
```

Example:

```bash
mongosh "mongodb://localhost:27017/commerce"
```

Then:

```javascript
db.runCommand({ ping: 1 })

show collections

db.orders.find().limit(5)

db.orders.getIndexes()
```

## Debugging an Application Query

When a Python, FastAPI, or Django application reports a slow query:

```text
Application
    ↓
Capture query shape
    ↓
mongosh
    ↓
Reproduce query
    ↓
explain("executionStats")
    ↓
Inspect index
    ↓
Compare with application metrics
```

This separates:

- Application latency
- Network latency
- MongoDB execution time
- Serialization overhead
- Connection pool waiting

## CLI Tool Selection

| Task | Preferred tool |
|---|---|
| Interactive query | `mongosh` |
| Query plan analysis | `mongosh` + `explain()` |
| Database inspection | `mongosh` |
| GUI document inspection | Compass |
| JSON import | `mongoimport` |
| CSV import | `mongoimport` |
| JSON export | `mongoexport` |
| Logical backup | `mongodump` |
| Logical restore | `mongorestore` |
| Python application access | PyMongo |
| Automated API access | Application driver |

## Security Checklist

Before using `mongosh` against production:

- [ ] Use an approved connection method.
- [ ] Confirm TLS configuration.
- [ ] Avoid credentials in shell history.
- [ ] Use least-privilege credentials.
- [ ] Confirm the target environment.
- [ ] Avoid copying production documents into insecure locations.
- [ ] Avoid printing secrets or sensitive fields.
- [ ] Use audited operational procedures where required.
- [ ] Prefer read-only access for investigation.
- [ ] Review destructive commands before execution.

## Senior-Level Shell Usage

A senior engineer should use `mongosh` as a diagnostic instrument rather than simply as a CRUD interface.

A production investigation often follows:

```text
Incident
   ↓
Application metrics
   ↓
MongoDB metrics
   ↓
mongosh inspection
   ↓
Query / topology / index analysis
   ↓
Root cause
   ↓
Controlled remediation
   ↓
Post-incident validation
```

For example, if API latency increases:

```text
API latency ↑
     ↓
MongoDB repository latency ↑
     ↓
Query latency ↑
     ↓
mongosh explain()
     ↓
COLLSCAN / excessive docs examined
     ↓
Index/query mismatch
     ↓
Correct index
     ↓
Re-run explain()
     ↓
Monitor production
```

The shell is most valuable when it is combined with application observability and database metrics.

## Interview Considerations

### What is `mongosh`?

`mongosh` is MongoDB's modern interactive shell used for querying, administration, diagnostics, and scripting against MongoDB deployments.

### Should application code use `mongosh`?

No.

Application code should use a supported MongoDB driver such as PyMongo.

### How do you investigate a slow MongoDB query?

Start with the exact query shape and run:

```javascript
db.collection.find(
  filter
).explain("executionStats")
```

Then inspect:

- Winning plan
- `COLLSCAN`
- `IXSCAN`
- `totalKeysExamined`
- `totalDocsExamined`
- `nReturned`
- Execution time
- Index suitability

### How do you safely execute a production update?

Use a staged workflow:

```text
Confirm environment
    ↓
Build filter
    ↓
Count matches
    ↓
Inspect sample
    ↓
Review operation
    ↓
Execute
    ↓
Verify result
```

### Why is `ObjectId` important in `mongosh`?

MongoDB distinguishes BSON types. A string containing an ObjectId's hexadecimal representation is not the same BSON value as an actual `ObjectId`.

### Why should `mongosh` scripts be idempotent?

Operational scripts may need to be retried after partial execution or uncertain outcomes. Idempotent operations reduce the risk of duplicate or inconsistent mutations.

## Key Takeaways

- **`mongosh` is primarily an operational, diagnostic, and administrative interface; application code should use an appropriate MongoDB driver.**
- **Always verify database context, environment, filters, and BSON types before executing production operations.**
- **Use `explain("executionStats")`, index inspection, and targeted statistics to diagnose query and performance problems rather than guessing.**
- **Treat destructive or broad shell operations as production changes: validate first, minimize privileges, make scripts idempotent where possible, and verify the result.**
- **Senior-level `mongosh` usage combines shell commands with application metrics, MongoDB topology, indexes, security controls, and operational procedures.**