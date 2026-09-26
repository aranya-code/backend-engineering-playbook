# 15- Architecture Questions

## Overview

MongoDB architecture questions evaluate whether an engineer can design a system around MongoDB rather than simply use MongoDB APIs.

At senior level, the discussion should cover:

- Data modeling
- Access patterns
- Indexing
- Read and write paths
- Replica sets
- Consistency
- Transactions
- Caching
- Sharding
- Event-driven integration
- Failure handling
- Security
- Capacity planning
- Backup and recovery
- Operational ownership

A strong architecture answer starts with requirements and workload characteristics rather than immediately selecting MongoDB features.

```text
Business Requirements
        ↓
Access Patterns
        ↓
Data Model
        ↓
Query Patterns
        ↓
Indexes
        ↓
Read / Write Strategy
        ↓
Consistency Requirements
        ↓
Replication / HA
        ↓
Scaling Strategy
        ↓
Operations / DR
```

## Architecture Decision Framework

Before designing a MongoDB architecture, establish:

| Concern | Questions |
|---|---|
| Workload | Read-heavy, write-heavy, or mixed? |
| Data volume | How large is the dataset today and in 1–3 years? |
| Traffic | Requests/sec and peak traffic? |
| Query patterns | Which queries are latency-sensitive? |
| Consistency | Strong, eventual, or operation-specific? |
| Availability | Required uptime and failure tolerance? |
| Latency | Target p50/p95/p99? |
| Transactions | Are multi-document atomic operations required? |
| Growth | Vertical, horizontal, or both? |
| Geography | Single region or global? |
| Security | Authentication, authorization, encryption, audit requirements? |
| Recovery | RPO and RTO? |
| Operations | Who manages upgrades, backups, scaling, and incidents? |

The most important senior-level principle is:

> Design MongoDB around application access patterns, not around abstract entities alone.

## MongoDB Architecture Building Blocks

A production MongoDB deployment commonly consists of:

```mermaid
flowchart LR
    Client[Clients] --> API[API Service]
    API --> Driver[MongoDB Driver]
    Driver --> Router[MongoDB Router / Direct Connection]
    Router --> Primary[(Primary)]
    Router --> Secondary1[(Secondary)]
    Router --> Secondary2[(Secondary)]
    Primary --> Oplog[(Oplog)]
    Oplog --> Secondary1
    Oplog --> Secondary2
```

For a replica set:

- One member normally serves as primary.
- Secondaries replicate from the primary.
- Elections can select a new primary.
- The oplog records replicated operations.
- Clients use the driver's topology discovery and retry mechanisms.

For a sharded deployment:

```mermaid
flowchart LR
    App[Application] --> Mongos[mongos]
    Mongos --> Shard1[Shard 1]
    Mongos --> Shard2[Shard 2]
    Mongos --> Shard3[Shard 3]
    Mongos --> Config[Config Server Replica Set]
```

Each shard is itself normally a replica set.

## Architecture Question: Design a MongoDB Backend for a REST API

### Requirements

Assume:

- FastAPI service
- 10,000 requests/sec peak
- Mostly reads
- User and order data
- p95 API latency target below 200 ms
- High availability required
- Horizontal application scaling
- AWS deployment

### Architecture

```mermaid
flowchart LR
    User[Clients] --> ALB[Load Balancer]
    ALB --> API1[FastAPI]
    ALB --> API2[FastAPI]
    ALB --> APIN[FastAPI]
    
    API1 --> Redis[(Redis)]
    API2 --> Redis
    APIN --> Redis

    API1 --> Mongo[(MongoDB Replica Set)]
    API2 --> Mongo
    APIN --> Mongo

    Mongo --> Primary[(Primary)]
    Mongo --> S1[(Secondary)]
    Mongo --> S2[(Secondary)]

    Primary --> Backup[Managed Backup / PITR]
```

### Design Considerations

Application instances should be stateless.

MongoDB should provide:

- Durable storage
- Replica-set high availability
- Appropriate indexes
- Connection pooling
- Backup and recovery

Redis may be used for:

- Hot objects
- Expensive read results
- Rate limiting
- Short-lived derived state

Caching should not be introduced automatically. First determine whether MongoDB and its indexes can satisfy the latency requirement.

## Architecture Question: Design a User Profile System

### Access Pattern

Typical operations:

```text
Get user by ID
Update profile
Get user preferences
Search users by email
```

A document could be:

```json
{
  "_id": "ObjectId(...)",
  "email": "user@example.com",
  "name": "Alice",
  "profile": {
    "timezone": "Asia/Kolkata",
    "language": "en"
  },
  "preferences": {
    "email_notifications": true,
    "marketing": false
  }
}
```

### Indexes

If email lookup is common:

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

### Architecture Reasoning

Embedding profile and preference data can be appropriate when:

