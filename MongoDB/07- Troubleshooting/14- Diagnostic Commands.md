# 14- Diagnostic Commands

## Overview

MongoDB troubleshooting depends on collecting evidence from the database, replica-set topology, queries, indexes, connections, storage, and application environment.

Commands should be used to answer a specific diagnostic question rather than executed as an arbitrary checklist.

A useful production workflow is:

```text
Symptom
↓
Identify affected layer
↓
Collect topology and health information
↓
Inspect workload
↓
Inspect query/index behavior
↓
Inspect resource pressure
↓
Correlate with application metrics
↓
Form root-cause hypothesis
↓
Validate hypothesis
```

The most important diagnostic principle is to distinguish:

```text
Database is unhealthy
```

from:

```text
Database is healthy but the application is using it inefficiently
```

## Diagnostic Command Categories

| Area | Primary tools | Typical questions |
|---|---|---|
| Connectivity | `mongosh`, `db.hello()` | Can the client reach MongoDB? |
| Topology | `rs.status()`, `rs.conf()` | Is the replica set healthy? |
| Server health | `serverStatus()` | Is MongoDB resource constrained? |
| Database health | `db.stats()` | How large is the database? |
| Collection health | `collStats` | Which collections consume resources? |
| Indexes | `getIndexes()`, `$indexStats` | Are indexes correct and being used? |
| Queries | `explain()` | Why is a query slow? |
| Operations | `currentOp()` | What is running now? |
| Replication | `rs.printSecondaryReplicationInfo()` | Are secondaries lagging? |
| Connections | `serverStatus()` | Is the connection pool or server saturated? |
| Storage | OS metrics + MongoDB metrics | Is disk I/O the bottleneck? |
| Users | `usersInfo()` | Which privileges exist? |
| Logs | MongoDB logs | What happened around the incident? |
| Backup | `mongodump`, `mongorestore` | Can recovery artifacts be inspected or tested? |

## Connecting with `mongosh`

### Local MongoDB

```bash
mongosh
```

Specify a database:

```bash
mongosh "mongodb://localhost:27017/appdb"
```

### Authenticated Connection

```bash
mongosh \
  "mongodb://app_user:${MONGODB_PASSWORD}@mongodb.internal:27017/appdb?authSource=admin"
```

For SRV connection strings:

```bash
mongosh "$MONGODB_URI"
```

### TLS Connection

```bash
mongosh \
  "mongodb://mongodb.internal:27017/appdb" \
  --tls \
  --tlsCAFile /etc/mongodb/ca.pem
```

### Production Considerations

Avoid placing passwords directly in shell history.

Prefer:

```bash
mongosh "$MONGODB_URI"
```

with the URI supplied securely through the environment or approved secret-management mechanism.

## Basic Connectivity Diagnostics

### Check Server Identity

```javascript
db.hello()
```

Useful fields include:

```text
isWritablePrimary
secondary
primary
hosts
me
setName
```

This is one of the first commands to run when diagnosing topology or routing problems.

### Check Server Version

```javascript
db.version()
```

For deployment compatibility, also inspect build information:

```javascript
db.adminCommand({ buildInfo: 1 })
```

### Ping the Server

```javascript
db.adminCommand({ ping: 1 })
```

A successful ping proves that the server accepted the command. It does not prove that the application workload is healthy.

## Database Inspection

### List Databases

```javascript
show dbs
```

Or:

```javascript
db.adminCommand({ listDatabases: 1 })
```

### Select a Database

```javascript
use appdb
```

### Show Current Database

```javascript
db.getName()
```

### List Collections

```javascript
show collections
```

Or:

```javascript
db.getCollectionNames()
```

### Inspect Collection Metadata

```javascript
db.getCollectionInfos()
```

Inspect one collection:

```javascript
db.getCollectionInfos({
    name: "orders"
})
```

This is particularly useful when investigating:

- Validators
- Validation level
- Validation action
- Collection options
- Capped collections
- Collection configuration

## Database Statistics

Run:

```javascript
db.stats()
```

For more readable output:

```javascript
db.stats(1024 * 1024)
```

This expresses sizes in approximately MiB.

Useful fields include:

| Field | Meaning |
|---|---|
| `collections` | Number of collections |
| `objects` | Approximate document count |
| `dataSize` | Logical data size |
| `storageSize` | Storage allocated |
| `indexes` | Number of indexes |
| `indexSize` | Total index size |
| `avgObjSize` | Average document size |

### Production Interpretation

A growing `dataSize` is not automatically a problem.

Investigate the relationship between:

```text
Logical data
+
Storage allocation
+
Index size
+
Available storage
+
Working set
```

## Collection Statistics

Run:

```javascript
db.orders.stats()
```

Or:

