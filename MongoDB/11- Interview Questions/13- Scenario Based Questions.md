# 13- Scenario Based Questions

## Overview

Scenario-based MongoDB interviews test engineering judgment rather than command memorization. The interviewer is typically evaluating whether you can reason about:

- Data modeling
- Query patterns
- Index selection
- Consistency
- Transactions
- Replication
- High availability
- Sharding
- Performance
- Security
- Failure handling
- Backup and recovery
- Python and API integration
- Operational trade-offs

A strong answer should follow a consistent reasoning process:

```text
Understand the requirement
        ↓
Identify access patterns
        ↓
Choose data model
        ↓
Define consistency requirements
        ↓
Design indexes
        ↓
Choose deployment topology
        ↓
Consider failure modes
        ↓
Measure performance
        ↓
Define monitoring and recovery
```

The goal is not to immediately propose a MongoDB feature. Start with business and workload requirements, then choose the MongoDB capability that satisfies them.

## How to Approach MongoDB Scenarios

A senior-level answer should normally address these dimensions:

| Dimension | Questions to Ask |
|---|---|
| Data model | What data is stored together? |
| Access patterns | How will the application read and update it? |
| Cardinality | How many related documents can exist? |
| Consistency | How fresh must reads be? |
| Atomicity | Which changes must succeed together? |
| Performance | What are the latency and throughput targets? |
| Scale | How large will the collection become? |
| Availability | What failures must the system tolerate? |
| Security | Who can access which data? |
| Operations | How will the system be monitored and recovered? |
| Cost | What infrastructure and storage growth are acceptable? |

Avoid answers such as:

> "I would add an index."

A stronger answer explains:

> "I would first identify the query shape, inspect its selectivity and sort requirements, then verify the execution plan. If the query is frequent and selective, I would design a compound index around its equality, sort, and range predicates and validate the improvement with execution statistics."

## Scenario: Design a User Profile Collection

### Requirement

A SaaS application needs to store:

- User identity
- Email
- Name
- Tenant
- Preferences
- Addresses
- Login metadata

The application frequently retrieves a user by:

```text
tenant_id + email
```

and by:

```text
tenant_id + user_id
```

### Design

A possible document:

```json
{
  "_id": "ObjectId(...)",
  "tenant_id": "tenant-123",
  "email": "user@example.com",
  "name": "Alice",
  "preferences": {
    "language": "en",
    "timezone": "Asia/Kolkata"
  },
  "addresses": [
    {
      "type": "home",
      "city": "Kolkata"
    }
  ],
  "created_at": "2026-09-27T10:00:00Z",
  "updated_at": "2026-09-27T10:00:00Z"
}
```

Indexes:

```javascript
db.users.createIndex(
  { tenant_id: 1, email: 1 },
  { unique: true }
)

db.users.createIndex(
  { tenant_id: 1, _id: 1 }
)
```

The compound unique index also enforces tenant-scoped email uniqueness.

### Senior Considerations

Ask:

- Can an email belong to multiple tenants?
- Is email case sensitivity relevant?
- Can preferences grow without bound?
- Are addresses frequently queried independently?
- Is `tenant_id` always present?
- Is user deletion hard or soft?
- Are sensitive fields returned to clients?

The important point is that schema and indexes follow access patterns.

## Scenario: Embed or Reference Order Items?

### Requirement

An order contains line items. A typical order has 1–20 items, but some enterprise orders can contain thousands.

### Option A: Embed

```json
{
  "_id": "order-123",
  "customer_id": "customer-1",
  "items": [
    {
      "product_id": "product-1",
      "name": "Keyboard",
      "quantity": 2,
      "unit_price": 80
    }
  ]
}
```

Advantages:

- One read retrieves the order
- Atomic updates within the order
- Good locality
- Simple API retrieval

Limitations:

- Document growth
- Large orders can become expensive
- Updating individual elements can become complex
- Unbounded arrays are dangerous

### Option B: Reference

```text
orders
    │
    └── order_id

order_items
    │
    ├── order_id
    ├── product_id
    └── quantity
```

Advantages:

- Independent lifecycle
- Better for large or unbounded collections
- Smaller parent documents

Limitations:

- Multiple queries
- More application complexity
- Possible `$lookup`

### Interview Answer

The correct decision depends on cardinality and access patterns.

For bounded line items that are almost always read with the order, embedding is usually attractive. For very large or independently queried item sets, referencing becomes more appropriate.

## Scenario: A Document Has an Unbounded Array

### Problem

A user document contains:

```json
{
  "_id": "user-1",
  "events": [
    "... millions of events ..."
  ]
}
```

### Why It Is Dangerous

An unbounded array can cause:

- Large document growth
- Higher read cost
- Expensive updates
- Larger replication traffic
- Working-set pressure
- Serialization overhead

### Better Design

Store events independently:

```json
{
  "_id": "event-1",
  "user_id": "user-1",
  "type": "login",
  "created_at": "2026-09-27T10:00:00Z"
}
```

Index:

```javascript
db.events.createIndex({
  user_id: 1,
  created_at: -1
})
```

This supports:

```text
Get latest events for user
```

without loading the entire user history.

## Scenario: Design a Multi-Tenant SaaS Database

### Requirement

A SaaS platform has thousands of tenants. Each tenant has:

- Users
- Orders
- Documents
- Audit records

The primary requirement is strict tenant isolation.

### Shared Collection Model

```json
{
  "_id": "ObjectId(...)",
  "tenant_id": "tenant-123",
  "name": "Alice"
}
```

Queries should include the tenant:

```python
query = {
    "tenant_id": authenticated_tenant_id,
    "_id": user_id,
}
```

