# 01- Core MongoDB Interview Questions

## Overview

This document is an interview-focused reference for MongoDB fundamentals and core backend engineering concepts.

The questions progress from foundational MongoDB concepts to senior-level reasoning around data modeling, queries, indexing, consistency, transactions, replication, performance, and Python integration.

The goal is not to memorize commands. Strong MongoDB interviews typically test whether you can explain **why a design works, what trade-offs it introduces, and how it behaves under production load**.

---

## MongoDB Fundamentals

### What is MongoDB?

MongoDB is a document-oriented NoSQL database that stores data as BSON documents inside collections.

Instead of organizing data primarily around tables and rows, MongoDB organizes it around:

```text
Database
    ↓
Collection
    ↓
Document
    ↓
Fields
```

A document can contain nested objects and arrays:

```json
{
  "_id": "customer-001",
  "name": "Aranya",
  "email": "aranya@example.com",
  "address": {
    "city": "Kolkata",
    "country": "India"
  },
  "orders": [
    {
      "order_id": "order-001",
      "total": 2500
    }
  ]
}
```

MongoDB is particularly useful when:

- Data structures evolve frequently.
- Documents naturally represent application entities.
- Nested data is commonly accessed together.
- Horizontal scaling is required.
- The application benefits from flexible schema design.

The important engineering principle is that MongoDB schema design should still be deliberate. Flexible schema does not mean schema-less architecture.

---

### How is MongoDB different from a relational database?

| Concept | MongoDB | Relational Database |
|---|---|---|
| Primary structure | Document | Table |
| Record | Document | Row |
| Attribute | Field | Column |
| Relationship | Embedded/reference | Foreign key |
| Schema | Flexible | Usually explicitly defined |
| Joins | `$lookup`, application logic | Native joins |
| Transactions | Supported | Mature core capability |
| Scaling model | Replication + sharding | Replication + partitioning/sharding depending on DB |
| Typical modeling approach | Access-pattern driven | Relationship/normalization driven |

The important difference is not simply "MongoDB is NoSQL."

The more useful distinction is:

> MongoDB encourages modeling data around the application's access patterns and document boundaries.

A relational design may normalize related data into multiple tables and reconstruct it using joins. MongoDB may instead embed frequently accessed related data into one document.

---

### What is BSON?

BSON means **Binary JSON**.

MongoDB stores documents internally using BSON rather than plain JSON.

BSON supports JSON-like structures plus additional types such as:

- `ObjectId`
- `Date`
- `Decimal128`
- `Binary`
- `Int32`
- `Int64`
- `Timestamp`

This matters because MongoDB can preserve types that JSON cannot represent natively.

---

### What is an ObjectId?

`ObjectId` is a BSON type commonly used as MongoDB's default `_id`.

Example:

```javascript
ObjectId("650f1c9f8b7e123456789abc")
```

It is designed to provide a practically unique identifier and contains timestamp-related information.

In Python:

```python
from bson import ObjectId

document_id = ObjectId()

collection.find_one({"_id": document_id})
```

A common interview trap is assuming that every MongoDB `_id` must be an `ObjectId`.

It does not.

MongoDB allows other unique `_id` values, such as strings or application-generated UUIDs.

---

### What is schema flexibility?

MongoDB does not require every document in a collection to have exactly the same fields.

For example:

```json
{
  "name": "Alice",
  "email": "alice@example.com"
}
```

and:

```json
{
  "name": "Bob",
  "email": "bob@example.com",
  "phone": "+91-9999999999"
}
```

can coexist.

However, production applications often enforce schema discipline using:

- Application-level validation
- Pydantic models
- JSON Schema validation
- Versioned document structures
- Migration scripts
- Contract tests

---

## Documents and Data Modeling

### What is the most important principle when designing a MongoDB schema?

Design around **access patterns**.

Before creating collections, identify:

