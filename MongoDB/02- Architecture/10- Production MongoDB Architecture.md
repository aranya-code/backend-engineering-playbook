# 10- Production MongoDB Architecture

## Overview

A production MongoDB architecture is not simply a MongoDB server connected to an application. It is a complete system covering data modeling, query behavior, replication, high availability, security, networking, observability, backups, deployment, capacity planning, and application integration.

A typical production architecture looks like:

```text
Clients
   │
   ▼
Load Balancer / API Gateway
   │
   ▼
Application Instances
   │
   ├──────────────► Redis
   │
   ├──────────────► Kafka
   │
   ▼
MongoDB
   │
   ├── Replica Set
   │   ├── Primary
   │   ├── Secondary
   │   └── Secondary
   │
   ├── Monitoring
   └── Backup / Disaster Recovery
```

For larger workloads, the database layer may become a sharded cluster:

```text
Application
     │
     ▼
mongos
     │
 ┌───┼───────────┐
 ▼   ▼           ▼
S1   S2          S3
│    │           │
RS   RS          RS
```

The architecture should be driven by:

- workload characteristics
- access patterns
- consistency requirements
- availability requirements
- data growth
- throughput requirements
- recovery objectives
- security requirements
- operational capabilities
- cost constraints

The goal is not to maximize the number of MongoDB components. The goal is to provide the required reliability and performance with an architecture that the engineering team can operate safely.

---

## Production Architecture Principles

A production MongoDB system should generally follow these principles:

| Principle | Production Approach |
|---|---|
| Availability | Replica sets with failure-domain distribution |
| Scalability | Optimize first, shard when horizontal scaling is justified |
| Consistency | Explicitly choose read/write concerns |
| Performance | Access-pattern-driven indexes and queries |
| Security | Authentication, authorization, TLS, private networking |
| Reliability | Timeouts, retries, idempotency, monitoring |
| Recovery | Independent backups and tested restores |
| Operations | Metrics, logs, alerts, runbooks |
| Deployment | Automated and controlled infrastructure changes |
| Application integration | Long-lived connection pools and repository/service layers |
| Cost | Capacity planning and workload-aware scaling |

A strong MongoDB architecture also assumes that failures will occur.

Design for:

```text
Primary failure
Secondary failure
AZ failure
Network partition
Storage failure
Application failure
Bad deployment
Logical data corruption
Credential compromise
Regional failure
```

---

## Production Reference Architecture

A typical AWS-based backend architecture can look like:

```mermaid
flowchart TB
    Client[Clients]
    DNS[DNS / Route 53]
    LB[Load Balancer]
    API1[API Instance 1]
    API2[API Instance 2]
    API3[API Instance 3]

    Redis[(Redis)]
    Kafka[(Kafka)]
    
    subgraph VPC["Private VPC"]
        subgraph DB["MongoDB Private Network"]
            P[(Primary)]
            S1[(Secondary)]
            S2[(Secondary)]
        end

        Monitoring[Monitoring / Logging]
        Backup[Backup / DR]
    end

    Client --> DNS
    DNS --> LB
    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> Redis
    API2 --> Redis
    API3 --> Redis

    API1 --> Kafka
    API2 --> Kafka
    API3 --> Kafka

    API1 --> P
    API2 --> P
    API3 --> P

    P --> S1
    P --> S2

    DB --> Monitoring
    DB --> Backup
```

For a sharded deployment:

```mermaid
flowchart TB
    Client[Clients]
    LB[Load Balancer]
    API[Application Cluster]

    M1[mongos 1]
    M2[mongos 2]

    Config[(Config Server Replica Set)]

    subgraph Shard1["Shard 1 Replica Set"]
        P1[(Primary)]
        S11[(Secondary)]
        S12[(Secondary)]
    end

    subgraph Shard2["Shard 2 Replica Set"]
        P2[(Primary)]
        S21[(Secondary)]
        S22[(Secondary)]
    end

    subgraph Shard3["Shard 3 Replica Set"]
        P3[(Primary)]
        S31[(Secondary)]
        S32[(Secondary)]
    end

    Client --> LB
    LB --> API

    API --> M1
    API --> M2

    M1 --> Config
    M2 --> Config

    M1 --> P1
    M1 --> P2
    M1 --> P3

    M2 --> P1
    M2 --> P2
    M2 --> P3

    P1 --> S11
    P1 --> S12

    P2 --> S21
    P2 --> S22

    P3 --> S31
    P3 --> S32
```

The second architecture is appropriate only when workload characteristics justify sharding.

---

## Application Architecture

The database should not normally be accessed directly from every application layer.

A clean backend architecture is:

```text
HTTP / gRPC
    │
    ▼
Controller / View
    │
    ▼
Service Layer
    │
    ▼
Repository
    │
    ▼
MongoClient
    │
    ▼
MongoDB
```

Responsibilities should remain separated.

### Controller

Handles:

- HTTP/gRPC input
- authentication context
- request validation
- response serialization

### Service

Handles:

- business rules
- transactions
- orchestration
- idempotency
- domain decisions

### Repository

Handles:

- MongoDB queries
- projections
- indexes
- persistence
- database-specific error translation

This separation prevents MongoDB-specific query logic from spreading throughout the application.

---

## Connection Architecture

A production application should normally create a long-lived `MongoClient`.

Avoid:

```python
def get_user(user_id):
    client = MongoClient(MONGODB_URI)
    ...
```

This creates unnecessary connection-management overhead.

Prefer:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

Then reuse the client throughout the process.

The driver maintains connection pools internally.

---

## Connection Pooling

Conceptually:

```text
Application Process
       │
       ▼
   MongoClient
       │
       ▼
 Connection Pool
 ┌─────┼─────┐
 ▼     ▼     ▼
 C1    C2    C3
```

Connection pools prevent every request from creating a new database connection.

Pool sizing should consider:

- application concurrency
- number of workers
- request latency
- database capacity
- number of application instances

If:

```text
100 application processes
×
100 database connections
```

are allowed without capacity analysis, the database can receive thousands of simultaneous connections.

Connection limits should therefore be designed at the system level.

---

## Timeouts

Production applications should not allow database operations to wait indefinitely.

Useful timeout categories include:

| Timeout | Purpose |
|---|---|
| Server selection | Maximum time to locate a suitable MongoDB server |
| Connection timeout | Maximum time to establish a connection |
| Socket timeout | Maximum time waiting for socket operations |
| Transaction timeout | Maximum transaction execution window |
| Application request timeout | Maximum API request duration |

Timeouts should be aligned.

For example:

```text
API timeout
    >
Database operation timeout
    >
Connection timeout
```

The exact values depend on the application's latency budget.

---

## Connection String Management

Do not hard-code production credentials:

```python
MONGODB_URI = "mongodb://admin:password@mongo1:27017/app"
```

Prefer environment or secret-manager configuration:

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
```

A production connection string should include the appropriate topology and security options.

For a replica set:

```text
mongodb://mongo1,mongo2,mongo3/app?replicaSet=rs0
```

For a sharded deployment, applications normally connect through `mongos` routers:

```text
mongodb://mongos-1,mongos-2/app
```

---

## Environment Separation

Production MongoDB configuration should be isolated from development and testing.

```text
Development
    ↓
Local MongoDB / Docker

Testing
    ↓
Dedicated test database

Staging
    ↓
Production-like topology

Production
    ↓
Managed / highly available MongoDB
```

Do not use the production database for integration tests.

---

## Data Modeling

Production MongoDB design starts with access patterns.

Do not begin with:

```text
"What tables would I create?"
```

Instead ask:

```text
What queries will the application execute?
What data is read together?
What data changes together?
What data grows without bound?
What data must remain strongly consistent?
```

MongoDB models should optimize the application's actual workload.

---

## Embedding vs Referencing

Consider an order:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUS-1001",
  "items": [
    {
      "product_id": "P-100",
      "quantity": 2,
      "price": 49.99
    }
  ]
}
```

Embedding is useful when:

- child data is normally read with the parent
- child cardinality is bounded
- atomic updates are useful
- document growth is controlled

References are more appropriate when:

- child data grows without bound
- entities have independent lifecycles
- children are queried independently
- duplication would be expensive

---

## Document Growth

MongoDB documents should remain bounded and operationally manageable.

Avoid unbounded arrays such as:

```json
{
  "user_id": "U1001",
  "events": [
    "... potentially millions of events ..."
  ]
}
```

Prefer a separate collection:

```text
users
events
```

with:

```text
events.user_id → users.user_id
```

Unbounded document growth can cause:

- larger reads
- larger writes
- memory pressure
- document relocation
- contention
- difficult indexing
- operational problems

---

## Hot Documents

A hot document receives frequent concurrent updates.

Example:

```json
{
  "_id": "global-counter",
  "count": 123456789
}
```

If thousands of workers repeatedly update the same document, it becomes a contention point.

Possible alternatives include:

- sharded counters
- bucketed counters
- append-only events
- asynchronous aggregation
- Redis counters
- partitioned state

The correct design depends on consistency requirements.

---

## Schema Validation

MongoDB's flexible schema should not mean uncontrolled schema.

Production systems can use JSON Schema validation for critical collections.