```javascript
db.runCommand({
    collStats: "orders"
})
```

Useful information includes:

- Document count
- Logical size
- Storage size
- Average document size
- Index count
- Index sizes

### Why Collection Statistics Matter

If one collection suddenly becomes much larger, investigate:

- Data-retention behavior
- Unbounded arrays
- Duplicate records
- Missing TTL policies
- Import jobs
- Unexpected application writes

## Collection Size Investigation

A useful diagnostic comparison is:

```text
dataSize
storageSize
totalIndexSize
```

A collection can have relatively small logical data but substantial index/storage overhead.

Do not treat storage size as equivalent to the number of bytes returned by queries.

## Server Status

One of the most important diagnostic commands is:

```javascript
db.serverStatus()
```

For a specific subsystem:

```javascript
db.serverStatus().connections
```

```javascript
db.serverStatus().opcounters
```

```javascript
db.serverStatus().network
```

```javascript
db.serverStatus().mem
```

```javascript
db.serverStatus().wiredTiger
```

The exact fields available can vary by MongoDB version and deployment.

## Connection Diagnostics

Inspect connection information:

```javascript
db.serverStatus().connections
```

Typical fields include:

```text
current
available
totalCreated
```

### Interpretation

```text
current ↑
totalCreated ↑ rapidly
```

may indicate connection churn.

A high `current` value alone does not prove that the connection pool is exhausted.

Correlate it with:

- Application worker count
- Pool configuration
- Request latency
- MongoDB operation latency
- Connection creation rate

## Network Diagnostics

Inspect:

```javascript
db.serverStatus().network
```

Useful information can include:

- Bytes in
- Bytes out
- Request counts
- Connection metrics

A sudden increase in network traffic may indicate:

- Large projections
- Large documents
- Increased query volume
- Application regressions
- Missing pagination

## Operation Counters

Inspect:

```javascript
db.serverStatus().opcounters
```

This provides workload-level information such as:

```text
insert
query
update
delete
getmore
command
```

Compare operation rates before and during an incident.

For example:

```text
Normal:
queries = 20k/min

Incident:
queries = 150k/min
```

This strongly suggests a workload change even if MongoDB configuration has not changed.

## Current Operations

Inspect active operations:

```javascript
db.currentOp()
```

On modern deployments, use the appropriate privileges and filtering carefully.

For example:

```javascript
db.currentOp({
    active: true
})
```

Filter by operation namespace:

```javascript
db.currentOp({
    active: true,
    ns: "appdb.orders"
})
```

### What to Look For

- Long-running operations
- Large scans
- Blocked operations
- Long-running transactions
- Unexpected clients
- Large aggregations
- Operations running during a performance incident

### Production Warning

`currentOp()` can itself return a large amount of information.

Use targeted filters during incidents instead of repeatedly dumping all active operations.

## Query Diagnostics with `explain()`

`explain()` is the primary tool for understanding query execution.

Example:

```javascript
db.orders.find({
    customer_id: "CUST-1001",
    status: "pending"
}).explain("executionStats")
```

### Explain Modes

```javascript
.explain("queryPlanner")
```

```javascript
.explain("executionStats")
```

```javascript
.explain("allPlansExecution")
```

Use `executionStats` when diagnosing actual query performance.

Use `allPlansExecution` selectively because it can be more expensive and verbose.

## Reading an Explain Plan

Important fields include:

| Field | Why it matters |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index entries examined |
| `totalDocsExamined` | Documents examined |
| `executionTimeMillis` | Observed execution time |
| `winningPlan` | Selected execution plan |
| `rejectedPlans` | Alternative plans considered |

### Healthy Query Pattern

A selective indexed query might resemble:

```text
nReturned: 20
totalKeysExamined: 20
totalDocsExamined: 20
```

### Suspicious Query Pattern

```text
nReturned: 20
totalKeysExamined: 900000
totalDocsExamined: 900000
```

This indicates substantially more work than the result size suggests.

It does not automatically prove that an index is missing, but it is a strong signal for further investigation.

## Detecting Collection Scans

Look for:

```text
COLLSCAN
```

A collection scan means MongoDB is scanning collection records rather than using an appropriate index for the query.

Example:

```javascript
db.orders.find({
    customer_id: "CUST-1001"
}).explain("executionStats")
```

If the plan contains:

```text
COLLSCAN
```

investigate:

- Whether the query should be indexed
- Query selectivity
- Data volume
- Whether the scan is intentional
- Whether an index would actually improve the workload

A `COLLSCAN` is not automatically a failure. A small collection may be faster to scan than to maintain or traverse an unnecessary index.

## Detecting Index Scans

Look for:

```text
IXSCAN
```

An `IXSCAN` indicates index traversal.

However:

```text
IXSCAN
```

