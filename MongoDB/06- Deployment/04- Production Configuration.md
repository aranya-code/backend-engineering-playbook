# 04- Production Configuration

## Overview

Production MongoDB configuration is the process of defining database runtime, networking, security, durability, connection, replication, and operational settings for a workload that must remain reliable under real traffic.

Production configuration is not simply a larger version of local configuration. The primary concerns are:

- Security and least privilege
- Durable storage
- High availability
- Predictable connection behavior
- Appropriate read and write guarantees
- Resource capacity
- Monitoring and alerting
- Backup and disaster recovery
- Controlled upgrades
- Operational safety

A typical backend architecture separates application configuration from database infrastructure:

```mermaid
flowchart LR
    Client[Clients]
    LB[Load Balancer / Nginx]
    API[API Services]
    Pool[MongoDB Driver Connection Pools]
    Mongo[MongoDB Replica Set]
    Backup[Backup / PITR]
    Monitor[Monitoring and Alerting]
    Secrets[Secret Manager]

    Client --> LB
    LB --> API
    API --> Pool
    Pool --> Mongo
    Mongo --> Backup
    Mongo --> Monitor
    Secrets --> API
    Secrets --> Mongo
```

The application should consume MongoDB through a controlled connection configuration rather than embedding infrastructure assumptions in application code.

## Production Configuration Principles

A production MongoDB deployment should follow these principles:

| Principle | Production approach |
|---|---|
| Security | Authentication, authorization, TLS, least privilege |
| Availability | Replica sets or managed high-availability deployment |
| Durability | Appropriate write concern and persistent storage |
| Connectivity | Stable DNS, controlled network paths, connection pooling |
| Performance | Access-pattern-driven indexes and bounded queries |
| Recovery | Tested backups and documented recovery procedures |
| Observability | Metrics, logs, alerts, query performance monitoring |
| Configuration | Externalized and version-controlled where safe |
| Secrets | Secret manager or protected runtime injection |
| Changes | Tested, staged, and reversible |
| Capacity | Planned for storage, memory, CPU, and connections |

## Configuration Layers

MongoDB production configuration exists at several layers.

```text
Application
    |
    +-- MongoDB URI
    +-- Driver timeouts
    +-- Pool configuration
    +-- Retry behavior
    |
Network
    |
    +-- DNS
    +-- Firewall
    +-- TLS
    |
MongoDB
    |
    +-- Authentication
    +-- Authorization
    +-- Replica set
    +-- Read/write concerns
    +-- Storage
    +-- Runtime settings
    |
Infrastructure
    |
    +-- CPU
    +-- Memory
    +-- Disk
    +-- Backup
    +-- Monitoring
```

A common senior-level mistake is configuring only MongoDB itself while ignoring the behavior of the application driver and infrastructure around it.

## Configuration Sources

Production configuration should be externalized from application source code.

Typical sources include:

- Environment variables
- Kubernetes Secrets
- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- CI/CD secret stores
- Platform-specific secret managers
- MongoDB deployment configuration

A typical application configuration might contain:

```text
MONGODB_URI
MONGODB_DATABASE
MONGODB_SERVER_SELECTION_TIMEOUT_MS
MONGODB_CONNECT_TIMEOUT_MS
MONGODB_SOCKET_TIMEOUT_MS
MONGODB_MAX_POOL_SIZE
MONGODB_MIN_POOL_SIZE
MONGODB_WAIT_QUEUE_TIMEOUT_MS
```

Do not place credentials directly in:

```python
MongoClient("mongodb://admin:password@...")
```

## MongoDB Connection URI

A production URI commonly looks like:

```text
mongodb://app_user:${PASSWORD}@mongo-1.example.internal:27017,mongo-2.example.internal:27017,mongo-3.example.internal:27017/orders?replicaSet=rs0&authSource=admin
```

For MongoDB Atlas, the URI may use the `mongodb+srv` scheme:

```text
mongodb+srv://app_user:${PASSWORD}@cluster.example.mongodb.net/orders
```

