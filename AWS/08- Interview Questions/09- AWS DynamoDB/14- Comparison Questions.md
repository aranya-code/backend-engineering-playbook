# 11- Comparison Questions

## Overview

DynamoDB comparison questions test whether an engineer understands the trade-offs behind DynamoDB's data model, consistency model, capacity modes, indexing strategies, access patterns, and operational behavior.

The strongest interview answers do not simply state which option is "better." They explain **when each option is appropriate, what trade-off it introduces, and how the decision affects scalability, latency, reliability, and cost**.

---

## Query vs Scan

### Question

**What is the difference between `Query` and `Scan` in DynamoDB?**

| Aspect | Query | Scan |
|---|---|---|
| Access pattern | Key-based | Entire table/index |
| Partition key | Required | Not required |
| Efficiency | Generally efficient | Potentially expensive |
| Data evaluated | Matching key range | Table/index data |
| Production API usage | Preferred | Usually avoided |
| Pagination | Required for large results | Required |
| Typical use | Application access patterns | Admin jobs, migrations, controlled analysis |

`Query` should normally be the default for application reads.

```python
from boto3.dynamodb.conditions import Key

response = table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#123")
)
```

A scan should be deliberate:

```python
response = table.scan(
    Limit=100
)
```

### Interview Trap

A `FilterExpression` does not make a scan efficient. DynamoDB still evaluates the underlying data before filtering the returned results.

---

## GetItem vs Query

### Question

**When would you use `GetItem` instead of `Query`?**

| Aspect | GetItem | Query |
|---|---|---|
| Purpose | Retrieve one item by full primary key | Retrieve one or more items |
| Key required | Complete primary key | Partition key required |
| Result | At most one item | Multiple items |
| Typical latency | Very low | Depends on result size |
| Use case | Direct lookup | Collection/range retrieval |

Example:

```python
response = table.get_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    }
)
```

Use `GetItem` when the application knows the complete primary key.

Use `Query` when it needs a collection of related items.

---

## Query vs BatchGetItem

### Question

**What is the difference between `Query` and `BatchGetItem`?**

| Aspect | Query | BatchGetItem |
|---|---|---|
| Selection | Key condition | Explicit keys |
| Result | Key range | Specific items |
| Number of keys | Not explicitly enumerated | Up to 100 items per operation |
| Access pattern | Collection retrieval | Multiple direct lookups |
| Ordering | Query ordering semantics | No guaranteed order |
| Typical use | Customer's orders | Retrieve known orders |

Use `BatchGetItem` when the application already knows the keys it needs.

---

## PutItem vs UpdateItem

### Question

**What is the difference between `PutItem` and `UpdateItem`?**

| Aspect | PutItem | UpdateItem |
|---|---|---|
| Operation | Creates/replaces item | Modifies selected attributes |
| Existing item | Can replace it | Updates it |
| Partial update | No | Yes |
| Expressions | Conditions supported | Update expressions supported |
| Typical use | Full item write | Attribute-level changes |

Example:

```python
table.put_item(
    Item={
        "PK": "ORDER#123",
        "SK": "DETAILS",
        "status": "PENDING",
    }
)
```

Versus:

```python
table.update_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    UpdateExpression="SET #status = :status",
    ExpressionAttributeNames={
        "#status": "status",
    },
    ExpressionAttributeValues={
        ":status": "CONFIRMED",
    },
)
```

A common production mistake is using `PutItem` for a partial modification and unintentionally replacing attributes that were not included in the request.

---

## DeleteItem vs UpdateItem

### Question

**When would you use `DeleteItem` instead of setting a status such as `DELETED`?**

Use `DeleteItem` when the item no longer needs to exist as part of the application's active data model.

Use a soft-delete attribute when the application needs:

- Auditability
- Recovery
- Historical state
- Regulatory retention
- Logical deletion

For example:

```text
Hard Delete

Item
 ↓
DeleteItem
 ↓
Removed
```

versus:

```text
Soft Delete

Item
 ↓
status = DELETED
 ↓
Still stored
```

