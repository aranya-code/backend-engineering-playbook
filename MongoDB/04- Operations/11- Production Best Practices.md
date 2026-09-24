# 11- Production Best Practices

## Overview

Running MongoDB in production requires more than choosing an appropriate schema and adding indexes. Production reliability depends on coordinated decisions across data modeling, query design, connection management, replication, security, observability, backups, deployment, capacity, and operational processes.

A useful production model is:

```text
Application
    ↓
Connection management
    ↓
Query / write design
    ↓
Indexes
    ↓
MongoDB deployment
    ↓
Replication / sharding
    ↓
Storage / network
    ↓
Monitoring / backup / recovery
```

A production-ready MongoDB system should provide:

- Predictable latency
- Durable writes
- High availability
- Controlled schema evolution
- Secure access
- Observable behavior
- Tested backups and recovery
- Capacity headroom
- Controlled operational changes
- Documented incident procedures

The most important principle is to treat MongoDB as part of the complete backend system rather than as an isolated database component.

## Production Architecture

A typical backend architecture can look like:

```mermaid
flowchart LR
    C[Clients] --> LB[Load Balancer / Nginx]
    LB --> API[FastAPI / Django]
    API --> CACHE[Redis]
    API --> MQ[Kafka / Celery]
    API --> DB[(MongoDB)]

    MQ --> WORKER[Background Workers]
    WORKER --> DB

    DB --> RS[Replica Set]
    RS --> P[Primary]
    RS --> S1[Secondary]
    RS --> S2[Secondary]

    DB --> OBS[Monitoring / Logging]
    DB --> BAK[Backup / Recovery]
```

The exact architecture depends on workload, availability requirements, and deployment model.

For larger deployments:

```text
Application
    ↓
mongos
    ↓
Sharded Cluster
    ├── Shard 1 Replica Set
    ├── Shard 2 Replica Set
    └── Shard 3 Replica Set
```

Do not introduce sharding merely because the application is growing. First establish whether the workload actually requires horizontal database scaling.

## Production Design Principles

A production MongoDB deployment should generally follow these principles:

| Area | Production principle |
|---|---|
| Schema | Model around access patterns |
| Documents | Keep growth bounded |
| Indexes | Build from measured query patterns |
| Queries | Avoid unbounded scans |
| Writes | Keep operations targeted and efficient |
| Transactions | Use only where atomicity requires them |
| Connections | Reuse long-lived clients |
| Replication | Distribute members across failure domains |
| Security | Enforce authentication and least privilege |
| Monitoring | Measure database and application behavior |
| Backups | Test restoration, not only backup creation |
| Capacity | Maintain operational headroom |
| Deployment | Make infrastructure changes reproducible |
| Operations | Use documented runbooks |
| Recovery | Validate RPO and RTO periodically |

## Data Modeling Best Practices

MongoDB schema design should start from application access patterns.

Ask:

```text
What does the application read together?
What does it update together?
What grows independently?
What requires independent lifecycle management?
What is queried frequently?
What has unbounded cardinality?
```

Avoid designing the schema solely around entities.

### Embed When Data Belongs Together

Example:

```json
{
  "_id": "order-123",
  "customer": {
    "id": "customer-42",
    "name": "Example Customer"
  },
  "shipping_address": {
    "city": "Kolkata",
    "country": "IN"
  }
}
```

Embedding can provide efficient reads when the embedded data:

- Is bounded
- Is usually accessed with the parent
- Has the same lifecycle
- Does not grow without control

### Reference When Data Grows Independently

For high-cardinality data:

```text
orders
customers
payments
events
```

references are often more appropriate.

Avoid:

```json
{
  "_id": "customer-42",
  "orders": [
    "... thousands or millions of orders ..."
  ]
}
```

An unbounded array creates document-growth, indexing, and operational problems.

## Control Document Growth

A document should have predictable growth characteristics.

Good:

```text
Order
├── customer
├── items
├── totals
└── status_history with bounded size
```

Risky:

```text
Customer
└── all historical transactions
```

When an embedded collection can grow indefinitely, consider a separate collection.

## Denormalization

Controlled duplication is often appropriate in MongoDB.

For example:

```json
{
  "customer_id": "cust-123",
  "customer_name": "Alice",
  "order_total": 1250
}
```

Duplicating `customer_name` can avoid a join for common read paths.

