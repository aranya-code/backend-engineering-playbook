# 14- Troubleshooting Questions

## Overview

MongoDB troubleshooting interviews evaluate whether an engineer can move from symptoms to measurable evidence, isolate the failure domain, identify the root cause, and implement a safe corrective action.

A strong troubleshooting process is:

```text
Symptom
   ↓
Define expected behavior
   ↓
Collect evidence
   ↓
Identify failure domain
   ↓
Isolate query / application / database / infrastructure
   ↓
Validate hypothesis
   ↓
Apply corrective action
   ↓
Measure recovery
   ↓
Prevent recurrence
```

The key principle is:

> Do not optimize or change MongoDB configuration before establishing what is actually failing.

A production incident may involve several layers simultaneously:

```text
Client
  ↓
Load Balancer / Nginx
  ↓
Django / FastAPI
  ↓
Repository / Driver
  ↓
Connection Pool
  ↓
MongoDB
  ↓
Storage / Network / Infrastructure
```

A senior engineer determines which layer is responsible before making changes.

## MongoDB Troubleshooting Workflow

Use the following workflow for most MongoDB incidents.

### Identify the Symptom

Define the problem precisely:

```text
What is slow?
What is failing?
When did it start?
Is it intermittent or constant?
Which endpoint or operation is affected?
Are all users affected?
Is one tenant affected?
Did traffic or data volume change?
```

Avoid vague statements such as:

```text
MongoDB is slow.
```

Prefer:

```text
GET /orders latency increased from 80 ms to 1.8 s
for approximately 20% of requests after 14:00 UTC.
```

### Establish the Baseline

Compare:

- Current latency
- Historical latency
- Request rate
- Error rate
- Query execution time
- CPU
- Memory
- Storage
- Connections
- Replication lag
- Data volume
- Index size

### Isolate the Layer

Determine whether the problem exists in:

| Layer | Examples |
|---|---|
| Client | Network timeout, DNS |
| API | Serialization, application CPU |
| Driver | Pool exhaustion, connection timeout |
| Query | Missing index, inefficient filter |
| Database | Resource saturation |
| Replica set | Elections, replication lag |
| Storage | Disk latency, capacity |
| Network | Packet loss, latency |
| Deployment | Configuration or topology change |

### Validate With Evidence

Useful evidence includes:

```text
explain("executionStats")
rs.status()
db.serverStatus()
db.stats()
db.collection.stats()
db.collection.aggregate(...)
db.currentOp()
```

The exact diagnostic command should match the failure domain.

## Scenario: MongoDB Connection Fails

### Symptom

A FastAPI application reports:

```text
ServerSelectionTimeoutError
```

### Possible Causes

- Incorrect connection string
- MongoDB unavailable
- DNS failure
- Network restriction
- Firewall/security group
- TLS mismatch
- Authentication failure
- Replica-set discovery issue
- Incorrect hostname or port
- Container networking problem

### Isolation Strategy

Start outside the application.

Test:

```bash
mongosh "mongodb://localhost:27017"
```

For a remote deployment:

```bash
mongosh "mongodb://user:password@mongodb.example.com:27017/?authSource=admin"
```

Then verify:

```text
DNS resolution
Network reachability
Port accessibility
TLS configuration
Credentials
Replica-set configuration
```

### Docker Example

If the application runs in Docker, this is often incorrect:

```text
mongodb://localhost:27017
```

Inside a container, `localhost` refers to the application container itself.

A Docker Compose service may instead use:

```text
mongodb://mongo:27017
```

where `mongo` is the MongoDB service name.

### Prevention

- Validate configuration during startup.
- Use environment-based configuration.
- Avoid hard-coded connection strings.
- Add connectivity checks to readiness handling.
- Monitor connection failures separately from application errors.

## Scenario: Authentication Fails

### Symptom

The application receives an authentication error.

### Possible Causes

- Incorrect username
- Incorrect password
- Wrong `authSource`
- User created in a different database
- Authentication mechanism mismatch
- Credential rotation issue
- Secret not mounted correctly

### Investigation

Test with the same credentials:

```bash
mongosh \
  "mongodb://app_user:password@mongo.example.com:27017/appdb?authSource=admin"
```

Check the user's authentication database.

The database where a MongoDB user is defined matters.

### Common Mistake

Assuming:

```text
application database = authentication database
```

These may be different.

### Production Considerations

- Store credentials in a secret manager.
- Rotate credentials.
- Use least-privilege roles.
- Never log connection strings.
- Avoid embedding credentials in source code.

## Scenario: TLS Connection Fails

### Symptoms

The application cannot establish a secure connection.

Possible errors include:

```text
TLS handshake failure
certificate verification failure
SSL error
```

### Possible Causes

- Expired certificate
- Incorrect CA bundle
- Hostname mismatch
- TLS version mismatch
- Client certificate issue
- Incorrect driver configuration

