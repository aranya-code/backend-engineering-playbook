# 02- Index Management

## Overview

MongoDB indexes are one of the primary mechanisms for controlling query performance. An index allows MongoDB to locate matching documents without scanning every document in a collection.

Indexes improve reads by introducing an additional data structure optimized for specific access patterns, but they are not free. Every index consumes storage, memory, build time, and write capacity. Each insert, update, or delete may require corresponding index maintenance.

A production indexing strategy therefore balances:

```text
Query performance
        +
Sort performance
        +
Index coverage
        +
Memory footprint
        +
Write overhead
        +
Storage cost
        +
Operational complexity
```

The correct question is not:

> "Which indexes can I create?"

It is:

> "Which indexes are justified by the application's actual query and sort patterns?"

For backend systems, index design should be driven by:

- Query patterns
- Filter selectivity
- Sort requirements
- Pagination strategy
- Data cardinality
- Read/write ratio
- Document structure
- Multi-tenant access patterns
- Aggregation workloads
- Production latency requirements

## How MongoDB Indexes Work

Without an appropriate index, a query may require a collection scan.

```text
Query
  │
  ▼
Collection Scan
  │
  ├── Document 1 → match?
  ├── Document 2 → match?
  ├── Document 3 → match?
  ├── ...
  └── Document N → match?
```

With an appropriate index:

```text
Query
  │
  ▼
Index
  │
  ├── Matching index entries
  │
  ▼
Document locations
  │
  ▼
Matching documents
```

Conceptually, an index changes the amount of work from something approaching:

```text
O(N)
```

for a broad collection scan toward work based on the relevant index traversal and matching documents.

The exact execution cost depends on:

- Index structure
- Query selectivity
- Number of matching documents
- Sort requirements
- Projection
- Data distribution
- Working-set residency
- Storage performance

An index does not automatically make every query fast.

## The Default `_id` Index

MongoDB automatically creates a unique index on `_id` for collections.

Inspect it with:

```javascript
db.orders.getIndexes()
```

Example:

```javascript
[
  {
    v: 2,
    key: {
      _id: 1
    },
    name: "_id_"
  }
]
```

The `_id` index guarantees uniqueness of `_id` values and supports efficient lookup by `_id`.

Do not attempt to remove the `_id` index from a normal MongoDB collection.

## Index Types

MongoDB supports several index patterns.

| Index type | Primary use |
|---|---|
| Single-field | Queries or sorts involving one field |
| Compound | Queries involving multiple fields |
| Multikey | Queries involving arrays |
| Unique | Enforce uniqueness |
| Partial | Index only documents matching a filter |
| Sparse | Index documents containing a field |
| TTL | Automatically expire documents |
| Text | Text-search workloads |
| Geospatial | Geospatial queries |
| Hashed | Hash-based access patterns and sharding |

The index type should follow the access pattern rather than being selected independently of the application's query design.

## Single-Field Indexes

Create a single-field index with:

```javascript
db.users.createIndex({
    email: 1
})
```

The `1` represents ascending index order.

A descending index uses:

```javascript
db.users.createIndex({
    created_at: -1
})
```

For equality lookups, direction is often less important than for sorting.

A common use case is:

```javascript
db.users.find({
    email: "user@example.com"
})
```

with:

```javascript
db.users.createIndex({
    email: 1
})
```

## When Single-Field Indexes Make Sense

Use a single-field index when:

- A field is frequently queried independently.
- The field is sufficiently selective.
- The query pattern is simple.
- No compound access pattern justifies a compound index.

Example:

```javascript
db.products.find({
    sku: "SKU-12345"
})
```

A unique index may be appropriate:

```javascript
db.products.createIndex(
    {
        sku: 1
    },
    {
        unique: true
    }
)
```

## Compound Indexes

A compound index contains multiple fields.

Example:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1,
    created_at: -1
})
```

This index can support query patterns such as:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
})
```

Compound indexes are central to production MongoDB performance because real backend queries frequently combine:

```text
Tenant / owner
+
Status / state
+
Time range
+
Sort
+
Pagination
```

## Compound Index Prefixes

For:

```javascript
{
    tenant_id: 1,
    status: 1,
    created_at: -1
}
```

the index has an ordered prefix structure:

```text
tenant_id
tenant_id + status
tenant_id + status + created_at
```

