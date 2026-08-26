# 12- Common Interview Traps

## Overview

DynamoDB interview traps usually test whether an engineer understands the difference between **what the service can do** and **what the service is designed to do efficiently**.

Many incorrect answers are technically plausible but ignore access patterns, partition distribution, consistency, capacity, index behavior, or operational trade-offs. Senior-level interviews typically focus on whether you can identify these constraints and make a defensible architecture decision.

---

## Access Pattern and Data Modeling Traps

### Trap: Treating DynamoDB Like a Relational Database

A common mistake is designing DynamoDB tables around entities first and queries later:

```text
Users
Orders
Products
Payments
```

and then expecting arbitrary joins and filters.

DynamoDB should generally be designed around **known access patterns**.

For example:

```text
Get all orders for a customer
Get a specific order
Get orders by status
Get recent orders for a customer
```

These requirements should drive the primary key and index design.

### Strong Interview Answer

> "I would identify the application's access patterns first, then design the partition key, sort key, and secondary indexes to support those patterns efficiently."

---

## Trap: Assuming DynamoDB Requires One Table Per Entity

DynamoDB supports both single-table and multi-table designs.

Single-table design can colocate related entities:

```text
PK              SK
CUSTOMER#123    PROFILE
CUSTOMER#123    ORDER#001
CUSTOMER#123    ORDER#002
```

The important question is not:

> "Should DynamoDB always use one table?"

It is:

> "Which table design provides efficient access patterns with acceptable complexity?"

Single-table design is powerful but should not become an architectural rule applied without considering the team's requirements and operational model.

---

## Trap: Designing the Partition Key From the Entity Name

A partition key such as:

```text
PK = ORDER
```

can create a severe hotspot if most writes target the same partition-key value.

A better design might distribute traffic using:

```text
PK = CUSTOMER#123
```

or another key with sufficient cardinality and appropriate access semantics.

The partition key must satisfy two requirements:

1. Support the required access pattern.
2. Distribute workload sufficiently across partitions.

---

## Trap: Thinking High Cardinality Alone Guarantees Good Distribution

A partition key with many possible values is not automatically well distributed.

Consider:

```text
PK = USER_ID
```

If one user receives 80% of all traffic, the workload can still be heavily concentrated.

Evaluate both:

- Cardinality
- Traffic distribution

A senior engineer considers **access frequency per key**, not just the number of unique keys.

---

## Trap: Using a Timestamp as the Partition Key

A timestamp can create poor distribution if many writes use the same time bucket.

For example:

```text
PK = 2026-08-26
```

can concentrate all writes for that day under one partition-key value.

Timestamps are often better suited to sort-key attributes when combined with an appropriate partition key.

---

## Query and Scan Traps

### Trap: Saying `Scan` Is Fine Because the Table Is Currently Small

A scan may appear harmless during development:

```python
table.scan()
```

but its cost and latency scale with the amount of data evaluated.

Production applications should generally use:

```text
GetItem
Query
BatchGetItem
```

where appropriate.

A scan can still be useful for controlled administrative workloads, migrations, or specialized background processing, but it should be deliberate.

---

## Trap: Thinking FilterExpression Makes Scan Efficient

This is one of the most common DynamoDB interview traps.

Consider:

```python
table.scan(
    FilterExpression=Attr("status").eq("ACTIVE")
)
```

The filter does not make DynamoDB scan only active items.

DynamoDB evaluates the underlying items and applies the filter to determine what is returned.

Therefore:

```text
Table
 ↓
Read/evaluate items
 ↓
FilterExpression
 ↓
Returned items
```

The filter is not equivalent to an indexed query.

---

## Trap: Confusing KeyConditionExpression and FilterExpression

`KeyConditionExpression` determines which items are selected by the query's key structure.

`FilterExpression` removes items after they have been evaluated.

| Expression | Purpose |
|---|---|
| `KeyConditionExpression` | Selects items using key attributes |
| `FilterExpression` | Filters evaluated results |
| `ProjectionExpression` | Controls returned attributes |

The distinction matters for both performance and cost.

---

## Trap: Assuming Query Always Returns the Entire Result

DynamoDB responses can be paginated.

A query may return:

```json
{
  "Items": [],
  "LastEvaluatedKey": {}
}
```

When `LastEvaluatedKey` is present, the client may need to continue querying.

Production applications should not assume a single request retrieves an unlimited result set.

---

## Consistency Traps

### Trap: Assuming DynamoDB Reads Are Always Strongly Consistent

DynamoDB reads are eventually consistent by default for supported read operations.

Strong consistency must be explicitly requested where supported:

```python
table.get_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    ConsistentRead=True,
)
```

Do not enable strong reads everywhere without identifying the business requirement.

---

## Trap: Assuming Strong Consistency Is Available Everywhere

Strongly consistent reads are not supported for GSIs.

This distinction is particularly important:

| Resource | Strongly consistent read |
|---|---|
| Base table | Supported |
| LSI | Supported |
| GSI | Not supported |

If an access pattern requires strong consistency, this constraint must be considered during index design.

---

## Trap: Confusing Strong Consistency With Transactions

These solve different problems.

### Strong Read

Answers:

> "Give me the latest available value according to strong-read semantics."

### Transaction

Answers:

> "Perform these related operations atomically."

For example:

```text
Strong Read
→ Read current state

Transaction
→ Update Order
→ Update Inventory
→ Create Payment Record
→ Commit atomically
```

A strongly consistent read does not provide multi-item transactional guarantees.

---

## Index Traps

### Trap: Assuming GSIs Are Free

A GSI introduces additional:

- Storage
- Write work
- Read capacity/cost
- Operational complexity

Do not create indexes simply because an attribute might be queried someday.

Design indexes around actual access patterns.

---

## Trap: Assuming GSI and LSI Are Interchangeable

They differ in important ways.

| Characteristic | LSI | GSI |
|---|---|---|
| Partition key | Same as base table | Can differ |
| Sort key | Can differ | Can differ |
| Creation | At table creation | Can be added later |
| Strong reads | Supported | Not supported |
| Capacity | Uses base table capacity | Independently configured |
| Scope | Same partition-key value | Independent |

A common interview mistake is remembering only that both are secondary indexes and overlooking these constraints.

---

## Trap: Assuming an LSI Can Change the Partition Key

It cannot.

An LSI uses the same partition key as the base table.

For example:

```text
Base Table
PK = CUSTOMER_ID
SK = ORDER_ID
```

An LSI can provide:

```text
PK = CUSTOMER_ID
LSI SK = CREATED_AT
```

but cannot provide:

```text
PK = ORDER_STATUS
```

That type of access pattern generally requires a GSI or another modeling strategy.

---

## Trap: Assuming a GSI Is Immediately Consistent With the Base Table

GSI updates are propagated asynchronously.

Therefore, applications should account for eventual consistency when reading from GSIs.

Do not design a critical workflow around an assumption that a newly written item will immediately appear in a GSI.

---

## Trap: Assuming `ProjectionExpression` Reduces Read Capacity Consumption

`ProjectionExpression` controls which attributes are returned to the application.

It does not mean DynamoDB only evaluates the projected attributes for capacity purposes.

Do not confuse:

```text
Network payload reduction
```

with:

```text
Underlying read capacity reduction
```

---

## Capacity Traps

### Trap: Assuming On-Demand Is Always Cheaper

On-demand capacity simplifies capacity management and is useful for unpredictable workloads.

It is not universally cheaper.

For stable, predictable workloads, provisioned capacity may provide better economics.

Evaluate:

- Request volume
- Traffic predictability
- Peak-to-average ratio
- Growth
- Scaling behavior
- Cost requirements

---

## Trap: Assuming Provisioned Capacity Means No Automatic Scaling

Provisioned capacity can be combined with Application Auto Scaling.

A production architecture may use:

```text
Predictable baseline
        ↓
Provisioned capacity
        ↓
Application Auto Scaling
        ↓
Capacity adjustment
```

The capacity mode and autoscaling strategy are separate concepts.

---

## Trap: Confusing RCUs and WCUs

Read and write capacity are different resources.

Do not assume:

```text
1 read = 1 RCU
```

or:

```text
1 write = 1 WCU
```

without considering item size and read consistency.

Capacity calculations must account for:

- Item size
- Read type
- Write size
- Number of operations
- Requested throughput