Example:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["order_id", "customer_id", "status"],
      properties: {
        order_id: {
          bsonType: "string"
        },
        customer_id: {
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

Application-level validation should still exist.

Database validation protects the database from invalid writes originating outside the primary application.

---

## Index Strategy

Indexes should be derived from actual queries.

Suppose the API frequently executes:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  status: "pending"
}).sort({
  created_at: -1
})
```

A candidate index is:

```javascript
db.orders.createIndex({
  tenant_id: 1,
  status: 1,
  created_at: -1
})
```

But index design must be validated using actual execution plans.

Do not create indexes simply because fields appear frequently in documents.

---

## Index Costs

Every additional index has costs:

```text
More indexes
    ↓
More storage
    ↓
More memory pressure
    ↓
More write work
    ↓
More maintenance
```

A production index review should ask:

- Which query requires this index?
- What is the query frequency?
- Does the index improve the winning plan?
- Is it redundant?
- How large is it?
- What is the write overhead?

---

## Query Performance

Use `explain()` to investigate production query performance.

Example:

```javascript
db.orders
  .explain("executionStats")
  .find({
    tenant_id: "tenant-123",
    status: "pending"
  })
  .sort({
    created_at: -1
  })
```

Important metrics include:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

A useful rule of thumb is to investigate queries where:

```text
totalDocsExamined >> nReturned
```

This often indicates that MongoDB is examining significantly more documents than the application actually needs.

It is not a universal failure condition, but it is a useful signal.

---

## Aggregation Architecture

Aggregation is appropriate for:

- reporting
- grouped statistics
- transformations
- analytical APIs
- ETL-style processing
- materialized results

A production pipeline should filter early.

Prefer:

```javascript
[
  {
    $match: {
      tenant_id: "tenant-123",
      status: "completed"
    }
  },
  {
    $group: {
      _id: "$customer_id",
      total: {
        $sum: "$amount"
      }
    }
  }
]
```

over unnecessarily processing the entire collection before filtering.

---

## Large Aggregations

Large aggregation pipelines can consume significant:

- CPU
- memory
- disk
- network bandwidth

Do not run expensive analytical pipelines synchronously inside latency-sensitive API requests unless the workload has been measured and sized appropriately.

Alternatives include:

```text
MongoDB
   ↓
Scheduled aggregation
   ↓
Materialized collection
   ↓
API reads precomputed result
```

or:

```text
MongoDB
   ↓
Kafka / CDC
   ↓
Analytics system
```

---

## Read and Write Workloads

Production systems should classify workloads.

| Workload | Typical Strategy |
|---|---|
| Transactional reads | Primary / appropriate consistency |
| High-volume point reads | Indexed queries + cache |
| Reporting | Secondary or dedicated analytics path |
| Aggregation | Controlled pipelines / precomputation |
| High write throughput | Schema optimization / sharding |
| Event processing | Change streams / Kafka |
| Background jobs | Celery / workers with controlled concurrency |

Do not make every request use the same read preference or consistency level.

---

## Read Preference

Typical choices include:

```text
primary
primaryPreferred
secondary
secondaryPreferred
nearest
```

Use primary reads when immediate consistency matters.

Secondary reads may be useful for:

- dashboards
- reporting
- non-critical search
- analytics

But secondary reads can return stale data.

---

## Write Concern

For important production writes, explicitly define the desired write durability.

For example:

```python
from pymongo import WriteConcern

collection = db.get_collection(
    "orders",
    write_concern=WriteConcern(w="majority")
)
```

Majority writes can provide stronger durability semantics but may have higher latency and may become unavailable if a majority cannot acknowledge writes.

The choice should be driven by business requirements.

---

## Read Concern

Read concern controls the consistency characteristics of reads.

A production system should document why a particular read concern is used.

Example reasoning:

```text
Financial state
    ↓
Strong consistency requirements

Analytics
    ↓
Stale reads may be acceptable
```

Do not select a read concern simply because it is the default or because it appears faster in a local benchmark.

---

## Transactions

MongoDB provides atomicity for individual document operations and supports multi-document transactions.

Use transactions when multiple writes must satisfy an atomic business invariant.

Example:

```text
Create order
    +
Reserve inventory
    +
Record payment state
```

However, avoid using transactions as a substitute for good document modeling.

If related data can be modeled into one document and updated atomically, that can be simpler and faster than a multi-document transaction.

---

## Transaction Design

A transaction should be:

- short-lived
- narrowly scoped
- deterministic
- retry-aware
- free of unnecessary external side effects

Avoid:

```text
Start transaction
   ↓
Call external payment API
   ↓
Wait 5 seconds
   ↓
Call another service
   ↓
Commit
```

Database transactions should not become distributed workflow coordinators.

Prefer:

```text
Database transaction
    ↓
Persist internal state