- They are usually read together.
- They have bounded size.
- They share lifecycle ownership.

Separate collections become more attractive when:

- Data has independent lifecycle.
- Data is independently queried.
- Data can grow without a practical bound.
- Different services own the data.

## Architecture Question: Embed or Reference?

The decision should be driven by access patterns.

| Requirement | Typical Direction |
|---|---|
| Always read together | Embed |
| Small bounded child data | Embed |
| Child has independent lifecycle | Reference |
| Unbounded child collection | Reference |
| Frequently updated independently | Reference |
| Strong ownership boundary | Reference |
| Read-heavy aggregate | Often embed |
| Large many-to-many relationship | Usually reference |

### Example

An order may embed line items:

```json
{
  "_id": "order-123",
  "customer_id": "customer-456",
  "items": [
    {
      "product_id": "product-1",
      "name": "Keyboard",
      "quantity": 2,
      "unit_price": 75
    }
  ]
}
```

The historical product name and price are intentionally duplicated.

This is controlled denormalization because the order needs the historical values even if the current product changes.

## Architecture Question: Design a Multi-Tenant SaaS Database

A common model is:

```json
{
  "_id": "ObjectId(...)",
  "tenant_id": "tenant-123",
  "status": "active",
  "created_at": "..."
}
```

Every tenant-scoped query should include:

```javascript
{
  tenant_id: "tenant-123"
}
```

### Index Strategy

For common tenant queries:

```javascript
db.orders.createIndex({
  tenant_id: 1,
  created_at: -1
})
```

### Isolation

Application-level tenant filtering should not be the only protection.

Use:

- Explicit repository boundaries
- Tenant-aware service methods
- Authorization checks
- Tests for cross-tenant access
- Auditing
- Carefully designed indexes

### Large Tenant Problem

If one tenant becomes much larger than others, a simple tenant-based model may create a hotspot.

Possible approaches include:

- Workload isolation
- Tenant-specific collections only when justified
- Dedicated database deployment
- Sharding
- Partitioning strategy based on actual access patterns

Do not introduce tenant-specific infrastructure prematurely.

## Architecture Question: Design an Order Management System

### Requirements

- Create orders
- Add line items
- Read order history
- Update order status
- Preserve historical pricing
- High read volume
- Moderate writes

### Document Design

```json
{
  "_id": "order-123",
  "customer_id": "customer-456",
  "status": "confirmed",
  "created_at": "2026-09-27T10:00:00Z",
  "items": [
    {
      "product_id": "product-1",
      "name": "Keyboard",
      "quantity": 2,
      "unit_price": 75
    }
  ],
  "total": 150
}
```

### Why Embed Items?

The application frequently needs:

```text
Order + line items
```

in one read.

Embedding avoids a second query for normal order retrieval.

### Potential Problem

If orders can contain an unbounded number of items, the model needs reconsideration.

Document growth is a schema-design constraint.

## Architecture Question: Design a Social Feed

### Requirements

- Users follow other users.
- Users publish posts.
- Users read a feed.
- High read volume.
- Potentially high write volume.

A naïve approach is to construct every feed dynamically:

```text
Read followers
↓
Find posts
↓
Sort
↓
Merge
↓
Return
```

At scale this can become expensive.

### Possible Architecture

Use precomputed feed entries:

```text
Post Created
    ↓
Kafka / Event Bus
    ↓
Feed Workers
    ↓
Feed Storage
    ↓
Redis / MongoDB
    ↓
Feed API
```

MongoDB may store durable feed entries while Redis can serve hot feeds.

### Trade-off

Fan-out-on-write:

```text
Fast reads
Higher write amplification
```

Fan-out-on-read:

```text
Lower write amplification
More expensive reads
```

The correct choice depends on follower distribution and workload.

## Architecture Question: Design a Product Catalog

### Requirements

- Millions of products
- Read-heavy
- Search and filtering
- Product attributes vary by category
- High availability

MongoDB's flexible document model can represent category-specific attributes:

```json
{
  "_id": "product-123",
  "category": "laptop",
  "name": "Example Laptop",
  "attributes": {
    "ram_gb": 32,
    "storage_gb": 1024,
    "screen_size": 15.6
  }
}
```

### Architecture

```text
Catalog API
   ↓
Redis Cache
   ↓
MongoDB
   ↓
Search System
```

MongoDB should not automatically be treated as a replacement for a specialized search engine when search requirements become complex.

For advanced search requirements, a dedicated search system may be appropriate.

## Architecture Question: Design a High-Availability MongoDB Deployment

A typical replica-set architecture:

```mermaid
flowchart TB
    App[Application] --> Primary[(Primary)]
    App --> SecondaryRead[(Secondary Reads)]

    Primary --> S1[(Secondary)]
    Primary --> S2[(Secondary)]

    S1 --> Monitor[Monitoring]
    S2 --> Monitor
    Primary --> Monitor
```

