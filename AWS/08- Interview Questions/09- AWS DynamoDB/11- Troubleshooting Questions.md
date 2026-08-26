# 08- Troubleshooting Questions

## Overview

DynamoDB troubleshooting interviews evaluate whether an engineer can move beyond API usage and systematically diagnose problems involving access patterns, throttling, latency, consistency, indexes, partition distribution, capacity, networking, permissions, and application behavior.

A strong troubleshooting approach starts with the observed symptom and works backward through the request path:

```text
Application
    ↓
AWS SDK / Boto3
    ↓
IAM / Network
    ↓
DynamoDB API
    ↓
Table / Index
    ↓
Partition Distribution
    ↓
Capacity / Storage / Data Model
```

The goal is to identify the actual bottleneck rather than immediately increasing capacity or adding retries.

---

## Troubleshooting Methodology

### Question

**A DynamoDB API is suddenly experiencing high latency. How would you investigate it?**

**Answer:**

Start by establishing whether the latency is:

- Application-side
- SDK/client-side
- Network-related
- DynamoDB service-side
- Caused by throttling
- Caused by inefficient access patterns

A practical investigation sequence is:

```text
1. Confirm the affected API and time window
        ↓
2. Check application latency and error rates
        ↓
3. Inspect DynamoDB throttling and consumed capacity
        ↓
4. Identify affected table/index
        ↓
5. Check partition-level behavior
        ↓
6. Inspect query/scan patterns
        ↓
7. Check item sizes and returned data
        ↓
8. Inspect SDK retries and retry latency
        ↓
9. Check recent deployments/configuration changes
        ↓
10. Mitigate and validate
```

Do not begin by blindly increasing provisioned capacity. First determine whether the workload is actually capacity-bound.

---

## Metrics to Check First

### Question

**Which DynamoDB metrics would you check during an incident?**

**Answer:**

Important CloudWatch metrics include:

| Metric | What It Helps Identify |
|---|---|
| `ConsumedReadCapacityUnits` | Read workload |
| `ConsumedWriteCapacityUnits` | Write workload |
| `ReadThrottleEvents` | Read throttling |
| `WriteThrottleEvents` | Write throttling |
| `ThrottledRequests` | Requests being throttled |
| `SuccessfulRequestLatency` | DynamoDB-side latency |
| `SystemErrors` | Service-side failures |
| `UserErrors` | Client/request errors |
| `ReturnedItemCount` | Query result volume |
| `ReturnedBytes` | Response size |
| `ConditionalCheckFailedRequests` | Conditional write conflicts |

CloudWatch metrics should be correlated with application metrics rather than viewed in isolation.

For example:

```text
API latency ↑
    +
DynamoDB SuccessfulRequestLatency normal
    +
SDK retry latency ↑
    ↓
Investigate client-side retries or throttling
```

---

## Throttling

### Question

**Your DynamoDB table is returning throttling errors. What would you investigate?**

**Answer:**

First determine:

1. Whether the table is using provisioned or on-demand capacity.
2. Whether reads or writes are being throttled.
3. Whether the table or an index is affected.
4. Whether throttling is distributed across partitions.
5. Whether a single partition key is disproportionately hot.
6. Whether the workload recently changed.
7. Whether the application is generating retry amplification.

The investigation should distinguish between:

```text
Insufficient overall capacity
```

and:

```text
Uneven workload distribution / hot partition
```

Increasing total capacity does not necessarily solve a workload concentrated on a problematic partition.

---

## Hot Partition

### Question

**What is a hot partition and how would you diagnose it?**

**Answer:**

A hot partition occurs when a disproportionate amount of traffic is directed to a small portion of DynamoDB's physical partitions.

A common cause is poor partition-key distribution.

For example:

```text
PK = CUSTOMER#123
```

If millions of requests target that same partition-key value, the logical access pattern can become highly concentrated.

A better design might distribute requests according to the application's access pattern:

```text
CUSTOMER#123#0
CUSTOMER#123#1
CUSTOMER#123#2
...
```

when controlled sharding is appropriate.

However, adding random suffixes should not be done automatically. It complicates reads and writes and should only be introduced when the workload actually requires it.

---

## Diagnosing a Hot Key

### Question

**How would you determine which partition key is causing a hot-key problem?**

**Answer:**

Start from application and access-pattern data.

Useful sources include:

- Request logs
- Partition-key values in structured logs
- API traffic distributions
- DynamoDB Contributor Insights
- CloudWatch metrics
- Application tracing
- Query/write frequency by logical entity

A useful diagnostic question is:

> Is a small number of logical partition-key values responsible for a large percentage of requests?

For example:

```text
Total requests:       10,000,000
CUSTOMER#123:          7,500,000
CUSTOMER#456:            200,000
CUSTOMER#789:            100,000
Others:               2,200,000
```

This workload is highly skewed even if the table has sufficient aggregate capacity.

---

## Question

**Can increasing DynamoDB capacity solve a hot partition?**

**Answer:**

Not necessarily.

If traffic is concentrated on a single partition-key value, simply increasing table-level capacity may not eliminate the underlying distribution problem.

The correct solution depends on the workload:

- Improve partition-key distribution.
- Introduce controlled write sharding.
- Change the access pattern.
- Distribute traffic across multiple logical keys.
- Cache extremely hot reads where appropriate.
- Use a different data model.

The important interview point is:

> Capacity and distribution are separate dimensions of scalability.

---

## Read Throttling

### Question

**A DynamoDB table is experiencing read throttling. What would you check?**

**Answer:**

Check:

- `ReadThrottleEvents`
- `ConsumedReadCapacityUnits`
- Read traffic by table and index
- Strongly consistent read usage
- Query result sizes
- Repeated reads for the same key
- Hot partition keys
- Scan operations
- GSI read traffic
- Application retry behavior

Also check whether the application is unnecessarily requesting strongly consistent reads.

Strongly consistent reads consume more read capacity than eventually consistent reads for the same amount of data.

---

## Write Throttling

### Question

**A table experiences write throttling while overall traffic looks normal. What could cause it?**

**Answer:**

Possible causes include:

- Hot partition keys
- Uneven write distribution
- Large item sizes
- GSI write amplification
- Sudden traffic spikes
- Provisioned capacity being too low
- Bursty workloads
- Multiple indexes receiving the same writes

A particularly important production consideration is GSI write amplification.

For example:

```text
Application Write
       ↓
Base Table
       ↓
GSI 1
       ↓
GSI 2
```

A single application write can therefore create additional index maintenance work.

---

## GSI Throttling

### Question

**The base table has enough capacity, but requests are still being throttled. What would you investigate?**

**Answer:**

Check whether a global secondary index is throttling.

A GSI has its own capacity characteristics and can become the bottleneck.

The request path may look like:

```text
Application
    ↓
Write to Table
    ↓
Base Table Capacity ── OK
    ↓
GSI Update
    ↓
GSI Capacity ── Throttled
```

Inspect table and index metrics independently.

Never assume that healthy base-table metrics mean every access path is healthy.

---

## Latency

### Question

**DynamoDB latency increased after a deployment, but there are no throttling errors. What would you check?**

**Answer:**

Investigate:

- Query vs scan usage
- Number of returned items
- Item sizes
- Projection expressions
- Pagination behavior
- Boto3 retry configuration
- Connection reuse
- Connection-pool configuration
- Application serialization/deserialization
- Network latency
- Recent code changes
- New indexes or access patterns
- Increased request concurrency

Also compare:

```text
DynamoDB service latency
vs
SDK latency
vs
API latency
```

This distinction helps identify where the latency is actually introduced.

---

## Query Is Slow

### Question

**A DynamoDB query is taking too long. What would you check?**

**Answer:**

Check:

- Partition-key selectivity
- Number of items matched
- Sort-key condition
- Filter expressions
- Item size
- Projection
- Pagination
- Index selection
- Number of pages required

A common mistake is assuming a `FilterExpression` makes the database scan less data.

For example:

```python
table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#123"),
    FilterExpression=Attr("status").eq("ACTIVE"),
)
```

The filter is applied after DynamoDB identifies and reads the matching key range.

If the query reads 100,000 items and returns only 100, the access pattern may be inefficient even though the response contains only 100 items.

---

## FilterExpression Misuse

### Question

**Why can a FilterExpression fail to solve a DynamoDB performance problem?**

**Answer:**

A filter does not turn an inefficient access pattern into an efficient one.

Conceptually:

```text
Partition Key / Key Condition
            ↓
Items read
            ↓
FilterExpression
            ↓
Items returned
```