Outbox / event
    ↓
External processing
```

when appropriate.

---

## Transaction Example in Python

```python
from pymongo import MongoClient

client = MongoClient(MONGODB_URI)

with client.start_session() as session:
    with session.start_transaction():
        orders.insert_one(
            {
                "order_id": "ORD-1001",
                "status": "confirmed",
            },
            session=session,
        )

        inventory.update_one(
            {"product_id": "P-100"},
            {"$inc": {"available": -1}},
            session=session,
        )
```

Production code should also handle transient transaction errors and ensure the business operation is safe to retry.

---

## Replica Set Architecture

For most production deployments, a replica set is the foundation of HA.

Typical topology:

```text
                Primary
                   │
          ┌────────┴────────┐
          ▼                 ▼
      Secondary         Secondary
```

Members should be distributed across independent failure domains.

For AWS:

```text
AZ-A → Primary
AZ-B → Secondary
AZ-C → Secondary
```

This provides protection against a single-AZ failure when the topology retains a voting majority.

---

## Failover

The simplified failover lifecycle is:

```mermaid
sequenceDiagram
    participant App as Application
    participant P as Primary
    participant S1 as Secondary
    participant S2 as Secondary

    App->>P: Write
    P-->>App: Acknowledge

    P-xS1: Primary fails
    P-xS2: Primary fails

    S1->>S2: Election
    S2-->>S1: Election coordination

    S1->>S1: Become primary
    App->>S1: Retry / reconnect
    S1-->>App: Write succeeds
```

Applications should expect transient errors during elections.

---

## High Availability Is End-to-End

MongoDB HA alone is insufficient.

Consider:

```text
Internet
   ↓
Single API server
   ↓
MongoDB Replica Set
```

The MongoDB layer is highly available, but the API server is not.

A production architecture should consider:

```text
DNS
 ↓
Load Balancer
 ↓
Multiple API instances
 ↓
Redis / Kafka
 ↓
MongoDB Replica Set
 ↓
Backup / DR
```

Every critical dependency should have an appropriate failure strategy.

---

## Sharding Decision

Sharding should be introduced when horizontal scaling is required.

Typical reasons include:

- write throughput exceeds one primary's sustainable capacity
- dataset size exceeds practical single-node capacity
- working set requirements exceed available memory
- workload requires horizontal distribution

Do not use sharding as the first response to a slow query.

Investigate:

```text
Query
 ↓
Index
 ↓
Schema
 ↓
Resource utilization
 ↓
Read/write pattern
 ↓
Only then sharding
```

---

## Sharded Production Architecture

A production sharded deployment should normally contain:

```text
Application
    │
    ▼
Multiple mongos
    │
    ├── Config Server Replica Set
    │
    ├── Shard 1 Replica Set
    │
    ├── Shard 2 Replica Set
    │
    └── Shard 3 Replica Set
```

Each shard should have its own HA topology.

A sharded cluster is therefore more complex than simply adding another MongoDB server.

---

## Shard-Key Design

The shard key should be selected using:

- cardinality
- frequency
- monotonicity
- query targeting
- write distribution
- data distribution
- growth characteristics

Example:

```javascript
{
  tenant_id: 1,
  created_at: 1
}
```

may be useful for tenant-oriented workloads, but a dominant tenant can still create a hot shard.

A good shard key must be validated against actual production-like traffic.

---

## Avoiding Scatter-Gather

Consider:

```javascript
{
  status: "pending"
}
```

when the collection is sharded by:

```javascript
{
  tenant_id: 1
}
```

The query may need to contact multiple shards.

Prefer queries that include routing information when the application's access pattern allows it:

```javascript
{
  tenant_id: "tenant-123",
  status: "pending"
}
```

This can reduce cluster-wide work.

---

## MongoDB and Redis

Redis should be used to solve a different problem from MongoDB.

Typical architecture:

```text
API
 │
 ├── Redis → Fast cache
 │
 └── MongoDB → Durable source of truth
```

Good cache candidates include:

- frequently accessed metadata
- configuration
- session-related data
- expensive computed results

Do not use Redis to hide an unoptimized MongoDB query indefinitely.

---

## MongoDB and Kafka

Kafka can decouple MongoDB-backed workloads.

Example:

```text
API
 │
 ▼
MongoDB
 │
 ▼
Outbox / Change Stream
 │
 ▼
Kafka
 │
 ├── Search Service
 ├── Notification Service
 └── Analytics Service
```

This can reduce synchronous coupling between services.

Events should be:

- idempotently processed
- versioned
- observable
- retryable

---

## Change Streams

Change streams are useful for event-driven MongoDB workloads.

Example:

```python
with db.orders.watch() as stream:
    for change in stream:
        process_change(change)