The trade-off is consistency management.

When the source value changes:

```text
Customer name changes
        ↓
Duplicated values may become stale
```

Use duplication when the read-performance or access-pattern benefit justifies the consistency cost.

## Schema Validation

Schema flexibility does not mean schema discipline should be absent.

Use MongoDB schema validation where appropriate for critical collections.

Example:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "status", "total"],
      properties: {
        customer_id: {
          bsonType: "string"
        },
        status: {
          enum: ["pending", "paid", "cancelled"]
        },
        total: {
          bsonType: "decimal"
        }
      }
    }
  },
  validationAction: "error"
})
```

Application-level validation should still exist.

A robust system uses:

```text
API validation
+
Service validation
+
Database validation
```

where each layer protects a different boundary.

## Schema Evolution

Production schema changes should be backward-compatible whenever possible.

Prefer:

```text
Deploy code that understands old + new schema
        ↓
Backfill data
        ↓
Start writing new representation
        ↓
Remove old representation later
```

Avoid:

```text
Change schema
↓
Immediately deploy only new application code
```

because rolling deployments can temporarily run multiple application versions.

## Query Design

Production queries should be:

- Selective
- Index-supported
- Bounded
- Observable
- Consistent with expected cardinality

Example:

```javascript
db.orders.find(
  {
    tenant_id: "tenant-123",
    status: "paid"
  },
  {
    _id: 1,
    total: 1,
    created_at: 1
  }
).sort({
  created_at: -1
}).limit(50)
```

This query has explicit:

- Filter
- Projection
- Sort
- Limit

Such boundaries are important for predictable API behavior.

## Avoid Unbounded Queries

Avoid endpoints that effectively perform:

```javascript
db.orders.find({}).toArray()
```

on a large collection.

Instead use:

```text
Filtering
+
Projection
+
Pagination
+
Maximum page size
```

API contracts should enforce maximum page sizes.

## Pagination

For small datasets, `skip()` can be acceptable.

For large or frequently changing datasets, cursor-based pagination is generally more predictable.

Example:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  _id: { $lt: last_seen_id }
}).sort({
  _id: -1
}).limit(50)
```

The exact pagination key should match the query and index design.

Avoid deep pagination such as:

```javascript
.skip(500000)
```

on large collections without validating its performance characteristics.

## Query Timeouts

Production database operations should not run indefinitely.

PyMongo example:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=2_000,
    socketTimeoutMS=10_000,
    waitQueueTimeoutMS=2_000,
)
```

Timeout values should be derived from the service's latency budget.

A timeout is not a substitute for query optimization.

## Query Plan Validation

Use `explain()` for important queries.

```javascript
db.orders.explain("executionStats").find({
  tenant_id: "tenant-123",
  status: "paid"
})
```

Review:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

A query returning 20 documents while examining millions of documents is a strong candidate for optimization.

## Indexing Best Practices

Indexes should be driven by real query patterns.

For:

```javascript
{
  tenant_id: "tenant-123",
  status: "paid"
}
```

followed by:

```javascript
sort({ created_at: -1 })
```

a candidate index may be:

```javascript
db.orders.createIndex({
  tenant_id: 1,
  status: 1,
  created_at: -1
})
```

Validate it with `explain()` rather than assuming it is optimal.

## ESR Guideline

The Equality-Sort-Range guideline is a useful starting point:

```text
Equality
    ↓
Sort
    ↓
Range
```

Example:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  created_at: {
    $gte: ISODate("2026-01-01")
  }
}).sort({
  priority: -1
})
```

Potential index design should be evaluated against:

```text
tenant_id
priority
created_at
```

The final ordering depends on the complete query workload, selectivity, and sort behavior.

ESR is a guideline, not a rule that should override actual query-plan evidence.

## Avoid Over-Indexing

Every additional index has costs:

- Storage
- Memory
- Write overhead
- Index build time
- Backup overhead
- Operational complexity

Review indexes periodically.

```javascript
db.orders.aggregate([
  { $indexStats: {} }
])
```

Index usage data should be interpreted over a representative observation period because an index that appears unused during a short window may still be required by infrequent production workflows.

## Covered Queries

Projection can reduce document reads when a query can be satisfied directly from an index.

For example:

```javascript
db.users.find(
  { email: "user@example.com" },
  { _id: 1, email: 1 }
)
```

with an appropriate index can reduce document-fetch work.