### Investigation

Verify:

```text
Certificate validity
Certificate chain
Hostname
CA configuration
Driver configuration
Server TLS configuration
```

For production, do not solve certificate problems by disabling verification.

Avoid configurations equivalent to:

```text
tlsAllowInvalidCertificates=true
```

unless there is a narrowly controlled diagnostic purpose.

## Scenario: Query Suddenly Becomes Slow

### Symptom

A query that normally takes:

```text
30 ms
```

now takes:

```text
2 seconds
```

### Investigation

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

### Interpretation

A useful signal is:

```text
totalDocsExamined >> nReturned
```

For example:

```text
nReturned = 10
totalDocsExamined = 2,000,000
```

This suggests that MongoDB examined far more documents than the query returned.

### Possible Causes

- Missing index
- Poor index design
- Data growth
- Changed data distribution
- Query shape changed
- Inefficient sort
- Working-set pressure
- Infrastructure degradation

## Scenario: Query Uses COLLSCAN

### Symptom

The execution plan contains:

```text
COLLSCAN
```

### Meaning

MongoDB is scanning the collection instead of using an index for that operation.

### Do Not Automatically Assume It Is Wrong

A collection scan can be reasonable when:

- The collection is small.
- The query returns a large percentage of documents.
- An index would not be selective.
- The query is infrequent.

### Investigate

Compare:

```text
Collection size
Documents returned
Documents examined
Query frequency
Execution time
```

A query returning 5 million of 6 million documents may not benefit significantly from an index.

A query returning 10 of 6 million documents is a different situation.

## Scenario: Index Exists but Query Is Still Slow

### Symptom

The collection has an apparently relevant index, but the query remains slow.

### Possible Causes

- Wrong field order
- Poor selectivity
- Sort not supported
- Index does not match the query shape
- Too many keys examined
- Multikey behavior
- Query transformation
- Fetching large documents
- Index is not actually the winning plan

### Investigation

Use:

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  status: "active"
}).sort({
  created_at: -1
}).explain("executionStats")
```

Look for:

```text
IXSCAN
FETCH
SORT
COLLSCAN
```

An index being present does not mean it is the right index.

## Scenario: Query Has an Expensive SORT

### Symptom

The plan contains:

```text
SORT
```

after fetching documents.

### Example Query

```javascript
db.orders.find({
  tenant_id: "tenant-123",
  status: "active"
}).sort({
  created_at: -1
})
```

Potential index:

```javascript
db.orders.createIndex({
  tenant_id: 1,
  status: 1,
  created_at: -1
})
```

This allows the index to support filtering and ordering more effectively.

### Production Validation

Compare:

```text
Before:
IXSCAN → FETCH → SORT

After:
IXSCAN → FETCH
```

Do not assume the new index is beneficial until execution statistics confirm it.

## Scenario: `totalKeysExamined` Is Very High

### Symptom

The query returns 20 documents but examines hundreds of thousands of index keys.

### Possible Causes

- Poor selectivity
- Incorrect compound index order
- Low-cardinality leading field
- Query shape mismatch
- Large range scan

### Investigation

Compare:

```text
nReturned
totalKeysExamined
totalDocsExamined
```

A healthy selective query often has relatively small examination-to-result ratios.

### Corrective Action

Reconsider:

- Compound index ordering
- Equality fields
- Sort fields
- Range fields
- Query predicates
- Data distribution

## Scenario: Pagination Becomes Slower on Deep Pages

### Symptom

Page 1:

```text
20 ms
```

Page 10,000:

```text
2 seconds
```

### Likely Cause

Offset pagination:

```javascript
db.orders.find(query)
  .sort({ created_at: -1 })
  .skip(200000)
  .limit(20)
```

### Better Approach

Use cursor-based pagination.

A stable ordering can use:

```text
created_at + _id
```

The cursor should contain the values necessary to continue from the previous result set.

### Interview Point

`skip()` is not inherently incorrect. It becomes problematic when page depth and dataset size grow.

## Scenario: Duplicate Records Are Being Created

### Symptom

Two requests create the same logical entity.

### Incorrect Pattern

```python
existing = collection.find_one({"email": email})

if not existing:
    collection.insert_one({
        "email": email,
    })
```

### Why It Fails

Two requests can execute:

```text
Request A → find → nothing
Request B → find → nothing

Request A → insert
Request B → insert
```

### Correct Approach

Enforce uniqueness in MongoDB:

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

Handle:

```python
from pymongo.errors import DuplicateKeyError
```

The database constraint closes the race condition.

## Scenario: Updates Are Not Taking Effect

### Symptom

An update operation succeeds but the expected document remains unchanged.

### Possible Causes

- Incorrect filter
- Wrong `_id` type
- Wrong database
- Wrong collection
- Update path incorrect
- Application is reading stale data
- Update matched zero documents

### Inspect the Result

```python
result = collection.update_one(
    {"_id": user_id},
    {"$set": {"status": "active"}},
)