Indexes should frequently begin with the tenant dimension where it forms part of the access pattern:

```javascript
db.users.createIndex({
  tenant_id: 1,
  created_at: -1
})
```

### Security Requirement

Never trust:

```text
?tenant_id=tenant-456
```

from the client.

The application should derive the tenant context from authenticated identity and authorization.

### Senior Considerations

Evaluate:

- Number of tenants
- Tenant size distribution
- Largest tenant
- Data isolation requirements
- Regulatory requirements
- Cross-tenant administration
- Backup requirements
- Index size
- Sharding strategy

A shared collection is operationally simple, but tenant isolation must be enforced consistently.

## Scenario: One Tenant Is Much Larger Than Others

### Problem

A shared MongoDB collection contains:

```text
10,000 small tenants
1 extremely large tenant
```

The large tenant generates most of the traffic.

### Risks

- Hot partitions
- Uneven workload
- Large indexes
- Cache pressure
- Noisy-neighbor effects

### Possible Solutions

Depending on workload:

- Separate high-volume tenants
- Use tenant-aware indexes
- Partition data by workload characteristics
- Use dedicated collections or databases for exceptional tenants
- Design a shard key around tenant distribution
- Introduce caching

The key is not to automatically create one database per tenant.

Database-per-tenant architecture can become operationally expensive at large tenant counts.

## Scenario: A Query Is Suddenly Slow

### Symptom

An API endpoint normally responds in:

```text
50 ms
```

but now takes:

```text
2 seconds
```

### Investigation

Start with:

```text
Application latency
        ↓
MongoDB latency
        ↓
Query shape
        ↓
Explain plan
        ↓
Index usage
        ↓
Data volume
        ↓
Infrastructure health
```

Run:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  status: "active"
}).explain("executionStats")
```

Inspect:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
winningPlan
```

### Possible Causes

- Missing index
- Index no longer selective
- Large data growth
- Collection scan
- Expensive sort
- Large documents
- Connection pool exhaustion
- Replica-set issues
- Infrastructure resource pressure

### Senior Response

Do not immediately add an index.

First determine:

1. Whether the query changed
2. Whether data distribution changed
3. Whether the existing index still matches the workload
4. Whether the execution plan changed
5. Whether the problem is actually MongoDB

## Scenario: Query Uses COLLSCAN

### Problem

The explain plan contains:

```text
COLLSCAN
```

### Initial Interpretation

MongoDB is scanning collection documents rather than using an index.

However, `COLLSCAN` is not automatically a bug.

If the query intentionally reads a large percentage of a small collection, a collection scan may be reasonable.

### Investigation

Check:

```text
Collection size
Selectivity
Query frequency
Documents examined
Documents returned
Execution time
```

If:

```text
nReturned = 10
totalDocsExamined = 5,000,000
```

the query is a strong optimization candidate.

If:

```text
nReturned = 4,500,000
totalDocsExamined = 5,000,000
```

an index may provide little benefit.

## Scenario: Query Uses SORT Stage

### Problem

The query plan contains:

```text
IXSCAN
  ↓
FETCH
  ↓
SORT
```

The query filters correctly but performs an expensive sort.

### Solution

Design the index to support both filtering and sorting.

Example query:

```python
collection.find({
    "tenant_id": tenant_id,
    "status": "active",
}).sort(
    "created_at",
    -1,
)
```

Possible index:

```javascript
db.orders.createIndex({
  tenant_id: 1,
  status: 1,
  created_at: -1
})
```

Validate using `explain()` rather than assuming the index is optimal.

## Scenario: Pagination Becomes Slow

### Problem

The API uses:

```python
collection.find(query).skip(500000).limit(20)
```

### Why

MongoDB may need to traverse a large number of preceding results before returning the requested page.

### Better Design

Use cursor-based pagination.

```text
First request
    ↓
20 results
    ↓
Opaque cursor
    ↓
Next request
    ↓
Query after cursor
```

Example ordering:

```python
.sort([
    ("created_at", -1),
    ("_id", -1),
])
```

The index should support the filter and ordering.

### Interview Point

Offset pagination is simple and often acceptable for small datasets. Cursor pagination becomes more appropriate as datasets and page depths grow.

## Scenario: Duplicate User Registrations

### Requirement

Two requests arrive simultaneously:

```text
POST /users
POST /users
```

Both attempt to register:

```text
user@example.com
```

### Incorrect Approach

```python
if not collection.find_one({"email": email}):
    collection.insert_one(document)
```

This creates a race condition.

Both requests can observe that the email does not exist.

### Correct Approach

Create a unique index:

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

Then handle:

```python
from pymongo.errors import DuplicateKeyError
```

The database becomes the final enforcement point.

## Scenario: Implement Idempotent API Writes

### Requirement

A payment service retries:

```text
POST /orders
```

The client may send the same request multiple times.

### Design

Use an idempotency key:

```text
Idempotency-Key: 9c1d...
```

Store it with the result:

```json
{
  "_id": "ObjectId(...)",
  "idempotency_key": "9c1d...",
  "status": "completed",
  "response": {
    "order_id": "order-123"
  }
}
```

Create a unique index:

```javascript
db.idempotency.createIndex(
  { idempotency_key: 1 },
  { unique: true }
)
```

The operation becomes retry-safe.

### Senior Considerations

Define:

- Key lifetime
- Request-body consistency
- Result retention
- Concurrent requests
- Failure after database write
- Failure before response delivery

Idempotency is especially important when API retries interact with MongoDB transactions.

## Scenario: Two Documents Must Change Atomically

### Requirement

A wallet transfer must:

```text
Debit account A
Credit account B
```

Both changes must succeed or neither should be applied.

### Solution

Use a MongoDB transaction.

```python
with client.start_session() as session:
    with session.start_transaction():
        accounts.update_one(
            {
                "_id": source_id,
                "balance": {"$gte": amount},
            },
            {
                "$inc": {"balance": -amount},
            },
            session=session,
        )

        accounts.update_one(
            {"_id": destination_id},
            {
                "$inc": {"balance": amount},
            },
            session=session,
        )
```

### Senior Considerations

Ask:

- Can the data model be redesigned to use one atomic document?
- What is the transaction duration?
- What happens during a primary election?
- Is retry safe?
- What read and write concerns are required?
- Are external calls being made inside the transaction?

Do not use transactions merely because they exist.

## Scenario: Transaction Is Taking Too Long

### Symptom

Transactions frequently take:

```text
2–5 seconds
```

### Possible Causes

- Too many operations
- Large reads
- External API calls
- Poor indexes
- Contention
- Large document updates
- Application computation inside transaction

### Investigation

Review:

```text
Transaction duration
Operations per transaction
Query plans
Lock/contention indicators
Network latency
External calls
```

### Corrective Actions

- Reduce transaction scope
- Improve indexes
- Move external calls outside the transaction
- Split large operations
- Redesign the data model
- Use idempotent compensating workflows where appropriate

A database transaction should not become a workflow engine.

## Scenario: Read Must Immediately See a Write

### Requirement

A user updates an account and immediately requests the account.

The second read must reflect the write.

### Risk

If the read is directed to a secondary, replication lag may produce a stale result.

### Design

Use an appropriate read preference and consistency strategy.

For strongly consistency-sensitive operations, primary-oriented reads are often appropriate.

The important interview point is:

```text
Read scaling
    versus
Read freshness
```

You cannot optimize one without considering the other.

## Scenario: Secondary Reads Are Stale

### Symptom

The application reads old data from secondary members.

### Possible Causes

- Replication lag
- Heavy write workload
- Slow secondary
- Network problems
- Resource saturation

Inspect:

```javascript
rs.status()
```

Monitor replication lag over time rather than checking it only after an incident.

### Corrective Actions

Depending on the workload:

- Route consistency-sensitive reads to primary
- Improve secondary capacity
- Reduce write amplification
- Review indexes
- Investigate infrastructure saturation
- Reconsider the need for secondary reads

## Scenario: Primary Fails

### Requirement

The application must continue operating when the MongoDB primary becomes unavailable.

### Architecture

```text
                 FastAPI / Django
                        │
                        ▼
                 MongoDB Driver
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Primary    Secondary  Secondary
             │          ▲          ▲
             └──────────┴──────────┘
                  Replication
```

The driver discovers the replica-set topology and can reconnect to the newly elected primary.

### Senior Considerations

Review:

- Replica-set size
- Election behavior
- Write concern
- Read preference
- Retryable operations
- Connection timeout
- Application timeout
- Transaction retry behavior
- Monitoring

Do not hard-code one primary hostname into application logic.

## Scenario: Secondary Lag Is Increasing

### Symptom

Replication lag increases continuously.

### Possible Causes

- High write throughput
- Secondary resource saturation
- Slow disk
- Network latency
- Large indexes
- Expensive workload
- Insufficient hardware capacity

### Investigation

Compare:

```text
Primary write rate
Secondary replication rate
CPU
Memory
Disk I/O
Network
Oplog window
```

### Corrective Action

Depending on the root cause:

- Scale the secondary
- Reduce write amplification
- Review indexes
- Improve storage
- Reduce unnecessary workload
- Rebalance architecture

Do not simply increase application timeouts.

## Scenario: Rollback After Failure

### Requirement

A primary fails and previously acknowledged writes are not present after failover.

### Engineering Question

Determine the write concern used by the application.

A stronger write concern, such as majority acknowledgment, provides stronger durability semantics in a replica-set deployment than weaker acknowledgment settings.

### Investigation

Review:

- Write concern
- Replica topology
- Failure timing
- Election sequence
- Application retry behavior

The important lesson is that durability depends on the configured acknowledgment and replication model.

## Scenario: Design High Availability Across Availability Zones

A production replica set can distribute members across failure domains.

```text
Region
│
├── AZ-A
│   └── MongoDB Member
│
├── AZ-B
│   └── MongoDB Member
│
└── AZ-C
    └── MongoDB Member
```

Benefits:

- Better failure-domain isolation
- Reduced risk of losing quorum from a single AZ failure

Consider:

- Network latency
- Voting members
- Election behavior
- Storage performance
- Backup strategy
- Cost

High availability is not simply "three servers"; failure-domain placement matters.

## Scenario: Design a Global Application

### Requirement

Users exist across multiple geographic regions.

### Questions

Before choosing a topology, determine:

- Where writes originate
- Where reads originate
- Required read freshness
- Data residency
- RPO/RTO
- Cross-region latency
- Regulatory requirements
- Failover requirements

Possible architecture:

```text
Region A
FastAPI
   │
   ▼
MongoDB Deployment
   │
   │ replication
   ▼
Region B
MongoDB Deployment
   │
   ▼
Regional API
```

Do not assume multi-region replication automatically solves global consistency.

## Scenario: Collection Has 500 Million Documents

### Problem

A collection has grown to hundreds of millions of documents.

Queries are becoming slower and storage is increasing rapidly.

### Investigation

Measure:

- Query latency
- Index size
- Working set
- Storage growth
- Document size
- Query selectivity
- Write rate
- Read rate
- Hot partitions

### Possible Solutions