### Design Goals

- Survive one node failure.
- Automatically elect a replacement primary.
- Replicate data.
- Support backups.
- Provide monitoring.

### Important Configuration Concepts

Consider:

- Member priority
- Voting members
- Write concern
- Read preference
- Network topology
- Storage performance
- Backup strategy

### Common Mistake

Running three MongoDB processes on the same physical host does not provide meaningful host-level high availability.

Failure domains matter.

## Architecture Question: Why Use Three Replica Set Members?

A three-member replica set can tolerate one member failure while maintaining a voting majority.

The architecture should place members across independent failure domains when possible.

For example:

```text
Availability Zone A → Member 1
Availability Zone B → Member 2
Availability Zone C → Member 3
```

The exact topology depends on the infrastructure provider and workload.

The goal is to avoid placing all voting members behind a single failure domain.

## Architecture Question: Should Reads Go to Secondaries?

It depends on consistency requirements.

### Secondary Reads Can Help When

- Reads are naturally eventually consistent.
- Workload is read-heavy.
- Some stale data is acceptable.
- The application explicitly understands read preference behavior.

### Primary Reads Are Preferable When

- Read-after-write behavior matters.
- Freshness is critical.
- The operation depends on the latest state.

### Interview Trap

Do not say:

> Always read from secondaries to scale reads.

This ignores:

- Replication lag
- Staleness
- Read preference
- Connection routing
- Workload characteristics

## Architecture Question: Design a Sharded MongoDB System

### Requirements

Assume:

- Hundreds of millions of documents
- High write volume
- Dataset larger than a single node's practical capacity
- Horizontal scaling required

Architecture:

```mermaid
flowchart LR
    API[Application] --> M[Mongos]

    M --> S1[Shard 1 Replica Set]
    M --> S2[Shard 2 Replica Set]
    M --> S3[Shard 3 Replica Set]

    Config[Config Server Replica Set] --> M
```

### Shard Key Selection

A good shard key should generally provide:

- High cardinality
- Reasonable distribution
- Suitable query targeting
- Acceptable write distribution

Avoid selecting a key only because it is frequently queried.

### Example

A monotonically increasing identifier can create concentration of new writes depending on the sharding strategy.

A hashed key can distribute writes more evenly but may reduce range-query targeting.

The trade-off must be evaluated against actual access patterns.

## Architecture Question: What Makes a Good Shard Key?

Evaluate:

```text
Cardinality
Frequency
Distribution
Query targeting
Write distribution
Growth
Range-query requirements
```

### Example

Suppose:

```text
tenant_id
```

has only 100 tenants but billions of documents.

Although it is semantically meaningful, it may have insufficient cardinality for a large sharded deployment.

A more granular compound strategy may be necessary.

### Senior-Level Answer

A shard key is difficult to change later, so it should be selected from measured workload characteristics rather than intuition.

## Architecture Question: Avoid Scatter-Gather Queries

A query that cannot be targeted to a specific shard may execute across many shards.

```text
mongos
 ├── Shard 1
 ├── Shard 2
 ├── Shard 3
 └── Shard 4
```

Each shard processes the request and the router combines results.

This increases:

- Network traffic
- CPU usage
- Latency
- Cluster-wide workload

Good shard-key-aware queries can target fewer shards.

## Architecture Question: Design MongoDB for Global Users

A global application introduces:

```text
Latency
Data locality
Consistency
Regional failures
Replication
Compliance
Disaster recovery
```

Possible architecture:

```mermaid
flowchart LR
    UserA[Users Region A] --> APIA[API Region A]
    UserB[Users Region B] --> APIB[API Region B]

    APIA --> DBA[(MongoDB Deployment)]
    APIB --> DBA
```

For globally distributed systems, evaluate the application's actual consistency and locality requirements before selecting a topology.

Consider:

- Regional latency
- Write ownership
- Read locality
- Failover
- Data residency
- Recovery objectives

Do not assume multi-region automatically means better availability or lower latency.

## Architecture Question: MongoDB and Redis Together

A common architecture is:

```mermaid
flowchart LR
    API[API] --> Redis[(Redis)]
    API --> Mongo[(MongoDB)]
    Redis --> Mongo
```

MongoDB should normally remain the durable source of truth.

Redis may provide:

- Cache
- Rate limiting
- Session state
- Distributed coordination
- Hot derived data

### Cache-Aside Pattern

```text
Request
  ↓
Redis GET
  ↓
Hit? ── Yes → Return
  │
  No
  ↓
MongoDB
  ↓
Redis SET
  ↓
Return
```

### Common Failure

Treating Redis as the authoritative copy without designing durability and recovery requirements.

## Architecture Question: MongoDB and Kafka

MongoDB and Kafka solve different problems.