Important URI components include:

| Component | Purpose |
|---|---|
| Username | Database identity |
| Password | Authentication credential |
| Hosts | MongoDB topology entry points |
| Database | Default application database |
| `replicaSet` | Expected replica-set name |
| `authSource` | Database containing the user |
| TLS options | Encrypted connection configuration |
| Read preference | Controls eligible read nodes |
| Retry options | Controls retry behavior |

Do not copy a URI from one environment into another without reviewing its topology, credentials, and security settings.

## DNS and Stable Hostnames

Production applications should use stable DNS names rather than database IP addresses.

Prefer:

```text
mongodb://mongo-primary.internal.example:27017/orders
```

or a topology-aware URI.

Avoid hard-coding:

```text
mongodb://10.42.17.23:27017/orders
```

IP addresses can change because of:

- Failover
- Instance replacement
- Scaling
- Infrastructure migration
- Disaster recovery
- Cloud networking changes

For replica sets, the addresses advertised by MongoDB must be reachable by the clients.

## TLS

Production MongoDB connections should normally use TLS.

TLS protects:

```text
Application
    |
    | Encrypted connection
    v
MongoDB
```

without TLS:

```text
Application
    |
    | Potentially observable database traffic
    v
MongoDB
```

A production TLS configuration should consider:

- Certificate authority
- Server certificates
- Client certificate authentication where required
- Certificate rotation
- Hostname validation
- Certificate expiration monitoring

For PyMongo, TLS configuration can be supplied through the URI or client options.

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    tls=True,
    serverSelectionTimeoutMS=5000,
)
```

For certificate-based validation, configure the appropriate CA file rather than disabling certificate verification.

Avoid:

```python
tlsAllowInvalidCertificates=True
```

as a production workaround.

## Authentication

Authentication answers:

> Who is connecting?

Authorization answers:

> What is that identity allowed to do?

Production deployments should separate administrative identities from application identities.

Example:

```text
MongoDB
 |
 +-- Platform Admin
 |      |
 |      +-- Database administration
 |
 +-- Application User
        |
        +-- orders: readWrite
        +-- analytics: read
```

The API should not use a global administrative account.

## Least Privilege

An application user should receive only the permissions required by the application.

For example:

```javascript
use orders

db.createUser({
  user: "orders_api",
  pwd: passwordFromSecretManager,
  roles: [
    {
      role: "readWrite",
      db: "orders"
    }
  ]
})
```

The exact roles should be based on actual application operations.

If an application only reads data, do not grant:

```text
readWrite
```

when:

```text
read
```

is sufficient.

## Secret Management

Database credentials are production secrets.

Do not commit:

```text
mongodb://admin:ProductionPassword@...
```

to:

- Git
- Docker images
- Application source
- Terraform state without appropriate controls
- CI logs
- Debug output
- Configuration repositories intended to be public

A typical cloud deployment might use:

```mermaid
flowchart LR
    SecretManager[Secret Manager]
    Workload[API Workload]
    Driver[MongoDB Driver]
    Mongo[MongoDB]

    SecretManager --> Workload
    Workload --> Driver
    Driver --> Mongo
```

The workload retrieves credentials at runtime or receives them through a protected secret-injection mechanism.

## Credential Rotation

Credential rotation should not require rebuilding the application.

A robust approach is:

```text
Create New Credential
        ↓
Deploy Configuration
        ↓
Verify New Credential
        ↓
Switch Application
        ↓
Revoke Old Credential
        ↓
Monitor
```

If the application maintains long-lived MongoDB clients, credential rotation procedures must account for existing connections and connection-pool behavior.

## Connection Pooling

MongoDB drivers maintain connection pools.

For PyMongo:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    maxPoolSize=100,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

The values above are examples, not universal production defaults.

Pool sizing should be based on:

- Application concurrency
- Number of application instances
- Request latency
- Database capacity
- Number of MongoDB servers
- Workload characteristics

Do not multiply `maxPoolSize` by one application instance and assume that is the total number of database connections.

A deployment with multiple application processes can create substantially more connections:

```text
Application Instance 1
    └── MongoDB Pool