Soft deletion increases storage and requires every relevant access pattern to account for deleted records.

---

## Strongly Consistent vs Eventually Consistent Reads

### Question

**What is the difference between strongly consistent and eventually consistent reads?**

| Aspect | Eventually Consistent | Strongly Consistent |
|---|---|---|
| Visibility | May temporarily return older data | Reflects successful writes according to strong-read semantics |
| Default | Yes for supported reads | Must be requested |
| Cost | Lower read capacity requirement | Higher read capacity requirement |
| Latency/availability trade-off | Generally more flexible | Stronger read guarantee |
| Use case | Most read-heavy workloads | Critical read-after-write requirements |

Example:

```python
response = table.get_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    ConsistentRead=True,
)
```

Do not enable strong consistency globally without identifying which access patterns actually require it.

---

## LSI vs GSI

### Question

**What is the difference between a Local Secondary Index and a Global Secondary Index?**

| Aspect | LSI | GSI |
|---|---|---|
| Partition key | Same as base table | Can be different |
| Sort key | Different | Can be different |
| Creation | Must be defined when table is created | Can be added/removed separately |
| Scope | Same partition-key value as base table | Independent key distribution |
| Capacity | Shares table capacity | Has its own capacity configuration |
| Use case | Alternative sorting within same partition | Different access pattern |

Example:

```text
Base Table

PK = CUSTOMER#123
SK = ORDER#001
```

An LSI can use:

```text
PK = CUSTOMER#123
LSI SK = CREATED_AT
```

A GSI can instead support a completely different access pattern:

```text
GSI PK = STATUS
GSI SK = CREATED_AT
```

---

## LSI vs GSI: Design Decision

### Question

**When should you choose an LSI over a GSI?**

Use an LSI when:

- The access pattern uses the same partition key as the base table.
- You need an alternative sort key.
- The index must be part of the initial table design.
- The LSI's constraints fit the workload.

Use a GSI when:

- The query needs a different partition key.
- The workload requires independent capacity configuration.
- The access pattern may evolve independently from the base table.
- The index can be created after the table exists.

For most new access patterns requiring a different partition key, a GSI is the more flexible choice.

---

## GSI vs Separate Table

### Question

**When would you use a GSI instead of maintaining a separate table?**

A GSI is appropriate when the alternate access pattern can be represented naturally as an index and the consistency, projection, capacity, and operational characteristics are acceptable.

A separate table may be appropriate when:

- The alternate model is substantially different.
- The data lifecycle differs.
- Independent operational scaling is required.
- The access pattern requires a specialized materialized view.
- Stronger isolation is desirable.

Example:

```text
Base Table
    ↓
GSI
    ↓
Alternate access pattern
```

versus:

```text
Base Table
    ↓
Application / Stream Processor
    ↓
Materialized Table
```

The second architecture provides greater modeling freedom but introduces synchronization complexity.

---

## Table vs GSI

### Question

**Does a GSI store a completely independent copy of the table?**

No.

A GSI contains indexed attributes and projected attributes rather than necessarily duplicating every attribute from the base table.

The projection can include:

- `KEYS_ONLY`
- `INCLUDE`
- `ALL`

The projection decision affects storage and index usefulness.

---

## GSI vs LSI Consistency

### Question

**Can you use strongly consistent reads against both GSIs and LSIs?**

No.

LSIs support strongly consistent reads.

GSIs do not support strongly consistent reads because they are maintained separately from the base table.

This is an important interview distinction.

---

## Provisioned vs On-Demand Capacity

### Question

**What is the difference between provisioned and on-demand capacity mode?**

| Aspect | Provisioned | On-Demand |
|---|---|---|
| Capacity model | Explicit capacity | Automatically handles capacity based on traffic |
| Predictable workload | Strong fit | Also possible |
| Traffic variability | Requires planning/autoscaling | Better suited to variable workloads |
| Capacity planning | Required | Reduced |
| Cost model | Capacity-based | Request-based |
| Operational complexity | Higher | Lower |