| Technology | Primary Role |
|---|---|
| MongoDB | Durable document storage |
| Kafka | Durable event streaming |
| Redis | Low-latency cache/state |

A common architecture is:

```text
API
 ↓
MongoDB
 ↓
Outbox / Change Stream
 ↓
Kafka
 ↓
Consumers
```

The exact integration should be selected based on delivery and consistency requirements.

## Architecture Question: How Do You Maintain MongoDB and Kafka Consistency?

Avoid:

```text
Write MongoDB
↓
Publish Kafka
```

as two independent operations without considering failure between them.

A process can fail after the database write but before event publication.

Possible approaches include:

- Transactional outbox
- Change streams
- Kafka Connect or managed integration
- Idempotent consumers

### Transactional Outbox

```mermaid
sequenceDiagram
    participant API
    participant Mongo
    participant Worker
    participant Kafka

    API->>Mongo: Transaction: business data + outbox event
    Mongo-->>API: Commit
    Worker->>Mongo: Read pending outbox
    Worker->>Kafka: Publish event
    Kafka-->>Worker: Acknowledge
    Worker->>Mongo: Mark event published
```

This separates business transaction atomicity from event delivery.

## Architecture Question: Design an Event-Driven MongoDB System

A change-stream-based architecture can look like:

```mermaid
flowchart LR
    Mongo[(MongoDB)] --> CS[Change Stream]
    CS --> Consumer[Python Consumer]
    Consumer --> Kafka[(Kafka)]
    Kafka --> ServiceA[Service A]
    Kafka --> ServiceB[Service B]
```

### Important Considerations

- Resume tokens
- Consumer restart
- Duplicate processing
- Idempotency
- Backpressure
- Monitoring
- Error handling
- Dead-letter strategy where applicable

Change streams are not a replacement for Kafka in every architecture.

## Architecture Question: Design a Payment-Related System

MongoDB can participate in payment systems, but the architecture must prioritize correctness.

Potential components:

```text
Payment API
   ↓
Payment Service
   ↓
MongoDB
   ↓
Payment State
   ↓
External Payment Provider
```

Critical concepts include:

- Idempotency keys
- State transitions
- Unique constraints
- Transaction boundaries
- Audit records
- Retry safety
- Reconciliation

Do not assume a database transaction can make an external payment provider transactionally consistent with MongoDB.

## Architecture Question: Design Idempotent APIs

For operations such as:

```text
POST /payments
POST /orders
POST /subscriptions
```

accept an idempotency key.

Example:

```json
{
  "idempotency_key": "req-8f92...",
  "amount": 1000
}
```

Store the key with the resulting operation.

Create an appropriate unique index:

```javascript
db.payment_requests.createIndex(
  {
    customer_id: 1,
    idempotency_key: 1
  },
  {
    unique: true
  }
)
```

The database constraint provides protection against concurrent duplicate requests.

## Architecture Question: When Should You Use Transactions?

Use transactions when a business invariant genuinely spans multiple documents or collections and cannot be safely represented as one atomic document operation.

Examples:

```text
Create order + reserve inventory
Update multiple account-related records
Change state across related documents
```

Avoid transactions for:

- Large batch processing
- Long-running workflows
- External network calls
- Operations that can be modeled as a single document update
- Workloads where eventual consistency is acceptable

The best transaction is often the one eliminated by better data modeling.

## Architecture Question: MongoDB Versus PostgreSQL

The decision should be workload-driven.

| Concern | MongoDB | PostgreSQL |
|---|---|---|
| Document-oriented data | Strong fit | JSONB available |
| Flexible schema | Strong fit | Possible |
| Complex relational joins | Less natural | Strong |
| Referential integrity | Application/database design dependent | Strong |
| Transactions | Supported | Mature relational model |
| Query-driven document modeling | Strong | Strong but relational-first |
| Ad hoc relational analytics | Possible | Strong |
| Embedded aggregates | Natural | Possible |
| Horizontal document workload | Strong capabilities | Requires architecture |
| Existing relational ecosystem | Different model | Strong |

Do not frame this as:

```text
MongoDB = NoSQL
PostgreSQL = SQL
```

The architectural decision should consider:

```text
Access patterns
Consistency
Data relationships
Operational requirements
Team expertise
Scale
Query complexity
```

## Architecture Question: Polyglot Persistence

A backend may use:

```mermaid
flowchart LR
    API[API Services]
    API --> PG[(PostgreSQL)]
    API --> Mongo[(MongoDB)]
    API --> Redis[(Redis)]
    API --> Kafka[(Kafka)]
```

Possible responsibilities:

- PostgreSQL → strongly relational transactional data
- MongoDB → document-oriented aggregates
- Redis → low-latency cache
- Kafka → event streaming

### Risk

Polyglot persistence increases:

- Operational complexity
- Data synchronization concerns
- Monitoring requirements
- Failure modes
- Developer cognitive load