---

## Trap: Ignoring Item Size

DynamoDB capacity consumption is affected by item size.

An engineer who calculates capacity solely from request count can significantly underestimate resource requirements.

For example:

```text
10,000 small writes/sec
```

and:

```text
10,000 large writes/sec
```

do not necessarily have the same capacity requirements.

---

## Hot Partition Traps

### Trap: Assuming DynamoDB Automatically Eliminates Hotspots

DynamoDB distributes data across partitions, but poor key design can still create concentrated traffic.

A classic example is:

```text
PK = PRODUCT#POPULAR
```

if one extremely popular product receives most requests.

Possible mitigation strategies include:

- Better partition-key distribution
- Write sharding
- Application-level aggregation
- Caching with Redis
- Different access-pattern modeling

---

## Trap: Solving Every Hot Partition With More Capacity

Adding capacity does not necessarily solve a concentrated partition-key workload.

If traffic is concentrated on a single partition key, the fundamental problem may be **distribution**, not total table capacity.

This is a key senior-level distinction:

```text
Low total capacity
        ≠
Hot partition
```

---

## Write Sharding Traps

Write sharding can distribute high-volume writes:

```text
PRODUCT#123#0
PRODUCT#123#1
PRODUCT#123#2
PRODUCT#123#3
```

However, it introduces additional read complexity because the application may need to query multiple shards and merge results.

Do not introduce write sharding unless the workload actually requires it.

---

## Transaction Traps

### Trap: Assuming DynamoDB Transactions Are Free

Transactions introduce additional processing and cost.

Use transactions when atomicity is a business requirement.

Do not replace every conditional write with a transaction.

For example, a single-item invariant may only require:

```text
UpdateItem
+
ConditionExpression
```

rather than a multi-item transaction.

---

## Trap: Assuming Transactions Remove All Race Conditions

Transactions provide atomicity for participating operations, but application-level concurrency and workflow design still matter.

You must still consider:

- Idempotency
- Retry behavior
- Conditional expressions
- Transaction conflicts
- External side effects

A database transaction cannot roll back an already-sent external HTTP request or Kafka event.

---

## Batch Operation Traps

### Trap: Assuming `BatchWriteItem` Is Transactional

It is not.

Batch operations are intended for efficient bulk processing, not all-or-nothing business transactions.

Use transactional APIs when atomicity is required.

---

## Trap: Ignoring Unprocessed Items

Batch operations can return unprocessed items.

Production code should handle them appropriately rather than assuming the entire batch succeeded.

Conceptually:

```text
Batch Request
     ↓
DynamoDB
     ↓
Processed + Unprocessed
                ↓
             Retry
```

Retries should use appropriate backoff rather than immediately hammering the service.

---

## TTL Traps

### Trap: Assuming TTL Deletes Items Exactly at the Expiration Timestamp

TTL deletion is asynchronous.

If:

```text
expires_at = 12:00:00
```

you should not assume the item disappears exactly at 12:00:00.

TTL is appropriate for automatic cleanup, not precise-time business workflows.

---

## Trap: Using TTL as a Scheduler

This is incorrect:

```text
TTL expires at 10:00
        ↓
Payment must happen at 10:00
```

TTL should not be treated as an exact event scheduler.

For time-sensitive workflows, use an appropriate scheduling/event architecture.

---

## Streams Traps

### Trap: Assuming DynamoDB Streams Are the Same as Kafka

DynamoDB Streams capture item-level changes from DynamoDB.

Kafka is a general-purpose distributed event-streaming platform.

Use Streams when:

```text
DynamoDB Change
      ↓
Consumer
```

is the core requirement.

Use Kafka when you need a broader event-streaming architecture involving independent producers, consumers, retention, replay, and event-processing requirements.

---

## Trap: Assuming Streams Make External Side Effects Exactly Once

Consider:

```text
DynamoDB
   ↓
Stream
   ↓
Lambda
   ↓
External API
```

The external API call can fail or be retried.

Consumers should therefore be designed for idempotency.

A senior engineer should explicitly mention:

- Retries
- Duplicate processing
- Idempotency keys
- Dead-letter handling
- Observability

---

## Global Tables Traps