Therefore:

```text
10,000 items read
100 items returned
```

is still a workload involving 10,000 evaluated items.

If the filtered attribute represents a core access pattern, consider:

- A different primary key design
- A GSI
- A different sort-key structure
- A materialized access pattern

---

## Scan Problem

### Question

**You discover that a production API is using `Scan`. What would you do?**

**Answer:**

First determine why the scan exists.

If the API requires retrieving entities based on a non-key attribute, the data model may not support the access pattern.

A production remediation could involve:

```text
Current

API
 ↓
Scan
 ↓
Filter
 ↓
Response
```

Changing to:

```text
API
 ↓
Query
 ↓
Appropriate GSI
 ↓
Response
```

The correct solution is usually data-model redesign rather than simply increasing capacity.

---

## Unexpected Empty Results

### Question

**A DynamoDB query returns no items, but you know the data exists. What would you check?**

**Answer:**

Check:

- Exact partition-key value
- Sort-key condition
- Data types
- Index name
- Index key attributes
- Whether the item exists in the queried index
- Whether the index is sparse
- Region
- AWS account
- Table name
- Eventual consistency
- Application serialization

A common issue is querying a GSI where an item does not contain the required index key attributes.

Such an item may not appear in the index.

---

## GSI Missing Items

### Question

**Why might an item exist in the base table but not appear in a GSI?**

**Answer:**

A GSI can be sparse.

If an item does not contain the required GSI key attributes, DynamoDB does not include that item in the index.

For example:

```text
Base Table

PK              status
ORDER#1         PENDING
ORDER#2         SHIPPED
ORDER#3         <missing>
```

If `status` is an index key, `ORDER#3` may not appear in the GSI.

This is often intentional, but it can also expose incorrect data modeling.

---

## Strong vs Eventual Consistency

### Question

**A newly written item is sometimes not immediately visible to a read. What could be happening?**

**Answer:**

The application may be using eventually consistent reads.

For example:

```text
Write
 ↓
DynamoDB
 ↓
Eventually consistent read
 ↓
May temporarily observe older state
```

For operations that require immediate visibility, use a strongly consistent read where supported.

However, strong consistency should be used selectively because it has different capacity and availability characteristics from eventually consistent reads.

---

## Conditional Check Failures

### Question

**Your application suddenly reports many `ConditionalCheckFailedException` errors. What does that mean?**

**Answer:**

It usually means the application condition is not satisfied.

For example:

```python
ConditionExpression="#status = :pending"
```

If many workers attempt the same state transition:

```text
Worker A ── PENDING → CONFIRMED
Worker B ── PENDING → CONFIRMED
Worker C ── PENDING → CONFIRMED
```

Only one may successfully satisfy the expected condition.

A spike in conditional failures may indicate:

- Increased concurrency
- Duplicate processing
- Incorrect retry behavior
- Race conditions
- Unexpected application state
- A downstream queue delivering duplicate work

Do not automatically retry conditional failures indefinitely.

---

## Optimistic Locking Failures

### Question

**An optimistic-locking implementation is failing frequently. How would you investigate it?**

**Answer:**

Check:

- Version values being sent by clients
- Concurrent writers
- Retry behavior
- Long-lived stale objects
- Duplicate processing
- Incorrect version increments
- Whether all writers follow the same locking convention

A high conflict rate may indicate that the application's concurrency model does not match the chosen optimistic-locking strategy.

---

## Transaction Failures

### Question

**A DynamoDB transaction is failing. How would you troubleshoot it?**

**Answer:**

Check:

- Conditional expressions
- Item conflicts
- Transaction size
- Duplicate item operations
- Capacity/throttling
- Validation errors
- Application retries
- Idempotency requirements

Do not treat a transaction failure as equivalent to a transient network failure.

Determine whether the transaction was rejected because of a business condition or because of infrastructure/resource pressure.

---

## Duplicate Processing

### Question

**A DynamoDB-backed worker appears to process the same event multiple times. How would you troubleshoot it?**

**Answer:**

Start with the processing model.

Possible causes include:

- At-least-once delivery
- Worker retries
- Lambda retries
- Queue redelivery
- Application timeout after successful processing
- Missing idempotency
- Duplicate event generation

Use an idempotency key and conditional write where appropriate:

```text
Event
 ↓
Idempotency Record
 ↓
attribute_not_exists(PK)
 ↓
Process
 ↓
Mark Complete
```