Application Instance 2
    └── MongoDB Pool

Application Instance 3
    └── MongoDB Pool
```

Therefore capacity planning must consider the entire application fleet.

## Connection Pool Configuration

Important PyMongo settings include:

| Setting | Purpose |
|---|---|
| `maxPoolSize` | Maximum pooled connections per server |
| `minPoolSize` | Minimum maintained pool size |
| `maxConnecting` | Limits concurrent connection establishment |
| `waitQueueTimeoutMS` | Maximum time waiting for a pool connection |
| `serverSelectionTimeoutMS` | Maximum time selecting a suitable server |
| `connectTimeoutMS` | Connection establishment timeout |
| `socketTimeoutMS` | Socket operation timeout |

Avoid selecting values simply because they appear in an example online.

A useful production workflow is:

```text
Measure workload
    ↓
Estimate concurrency
    ↓
Configure pool
    ↓
Load test
    ↓
Monitor connection utilization
    ↓
Adjust
```

## Timeout Strategy

Timeouts prevent a degraded database or network from causing requests to wait indefinitely.

Common timeout categories include:

```text
Application Request Timeout
        |
        +-- Server Selection Timeout
        +-- Connection Timeout
        +-- Socket Timeout
        +-- Pool Wait Timeout
```

These timeouts serve different purposes.

For example:

```python
client = MongoClient(
    mongodb_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    waitQueueTimeoutMS=2000,
)
```

The values should align with the application's latency budget.

A database timeout should generally be shorter than the upstream timeout when the application needs to fail fast.

## Retry Behavior

MongoDB drivers support retryable operations in appropriate circumstances.

Retries must not be treated as a universal solution to database failures.

Consider:

- Operation idempotency
- Retryable writes
- Transaction retry behavior
- Application request retries
- Duplicate side effects
- Timeout semantics
- Backoff

A problematic architecture is:

```text
HTTP Retry
    ↓
Application Retry
    ↓
MongoDB Driver Retry
    ↓
Database
```

Multiple retry layers can amplify load during an incident.

Prefer bounded retries with backoff and clear ownership of retry behavior.

## Write Concern

Write concern determines how strongly MongoDB acknowledges writes.

Common concepts include:

```text
w: 1
w: "majority"
w: 0
```

A simplified comparison:

| Write concern | Characteristics |
|---|---|
| `w: 0` | Client does not wait for write acknowledgment |
| `w: 1` | Acknowledgment from primary |
| `w: "majority"` | Acknowledgment after majority requirements are satisfied |

For important production data, majority acknowledgement is often appropriate, but the correct choice depends on the application's durability and latency requirements.

Do not select a write concern without considering:

- RPO
- Latency
- Replica topology
- Failure behavior
- Business criticality

## Read Concern

Read concern controls consistency and durability guarantees for reads.

Common levels include:

- `local`
- `available`
- `majority`
- `linearizable`
- `snapshot`

The appropriate level depends on the operation.

For example:

```text
Dashboard Read
    → May tolerate slightly different visibility semantics

Financial State Transition
    → Requires stronger consistency guarantees
```

Do not automatically use the strongest possible read concern everywhere because stronger guarantees can affect latency and availability characteristics.

## Read Preference

Read preference determines which replica-set members can serve reads.

Common modes include:

| Mode | Typical use |
|---|---|
| `primary` | Strong default for application reads |
| `primaryPreferred` | Prefer primary, allow fallback |
| `secondary` | Read from secondaries |
| `secondaryPreferred` | Prefer secondaries |
| `nearest` | Choose low-latency eligible member |

Secondary reads introduce important considerations:

- Replication lag
- Stale reads
- Read-after-write behavior
- Geographic topology
- Operational complexity

Do not use secondary reads simply to increase throughput without measuring whether the workload can tolerate the consistency implications.

## Replica Set Configuration

Production MongoDB should normally use a replica set when high availability is required.

```mermaid
flowchart LR
    API[Application]
    P[Primary]
    S1[Secondary]
    S2[Secondary]

    API --> P
    P --> S1
    P --> S2