print(result.matched_count)
print(result.modified_count)
```

Interpretation:

| Result | Meaning |
|---|---|
| `matched_count = 0` | Filter matched nothing |
| `matched_count = 1`, `modified_count = 0` | Document matched but no change was necessary |
| `modified_count = 1` | Document was changed |

## Scenario: `_id` Query Returns Nothing

### Symptom

The document exists, but:

```python
collection.find_one({"_id": "64f..."})
```

returns `None`.

### Possible Cause

The database stores `_id` as an `ObjectId`, not a string.

Correct:

```python
from bson import ObjectId

document = collection.find_one({
    "_id": ObjectId(user_id),
})
```

### Common Mistake

Converting every ID to `ObjectId` without validation.

An invalid value can raise:

```text
InvalidId
```

Validate input before constructing the query.

## Scenario: Update Accidentally Deletes Fields

### Problem

A developer uses replacement semantics:

```python
collection.replace_one(
    {"_id": user_id},
    {
        "name": "Alice",
    },
)
```

This replaces the document rather than modifying only `name`.

### Safer Partial Update

```python
collection.update_one(
    {"_id": user_id},
    {
        "$set": {
            "name": "Alice",
        }
    },
)
```

Use replacement only when the application intentionally owns the entire document representation.

## Scenario: Bulk Write Is Failing Partially

### Symptom

A bulk operation processes some operations but not others.

### Investigation

Determine:

```text
ordered=True or False
```

With ordered operations, execution can stop at an error.

With unordered operations, independent operations can continue.

Inspect the bulk result and exceptions rather than assuming all operations succeeded or all failed.

### Production Considerations

For large migrations:

- Use bounded batches.
- Track progress.
- Make operations idempotent.
- Capture failures.
- Support resume.
- Avoid loading the entire dataset into memory.

## Scenario: Aggregation Is Extremely Slow

### Symptom

An aggregation endpoint takes several seconds or minutes.

### Investigation

Inspect:

```text
Input size
$match selectivity
$lookup cardinality
$unwind expansion
$group cardinality
$sort cost
Intermediate results
Indexes
```

### Common Problem

Starting with:

```text
$lookup
↓
$unwind
↓
$group
↓
$match
```

when filtering could have happened earlier.

Prefer:

```text
$match
↓
$project
↓
$lookup
↓
$unwind
↓
$group
```

when the semantics permit.

### Principle

Reduce the number and size of documents as early as possible.

## Scenario: `$lookup` Is Slow

### Possible Causes

- Missing index on the foreign collection
- Large join cardinality
- Large documents
- Excessive data entering the lookup
- Poor schema design

### Investigation

Determine:

```text
How many documents enter $lookup?
How many matches exist per document?
Is the join field indexed?
Can the data be embedded?
Can the result be precomputed?
```

Do not treat `$lookup` as equivalent to an inexpensive relational join.

## Scenario: Aggregation Consumes Too Much Memory

### Symptoms

- High database resource usage
- Long-running aggregation
- Large sorts or groups
- API timeouts

### Possible Causes

- Large `$sort`
- High-cardinality `$group`
- Large `$unwind`
- Huge intermediate datasets
- Missing early filtering

### Corrective Actions

- Filter earlier.
- Project only required fields.
- Add appropriate indexes.
- Reduce intermediate result sizes.
- Precompute expensive reports.
- Move heavy analytics to asynchronous workflows.

## Scenario: Application Requests Time Out

### Symptom

FastAPI returns:

```text
504 Gateway Timeout
```

### Do Not Assume MongoDB Is the Cause

The request path may be:

```text
Client
  ↓
Nginx
  ↓
Load Balancer
  ↓
FastAPI
  ↓