- What queries will be executed?
- Which fields are filtered?
- Which fields are sorted?
- Which data is always read together?
- What is the expected document size?
- How frequently is data updated?
- What is the cardinality of relationships?
- Which operations must be atomic?

A useful design process is:

```text
Business requirements
        ↓
Access patterns
        ↓
Document boundaries
        ↓
Embedding/reference decisions
        ↓
Indexes
        ↓
Operational characteristics
```

---

### When should you embed documents?

Embedding is appropriate when related data:

- Is usually read with the parent.
- Has a bounded size.
- Has a similar lifecycle.
- Does not need independent querying at large scale.
- Benefits from single-document atomicity.

Example:

```json
{
  "_id": "customer-001",
  "name": "Alice",
  "address": {
    "city": "Kolkata",
    "country": "India"
  }
}
```

Reading the customer also retrieves the address.

Advantages:

- Fewer queries.
- No join required.
- Atomic updates within the document.
- Good read performance.

Limitations:

- Document growth.
- Repeated data.
- Potential write contention on hot documents.

---

### When should you use references?

Use references when related data:

- Has independent lifecycle.
- Is large or unbounded.
- Is shared by many parent documents.
- Must be queried independently.
- Changes frequently and should not be duplicated.

Example:

```json
{
  "_id": "order-001",
  "customer_id": "customer-001",
  "items": [
    {
      "product_id": "product-001",
      "quantity": 2
    }
  ]
}
```

The order references the customer and product rather than embedding complete customer and product documents.

---

### Embedding vs referencing: how would you decide in an interview?

Do not answer simply:

> "Embed for performance and reference for normalization."

A stronger answer is:

> "I would start with access patterns, cardinality, document growth, update frequency, and consistency requirements. If related data is bounded, read together, and has the same lifecycle, I prefer embedding. If it is independently accessed, unbounded, shared, or frequently updated independently, I prefer references."

---

### How would you model one-to-many relationships?

It depends on cardinality.

For bounded relationships:

```json
{
  "_id": "customer-001",
  "addresses": [
    {
      "type": "home",
      "city": "Kolkata"
    },
    {
      "type": "work",
      "city": "Bengaluru"
    }
  ]
}
```

For large or unbounded relationships:

```text
customers
    |
    | customer_id
    ↓
orders
```

Do not create an ever-growing array containing millions of child documents inside one parent document.

---

### What is a hot document?

A hot document is a document that receives disproportionately frequent reads or writes.

For example:

```json
{
  "_id": "global-counter",
  "count": 9823749823
}
```

If thousands of workers continuously update this same document, it can become a contention point.

Possible solutions include:

- Sharding counters.
- Partitioning state.
- Using multiple counter documents.
- Aggregating periodically.
- Redesigning the access pattern.

---

### What is document growth and why does it matter?

Documents can grow as the application adds embedded data.

Unbounded growth can cause:

- Larger reads and writes.
- Increased memory pressure.
- More document movement internally.
- Higher replication traffic.
- Hot-document contention.
- Approaching MongoDB's document-size limit.

A common anti-pattern is embedding an unbounded event or transaction history directly inside a parent document.

---

## CRUD

### What is the difference between `insertOne()` and `insertMany()`?

`insertOne()` inserts a single document.

```javascript
db.users.insertOne({
  name: "Alice",
  email: "alice@example.com"
})
```

`insertMany()` inserts multiple documents:

```javascript
db.users.insertMany([
  {name: "Alice"},
  {name: "Bob"}
])
```

`insertMany()` is useful for batch ingestion and can reduce per-operation overhead.

In Python:

```python
collection.insert_many(documents)
```

For high-volume workloads, consider `bulk_write()` when different operations need to be mixed.

---

### What is an upsert?

An upsert means:

> Update the matching document; if none exists, insert a new document.

Example:

```javascript
db.users.updateOne(
  {email: "alice@example.com"},
  {$set: {name: "Alice"}},
  {upsert: true}
)
```