Always validate the actual execution plan.

## Write Best Practices

Prefer targeted writes.

Good:

```javascript
db.orders.updateOne(
  {
    _id: order_id,
    tenant_id: tenant_id
  },
  {
    $set: {
      status: "completed",
      updated_at: new Date()
    }
  }
)
```

Avoid loading a document into the application merely to modify one field:

```text
Read document
↓
Modify in Python
↓
Write entire document
```

when an atomic update can perform the operation directly.

## Bulk Writes

For high-volume independent operations, use bulk writes.

```python
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"_id": order_id},
        {"$set": {"status": "processed"}}
    )
    for order_id in order_ids
]

result = collection.bulk_write(
    operations,
    ordered=False,
)
```

`ordered=False` can improve throughput when operations are independent and ordering is not required.

Do not use unordered execution when business correctness depends on operation ordering.

## Single-Document Atomicity

MongoDB provides atomicity for operations affecting a single document.

Prefer modeling related state together when it naturally belongs in the same document.

For example:

```text
Order
├── status
├── total
└── payment_status
```

may be updated atomically when the state transition belongs together.

Do not introduce multi-document transactions merely to compensate for poor data modeling.

## Transactions

Use transactions when a business invariant genuinely spans multiple documents or collections.

Example use cases:

- Coordinated financial records
- Inventory and order state
- Multiple related writes requiring atomic commit

Avoid long transactions involving:

- External HTTP calls
- Kafka publishing
- User interaction
- Long-running computation
- Large unbounded scans

A transaction should be short and focused.

## Transaction Retry Design

Transactions can encounter transient failures.

Production code should use the driver's supported transaction retry mechanisms where appropriate rather than implementing arbitrary retry loops.

Business operations should also be idempotent where possible.

A useful architecture is:

```text
Request
   ↓
Validate
   ↓
Transaction
   ↓
Commit
   ↓
Publish event / continue workflow
```

For atomic database-to-event workflows, consider an outbox-style design rather than trying to hold a database transaction open while communicating with Kafka.

## Read and Write Concerns

Choose read and write concerns deliberately.

Examples include:

```text
writeConcern: majority
```

for stronger durability semantics in replica-set deployments.

Read preference should also match the application's consistency requirements.

Do not route latency-sensitive reads to secondaries simply because they are available.

Secondary reads can introduce replication-lag-related staleness.

## High Availability

A production replica set should generally distribute members across independent failure domains.

Example:

```mermaid
flowchart LR
    A[Application] --> P[Primary]
    P --> S1[Secondary AZ-B]
    P --> S2[Secondary AZ-C]

    S1 -. Election participation .-> P
    S2 -. Election participation .-> P
```

The exact topology depends on the infrastructure provider and availability requirements.

## Replica Set Best Practices

Monitor:

- Primary availability
- Election frequency
- Replication lag
- Oplog window
- Member health
- Initial sync activity
- Rollbacks
- Network connectivity

A healthy replica set should not require frequent manual intervention.

## Failure Domains

Do not place all replica members in the same failure domain.

Possible failure domains include:

- Availability Zones
- Hosts
- Racks
- Regions

For disaster recovery across regions, consider the latency, write semantics, operational complexity, and recovery objectives before introducing cross-region topology.

## Read Scaling

Secondaries can support specific read workloads when the application can tolerate the associated consistency characteristics.

Suitable workloads may include:

- Reporting
- Non-critical reads
- Background processing
- Some analytical workloads

Avoid using secondary reads as a blanket solution for poor query performance.

Optimize query design first.

## Sharding

Introduce sharding when the workload requires horizontal distribution of data or operations and a properly sized replica set is no longer sufficient.

Before sharding, validate:

```text
Query performance
Index design
Working set
Storage performance
CPU
Connection capacity
Data growth
```

Sharding adds:

- Operational complexity
- Shard-key constraints
- Cross-shard query behavior
- Additional monitoring
- Additional failure modes

## Shard-Key Design

A production shard key should be evaluated against:

- Cardinality
- Frequency
- Distribution
- Query targeting
- Write distribution
- Growth pattern

Example:

```text
tenant_id
```

may be useful for tenant-targeted workloads but can create a hot shard if one tenant dominates traffic.

A compound shard key may be required.

Do not choose a shard key merely because it is unique.

## Aggregation Best Practices