Provisioned mode is often attractive for stable, predictable workloads.

On-demand mode is useful for workloads where traffic is difficult to predict or changes significantly.

The correct decision should be based on workload characteristics and cost analysis rather than assuming one mode is universally better.

---

## Provisioned Capacity vs Auto Scaling

### Question

**Does provisioned capacity mean capacity cannot scale automatically?**

No.

Provisioned capacity can be combined with Application Auto Scaling.

Conceptually:

```text
Application Traffic
        ↓
Consumed Capacity
        ↓
Auto Scaling
        ↓
Provisioned Capacity
```

This is useful for workloads with predictable baseline traffic and controlled variation.

---

## On-Demand vs Provisioned: Interview Scenario

### Question

**Which capacity mode would you choose for an application with highly unpredictable traffic?**

A reasonable starting point is on-demand capacity because it reduces the need to pre-plan capacity.

However, the decision should consider:

- Traffic shape
- Sustained workload
- Cost
- Growth
- Predictability
- Operational requirements
- Existing autoscaling strategy

A senior answer should avoid saying "on-demand is always better for unpredictable traffic" without considering cost and workload characteristics.

---

## DynamoDB vs PostgreSQL

### Question

**When would you choose DynamoDB over PostgreSQL?**

| Requirement | DynamoDB | PostgreSQL |
|---|---|---|
| Known access patterns | Excellent | Excellent |
| Flexible ad-hoc queries | Limited | Strong |
| Relational joins | No | Strong |
| Horizontal scale | Excellent | Possible with additional architecture |
| Transactions | Supported with DynamoDB semantics | Strong relational transactions |
| Schema flexibility | High | Structured |
| Operational model | Managed NoSQL | Managed/relational |
| Complex analytics | Usually external tooling | Stronger SQL ecosystem |
| Massive key-value workloads | Strong fit | May require additional architecture |

DynamoDB is attractive when the application can model its data around known access patterns and needs predictable, highly scalable key-value/document access.

PostgreSQL is often a better fit when the domain depends heavily on:

- Joins
- Complex filtering
- Ad-hoc queries
- Relational integrity
- Rich SQL
- Reporting

---

## DynamoDB vs Redis

### Question

**What is the difference between DynamoDB and Redis?**

| Aspect | DynamoDB | Redis |
|---|---|---|
| Primary role | Persistent database | In-memory data store |
| Durability | Persistent | Depends on configuration |
| Query model | Key-value/document | Rich data structures |
| Typical use | System of record | Cache, counters, transient state |
| Persistence | Core capability | Configurable |
| Latency | Low | Extremely low |
| Dataset size | Large persistent datasets | Memory-oriented |
| Scaling | Managed distributed database | Depends on deployment mode |

A common backend architecture is:

```text
Client
  ↓
FastAPI / Django
  ↓
Redis Cache
  ↓
DynamoDB
```

Redis should not automatically replace DynamoDB as the system of record.

---

## DynamoDB vs S3

### Question

**When should data be stored in DynamoDB versus S3?**

Use DynamoDB for:

- Structured application records
- Key-based lookups
- Metadata
- State
- Low-latency application access

Use S3 for:

- Large objects
- Images
- Videos
- Documents
- Backups
- Data lake workloads

A common architecture is:

```text
DynamoDB
──────────────
order_id
customer_id
status
document_key
──────────────
        │
        │
        ▼
S3
──────────────
Large Document
──────────────
```

Do not use DynamoDB as a general-purpose blob store when S3 is more appropriate.

---

## DynamoDB vs Aurora

### Question

**When would you choose DynamoDB instead of Amazon Aurora?**

DynamoDB is a strong candidate when:

- Access patterns are known.
- The workload is key-oriented.
- Horizontal scale is central.
- The domain does not require relational joins.
- Predictable low-latency access is important.

Aurora is a strong candidate when:

- SQL is required.
- Relational modeling is important.
- Complex queries are needed.
- Joins are central to the application.
- Existing relational workloads are being migrated.

---