### Trap: Assuming Global Tables Automatically Solve Disaster Recovery

Global Tables can provide multi-region replication, but they do not eliminate application-level failure scenarios.

You still need to consider:

- Regional failures
- Conflict behavior
- Failover strategy
- Application routing
- Data residency
- Operational monitoring
- Recovery procedures

Multi-region architecture is more than simply enabling replication.

---

## Trap: Assuming Global Tables Mean Writes Are Always Conflict-Free

Multi-region writes can create conflicts when multiple regions update the same logical item.

Applications should define clear ownership and conflict-handling strategies.

A useful design principle is:

```text
Prefer independent regional writes
when business semantics allow it.
```

---

## Single-Table Design Traps

### Trap: Thinking Single-Table Design Means One Item Type

A single DynamoDB table can contain multiple entity types:

```text
CUSTOMER#123 / PROFILE
CUSTOMER#123 / ORDER#001
CUSTOMER#123 / ORDER#002
```

The purpose is to optimize related access patterns, not to restrict the table to one entity type.

---

## Trap: Overusing Single-Table Design

Single-table design can become difficult to maintain if:

- Access patterns are poorly documented.
- Key semantics are unclear.
- The team lacks DynamoDB experience.
- Too many unrelated entities are colocated.
- Indexes become difficult to reason about.

The design should optimize important access patterns without creating unnecessary cognitive complexity.

---

## Cache Traps

### Trap: Assuming Redis Automatically Fixes DynamoDB Performance

If an application performs inefficient scans, adding Redis may hide the problem temporarily without fixing the underlying data model.

A better sequence is:

```text
1. Verify access pattern
2. Verify key design
3. Check Query efficiency
4. Check partition distribution
5. Check capacity/throttling
6. Add caching if justified
```

Caching is an optimization, not a substitute for correct database modeling.

---

## Conditional Expression Traps

### Trap: Assuming Application-Level Checks Are Equivalent to Conditional Writes

This pattern is unsafe:

```text
Application:
    Read balance = 100

Application:
    balance >= 50

Application:
    Write balance = 50
```

Another request can modify the item between the read and write.

A conditional update can enforce the invariant closer to the write:

```text
Update balance
IF balance >= 50
```

This reduces race conditions for single-item state transitions.

---

## Idempotency Traps

### Trap: Assuming Retries Are Always Safe

A retry can duplicate a business operation.

For example:

```text
Request
  ↓
Create Payment
  ↓
Timeout
  ↓
Client retries
  ↓
Create Payment again
```

DynamoDB can help implement idempotency using a unique request key:

```text
PK = IDEMPOTENCY#request-123
```

The application can use conditional writes to ensure the request is processed only once according to its business semantics.

---

## Error Handling Traps

### Trap: Treating Every DynamoDB Exception as a Generic Failure

Different errors imply different responses.

Examples include:

- Throttling
- Conditional check failure
- Validation errors
- Resource-not-found conditions
- Transaction conflicts
- Access denied
- Network/client failures

A production application should classify errors rather than retrying everything.

---

## Retry Traps

### Trap: Retrying Every Failure Immediately

This can amplify an existing capacity or dependency problem.

Prefer controlled retries with exponential backoff and jitter where retrying is appropriate.

```text
Request
  ↓
Failure
  ↓
Backoff
  ↓
Retry
  ↓
Backoff
  ↓
Retry
```

Do not retry deterministic validation failures.

---

## Security Traps

### Trap: Assuming DynamoDB Encryption Means the Application Needs No Security Controls

Encryption at rest does not replace:

- IAM authorization
- Least-privilege policies
- Network controls where applicable
- Application authorization
- Audit logging
- Secrets management

A production security model must protect both the data and the operations that access it.

---

## IAM Traps

### Trap: Giving an Application Full DynamoDB Permissions

Avoid broad policies such as unrestricted:

```text
dynamodb:*
```

for application roles.

Prefer permissions scoped to:

- Required tables
- Required indexes
- Required operations

For example:

```text
GetItem
PutItem
UpdateItem
Query
```

only where required.

---

## Monitoring Traps

### Trap: Monitoring Only Consumed Capacity

Capacity metrics alone are insufficient.