```

The primary handles writes under normal operation.

Secondaries replicate the primary's operations.

If the primary becomes unavailable, an eligible secondary can be elected.

The deployment should provide independent failure domains where possible.

## Failure Domains

A replica set with three members on the same physical host does not provide meaningful host-level high availability.

Prefer:

```text
Availability Zone A
    MongoDB Member

Availability Zone B
    MongoDB Member

Availability Zone C
    MongoDB Member
```

where the infrastructure platform and MongoDB architecture support this topology.

The exact topology depends on:

- Region
- Availability zones
- Network latency
- Election requirements
- Cost
- Disaster recovery objectives

## Arbiter Considerations

Arbiters participate in elections but do not store a copy of the data.

They should not be treated as a substitute for a data-bearing replica.

For production architectures, data-bearing members are generally preferred when capacity and failure-domain requirements permit.

## Storage Configuration

MongoDB storage performance directly affects database latency.

Production storage planning should consider:

- Capacity
- IOPS
- Throughput
- Latency
- Filesystem behavior
- Growth rate
- Journal behavior
- Backup requirements

A database can have sufficient CPU and memory while still being storage-bound.

Monitor:

```text
Disk Utilization
Disk Latency
IOPS
Throughput
Storage Growth
```

## Working Set and Memory

MongoDB performance is strongly influenced by whether frequently accessed data and indexes fit effectively within available memory.

A simplified model:

```text
RAM
 |
 +-- MongoDB / WiredTiger
 |      |
 |      +-- Frequently accessed data
 |      +-- Indexes
 |
 +-- Operating System
 |
 +-- Other Processes
```

Do not allocate all host memory to MongoDB without considering the operating system and other required processes.

Memory sizing should be validated using actual workload metrics.

## Index Configuration

Production indexes should come from real access patterns.

For example:

```javascript
db.orders.createIndex({
  customer_id: 1,
  status: 1,
  created_at: -1
})
```

This may support a query such as:

```javascript
db.orders.find({
  customer_id: ObjectId("64b000000000000000000001"),
  status: "PAID"
}).sort({
  created_at: -1
})
```

Index design should consider:

- Equality predicates
- Sort requirements
- Range predicates
- Selectivity
- Cardinality
- Write overhead
- Index size
- Query frequency

Do not create indexes merely because a field appears in a document.

## Index Lifecycle

Production index management should be deliberate.

A typical lifecycle is:

```text
Observe Query
    ↓
Capture Query Shape
    ↓
Analyze Explain Plan
    ↓
Design Candidate Index
    ↓
Measure
    ↓
Deploy
    ↓
Monitor
    ↓
Retain / Modify / Remove
```

Unused indexes consume storage and increase write overhead.

Index changes should be treated as production changes, not harmless configuration edits.

## Schema Validation

MongoDB's flexible document model does not mean production data should have no constraints.

JSON Schema validation can enforce important invariants.

Example:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "status", "created_at"],
      properties: {
        customer_id: {
          bsonType: "objectId"
        },
        status: {
          enum: ["PENDING", "PAID", "CANCELLED"]
        },
        created_at: {
          bsonType: "date"
        }
      }
    }
  }
})
```

Validation should complement application-level validation.

Use database validation to protect important data invariants, especially when multiple services or tools can write to the database.

## Production Configuration With Python

A production configuration object can centralize driver settings.

```python
import os
from dataclasses import dataclass

from pymongo import MongoClient


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database: str
    server_selection_timeout_ms: int = 5000
    connect_timeout_ms: int = 5000
    socket_timeout_ms: int = 10000
    max_pool_size: int = 100
    min_pool_size: int = 10
    wait_queue_timeout_ms: int = 2000


settings = MongoSettings(
    uri=os.environ["MONGODB_URI"],
    database=os.environ["MONGODB_DATABASE"],
)

client = MongoClient(
    settings.uri,
    serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
    connectTimeoutMS=settings.connect_timeout_ms,
    socketTimeoutMS=settings.socket_timeout_ms,
    maxPoolSize=settings.max_pool_size,
    minPoolSize=settings.min_pool_size,
    waitQueueTimeoutMS=settings.wait_queue_timeout_ms,
)

db = client[settings.database]
```