Queries that use the leading fields can generally benefit more directly from the index than queries that skip the prefix.

For example:

```javascript
{
    tenant_id: "tenant-42"
}
```

aligns with the prefix.

But a query primarily filtering on:

```javascript
{
    status: "pending"
}
```

does not have the same direct alignment with the compound index.

## Index Ordering and Query Design

Index field order should be selected from actual query patterns.

Consider:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
})
```

A natural candidate is:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1,
    created_at: -1
})
```

The index aligns with:

```text
Equality
Equality
Sort
```

This is an example of the ESR guideline.

## ESR Guideline

ESR stands for:

```text
Equality
Sort
Range
```

It is a practical guideline for compound index design.

For a query such as:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "paid",
    created_at: {
        $gte: ISODate("2026-01-01T00:00:00Z")
    }
}).sort({
    priority: -1
})
```

a candidate index might be:

```javascript
{
    tenant_id: 1,
    status: 1,
    priority: -1,
    created_at: 1
}
```

However, ESR is a guideline, not an unconditional rule.

Actual index selection should be validated with:

```javascript
.explain("executionStats")
```

Data distribution and query shape can change which index performs best.

## Selectivity and Cardinality

Index design must consider cardinality.

Cardinality describes how many distinct values a field contains.

Examples:

| Field | Typical cardinality |
|---|---|
| Country | Low |
| Status | Low |
| Tenant ID | Medium/high |
| Email | High |
| UUID | Very high |

A query such as:

```javascript
{
    status: "active"
}
```

may match a large portion of the collection.

An index on `status` can still be useful, but its effectiveness depends on the complete query pattern and workload.

A highly selective query such as:

```javascript
{
    user_id: "7b8..."
}
```

may benefit much more directly from an index.

Do not use "high cardinality" as the only index-selection rule.

## Unique Indexes

Unique indexes enforce uniqueness.

Example:

```javascript
db.users.createIndex(
    {
        email: 1
    },
    {
        unique: true
    }
)
```

This turns an application-level assumption:

```text
email must be unique
```

into a database-enforced invariant.

This is preferable to relying exclusively on:

```python
if not user_exists(email):
    create_user(email)