does not automatically mean the query is efficient.

A query can use an index and still examine a very large number of keys.

Always evaluate:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

## Detecting In-Memory Sorts

Look for:

```text
SORT
```

Example query:

```javascript
db.orders.find({
    customer_id: "CUST-1001"
}).sort({
    created_at: -1
}).explain("executionStats")
```

If sorting is performed separately from an efficient index traversal, investigate whether the index can support both filtering and ordering.

For example:

```javascript
db.orders.createIndex({
    customer_id: 1,
    created_at: -1
})
```

## Query and Projection Diagnostics

Inspect only the fields required by the API:

```javascript
db.orders.find(
    { customer_id: "CUST-1001" },
    {
        _id: 1,
        order_number: 1,
        status: 1,
        created_at: 1
    }
)
```

Large documents increase:

- Network traffic
- Deserialization cost
- Application memory
- MongoDB work
- API response size

Projection should therefore be considered part of performance diagnosis.

## Index Inspection

List indexes:

```javascript
db.orders.getIndexes()
```

Inspect index names and definitions:

```javascript
db.orders.getIndexes().forEach(index => printjson(index))
```

### Index Statistics

Use:

```javascript
db.orders.aggregate([
    { $indexStats: {} }
])
```

This can help identify index usage over the statistics collection period.

### Important Limitation

Low or zero usage does not automatically mean an index should be removed.

Consider:

- Rare administrative queries
- Disaster-recovery procedures
- Reporting jobs
- Unique constraints
- TTL behavior
- Application features that are not currently active

## Finding Large Indexes

Database statistics:

```javascript
db.stats()
```

Collection statistics:

```javascript
db.orders.stats()
```

Compare:

```text
dataSize
storageSize
totalIndexSize
```

Large indexes can increase:

- Memory pressure
- Disk usage
- Write cost
- Index build time
- Backup size

## Index Definition Diagnostics

Inspect:

```javascript
db.orders.getIndexes()
```

Verify:

- Field order
- Sort direction
- Unique constraint
- Partial filter
- Sparse configuration
- TTL configuration
- Multikey behavior

A common incident pattern is an index that looks conceptually correct but does not match the real query shape.

## Query Planner Diagnostics

Use:

```javascript
db.orders.find({
    tenant_id: "T100",
    status: "pending"
}).sort({
    created_at: -1
}).explain("executionStats")
```

Inspect:

```text
winningPlan
rejectedPlans
```

When a query becomes slower after an index change, compare the winning plan before and after the change.

## Plan Cache Diagnostics

MongoDB maintains internal query-planning information.

For supported MongoDB versions and deployments, inspect plan-cache information using the appropriate database commands or administrative tooling for the deployed version.

Do not clear plan-cache state as a first troubleshooting action.

First establish:

```text
Query shape
+
Available indexes
+
Winning plan
+
Workload characteristics
```

Plan-cache manipulation should be a deliberate operational action.

## Slow Query Diagnostics

Slow queries can be investigated through:

- Profiler data
- MongoDB logs
- Monitoring platforms
- Application tracing
- `explain()`

If the profiler is already enabled, inspect:

```javascript
db.system.profile.find().sort({
    ts: -1
}).limit(20)
```

### Important Production Consideration

Profiling has overhead.

Do not enable aggressive profiling levels indiscriminately on a busy production cluster.

Use the least intrusive diagnostic mechanism that answers the question.

## Database Profiler

Check profiler configuration:

```javascript
db.getProfilingStatus()
```

Example configuration:

```javascript
db.setProfilingLevel(1, {
    slowms: 100
})
```

The exact threshold should be selected according to workload characteristics.

### Production Guidance

Profiling should be:

- Purpose-driven
- Time-bounded
- Monitored
- Reverted when no longer needed

Do not leave expensive diagnostic settings enabled indefinitely without justification.

## Replica Set Diagnostics

### Replica Set Status

Run:

```javascript
rs.status()
```

This is one of the most important production commands.

Inspect:

- Member state
- Health
- Primary
- Secondary
- Election information
- Optime
- Replication progress
- Member errors

### Replica Set Configuration

Run:

```javascript
rs.conf()
```

Inspect:

- Member hosts
- Priority
- Votes
- Hidden status
- Tags
- Election configuration

### Replica Set State

```javascript
rs.isMaster()
```

For modern MongoDB deployments, prefer:

```javascript
db.hello()
```

`rs.isMaster()` is retained primarily for compatibility with older terminology and clients.

## Replication Lag Diagnostics

On a replica-set member:

```javascript
rs.printSecondaryReplicationInfo()
```

This provides human-readable replication information.

Another useful command is:

```javascript
rs.printReplicationInfo()
```

which provides oplog-related information.

### What to Investigate