```

Production consumers should handle:

- resume tokens
- reconnects
- duplicate processing
- consumer restarts
- backpressure
- idempotency

Do not assume a change-stream consumer will never disconnect.

---

## Security Architecture

MongoDB should normally be deployed on private networks.

A production security architecture includes:

```text
Application
    │
    │ TLS
    ▼
MongoDB / mongos
    │
    ├── Authentication
    ├── Authorization
    ├── TLS
    └── Network Restrictions
```

Critical controls include:

- authentication
- least privilege
- TLS
- network isolation
- secret management
- encryption at rest
- audit logging where required
- security monitoring

---

## Least Privilege

Avoid using a highly privileged administrative user from the application.

Instead:

```text
Application User
    ↓
Only required database
    ↓
Only required collections
    ↓
Only required operations
```

For example, an order service should not automatically receive cluster-wide administrative privileges.

Separate:

```text
Application credentials
Administrative credentials
Backup credentials
Monitoring credentials
Migration credentials
```

where practical.

---

## Network Security

Production MongoDB servers should generally not be directly exposed to the public internet.

A typical AWS architecture is:

```text
Public Subnets
    │
    └── Load Balancer

Private Subnets
    ├── Application
    ├── MongoDB
    ├── Redis
    └── Kafka
```

Security groups or equivalent controls should allow only required traffic.

---

## TLS

TLS protects MongoDB traffic from network interception.

Use TLS for:

- application-to-MongoDB traffic
- inter-member communication where configured
- administrative connections where required

Certificate lifecycle management should include:

```text
Issue
 ↓
Deploy
 ↓
Validate
 ↓
Rotate
 ↓
Remove old certificate
```

Certificate expiration should be monitored.

---

## Secret Management

Production secrets should not be stored in:

- Git repositories
- Docker images
- source code
- plaintext configuration files
- CI logs

Use an appropriate secret-management system such as:

- AWS Secrets Manager
- Kubernetes Secrets with appropriate encryption/access controls
- CI/CD secret stores
- managed database credential systems

Rotate credentials using a tested procedure.

---

## Monitoring Architecture

Production MongoDB monitoring should cover four layers:

```text
Application
    ↓
Driver / Connection Pool
    ↓
MongoDB
    ↓
Infrastructure
```

### Application

Monitor:

- request latency
- database error rate
- timeout rate
- retry count
- transaction failures

### Driver

Monitor:

- pool utilization
- server selection failures
- connection failures
- topology changes

### MongoDB

Monitor:

- query latency
- operations
- replication lag
- elections
- connections
- memory
- CPU
- storage

### Infrastructure

Monitor:

- disk
- IOPS
- network
- instance health
- AZ health

---

## Logging

Database logging should support incident investigation without exposing sensitive data.

Avoid logging:

```text
passwords
tokens
credentials
full sensitive documents
payment information
personal secrets
```

Useful log information includes:

```text
operation type
collection
duration
request correlation ID
application service
error category
retry count
```

Slow-query logging should be configured carefully to avoid excessive operational noise.

---

## Correlation IDs

A production request can be traced through:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI / Django
  ↓
MongoDB
  ↓
Kafka
  ↓
Worker
```

Use a correlation ID:

```text
request_id = 8c5c...
```

to connect logs across services.

This significantly reduces troubleshooting time in distributed systems.

---

## Observability

A useful observability model is:

```text
Metrics
  +
Logs
  +
Traces
  +
Database Diagnostics
```

Metrics answer:

```text
How often?
How much?
How slow?
```

Logs answer:

```text
What happened?
```

Traces answer:

```text
Where did time go?
```

MongoDB diagnostics answer:

```text
What is the database doing?
```

---

## Capacity Planning

Production capacity should account for:

```text
Current workload
+
Growth
+
Peak traffic
+
Failover capacity
+
Backup overhead
+
Maintenance overhead
```

For example, if two healthy database members are already running at high utilization, losing one member may create immediate capacity problems even though the replica set technically remains available.

HA therefore requires **capacity headroom**, not merely redundancy.

---

## Storage Planning

Storage requirements include more than document size.

Consider:

```text
Documents
+
Indexes
+
Replication
+
Oplog
+
Temporary working space
+
Backup
+
Growth
```

Monitor storage trends instead of waiting for disk utilization to reach critical levels.

Storage exhaustion can cause:

- write failures
- replication problems
- degraded performance
- member failures
- extended recovery times

---

## Working Set

MongoDB performance depends heavily on whether frequently accessed data and indexes fit effectively within available memory.

A workload with:

```text
100 GB collection
20 GB frequently accessed data
10 GB indexes
```