```

because concurrent requests can otherwise pass the check simultaneously.

## Unique Indexes and Concurrency

Consider:

```text
Request A ── check email ── not found ── insert
Request B ── check email ── not found ── insert
```

Application-only validation can race.

A unique index provides database-level enforcement:

```text
Request A ── insert ── success
Request B ── insert ── duplicate key error
```

The application should handle the resulting duplicate-key error cleanly.

## Partial Indexes

A partial index only indexes documents matching a specified filter.

Example:

```javascript
db.orders.createIndex(
    {
        tenant_id: 1,
        created_at: -1
    },
    {
        partialFilterExpression: {
            status: "active"
        }
    }
)
```

This can reduce:

- Index size
- Index maintenance
- Memory consumption

when only a subset of documents participates in an important workload.

## When Partial Indexes Are Useful

Partial indexes are particularly useful when:

```text
Only a subset of documents
is queried frequently
```

Examples:

- Active accounts
- Pending jobs
- Unprocessed events
- Non-deleted records
- Current subscriptions

Example:

```javascript
db.jobs.createIndex(
    {
        status: 1,
        scheduled_at: 1
    },
    {
        partialFilterExpression: {
            status: {
                $in: ["pending", "retry"]
            }
        }
    }
)
```

This can be preferable to indexing every historical job.

## Partial Index Limitations

The query must be compatible with the partial-index filter for MongoDB to safely use the partial index.

For example, an index restricted to:

```javascript
{
    status: "active"
}
```

cannot generally serve as a complete index for queries requiring arbitrary status values.

Always validate candidate indexes with `explain()`.

## Sparse Indexes

A sparse index only includes documents containing the indexed field.

Example:

```javascript
db.users.createIndex(
    {
        secondary_email: 1
    },
    {
        sparse: true
    }
)
```

Sparse indexes can be useful when a field is optional and absent from many documents.

However, partial indexes are often more expressive because they allow explicit filtering conditions.

Do not use sparse indexes simply because a field is optional. First determine whether a partial index better expresses the intended workload.

## TTL Indexes

TTL indexes automatically remove documents after a configured period.

Example:

```javascript
db.sessions.createIndex(
    {
        created_at: 1
    },
    {
        expireAfterSeconds: 86400
    }
)
```

This is useful for:

- Temporary sessions
- Short-lived tokens
- Expiring event data
- Cache-like documents
- Operational records with explicit retention requirements

TTL deletion is performed asynchronously. It should not be treated as an exact-time scheduler.

## TTL Production Considerations

TTL indexes are appropriate when:

```text
Data has a defined retention period
```

They are not appropriate when deletion must happen at an exact business-defined instant.

For example:

```text
"Delete this session after approximately 24 hours"
```

is a reasonable TTL use case.

A requirement such as:

```text
"Execute exactly at 10:00:00"
```

should not depend on TTL deletion timing.

## Multikey Indexes

MongoDB automatically treats an index involving an array field as a multikey index.

Example document:

```json
{
  "order_id": "ORD-1001",
  "tags": [
    "priority",
    "international"
  ]
}
```

Index:

```javascript
db.orders.createIndex({
    tags: 1
})
```

Multikey indexes allow queries against array elements.

However, large arrays can increase index size and write overhead.

## Large Arrays and Index Growth

Suppose each document contains:

```json
{
  "user_id": "U100",
  "permissions": [
    "... thousands of values ..."
  ]
}
```

Indexing the array can generate substantial index entries.

This can increase:

- Storage
- Write cost
- Cache pressure
- Index maintenance time

Unbounded arrays are both a data-modeling and indexing concern.

## Text Indexes

Text indexes support MongoDB text-search functionality.

Example:

```javascript
db.products.createIndex({
    description: "text"
})
```

Query:

```javascript
db.products.find({
    $text: {
        $search: "wireless headphones"
    }
})
```

Text indexes can be useful for simple text-search requirements, but they are not a general replacement for specialized search systems.

For advanced search requirements, evaluate the capabilities and operational requirements of MongoDB's search features or dedicated search platforms.

## Geospatial Indexes

For geospatial workloads, MongoDB supports geospatial index types such as `2dsphere`.

Example:

```javascript
db.locations.createIndex({
    coordinates: "2dsphere"
})
```

A geospatial query can use operators such as:

```javascript
db.locations.find({
    coordinates: {
        $near: {
            $geometry: {
                type: "Point",
                coordinates: [88.3639, 22.5726]
            },
            $maxDistance: 5000
        }
    }
})
```

Use geospatial indexes only when the data model and query semantics require them.

## Hashed Indexes

Hashed indexes transform indexed values into hash values.

Example:

```javascript
db.users.createIndex({
    user_id: "hashed"
})
```

Hashed indexes are particularly relevant to hash-based sharding and certain equality workloads.

They are not a general-purpose replacement for normal B-tree-style indexes because they do not provide the same ordering semantics for range queries or sorting.

## Index Intersection

MongoDB can sometimes use multiple indexes for a query.

For example:

```javascript
{
    tenant_id: "tenant-42",
    status: "pending"
}
```

could potentially involve separate indexes:

```javascript
{
    tenant_id: 1
}
```

and:

```javascript
{
    status: 1
}
```

However, relying on index intersection as the primary indexing strategy is often inferior to designing an index around a frequent query shape.

If a query is important and predictable, prefer an index explicitly aligned with that query.

## Covered Queries

A covered query can be satisfied entirely from an index without fetching the full documents.

Consider:

```javascript
db.users.createIndex({
    tenant_id: 1,
    email: 1
})
```

Query:

```javascript
db.users.find(
    {
        tenant_id: "tenant-42"
    },
    {
        _id: 0,
        email: 1
    }
)
```

The query may be covered by the index because both the filter and requested field are represented in the index.

Covered queries can reduce document fetches and therefore reduce I/O.

Validate coverage using:

```javascript
.explain("executionStats")
```

## Sorting and Indexes

Sorting can become expensive when MongoDB must sort a large intermediate result.

Example:

```javascript
db.orders.find({
    tenant_id: "tenant-42"
}).sort({
    created_at: -1
})
```

A matching compound index can often avoid an in-memory sort:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    created_at: -1
})
```

Inspect the execution plan for stages such as:

```text
SORT
```

An explicit `SORT` stage is not automatically a problem, but a large blocking sort in a latency-sensitive query deserves investigation.