Upserts are useful for:

- Idempotent consumers.
- Synchronization jobs.
- Cache/database reconciliation.
- External system imports.

The filter must be designed carefully. A weak filter can create unintended documents.

---

### What is the difference between `updateOne()` and `replaceOne()`?

`updateOne()` modifies selected fields using update operators:

```javascript
db.users.updateOne(
  {_id: 1},
  {$set: {status: "active"}}
)
```

`replaceOne()` replaces the entire document except for its identity semantics:

```javascript
db.users.replaceOne(
  {_id: 1},
  {
    _id: 1,
    name: "Alice",
    status: "active"
  }
)
```

Use `replaceOne()` only when the application owns the complete document representation.

---

### What is atomic in MongoDB?

Individual operations on a single document are atomic.

For example:

```javascript
db.accounts.updateOne(
  {_id: "account-001"},
  {$inc: {balance: -100}}
)
```

The update is atomic for that document.

MongoDB also supports multi-document transactions, but transactions should not be used to compensate for poor document modeling.

---

### What is a bulk write?

A bulk write groups multiple write operations into one API request.

Python example:

```python
from pymongo import DeleteOne, InsertOne, UpdateOne

operations = [
    InsertOne({"_id": "user-1", "name": "Alice"}),
    UpdateOne(
        {"_id": "user-2"},
        {"$set": {"active": True}},
    ),
    DeleteOne({"_id": "user-3"}),
]

collection.bulk_write(operations)
```

Bulk writes are useful for:

- ETL pipelines.
- Data migrations.
- Batch processing.
- Synchronization workers.

---

## Querying

### What are MongoDB query operators?

MongoDB query operators allow applications to express conditions.

Common categories include:

| Category | Examples |
|---|---|
| Comparison | `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin` |
| Logical | `$and`, `$or`, `$not`, `$nor` |
| Element | `$exists`, `$type` |
| Array | `$all`, `$elemMatch`, `$size` |
| Evaluation | `$regex`, `$expr` |
| Geospatial | `$near`, `$geoWithin` |

Example:

```javascript
db.orders.find({
  status: "completed",
  total: {$gte: 1000}
})
```

---

### What is projection?

Projection controls which fields MongoDB returns.

```javascript
db.users.find(
  {status: "active"},
  {name: 1, email: 1}
)
```

Projection can reduce:

- Network transfer.
- Application memory usage.
- Serialization cost.

It does not automatically make every query fast. Index design and query execution still matter.

---

### What is a cursor?

A cursor represents the result set returned by a query.

MongoDB does not necessarily materialize the entire result set in application memory.

Python example:

```python
cursor = collection.find(
    {"status": "active"},
    {"_id": 1, "email": 1},
)

for document in cursor:
    process(document)
```

This pattern is preferable to loading very large result sets into a Python list.

---

### Why can `skip()` become inefficient for pagination?

Offset pagination such as:

```javascript
db.orders.find()
  .sort({_id: 1})
  .skip(100000)
  .limit(100)
```

may require MongoDB to walk past many records before returning the requested page.

For large collections, range-based pagination is often preferable.

Example:

```javascript
db.orders.find({
  _id: {$gt: last_seen_id}
})
.sort({_id: 1})
.limit(100)
```

This is commonly called **cursor-based** or **keyset pagination**.

---

### How would you implement pagination in a Python API?

A production-oriented design might expose:

```text
GET /orders?limit=50&after=<cursor>
```

The cursor represents the last observed sort key.

Conceptually:

```python
query = {"_id": {"$gt": last_id}}

documents = (
    collection
    .find(query)
    .sort("_id", 1)
    .limit(50)
)
```

For compound sorting, the cursor must represent all required ordering fields.

---

## Indexing

### Why do indexes exist?

An index allows MongoDB to locate matching documents without scanning every document in the collection.