MongoDB
```

Potential timeout sources include:

- Nginx
- Load balancer
- Application server
- Driver
- MongoDB
- External service

### Investigation

Compare timestamps across:

```text
Nginx logs
Application logs
MongoDB query duration
Database metrics
```

A senior engineer correlates timestamps using a request ID or trace ID.

## Scenario: MongoDB Connection Pool Is Exhausted

### Symptoms

- Requests queue
- MongoDB appears healthy
- Application latency rises
- Connection count is high

### Possible Causes

- Pool too small
- Long-running queries
- Long transactions
- Too many application workers
- Too many Kubernetes replicas
- Connections held longer than necessary

### Important Calculation

If:

```text
20 pods
×
4 worker processes
×
100 max connections
```

the theoretical application-side connection demand can become substantial.

The exact number depends on the driver and process architecture, but the principle is critical:

> Pool settings must be evaluated across the entire deployment, not per process in isolation.

### Corrective Actions

- Measure query duration.
- Measure pool utilization.
- Reduce unnecessary transaction duration.
- Fix slow queries.
- Recalculate pool capacity.
- Avoid blindly increasing pool size.

## Scenario: MongoDB CPU Is High

### Possible Causes

- High query volume
- Collection scans
- Expensive aggregation
- Large sorts
- Regex queries
- High write throughput
- Index maintenance
- Resource-intensive workloads

### Investigation

Correlate:

```text
CPU
Operations/sec
Query latency
Slow queries
Execution plans
Aggregation workload
Index changes
Traffic
```

High CPU is a symptom, not a root cause.

## Scenario: MongoDB Memory Usage Is High

MongoDB uses memory aggressively for database operations and caching.

High memory usage is not automatically a failure.

Investigate:

- Working set
- Cache behavior
- Index size
- Collection size
- Large documents
- Aggregation workloads
- Operating-system memory pressure

The important question is:

```text
Is the system under memory pressure?
```

rather than:

```text
Is MongoDB using a lot of RAM?
```

## Scenario: Disk Usage Is Growing Rapidly

### Possible Causes

- Data growth
- Large documents
- Index growth
- Oplog growth
- Temporary workload
- Missing TTL/retention policy
- Excessive duplication

### Investigation

Measure:

```text
Data size
Index size
Storage growth rate
Oplog size
Collection growth
Document size
```

### Corrective Actions

Depending on the cause:

- Archive old data.
- Apply lifecycle policies.
- Remove unnecessary indexes.
- Reduce document duplication.
- Resize storage.
- Review retention requirements.

Do not delete data simply to recover disk space without understanding retention and recovery requirements.

## Scenario: Oplog Window Is Shrinking

### Symptom

The available replication history becomes too small for secondary recovery or operational requirements.

### Possible Causes

- Increased write volume
- Insufficient oplog capacity
- Secondary lag
- Large replication workload

### Investigation

Monitor:

```text
Write throughput
Oplog size
Oplog window
Secondary lag
```

The important operational metric is not only oplog size but how much time the oplog currently covers.

## Scenario: Secondary Is Lagging

### Symptom

Replication lag increases.

### Possible Causes

- Slow disk
- CPU saturation
- Network latency
- Heavy writes
- Large indexes
- Expensive workloads
- Insufficient secondary capacity

### Investigation

Use replica-set status and correlate with infrastructure metrics.

```javascript
rs.status()
```

### Corrective Actions

- Investigate resource saturation.
- Improve secondary capacity.
- Reduce unnecessary write amplification.
- Review indexes.
- Review workload distribution.
- Ensure the oplog window provides sufficient recovery margin.

## Scenario: Replica Set Has No Healthy Primary

### Symptom

Applications cannot perform normal writes.

### Possible Causes

- Primary failure
- Election failure
- Network partition
- Majority unavailable
- Misconfigured replica-set members
- Authentication or connectivity issues

### Investigation

```javascript
rs.status()
```

Inspect:

```text
Member state
Health
Last heartbeat
Election information
Replication state
```

Also check network connectivity between members.

### Senior Consideration

A replica set needs a functioning voting majority for normal election behavior. Network partitions can therefore affect availability even when individual servers are healthy.

## Scenario: MongoDB Keeps Electing New Primaries

### Symptom

The application experiences repeated primary changes.

### Possible Causes

- Network instability
- CPU saturation
- Disk latency
- Resource starvation
- Container restarts
- Host failures
- Incorrect deployment topology

### Investigation

Correlate:

```text
Election events
Host health
Network errors
Container restarts
Disk latency
CPU
Memory
```

Repeated elections are an availability problem, not merely an application reconnection problem.

## Scenario: Application Sees Stale Reads

### Symptom

A write succeeds, but a subsequent read returns older data.

### Possible Causes

- Reading from secondary
- Replication lag
- Read preference configuration
- Read concern configuration

### Investigation

Check:

```text
Read preference
Read concern
Replica-set topology
Replication lag
```

### Corrective Action

For operations requiring immediate visibility, use an appropriate consistency strategy rather than assuming every read is served from the primary.

## Scenario: Transaction Fails During Primary Election

### Symptom

A transaction aborts or receives a transient transaction error.

### Possible Causes

- Primary election
- Network interruption
- Transaction lifetime
- Write conflict
- Resource pressure

### Corrective Action

Use the driver's transaction retry mechanisms appropriately and ensure the transaction's business operation is safe to retry.

Never retry a transaction blindly if the surrounding business operation is not idempotent.

## Scenario: Transaction Is Causing Performance Problems

### Symptoms

- Increased latency
- Lock/contention effects
- Increased resource usage
- More transient failures

### Possible Causes

- Long transaction duration
- Too many operations
- Large reads
- External calls inside transaction
- High contention
- Poor indexing

### Better Design

Keep transactions:

```text
Small
Short
Indexed
Deterministic
Retry-aware
```

Avoid:

```text
Start transaction
↓
HTTP call
↓
Wait 2 seconds
↓
Database operation
↓
Another external call
↓
Commit
```

External network calls should generally be outside database transactions.

## Scenario: Change Stream Stops Receiving Events

### Possible Causes

- Connection loss
- Consumer crash
- Replica-set issue
- Resume token problem
- Cursor timeout or lifecycle problem
- Authentication failure

### Investigation

Check:

```text
Consumer logs
Connection state
Replica-set health
Resume token
MongoDB server health
```

### Production Design

Consumers should support:

```text
Connect
↓
Read event
↓
Process idempotently
↓
Persist progress
↓
Reconnect on failure
↓
Resume
```

## Scenario: Change Stream Consumer Processes Duplicate Events

### Root Cause

Event-driven systems commonly provide at-least-once processing semantics.

### Solution

Make the consumer idempotent.

For example:

```text
event_id
   ↓