Use multiple databases only when the workload justifies the additional complexity.

## Architecture Question: Design for Read-Heavy Workload

Assume:

```text
95% reads
5% writes
```

Architecture may include:

```text
API
 ↓
Redis
 ↓
MongoDB Replica Set
```

Optimization priorities:

- Query-specific indexes
- Projection
- Cache hit ratio
- Connection pooling
- Working set
- Read distribution
- Payload size

Do not immediately scale infrastructure before optimizing query patterns.

## Architecture Question: Design for Write-Heavy Workload

Assume:

```text
10% reads
90% writes
```

Priorities change:

- Minimize unnecessary indexes.
- Avoid hot documents.
- Batch writes where appropriate.
- Use bulk operations.
- Avoid excessive synchronous secondary work.
- Evaluate shard-key distribution.
- Monitor replication and storage throughput.

A schema optimized for reads can be inappropriate for write-heavy workloads.

## Architecture Question: Avoid Hot Documents

Suppose thousands of requests continuously update:

```json
{
  "_id": "global-counter",
  "count": 123456789
}
```

This creates a concentrated write hotspot.

Possible alternatives include:

- Partitioned counters
- Bucketed counters
- Asynchronous aggregation
- Sharded counter design

The correct approach depends on consistency and accuracy requirements.

## Architecture Question: Design Time-Series Data Storage

For metrics or event-like data:

```json
{
  "service": "orders",
  "metric": "latency_ms",
  "timestamp": "2026-09-27T10:00:00Z",
  "value": 84.2
}
```

Important architecture questions include:

- Retention
- Time-based querying
- Write rate
- Aggregation requirements
- Compression
- Index strategy
- Storage growth

MongoDB time-series collections can be appropriate for suitable workloads.

Do not treat time-series data exactly like general-purpose application documents.

## Architecture Question: Design Audit Logging

Audit records should generally be append-oriented.

Example:

```json
{
  "entity_type": "order",
  "entity_id": "order-123",
  "actor_id": "user-456",
  "action": "status_changed",
  "timestamp": "2026-09-27T10:00:00Z",
  "metadata": {
    "from": "pending",
    "to": "confirmed"
  }
}
```

Consider:

- Retention
- Immutability
- Access control
- Indexing
- Storage growth
- Compliance
- Query requirements

Do not expose audit collections to arbitrary application writes.

## Architecture Question: Design Soft Deletes

A common model is:

```json
{
  "_id": "user-123",
  "deleted_at": null
}
```

Normal queries should exclude deleted records.

Indexes may use partial filtering where appropriate:

```javascript
db.users.createIndex(
  { email: 1 },
  {
    unique: true,
    partialFilterExpression: {
      deleted_at: null
    }
  }
)
```

Be careful with the exact uniqueness semantics required by the business.

Soft deletion is a data lifecycle decision, not merely an extra field.

## Architecture Question: Design Schema Evolution

MongoDB's flexible schema does not eliminate migration problems.

For rolling deployments:

```text
Old application
      ↓
Old + new schema compatibility
      ↓
New application
      ↓
Backfill
      ↓
Remove old representation
```

Prefer additive changes where possible.

Avoid deployments where:

```text
Version A requires field X
Version B removes field X
```

while both versions are simultaneously running.

## Architecture Question: Large Collection With Performance Regression

Suppose:

```text
100 million documents
```

and a query was fast six months ago but is now slow.

Possible causes:

- Dataset growth
- Index no longer fits working set
- Data distribution changed
- Query selectivity decreased
- Index became less useful
- Increased concurrency
- Storage pressure

The correct response is not automatically:

```text
Add more RAM.
```

First measure:

```text
Query plan
Data size
Index size
Working set
Traffic
Resource usage
```

## Architecture Question: Design Backup and Disaster Recovery

A production architecture should separate:

```text
Primary database
        ↓
Replication
        ↓
Managed backups
        ↓
Point-in-time recovery
        ↓
Restore environment
```

Define:

### RPO

How much data loss is acceptable?

### RTO

How long can recovery take?

Example:

```text
RPO = 5 minutes
RTO = 30 minutes
```

These requirements influence backup frequency, topology, automation, and recovery design.

## Architecture Question: How Would You Design Disaster Recovery?

Consider:

- Backup frequency
- Point-in-time recovery
- Independent backup storage
- Regional failure
- Credential recovery
- DNS/application failover
- Infrastructure recreation
- Data validation
- Restore testing

A DR architecture is incomplete until restoration has been tested.

## Architecture Question: Design MongoDB on Kubernetes

MongoDB can run on Kubernetes, but stateful database operations require careful operational design.

Consider:

```text
Stateful workload
↓
Persistent storage
↓
Stable network identity
↓
Replica-set topology
↓
Pod disruption
↓
Node failure
↓
Backup
↓
Upgrade strategy
```