## Pagination and Indexes

Offset pagination:

```javascript
db.orders.find({
    tenant_id: "tenant-42"
})
.skip(100000)
.limit(50)
```

can become increasingly expensive as the offset grows.

Cursor-based pagination is usually more scalable.

Example:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    created_at: {
        $lt: last_seen_created_at
    }
})
.sort({
    created_at: -1
})
.limit(50)
```

Supporting index:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    created_at: -1
})
```

For production APIs, index design and pagination design should be considered together.

## Query Planner

MongoDB's query planner evaluates candidate execution strategies and selects a winning plan.

Conceptually:

```text
Query
  │
  ▼
Query Planner
  │
  ├── Collection scan
  ├── Index A
  ├── Index B
  └── Index C
  │
  ▼
Winning Plan
  │
  ▼
Execution
```

The winning plan depends on:

- Query shape
- Available indexes
- Data distribution
- Sort requirements
- Query planner behavior
- Runtime observations

Do not assume that the existence of an index means MongoDB will always choose it.

## Explain Plans

Use:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).explain("executionStats")
```

Important metrics include:

| Metric | Meaning |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index keys examined |
| `totalDocsExamined` | Documents examined |
| `executionTimeMillis` | Execution time |
| `winningPlan` | Selected execution strategy |
| `rejectedPlans` | Alternative candidate plans |

A useful diagnostic comparison is:

```text
nReturned
vs
totalDocsExamined
vs
totalKeysExamined
```

## Detecting Inefficient Index Usage

Suppose:

```text
nReturned           = 50
totalKeysExamined  = 900000
totalDocsExamined  = 900000
```

This suggests the query performed a large amount of work relative to its result size.

By contrast:

```text
nReturned           = 50
totalKeysExamined  = 60
totalDocsExamined  = 50
```

is generally a much more efficient execution pattern.

These values must still be interpreted in context.

## `COLLSCAN`

A `COLLSCAN` stage indicates a collection scan.

Example conceptual plan:

```text
COLLSCAN
   │
   ▼
Entire collection
```

A collection scan is not automatically wrong.

It can be reasonable when:

- The collection is small.
- The query returns most documents.
- The query is administrative.
- An index would not provide meaningful selectivity.

A large, frequent, latency-sensitive API query performing a collection scan is a stronger signal for investigation.

## `IXSCAN`

An `IXSCAN` stage indicates index scanning.

Conceptually:

```text
IXSCAN
  │
  ▼
Index entries
  │
  ▼
Matching document references
```

An `IXSCAN` alone does not prove good performance.

An index can still be poorly selective and require many keys to be examined.

## `FETCH`

A `FETCH` stage means MongoDB retrieves documents after obtaining candidate records from the index.

Conceptually:

```text
IXSCAN
  ↓
Document references
  ↓
FETCH
  ↓
Documents
```

A covered query may avoid fetching the full documents.

## Index Lifecycle

Indexes should be treated as production artifacts.

A mature lifecycle is:

```text
Identify query pattern
        ↓
Measure baseline
        ↓
Design candidate index
        ↓
Test with realistic data
        ↓
Validate with explain
        ↓
Build index safely
        ↓
Observe production behavior
        ↓
Monitor size and usage
        ↓
Review periodically
        ↓
Remove only after validation
```

Index creation should not be treated as a one-time development task.

## Creating Indexes

Basic:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    created_at: -1
})
```

Named:

```javascript
db.orders.createIndex(
    {
        tenant_id: 1,
        created_at: -1
    },
    {
        name: "orders_tenant_created_desc"
    }
)
```

Explicit names make operational tooling and index review easier.

## Creating Multiple Indexes

MongoDB supports creating multiple indexes in one operation.

Example:

```javascript
db.orders.createIndexes([
    {
        key: {
            tenant_id: 1,
            created_at: -1
        },
        name: "orders_tenant_created_desc"
    },
    {
        key: {
            tenant_id: 1,
            status: 1
        },
        name: "orders_tenant_status"
    }
])
```

Build indexes intentionally rather than creating large numbers of speculative indexes.

## Dropping an Index

Drop a named index:

```javascript
db.orders.dropIndex(
    "orders_tenant_created_desc"
)
```

You can also specify the key pattern:

```javascript
db.orders.dropIndex({
    tenant_id: 1,
    created_at: -1
})
```