Check processed-events store
   ↓
Already processed?
   ├── Yes → Ignore
   └── No  → Process
              ↓
          Record completion
```

Do not build a system that assumes a distributed event will always be delivered exactly once.

## Scenario: NoSQL Injection Vulnerability

### Vulnerable Pattern

```python
filters = request.json()["filter"]

collection.find(filters)
```

The client can potentially control MongoDB operators.

### Safer Pattern

Define an explicit API contract:

```python
class UserFilter(BaseModel):
    email: str | None = None
    status: str | None = None
```

Build the MongoDB filter from validated fields:

```python
query = {}

if filters.email is not None:
    query["email"] = filters.email

if filters.status is not None:
    query["status"] = filters.status
```

Never expose arbitrary MongoDB query syntax to external clients.

## Scenario: Sensitive Data Appears in Logs

### Symptom

Application logs contain:

```text
MongoDB URI
Passwords
Access tokens
Customer documents
```

### Risk

Logs can become a separate security boundary.

### Corrective Action

Use structured logging:

```json
{
  "event": "mongo_query_failed",
  "operation": "find_user",
  "request_id": "req-123",
  "error_type": "ServerSelectionTimeoutError"
}
```

Log identifiers and metadata rather than complete sensitive documents.

## Scenario: Backup Succeeds but Restore Fails

### Root Cause

The team verified backup creation but never tested restoration.

### Recovery Validation

```text
Backup
  ↓
Artifact validation
  ↓
Restore into isolated environment
  ↓
Application connectivity test
  ↓
Data integrity validation
  ↓
Measure recovery duration
```

### Interview Point

Backup and recovery are separate capabilities.

A backup strategy without tested restoration does not establish operational recoverability.

## Scenario: `mongorestore` Fails

### Possible Causes

- Authentication issue
- Incorrect URI
- Incompatible dump format
- Wrong namespace
- Existing conflicting data
- Network failure
- Insufficient permissions
- Storage capacity

### Investigation

Validate:

```text
Backup artifact
Connection
Credentials
Target database
Permissions
Available storage
Restore command
```

For production recovery, test the restore procedure before an incident.

## Scenario: Database Disk Is Almost Full

### Immediate Risk

A full filesystem can cause severe operational problems.

### Immediate Investigation

Identify:

```text
Data growth
Index growth
Oplog growth
Logs
Temporary files
Other processes
```

### Response

Do not immediately delete database files manually.

First determine what is consuming the disk and follow the database deployment's supported storage and recovery procedures.

## Scenario: MongoDB Works Locally but Fails in Kubernetes

### Common Causes

- Incorrect service DNS
- Wrong port
- Incorrect connection string
- NetworkPolicy
- Secret configuration
- TLS mismatch
- Replica-set hostname discovery
- Readiness/startup ordering
- Resource limits

### Debugging

From the application pod:

```bash
mongosh "mongodb://mongo:27017"
```

Then test DNS and network connectivity.

### Kubernetes Consideration

MongoDB replica-set members must advertise hostnames that other members and clients can actually resolve and reach.

Container-local addresses should not accidentally become production replica-set addresses.

## Scenario: MongoDB Works in Docker but Not From the Host

### Common Cause

Port mapping is missing or incorrect.

Example:

```yaml
services:
  mongo:
    image: mongo
    ports:
      - "27017:27017"