The application should create and reuse the client rather than constructing a new client for each request.

## FastAPI Production Configuration

FastAPI applications can initialize the MongoDB client during application startup.

```python
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MongoClient(
        os.environ["MONGODB_URI"],
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=100,
    )

    client.admin.command("ping")

    app.state.mongo_client = client
    app.state.mongo_db = client[os.environ["MONGODB_DATABASE"]]

    try:
        yield
    finally:
        client.close()


app = FastAPI(lifespan=lifespan)
```

If the application uses an asynchronous MongoDB client, the lifecycle and concurrency model should be designed around that client's async semantics rather than mixing blocking database operations into an async request path.

## Django Production Configuration

For Django applications using MongoDB through PyMongo or a compatible integration layer, keep MongoDB configuration separate from Django's relational database configuration when both are present.

Example:

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DATABASE = os.environ["MONGODB_DATABASE"]
```

A repository layer can then encapsulate MongoDB access:

```text
Django View
    ↓
Service Layer
    ↓
Repository
    ↓
PyMongo
    ↓
MongoDB
```

This avoids spreading MongoDB-specific connection and query logic throughout views and business logic.

## Kubernetes Configuration

A Kubernetes workload should normally receive MongoDB configuration through environment variables or mounted secrets.

Conceptually:

```yaml
env:
  - name: MONGODB_URI
    valueFrom:
      secretKeyRef:
        name: mongodb
        key: uri
```

Do not place production credentials directly in Deployment manifests committed to source control.

Kubernetes itself does not solve MongoDB high availability, backup, or database operations. If MongoDB is self-managed on Kubernetes, persistent storage, topology, upgrades, backup, and failure handling must be explicitly designed.

## Network Security

MongoDB should not be directly reachable from the public internet unless there is an exceptional and explicitly designed requirement.

A typical architecture is:

```text
Internet
   |
   v
Load Balancer
   |
   v
Application Network
   |
   v
MongoDB Private Network
```

MongoDB should generally be placed behind:

- Private subnets
- Security groups
- Network ACLs where appropriate
- Private endpoints or private connectivity
- Firewall rules
- TLS

Only required application networks should be able to reach MongoDB.

## AWS-Oriented Architecture

A self-managed MongoDB deployment on AWS may look like:

```mermaid
flowchart TB
    Internet[Internet]
    ALB[Application Load Balancer]
    App1[API Instance]
    App2[API Instance]

    subgraph VPC
        subgraph PrivateA[Private Subnet AZ-A]
            M1[MongoDB Member]
        end

        subgraph PrivateB[Private Subnet AZ-B]
            M2[MongoDB Member]
        end

        subgraph PrivateC[Private Subnet AZ-C]
            M3[MongoDB Member]
        end

        Backup[(Backup Storage)]
    end

    Internet --> ALB
    ALB --> App1
    ALB --> App2
    App1 --> M1
    App2 --> M1
    M1 --> M2
    M1 --> M3
    M1 --> Backup