The key is to make repeated delivery safe rather than assuming every event is delivered exactly once.

---

## DynamoDB Streams Troubleshooting

### Question

**A DynamoDB Streams consumer is not processing events. What would you check?**

**Answer:**

Check:

- Stream enabled on the table
- Stream view type
- Event source configuration
- Consumer permissions
- Lambda execution role
- Iterator age
- Consumer errors
- Failed records
- Retry behavior
- Dead-letter handling
- Region/account configuration

For Lambda-based processing, inspect both DynamoDB/Lambda metrics and application logs.

---

## Stream Processing Lag

### Question

**A DynamoDB Stream consumer has increasing processing lag. What could cause it?**

**Answer:**

Possible causes include:

- Consumer concurrency too low
- Slow downstream API
- Database calls inside the handler
- Excessive per-record processing
- Throttling downstream dependencies
- Poison records
- Insufficient Lambda concurrency
- Large bursts of table activity

The investigation should identify whether the bottleneck is:

```text
DynamoDB Stream
      ↓
Consumer
      ↓
Business Logic
      ↓
Downstream Dependency
```

Increasing consumer concurrency does not help if the downstream dependency is already saturated.

---

## IAM Access Denied

### Question

**Your application receives `AccessDeniedException` when accessing DynamoDB. What would you check?**

**Answer:**

Check:

- IAM identity
- IAM role attached to the workload
- Identity policy
- Resource policy where applicable
- Explicit denies
- Permission boundaries
- AWS Organizations SCPs
- Region
- Table ARN
- Index ARN where relevant
- Session policies

Verify the actual runtime identity rather than assuming the local developer identity is being used.

For example:

```bash
aws sts get-caller-identity
```

This is one of the first commands to run when credentials are unclear.

---

## Wrong AWS Account or Region

### Question

**The application says the DynamoDB table does not exist, but the table is visible in the AWS Console. What would you check?**

**Answer:**

Verify:

```text
AWS Account
AWS Region
AWS Profile
IAM Role
Table Name
Environment Variables
```

Useful command:

```bash
aws sts get-caller-identity
```

Then:

```bash
aws dynamodb list-tables \
  --region ap-south-1
```

A frequent production mistake is debugging the correct table in the wrong AWS account or region.

---

## ResourceNotFoundException

### Question

**What can cause `ResourceNotFoundException` for DynamoDB?**

**Answer:**

Common causes include:

- Incorrect table name
- Incorrect AWS region
- Incorrect AWS account
- Table deleted
- Deployment configuration mismatch
- IAM role accessing a different environment
- Incorrect endpoint configuration

For local development, also verify that a custom DynamoDB endpoint is not accidentally configured.

---

## Boto3 Credentials Work Locally but Fail in Production

### Question

**Why might Boto3 work on a developer machine but fail in ECS or Lambda?**

**Answer:**

Local development may use:

```text
~/.aws/credentials
```

while production uses:

```text
IAM Role
```

If the production role lacks the required permission, the same Python code can fail.

The correct approach is to inspect the runtime identity and permissions rather than copying local credentials into production.

---

## Network Troubleshooting

### Question

**A private workload cannot access DynamoDB. What would you investigate?**

**Answer:**

If the workload runs in a VPC without public internet access, verify the network path to the regional DynamoDB service.

Depending on the architecture, this may involve a DynamoDB VPC endpoint.

Check:

- VPC endpoint configuration
- Route tables
- Endpoint policy
- Security configuration
- DNS behavior
- IAM permissions
- Region
- Application endpoint configuration

The high-level flow is:

```text
Private Subnet
     ↓
DynamoDB VPC Endpoint
     ↓
AWS DynamoDB Service
```

For production workloads, avoid routing AWS service traffic through unnecessary public network paths when an appropriate private connectivity mechanism is available.

---

## Boto3 Connection Problems

### Question

**Your FastAPI application occasionally experiences connection errors when calling DynamoDB. What would you inspect?**

**Answer:**

Investigate:

- Boto3 client/resource lifecycle
- Connection pooling
- Application concurrency
- Socket exhaustion
- Network path
- DNS
- Timeouts
- Retry behavior
- Container resource limits
- Deployment behavior

A common mistake is creating a new Boto3 client or resource for every request.