may behave very differently from one where the active working set is hundreds of gigabytes larger than available memory.

Monitor:

- memory utilization
- cache behavior
- page faults
- query latency
- disk I/O

Memory sizing should be based on measured workload behavior.

---

## Large Documents

Large documents can increase:

- network transfer
- memory consumption
- serialization cost
- update cost
- replication traffic

Avoid returning unnecessary fields.

Prefer projections:

```python
projection = {
    "_id": 1,
    "order_id": 1,
    "status": 1,
}
```

For API endpoints, do not retrieve an entire large document when the client needs only three fields.

---

## Pagination

Avoid deep offset pagination for large collections:

```javascript
db.orders
  .find(query)
  .skip(1000000)
  .limit(50)
```

Prefer cursor-based pagination.

Example:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  created_at: {
    $lt: last_seen_timestamp
  }
})
.sort({
  created_at: -1
})
.limit(50)
```

The exact pagination strategy should account for duplicate timestamps and stable ordering.

---

## Backup Architecture

Backups should be independent from ordinary replication.

A production strategy can include:

```text
MongoDB
   │
   ├── Replica Set
   │
   ├── Continuous / Managed Backup
   │
   └── Periodic Backup Validation
```

Backups should support the required:

- RPO
- RTO
- retention period
- compliance requirements
- recovery scenarios

---

## Logical Backups

`mongodump` can produce logical backups.

Example:

```bash
mongodump \
  --uri="$MONGODB_URI" \
  --out="/backup/mongodb"
```

Restore:

```bash
mongorestore \
  --uri="$RESTORE_MONGODB_URI" \
  "/backup/mongodb"
```

Logical backup and restore can be useful for smaller datasets and migration workflows.

For large production deployments, evaluate managed snapshots, physical backups, and point-in-time recovery capabilities appropriate to the deployment.

---

## Restore Testing

A backup that has never been restored should not be considered fully validated.

A restore test should verify:

```text
Backup exists
    ↓
Backup can be restored
    ↓
MongoDB starts correctly
    ↓
Collections exist
    ↓
Indexes exist
    ↓
Critical records exist
    ↓
Application can connect
    ↓
Critical workflows succeed
```

Record:

- restore duration
- data recovered
- failures
- operational steps
- actual RTO

---

## Disaster Recovery

A production DR strategy should explicitly define:

```text
RPO
RTO
Recovery Environment
Backup Source
Traffic Switching
Validation Procedure
Rollback Procedure
```

Example:

```text
Primary Region
      │
      ▼
Failure
      │
      ▼
Declare Incident
      │
      ▼
Recover MongoDB
      │
      ▼
Validate Data
      │
      ▼
Recover Application
      │
      ▼
Switch Traffic
      │
      ▼
Monitor
```

DR should be tested rather than documented only on paper.

---

## Deployment Strategies

MongoDB changes should be separated into categories.

| Change | Risk |
|---|---|
| Application query change | Medium |
| New index | Medium |
| Schema validation change | Medium |
| Replica configuration | High |
| Shard-key change | High |
| Resharding | High |
| MongoDB version upgrade | High |
| Storage migration | High |

High-risk changes should have:

- staging validation
- backups
- monitoring
- maintenance plan
- rollback/recovery plan
- explicit ownership

---

## MongoDB Version Upgrades

A production MongoDB upgrade should follow a controlled process.

Typical workflow:

```text
Review Compatibility
        ↓
Test Application
        ↓
Test Driver
        ↓
Test Queries
        ↓
Validate Backup
        ↓
Upgrade Staging
        ↓
Observe
        ↓
Upgrade Production
        ↓
Monitor
```

Do not upgrade the database and application driver simultaneously without testing compatibility.

---

## Rolling Changes

Replica sets can support controlled rolling maintenance.

A conceptual sequence is:

```text
Secondary 1
   ↓
Upgrade

Secondary 2
   ↓
Upgrade

Primary
   ↓
Controlled stepdown
   ↓
Upgrade
```

Exact upgrade procedures depend on MongoDB version and deployment model.

The principle is:

> Maintain a healthy majority and validate each step before proceeding.

---

## Docker and Kubernetes

Local Docker is useful for development.

Example:

```yaml
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
```

This is not a production HA configuration.

Production Kubernetes deployments require additional concerns:

- persistent volumes
- stable identities
- topology-aware scheduling
- anti-affinity
- disruption handling
- storage reliability
- backup
- monitoring
- upgrade procedures

For many organizations, MongoDB Atlas or another managed deployment can reduce operational complexity.

---

## Infrastructure as Code

Production MongoDB infrastructure should ideally be reproducible.

Use infrastructure-as-code tools where appropriate:

```text
Terraform
CloudFormation
Kubernetes manifests
Helm
```

Store infrastructure configuration in version control.

Do not store:

- passwords
- private keys
- production connection strings
- secrets

in the repository.

---

## CI/CD Integration

A database-aware CI/CD pipeline can include:

```text
Code Change
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
MongoDB Query Tests
   ↓