```text
Primary write rate
+
Secondary apply rate
+
Storage latency
+
CPU
+
Network
```

Replication lag is a symptom. Identify why the secondary cannot keep up.

## Oplog Diagnostics

Inspect oplog information:

```javascript
rs.printReplicationInfo()
```

The output helps estimate the available oplog history window.

### Why It Matters

The oplog window affects:

- Recovery options
- Secondary recovery
- Change-stream continuity
- Initial sync risk

A high write rate can cause a fixed-size oplog to represent a shorter time window.

## Replica Set Member Information

Use:

```javascript
rs.status().members
```

For focused inspection:

```javascript
rs.status().members.map(member => ({
    name: member.name,
    stateStr: member.stateStr,
    health: member.health,
    syncSourceHost: member.syncSourceHost
}))
```

This is useful when quickly identifying unhealthy members.

## Elections

Inspect replica-set status:

```javascript
rs.status()
```

Look for:

- Election activity
- Primary changes
- Member state transitions
- Network-related failures

Repeated elections can indicate a systemic problem rather than healthy failover behavior.

Potential causes include:

- Network instability
- Resource starvation
- Host failures
- Configuration problems

## Hidden and Priority Members

Inspect:

```javascript
rs.conf()
```

Pay attention to:

```text
priority
hidden
votes
```

These settings influence:

- Election eligibility
- Read routing
- Reporting workloads
- Backup architecture

Do not change them during an incident without understanding their effect on quorum and elections.

## Server Resource Diagnostics

MongoDB diagnostics should be correlated with operating-system metrics.

Useful OS-level commands include:

```bash
top
```

```bash
free -h
```

```bash
df -h
```

```bash
iostat -xz 1
```

```bash
vmstat 1
```

On Linux systems, these help distinguish:

```text
CPU saturation
Memory pressure
Disk saturation
I/O wait
```

from MongoDB-level problems.

## CPU Diagnostics

Use:

```bash
top
```

or:

```bash
htop
```

Correlate CPU utilization with:

```javascript
db.serverStatus().opcounters
```

and slow-query data.

High CPU plus a sudden query-volume increase usually requires workload investigation before infrastructure scaling.

## Memory Diagnostics

Inspect OS memory:

```bash
free -h
```

MongoDB server metrics:

```javascript
db.serverStatus().mem
```

For WiredTiger-related information:

```javascript
db.serverStatus().wiredTiger
```

Interpret memory together with:

- Working-set behavior
- Index size
- Query patterns
- Storage latency
- Container limits

## Disk Diagnostics

Check filesystem capacity:

```bash
df -h
```

Check inode availability:

```bash
df -i
```

Inspect I/O:

```bash
iostat -xz 1
```

Look for:

```text
util
await
read throughput
write throughput
IOPS
```

High disk utilization combined with high latency can explain MongoDB latency even when CPU is normal.

## Kubernetes Diagnostics

When MongoDB or applications run in Kubernetes, correlate database symptoms with cluster state.

Check pods:

```bash
kubectl get pods -A
```

Inspect a MongoDB pod:

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Check logs:

```bash
kubectl logs <pod-name> -n <namespace>
```

Check previous container logs:

```bash
kubectl logs <pod-name> -n <namespace> --previous
```

Inspect resource usage:

```bash
kubectl top pod <pod-name> -n <namespace>
```

Check events:

```bash
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

### Production Questions

When MongoDB runs in Kubernetes, investigate:

- Pod restarts
- OOM kills
- CPU throttling
- Persistent-volume latency
- Node failures
- Pod rescheduling
- Network policies
- DNS
- Resource limits

## Docker Diagnostics

Inspect containers:

```bash
docker ps
```

Inspect MongoDB logs:

```bash
docker logs <container-name>
```

Inspect configuration:

```bash
docker inspect <container-name>
```

Inspect resource usage:

```bash
docker stats <container-name>
```

Check volumes:

```bash
docker volume ls
```

A Docker container being healthy does not guarantee that MongoDB's replica-set or application workload is healthy.

## Authentication Diagnostics

Inspect the current authenticated user:

```javascript
db.runCommand({
    connectionStatus: 1
})
```

This can show:

- Authenticated users
- Authentication mechanisms
- Effective roles

Inspect a specific user when authorized:

```javascript
db.runCommand({
    usersInfo: "app_user",
    showPrivileges: true
})
```

Use the minimum privileges necessary for diagnostics.

## Role Diagnostics

List roles:

```javascript
db.getRoles({
    showBuiltinRoles: true
})
```

Inspect a specific role:

```javascript
db.getRoles({
    role: "readWrite",
    showPrivileges: true
})
```

When diagnosing authorization failures, verify:

```text
User
↓
Authentication database
↓
Assigned roles
↓
Target database
↓
Target collection
↓
Required action
```

## Schema Validation Diagnostics

Inspect collection configuration:

```javascript
db.getCollectionInfos({
    name: "orders"
})
```

Look for:

```text
validator
validationLevel
validationAction
```

### Test a Suspected Invalid Document Safely

Use a controlled test environment rather than attempting production writes merely to test validation.

Schema-validation problems should be diagnosed from:

- Collection metadata
- Application errors
- Rejected write payloads
- Existing document inspection

## Document Inspection

Inspect one document:

```javascript
db.orders.findOne()
```

Inspect a specific document:

```javascript
db.orders.findOne({
    order_id: "ORD-1001"
})
```

Inspect document types:

```javascript
db.orders.aggregate([
    {
        $project: {
            order_id: 1,
            customer_id: 1,
            created_at: 1
        }
    },
    {
        $limit: 10
    }
])
```

For schema drift, inspect multiple representative documents rather than assuming one document represents the collection.

## Finding Unexpected BSON Types

Example:

```javascript
db.orders.find({
    customer_id: {
        $type: "array"
    }
})
```

Other useful checks include:

```javascript
db.orders.find({
    created_at: {
        $type: "string"
    }
})
```

This can expose data inserted with the wrong BSON type.

## Duplicate Detection

For a suspected duplicate business key:

```javascript
db.orders.aggregate([
    {
        $group: {
            _id: "$order_number",
            count: { $sum: 1 }
        }
    },
    {
        $match: {
            count: { $gt: 1 }
        }
    },
    {
        $sort: {
            count: -1
        }
    }
])
```

Use this for diagnosis before deciding whether a unique index is appropriate.

## Finding Null or Missing Fields

Missing field:

```javascript
db.orders.find({
    customer_id: {
        $exists: false
    }
})
```

Explicit `null`:

```javascript
db.orders.find({
    customer_id: null
})
```

These are not always equivalent from an application-data perspective.

## Array Diagnostics

Find unexpectedly large arrays:

```javascript
db.customers.aggregate([
    {
        $project: {
            customer_id: 1,
            event_count: {
                $size: {
                    $ifNull: ["$events", []]
                }
            }
        }
    },
    {
        $sort: {
            event_count: -1
        }
    },
    {
        $limit: 20
    }
])
```

This is useful when investigating:

- Large documents
- Slow updates
- Hot documents
- Unbounded array growth

## Aggregation Diagnostics

Always inspect expensive aggregations with:

```javascript
db.orders.aggregate([
    {
        $match: {
            status: "completed"
        }
    },
    {
        $group: {
            _id: "$customer_id",
            total: { $sum: "$amount" }
        }
    }
], {
    explain: true
})
```

For a production investigation, inspect:

- Documents entering expensive stages
- `$sort`
- `$group`
- `$lookup`
- `$unwind`
- Memory usage
- Index usage
- Result cardinality

## `$lookup` Diagnostics

A `$lookup` can become expensive when the join is performed over large datasets.

Investigate:

```text
Input cardinality
+
Foreign collection size
+
Join-field index
+
Returned array size
```

Verify the foreign collection has an appropriate index for the lookup pattern where applicable.

## `$unwind` Diagnostics

`$unwind` can multiply documents dramatically.

Example:

```text
1 document
+
10,000 array elements
=
10,000 pipeline documents
```

When an aggregation suddenly becomes expensive, inspect array cardinality before and after `$unwind`.

## `$group` Diagnostics

Large `$group` stages can consume substantial resources.

Investigate:

- Number of input documents
- Group cardinality
- Group key distribution
- Memory requirements
- Whether filtering can happen earlier

## Query Count Diagnostics from Python

Instrument application-level database calls.

For example, a FastAPI request should make an expected number of MongoDB operations:

```text
GET /orders
Expected:
1 database query

Observed:
1 + N customer queries
```

This can reveal N+1 problems that MongoDB itself cannot identify as an application-design issue.

## PyMongo Connection Diagnostics

Inspect client configuration in the application rather than changing it interactively during an incident.

Important settings include:

```text
maxPoolSize
minPoolSize
maxConnecting
waitQueueTimeoutMS
serverSelectionTimeoutMS
connectTimeoutMS
socketTimeoutMS
```

Example configuration:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    maxPoolSize=100,
    minPoolSize=10,
    maxConnecting=2,
    waitQueueTimeoutMS=2_000,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)
```

Exact values should be derived from workload and deployment topology rather than copied blindly.

## Python Connectivity Test

A minimal operational health check:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    serverSelectionTimeoutMS=5_000,
)

try:
    client.admin.command("ping")
    print("MongoDB reachable")
finally:
    client.close()