Filter early:

```javascript
db.orders.aggregate([
  {
    $match: {
      tenant_id: "tenant-123",
      status: "completed"
    }
  },
  {
    $group: {
      _id: "$customer_id",
      total: { $sum: "$amount" }
    }
  }
])
```

Avoid processing millions of documents when the business query only needs a small subset.

General principles:

- `$match` early
- Project only required fields
- Avoid unnecessary `$unwind`
- Control `$lookup` cardinality
- Avoid large unbounded `$group`
- Validate expensive `$sort`
- Use indexes where applicable
- Measure with `explain()`

## Aggregation and API Design

Do not expose arbitrary aggregation capability directly to clients.

Bad architecture:

```text
Client
  ↓
Arbitrary MongoDB aggregation
```

Prefer:

```text
Client
  ↓
Validated API parameters
  ↓
Service layer
  ↓
Controlled aggregation pipeline
  ↓
MongoDB
```

This prevents uncontrolled resource consumption and reduces injection and authorization risks.

## Security Best Practices

Production MongoDB deployments should enforce:

- Authentication
- Authorization
- TLS
- Network restrictions
- Least privilege
- Secret management
- Credential rotation
- Auditing where required
- Security monitoring

Never expose MongoDB directly to the public internet unless there is a very specific, controlled architecture that requires it.

## Least Privilege

Application users should have only the permissions they require.

For example:

```text
Order API
    ↓
Order database user
    ↓
Required collections/actions
```

Avoid giving application services administrative roles.

Separate identities for:

- Application services
- Migration jobs
- Backup operations
- Administrative access
- Reporting workloads

## Credential Management

Do not hard-code:

```python
MONGODB_URI = "mongodb://admin:password@..."
```

Use environment variables or a secret-management system.

For example:

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
```

In Kubernetes, use:

- Kubernetes Secrets
- External secret managers
- Cloud secret-management services

Avoid committing connection strings to Git.

## Network Security

Prefer private network connectivity.

A production architecture should generally look like:

```text
Internet
   ↓
Load Balancer
   ↓
Application Network
   ↓
Private MongoDB Network
```

rather than:

```text
Internet
   ↓
MongoDB
```

Use firewall/security-group rules to restrict database access to expected application and administrative sources.

## TLS

Use TLS for production connections where required by the deployment and security model.

Validate certificates properly.

Do not use insecure certificate bypasses simply to resolve connection problems.

Avoid production configurations equivalent to:

```text
tlsAllowInvalidCertificates=true
```

unless there is a tightly controlled and explicitly justified operational scenario.

## Encryption at Rest

Encryption at rest protects stored database data and backups against unauthorized access to storage.

It does not replace:

- Authentication
- Authorization
- TLS
- Network isolation
- Secret management

Security should be layered.

## Python Integration

Use one long-lived `MongoClient` per application process.

A simplified repository structure:

```text
app/
├── config.py
├── database.py
├── repositories/
│   └── orders.py
├── services/
│   └── orders.py
└── api/
    └── orders.py
```

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    settings.mongodb_uri,
    maxPoolSize=100,
    serverSelectionTimeoutMS=5_000,
)

database = client[settings.mongodb_database]
orders = database["orders"]
```

The repository should encapsulate persistence details rather than spreading raw MongoDB operations throughout API handlers.

## Repository Pattern

Example:

```python
from bson import ObjectId


class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, order_id: ObjectId):
        return self.collection.find_one(
            {"_id": order_id},
            {
                "_id": 1,
                "customer_id": 1,
                "status": 1,
                "total": 1,
            },
        )

    def update_status(self, order_id: ObjectId, status: str):
        return self.collection.update_one(
            {"_id": order_id},
            {"$set": {"status": status}},
        )
```

This separation improves:

- Testing
- Maintainability
- Query consistency
- Observability
- Migration flexibility

## FastAPI Integration

Use application lifecycle management for the MongoDB client.

A simplified pattern:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5_000,
    )

    yield

    app.state.mongo.close()


app = FastAPI(lifespan=lifespan)
```

The exact driver choice matters.

For synchronous PyMongo:

```text
FastAPI
   ↓
sync MongoClient
```

database operations should not block the event loop. For high-concurrency async applications, use the current PyMongo async API where appropriate and follow its concurrency/lifecycle requirements.

Do not select an async driver merely because the framework is async; measure the workload and understand the driver's behavior.

## Django Integration

MongoDB is not equivalent to Django's native relational ORM.

Production architectures commonly use:

```text
Django
   ↓