Without an appropriate index:

```text
Query
  ↓
COLLSCAN
  ↓
Many documents examined
```

With an appropriate index:

```text
Query
  ↓
IXSCAN
  ↓
Matching keys
  ↓
Relevant documents
```

Indexes improve reads but increase:

- Storage requirements.
- Write cost.
- Memory pressure.
- Index maintenance overhead.

---

### What index is created automatically?

MongoDB automatically creates an index on `_id`.

```javascript
db.users.getIndexes()
```

The `_id` index enforces uniqueness for `_id` values and supports `_id` lookups.

---

### What is a compound index?

A compound index contains multiple fields.

```javascript
db.orders.createIndex({
  customer_id: 1,
  status: 1,
  created_at: -1
})
```

It can support queries that align with the index's field ordering.

Compound indexes should be designed from real query patterns rather than created arbitrarily.

---

### What is the ESR guideline?

ESR stands for:

- **Equality**
- **Sort**
- **Range**

A common compound-index design heuristic is to place equality fields first, followed by sort fields and then range fields when that ordering fits the workload.

Example query:

```javascript
db.orders.find({
  customer_id: "customer-001",
  status: "completed",
  created_at: {$gte: start_date}
}).sort({
  total: -1
})
```

A candidate index must be evaluated using `explain()` rather than selected solely from the acronym.

---

### What is a multikey index?

A multikey index indexes array values.

Given:

```json
{
  "tags": ["python", "mongodb", "backend"]
}
```

an index such as:

```javascript
db.posts.createIndex({tags: 1})
```

can support queries against array elements.

Multikey indexes have additional constraints and design considerations, especially when multiple array fields are involved.

---

### What is a covered query?

A covered query can be satisfied entirely from an index without fetching the full documents.

For example, if an index contains:

```javascript
{email: 1, status: 1}
```

and the query filters and projects only those indexed fields, MongoDB may avoid fetching documents.

Covered queries can reduce I/O, but they should be treated as an optimization rather than a default design objective.

---

### What is a partial index?

A partial index indexes only documents matching a filter.

Example:

```javascript
db.orders.createIndex(
  {customer_id: 1, created_at: -1},
  {
    partialFilterExpression: {
      status: "active"
    }
  }
)
```

This can reduce index size and maintenance cost when only a subset of documents is queried frequently.

---

### What is a TTL index?

A TTL index automatically removes documents after a configured period.

Typical use cases:

- Sessions
- Temporary tokens
- Short-lived events
- Expiring cache-like records

Example:

```javascript
db.sessions.createIndex(
  {created_at: 1},
  {expireAfterSeconds: 3600}
)
```

TTL deletion is asynchronous. It should not be treated as an exact-time scheduling mechanism.

---

### What is over-indexing?

Over-indexing occurs when a collection contains more indexes than the workload requires.

Every additional index can increase:

- Write latency.
- Storage.
- Memory usage.
- Maintenance work.

A senior engineer should periodically evaluate:

- Query patterns.
- Index usage.
- Index size.
- Write performance.
- Redundant indexes.

---

## Query Performance

### How do you diagnose a slow MongoDB query?

Start with `explain()`.

```javascript
db.orders.find({
  customer_id: "customer-001",
  status: "completed"
}).explain("executionStats")
```

Important metrics include:

| Metric | Meaning |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index entries examined |
| `totalDocsExamined` | Documents examined |
| Execution time | Query execution duration |
| `COLLSCAN` | Collection scan |
| `IXSCAN` | Index scan |
| `FETCH` | Document retrieval after index lookup |
| `SORT` | Explicit sort stage |

A useful diagnostic heuristic is:

```text
totalDocsExamined >> nReturned
```

This often indicates that the query is examining substantially more documents than it returns.

---

### What is a COLLSCAN?

`COLLSCAN` means MongoDB is scanning the collection.

It is not automatically a problem.