Production monitoring should consider:

- Throttled requests
- Consumed read/write capacity
- Latency
- Error rates
- Conditional check failures
- Transaction conflicts
- Hot partitions
- Stream processing failures
- Application-level SLOs

The database should be monitored as part of the complete request path.

---

## Cost Traps

### Trap: Assuming DynamoDB Cost Is Determined Only by Table Size

Production cost can also be affected by:

- Read/write traffic
- Item size
- Secondary indexes
- Global Tables
- Streams
- Backups
- Point-in-time recovery
- On-demand versus provisioned capacity
- Replication
- Additional application infrastructure

A senior engineer should evaluate the entire architecture rather than only storage cost.

---

## Architecture Interview Trap

### Trap: Answering "How Would You Design This DynamoDB Table?" Before Asking About Access Patterns

A strong answer begins with questions such as:

- What operations must the system support?
- What are the read/write ratios?
- What is the expected traffic?
- Which queries require low latency?
- Which data must be strongly consistent?
- What are the largest items?
- Are there hot entities?
- Is multi-region access required?
- What are the retention requirements?
- Which operations must be atomic?

Only then should the key schema be proposed.

---

## Senior-Level Interview Trap

### Trap: Giving a Technically Correct Answer Without Discussing Trade-offs

For example:

> "Use a GSI to query by status."

This may be correct but incomplete.

A stronger answer is:

> "A GSI can support querying by status, but I would first verify the cardinality and traffic distribution of the status values. If most requests target one status, that GSI partition key could become a hotspot. I would also account for the additional storage and write cost of maintaining the index."

That demonstrates engineering judgment rather than memorization.

---

## Rapid-Fire Trap Reference

| Interview Trap | Correct Mental Model |
|---|---|
| DynamoDB is a SQL replacement | It is an access-pattern-oriented NoSQL database |
| Scan + filter is efficient | Filtering happens after evaluation |
| More capacity fixes every problem | Hot keys require distribution |
| High cardinality guarantees distribution | Traffic distribution also matters |
| GSI = independent table | It is a secondary index with projected attributes |
| GSI supports strong reads | GSI reads are eventually consistent |
| LSI can use any partition key | LSI retains the base table partition key |
| Transactions solve everything | Use them only when atomicity is required |
| BatchWrite is transactional | Batch operations are not all-or-nothing transactions |
| TTL is a scheduler | TTL cleanup is asynchronous |
| Streams = Kafka | Streams are DynamoDB change capture |
| Redis fixes bad data modeling | Fix access patterns first |
| Global Tables = automatic DR | Multi-region operation requires application planning |
| Retries are always safe | Retries require idempotency analysis |
| Encryption solves DynamoDB security | IAM and authorization remain essential |
| Capacity metrics are enough | Monitor latency, throttling, errors, and workload behavior |
| Single-table is mandatory | Choose single- or multi-table based on access patterns |
| On-demand is always cheaper | Cost depends on workload shape |
| Strong consistency is always better | Consistency is a business requirement |
| More indexes are always better | Indexes introduce storage, write, and operational cost |

---

## How to Answer DynamoDB Trap Questions

When a question appears to have an obvious answer, pause and evaluate it against these dimensions:

```text
Access Pattern
      ↓
Partition Distribution
      ↓
Consistency
      ↓
Scalability
      ↓
Latency
      ↓
Cost
      ↓
Reliability
      ↓
Operational Complexity
      ↓
Security
```

A senior backend engineer should be able to explain not only **what DynamoDB feature to use**, but also **why that feature is appropriate, what assumptions it depends on, and what failure mode it introduces**.

---

## Key Takeaways

- DynamoDB interview traps usually expose misunderstandings around access-pattern-driven design, partition distribution, consistency, capacity, and indexes.
- A technically valid feature choice is incomplete without explaining its scalability, cost, consistency, and operational trade-offs.
- Hot partitions, inefficient scans, unnecessary indexes, unsafe retries, and incorrect consistency assumptions are common production failure modes.
- Strong DynamoDB answers start from business access patterns and invariants rather than jumping directly to a table or index design.
- Senior-level answers explicitly identify assumptions, limitations, failure modes, and the conditions under which an alternative design would be preferable.