For production, evaluate whether self-managed MongoDB provides enough operational value compared with a managed service.

Do not treat a database as simply another stateless Deployment.

## Architecture Question: Design MongoDB With AWS

A backend architecture may look like:

```mermaid
flowchart LR
    User[Users] --> ALB[Application Load Balancer]
    ALB --> ECS[ECS / Kubernetes]
    ECS --> Mongo[(MongoDB Atlas / Managed MongoDB)]
    ECS --> Redis[(ElastiCache / Redis)]
    ECS --> Kafka[(Kafka)]
    Mongo --> Backup[Managed Backup / PITR]
```

Important concerns:

- Network isolation
- Private connectivity
- Security groups
- Secrets
- TLS
- Backup
- Monitoring
- Cost
- Multi-AZ architecture

The exact AWS architecture depends on whether MongoDB is self-managed or provided by a managed platform.

## Architecture Question: Connection Pool Architecture

Every application process can maintain its own MongoDB connection pool.

For example:

```text
10 Kubernetes pods
×
4 application workers
×
50 pool connections
=
2,000 potential connections
```

This is a simplified capacity calculation, but it illustrates the important principle:

> Connection pools multiply across processes and replicas.

Pool sizing must consider:

- Number of pods
- Number of workers
- Maximum pool size
- Database connection limits
- Query latency
- Traffic patterns

## Architecture Question: Design MongoDB for Microservices

A common mistake is creating one MongoDB database that every service freely accesses.

Prefer clear ownership:

```mermaid
flowchart LR
    OrderService[Order Service] --> OrderDB[(Order Data)]
    UserService[User Service] --> UserDB[(User Data)]
    CatalogService[Catalog Service] --> CatalogDB[(Catalog Data)]
```

The physical deployment may still share infrastructure, but logical ownership should remain clear.

Services should generally communicate through APIs or events rather than directly modifying another service's collections.

## Architecture Question: Should Every Microservice Have Its Own MongoDB Cluster?

Not necessarily.

Possible levels of isolation:

```text
Shared cluster
    ↓
Separate databases
    ↓
Separate collections
    ↓
Separate cluster
    ↓
Separate deployment / region
```

Choose the boundary based on:

- Scale
- Security
- Failure isolation
- Compliance
- Performance
- Cost
- Team ownership

Physical isolation has operational and financial costs.

## Architecture Question: Design a Multi-Region Service

Before introducing multi-region MongoDB architecture, establish:

```text
Who owns writes?
Where are reads served?
What happens during network partition?
How much stale data is acceptable?
What happens during regional failure?
What is the recovery strategy?
```

Multi-region designs increase complexity around:

- Latency
- Consistency
- Failover
- Data residency
- Operational procedures

A single-region multi-AZ architecture may be sufficient for many systems.

## Architecture Question: Design for Zero-Downtime Deployment

MongoDB schema changes should support rolling application deployment.

A safe pattern is:

```text
Deploy backward-compatible application
        ↓
Verify production behavior
        ↓
Backfill data
        ↓
Switch reads/writes
        ↓
Remove deprecated fields later
```

Avoid making an application deployment and destructive schema migration inseparable.

## Architecture Question: Design Index Lifecycle Management

Indexes should follow a lifecycle:

```text
Query requirement
      ↓
Index design
      ↓
Deploy
      ↓
Measure
      ↓
Monitor usage
      ↓
Re-evaluate
      ↓
Retain / modify / remove
```

Review:

- Query frequency
- Query latency
- Index size
- Write cost
- Storage usage
- Index utilization

Indexes should be treated as architectural dependencies.

## Architecture Question: Design Observability

A production MongoDB architecture should expose:

```text
Application
 ├── Request latency
 ├── Error rate
 └── Throughput

MongoDB
 ├── Query latency
 ├── Operations/sec
 ├── Connections
 ├── CPU
 ├── Memory
 ├── Disk
 ├── Replication lag
 └── Storage growth

Replica Set
 ├── Primary state
 ├── Elections
 ├── Member health
 └── Oplog window
```

Use request IDs or trace IDs to correlate application requests with database operations.

## Architecture Question: Design Security

A production MongoDB architecture should include:

```text
Application
   ↓
Private Network
   ↓
TLS
   ↓
MongoDB Authentication
   ↓
Least-Privilege Authorization
   ↓
Encrypted Storage
   ↓
Auditing / Monitoring
```

### Important Controls

- TLS for connections
- Strong authentication
- Least-privilege roles
- Network restrictions
- Secret management
- Encryption at rest
- Audit logging where required
- Credential rotation
- Security monitoring

Never expose MongoDB directly to the public internet simply to simplify development.

## Architecture Question: Design a Secure Connection From FastAPI

Configuration should come from the environment or secret-management system.

```python
from os import environ

MONGODB_URI = environ["MONGODB_URI"]
```