Prefer reusable clients/resources so the underlying HTTP connections can be reused.

---

## Retry Storm

### Question

**An application experiences throttling, and after adding retries the incident becomes worse. Why?**

**Answer:**

The application created retry amplification:

```text
Original Traffic
      ↓
DynamoDB throttling
      ↓
Retries
      ↓
More traffic
      ↓
More throttling
      ↓
More retries
```

Use:

- Exponential backoff
- Jitter
- Bounded retry attempts
- Appropriate botocore retry configuration
- Application-level rate limiting
- Queue-based buffering where appropriate

Retries should reduce the impact of transient failures, not multiply load during an incident.

---

## Pagination Bug

### Question

**An API returns only the first 1 MB of DynamoDB results. What is likely wrong?**

**Answer:**

The application probably assumes that one `Query` response contains the entire result set.

DynamoDB operations can return a continuation key:

```python
response.get("LastEvaluatedKey")
```

If present, the application must continue from that key when retrieving additional data.

For public APIs, convert the continuation state into a stable cursor rather than exposing raw database implementation details when possible.

---

## Item Size Problems

### Question

**A DynamoDB operation becomes expensive or slow after items grow significantly. What would you investigate?**

**Answer:**

Check:

- Item size
- Number of attributes
- Large strings/blobs
- Nested structures
- Projection
- GSI projections
- Query result volume
- Read/write capacity consumption

Large items increase the amount of data DynamoDB must process and transfer.

Do not store large binary payloads directly in DynamoDB when object storage such as S3 is a better fit.

A common pattern is:

```text
API
 ↓
S3 → Large Object
 ↓
DynamoDB → Metadata / S3 Key
```

---

## Cost Spike

### Question

**DynamoDB cost suddenly increased. How would you investigate it?**

**Answer:**

Break the increase down by:

- Table
- GSI
- Read capacity
- Write capacity
- On-demand request volume
- Storage
- Streams
- Backup/PITR-related usage
- Data transfer where applicable

Then correlate the increase with:

- Deployment
- Traffic growth
- New query patterns
- Scans
- Larger items
- New indexes
- Background jobs
- Retry storms

A particularly important question is:

> Did traffic increase, or did the cost per request increase?

---

## Unexpected Capacity Consumption

### Question

**An API reads only a few items, but DynamoDB capacity consumption is unexpectedly high. What could be wrong?**

**Answer:**

Investigate:

- Item sizes
- Query result size
- Number of evaluated items
- Strong consistency
- Scan usage
- Filter expressions
- Repeated retries
- GSI reads
- Pagination

The number of returned items is not enough to understand DynamoDB workload cost.

You need to understand how much data DynamoDB had to evaluate and read.

---

## GSI Backlog or Propagation Delay

### Question

**A newly written item is visible in the base table but temporarily unavailable through a GSI. How would you investigate it?**

**Answer:**

First determine whether the application is observing normal index propagation behavior or an actual operational problem.

Check:

- Base-table write success
- GSI configuration
- GSI key attributes
- Index status
- Application read consistency expectations
- Time between write and query
- Whether the item qualifies for the index

Do not design business-critical correctness logic around an assumption that an index query immediately represents the state observed through another access path.

---

## Data Type Mismatch

### Question

**A query does not match an item even though the values look identical. What could be wrong?**

**Answer:**

Check DynamoDB data types.

For example:

```text
"123"
```

and:

```text
123
```

are different DynamoDB types.

A string key and numeric key are not interchangeable.

This is especially important when values are generated by different services written in different languages.

---

## Serialization Problems

### Question

**A Python application fails when writing a `Decimal` or floating-point value to DynamoDB. What would you investigate?**

**Answer:**

Boto3's DynamoDB serialization behavior should be considered when working with numeric values.

For financial or exact-value data, prefer `Decimal` rather than relying on binary floating-point arithmetic.

Example:

```python
from decimal import Decimal

item = {
    "PK": "ORDER#123",
    "amount": Decimal("1499.99"),
}
```

Avoid blindly converting financial values through `float`.

---

## Conditional Write Failure vs Throttling

### Question

**How do you distinguish a conditional-write conflict from throttling?**

**Answer:**

Inspect the AWS error code.

For example:

```text
ConditionalCheckFailedException
    ↓
Business/application condition failed

ProvisionedThroughputExceededException
    ↓
Capacity-related throttling

ThrottlingException
    ↓
Request throttling
```