Depending on workload:

- Better indexing
- Archival
- TTL for temporary data
- Data lifecycle management
- Document redesign
- Collection partitioning strategies
- Sharding

Do not jump directly to sharding before fixing inefficient queries and data modeling.

## Scenario: When Should You Shard?

Sharding becomes relevant when a single replica set cannot satisfy the workload's scale requirements.

Consider:

```text
Data volume
Write throughput
Read throughput
Storage capacity
Working set
Connection load
Growth rate
```

Sharding introduces additional complexity:

```text
Application
    │
    ▼
  mongos
    │
 ┌──┼──┐
 ▼  ▼  ▼
S1 S2 S3
```

Before sharding, verify:

- Query/index optimization
- Hardware scaling
- Data lifecycle policies
- Caching
- Schema design
- Archival

## Scenario: Choose a Shard Key

Suppose orders contain:

```json
{
  "tenant_id": "tenant-123",
  "order_id": "order-123",
  "created_at": "2026-09-27T10:00:00Z"
}
```

Candidate shard keys include:

```text
tenant_id
order_id
hashed(order_id)
tenant_id + order_id
```

Evaluate:

| Property | Question |
|---|---|
| Cardinality | Are there enough distinct values? |
| Frequency | Is one value disproportionately common? |
| Distribution | Will writes spread across shards? |
| Query targeting | Do common queries include the key? |
| Monotonicity | Will writes concentrate on one shard? |
| Growth | Will distribution remain healthy? |

A good shard key balances data distribution with query targeting.

## Scenario: Hot Shard

### Symptom

One shard handles most traffic.

### Possible Causes

- Poor shard key
- Low cardinality
- Highly frequent shard-key value
- Monotonically increasing key
- Tenant concentration

### Investigation

Measure:

```text
Operations per shard
Storage per shard
Chunk distribution
Query targeting
Write distribution
```

### Corrective Actions

Depending on the workload:

- Redesign shard key
- Reshard
- Improve query targeting
- Distribute tenant workload
- Change write distribution

A shard key is an architectural decision, not merely an indexing decision.

## Scenario: Aggregation Is Too Expensive

### Problem

A Django or FastAPI endpoint executes:

```text
$match
$lookup
$unwind
$group
$sort
```

against hundreds of millions of documents.

### Investigation

Inspect:

```text
Input document count
Intermediate result size
Indexes
$lookup cardinality
$group memory
Sort cost
Execution statistics
```

### Optimization

Start filtering early:

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
      total: { $sum: "$amount" }
    }
  }
]
```

Potentially move expensive reports to asynchronous processing.

## Scenario: Aggregation Needs Pagination

### Problem

A reporting endpoint uses:

```text
$sort
$skip
$limit
```

over a very large dataset.

### Risks

Deep `$skip` can become expensive.

### Better Design

Where the report semantics allow it, use stable key-based pagination.

For example:

```text
created_at + _id
```

can provide deterministic ordering.

For complex analytics, another option is precomputed reporting data rather than repeatedly executing the same expensive aggregation.

## Scenario: `$lookup` Is Becoming a Bottleneck

### Problem

An aggregation performs a large `$lookup` between collections.

### Investigation

Ask:

- Is the join required?
- Is the foreign field indexed?
- How many documents are joining?
- Is the relationship bounded?
- Could controlled denormalization work?
- Can the data model be redesigned?

MongoDB supports joins through `$lookup`, but frequent expensive joins can indicate that the data model does not match the workload.

## Scenario: Cache MongoDB Results

### Requirement

A product catalog is read thousands of times per second but changes infrequently.

### Architecture

```text
Client
  │
  ▼
Django / FastAPI
  │
  ├── Redis ── Cache Hit
  │
  └── MongoDB ── Cache Miss
```

Example flow:

```text
Request
  ↓
Redis GET
  │
  ├── Hit → Return
  │
  └── Miss
        ↓
     MongoDB
        ↓
     Redis SET
        ↓
     Return
```

### Senior Considerations

Define:

- TTL
- Cache invalidation
- Stale data tolerance
- Serialization format
- Cache stampede protection
- Memory limits

Do not use Redis to compensate for an inefficient database query.

## Scenario: Cache Stampede

### Problem

A popular cached document expires.

Thousands of requests simultaneously query MongoDB.

```text
Cache expires
     ↓
Thousands of misses
     ↓
MongoDB overload
```

### Mitigation

Possible approaches include:

- Request coalescing
- Locking
- Probabilistic early refresh
- Staggered expiration
- Background refresh

The exact approach depends on latency and consistency requirements.

## Scenario: MongoDB and Kafka Must Stay Consistent

### Problem

An application needs to:

```text
1. Write MongoDB
2. Publish Kafka event
```

This is not automatically atomic.

Failure can occur:

```text
MongoDB write succeeds
        ↓
Kafka publish fails
```

### Better Architecture

Consider an outbox-style design or another durable event publication mechanism.

```text
Application
    │
    ▼
MongoDB Transaction
    │
    ├── Business Document
    └── Outbox Event
             │
             ▼
       Event Publisher
             │
             ▼
           Kafka
```

The consumer should be idempotent.

## Scenario: Change Stream Consumer Crashes

### Problem

A Python consumer processes MongoDB changes and crashes after performing the business action but before recording its progress.

### Risk

The event may be delivered again.

### Correct Design

Treat processing as at-least-once unless the complete architecture guarantees stronger semantics.

Use:

- Resume tokens
- Idempotency keys
- Durable processing state
- Duplicate detection
- Retry handling

Example:

```text
Change Event
    ↓
Validate
    ↓
Check Idempotency
    ↓