Service Layer
   ↓
Repository / PyMongo
   ↓
MongoDB
```

MongoDB-specific integrations and third-party ODMs can also be considered.

Keep MongoDB persistence concerns explicit rather than assuming that relational ORM patterns map directly to document databases.

## Background Workers

Celery and Kafka consumers can generate significant MongoDB traffic.

Example:

```mermaid
flowchart LR
    K[Kafka] --> W[Consumer]
    W --> R[Repository]
    R --> M[(MongoDB)]
    M --> W
```

Workers should have:

- Controlled concurrency
- Bounded retries
- Idempotent processing
- Backpressure
- Batch operations where appropriate
- Monitoring

Do not allow worker concurrency to grow independently of MongoDB capacity.

## Idempotency

Production event consumers should assume duplicate delivery can occur.

For example:

```python
collection.update_one(
    {
        "event_id": event_id,
    },
    {
        "$setOnInsert": {
            "processed_at": datetime.now(timezone.utc),
            "event_type": event_type,
        }
    },
    upsert=True,
)
```

The exact implementation depends on the business operation, but the principle is:

```text
Duplicate event
    ↓
Detect previous processing
    ↓
Avoid duplicate side effect
```

## Change Streams

Change streams are useful for event-driven integrations.

Typical flow:

```text
MongoDB
   ↓
Change Stream
   ↓
Consumer
   ↓
Kafka / Celery / Service
```

Consumers should handle:

- Resume tokens
- Transient failures
- Reconnection
- Duplicate processing
- Idempotency
- Consumer lag
- Shutdown

Do not assume change streams replace a durable event architecture in every use case.

## Monitoring

Production monitoring should cover both infrastructure and application behavior.

### Database Metrics

Monitor:

- CPU
- Memory
- Storage
- I/O latency
- Network
- Connections
- Operations/sec
- Query latency
- Write latency

### MongoDB Metrics

Monitor:

- Replication lag
- Oplog window
- Elections
- Query execution
- Index usage
- Collection growth
- Database growth
- Lock/contention indicators
- Cursor behavior

### Application Metrics

Monitor:

- API latency
- Error rate
- MongoDB latency
- Pool wait time
- Timeout rate
- Retry rate
- Queue depth

The correlation is important:

```text
API latency increases
        ↓
MongoDB latency increases
        ↓
Storage latency increases
        ↓
Database becomes resource constrained
```

This is more actionable than looking at CPU alone.

## Slow Query Monitoring

Use query monitoring and profiling appropriately.

The objective is to identify:

```text
Query shape
+
Frequency
+
Latency
+
Resource consumption
```

A query that is slow but executed once per hour may be less important than a query that is moderately expensive and executed thousands of times per second.

Prioritize based on total workload impact.

## Logging

Application logs should include useful context without exposing secrets.

Example:

```text
request_id
service
operation
collection
query_shape
duration_ms
result_count
error
```

Avoid logging:

- Passwords
- Connection strings
- Access tokens
- Sensitive document contents

Prefer structured logging so MongoDB-related incidents can be correlated across services.

## Distributed Tracing

For microservices, trace:

```text
HTTP request
   ↓
Service
   ↓
MongoDB operation
   ↓