Migration / Index Validation
   ↓
Build
   ↓
Deploy Staging
   ↓
Smoke Tests
   ↓
Production Deployment
```

Production database changes should be decoupled from application deployment when they carry independent operational risk.

---

## Testing Strategy

A production MongoDB application should use multiple testing levels.

### Unit Tests

Test:

- service logic
- validation
- transformations
- error handling

### Integration Tests

Test:

- actual MongoDB queries
- indexes
- transactions
- repository behavior
- serialization

### Performance Tests

Test:

- query latency
- concurrent requests
- connection pools
- aggregation workloads
- failover

### Failure Tests

Test:

- primary failure
- connection failure
- transient errors
- replication lag
- backup restoration

---

## FastAPI Production Pattern

A simplified FastAPI architecture:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient

client: MongoClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client

    client = MongoClient(
        "mongodb://mongo1,mongo2,mongo3/app?replicaSet=rs0",
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )

    client.admin.command("ping")

    yield

    client.close()


app = FastAPI(lifespan=lifespan)
```

If synchronous PyMongo is used, database operations should be integrated carefully with FastAPI's execution model so that blocking operations do not unnecessarily block the event loop.

For an async application, use an appropriate asynchronous MongoDB driver approach supported by the application's current driver stack.

---

## Django Production Pattern

A Django service can use a repository abstraction:

```python
class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, order_id: str):
        return self.collection.find_one(
            {"order_id": order_id},
            {
                "_id": 0,
                "order_id": 1,
                "status": 1,
            },
        )
```

The service layer can then use:

```python
class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def get_order(self, order_id: str):
        return self.repository.get_by_id(order_id)
```

This keeps MongoDB-specific details outside views and business logic.

---

## MongoDB and Nginx

Nginx normally belongs in front of the HTTP application layer:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI / Django
  ↓