Process
    ↓
Persist Processing State
    ↓
Advance / Resume
```

Never assume consumers process each event exactly once.

## Scenario: Secure a MongoDB-Backed API

### Requirement

A Django or FastAPI service exposes customer data.

Security layers should include:

```text
Client
  ↓
TLS
  ↓
Authentication
  ↓
Authorization
  ↓
Tenant Isolation
  ↓
Application Validation
  ↓
MongoDB Least-Privilege User
  ↓
MongoDB Network Controls
```

MongoDB should not be publicly accessible simply because the API is protected.

Use:

- TLS
- Authentication
- Least privilege
- Network restrictions
- Secret management
- Credential rotation
- Auditing where required
- Encryption at rest

## Scenario: Prevent NoSQL Injection

### Vulnerable Pattern

```python
query = request.json()["filter"]

collection.find(query)
```

A client may submit MongoDB operators that the application did not intend to expose.

### Safer Pattern

Define a typed API contract:

```python
class UserFilter(BaseModel):
    status: str | None = None
    country: str | None = None
```

Construct the MongoDB query explicitly:

```python
query = {}

if filters.status:
    query["status"] = filters.status

if filters.country:
    query["country"] = filters.country
```

Never expose unrestricted database query syntax to untrusted clients.

## Scenario: Sensitive Data Appears in Logs

### Problem

An exception logs:

```text
MongoDB query:
{
    "email": "user@example.com",
    "password": "secret"
}
```

### Risk

Logs become a secondary sensitive-data store.

### Corrective Action

Use structured logging with safe fields:

```json
{
  "operation": "create_user",
  "request_id": "req-123",
  "error_type": "DuplicateKeyError"
}
```

Never log:

- Passwords
- Connection strings
- Access tokens
- Database credentials
- Complete sensitive documents

## Scenario: MongoDB Connection Pool Is Exhausted

### Symptoms

Requests become slow while MongoDB itself appears healthy.

### Possible Causes

- Too many concurrent requests
- Pool too small
- Long-running queries
- Long transactions
- Connections not being released properly
- Too many application workers
- Too many pods

### Investigation

Compare:

```text
HTTP concurrency
MongoDB connection count
Pool configuration
Query duration
Transaction duration
Number of application processes
```

A useful calculation is:

```text
Potential connections
≈
Application processes × maxPoolSize
```

Then multiply across application instances.

### Corrective Action

Do not immediately increase the pool.

First determine whether queries or transactions are holding connections too long.

## Scenario: Application Restarts Frequently

### Problem

Django or FastAPI pods restart and MongoDB connections spike.

### Possible Causes

- Incorrect health checks
- Startup dependency failures
- Aggressive liveness probes
- Insufficient resource limits
- MongoDB connectivity issues
- Connection initialization failures

### Investigation

Check:

```text
Pod restart count
Application startup logs
MongoDB connection errors
Readiness state
Liveness state
CPU
Memory
```

A readiness failure should not necessarily kill the process.

Separate:

```text
Can this instance receive traffic?
```

from:

```text
Is this process fundamentally unhealthy?
```

## Scenario: Backup Exists but Restore Fails

### Problem

The team discovers that a backup cannot restore successfully during an incident.

### Root Cause

Backup existence was treated as proof of recoverability.

### Better Process

```text
Backup
  ↓
Automated Validation
  ↓
Test Restore
  ↓
Application Validation
  ↓
Measure Recovery Time
  ↓
Document Runbook
```

Define:

- RPO
- RTO
- Backup retention
- Restore ownership
- Recovery environment
- Validation procedure

Recovery testing should be performed regularly.

## Scenario: Design a Disaster Recovery Strategy

### Requirement

The MongoDB-backed application must recover from regional infrastructure failure.

Evaluate:

| Requirement | Decision |
|---|---|
| RPO | How much data loss is acceptable? |
| RTO | How quickly must service recover? |
| Region failure | Is cross-region recovery required? |
| Data residency | Where can data be stored? |
| Backup | How frequently are backups taken? |
| PITR | Is point-in-time recovery required? |
| DNS | How is traffic redirected? |
| Secrets | How are credentials recovered? |
| Validation | How is recovered data verified? |

The database recovery plan must include the application.

```text
Database Recovery
       +
Application Recovery
       +
Configuration Recovery
       +
Traffic Recovery
       =
Complete DR Strategy
```

## Scenario: Schema Evolution

### Problem

The application currently stores:

```json
{
  "name": "Alice"
}
```

A new version requires:

```json
{
  "name": "Alice",
  "profile": {
    "timezone": "Asia/Kolkata"
  }
}
```

### Options

For backward-compatible changes, applications can support both versions temporarily.

```python
timezone = document.get(
    "profile",
    {},
).get(
    "timezone",
    "UTC",
)
```

For large migrations:

```text
Deploy compatible application
        ↓
Backfill documents
        ↓
Validate migration
        ↓
Switch reads
        ↓
Remove legacy behavior
```

Avoid requiring a massive blocking migration unless the workload and operational environment support it.

## Scenario: Enforce Schema Validation

### Requirement

Multiple services write to the same MongoDB collection.

Application validation alone is insufficient because not every writer uses the same validation code.

### Solution

Use MongoDB schema validation for persistence-level constraints.

Combine:

```text
API Validation
      +
Service Validation
      +
MongoDB Validation
```

The layers serve different purposes.

## Scenario: Import Millions of Documents

### Requirement

Import a large dataset into MongoDB.

### Risks

- Excessive memory usage
- Large transactions
- Index maintenance cost
- Network saturation
- Duplicate data
- Application downtime

### Approach

Consider:

```text
Validate source
   ↓