```

For many teams, MongoDB Atlas can reduce the operational burden of managing the database infrastructure itself. The decision should be based on requirements, cost, compliance, network architecture, and operational capabilities.

## Environment Separation

Production should not share credentials or database infrastructure with development.

A useful separation is:

| Environment | Database | Credentials | Data |
|---|---|---|---|
| Development | Development MongoDB | Dev secrets | Synthetic |
| Test | Ephemeral/test MongoDB | Test secrets | Generated |
| Staging | Staging cluster | Staging secrets | Controlled |
| Production | Production cluster | Production secrets | Production |

Do not use production credentials in staging simply because it makes testing easier.

## Configuration Drift

Configuration drift occurs when environments gradually stop matching their intended configuration.

Examples include:

- Different MongoDB versions
- Different index definitions
- Different TLS settings
- Different authentication policies
- Different replica-set settings
- Different connection timeout values

Use infrastructure-as-code and configuration management where appropriate.

Database schema and index changes should also have a controlled deployment process.

## Database Initialization and Migrations

MongoDB does not require relational-style schema migrations for every schema change, but production applications still need controlled database changes.

Examples:

- Create indexes
- Update validation rules
- Backfill fields
- Transform documents
- Create collections
- Change application-visible schema

A safe migration pattern is:

```text
Deploy Backward-Compatible Application
        ↓
Apply Database Change
        ↓
Backfill / Verify
        ↓
Enable New Application Behavior
        ↓
Remove Legacy Structure
```

Avoid application deployments that require an instantaneous destructive schema transformation across a very large collection.

## Rolling Changes

For a replica-set deployment, changes should be designed so that individual members can be updated without causing unnecessary downtime.

A controlled operational workflow is:

```text
Validate Change
    ↓
Backup / Recovery Check
    ↓
Update One Member
    ↓
Verify Health
    ↓
Continue Through Topology
    ↓
Verify Replica Set
    ↓
Verify Application
```

The exact procedure depends on the deployment platform and MongoDB topology.

## Monitoring

Production MongoDB monitoring should cover both database health and application behavior.

Important signals include:

| Area | Examples |
|---|---|
| Availability | Replica health, elections, server availability |
| Replication | Lag, oplog window |
| Connections | Current connections, pool pressure |
| Performance | Query latency, slow operations |
| Storage | Disk usage, growth, I/O |
| Memory | Working set and memory pressure |
| Operations | Read/write throughput |
| Indexes | Size, usage, maintenance cost |
| Errors | Authentication, network, command failures |
| Backups | Success, freshness, restore validation |

Monitoring should focus on symptoms that affect application behavior, not only infrastructure utilization.

## Logging

MongoDB logs should be centralized where practical.

Logs can help investigate:

- Connection failures
- Authentication errors
- Elections
- Replication issues
- Slow operations
- Storage issues
- Configuration problems

Avoid logging sensitive credentials or connection strings containing passwords.

## Alerting

Alerts should be actionable.

Examples:

```text
Replica member unavailable
Replication lag exceeds threshold
Disk capacity approaching limit
Backup failed
Backup freshness exceeds RPO
Connection pool saturation
Sustained query latency increase
Oplog window approaching recovery requirement
```

Avoid alerting on every low-level metric without understanding whether it represents an actionable failure.

## Backup Configuration

Production configuration must include recovery planning.

A complete strategy considers:

- Backup frequency
- Retention
- Logical vs physical backup
- Point-in-time recovery
- Off-site storage
- Encryption
- Restore validation
- RPO
- RTO

The existence of a successful backup job does not prove that recovery will succeed.

Test restoration independently.

## Disaster Recovery

High availability and disaster recovery solve different problems.

```text
High Availability
    ↓
Survive component failure

Disaster Recovery
    ↓
Recover from larger-scale failure
```

A replica set can protect against some member failures but does not replace:

- Independent backups
- Cross-region recovery where required
- Restore procedures
- Recovery testing

## Capacity Planning

Capacity planning should include:

```text
Current Workload
    +
Growth Rate
    +
Peak Traffic
    +
Replication Overhead
    +
Index Growth
    +
Backup Requirements
    +
Recovery Requirements
```

Track:

- Collection size
- Index size
- Storage growth
- Operations per second
- Query latency
- Connections
- CPU
- Memory
- Disk I/O
- Replication lag

Do not wait for disk exhaustion or connection saturation before planning capacity.

## Production Performance Workflow

When a production query becomes slow:

```text
Observe Latency Increase
        ↓
Identify Query Shape
        ↓
Run explain("executionStats")
        ↓