Never remove an index from production merely because it appears redundant without validating all workloads.

## Dropping All Non-`_id` Indexes

MongoDB supports:

```javascript
db.orders.dropIndexes()
```

This is a destructive administrative operation.

Do not run it casually against production.

It can cause immediate performance regressions by removing all user-created indexes.

## Hidden Indexes

MongoDB supports hiding indexes from the query planner without immediately dropping them.

Conceptually:

```javascript
db.orders.hideIndex(
    "orders_tenant_created_desc"
)
```

A hidden index remains available for inspection and can be unhidden later.

This provides a safer way to test whether removing an index would affect query plans.

The operational pattern is:

```text
Existing index
      ↓
Hide index
      ↓
Observe query behavior
      ↓
Validate production workload
      ↓
Unhide or remove
```

This is generally safer than immediately dropping an uncertain index.

## Index Build Considerations

Building an index on a large production collection can consume substantial:

- CPU
- Memory
- I/O
- Disk space
- Operational capacity

Before creating an index, consider:

- Collection size
- Existing workload
- Replica-set topology
- Storage headroom
- Maintenance window
- Managed-service behavior
- Application latency requirements

Index creation should be planned like a production change.

## Indexes in Replica Sets

Replica-set deployments require additional operational consideration.

Index creation affects database resources and therefore can influence:

- Primary workload
- Replication behavior
- Secondary performance
- Application latency

For large collections, follow the deployment's supported operational procedures and test index builds on representative data before production rollout.

Do not assume that a theoretically correct index is operationally free to build.

## Indexes and Write Performance

Every relevant write can require index maintenance.

For:

```text
1 document insert
```

MongoDB may need to update:

```text
_id index
+
index A
+
index B
+
index C
+
...
```

Therefore:

```text
More indexes
    ↓
More write maintenance
    ↓
Higher write cost
```

This is why over-indexing is a common production problem.

## Read/Write Trade-off

| Strategy | Read impact | Write impact | Storage |
|---|---|---|---|
| No secondary indexes | Poor for selective queries | Low | Low |
| Few targeted indexes | Good | Moderate | Moderate |
| Many indexes | Potentially excellent | High | High |
| Redundant indexes | Little additional value | Unnecessary cost | Unnecessary |

The goal is not maximum index count.

The goal is an index set that efficiently supports important workloads.

## Index Redundancy

Consider:

```javascript
{
    tenant_id: 1
}
```

and:

```javascript
{
    tenant_id: 1,
    created_at: -1
}
```

The compound index may already support some queries that the single-field index supports.

This does not automatically mean the single-field index is redundant.

Validate:

- Query shapes
- Sort behavior
- Selectivity
- Index usage
- Application workload

Then determine whether the smaller index provides meaningful independent value.

## Index Naming Convention

Use descriptive names.

Example:

```javascript
{
    tenant_id: 1,
    status: 1,
    created_at: -1
}
```

could be named:

```text
orders_tenant_status_created_desc
```

rather than:

```text
idx1
```

A useful convention should make the indexed fields and direction obvious.

## Indexes and Multi-Tenant Systems

Multi-tenant systems commonly filter by:

```javascript
tenant_id
```

For example:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
})
```

A compound index might be:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1,
    created_at: -1
})
```

This can support tenant-scoped access efficiently.

Tenant isolation is primarily a security and application-design concern. An index improves performance but does not enforce authorization.

## Indexes and Soft Deletes

Suppose documents contain:

```javascript
{
    tenant_id: "tenant-42",
    deleted_at: null
}
```

and most application queries exclude deleted records.

A partial index may be useful:

```javascript
db.orders.createIndex(
    {
        tenant_id: 1,
        created_at: -1
    },
    {
        partialFilterExpression: {
            deleted_at: null
        }
    }
)
```

This can avoid indexing historical/deleted documents when they are outside the primary workload.

Validate the exact query shape and partial-index eligibility with `explain()`.

## Indexes and Background Workers

Celery or other workers often query operational states:

```javascript
db.jobs.find({
    status: "pending",
    scheduled_at: {
        $lte: new Date()
    }
}).sort({
    scheduled_at: 1
}).limit(100)
```

A candidate index:

```javascript
db.jobs.createIndex({
    status: 1,
    scheduled_at: 1
})
```