## BatchWriteItem vs TransactWriteItems

### Question

**What is the difference between batch writes and transactions?**

| Aspect | Batch Write | Transaction |
|---|---|---|
| Primary goal | Efficient bulk operations | Atomic multi-item operations |
| Atomic across all operations | No | Yes, transaction semantics |
| Typical use | Bulk import/delete | Business-critical consistency |
| Conditional operations | Limited compared with transactions | Supported |
| Cost/complexity | Lower | Higher |

Use batch operations for throughput.

Use transactions when atomicity is part of the business requirement.

---

## BatchGetItem vs TransactGetItems

### Question

**When would you use `BatchGetItem` versus `TransactGetItems`?**

`BatchGetItem` is appropriate when retrieving multiple known items efficiently.

`TransactGetItems` is appropriate when the application needs a transactional read across multiple items.

Do not choose a transaction merely because multiple records are involved. Use it when transactional consistency is actually required.

---

## DynamoDB Streams vs Kafka

### Question

**What is the difference between DynamoDB Streams and Kafka?**

| Aspect | DynamoDB Streams | Kafka |
|---|---|---|
| Primary purpose | Capture DynamoDB item changes | General-purpose event streaming |
| Source | DynamoDB table changes | Many producers |
| Retention/use model | Change-data capture | Durable event log |
| Consumers | Lambda and stream consumers | Many consumer applications |
| Replay architecture | More limited | Strong replay-oriented model |
| Event source | DynamoDB | General event producers |
| Operational scope | Tightly integrated with DynamoDB | General event platform |

Use DynamoDB Streams when the primary requirement is reacting to DynamoDB changes.

Use Kafka when the organization needs a broader event-streaming platform with independent producers, consumers, retention, replay, and event-processing requirements.

---

## DynamoDB Streams vs EventBridge

### Question

**How do DynamoDB Streams and EventBridge differ?**

DynamoDB Streams captures changes originating from DynamoDB.

EventBridge is an event-routing service designed to route events between producers and consumers.

A common architecture is:

```text
DynamoDB
    ↓
DynamoDB Stream
    ↓
Lambda
    ↓
EventBridge
    ↓
Multiple Consumers
```

This can separate database change capture from broader enterprise event routing.

---

## DynamoDB vs MongoDB

### Question

**How does DynamoDB compare with MongoDB?**

| Aspect | DynamoDB | MongoDB |
|---|---|---|
| Managed AWS integration | Excellent | Requires MongoDB service/deployment |
| Data model | Key-value/document | Document |
| Query flexibility | Access-pattern driven | Rich document queries |
| Joins | Not relational | Limited compared with SQL |
| Scaling | AWS-managed distributed model | Distributed cluster model |
| Indexing | Primary key + secondary indexes | Multiple index/query capabilities |
| Operational model | Highly managed | More database configuration/control |

DynamoDB is particularly strong when the application is designed around known access patterns and AWS-native managed infrastructure.

MongoDB can be attractive when richer document querying and flexible query patterns are more important.

---

## DynamoDB vs Cassandra

### Question

**What are the major differences between DynamoDB and Cassandra?**

Both are distributed NoSQL systems designed for scalable workloads, but their operational models differ.

| Aspect | DynamoDB | Cassandra |
|---|---|---|
| Service model | Fully managed AWS service | Self-managed or managed service |
| Infrastructure | AWS-managed | More operational responsibility |
| Data modeling | Query/access-pattern driven | Query-driven |
| Multi-region | Global Tables | Multi-datacenter replication |
| Operational burden | Lower | Higher |
| AWS integration | Native | External |

The choice is often influenced as much by operational requirements and ecosystem as by database capabilities.

---

## DynamoDB vs RDBMS Transactions

### Question

**Are DynamoDB transactions equivalent to PostgreSQL transactions?**

No.

DynamoDB supports transactional operations, but its transaction model is designed around DynamoDB's distributed NoSQL architecture.

PostgreSQL provides a broader relational transaction model involving:

- Multiple statements
- Relational constraints
- Joins
- Isolation levels
- Rich SQL operations