```

Then:

```text
Host → localhost:27017
Container → mongo:27017
```

These are different networking paths.

## Scenario: Compass Cannot Connect

### Troubleshooting Sequence

```text
Connection string
↓
Hostname
↓
Port
↓
Network access
↓
Authentication
↓
TLS
↓
Replica-set configuration
```

For MongoDB Atlas, also verify:

- Network access rules
- Database user
- Connection string
- TLS requirements
- Client IP access

Do not expose MongoDB publicly simply to make Compass connect.

## Scenario: `mongosh` Connects but Application Does Not

### Possible Causes

- Different connection string
- Different authentication source
- Different DNS resolution
- Different TLS settings
- Different network location
- Driver configuration
- Connection pool behavior

Compare the application configuration directly with the working shell configuration.

## Scenario: Application Has Intermittent MongoDB Errors

### Symptoms

Most requests succeed, but some fail.

### Possible Causes

- Connection pool exhaustion
- Network instability
- Primary elections
- Replica-set topology changes
- Slow queries
- Timeout configuration
- Resource saturation

### Investigation

Correlate:

```text
Request ID
Timestamp
MongoDB operation
Application worker
Connection state
Replica-set events
Database metrics
```

Intermittent failures require correlation rather than single-request inspection.

## Scenario: Retry Storm During MongoDB Outage

### Failure Pattern

```text
MongoDB unavailable
       ↓
Application retries
       ↓
More requests
       ↓
More connection attempts
       ↓
MongoDB recovery becomes harder
```

### Better Strategy

Use:

- Bounded retries
- Exponential backoff
- Jitter
- Short connection timeouts
- Circuit-breaking where appropriate
- Idempotency
- Clear failure responses

Retry policies should be designed as part of the system, not added independently by every service.

## Scenario: Slow API but Fast MongoDB Query

### Symptom

MongoDB reports a 20 ms query, but API latency is 500 ms.

### Possible Causes

- Serialization
- Pydantic validation
- Application computation
- Network latency
- Redis calls
- External APIs
- Thread/process contention
- Large response payload

### Investigation

Trace the complete request:

```text
HTTP request
  ↓
Application logic
  ↓
MongoDB
  ↓
Serialization
  ↓
HTTP response
```

Do not optimize MongoDB when MongoDB is not the bottleneck.

## Scenario: Fast MongoDB Query but High Database CPU

A query can be fast for an individual request while the database is still overloaded due to very high query volume.

For example:

```text
1 query × 5 ms
```

may be harmless.

But:

```text
100,000 queries/sec × 5 ms
```

can represent a substantial workload.

Performance analysis must consider both:

```text
Per-operation latency
```

and:

```text
Aggregate workload
```

## Scenario: Query Works in Compass but Fails in Application

### Possible Causes

- Different database
- Different user
- Different authentication context
- Different query serialization
- Incorrect `ObjectId`
- Different field types
- Different environment variables
- Application query construction bug

### Debugging

Log safe query metadata:

```text
Database
Collection
Operation
Filter field names
Parameter types
Request ID
```

Do not log secrets or complete sensitive documents.

## Scenario: Schema Validation Rejects Writes

### Symptom

Insert or update fails because the document does not satisfy collection validation.

### Investigation

Check:

```text
Required fields
BSON types
Nested fields
Array structure
Validation level
Validation action
```

Compare the failing document against the intended schema.

### Common Mistake

Assuming MongoDB's flexible schema means every document can have arbitrary structure.

Production systems can and often should enforce important structural constraints.

## Scenario: Application Expects a Field That Does Not Exist

### Symptom

A newer application version expects:

```text
profile.timezone
```

but older documents do not contain it.

### Safe Approach

Support the old state temporarily:

```python
timezone = (
    document.get("profile", {}).get("timezone")
    or "UTC"
)
```

Then perform a controlled migration if the field becomes mandatory.

Schema evolution should be compatible with rolling deployments.

## Scenario: Index Exists but Writes Became Slow

### Possible Causes

Every additional index can increase write maintenance work.

A write-heavy collection with many indexes may experience:

```text
Insert
   ↓
Document update
   ↓
Index maintenance
   ↓