MongoDB
```

Do not expose MongoDB directly through an HTTP reverse proxy as a replacement for proper database networking and security.

Nginx should handle concerns such as:

- HTTP routing
- TLS termination where appropriate
- rate limiting
- request size controls
- load balancing

MongoDB should remain behind appropriate network boundaries.

---

## Operational Runbooks

Production teams should maintain runbooks for:

- primary failure
- secondary failure
- replication lag
- disk exhaustion
- connection exhaustion
- slow queries
- index problems
- backup failure
- restore
- accidental deletion
- credential rotation
- certificate rotation
- MongoDB upgrade
- shard addition
- shard removal
- regional failure

A runbook should contain:

```text
Symptom
↓
Impact
↓
Immediate checks
↓
Diagnostic commands
↓
Decision points
↓
Corrective action
↓
Validation
↓
Prevention
```

---

## Common Production Mistakes

### Single MongoDB Instance

```text
Application → One MongoDB server
```

This creates an obvious single point of failure.

Use a replica set for production HA where appropriate.

### Single Application Instance

A highly available database does not compensate for a single API server.

### Creating MongoClient Per Request

This causes unnecessary connection creation and resource consumption.

### No Timeouts

An unavailable database can cause requests to remain blocked for too long.

### No Query-Based Index Strategy

Indexes should be designed from actual query patterns.

### Over-Indexing

Every index adds storage and write overhead.

### Unbounded Arrays

Large documents eventually become operational problems.

### Unnecessary Transactions

Transactions can add latency and coordination overhead.

### Blind Secondary Reads

Stale reads can produce incorrect business behavior.

### No Backup Testing

A backup that cannot be restored is not a reliable recovery strategy.

### Production Secrets in Git

Credentials can leak through repository history and CI logs.

### Direct Application Connections to Shards

Applications in a sharded deployment should normally use `mongos`.

### Sharding Too Early

Sharding adds significant operational complexity.

### Treating Replication as Backup

Replicated bad data is still bad data.

---

## Interview Traps

### "MongoDB is production-ready because it supports replication."

Replication is only one component of a production architecture.

Production readiness also requires:

- HA topology
- application failover
- security
- monitoring
- backup
- recovery
- capacity planning

### "Three MongoDB nodes guarantee zero downtime."

Elections and transient network failures can still cause temporary request failures.

### "Adding indexes always improves performance."

Indexes improve some reads but increase storage and write overhead.

### "Sharding automatically makes queries faster."

Poorly targeted queries can become more expensive because multiple shards participate.

### "A secondary is a backup."

A secondary is a replicated database member, not an independent protection against logical corruption.

### "Transactions mean MongoDB should be modeled like PostgreSQL."

Transactions exist, but MongoDB's document model should still be used deliberately.

### "More replicas solve write scaling."

Replica sets provide redundancy and can support read scaling, but normal writes still go through the primary.

---

## Production Architecture Decision Matrix

| Requirement | Recommended Architecture |
|---|---|
| Local development | Single MongoDB / Docker |
| Small production workload | Replica set |
| High availability | Multi-AZ replica set |
| Read-heavy workload | Replica set + appropriate secondary reads |
| High write throughput | Optimize first, then evaluate sharding |
| Very large dataset | Evaluate sharding |
| Multi-region DR | Multi-region topology + independent backup strategy |
| Managed operations | MongoDB Atlas or equivalent managed deployment |
| Event-driven processing | Change streams / Kafka |
| Low-latency repeated reads | MongoDB + Redis |
| Analytical workload | Secondary / materialized results / analytics platform |
| Strong business invariants | Appropriate transactions + data modeling |

---

## Production Readiness Checklist

### Architecture

- [ ] Workload characteristics documented
- [ ] Access patterns documented
- [ ] Data model reviewed
- [ ] Replica topology designed
- [ ] Failure domains identified
- [ ] Sharding evaluated based on measured requirements

### Application

- [ ] Long-lived `MongoClient`
- [ ] Connection pooling configured
- [ ] Server-selection timeout configured
- [ ] Connection timeout configured
- [ ] Socket timeout configured
- [ ] Retry behavior tested
- [ ] Idempotency designed
- [ ] Repository/service boundaries defined

### Database

- [ ] Indexes derived from query patterns
- [ ] Slow queries monitored
- [ ] `explain()` used for critical queries
- [ ] Schema validation considered
- [ ] Transactions limited to required workflows
- [ ] Read/write concerns explicitly selected

### High Availability

- [ ] Replica set deployed
- [ ] Members distributed across failure domains
- [ ] Application failover tested
- [ ] Primary stepdown tested
- [ ] Replication lag monitored
- [ ] Capacity headroom maintained

### Security

- [ ] Authentication enabled
- [ ] Least-privilege users configured
- [ ] TLS configured
- [ ] Private networking configured
- [ ] Secrets stored securely
- [ ] Credentials rotated
- [ ] Security events monitored

### Operations

- [ ] Metrics collected
- [ ] Logs centralized
- [ ] Alerts configured
- [ ] Slow-query monitoring enabled
- [ ] Storage growth monitored
- [ ] Connection usage monitored
- [ ] Runbooks documented

### Backup and DR

- [ ] Backups configured
- [ ] Backup retention defined
- [ ] Restore tested
- [ ] RPO documented
- [ ] RTO documented
- [ ] Disaster-recovery procedure tested

### Deployment

- [ ] Infrastructure is reproducible
- [ ] Production configuration is version-controlled without secrets
- [ ] Database changes are reviewed
- [ ] Upgrade procedure documented
- [ ] Rollback/recovery procedure documented

---

## Senior-Level Architecture Review

Before approving a production MongoDB architecture, ask:

```text
What is the workload?
        ↓
What are the critical access patterns?
        ↓
How is the data modeled?
        ↓
What indexes support the workload?
        ↓
What happens when the primary fails?
        ↓
What happens when an AZ fails?
        ↓
What happens when MongoDB is unavailable?
        ↓
How does the application retry?
        ↓
Are retries idempotent?
        ↓
How is sensitive data protected?
        ↓
How is the system monitored?
        ↓
How is data backed up?
        ↓
Can the backup actually be restored?
        ↓
What is the RPO?
        ↓
What is the RTO?
        ↓
When does the architecture need sharding?
        ↓
Can the team operate all of this at 3 AM?
```

The final question is particularly important.

A technically sophisticated architecture that the team cannot troubleshoot, restore, upgrade, or operate reliably is not production-ready.

---

## Key Takeaways

- **Production MongoDB architecture is an end-to-end system involving data modeling, indexes, connection management, replication, security, observability, backups, recovery, and application behavior—not merely a database deployment.**
- **Replica sets provide the foundation for high availability, while sharding should be introduced only when measured storage or workload requirements justify horizontal scaling.**
- **Application architecture matters as much as database topology: use long-lived connection pools, explicit timeouts, appropriate consistency settings, retry-safe operations, and idempotent business workflows.**
- **Security, monitoring, backup, and disaster recovery must be designed as first-class production capabilities, with restore and failover procedures tested before incidents occur.**
- **A production architecture is successful only when it meets its performance, availability, security, RPO/RTO, and operational requirements while remaining understandable and maintainable by the engineering team.**