The application should not contain:

```python
MONGODB_URI = "mongodb://admin:password@..."
```

Production configuration should also specify appropriate:

- Connection timeouts
- Server selection timeout
- TLS requirements
- Pool limits
- Retry behavior

Exact values should be determined through workload testing rather than copied blindly.

## Architecture Question: FastAPI + MongoDB Architecture

A maintainable architecture can be:

```text
HTTP Layer
   ↓
Pydantic Schemas
   ↓
Service Layer
   ↓
Repository Layer
   ↓
PyMongo Driver
   ↓
MongoDB
```

### Repository

Responsible for:

- MongoDB queries
- Persistence operations
- Mapping database errors

### Service

Responsible for:

- Business rules
- Transactions
- Idempotency
- Workflow orchestration

### API Layer

Responsible for:

- Authentication
- Validation
- HTTP semantics
- Response serialization

Avoid placing complex MongoDB queries directly inside route handlers.

## Architecture Question: Synchronous Versus Asynchronous Python Driver

The architecture should match the application concurrency model and driver capabilities.

For synchronous PyMongo:

```text
FastAPI
  ↓
Sync repository
  ↓
PyMongo
```

For an asynchronous driver:

```text
FastAPI
  ↓
Async repository
  ↓
Async MongoDB driver
```

Do not mix blocking database calls into an async request path without understanding the execution implications.

When selecting a driver, verify current MongoDB and driver support rather than relying on obsolete tutorials.

## Architecture Question: Django + MongoDB

Django is designed primarily around relational database ORM semantics.

A MongoDB architecture may instead use:

```text
Django
  ↓
Service Layer
  ↓
Repository
  ↓
PyMongo / MongoEngine
  ↓
MongoDB
```

Do not assume Django's native relational ORM behavior maps directly to MongoDB.

Use a clear persistence boundary so that MongoDB-specific behavior does not leak throughout the application.

## Architecture Question: Design for Testing

A production MongoDB architecture should support:

```text
Unit tests
Integration tests
Repository tests
API tests
Migration tests
Failure tests
Recovery tests
```

Repository integration tests should exercise:

- Real MongoDB behavior
- Index constraints
- BSON types
- Transactions where applicable
- Aggregation
- Error handling

Mocks alone cannot validate database behavior.

## Architecture Question: Design for Capacity Growth

Capacity planning should track:

```text
Current data
+
Growth rate
+
Index growth
+
Write throughput
+
Read throughput
+
Peak traffic
+
Replication overhead
+
Backup requirements
```

Monitor trends rather than waiting for resource exhaustion.

Useful metrics include:

- Storage growth/day
- Documents created/day
- Average document size
- Index size
- Operations/sec
- p95/p99 query latency
- Connection utilization
- Replication lag

## Architecture Question: When Should MongoDB Be Sharded?

Sharding becomes relevant when a single replica-set architecture cannot satisfy the workload's capacity or scaling requirements.

Potential drivers include:

- Dataset size
- Write throughput
- Read throughput
- Storage limits
- Working-set requirements
- Horizontal scaling requirements

Do not shard simply because the dataset is large.

A well-designed replica set with appropriate storage and indexes may support substantial workloads.

## Architecture Question: When Should You Avoid MongoDB?

MongoDB may be a poor fit when the dominant workload requires:

- Complex relational joins
- Extensive foreign-key enforcement
- Relational reporting
- Mature relational transactional workflows
- SQL-specific ecosystem capabilities

The correct answer is workload-dependent.

A senior engineer should be able to explain both:

```text
Why MongoDB fits
```

and:

```text
Why another database may fit better
```

## Architecture Question: MongoDB Anti-Patterns

### Treating MongoDB Like a Relational Database

Creating many normalized collections and reconstructing every response through joins can defeat the benefits of document modeling.

### Treating MongoDB Like a Key-Value Store

Ignoring document modeling and querying capabilities can lead to inefficient architectures.

### Unbounded Arrays

A document containing millions of child elements creates growth and update problems.

### Too Many Indexes

Indexes improve reads but add storage and write costs.

### Large Transactions

Long transactions increase contention and resource usage.

### Arbitrary Client Queries

Never allow external clients to submit unrestricted MongoDB filters.

### Shared Collection Ownership

Multiple services independently modifying the same documents creates unclear ownership and consistency problems.

### Using Redis as the Source of Truth

Caching architecture should preserve durable state in the appropriate database.

### Premature Sharding

Sharding introduces significant operational complexity.

## Architecture Interview Framework

For a MongoDB architecture question, structure the answer around:

```text
Requirements
↓
Traffic and scale
↓
Access patterns
↓
Data model
↓
Indexes
↓
Read/write path
↓
Consistency
↓
Transactions
↓
Caching
↓
Replication / HA
↓
Sharding
↓
Security
↓
Observability
↓
Backup / DR
↓
Failure scenarios
↓
Trade-offs
```