Check Index Usage
        ↓
Check Data Distribution
        ↓
Check Working Set / Memory
        ↓
Check Server Resources
        ↓
Optimize
        ↓
Measure Again
```

Example:

```javascript
db.orders.find({
  customer_id: ObjectId("64b000000000000000000001"),
  status: "PAID"
}).sort({
  created_at: -1
}).explain("executionStats")
```

Focus on:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

A query returning 20 documents but examining millions of documents is a strong candidate for investigation.

## Production Pitfalls

### Over-Sized Connection Pools

Large pools multiplied across many application instances can exhaust MongoDB connection capacity.

### Excessive Retries

Retries can convert a transient database problem into a larger outage by multiplying traffic.

### Secondary Reads Without Consistency Analysis

Reading from secondaries can expose replication lag.

### Missing Index Governance

Indexes improve reads but consume storage and increase write overhead.

### Public MongoDB Exposure

Exposing port `27017` to the internet creates unnecessary attack surface.

### Root Application Credentials

Administrative credentials dramatically increase the impact of application compromise.

### No Restore Testing

A backup that has never been restored is an unverified recovery mechanism.

### Configuration Drift

Small differences between staging and production can produce failures that are difficult to reproduce.

### Treating MongoDB Configuration as Static

Connection pools, capacity, indexes, storage, and workload characteristics change over time. Production configuration should be continuously validated against observed behavior.

## Troubleshooting

### Connection Timeout

```text
Symptom
↓
Application cannot connect or requests time out
↓
Possible causes
↓
DNS failure
Network restriction
TLS failure
Incorrect hostname
MongoDB unavailable
Pool exhaustion
Server selection timeout too low
↓
Isolation strategy
↓
Validate DNS, network reachability, MongoDB health, TLS, and pool metrics independently
↓
Diagnostic commands
```

```bash
mongosh "$MONGODB_URI" --eval 'db.runCommand({ ping: 1 })'
```

```bash
nslookup mongo.example.internal
```

```text
Root cause
↓
Identify whether failure occurs during DNS, TCP/TLS connection, server selection, or pool acquisition
↓
Corrective action
↓
Fix the specific infrastructure or driver configuration issue
↓
Prevention
↓
Monitor connection failures and pool pressure and test failure scenarios
```

### Authentication Failure

```text
Symptom
↓
MongoDB rejects application credentials
↓
Possible causes
↓
Wrong username
Wrong password
Wrong authSource
Expired or rotated credential
Incorrect secret injection
↓
Isolation strategy
↓
Verify secret source and authentication database without exposing credentials in logs
↓
Diagnostic commands
```

```bash
mongosh "$MONGODB_URI" --eval 'db.runCommand({ connectionStatus: 1 })'
```

```text
Root cause
↓
Credential or authentication configuration mismatch
↓
Corrective action
↓
Correct secret, authSource, or user configuration
↓
Prevention
↓
Automate credential rotation and validate configuration during deployment
```

### Replica Set Member Unavailable

```text
Symptom
↓
Replica-set health reports an unavailable member
↓
Possible causes
↓
Host failure
Network failure
Disk failure
MongoDB process failure
Certificate problem
Resource exhaustion
↓
Isolation strategy
↓
Check member state, logs, host health, storage, and network
↓
Diagnostic commands
```

```javascript
rs.status()
```

```javascript
rs.conf()
```

```text
Root cause
↓
Determine whether the failure is process, host, network, storage, or configuration related
↓
Corrective action
↓
Restore the affected member or replace it according to the operational runbook
↓
Prevention
↓
Monitor replica health and rehearse member-recovery procedures
```

### Replication Lag

```text
Symptom
↓
Secondary members fall behind the primary
↓
Possible causes
↓
Insufficient disk I/O
CPU pressure
Large write workload
Network latency
Slow secondary
Long-running operations
↓
Isolation strategy
↓
Compare primary throughput, secondary resources, and replication metrics
↓
Diagnostic commands
```

```javascript
rs.printSecondaryReplicationInfo()
```

```javascript
rs.status()
```

```text
Root cause
↓
Secondary cannot process replicated operations quickly enough
↓
Corrective action
↓
Address resource bottleneck, workload, topology, or capacity issue
↓
Prevention
↓
Monitor lag and maintain sufficient resource headroom
```

## Production Configuration Checklist

### Connectivity

- [ ] Stable DNS names are used.
- [ ] MongoDB is reachable only from required networks.
- [ ] TLS is enabled where required.
- [ ] Certificate validation is enforced.
- [ ] Connection timeouts are configured.
- [ ] Pool settings are sized for the complete application fleet.

### Security

- [ ] Authentication is enabled.
- [ ] Application identities use least privilege.
- [ ] Administrative credentials are separated.
- [ ] Secrets are stored outside source code.
- [ ] Credential rotation is documented.
- [ ] MongoDB is not unnecessarily exposed publicly.

### Replica Set

- [ ] Replica-set topology meets availability requirements.
- [ ] Members use appropriate failure domains.
- [ ] Advertised member addresses are reachable.
- [ ] Write concern is appropriate for the workload.
- [ ] Read preference is intentional.
- [ ] Replication lag is monitored.

### Performance

- [ ] Production query patterns have appropriate indexes.
- [ ] Indexes are reviewed periodically.
- [ ] Query performance is monitored.
- [ ] Connection pools are sized deliberately.
- [ ] Memory and working-set behavior are understood.
- [ ] Storage performance is sufficient.

### Reliability

- [ ] Backups are configured.
- [ ] Backup freshness is monitored.
- [ ] Restore procedures are documented.
- [ ] Recovery testing is performed.
- [ ] RPO and RTO are defined.
- [ ] Disaster recovery requirements are understood.

### Operations

- [ ] MongoDB logs are centralized where appropriate.
- [ ] Replica health is monitored.
- [ ] Storage growth is monitored.
- [ ] Connection pressure is monitored.
- [ ] Alerts are actionable.
- [ ] MongoDB upgrades are tested before production rollout.
- [ ] Configuration changes are controlled and auditable.

## Interview Focus

| Question | Key point |
|---|---|
| What belongs in production MongoDB configuration? | Security, connectivity, replication, durability, performance, storage, monitoring, and recovery |
| Why should MongoDB use stable DNS names? | IP addresses can change during failover or infrastructure replacement |
| Why is TLS important? | It protects MongoDB traffic and credentials in transit |
| Why should applications avoid root credentials? | Least privilege limits the impact of application compromise |
| Why is connection-pool sizing important? | Each application process can create a pool and the fleet can exhaust database connection capacity |
| What is the difference between read concern and read preference? | Read concern controls read guarantees; read preference controls eligible replica-set members |
| Why use `w: "majority"`? | It can provide stronger durability semantics than acknowledging only the primary |
| Why can secondary reads be dangerous? | Secondaries can lag behind the primary |
| Why does a replica set need appropriate failure domains? | Multiple members on the same failure domain can fail together |
| Why are backups not sufficient without restore testing? | A backup artifact does not prove that recovery is operationally possible |
| Why should indexes be reviewed? | Indexes consume storage and add write and maintenance overhead |
| Why are timeouts important? | They prevent stalled network/database operations from consuming application resources indefinitely |

## Key Takeaways

- **Production MongoDB configuration is an end-to-end system concern spanning the driver, network, database, storage, security, monitoring, and recovery architecture.**
- **Use stable topology-aware connectivity, TLS, least-privilege identities, deliberate connection pools, and bounded timeouts rather than relying on local-development defaults.**
- **Replica-set topology, read/write concerns, and storage design must be selected according to availability, consistency, durability, and latency requirements.**
- **Performance configuration should be driven by real query patterns, connection usage, working-set behavior, storage metrics, and measured workload rather than arbitrary tuning values.**
- **A production configuration is incomplete without tested backups, recovery procedures, monitoring, capacity planning, secret management, and a controlled upgrade process.**