```

For a long-running application, do not create a new `MongoClient` for every request.

Reuse a client for the process lifecycle.

## FastAPI Diagnostics

A FastAPI application should expose application-level health independently from MongoDB internals.

Example:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/health/ready")
def readiness_check() -> dict[str, str]:
    try:
        app.state.mongo.admin.command(
            "ping",
            maxTimeMS=1_000,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB unavailable",
        ) from exc

    return {"status": "ready"}
```

A readiness endpoint should be designed carefully so that health checking itself does not become a significant database workload.

## Django Diagnostics

For Django applications using PyMongo or a MongoDB-specific integration, investigate:

```text
Application configuration
MongoDB URI
Connection lifecycle
Repository/service calls
Query latency
Exception logs
```

Do not assume Django's relational database management commands or ORM behavior directly applies to MongoDB.

## Transaction Diagnostics

When a transaction fails, capture:

- Session lifecycle
- Transaction duration
- Operations performed
- Error labels
- Write concern
- Read concern
- Replica-set state

In PyMongo, transaction exceptions should be classified rather than treated as generic database errors.

Example:

```python
try:
    with client.start_session() as session:
        with session.start_transaction():
            collection_a.insert_one(
                document_a,
                session=session,
            )
            collection_b.update_one(
                {"_id": document_b_id},
                {"$set": {"status": "processed"}},
                session=session,
            )
except Exception as exc:
    logger.exception("MongoDB transaction failed")
    raise
```

During an incident, investigate whether failures correlate with elections, write conflicts, or resource pressure.

## Change Stream Diagnostics

Check the consumer application for:

- Last processed event
- Last persisted resume token
- Consumer process state
- Processing latency
- Downstream errors
- MongoDB connectivity

A change-stream consumer should be observable independently from MongoDB.

Useful metrics include:

```text
events_received
events_processed
events_failed
consumer_lag
last_resume_token_timestamp
```

## Backup and Recovery Diagnostics

Verify backup availability through the appropriate backup system.

For logical backups, inspect available artifacts before attempting restoration.

Example:

```bash
mongodump \
  --uri="$MONGODB_URI" \
  --archive=backup.archive \
  --gzip
```

Validate an archive in an isolated environment through the documented restore process:

```bash
mongorestore \
  --uri="$RECOVERY_MONGODB_URI" \
  --archive=backup.archive \
  --gzip
```

Do not restore directly over production merely to test whether a backup works.

## Import and Export Diagnostics

Inspect import source files before importing.

For JSON:

```bash
mongoimport \
  --uri="$MONGODB_URI" \
  --db=appdb \
  --collection=orders \
  --file=orders.json
```

For JSON Lines:

```bash
mongoimport \
  --uri="$MONGODB_URI" \
  --db=appdb \
  --collection=orders \
  --file=orders.jsonl
```

For CSV:

```bash
mongoimport \
  --uri="$MONGODB_URI" \
  --db=appdb \
  --collection=orders \
  --type=csv \
  --headerline \
  --file=orders.csv
```

When diagnosing import failures, inspect:

- Encoding
- Header names
- JSON structure
- BSON types
- Duplicate keys
- Schema validation
- Authentication
- Network connectivity
- Index overhead

## Log Diagnostics

MongoDB logs should be correlated with:

```text
Application logs
+
Infrastructure logs
+
Deployment events
+
Monitoring metrics
```

Search for:

- Connection errors
- Authentication errors
- Election events
- Replication warnings
- Storage errors
- Slow operations
- TLS errors
- Shutdown/restart events

Avoid treating logs as the only source of truth. Metrics and database state provide important context.

## Diagnostic Workflow for Slow APIs

Use this sequence:

```text
API latency increased
        ↓
Check application latency breakdown
        ↓
Check MongoDB operation latency
        ↓
Check connection-pool wait
        ↓
Identify slow query
        ↓
Run explain("executionStats")
        ↓
Inspect index/query shape
        ↓
Check CPU / memory / disk
        ↓
Validate optimization
```

Example query:

```javascript
db.orders.find({
    tenant_id: "T100",
    status: "pending"
}).sort({
    created_at: -1
}).limit(100).explain("executionStats")
```

## Diagnostic Workflow for Connection Failures

```text
Connection failure
        ↓
DNS resolution
        ↓
TCP connectivity
        ↓
TLS handshake
        ↓
MongoDB server selection
        ↓
Authentication
        ↓
Authorization
        ↓
Application connection pool
```

Each layer has different failure modes.

Do not jump directly to MongoDB authentication when DNS resolution itself is failing.

## Diagnostic Workflow for Replica-Set Problems

```text
Replica-set symptom
        ↓
db.hello()
        ↓
rs.status()
        ↓
rs.conf()
        ↓
Check elections
        ↓
Check replication lag
        ↓
Check network
        ↓
Check CPU / memory / disk
        ↓
Check oplog window
```