can support the worker's access pattern.

This is important because backend engineers often optimize API queries while forgetting:

- Celery workers
- Scheduled jobs
- Kafka consumers
- Reporting jobs
- Reconciliation processes

These workloads also require appropriate indexes.

## Indexes and Aggregation

Aggregation pipelines can benefit from indexes, particularly when early stages contain selective filters.

Example:

```javascript
db.orders.aggregate([
    {
        $match: {
            tenant_id: "tenant-42",
            status: "paid"
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
])
```

Candidate index:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1
})
```

A `$match` near the beginning of the pipeline can reduce the amount of data subsequent stages must process.

Always validate aggregation plans rather than assuming that adding an index guarantees improvement.

## Indexes and `$lookup`

For aggregation pipelines containing `$lookup`, index design must consider the foreign collection as well.

Example:

```javascript
{
    $lookup: {
        from: "customers",
        localField: "customer_id",
        foreignField: "_id",
        as: "customer"
    }
}
```

The foreign collection's join field should be appropriately indexed.

Indexes cannot compensate for an inherently excessive join workload, but they can substantially reduce lookup cost when the access pattern is selective.

## Indexes and Large Collections

For a collection containing hundreds of millions of documents:

```text
Index design becomes architecture.
```

A poor index can result in:

- Large storage consumption
- Increased memory pressure
- Long index builds
- Higher write latency
- Increased backup footprint

Before adding an index to a large production collection:

1. Measure the query.
2. Identify the query shape.
3. Validate selectivity.
4. Estimate index size.
5. Test against representative data.
6. Evaluate write overhead.
7. Plan deployment.
8. Monitor after rollout.

## Index Size and Memory

Indexes are part of the working set.

A large index that is frequently accessed can consume significant memory resources.

Example:

```text
Collection data = 800 GB
Indexes         = 500 GB
Hot working set = 100 GB
```

The entire dataset does not necessarily need to fit in memory, but frequently accessed index pages can have a substantial impact on performance.

Index design therefore affects both:

```text
Storage
```

and:

```text
Memory pressure
```

## Index Overloading

A common anti-pattern is creating one very large compound index to support many unrelated queries.

For example:

```javascript
{
    tenant_id: 1,
    status: 1,
    category: 1,
    region: 1,
    priority: 1,
    created_at: -1
}
```

This may look flexible, but it can introduce:

- Large index size
- Higher write cost
- Poor prefix alignment for some queries
- Increased memory pressure
- More difficult index maintenance

Design indexes around actual query families rather than attempting to create a universal index.

## Index Selection Workflow

A senior engineer should use a repeatable workflow.

```text
Identify slow query
        ↓
Capture exact query shape
        ↓
Measure baseline
        ↓
Run explain("executionStats")
        ↓
Inspect existing indexes
        ↓
Analyze selectivity and sort
        ↓
Design candidate index
        ↓
Test candidate
        ↓
Compare execution metrics
        ↓
Deploy safely
        ↓
Monitor production
        ↓
Review long-term usage
```

## Before-and-After Optimization Example

Query:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
}).limit(50)
```

Suppose the initial plan performs:

```text
COLLSCAN
+
SORT
```

with:

```text
totalDocsExamined = 8,000,000
nReturned         = 50
```

Candidate index:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1,
    created_at: -1
})
```

After deployment, the plan may use:

```text
IXSCAN
+
FETCH
+
LIMIT
```

with substantially fewer documents examined.

The important engineering process is not "add an index."

It is:

```text
Measure
→
Change
→
Measure again
```

## Python and PyMongo

Indexes should generally be managed as infrastructure or deployment concerns rather than being created every time an application process starts.

For example, application code can define expected indexes:

```python
from pymongo import ASCENDING, DESCENDING, IndexModel