A collection scan can be reasonable when:

- The collection is small.
- The query returns most documents.
- An index would not provide meaningful selectivity.

The mistake is treating every `COLLSCAN` as a failure.

---

### What is IXSCAN?

`IXSCAN` indicates that MongoDB is scanning an index.

An index scan is generally useful when the index efficiently narrows the candidate set.

However:

```text
IXSCAN != automatically fast
```

A poorly selective index can still examine a large number of keys and documents.

---

### What is the query planner?

MongoDB's query planner evaluates possible execution strategies and selects a winning plan.

Conceptually:

```text
Query
  ↓
Candidate plans
  ├── COLLSCAN
  ├── Index A
  ├── Index B
  └── Compound Index C
          ↓
     Winning plan
```

The planner's choice should be validated with actual execution statistics.

---

## Aggregation

### What is the aggregation pipeline?

The aggregation pipeline processes documents through a sequence of stages.

Example:

```javascript
db.orders.aggregate([
  {$match: {status: "completed"}},
  {
    $group: {
      _id: "$customer_id",
      total_spend: {$sum: "$total"}
    }
  },
  {$sort: {total_spend: -1}},
  {$limit: 10}
])
```

The pipeline conceptually behaves as:

```text
Documents
    ↓
$match
    ↓
$group
    ↓
$sort
    ↓
$limit
    ↓
Results
```

---

### Why should `$match` usually appear early?

Early filtering reduces the number of documents passed to later stages.

Poor:

```text
Large collection
    ↓
$group
    ↓
$match
```

Better:

```text
Large collection
    ↓
$match
    ↓
$group
```

Early filtering can also allow MongoDB to use appropriate indexes.

---

### What is `$lookup`?

`$lookup` performs a left outer join-like operation between collections.

Example:

```javascript
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customer_id",
      foreignField: "_id",
      as: "customer"
    }
  }
])
```

It is useful, but excessive `$lookup` usage can indicate that the data model or access pattern needs reconsideration.

---

## Transactions

### Does MongoDB support transactions?

Yes.

MongoDB supports:

- Single-document atomic operations.
- Multi-document transactions.

Transactions can span multiple documents and, depending on deployment topology, multiple collections/databases.

---

### When should you use a transaction?

Use a transaction when multiple writes must satisfy one atomic business invariant.

Example:

```text
Transfer $100
    ↓
Debit account A
    +
Credit account B
    ↓
Both succeed or both fail
```

Without a transaction, the system could debit one account and fail before crediting the other.

---

### When should you avoid transactions?

Avoid using transactions merely because they are available.

If a workflow can be represented as one atomic document update, that is often simpler.

Transactions can introduce:

- Additional coordination.
- Longer locks/resource retention.
- More operational complexity.
- Higher latency.
- Retry complexity.

Good MongoDB schema design can reduce the need for multi-document transactions.

---

### What is a MongoDB session?

A session represents logical interaction between the application and MongoDB.

Transactions are executed within sessions.

Python example:

```python
with client.start_session() as session:
    with session.start_transaction():
        accounts.update_one(
            {"_id": source_id},
            {"$inc": {"balance": -amount}},
            session=session,
        )

        accounts.update_one(
            {"_id": destination_id},
            {"$inc": {"balance": amount}},
            session=session,
        )
```

The same session must be propagated to the operations participating in the transaction.

---

### What are read concern and write concern?

They control consistency and durability behavior.

| Setting | Controls |
|---|---|
| Read concern | What level of data visibility a read requires |
| Write concern | What acknowledgment/durability level a write requires |
| Read preference | Which replica-set members can serve reads |

A common production configuration is based around majority acknowledgment where the application's durability requirements justify it.

---

## Replication and High Availability

### What is a replica set?

A replica set is a group of MongoDB servers that maintain copies of the same dataset.

Typical topology:

```text
                ┌──────────────┐
                │   Primary    │
                └──────┬───────┘
                       │
              Replication
                 ┌─────┴─────┐
                 ↓           ↓
          ┌──────────┐ ┌──────────┐
          │ Secondary│ │ Secondary│
          └──────────┘ └──────────┘
```

The primary normally handles writes.

Secondaries replicate data from the primary and can participate in failover.

---

### What happens when the primary fails?

The replica set detects the failure and eligible members can participate in an election.

Conceptually:

```text
Primary failure
      ↓
Heartbeat detection
      ↓
Election
      ↓
New primary
      ↓
Application reconnects
```

Applications should use a replica-set-aware connection string so the driver can discover the current topology.

---

### What is replication lag?

Replication lag is the delay between an operation being applied on the primary and being applied on a secondary.

High lag can affect:

- Read-after-write behavior.
- Secondary reads.
- Failover readiness.
- Storage capacity.
- Operational reliability.

Monitor replication lag in production.

---

### What is an oplog?

The oplog is a replication log maintained by replica-set members.

It records operations that secondaries use to replicate changes from the primary.

The oplog is also fundamental to features such as:

- Replication.
- Change streams.
- Initial synchronization and recovery mechanisms.

---

## Sharding

### Why does MongoDB support sharding?

Sharding provides horizontal scaling by distributing data across multiple shards.

A simplified architecture is:

```text
                    Application
                         |
                      mongos
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Shard A        Shard B        Shard C
```

Sharding can provide:

- Horizontal storage scaling.
- Horizontal throughput scaling.
- Distribution of large datasets.

However, sharding introduces significant operational and query-routing complexity.

---

### What makes a good shard key?

A good shard key should generally provide:

- High cardinality.
- Reasonable distribution.
- Appropriate frequency characteristics.
- Good query targeting.
- Low risk of creating hot shards.

Avoid choosing a shard key merely because it is unique.

A monotonically increasing key can create concentration of new writes depending on the shard-key design.

---

### What is a scatter-gather query?

A query that cannot be efficiently targeted to a specific shard may be sent to multiple shards.

Conceptually:

```text
Query
  ↓
mongos
  ├── Shard A
  ├── Shard B
  └── Shard C
       ↓
Merge results
```

Scatter-gather queries can become expensive as the cluster grows.

---

## Change Streams

### What are MongoDB change streams?

Change streams allow applications to observe changes to MongoDB data without continuously polling collections.

Applications can react to:

- Inserts
- Updates
- Replacements
- Deletes

Typical architecture:

```text
MongoDB
    ↓
Change Stream
    ↓
Consumer
    ↓
Event Handler
    ↓
Kafka / REST / Worker / Business Service
```

---

### What is a resume token?

A resume token identifies a position in the change stream.

Consumers can persist the token and use it to resume processing after a failure.

A robust consumer should consider:

- Resume-token persistence.
- Duplicate events.
- Consumer crashes.
- MongoDB connectivity failures.
- Idempotent event processing.

Change streams should not be treated as a replacement for durable event infrastructure in every architecture.

---

## Python and PyMongo

### How do you connect Python to MongoDB?

Using PyMongo:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    serverSelectionTimeoutMS=5000,
)

database = client["application"]
collection = database["users"]
```

For production applications:

- Do not hard-code credentials.
- Configure timeouts explicitly.
- Reuse a `MongoClient`.
- Configure connection pooling appropriately.
- Enable appropriate retry behavior.
- Monitor connection failures.

---

### Should you create a new `MongoClient` for every request?

No.

`MongoClient` is designed to manage connections and pooling.

A backend application should generally create a client during application initialization and reuse it.

Poor pattern:

```python
def get_user(user_id):
    client = MongoClient(uri)
    ...
```

Better:

```text
Application startup
        ↓
MongoClient
        ↓
Connection pool
        ↓