Batch input
   ↓
Bulk writes
   ↓
Controlled concurrency
   ↓
Monitor errors
   ↓
Validate counts
   ↓
Validate indexes
```

Do not load millions of documents into Python memory at once.

Use streaming and bounded batches.

## Scenario: Bulk Update Is Too Slow

### Problem

A migration updates millions of documents.

### Possible Causes

- Poor filter
- Missing index
- Large documents
- Too many indexes
- Excessive batch size
- Resource contention

### Better Approach

Use controlled bulk operations:

```python
from pymongo import UpdateMany

operations = [
    UpdateMany(
        {"status": "legacy"},
        {
            "$set": {
                "status": "active",
            }
        },
    )
]

collection.bulk_write(
    operations,
    ordered=False,
)
```

For very large migrations, design the migration as an operational job with:

- Progress tracking
- Resume capability
- Rate limiting
- Monitoring
- Rollback or compensating strategy

## Scenario: Index Creation Impacts Production

### Problem

A large production collection needs a new index.

### Risks

Index creation can consume substantial resources.

Evaluate:

- Collection size
- Available resources
- Query workload
- Deployment topology
- Index build behavior
- Maintenance window requirements
- Managed service capabilities

Do not treat index creation as a trivial metadata operation on very large collections.

## Scenario: Index Is No Longer Used

### Problem

A production system has dozens of indexes accumulated over several years.

### Risks

- Storage consumption
- Memory pressure
- Slower writes
- Index maintenance
- Operational complexity

### Investigation

Review index usage statistics and actual application query patterns.

Before removing an index:

1. Confirm its usage history.
2. Search application code and operational queries.
3. Check scheduled jobs.
4. Check reporting workloads.
5. Evaluate rollback strategy.
6. Remove carefully.
7. Monitor after removal.

Unused indexes should be treated as technical debt.

## Scenario: Production Query Regression

### Problem

A query was fast last month but is now slow.

### Possible Reasons

```text
Data growth
Query shape changed
Data distribution changed
Index changed
Working set no longer fits memory
Execution plan changed
Infrastructure degraded
```

### Investigation

Compare:

```text
Historical latency
Current latency
Historical explain plan
Current explain plan
Document count
Index size
Data distribution
Infrastructure metrics
```

Performance is a moving property of a production workload.

## Scenario: Large Documents Cause High Memory Usage

### Symptom

Django workers consume excessive memory when returning MongoDB results.

### Possible Causes

- Large documents
- Large result sets
- Missing projection
- Unbounded aggregation results
- Serialization overhead

### Corrective Actions

- Project only required fields
- Limit result sets
- Use pagination
- Stream where appropriate
- Redesign large documents
- Move large reports to background processing

The application may become the bottleneck even when MongoDB itself is healthy.

## Scenario: API Returns MongoDB Documents Directly

### Problem

A developer writes:

```python
return JsonResponse(document)
```

### Risks

- `ObjectId` serialization issues
- Internal fields exposed
- Sensitive fields leaked
- Database schema becomes API contract
- Future schema changes become breaking changes

### Better Design

Map persistence documents to API schemas explicitly.

```text
MongoDB Document
      ↓
Domain Representation
      ↓
API Serializer
      ↓
JSON
```

## Scenario: MongoDB Is Unavailable

### Requirement

The API must fail gracefully if MongoDB is temporarily unavailable.

### Incorrect Behavior

```text
MongoDB unavailable
      ↓
Every request retries repeatedly
      ↓
Database remains unavailable
      ↓
Application load increases
```

### Better Behavior

Use:

- Connection timeouts
- Request timeouts
- Bounded retries
- Exponential backoff
- Circuit-breaking patterns where appropriate
- Clear `503 Service Unavailable` responses
- Health monitoring

The API should not turn a database outage into a retry storm.

## Scenario: Database Outage and Circuit Breaking

A service may implement:

```text
Request
  ↓
MongoDB
  │
  ├── Healthy → Return result
  │
  └── Failure
       ↓
    Retry policy
       ↓
    Failure threshold
       ↓
    Circuit open
       ↓
    Fail fast
```

Circuit breaking is an application-level resilience mechanism. It should be used carefully and should not hide persistent database failures from monitoring.

## Scenario: Design a Read-Heavy Catalog

### Requirement

A product catalog receives:

```text
100,000 reads/sec
1,000 writes/sec
```

### Possible Architecture

```text
Clients
   │
   ▼
Load Balancer
   │
   ▼
Django / FastAPI
   │
   ├── Redis
   │
   └── MongoDB Replica Set