DynamoDB transactions are useful for atomic operations across multiple DynamoDB items, but they do not turn DynamoDB into a relational database.

---

## Conditional Write vs Transaction

### Question

**When is a conditional write preferable to a transaction?**

Use a conditional write when correctness depends on a condition involving a single item.

Example:

```text
Update inventory
IF quantity >= requested_quantity
```

Use a transaction when several items must participate in one atomic business operation.

Example:

```text
Update order
+
Decrement inventory
+
Create payment record
```

Do not use a transaction when a single conditional update is sufficient.

---

## TTL vs Explicit Delete

### Question

**What is the difference between DynamoDB TTL and explicit deletion?**

| Aspect | TTL | Explicit Delete |
|---|---|---|
| Trigger | Expiration timestamp | Application request |
| Timing | Asynchronous | Immediate operation request |
| Control | Limited | High |
| Typical use | Automatic expiration | Business deletion |
| Exact timing | Not guaranteed | Request-driven |

TTL is appropriate for:

- Temporary sessions
- Expiring tokens
- Short-lived records
- Cache-like data

It should not be treated as an exact-time scheduler.

---

## DynamoDB TTL vs Redis Expiration

### Question

**How does DynamoDB TTL differ from Redis key expiration?**

Both support expiration semantics, but they serve different roles.

Redis expiration is commonly used for cache and ephemeral data.

DynamoDB TTL is primarily an asynchronous cleanup mechanism for expired persistent records.

Therefore:

```text
Redis
→ Expiration is part of cache behavior

DynamoDB TTL
→ Expiration is asynchronous item cleanup
```

Do not design business logic that requires DynamoDB TTL deletion to occur at an exact timestamp.

---

## Strong Consistency vs Transactions

### Question

**Does using a strongly consistent read provide transaction semantics?**

No.

A strongly consistent read provides a stronger read visibility guarantee for the supported operation.

A transaction provides atomicity across a set of transactional operations.

They solve different problems:

```text
Strong Read
→ "What is the current committed value?"

Transaction
→ "Perform these operations atomically."
```

---

## Single-Table vs Multi-Table Design

### Question

**What is the difference between single-table and multi-table DynamoDB design?**

### Single-Table Design

Multiple entity types share one table:

```text
PK              SK
CUSTOMER#123    PROFILE
CUSTOMER#123    ORDER#1
CUSTOMER#123    ORDER#2
```

Advantages:

- Efficient related-entity queries
- Fewer tables
- Access-pattern-oriented design
- Potentially fewer operational resources

Limitations:

- More complex key design
- Requires careful access-pattern analysis
- Can be harder for teams unfamiliar with the model

### Multi-Table Design

Separate tables represent different entities:

```text
Customers
Orders
Payments
Products
```

Advantages:

- Clearer separation
- Easier independent lifecycle management
- Simpler mental model for some teams

Limitations:

- Cross-entity access may require multiple requests
- More tables to operate
- May require application-level joins

There is no universal rule that single-table design is always better.

---

## Single-Region vs Global Tables

### Question

**When should you use DynamoDB Global Tables?**

Use Global Tables when the application requires multi-region data replication and regional access.

Typical drivers include:

- Multi-region applications
- Regional latency requirements
- Disaster recovery
- Regional resilience
- Data locality requirements

Architecture:

```text
Region A
DynamoDB
    ↕
Global Tables Replication
    ↕
Region B
DynamoDB
```

Multi-region architecture introduces additional complexity around:

- Conflict resolution
- Write ownership
- Application behavior
- Regional failure
- Data residency
- Operational monitoring

Do not adopt Global Tables merely because multi-region sounds more resilient.

---

## Strongly Consistent vs Eventually Consistent Architecture

### Question

**How would you decide whether an application needs strong consistency?**

Ask:

- Does the user require immediate read-after-write visibility?
- Can stale data cause an incorrect business decision?
- Can the application tolerate temporary inconsistency?
- Can the operation be made idempotent?
- Can the workflow be asynchronous?