This prevents the discussion from becoming a list of MongoDB features.

## Senior-Level Architecture Questions

### How Would You Design MongoDB for 100 Million Documents?

Discuss:

- Access patterns
- Document size
- Index size
- Working set
- Query latency
- Storage
- Replica-set capacity
- Growth rate
- Backup
- Sharding requirements

### How Would You Handle a 10x Traffic Increase?

Consider:

```text
Application horizontal scaling
        ↓
Connection pool recalculation
        ↓
Query optimization
        ↓
Caching where appropriate
        ↓
MongoDB capacity
        ↓
Sharding if required
```

Do not assume adding API replicas alone solves database bottlenecks.

### How Would You Handle a Hot Shard?

Investigate:

- Shard-key distribution
- Write concentration
- Query concentration
- Tenant concentration
- Monotonic values

Potential remedies depend on the root cause and may include shard-key redesign or resharding.

### How Would You Handle a Hot Document?

Determine why many operations target the same document.

Possible designs:

- Partition the state
- Use bucketed counters
- Move derived state to asynchronous processing
- Reduce write frequency
- Redesign the aggregate

### How Would You Handle a MongoDB Outage?

The architecture should define:

```text
Detection
↓
Traffic behavior
↓
Retry policy
↓
Failover
↓
Data consistency
↓
Recovery
↓
Validation
```

The application should fail predictably rather than generating uncontrolled retries.

## Architecture Trade-Off Matrix

| Decision | Option A | Option B | Main Trade-Off |
|---|---|---|---|
| Data relationship | Embed | Reference | Read locality vs independent lifecycle |
| Pagination | Skip/limit | Cursor | Simplicity vs deep-page performance |
| Reads | Primary | Secondary | Freshness vs distribution |
| Storage | Replica set | Sharded cluster | Simplicity vs horizontal scale |
| Cache | None | Redis | Simplicity vs lower read latency |
| Events | Change streams | Kafka | Database coupling vs streaming platform |
| Schema | Flexible | Validation | Agility vs stronger enforcement |
| Transactions | Avoid | Use | Simplicity/performance vs atomicity |
| Deployment | Managed | Self-managed | Operational control vs operational burden |
| Persistence | Single DB | Polyglot | Simplicity vs workload specialization |

## Architecture Red Flags in Interviews

Be cautious when an architecture answer includes statements such as:

```text
"Just add an index."
"Just use Redis."
"Always read from secondaries."
"Always use transactions."
"MongoDB automatically scales."
"Sharding solves performance."
"Use one collection per user."
"Store everything in one document."
"Just increase the timeout."
"Retry until it works."
```

Each statement ignores important workload or failure characteristics.

A senior answer explains the conditions under which a technique is appropriate.

## Production Architecture Checklist

Before approving a MongoDB architecture, verify:

### Data

- Access patterns are documented.
- Embedding and referencing decisions are intentional.
- Document growth is bounded.
- Schema evolution is planned.
- Data ownership is clear.

### Queries

- Critical query shapes are known.
- Appropriate indexes exist.
- Pagination strategy is defined.
- Aggregations are measured.
- Query plans are reviewed.

### Reliability

- Replica-set topology is appropriate.
- Failure domains are separated.
- Elections and failover are understood.
- Write concern matches durability requirements.
- Read preference matches consistency requirements.

### Scalability

- Growth rate is known.
- Connection pools are sized globally.
- Working-set requirements are understood.
- Hot documents are identified.
- Sharding requirements are evaluated from workload evidence.

### Security

- Authentication is enabled.
- Least-privilege authorization is used.
- TLS is configured.
- Network access is restricted.
- Secrets are managed securely.
- Sensitive data is excluded from logs.

### Operations

- Metrics are collected.
- Slow queries are monitored.
- Replica health is monitored.
- Storage growth is tracked.
- Connection utilization is visible.
- Alerts have actionable thresholds.

### Disaster Recovery

- Backups are automated.
- Point-in-time recovery is available when required.
- RPO and RTO are documented.
- Restore procedures are tested.
- Recovery runbooks exist.

## Key Takeaways

- MongoDB architecture should begin with workload, access patterns, consistency, scale, and failure requirements rather than MongoDB features.
- Data modeling, indexing, replica-set topology, and shard-key selection are architectural decisions that directly determine application performance and scalability.
- Senior designs explicitly address consistency, connection pooling, caching, transactions, event delivery, security, observability, backup, and disaster recovery.
- MongoDB should have clear ownership boundaries in microservice architectures, while Redis, Kafka, PostgreSQL, and other systems should be introduced only when their workload-specific value justifies the added complexity.
- Strong architecture answers explain trade-offs, failure modes, operational consequences, and measurable validation criteria rather than presenting a single MongoDB pattern as universally correct.