Downstream service
```

Useful attributes include:

- Operation name
- Collection
- Duration
- Error
- Trace ID
- Service name

Do not place full query parameters or sensitive document values into traces.

## Capacity Planning

Track:

```text
Data growth
Index growth
CPU
Memory
Storage
I/O
Network
Connections
Replication lag
Oplog window
Query latency
```

Capacity planning should include:

- Current workload
- Peak workload
- Growth forecast
- Failure scenarios
- Backup requirements
- Recovery requirements

Do not wait for storage or CPU exhaustion before starting the scaling process.

## Resource Headroom

A production deployment needs headroom for:

- Traffic spikes
- Failover
- Index builds
- Backups
- Deployments
- Data migrations
- Rebalancing
- Incident recovery

Avoid designing normal operation around maximum resource utilization.

The appropriate headroom depends on measured workload, SLOs, failure requirements, and infrastructure characteristics.

## Backup Strategy

Replication is not backup.

Replication protects primarily against certain node failures and provides high availability.

Backups protect against:

- Accidental deletion
- Application bugs
- Corruption
- Malicious changes
- Operational mistakes
- Disaster scenarios

A production backup strategy should define:

```text
Backup frequency
Retention
RPO
RTO
Storage location
Encryption
Access control
Restore procedure
Validation procedure
```

## Backup Validation

A successful backup job does not prove recoverability.

Regularly test:

```text
Backup
↓
Restore
↓
Validate indexes/data
↓
Start application against restored environment
↓
Run functional checks
↓
Measure recovery time
```

Record actual recovery duration.

## Disaster Recovery

Define explicit failure scenarios:

- Primary failure
- Secondary failure
- Host failure
- Availability Zone failure
- Region failure
- Accidental deletion
- Credential compromise
- Corrupted deployment
- Application-induced data corruption

For each scenario document:

```text
Detection
↓
Isolation
↓
Recovery
↓
Validation
↓
Traffic restoration
↓
Post-incident actions
```

## RPO and RTO

RPO:

```text
How much data can we afford to lose?
```

RTO:

```text
How long can the service remain unavailable?
```

Architecture should be selected to meet these requirements rather than defining RPO/RTO after implementation.

## Deployment Best Practices

Infrastructure configuration should be reproducible.

Use:

- Infrastructure as Code
- Version-controlled configuration
- CI/CD
- Environment-specific configuration
- Secret management
- Automated validation

Do not rely on undocumented manual changes.

## Configuration Management

Separate:

```text
Application configuration
Database credentials
Environment configuration
Infrastructure configuration
Operational configuration
```

Use environment variables or a dedicated configuration system.

Example:

```text
MONGODB_URI
MONGODB_DATABASE
MONGODB_SERVER_SELECTION_TIMEOUT_MS
MONGODB_MAX_POOL_SIZE
```

Avoid hard-coding production values in application source code.

## Deployment Changes

For database changes:

```text
Review
↓
Test
↓
Deploy backward-compatible application
↓
Apply database change
↓
Observe
↓
Roll forward / rollback application
```

Avoid destructive database changes in the same deployment step as application changes unless the migration strategy has been explicitly designed for atomicity and rollback.

## Index Deployment

Treat index creation as a production change.

Before creating an index:

- Estimate index size
- Validate query need
- Check available storage
- Review write workload
- Evaluate build impact
- Test in a representative environment
- Define rollback/removal procedure

Do not create indexes manually in production and forget to encode them in infrastructure or application configuration.

## Data Migrations

Large migrations should be:

- Incremental
- Idempotent
- Observable
- Resumable
- Rate-limited

Avoid:

```text
Load millions of documents
↓
Transform all in application memory
↓
Write everything back
```

Prefer bounded batches.

Example:

```python
BATCH_SIZE = 1_000

while True:
    documents = list(
        collection.find(
            {"migration_version": {"$lt": 2}},
            {"_id": 1, "status": 1},
        ).limit(BATCH_SIZE)
    )

    if not documents:
        break

    operations = [
        UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"migration_version": 2}},
        )
        for doc in documents
    ]

    collection.bulk_write(operations, ordered=False)