The remediation is different.

| Failure | Typical Response |
|---|---|
| Conditional check failure | Investigate concurrency/business state |
| Throttling | Investigate capacity/distribution/load |
| Access denied | Investigate IAM |
| Resource not found | Investigate account/region/resource |
| Validation error | Investigate request/schema |
| Network timeout | Investigate client/network/dependency |

---

## Production Incident Scenario

### Question

**A checkout service using DynamoDB starts returning 500 errors during a traffic spike. How would you troubleshoot it?**

**Answer:**

Start with the request path:

```text
Client
  ↓
API Gateway / Load Balancer
  ↓
Application
  ↓
DynamoDB
```

Then correlate:

```text
Traffic
API latency
Application errors
DynamoDB latency
DynamoDB throttling
SDK retries
GSI metrics
Partition distribution
```

A possible diagnosis could be:

```text
Traffic spike
    ↓
Many requests for same product
    ↓
Hot partition
    ↓
Inventory writes throttled
    ↓
Boto3 retries
    ↓
Application latency increases
    ↓
API requests timeout
```

The correct mitigation could include:

- Reduce retry amplification
- Protect the API with rate limiting
- Improve key distribution
- Reduce contention
- Queue non-critical work
- Use caching for appropriate read paths
- Scale capacity where appropriate

The long-term fix should address the architectural bottleneck rather than relying solely on temporary capacity increases.

---

## Production Incident Scenario: Latency Without Throttling

### Question

**DynamoDB latency is high but throttling metrics are normal. What would you investigate?**

**Answer:**

Do not assume DynamoDB capacity is the problem.

Investigate:

```text
API latency
    ↓
Application processing
    ↓
Boto3 request latency
    ↓
DynamoDB service latency
```

Potential causes include:

- Large response payloads
- Large items
- Excessive serialization
- Slow network path
- Connection establishment
- Connection pool exhaustion
- Application CPU pressure
- Garbage collection
- Downstream processing after the DynamoDB call
- SDK retries caused by other transient failures

Distributed tracing is valuable when the application has multiple service dependencies.

---

## Production Incident Scenario: One Customer Causes Throttling

### Question

**A multi-tenant application experiences throttling whenever one large customer becomes active. What would you investigate?**

**Answer:**

Check whether tenant ID is the partition key:

```text
PK = TENANT#123
```

If a single tenant generates a disproportionate workload, that tenant may become a hot logical partition.

Potential strategies include:

- Tenant-aware sharding
- Composite partition keys
- Workload isolation
- Separate tables for extreme tenants
- Rate limiting
- Asynchronous processing
- Caching

The correct solution depends on tenant traffic characteristics and access patterns.

---

## Troubleshooting Checklist

| Symptom | First Areas to Check |
|---|---|
| High read latency | Query size, throttling, hot keys, SDK retries |
| High write latency | Hot keys, GSI writes, throttling |
| Read throttling | Capacity, hot partitions, strong reads |
| Write throttling | Capacity, key distribution, GSIs |
| Empty query result | Keys, index, region, data types |
| Missing GSI item | Index keys, sparse-index behavior |
| Access denied | IAM role, policies, SCPs |
| Resource not found | Account, region, table name |
| Duplicate processing | Retries, event delivery, idempotency |
| Conditional failures | Concurrency, state transitions |
| Stream lag | Consumer capacity, downstream dependencies |
| Cost spike | Scans, retries, traffic, item size, indexes |
| Connection errors | Client reuse, pooling, networking |
| API timeout | DynamoDB latency, retries, application processing |
| Unexpected capacity | Item size, scans, filters, consistency |

---

## Useful AWS CLI Commands

### Identify Current AWS Identity

```bash
aws sts get-caller-identity
```

### List DynamoDB Tables

```bash
aws dynamodb list-tables \
  --region ap-south-1
```

### Describe a Table

```bash
aws dynamodb describe-table \
  --table-name Orders \
  --region ap-south-1
```

### Check Table Configuration

```bash
aws dynamodb describe-table \
  --table-name Orders \
  --query 'Table.{Status:TableStatus,Keys:KeySchema,Indexes:GlobalSecondaryIndexes}' \
  --region ap-south-1
```

### Scan a Small Dataset During Troubleshooting