Requests / workers
```

Creating clients repeatedly adds connection-management overhead and can exhaust resources.

---

### How do you handle MongoDB configuration in Python?

Use environment-driven configuration.

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "application",
)
```

In production, secrets should come from an appropriate secret-management mechanism rather than source control.

---

### How should MongoDB repositories be structured?

A common backend architecture is:

```text
API / Worker
    ↓
Service Layer
    ↓
Repository
    ↓
PyMongo
    ↓
MongoDB
```

The repository owns database access patterns.

The service layer owns business rules.

This separation makes testing and application evolution easier.

---

## FastAPI and MongoDB

### How would you integrate MongoDB with FastAPI?

A typical architecture is:

```text
HTTP Request
     ↓
FastAPI Route
     ↓
Dependency
     ↓
Service
     ↓
Repository
     ↓
PyMongo
     ↓
MongoDB
```

Create the MongoDB client during application startup and close it during shutdown.

Do not create a new database client for every HTTP request.

---

### What should you consider when using synchronous PyMongo with FastAPI?

Synchronous database operations can block the executing thread.

For applications requiring asynchronous database access, choose a driver and architecture appropriate to the currently supported MongoDB Python ecosystem.

The important interview point is:

> Do not call blocking database operations from an async path without understanding their impact on concurrency.

---

## Django and MongoDB

### Can MongoDB be treated exactly like Django's default ORM?

No.

Django's built-in ORM is designed primarily around relational database concepts.

MongoDB is document-oriented and has different:

- Query semantics.
- Transactions.
- Relationships.
- Schema behavior.
- Indexing model.
- Aggregation capabilities.

Applications using Django with MongoDB often use:

- PyMongo directly.
- A MongoDB-compatible ODM where appropriate.
- Repository/service abstractions.

Do not pretend MongoDB collections behave like Django relational models.

---

## Security

### How should MongoDB be secured in production?

Important controls include:

- Authentication.
- Authorization.
- TLS.
- Network restrictions.
- Least-privilege users.
- Secret management.
- Encryption at rest.
- Encryption in transit.
- Auditing where required.
- Monitoring.
- Regular credential rotation.

A production application should not connect using a MongoDB administrative account.

Prefer a dedicated application identity with only the required permissions.

---

### What is least privilege in MongoDB?

Least privilege means granting an application only the permissions it requires.

For example:

```text
Reporting service
    ↓
Read-only permissions

Order service
    ↓
Read/write orders
    ↓
Required related collections only
```

Avoid giving every service:

```text
readWriteAnyDatabase
```

unless there is a documented operational requirement.

---

## Common Interview Traps

### "MongoDB is schema-less."

Incomplete.

A better answer:

> MongoDB provides schema flexibility, but production applications should still enforce useful contracts through application validation, database validation, versioning, and controlled migrations.

### "MongoDB does not support transactions."

Incorrect.

MongoDB supports both single-document atomicity and multi-document transactions.

### "NoSQL means no relationships."

Incorrect.

MongoDB can represent relationships using:

- Embedded documents.
- References.
- `$lookup`.
- Application-level joins.

The modeling strategy differs from relational databases.

### "Indexes always improve performance."

Incorrect.

Indexes improve specific access patterns while increasing write and storage costs.

An unused or poorly designed index can make the system worse.

### "COLLSCAN always means the query is bad."

Incorrect.

A collection scan can be appropriate for small collections or queries that return a large percentage of the collection.

### "Upsert makes a workflow exactly once."

Incorrect.

Upsert can provide idempotent persistence for a particular key, but external side effects and worker retries still require explicit idempotency design.

### "Embedding is always faster than referencing."

Incomplete.

Embedding can reduce round trips, but excessive embedding can cause document growth, larger writes, contention, and inefficient updates.

---

## Scenario-Based Interview Questions

### Design a notification system using MongoDB.

Consider:

```text
API
 ↓
Notification Service
 ↓
notifications collection
 ↓
Worker
 ↓
Email / SMS provider
```