```

Potential strategies:

- Appropriate indexes
- Projection
- Redis caching
- Primary/secondary read strategy where consistency permits
- CDN for externally cacheable content
- Product document modeling optimized for reads

Do not assume the database alone should handle every repeated read.

## Scenario: Design a Write-Heavy Event Store

### Requirement

Millions of events are written continuously.

Documents:

```json
{
  "event_id": "event-123",
  "source": "service-a",
  "type": "order.created",
  "created_at": "2026-09-27T10:00:00Z",
  "payload": {
    "order_id": "order-123"
  }
}
```

Design considerations:

- Append-oriented schema
- Appropriate indexes
- Retention policy
- TTL where applicable
- Archival
- Batch ingestion
- Write concern
- Storage growth
- Sharding if required
- Consumer architecture

Avoid creating unnecessary indexes on high-volume write collections.

## Scenario: TTL for Temporary Data

### Requirement

Session-like records should automatically expire.

Example:

```javascript
db.sessions.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0 }
)
```

Document:

```json
{
  "_id": "session-123",
  "user_id": "user-1",
  "expires_at": "2026-09-27T12:00:00Z"
}
```

TTL indexes are useful for:

- Temporary sessions
- Ephemeral tokens
- Temporary records
- Data retention workflows

Do not use TTL as a substitute for a comprehensive compliance or archival strategy.

## Scenario: Soft Delete

### Requirement

Records must appear deleted to normal users but remain recoverable.

Document:

```json
{
  "_id": "user-123",
  "deleted_at": null
}
```

Normal query:

```python
{
    "tenant_id": tenant_id,
    "deleted_at": None,
}
```

Important considerations:

- Index design
- Unique constraints
- Restore semantics
- Storage growth
- Compliance requirements
- Permanent deletion policies

Soft deletion is not the same as data deletion.

## Scenario: Unique Constraint With Soft Deletes

Suppose emails must be unique only for active users.

A partial unique index can be appropriate:

```javascript
db.users.createIndex(
  { tenant_id: 1, email: 1 },
  {
    unique: true,
    partialFilterExpression: {
      deleted_at: null
    }
  }
)
```

This demonstrates an important senior-level principle: database constraints can encode business rules when those rules are stable and persistence-level.

## Scenario: Production Data Migration

### Requirement

Rename:

```text
customer_name
```

to:

```text
customer.name
```

### Safer Strategy

```text
Deploy backward-compatible code
        ↓
Write new format
        ↓
Read both formats
        ↓
Backfill old documents
        ↓
Validate migration
        ↓
Remove legacy reads
```

This avoids requiring the entire collection to be migrated before the application can deploy.

## Scenario: MongoDB and Django Deployment Rollback

### Problem

A new application release expects a new MongoDB field structure, but the release must be rolled back.

### Risk

If the new release performed an incompatible schema migration, the old application may fail.

### Better Strategy

Use backward-compatible schema changes:

```text
Version N
   ↓
Deploy compatibility support
   ↓
Migrate data
   ↓
Deploy Version N+1
```

Schema migrations should be designed with application rollback in mind.

## Scenario: Monitor MongoDB in Production

At minimum, monitor:

```text
Application
├── Request rate
├── Error rate
├── Latency
└── Saturation

MongoDB
├── Query latency
├── Connections
├── CPU
├── Memory
├── Storage
├── Replication lag
├── Operation rate
└── Slow queries
```

The important relationship is:

```text
Application Metrics
        +
Database Metrics
        +
Infrastructure Metrics
        =
Useful Diagnosis
```

Monitoring only HTTP latency is insufficient.

## Scenario: Design a MongoDB Operational Runbook

A production runbook should contain:

### Connection Failure

```text
Check application logs
↓
Validate URI
↓
Test DNS
↓
Test network
↓
Test authentication
↓
Inspect MongoDB health
```

### Slow Query

```text
Identify endpoint
↓
Capture query shape
↓
Run explain()
↓
Inspect indexes
↓
Measure data examined
↓
Optimize
↓
Validate
```

### Replica Failure

```text
Check rs.status()
↓
Identify failed member
↓
Check network
↓
Check storage
↓
Check replication lag
↓
Determine recovery action
```

### Backup Failure

```text
Check backup job
↓
Inspect logs
↓
Validate storage
↓
Verify backup artifact
↓
Test restore
↓
Document outcome
```

Runbooks reduce dependence on individual engineers during incidents.

## Scenario: Choose MongoDB Versus PostgreSQL

### Requirement

A team is deciding whether to store application data in MongoDB or PostgreSQL.

Evaluate:

| Requirement | MongoDB | PostgreSQL |
|---|---|---|
| Flexible document structure | Strong fit | JSONB available |
| Complex relational joins | Possible but different model | Strong fit |
| Document-oriented access | Strong fit | Possible |
| Relational constraints | Limited compared with relational model | Strong fit |
| SQL analytics | No | Strong fit |
| Embedded aggregates | Strong fit | JSONB/composite options |
| Django native ORM | Not native relational semantics | Strong fit |
| Horizontal sharding | Available | Available through various architectures |
| Transactions | Supported | Strong relational transaction model |

The correct answer depends on workload and domain requirements, not database popularity.

## Scenario: MongoDB Versus Redis

MongoDB and Redis should not be treated as interchangeable.

```text
MongoDB → Durable document persistence
Redis   → Cache / ephemeral state / coordination
```

If data must survive application restarts and represent system-of-record state, MongoDB is generally the persistence layer.

If data can be reconstructed and is primarily used to accelerate reads, Redis may be appropriate.

## Scenario: MongoDB Versus Kafka

Kafka is an event-streaming platform, not a direct replacement for MongoDB persistence.

A common architecture is:

```text
Application
    │
    ├── MongoDB → Current state
    │
    └── Kafka   → Events
```

MongoDB answers:

```text
What is the current state?
```

Kafka can answer:

```text
What events occurred?
```

A system may need both.

## Scenario: Diagnose a Noisy Neighbor

### Problem

One tenant causes latency for all other tenants.

### Investigation

Measure:

- Requests per tenant
- MongoDB operations per tenant
- Query latency
- Document size
- Connection usage
- Cache hit rate
- Storage distribution

### Solutions

Depending on the workload:

- Tenant-level rate limiting
- Query optimization
- Caching
- Workload isolation
- Dedicated resources for very large tenants
- Sharding strategy
- Separate collections/databases for exceptional tenants

Multi-tenancy is both a data-modeling and capacity-planning problem.

## Scenario: Production Security Review

Use this checklist:

```text
Authentication
    ↓
Authorization
    ↓
Least privilege
    ↓