More storage I/O
```

### Investigation

Review:

- Number of indexes
- Index size
- Write throughput
- Index usage
- Query requirements

Remove obsolete indexes carefully after verifying they are not required by production workloads.

## Scenario: Too Many Indexes

### Symptoms

- Large storage footprint
- High write cost
- Memory pressure
- Slow index builds
- Operational complexity

### Approach

For every index ask:

```text
Which production query requires this?
How frequently is that query executed?
Is the index selective?
Can another index satisfy the query?
What is the write cost?
```

Indexes are production resources, not free metadata.

## Scenario: Large Document Causes API Memory Spike

### Problem

One MongoDB document contains a very large nested structure.

The API reads and serializes the complete document.

### Corrective Actions

- Use projection.
- Limit nested fields.
- Paginate child data.
- Split independently accessed data.
- Avoid unbounded arrays.
- Stream large responses where appropriate.

Example:

```python
projection = {
    "name": 1,
    "status": 1,
    "profile.timezone": 1,
}
```

Only retrieve what the endpoint needs.

## Scenario: Production Data Was Accidentally Deleted

### Immediate Response

Do not immediately start random restore operations.

Establish:

```text
What was deleted?
When?
Which collection?
How much data?
Can writes continue safely?
What backup exists?
What is the RPO?
What is the recovery point?
```

Then execute the documented recovery runbook.

Possible recovery sources include:

- Backup
- Point-in-time recovery
- Replica-based recovery strategy
- Application-level reconstruction
- Event history

Preserve evidence and avoid making destructive changes during investigation.

## Scenario: One Collection Is Growing Unusually Fast

### Investigation

Measure growth over time:

```text
Document count
Data size
Average document size
Index size
Write rate
Retention
Tenant distribution
```

Potential causes:

- Unexpected traffic
- Duplicate writes
- Retry bugs
- Missing TTL
- Event retention problem
- Schema change
- Large payloads

A sudden storage increase is often an application-level data lifecycle problem rather than a MongoDB capacity problem.

## Scenario: Diagnose a Production Incident

Use a structured incident workflow:

```text
Symptom
↓
Scope
↓
Impact
↓
Timeline
↓
Metrics
↓
Logs
↓
Query / database evidence
↓
Hypothesis
↓
Controlled test
↓
Mitigation
↓
Root cause
↓
Permanent fix
↓
Prevention
```

### Scope

Determine:

- All users or subset?
- One tenant or all tenants?
- One endpoint or all endpoints?
- Reads or writes?
- One collection or database-wide?
- One replica member or all members?

### Impact

Quantify:

```text
Error rate
Latency increase
Affected requests
Affected users
Data integrity risk
Duration
```

Senior troubleshooting is evidence-driven and measurable.

## Scenario: Production Incident Where MongoDB Is the Suspected Cause

Do not start by restarting MongoDB.

Use:

```text
Application metrics
        ↓
MongoDB metrics
        ↓
Query diagnostics
        ↓
Replica-set state
        ↓
Infrastructure metrics
        ↓
Network
```

Restarting a healthy database can destroy useful diagnostic information and potentially increase impact.

## Scenario: MongoDB Health Check Design

A health endpoint should distinguish between:

```text
Liveness
Readiness
Dependency health
```

For example:

```text
/liveness
    → Process is alive

/readiness
    → Instance can safely receive traffic
```

A MongoDB connectivity problem may make an instance unready without necessarily meaning the process itself should be terminated.

This distinction is particularly important in Kubernetes.

## Scenario: Production Diagnostic Command Reference

| Purpose | Command |
|---|---|
| Replica-set state | `rs.status()` |
| Replica configuration | `rs.conf()` |
| Replica-set members | `rs.status()` |
| Database statistics | `db.stats()` |
| Collection statistics | `db.collection.stats()` |
| Index information | `db.collection.getIndexes()` |
| Query execution | `explain("executionStats")` |
| Current operations | `db.currentOp()` |
| Server metrics | `db.serverStatus()` |
| Collection list | `show collections` |
| Database list | `show dbs` |
| Current database | `db` |
| MongoDB connection | `mongosh "<connection-string>"` |

The exact command should be selected based on the incident rather than executed indiscriminately.

## Troubleshooting Query Performance

Use this repeatable workflow:

```text
Slow query
   ↓
Capture exact query shape
   ↓
Run explain("executionStats")
   ↓
Check COLLSCAN / IXSCAN
   ↓
Check nReturned
   ↓
Check totalKeysExamined
   ↓
Check totalDocsExamined
   ↓
Check SORT
   ↓
Review index design
   ↓
Review data distribution
   ↓
Optimize
   ↓
Measure again
```

### Useful Signals

| Signal | What It Helps Identify |
|---|---|
| `COLLSCAN` | Collection scanning |
| `IXSCAN` | Index usage |
| `SORT` | In-memory or blocking sort behavior |
| `nReturned` | Result count |
| `totalKeysExamined` | Index work |
| `totalDocsExamined` | Document work |
| `executionTimeMillis` | Measured execution time |

Do not judge a query solely by whether an index appears in the plan.

## Troubleshooting Replication

Use:

```text
Application symptoms
↓
Check replica-set state
↓
Check member health
↓
Check replication lag
↓
Check network
↓
Check CPU / memory / disk
↓
Check oplog window
↓
Identify failed member
↓
Recover
↓
Validate replication
```

Common failure categories:

| Symptom | Likely Areas |
|---|---|
| No primary | Election, quorum, network |
| Secondary lag | Disk, CPU, network, write rate |
| Frequent elections | Host/network instability |
| Stale reads | Read preference, lag |
| Rollback | Failure timing, write concern |
| Initial sync failure | Network, storage, configuration |

## Troubleshooting Application Integration

For Django and FastAPI, separate:

```text
Framework
   ↓
Repository
   ↓
MongoDB Driver
   ↓
Connection Pool
   ↓