Potential document:

```json
{
  "_id": "notification-001",
  "user_id": "user-001",
  "type": "email",
  "status": "pending",
  "attempts": 0,
  "created_at": "2026-09-25T10:00:00Z",
  "retry_at": null
}
```

Important design questions:

- How are pending notifications claimed?
- How do multiple workers avoid processing the same notification?
- How are retries represented?
- How are permanent failures handled?
- How do you make provider calls idempotent?
- What indexes support the worker query?
- How do you recover jobs abandoned by crashed workers?

---

### Design an order model.

Start from access patterns:

```text
Get order by ID
List customer orders
Find pending orders
Find recent orders
Calculate customer spend
```

Potential indexes:

```javascript
db.orders.createIndex({
  customer_id: 1,
  created_at: -1
})

db.orders.createIndex({
  status: 1,
  created_at: -1
})
```

The exact indexes should be validated with actual query patterns and `explain()`.

---

### A query became slow after the collection grew from 1 million to 100 million documents. What do you investigate?

Use a structured workflow:

```text
Slow query
   ↓
Capture actual query
   ↓
Run explain("executionStats")
   ↓
Inspect nReturned
   ↓
Inspect totalDocsExamined
   ↓
Inspect totalKeysExamined
   ↓
Inspect winning plan
   ↓
Check indexes
   ↓
Check selectivity/cardinality
   ↓
Check sort behavior
   ↓
Check working set and memory
   ↓
Measure after optimization
```

Do not immediately create an index without understanding the workload.

---

### A worker processes the same MongoDB job twice. How would you investigate?

Check:

- Job-claim query.
- Atomicity of job claiming.
- Worker crash behavior.
- Retry behavior.
- Visibility/lease timeout.
- Job status transitions.
- Duplicate result persistence.
- External side effects.
- Idempotency keys.
- Unique indexes.

The important distinction is:

```text
Duplicate execution
        ≠
Duplicate persisted result
        ≠
Duplicate external side effect
```

Each layer requires its own protection.

---

## Senior-Level Discussion Topics

For senior interviews, expect questions that combine multiple MongoDB concepts.

Examples:

- How would you design a MongoDB schema for a high-write event system?
- How do you choose between embedding and referencing?
- How would you diagnose a query with high `totalDocsExamined`?
- How would you design cursor-based pagination?
- How would you make a MongoDB worker idempotent?
- When would you use a transaction instead of changing the document model?
- How would you choose a shard key?
- How would you handle replica-set failover?
- How would you design MongoDB connection pooling for a FastAPI service?
- How would you safely migrate millions of MongoDB documents?
- How would you detect and remove unused indexes?
- How would you design a change-stream consumer that survives crashes?
- How would you handle MongoDB outages in a microservice?
- How would you balance consistency, latency, and availability?
- How would you design backup and recovery for a production MongoDB cluster?

A strong senior-level answer should usually cover:

```text
Requirements
    ↓
Access patterns
    ↓
Data model
    ↓
Indexes
    ↓
Consistency
    ↓
Failure modes
    ↓
Scaling
    ↓
Observability
    ↓
Security
    ↓
Operational recovery
```

## Key Takeaways

- MongoDB schema design starts with **access patterns, cardinality, document growth, and consistency requirements**, not simply with converting relational tables into collections.
- Query performance depends on the interaction between **query shape, indexes, selectivity, sorting, and the query planner**; use `explain("executionStats")` to validate assumptions.
- MongoDB provides **single-document atomicity, multi-document transactions, replica sets, and configurable read/write behavior**, but each capability introduces specific operational trade-offs.
- Production background workers should assume **at-least-once execution** and use idempotency, durable job state, appropriate indexes, and explicit retry/error handling.
- Senior MongoDB engineering is primarily about **trade-off analysis**: data modeling, consistency, performance, scalability, reliability, security, and operational simplicity.