TLS
    ↓
Network restrictions
    ↓
Secret management
    ↓
Encryption
    ↓
Audit requirements
    ↓
Monitoring
    ↓
Credential rotation
```

Application security and MongoDB security must work together.

A secure API with unrestricted public MongoDB access is still insecure.

## Scenario: Interviewer Asks "What Would You Do First?"

When given an unfamiliar MongoDB production problem, do not immediately prescribe a technology.

Use:

```text
1. Clarify the symptom.
2. Establish the expected behavior.
3. Measure the current behavior.
4. Identify the affected component.
5. Inspect the relevant MongoDB operation.
6. Check query/index/data-model characteristics.
7. Identify the failure mode.
8. Apply the smallest safe correction.
9. Validate the result.
10. Add monitoring or prevention.
```

This demonstrates engineering judgment rather than memorized MongoDB commands.

## Scenario: Full Production Architecture

A mature MongoDB-backed Python service might look like:

```text
                         Internet
                            │
                            ▼
                     Load Balancer
                            │
                            ▼
                         Nginx
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
             Django                  FastAPI
                │                       │
                └───────────┬───────────┘
                            │
                     Service Layer
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
              Redis Cache        Mongo Repository
                                      │
                                      ▼
                              MongoDB Replica Set
                              ├── Primary
                              ├── Secondary
                              └── Secondary
                                      │
                              ┌───────┴────────┐
                              ▼                ▼
                           Backups         Monitoring

                    Background Processing
                            │
                            ▼
                         Celery
                            │
                            ▼
                         Workers

                    Event Streaming
                            │
                            ▼
                          Kafka
```

Senior-level concerns include:

- Stateless application instances
- Connection-pool sizing
- Query-driven indexes
- Data-model correctness
- API authorization
- Cache strategy
- Event consistency
- Replica-set health
- Backup and restore
- Observability
- Capacity planning
- Disaster recovery

## Senior Interview Decision Framework

When answering any MongoDB scenario, structure the response around:

### Requirement

What business or technical requirement must be satisfied?

### Workload

Determine:

```text
Read/write ratio
Request rate
Document size
Data volume
Growth rate
Query patterns
```

### Data Model

Choose:

```text
Embedding
References
Controlled duplication
Separate collections
```

based on access patterns.

### Indexes

Determine:

```text
Equality
Sort
Range
Selectivity
Cardinality
```

and validate using execution statistics.

### Consistency

Determine:

```text
Strong consistency requirement
Read preference
Read concern
Write concern
Transaction requirement
```

### Availability

Determine:

```text
Replica-set topology
Failure domains
Failover expectations
RPO
RTO
```

### Scalability

Determine whether the workload requires:

```text
Vertical scaling
Caching
Read scaling
Data lifecycle management
Sharding
```

### Security

Verify:

```text
Authentication
Authorization
Tenant isolation
TLS
Secrets
Network restrictions
Auditing
```

### Operations

Define:

```text
Monitoring
Logging
Alerting
Backups
Restore tests
Runbooks
Capacity planning
```

## Common Scenario-Based Interview Traps

### "Add an Index"

An index is not automatically the answer. First inspect the query shape and execution plan.

### "Use Transactions"

Transactions solve atomicity problems but introduce coordination and performance costs. First determine whether the data model can provide atomicity within one document.

### "Use Redis"

Caching does not fix poor query design.

### "Shard It"

Sharding adds significant operational complexity. Optimize schema, indexes, queries, and lifecycle management first.

### "Read From Secondaries"

Secondary reads can improve scalability but may introduce stale reads.

### "Create a Database Per Tenant"

This may improve isolation but can become operationally expensive at high tenant counts.

### "Use `$lookup` Everywhere"

Frequent joins may indicate that the data model does not match the workload.

### "Use `skip()` for Pagination"

Simple offset pagination can become expensive for deep pages.

### "Retry Everything"

Unbounded retries can amplify an outage.

### "Backups Exist"

A backup that has never been restored is not a validated recovery strategy.

## Production Scenario Checklist

Before finalizing a MongoDB design, verify:

- Access patterns are explicitly identified.
- Document boundaries are based on read and write behavior.
- Embedded arrays are bounded.
- Indexes support high-value queries.
- Query plans have been measured.
- Pagination is appropriate for dataset size.
- Transactions are used only where required.
- Read and write concerns match business requirements.
- Replica-set topology matches availability requirements.
- Sharding is considered only when scale requires it.
- Tenant isolation is enforced server-side.
- MongoDB credentials use least privilege.
- TLS and network restrictions are configured.
- Connection pools are sized across all application instances.
- Retry behavior is bounded and idempotent where required.
- Slow queries are monitored.
- Replication lag is monitored.
- Backups are tested through actual restores.
- RPO and RTO are documented.
- Schema migrations support application rollback.
- Operational runbooks exist.
- Failure scenarios have been tested.

## Key Takeaways

- Scenario-based MongoDB interviews are primarily about engineering reasoning: start with workload, access patterns, consistency, scale, and failure requirements before selecting MongoDB features.
- Data modeling and indexing must be designed together; embedding, references, compound indexes, pagination, and aggregation should reflect real production access patterns.
- Senior designs explicitly address failure modes, including replica elections, stale reads, transaction failures, connection exhaustion, cache stampedes, duplicate writes, and partial failures across databases or event systems.
- High availability and scalability require more than adding replicas or sharding; topology, shard keys, connection pools, workload distribution, monitoring, and recovery procedures must all be considered.
- A production-ready MongoDB answer always includes security, observability, backup and recovery, operational runbooks, measurable performance validation, and a clear prevention strategy.