```bash
aws dynamodb scan \
  --table-name Orders \
  --max-items 10 \
  --region ap-south-1
```

Avoid using unrestricted scans against large production tables merely for debugging.

### Query a Partition Key

```bash
aws dynamodb query \
  --table-name Orders \
  --key-condition-expression 'PK = :pk' \
  --expression-attribute-values '{":pk":{"S":"CUSTOMER#123"}}' \
  --region ap-south-1
```

---

## Common Troubleshooting Mistakes

| Mistake | Why It Fails | Better Approach |
|---|---|---|
| Immediately increasing capacity | May not fix hot partitions | Diagnose distribution first |
| Adding retries everywhere | Can amplify load | Use bounded backoff |
| Replacing `Query` with `Scan` | Hides data-model problems | Design the access pattern |
| Assuming returned items equal work | Reads may evaluate many items | Inspect evaluated data |
| Ignoring GSIs | Index can be the bottleneck | Monitor table and indexes separately |
| Blaming DynamoDB for API latency | Application may be slow | Trace the entire request |
| Ignoring item size | Large items increase workload | Inspect item and response size |
| Treating conditional failures as outages | They may be expected concurrency behavior | Classify errors |
| Debugging IAM without checking identity | Wrong role may be in use | Run `aws sts get-caller-identity` |
| Assuming TTL is immediate | TTL deletion is asynchronous | Never use TTL as an exact scheduler |
| Ignoring retries during incidents | Retry storms worsen failures | Inspect SDK retry behavior |
| Testing with production-wide scans | Can create unnecessary load | Query targeted keys or use controlled tooling |

---

## Interview Troubleshooting Framework

When answering a DynamoDB troubleshooting question in an interview, structure the response around five areas:

### Establish the Symptom

Clarify:

- What is failing?
- Which API?
- Which table or index?
- Since when?
- Is the failure intermittent or constant?
- Did traffic or code change?

### Check Observability

Look at:

- CloudWatch
- Application logs
- Distributed traces
- DynamoDB metrics
- SDK retry information
- Error codes

### Identify the Layer

Determine whether the issue is:

```text
Application
   ↓
SDK
   ↓
Network
   ↓
IAM
   ↓
DynamoDB
   ↓
Table / Index
   ↓
Partition Distribution
```

### Mitigate Safely

Depending on the cause:

- Reduce traffic
- Stop runaway workers
- Adjust capacity
- Reduce retries
- Enable or tune throttling protection
- Roll back a problematic deployment
- Fail gracefully
- Queue non-critical work

### Fix the Root Cause

Examples:

```text
Hot partition
    → Improve key distribution

Scan-heavy API
    → Redesign access pattern

Repeated reads
    → Add caching where appropriate

Retry storm
    → Add bounded exponential backoff

Duplicate processing
    → Add idempotency

Large items
    → Move large payloads to object storage
```

---

## Interview Traps

### Trap: "The table has enough capacity, so it cannot throttle."

False.

Capacity distribution and partition-level workload concentration matter.

### Trap: "Adding a FilterExpression makes a query efficient."

False.

Filtering happens after DynamoDB evaluates the matching key range.

### Trap: "Retries always improve reliability."

False.

Unbounded or aggressive retries can create retry storms.

### Trap: "If the item exists in the table, it must exist in the GSI."

False.

GSIs can be sparse when index key attributes are missing.

### Trap: "A conditional check failure means DynamoDB is broken."

False.

Conditional failures are often expected application-level concurrency behavior.

### Trap: "DynamoDB latency equals API latency."

False.

Application processing, networking, serialization, retries, and downstream dependencies can all contribute to end-to-end latency.

---

## Key Takeaways

- Troubleshoot DynamoDB systematically across application, SDK, IAM, networking, table/index, capacity, and partition-distribution layers instead of immediately increasing capacity.
- Hot partitions, inefficient access patterns, scans, large items, and GSI behavior can create production problems even when aggregate table capacity appears healthy.
- Always distinguish throttling, conditional conflicts, authorization failures, resource errors, validation errors, and network failures because each requires a different remediation strategy.
- CloudWatch metrics, application logs, tracing, structured partition-key telemetry, and SDK retry information should be correlated to identify the real bottleneck.
- Strong DynamoDB troubleshooting focuses on both immediate mitigation and the underlying data-model or workload-design problem that caused the incident.