## Diagnostic Workflow for High CPU

```text
High CPU
↓
Check operation rate
↓
Check slow queries
↓
Run explain()
↓
Check aggregation workloads
↓
Check indexes
↓
Check application traffic
↓
Check worker concurrency
↓
Determine query vs workload vs infrastructure cause
```

## Diagnostic Workflow for High Disk Usage

```text
High disk usage
↓
df -h
↓
Database size
↓
Collection size
↓
Index size
↓
Oplog / logs / temporary data
↓
Data-growth trend
↓
Capacity planning
```

Do not delete MongoDB data files manually to recover disk space.

## Diagnostic Workflow for Connection Pool Exhaustion

```text
Pool timeout
↓
Application replicas
↓
Worker processes
↓
MongoClient lifecycle
↓
Pool configuration
↓
MongoDB connection count
↓
MongoDB operation latency
↓
Long-running queries / transactions
↓
Root cause
```

A pool timeout can be caused by slow queries rather than an undersized pool.

## Production Diagnostic Command Reference

| Diagnostic question | Command |
|---|---|
| Is MongoDB reachable? | `db.adminCommand({ ping: 1 })` |
| Which node am I connected to? | `db.hello()` |
| What version is running? | `db.version()` |
| What databases exist? | `show dbs` |
| What collections exist? | `show collections` |
| How large is the database? | `db.stats()` |
| How large is a collection? | `db.collection.stats()` |
| What indexes exist? | `db.collection.getIndexes()` |
| Which indexes are being used? | `$indexStats` |
| Why is a query slow? | `explain("executionStats")` |
| What is running now? | `db.currentOp()` |
| Is the replica set healthy? | `rs.status()` |
| What is the replica-set configuration? | `rs.conf()` |
| What is the oplog window? | `rs.printReplicationInfo()` |
| Are secondaries lagging? | `rs.printSecondaryReplicationInfo()` |
| What are server connections? | `db.serverStatus().connections` |
| What is the operation rate? | `db.serverStatus().opcounters` |
| What is network activity? | `db.serverStatus().network` |
| What is memory information? | `db.serverStatus().mem` |
| What authentication context exists? | `db.runCommand({ connectionStatus: 1 })` |
| What collection validator exists? | `db.getCollectionInfos()` |
| What users exist? | `db.runCommand({ usersInfo: ... })` |

## Command Selection by Symptom

| Symptom | Start with | Then investigate |
|---|---|---|
| Connection timeout | `db.hello()` | DNS, TLS, pool, topology |
| Authentication error | `connectionStatus` | User, roles, `authSource` |
| Slow query | `explain()` | Indexes, data volume |
| High CPU | `serverStatus()` | Slow queries, aggregations |
| High disk I/O | `iostat` | Collection/index growth |
| High memory | `serverStatus()` | Working set, indexes |
| Primary unavailable | `rs.status()` | Elections, majority |
| Replica lag | `rs.status()` | CPU, disk, network |
| Pool exhaustion | `connections` | Application pool and latency |
| Data inconsistency | `find()`, aggregation | Writes, retries, migrations |
| Backup problem | Backup tooling | Restore validation |
| Change-stream gap | Consumer metrics | Resume token and oplog |
| Import failure | `mongoimport` output | Data types and validation |

## Production Diagnostic Safety

### Prefer Read-Only Diagnostics

Most incident investigation should begin with commands that do not mutate database state:

```javascript
db.hello()
db.stats()
db.serverStatus()
db.currentOp()
db.collection.getIndexes()
db.collection.find().explain("executionStats")
rs.status()
rs.conf()
```

### Be Careful with Diagnostic Operations

Some diagnostic activities can consume meaningful resources:

- Large collection scans
- Expensive aggregations
- Aggressive profiling
- Large `currentOp()` output
- Repeated statistics collection
- Production restore attempts

### Never Treat Diagnostic Commands as Harmless by Default

For example:

```javascript
db.orders.find({}).toArray()
```

can attempt to materialize a large result set.

Prefer:

```javascript
db.orders.find({}).limit(20)
```

or a targeted query.

## Security Considerations

Diagnostic privileges should follow least privilege.

Avoid giving every application user unrestricted administrative access merely to simplify troubleshooting.

Separate:

```text
Application credentials
```

from:

```text
Operational diagnostic credentials
```

Protect:

- Connection strings
- Passwords
- TLS private keys
- Audit information
- Customer data
- Query output

Avoid copying sensitive production documents into public issue trackers or chat systems.

## Common Diagnostic Mistakes

### Running `COLLSCAN` Queries Against Huge Collections

A diagnostic query can itself create production load.

Use:

```javascript
.limit(20)
```

and targeted filters.

### Increasing Timeouts Without Finding the Cause

Changing:

```text
5 seconds → 30 seconds
```

may hide the symptom while increasing resource consumption and request duration.

### Increasing Pool Size Blindly

A larger pool can increase concurrent work and worsen database saturation.

### Restarting MongoDB Before Collecting Evidence

Restarting can remove useful runtime evidence and temporarily hide the underlying cause.

### Assuming `IXSCAN` Means the Query Is Fast

An index can still require examination of a very large number of keys.

### Treating `COLLSCAN` as Automatically Bad

A collection scan on a tiny collection can be completely reasonable.

### Running Heavy Aggregations During an Incident

A diagnostic aggregation can compete with the production workload.

### Changing Replica-Set Configuration Without Understanding Quorum

Replica-set configuration changes can affect elections and availability.

### Deleting Files to Recover Disk Space

MongoDB data files, journal files, and other database-managed files should not be manually deleted.

### Using Production Data for Uncontrolled Testing

Use an isolated recovery environment for restore and data-validation testing.

## Senior-Level Diagnostic Reasoning

A strong MongoDB investigation correlates multiple signals.

For example:

```text
API latency ↑
    +
MongoDB query latency ↑
    +
totalDocsExamined ↑
    +
COLLSCAN
```

suggests a query-plan problem.

Another pattern:

```text
API latency ↑
    +
MongoDB latency normal
    +
pool wait ↑
```

points toward application connection management or concurrency.

Another:

```text
MongoDB latency ↑
    +
CPU normal
    +
disk await ↑
```

suggests a storage bottleneck.

Another:

```text
Write failures ↑
    +
Primary changed
    +
Replica-set election events
```

suggests a topology/failover event.

The goal is to build evidence chains rather than rely on a single metric.

## Diagnostic Evidence Model

For significant incidents, capture:

```text
Topology
    ↓
Workload
    ↓
Queries
    ↓
Indexes
    ↓
Connections
    ↓
Resources
    ↓
Application behavior
    ↓
Recent changes
```

A useful incident record might contain:

| Evidence | Example |
|---|---|
| Timestamp | `2026-09-23T14:20:00Z` |
| Primary | `mongo-01` |
| Replica lag | `18s` |
| CPU | `82%` |
| Disk await | `35ms` |
| Connections | `820` |
| Slow query | `orders.find(...)` |
| Query plan | `COLLSCAN` |
| Deployment | `api-v42` |
| Root-cause hypothesis | Missing index |

## Diagnostic Commands in CI/CD and Operations

Some diagnostics should be automated.

Examples:

- Replica-set health checks
- Connection checks
- Backup freshness checks
- Index presence validation
- Critical query smoke tests
- Schema validation checks
- Deployment compatibility checks

A deployment pipeline can validate connectivity:

```bash
mongosh "$MONGODB_URI" \
  --quiet \
  --eval 'db.adminCommand({ ping: 1 })'
```

A critical query can be tested against a production-like dataset before deployment.

## Operational Runbook

### Connectivity Incident

```text
1. Test DNS
2. Test network connectivity
3. Test TLS
4. Run db.hello()
5. Check replica-set status
6. Check authentication
7. Check application pool
8. Correlate with infrastructure changes
```

### Slow Query Incident

```text
1. Identify query shape
2. Capture execution statistics
3. Run explain()
4. Inspect indexes
5. Compare documents/keys examined
6. Check CPU and disk
7. Compare application versions
8. Validate optimization
```

### Replica Incident

```text
1. Run rs.status()
2. Identify primary
3. Check member health
4. Check election activity
5. Check replication lag
6. Check network
7. Check disk and CPU
8. Verify oplog window
```

### Data Integrity Incident

```text
1. Stop the source of corruption
2. Preserve evidence
3. Identify affected records
4. Determine recovery point
5. Restore into isolation if required
6. Reconcile data
7. Validate application state
8. Document prevention
```

## Key Takeaways

- **Use MongoDB diagnostic commands to answer specific operational questions; do not run large or expensive diagnostics indiscriminately against production.**
- **`db.hello()`, `rs.status()`, `db.serverStatus()`, `explain("executionStats")`, index inspection, and resource metrics form the core diagnostic toolkit for most incidents.**
- **Always correlate database evidence with application behavior, connection pools, worker concurrency, network conditions, storage performance, and recent deployments.**
- **`COLLSCAN`, high `totalDocsExamined`, pool timeouts, replication lag, and high disk latency are symptoms that require root-cause analysis rather than automatic configuration changes.**
- **Production diagnostics must preserve data safety and evidence: prefer targeted read-only commands, use least-privilege credentials, avoid destructive actions, and perform recovery testing in isolated environments.**