indexes = [
    IndexModel(
        [
            ("tenant_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING),
        ],
        name="orders_tenant_status_created_desc",
    ),
]
```

Index creation should then be handled through a controlled deployment or migration process appropriate to the application architecture.

Avoid this pattern on every request:

```python
collection.create_index(...)
```

It introduces unnecessary operational work and obscures schema changes.

## Django and Index Management

When using MongoDB with Django through a MongoDB-specific backend or an ODM such as MongoEngine, index management depends on the integration layer.

Do not assume Django's relational database indexing semantics map directly to MongoDB.

For PyMongo-based repository architectures, indexes are often managed explicitly:

```text
Application schema
        ↓
Index definitions
        ↓
Deployment / migration process
        ↓
MongoDB
```

The exact mechanism should be standardized within the project.

## FastAPI and Index Management

FastAPI applications should not create indexes inside individual request handlers.

Avoid:

```python
@app.get("/orders")
def get_orders():
    collection.create_index(...)
    return list(collection.find(...))
```

Instead:

```text
Deployment
   ↓
Database migration / operational job
   ↓
Index creation
   ↓
Application rollout
```

This keeps application request paths deterministic.

## CI/CD and Index Changes

Index changes should be treated as database schema changes.

A practical deployment flow is:

```mermaid
flowchart LR
    A[Query Analysis] --> B[Index Design]
    B --> C[Test Against Representative Data]
    C --> D[Review]
    D --> E[Production Index Build]
    E --> F[Monitor]
    F --> G[Validate Query Performance]
```

For critical indexes, record:

- Why the index exists
- Query pattern
- Expected workload
- Index definition
- Estimated size
- Deployment considerations
- Validation metrics

This makes future index cleanup much safer.

## Monitoring Indexes

Monitor:

- Index size
- Index growth
- Index usage
- Query latency
- Query plans
- Write latency
- Storage consumption
- Memory pressure

A useful operational correlation is:

```text
Index added
    ↓
Read latency decreases
    ↓
Write latency increases
    ↓
Storage increases
    ↓
Memory pressure changes
```

An index should be considered successful only after evaluating the whole workload.

## Production Index Review

Periodically review:

```text
Index definition
Index size
Index usage
Supported queries
Write overhead
Storage cost
```

For each index ask:

> What production workload justifies this index?

If the answer is unclear, investigate before changing it.

## Security Considerations

Indexes can indirectly affect security-sensitive query performance.

For example, authorization queries often contain:

```javascript
{
    tenant_id: "...",
    user_id: "...",
    resource_id: "..."
}
```

If these queries become slow, applications may be tempted to add caching or bypass checks.

Correct index design can help authorization queries remain predictable.

However:

> An index does not enforce authorization.

The application or database authorization model must still ensure that the caller is permitted to access the requested tenant or resource.

## High Availability Considerations

Indexes exist across replica-set members according to MongoDB's replication and index-building behavior.

Index changes should therefore be evaluated against:

- Primary workload
- Secondary workload
- Replication health
- Storage capacity
- Failover behavior

Monitor replication lag and node health during significant index operations.

For large production indexes, follow the current MongoDB deployment-specific recommendations rather than relying on outdated assumptions about index build behavior.

## Backup and Recovery Considerations

Indexes contribute to database storage and can affect:

- Backup size
- Restore duration
- Storage consumption
- Recovery planning

Logical backups such as `mongodump` include database objects and data, and index definitions are represented in the dump metadata.

For disaster recovery planning, test the complete restore process rather than assuming that a successful backup automatically guarantees a usable recovery.

## Operational Runbook

### Create an Index

```javascript
db.orders.createIndex(
    {
        tenant_id: 1,
        status: 1,
        created_at: -1
    },
    {
        name: "orders_tenant_status_created_desc"
    }
)
```

### Inspect Indexes

```javascript
db.orders.getIndexes()
```

### Inspect Index Sizes

```javascript
db.orders.stats().indexSizes
```

### Inspect Index Usage

```javascript
db.orders.aggregate([
    {
        $indexStats: {}
    }
])
```

### Analyze Query Execution

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
}).limit(50).explain("executionStats")
```

### Hide an Index

```javascript
db.orders.hideIndex(
    "orders_tenant_status_created_desc"
)
```

### Unhide an Index

```javascript
db.orders.unhideIndex(
    "orders_tenant_status_created_desc"
)
```

### Drop a Specific Index

```javascript
db.orders.dropIndex(
    "orders_tenant_status_created_desc"
)
```

## Common Mistakes

### Creating an Index for Every Query

**Problem:** Every new query receives a new index.

**Why it happens:** Indexes are treated as free performance improvements.

**Impact:**

- More storage
- Higher write overhead
- Larger working set
- More operational complexity

**Better approach:** Group related query patterns and design a minimal effective index set.

### Using the Wrong Compound Field Order

**Problem:** A compound index exists but does not align with the query's equality, sort, and range behavior.

**Fix:** Analyze the complete query and validate candidate ordering with `explain()`.

### Following ESR Mechanically

**Problem:** ESR is treated as an absolute algorithm.

**Fix:** Use ESR as a starting heuristic and validate against real data distribution and workload.

### Indexing Low-Selectivity Fields Alone

**Problem:** An index such as:

```javascript
{
    status: 1
}
```

may provide limited benefit when almost every document has the same status.

**Fix:** Evaluate the complete access pattern, often with additional fields.

### Ignoring Sort Requirements

**Problem:** The filter is indexed but the database still performs an expensive sort.

**Fix:** Design the compound index around both filtering and ordering.

### Ignoring Worker Queries

**Problem:** API queries are optimized while Celery, Kafka, or scheduled workloads remain slow.

**Fix:** Inventory all production query consumers.

### Dropping an Apparently Unused Index

**Problem:** The index is unused during the observation window but supports an infrequent workload.

**Fix:** Check application code, scheduled jobs, reporting workloads, and historical traffic before removal.

### Creating Indexes at Application Startup

**Problem:** Every application instance checks or builds indexes.

**Fix:** Manage indexes through controlled operational or deployment workflows.

### Ignoring Index Build Cost

**Problem:** A large production index is created without capacity planning.

**Fix:** Evaluate collection size, disk headroom, workload, replica-set impact, and deployment strategy.

### Treating Indexes as Authorization

**Problem:** Developers assume that an indexed `tenant_id` provides tenant isolation.

**Fix:** Authorization must be enforced separately. Indexes only optimize data access.

## Interview Traps

### Does Every Query Need an Index?

No.

Small collections, low-selectivity queries, full-collection operations, and administrative workloads may legitimately use collection scans.

### Does `IXSCAN` Mean the Query Is Fast?

No.

An index scan can still examine a large number of keys and documents.

Inspect:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

### Is a Compound Index Always Better Than Multiple Single-Field Indexes?

No.

It depends on query patterns, selectivity, sorting, write workload, and index maintenance cost.

### Is ESR a Strict Rule?

No.

ESR is a practical guideline for compound index design. Actual query behavior should be validated with realistic workloads and execution plans.

### Why Can Too Many Indexes Hurt Writes?

Every relevant write may require maintenance of multiple index structures.

Therefore:

```text
More indexes
→
More write work
→
Higher write latency and storage usage
```

### What Is a Covered Query?

A query that can obtain the required filter and projected fields entirely from an index without fetching the full documents.

### How Do You Decide Whether to Remove an Index?

Evaluate:

```text
Usage
+
Query patterns
+
Business importance
+
Query latency
+
Write overhead
+
Index size
```

Use hiding as a safer validation mechanism where appropriate before permanent removal.

## Troubleshooting Methodology

```text
Symptom
↓
Slow query / high write latency / excessive storage / memory pressure
↓
Possible causes
↓
Missing index / wrong index order / low selectivity / redundant indexes /
large multikey index / excessive index count / poor query shape
↓
Isolation strategy
↓
Capture the exact query and workload
↓
Diagnostic commands
↓
db.collection.getIndexes()
db.collection.stats()
db.collection.aggregate([{ $indexStats: {} }])
db.collection.find(...).explain("executionStats")
db.serverStatus()
↓
Root cause
↓
Determine whether the issue is query shape, index design, data distribution,
index footprint, or write-maintenance overhead
↓
Corrective action
↓
Create, modify, hide, or remove an index; or redesign the query/schema
↓
Prevention
↓
Query-driven index reviews, explain-plan validation,
production monitoring, and controlled index lifecycle management
```

## Key Takeaways

- **Design indexes from real query and sort patterns; do not treat indexes as free performance features.**
- **Compound indexes require deliberate field ordering, with ESR serving as a guideline that must be validated using real execution plans.**
- **Index size, usage, memory footprint, and write-maintenance cost must be evaluated together when managing production indexes.**
- **Use `explain("executionStats")`, `$indexStats`, and collection statistics to measure index effectiveness rather than assuming an index is useful because it exists.**
- **Treat index creation, hiding, and removal as production schema changes with controlled deployment, monitoring, and rollback considerations.**