```

For large production migrations, use a stable pagination strategy rather than repeatedly scanning the same unbounded query.

## Operational Runbooks

Important runbooks should cover:

- Primary unavailable
- Replica lag
- Storage exhaustion
- High CPU
- High memory pressure
- Slow queries
- Connection exhaustion
- Failed index deployment
- Failed backup
- Restore
- Accidental deletion
- Shard imbalance
- Authentication failures

Each runbook should contain:

```text
Symptoms
↓
Immediate safety actions
↓
Diagnostics
↓
Decision points
↓
Corrective action
↓
Validation
↓
Prevention
```

## Change Management

Database changes should be reviewed based on risk.

High-risk changes include:

- Shard-key changes
- Large index builds
- Collection migrations
- Major schema changes
- Replica-set topology changes
- Read/write concern changes
- Large data deletions
- Retention changes

Use staged rollout and monitoring for high-impact changes.

## Cost Optimization

Production optimization should consider total cost, not only compute.

Major cost drivers can include:

- Compute
- Memory
- Storage
- IOPS
- Network
- Backups
- Data transfer
- Over-indexing
- Oversized clusters

Avoid reducing cost by removing redundancy or backup coverage required by the application's reliability requirements.

## MongoDB Compass in Production

Compass is useful for:

- Query exploration
- Schema inspection
- Aggregation development
- Index inspection
- Troubleshooting

It should not become the primary mechanism for production changes.

Prefer:

```text
Code
+
Version control
+
CI/CD
+
Infrastructure automation
```

for repeatable production operations.

Manual Compass changes should be documented and reconciled with the source of truth.

## MongoDB Shell

`mongosh` is valuable for operational diagnostics.

Examples:

```javascript
db.stats()
```

```javascript
db.orders.stats()
```

```javascript
db.orders.getIndexes()
```

```javascript
db.orders.aggregate([
  { $indexStats: {} }
])
```

For replica sets:

```javascript
rs.status()
```

```javascript
rs.conf()
```

Use administrative commands carefully in production and verify the impact before executing write or topology-changing operations.

## Production Readiness Checklist

### Architecture

- [ ] Production topology is documented.
- [ ] Failure domains are understood.
- [ ] Replica-set configuration is appropriate.
- [ ] Sharding is used only when justified.
- [ ] Capacity headroom is documented.

### Data Modeling

- [ ] Access patterns drive schema design.
- [ ] Unbounded arrays are avoided.
- [ ] Document growth is controlled.
- [ ] Denormalization trade-offs are understood.
- [ ] Schema validation exists where appropriate.

### Queries

- [ ] Important queries are indexed.
- [ ] Query plans are validated.
- [ ] API queries are bounded.
- [ ] Pagination is implemented appropriately.
- [ ] Projections are used where beneficial.

### Indexes

- [ ] Indexes map to actual query patterns.
- [ ] Unused indexes are reviewed.
- [ ] Index size is monitored.
- [ ] Index creation is managed as a deployment change.

### Connections

- [ ] MongoClient is reused per process.
- [ ] Pool sizes are documented.
- [ ] Aggregate connections are understood.
- [ ] Connection wait time is monitored.

### Reliability

- [ ] Replica health is monitored.
- [ ] Replication lag is monitored.
- [ ] Oplog window is monitored.
- [ ] Failover has been tested.
- [ ] N-1 capacity is validated.

### Security

- [ ] Authentication is enabled.
- [ ] Least privilege is implemented.
- [ ] TLS is configured appropriately.
- [ ] MongoDB is network-restricted.
- [ ] Secrets are managed securely.
- [ ] Sensitive data is not exposed in logs.

### Backup and Recovery

- [ ] Backups are automated.
- [ ] Retention is documented.
- [ ] Restore procedures exist.
- [ ] Restore tests are performed.
- [ ] RPO is measured.
- [ ] RTO is measured.

### Operations

- [ ] Metrics are collected.
- [ ] Logs are centralized.
- [ ] Slow queries are monitored.
- [ ] Alerts have actionable thresholds.
- [ ] Runbooks exist.
- [ ] Capacity is reviewed periodically.

## Common Production Pitfalls

### Treating MongoDB Like PostgreSQL

MongoDB supports relational-like capabilities such as transactions and joins through `$lookup`, but its strongest designs usually come from document-oriented modeling.

Do not mechanically reproduce normalized relational schemas without evaluating MongoDB access patterns.

### Using Transactions Everywhere

Transactions add coordination and resource costs.

Use them when business invariants require multi-document atomicity.

### Creating an Index for Every Query

Indexes have costs.

Build indexes from representative workload analysis and validate them with query plans.

### Using `skip()` for Deep Pagination

Deep offsets can become expensive.

Prefer stable cursor-based pagination for large datasets.

### Creating a MongoClient Per Request

This causes connection churn and can exhaust resources.

Reuse a long-lived client per process.

### Scaling API Pods Without Database Planning

More API workers can create:

```text
More connections
+
More concurrent queries
+
More writes
```

Scale the database and application together.

### Using Secondaries as a Generic Performance Fix

Secondary reads can introduce stale reads and additional replication pressure.

First optimize the query and workload.

### Treating Replication as Backup

Replication does not protect against every logical or application-level failure.

Maintain independent backups.

### Running Large Migrations Without Backpressure

A migration can consume the same database resources required by user-facing traffic.

Rate-limit and monitor large migrations.

### Making Manual Production Changes

Changes made through Compass or `mongosh` can become invisible to the infrastructure source of truth.

Automate repeatable changes and document emergency exceptions.

## Production Troubleshooting Methodology

Use a consistent workflow:

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

### High Latency

```text
Symptom
↓
API latency increases
↓
Possible causes
- Slow MongoDB query
- Missing/inefficient index
- Storage latency
- CPU pressure
- Connection pool contention
- Replication-related workload
↓
Isolation
- Compare API vs DB latency
- Inspect explain()
- Check resource metrics
- Check connection pool wait
↓
Corrective action
- Optimize query/index
- Tune concurrency
- Increase capacity if required
↓
Prevention
- Query monitoring
- Load testing
- Capacity reviews
```

### High CPU

```text
Symptom
↓
MongoDB CPU remains high
↓
Possible causes
- Expensive queries
- Aggregations
- High concurrency
- Index maintenance
- Encryption overhead
- Background jobs
↓
Isolation
- Identify expensive query shapes
- Review aggregation workload
- Compare read/write rates
↓
Corrective action
- Optimize workload
- Reduce unnecessary concurrency
- Scale CPU if justified
↓
Prevention
- Query performance budgets
- Monitoring
- Load testing
```

### Storage Exhaustion

```text
Symptom
↓
Available storage decreases rapidly
↓
Possible causes
- Data growth
- Index growth
- Failed retention
- Large documents
- Backup artifacts
↓
Isolation
- Inspect database/collection statistics
- Inspect index sizes
- Review lifecycle jobs
↓
Corrective action
- Expand storage
- Correct retention
- Remove unnecessary indexes
- Archive data
↓
Prevention
- Growth forecasting
- Storage alerts
- Capacity reviews
```

### Connection Exhaustion

```text
Symptom
↓
Requests wait for MongoDB connections
↓
Possible causes
- Too many application processes
- Pool too large
- Pool too small
- Slow operations
- Connection leaks
↓
Isolation
- Inspect application pool metrics
- Inspect MongoDB connections
- Measure query latency
↓
Corrective action
- Tune pool/concurrency
- Fix slow queries
- Scale database if justified
↓
Prevention
- Connection-capacity model
- Autoscaling guardrails
- Load tests
```

## Interview Considerations

### What makes MongoDB production-ready?

A strong answer should cover:

```text
Good schema design
+
Query/index discipline
+
Connection management
+
Replica-set high availability
+
Security
+
Monitoring
+
Backup/recovery
+
Capacity planning
+
Operational automation
```

### How would you troubleshoot a slow MongoDB API?

Start from the user-visible symptom:

```text
API latency
↓
Database latency
↓
Query shape
↓
explain()
↓
Index/resource analysis
↓
Storage/CPU/memory
↓
Connection pool
↓
Corrective action
```

Do not immediately add hardware.

### Why is a replica set required for production?

It provides redundancy and automatic failover, allowing the deployment to tolerate certain node failures.

The topology must still be designed across appropriate failure domains and tested under failure conditions.

### How do you decide whether to use a transaction?

Ask whether the business invariant requires atomic changes across multiple documents.

If a single-document model can preserve the invariant, that is often simpler.

If multiple documents must change atomically, a transaction may be appropriate.

### How should MongoDB be secured?

At minimum, consider:

```text
Authentication
+
Least-privilege authorization
+
TLS
+
Network isolation
+
Secret management
+
Encryption at rest
+
Auditing/monitoring where required
```

### How do you operate MongoDB safely?

Use:

```text
Automation
+
Version control
+
Monitoring
+
Runbooks
+
Backups
+
Restore testing
+
Capacity planning
+
Controlled changes
```

The goal is predictable behavior rather than relying on manual intervention during incidents.

## Key Takeaways

- **Production MongoDB reliability starts with access-pattern-driven schema and query design, bounded document growth, appropriate indexes, and controlled application concurrency.**
- **High availability requires more than a replica set: distribute failure domains, monitor replication and elections, validate N-1 capacity, and test actual failover behavior.**
- **Security, observability, backups, restore testing, capacity planning, and operational runbooks are core production requirements, not optional infrastructure additions.**
- **Treat database changes as controlled production changes: use backward-compatible migrations, automated index management, bounded data migrations, CI/CD, and version-controlled configuration.**
- **When incidents occur, diagnose the complete request path—from API and connection pool through MongoDB query execution, resources, replication, and storage—before deciding to scale infrastructure.**