MongoDB
```

A useful diagnostic checklist:

- Is the connection URI correct?
- Is the correct database selected?
- Is authentication configured correctly?
- Is `authSource` correct?
- Is the `_id` type correct?
- Is the query filter correct?
- Is the projection correct?
- Is the cursor consumed correctly?
- Is the connection pool exhausted?
- Are timeouts configured?
- Are exceptions handled correctly?
- Is the application reading from the expected replica-set member?

## Troubleshooting Python Driver Errors

Common categories include:

| Error Category | Typical Cause |
|---|---|
| `ServerSelectionTimeoutError` | Connectivity/topology |
| `DuplicateKeyError` | Unique constraint violation |
| `OperationFailure` | Server-side operation/auth issue |
| `InvalidId` | Invalid `ObjectId` input |
| `BulkWriteError` | Bulk operation failures |
| `NetworkTimeout` | Network/server response delay |
| `ConnectionFailure` | Connection problem |

Handle known exceptions intentionally rather than catching:

```python
except Exception:
    ...
```

and silently continuing.

## Troubleshooting Methodology for Interviews

When an interviewer gives a MongoDB production problem, answer in this order:

### Define the Symptom

```text
What exactly is failing?
```

### Establish Scope

```text
Who is affected?
Which operation?
Which environment?
```

### Collect Evidence

```text
Metrics
Logs
Explain plans
Replica status
Infrastructure health
```

### Form Hypotheses

Keep multiple plausible causes initially.

### Isolate

Change or test one variable at a time when possible.

### Correct

Apply the smallest safe mitigation.

### Validate

Confirm the measured symptom has recovered.

### Prevent

Add:

- Monitoring
- Alerts
- Tests
- Index lifecycle checks
- Runbooks
- Capacity planning
- Safer deployment practices

## Common Troubleshooting Mistakes

### Restarting Before Diagnosing

A restart may temporarily hide the problem and destroy evidence.

### Adding Random Indexes

An index must correspond to a real query pattern and be validated with execution statistics.

### Increasing Timeouts

A larger timeout can hide an underlying performance problem.

### Increasing Connection Pools Blindly

A larger pool can increase database pressure rather than solve the root cause.

### Retrying Everything

Retries can amplify an outage.

### Reading From Secondaries Without Considering Consistency

This can introduce stale results.

### Running Large Production Migrations Without Controls

Unbounded migrations can consume CPU, memory, I/O, and replication capacity.

### Logging Sensitive Queries

Debugging information should not become a security incident.

### Treating Backups as Proven Recovery

Only tested restoration demonstrates operational recoverability.

### Assuming MongoDB Is the Bottleneck

Always trace the complete request path.

## Senior-Level Troubleshooting Principles

### Measure Before Changing

Use:

```text
Baseline
→
Change
→
Measure
```

rather than:

```text
Guess
→
Change
→
Hope
```

### Separate Symptoms From Root Causes

Example:

```text
API timeout
```

is a symptom.

Possible root causes:

```text
Slow MongoDB query
Connection pool exhaustion
Network latency
Serialization overhead
External service delay
```

### Prefer Reversible Changes

During incidents, prioritize mitigations that can be rolled back safely.

### Protect Data First

When correctness is uncertain, avoid destructive actions.

### Understand Failure Domains

Distinguish:

```text
Application failure
Database failure
Node failure
Availability-zone failure
Regional failure
```

### Make Recovery Observable

Recovery should be measurable:

```text
Latency recovered
Error rate recovered
Replication caught up
Connections normalized
Storage stabilized
```

## Production Troubleshooting Checklist

Before closing a MongoDB incident, verify:

- The original symptom is resolved.
- The affected scope is known.
- The root cause has supporting evidence.
- Query performance was measured where relevant.
- Replica health is normal.
- Replication lag is normal.
- Connection usage is normal.
- CPU, memory, disk, and network are healthy.
- No data integrity issue remains.
- Security implications were considered.
- Temporary mitigations are documented.
- Permanent corrective actions are tracked.
- Monitoring or alerting was improved if necessary.
- The runbook was updated when the incident revealed a missing procedure.
- Recovery was validated rather than assumed.

## Key Takeaways

- MongoDB troubleshooting should follow evidence: define the symptom, establish scope, inspect metrics and diagnostics, isolate the failure domain, then make a controlled change.
- Slow queries require execution-plan analysis using `explain("executionStats")`; `COLLSCAN`, `IXSCAN`, `SORT`, `nReturned`, `totalKeysExamined`, and `totalDocsExamined` provide critical evidence.
- Production failures often occur across boundaries between applications, drivers, connection pools, replica sets, networks, and infrastructure; never assume MongoDB is the bottleneck without measurement.
- Reliability requires bounded retries, correct timeout behavior, replica-set monitoring, tested backups, safe migrations, idempotent operations, and explicit recovery procedures.
- Senior troubleshooting is not just incident mitigation: every root cause should lead to measurable prevention through better design, monitoring, testing, capacity planning, or operational runbooks.