Examples where eventual consistency may be acceptable:

- Product recommendations
- Analytics dashboards
- Activity feeds
- Search indexes

Examples where stronger guarantees may matter:

- Inventory validation
- Critical state transitions
- Financial workflows

The correct answer depends on the business invariant rather than technical preference.

---

## Query vs GSI

### Question

**Is adding a GSI always better than changing the query?**

No.

A GSI should be introduced when it supports an important access pattern that the existing key schema cannot efficiently satisfy.

Adding an index introduces:

- Additional storage
- Additional write work
- Additional operational monitoring
- Additional cost
- Additional data-model complexity

Before creating a GSI, ask whether the access pattern can be served naturally by the existing partition and sort keys.

---

## Redis Cache vs DynamoDB Read

### Question

**When should you cache a DynamoDB read in Redis?**

Caching is useful when:

- The same data is read frequently.
- The data changes relatively infrequently.
- Lower latency is valuable.
- DynamoDB read traffic is high.
- The application can tolerate cache invalidation complexity.

Example:

```text
Request
  ↓
Redis
  ├── Hit → Return
  │
  └── Miss
       ↓
    DynamoDB
       ↓
    Redis
       ↓
    Return
```

Caching should not be introduced merely to compensate for an inefficient DynamoDB access pattern.

---

## DynamoDB vs ElastiCache

### Question

**Why would you use DynamoDB and ElastiCache together?**

They solve different problems.

```text
Application
    ↓
ElastiCache
    ↓ cache miss
DynamoDB
    ↓
Persistent data
```

DynamoDB can act as the persistent system of record while ElastiCache provides low-latency access to frequently requested data.

The architecture introduces cache invalidation and consistency considerations.

---

## Common Comparison Mistakes

| Mistake | Better Reasoning |
|---|---|
| "DynamoDB is always better than SQL" | Choose based on access patterns and relational requirements |
| "GSI is just another table" | Understand index keys, projection, capacity, and propagation |
| "Scan is fine for small APIs" | Consider future growth and production traffic |
| "On-demand is always cheaper" | Compare actual workload economics |
| "Transactions solve every consistency problem" | Use the smallest mechanism that satisfies the invariant |
| "Redis replaces DynamoDB" | Cache and persistent database have different roles |
| "Strong consistency should always be enabled" | Use it only where business requirements justify it |
| "Global Tables automatically solve DR" | Multi-region writes introduce architectural complexity |
| "More indexes always improve query performance" | Indexes add storage, write, and operational costs |
| "Single-table design is mandatory" | Choose the model appropriate for the workload and team |

---

## Interview Decision Framework

When asked to compare two DynamoDB technologies or architectural choices, use this structure:

```text
1. Define the two options
        ↓
2. Identify the primary difference
        ↓
3. Explain when each is appropriate
        ↓
4. Discuss scalability implications
        ↓
5. Discuss consistency implications
        ↓
6. Discuss cost implications
        ↓
7. Discuss operational complexity
        ↓
8. Give a production example
        ↓
9. State the trade-off
```

A strong senior-level answer should sound like:

> "I would choose A when the workload has requirement X. I would choose B when requirement Y matters more. The main trade-off is Z, and I would validate the choice against traffic shape, consistency requirements, cost, and operational constraints."

---

## Key Takeaways

- DynamoDB comparisons should be answered through workload, access-pattern, consistency, scalability, cost, and operational trade-offs rather than by declaring one technology universally better.
- `Query`, `GetItem`, GSIs, LSIs, batch operations, and transactions solve different problems; choosing the smallest mechanism that satisfies the access pattern usually produces simpler systems.
- DynamoDB is strongest for predictable key-oriented access at large scale, while relational databases remain stronger for joins, complex SQL, and ad-hoc relational workloads.
- Indexes, caches, transactions, Global Tables, and event-driven components improve specific capabilities but each introduces additional cost, complexity, or consistency considerations.
- Senior-level comparison answers explain not only what differs, but why the difference matters to production architecture.