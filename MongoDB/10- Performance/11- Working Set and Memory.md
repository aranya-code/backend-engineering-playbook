# 11- Working Set and Memory

## Overview

MongoDB performance depends heavily on how effectively frequently accessed data and indexes fit into available memory. The **working set** is the portion of application data and indexes that the workload actively accesses over a given period.

When the working set is effectively served from memory, MongoDB can avoid repeated storage reads. When it exceeds available memory, storage I/O becomes increasingly important and query latency can become less predictable.

A useful mental model is:

```text
Application workload
        │
        ▼
Frequently accessed documents + indexes
        │
        ▼
      Working Set
        │
        ▼
RAM / filesystem cache
        │
        ├── Cache hit → lower latency
        │
        └── Cache miss → storage I/O
                         │
                         ▼
                    Higher latency
```

Working-set analysis is therefore not simply a "how much RAM does MongoDB need?" question. It is a workload, index, document-size, access-pattern, and storage-performance problem.

## What Is the Working Set?

The working set is the subset of data and indexes that are actively used by the workload.

For a backend API, the working set might consist of:

```text
Users frequently queried
Orders from recent months
Active sessions
Product catalog
Frequently used indexes
Tenant metadata
Recent events
```

A collection may contain:

```text
2 TB total data
```

while the workload may repeatedly access only:

```text
150 GB of documents
+
30 GB of indexes
```

The workload's effective working set is therefore much smaller than the total database size.

The important question is not:

> Does the entire database fit into RAM?

It is:

> Does the data and index portion that the workload repeatedly needs have efficient access to memory?

## Why Working Set Matters

Memory access is substantially faster than storage access.

Conceptually:

```text
CPU
 ↓
Memory
 ↓
Storage
```

When a query repeatedly accesses data that is already available through the relevant cache layers:

```text
Query
  ↓
Index/data already cached
  ↓
Low storage I/O
  ↓
Predictable latency
```

When frequently accessed data repeatedly requires storage reads:

```text
Query
  ↓
Required page not cached
  ↓
Storage read
  ↓
I/O latency
  ↓
Higher query latency
```

This becomes particularly important for:

- High-QPS APIs
- Low-latency services
- Large collections
- Large indexes
- Random-access workloads
- Multi-tenant applications
- Aggregation workloads
- High-concurrency systems

## Total Dataset Size vs Working Set

These are different measurements.

| Metric | Meaning |
|---|---|
| Collection size | Logical size of collection data |
| Index size | Space consumed by indexes |
| Total database size | Aggregate logical storage footprint |
| Working set | Frequently accessed portion of data and indexes |
| Resident memory | Memory currently resident for MongoDB/process/cache purposes |
| Storage capacity | Total persistent storage available |

Example:

```text
Collection data      = 500 GB
Indexes              = 80 GB
Total logical data   = 580 GB
Active workload      = 100 GB
Available memory     = 128 GB
```

This may be substantially healthier than a workload that actively accesses the entire 580 GB randomly.

The numbers alone do not prove that the workload fits in memory, but they illustrate why total database size is not sufficient for capacity planning.

## MongoDB and Memory

Modern MongoDB deployments commonly rely on the operating system's filesystem cache in addition to memory used directly by MongoDB processes.

For WiredTiger-based deployments, the storage engine maintains an internal cache while the operating system also caches filesystem data.

Conceptually:

```text
MongoDB
   │
   ├── WiredTiger internal cache
   │
   └── OS filesystem cache
             │
             ▼
          Storage
```

The exact amount of memory available to each layer depends on the MongoDB version, deployment environment, configuration, operating system, and other processes.

Do not treat all machine RAM as application-available cache.

## WiredTiger Cache

WiredTiger uses an internal cache for frequently accessed database content and related structures.

MongoDB also benefits from filesystem caching.

This means a simplified model such as:

```text
RAM = MongoDB cache
```

is incorrect.

A better model is:

```text
System memory
    │
    ├── MongoDB process / WiredTiger cache
    ├── Filesystem cache
    ├── Other processes
    └── OS overhead
```

Capacity planning must therefore account for the complete system rather than assigning all memory to MongoDB.

## Memory Pressure

When the active workload exceeds available effective cache capacity, MongoDB may need to access storage more frequently.

The resulting behavior can look like:

```text
Working set grows
       ↓
Cache effectiveness decreases
       ↓
Storage reads increase
       ↓
I/O latency increases
       ↓
Query latency increases
       ↓
Application p95/p99 increases
```

Memory pressure does not necessarily cause immediate failure.

A common production symptom is gradually worsening latency under a larger or more diverse workload.

## Working Set and Indexes

Indexes are part of the performance-critical working set.

Consider:

```text
Documents = 200 GB
Indexes   = 100 GB
```

A query might retrieve only a small number of documents but depend heavily on a large index.

If the relevant index pages are frequently accessed, memory pressure can affect query performance even when the query returns only a few documents.

This is why index size matters in addition to collection size.

## Index Working Set

Consider:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).sort({
    created_at: -1
}).limit(50)
```

A suitable compound index might be:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    status: 1,
    created_at: -1
})
```

The workload may repeatedly access the corresponding index region.

If that region remains hot:

```text
Request
  ↓
Index lookup
  ↓
Small number of keys examined
  ↓
Small number of documents fetched
```

the query can remain fast even when the entire collection is much larger than RAM.

## Working Set and Selectivity

Selective queries reduce the amount of data the database needs to inspect.

Compare:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    order_id: "ORD-100123"
})
```

with:

```javascript
db.orders.find({
    status: "pending"
})
```

If `status = "pending"` matches a large percentage of the collection, the query may require significantly more index and document access.

High-selectivity access patterns often improve the effective working set because fewer pages are needed for a particular request.

## Working Set and Cardinality

Cardinality describes how many distinct values a field contains.

For example:

```text
tenant_id:
10 million distinct tenants
```

has very different access characteristics from:

```text
status:
5 distinct values
```

Low-cardinality indexes can still be useful, but indexing a low-cardinality field does not automatically make queries highly selective.

Working-set behavior depends on:

- Cardinality
- Data distribution
- Query frequency
- Query shape
- Index structure
- Document size
- Access locality

## Temporal Locality

Many backend workloads have temporal locality.

Examples:

```text
Recent orders
Recent events
Recently updated records
Current sessions
Today's transactions
```

A service might have:

```text
5 TB historical data
200 GB recent active data
```

If most requests access recent records, the effective working set can be closer to the active 200 GB than the entire historical dataset.

This is a major reason why time-based data modeling can have significant performance benefits.

## Example: Event Collection

Consider:

```json
{
  "_id": "...",
  "tenant_id": "tenant-42",
  "event_type": "payment",
  "created_at": "2026-09-20T10:30:00Z",
  "payload": {}
}
```

If most queries are:

```javascript
db.events.find({
    tenant_id: "tenant-42",
    created_at: {
        $gte: ISODate("2026-09-20T00:00:00Z")
    }
})
```

then recent data is likely to be accessed much more frequently than years-old events.

An index such as:

```javascript
db.events.createIndex({
    tenant_id: 1,
    created_at: -1
})
```

can support the dominant access pattern.

The goal is not necessarily to fit every historical document in memory.

## Working Set and Document Size

Large documents increase memory and I/O pressure.

Suppose:

```text
Document A = 4 KB
Document B = 500 KB
```

A query returning 100 documents could involve approximately:

```text
A: 100 × 4 KB   = 400 KB
B: 100 × 500 KB = 50 MB
```

The logical query result is still 100 documents, but the amount of data transferred and processed is dramatically different.

Large documents can therefore reduce the effective number of useful documents that fit into cache.

## Large Document Anti-Pattern

Avoid embedding unlimited historical data inside a document.

For example:

```json
{
  "_id": "user-123",
  "events": [
    "...",
    "...",
    "...",
    "... thousands of entries ..."
  ]
}
```

This can cause:

- Document growth
- Larger reads
- Larger updates
- More memory pressure
- Increased network transfer
- Hot-document contention

Prefer bounded arrays or separate collections when the child data grows continuously.

## Working Set and Hot Documents

A **hot document** is a document that is accessed or modified disproportionately often.

Examples:

```text
Account balance
Inventory counter
Popular product
Global configuration
Tenant metadata
Rate-limit state
```

A single document can become a contention and workload hotspot even if the overall working set is small.

For example:

```text
10,000 requests/sec
        ↓
same document
        ↓
repeated reads/writes
        ↓
hot access pattern
```

The solution may involve:

- Better data modeling
- Sharding the workload
- Bucketing
- Pre-aggregation
- Caching
- Reducing write frequency

Simply adding RAM does not necessarily solve a hot-document design problem.

## Working Set and Read-Heavy Workloads

Read-heavy workloads benefit strongly from good locality.

Example:

```text
Product API
    ↓
Popular products
    ↓
Frequently repeated queries
    ↓
Small active working set
```

Potential optimizations include:

- Proper indexes
- Projection
- Redis caching
- Query-result caching
- Efficient document design
- Read replicas where appropriate

MongoDB memory should complement, not replace, application-level caching strategies.

## MongoDB vs Redis

Redis is an explicit in-memory data store.

MongoDB is a persistent database that uses memory and storage together.

A common architecture is:

```text
Client
  ↓
FastAPI / Django
  ├── Redis → frequently cached application data
  │
  └── MongoDB → durable source of truth
```

Redis can reduce MongoDB load for:

- Frequently requested objects
- Session-like state
- Expensive computed responses
- Rate limiting
- Short-lived derived data

But Redis should not be introduced simply because MongoDB data does not fit entirely in RAM.

First identify whether the actual problem is:

- Poor indexing
- Poor query design
- Excessive document size
- Inefficient aggregation
- Insufficient memory
- Storage latency
- Excessive concurrency

## Projection and Working Set

Returning unnecessary fields increases data movement.

Instead of:

```javascript
db.users.find({
    tenant_id: "tenant-42"
})
```

consider:

```javascript
db.users.find(
    { tenant_id: "tenant-42" },
    {
        _id: 1,
        email: 1,
        name: 1
    }
)
```

Projection can reduce:

- Network transfer
- Application deserialization
- Memory usage
- Response size

When the query can be satisfied entirely from an index, projection can also enable a covered-query pattern.

## Covered Queries

A covered query can return required fields directly from an index without fetching the full document.

Example:

```javascript
db.users.createIndex({
    tenant_id: 1,
    email: 1
})
```

Query:

```javascript
db.users.find(
    { tenant_id: "tenant-42" },
    {
        _id: 0,
        email: 1
    }
)
```

The query can potentially avoid fetching documents if the filter and projected fields are available from the index.

This reduces document reads and can improve cache efficiency.

Validate with:

```javascript
db.users.find(
    { tenant_id: "tenant-42" },
    { _id: 0, email: 1 }
).explain("executionStats")
```

Do not assume a query is covered without verifying the actual execution plan.

## Working Set and Aggregation

Aggregation can consume significant memory depending on:

- Number of documents processed
- `$group`
- `$sort`
- `$lookup`
- `$facet`
- `$unwind`
- Intermediate result size
- Cardinality

For example:

```text
Large collection
      ↓
$match
      ↓
$group
      ↓
$sort
      ↓
$lookup
```

is substantially different from:

```text
Large collection
      ↓
$match
      ↓
$limit
      ↓
small working set
      ↓
remaining processing
```

Early filtering reduces the amount of data subsequent stages need to process.

## Working Set and `$sort`

Sorting large result sets can be expensive.

Example:

```javascript
db.orders.aggregate([
    {
        $sort: {
            created_at: -1
        }
    }
])
```

If the sort cannot efficiently use an appropriate index, MongoDB may need to process a large number of records.

Prefer filtering first:

```javascript
db.orders.aggregate([
    {
        $match: {
            tenant_id: "tenant-42",
            status: "completed"
        }
    },
    {
        $sort: {
            created_at: -1
        }
    },
    {
        $limit: 100
    }
])
```

and support the access pattern with an appropriate index.

## Working Set and `$group`

Grouping can create a large intermediate state.

For example:

```javascript
db.events.aggregate([
    {
        $group: {
            _id: "$customer_id",
            total: { $sum: "$amount" }
        }
    }
])
```

If millions of unique customers are involved, the grouping state can become substantial.

Reduce input early:

```javascript
db.events.aggregate([
    {
        $match: {
            tenant_id: "tenant-42",
            created_at: {
                $gte: ISODate("2026-09-01T00:00:00Z")
            }
        }
    },
    {
        $group: {
            _id: "$customer_id",
            total: { $sum: "$amount" }
        }
    }
])
```

The performance principle is:

> Reduce the number and size of documents entering expensive stages.

## Working Set and `$lookup`

`$lookup` can become expensive when large datasets are joined without appropriate indexes or filtering.

A poor pattern is:

```text
Huge local dataset
      ↓
$lookup
      ↓
Huge foreign dataset
      ↓
Large intermediate result
```

A better pattern is:

```text
Filter local data
      ↓
Reduce documents
      ↓
$lookup
      ↓
Use indexed foreign key
      ↓
Project only required fields
```

For high-throughput APIs, consider whether the join should happen at request time or whether the data should be modeled differently.

## Working Set and Pagination

Offset pagination:

```javascript
db.orders.find({
    tenant_id: "tenant-42"
})
.sort({
    created_at: -1
})
.skip(100000)
.limit(50)
```

can become increasingly expensive as the offset grows.

Cursor-based pagination is generally better for large datasets:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    created_at: {
        $lt: last_created_at
    }
})
.sort({
    created_at: -1
})
.limit(50)
```

With an appropriate index:

```javascript
db.orders.createIndex({
    tenant_id: 1,
    created_at: -1
})
```

the database can navigate directly toward the next page instead of repeatedly advancing through a large offset.

## Working Set and Query Locality

Two systems with the same database size can have very different performance.

### Workload A

```text
10 million requests
→ same 100,000 documents
```

### Workload B

```text
10 million requests
→ random access across 1 billion documents
```

Workload A has strong locality.

Workload B has poor locality.

Therefore:

```text
Database size alone
≠
Working-set size
≠
Performance
```

Access pattern is a first-class performance variable.

## Measuring Collection Size

MongoDB provides collection statistics that can help estimate storage characteristics.

For example:

```javascript
db.orders.stats()
```

Useful fields can include:

- `size`
- `count`
- `avgObjSize`
- `storageSize`
- `totalIndexSize`
- `nindexes`

The exact statistics available depend on MongoDB version and storage engine.

Use these values as inputs to capacity analysis rather than treating one metric as the entire memory requirement.

## Measuring Index Size

Inspect indexes with:

```javascript
db.orders.stats().indexSizes
```

This helps identify indexes consuming substantial storage.

Another useful inspection command is:

```javascript
db.orders.getIndexes()
```

Index size matters because a large index can increase memory pressure and storage I/O.

## `$collStats`

For deeper operational analysis, aggregation with `$collStats` can expose collection-level statistics.

Example:

```javascript
db.orders.aggregate([
    {
        $collStats: {
            storageStats: {}
        }
    }
])
```

Use administrative statistics carefully in production and prefer monitoring systems for continuous observability.

## Database-Level Statistics

For broad database inspection:

```javascript
db.stats()
```

This can help identify:

- Collection counts
- Object counts
- Storage usage
- Index usage
- Data size

Use database statistics together with host-level metrics.

## Server-Level Memory Observation

MongoDB server status can provide memory-related operational information:

```javascript
db.serverStatus()
```

Depending on version and deployment, inspect relevant:

- Memory metrics
- WiredTiger metrics
- Cache metrics
- Connections
- Operations
- Storage statistics

For production systems, combine MongoDB metrics with operating-system or infrastructure metrics.

## WiredTiger Cache Metrics

WiredTiger-related statistics can help identify cache pressure.

For example:

```javascript
db.serverStatus().wiredTiger.cache
```

Useful metrics vary by MongoDB version but can provide information about:

- Cache usage
- Dirty bytes
- Eviction
- Pages read
- Pages written
- Cache activity

Do not diagnose memory pressure from a single metric.

Correlate cache statistics with:

- Query latency
- Storage I/O
- CPU
- Page faults
- Working-set behavior
- Application traffic

## Cache Eviction

When cache capacity becomes constrained, WiredTiger may need to evict cached content.

Conceptually:

```text
New data needed
      ↓
Cache capacity constrained
      ↓
Eviction
      ↓
Other data removed
      ↓
Future access may require storage read
```

Heavy eviction activity combined with increasing storage I/O and latency can indicate memory pressure.

Eviction is not inherently bad. Caching systems are expected to evict data. The concern is sustained eviction pressure that materially affects workload performance.

## Dirty Data and Write Workloads

Write-heavy workloads introduce another memory dimension.

```text
Application writes
      ↓
MongoDB/WiredTiger
      ↓
Dirty cached data
      ↓
Flush/checkpoint
      ↓
Storage
```

Large sustained write workloads can create pressure related to:

- Dirty cache
- Storage throughput
- Checkpoint activity
- Journal activity
- Replication
- Disk latency

Memory sizing should therefore consider both reads and writes.

## Working Set and Write Performance

A write-heavy workload may not simply benefit from "more cache."

Consider:

```text
High write rate
+
Large documents
+
Large indexes
```

Every write may require updates to multiple indexes.

This increases:

- CPU work
- Memory activity
- Storage writes
- Cache pressure

Reducing unnecessary indexes can therefore improve write performance and memory behavior.

## Working Set and Over-Indexing

Suppose a collection has:

```text
Data        = 200 GB
Indexes     = 180 GB
```

The application may have excellent query coverage but pay a large memory and write-maintenance cost.

Every additional index should have a reason:

```text
Production query pattern
        ↓
Index requirement
        ↓
Performance validation
        ↓
Keep index
```

Do not create indexes simply because a field might be queried someday.

## Working Set and Sharding

In a sharded deployment, each shard has its own working set.

```text
                    Router
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
          Shard A   Shard B   Shard C
             │        │        │
          Working   Working   Working
           Set A     Set B     Set C
```

A good shard key distributes workload and storage.

A poor shard key can create:

```text
Hot shard
   ↓
Disproportionate working set
   ↓
Memory pressure
   ↓
Higher latency
```

Therefore shard-key design is also memory and cache-locality design.

## Multi-Tenant Systems

Multi-tenant applications often have skewed workloads.

Example:

```text
Tenant A → 50% of traffic
Tenant B → 10%
Tenant C → 5%
Remaining tenants → 35%
```

Tenant A's data may become disproportionately hot.

This can create:

- Uneven cache pressure
- Hot indexes
- Hot shards
- Hot documents

Measure workload distribution instead of assuming all tenants are equally active.

## Memory and Large Tenants

A large tenant can dominate the working set even if the overall system has many tenants.

Possible strategies include:

- Tenant-aware indexes
- Tenant-specific partitioning or sharding strategy
- Archiving
- Time-based collections where appropriate
- Caching
- Query limits
- Workload isolation

Avoid introducing architecture complexity without measured evidence.

## Working Set and Application Caching

Caching can reduce MongoDB working-set pressure.

Example:

```text
Request
  ↓
Redis
  ├── Hit → return
  │
  └── Miss
        ↓
     MongoDB
        ↓
     Redis
        ↓
     Response
```

However, caching introduces:

- Cache invalidation
- Staleness
- Memory cost
- Operational complexity
- Failure modes

Use caching when the access pattern justifies it.

## Working Set and Read Preference

Replica sets provide multiple nodes that may serve reads depending on the selected read preference.

Example:

```text
Application
    │
    ├── Primary
    │
    └── Secondary
```

Different members may develop different working sets depending on workload.

Read distribution should therefore be designed carefully.

Do not assume that adding read replicas automatically makes memory pressure disappear.

## Memory Pressure in Containers

Containerized MongoDB deployments require careful memory planning.

```text
Host
 ├── MongoDB container
 ├── Other containers
 └── OS overhead
```

Memory limits can affect MongoDB behavior significantly.

Avoid configuring a container's memory limit without understanding:

- MongoDB cache requirements
- OS/container behavior
- Filesystem cache
- Other processes
- Kubernetes resource requests
- Kubernetes memory limits

For production MongoDB, managed services or dedicated hosts often simplify capacity management.

## Kubernetes Memory Considerations

For Kubernetes-hosted MongoDB:

```text
Pod memory limit
      ↓
MongoDB available memory
      ↓
WiredTiger + filesystem/cache behavior
      ↓
Storage performance
```

Memory pressure can result in:

- Evictions
- Latency spikes
- OOM termination
- Restart loops
- Replica instability

MongoDB is stateful infrastructure and should not be operated like an ordinary stateless API pod without careful resource planning.

## AWS Considerations

For self-managed MongoDB on AWS, memory-sensitive workloads require instance selection based on:

- Available RAM
- CPU
- EBS throughput
- IOPS
- Network bandwidth
- Storage latency

For MongoDB Atlas, the selected cluster tier influences available compute, memory, and storage characteristics.

Do not choose an instance solely by total storage capacity.

A workload needing:

```text
100 GB storage
```

may require significantly more memory or I/O capacity depending on access patterns.

## Working Set and Storage Performance

A working set larger than memory is not necessarily a failure.

The system can remain healthy if storage is fast enough and access patterns are acceptable.

The architecture is:

```text
RAM
  ↓
Frequently used data
  ↓
Fast storage
  ↓
Less frequently used data
```

For workloads with frequent random reads, storage latency becomes much more important when the working set exceeds effective cache capacity.

## SSD vs Slow Storage

Storage characteristics matter more as cache misses increase.

```text
Cache hit
  ↓
Memory latency

Cache miss
  ↓
Storage latency
```

If storage is slow:

```text
Cache miss
    ↓
Long storage wait
    ↓
Query latency
    ↓
API p99 latency
```

Fast storage cannot replace good indexing, but it can reduce the penalty of cache misses.

## Memory vs CPU vs I/O

MongoDB performance should be treated as a system-level problem.

| Symptom | Potential bottleneck |
|---|---|
| High storage latency | Disk/I/O |
| High CPU | Query processing / concurrency |
| High cache pressure | Memory |
| High pool wait | Connection concurrency |
| High query execution time | Query/index design |
| High network throughput | Large documents/results |
| High replication lag | Primary workload or secondary capacity |

Do not automatically add RAM when CPU or storage is actually the bottleneck.

## Performance Diagnosis

A practical diagnosis flow is:

```text
Latency increase
      ↓
Measure application p95/p99
      ↓
Measure MongoDB query latency
      ↓
Check cache/WiredTiger metrics
      ↓
Check memory utilization
      ↓
Check storage latency/IOPS
      ↓
Check query plans
      ↓
Check working-set growth
      ↓
Check index size
      ↓
Identify bottleneck
      ↓
Optimize
      ↓
Benchmark
```

## Before and After Example

Suppose an API has:

```text
p95 latency = 180 ms
p99 latency = 700 ms
```

MongoDB query execution is:

```text
p95 = 15 ms
p99 = 25 ms
```

but storage latency is high and cache pressure is increasing.

Investigation reveals:

```text
Collection = 600 GB
Indexes    = 150 GB
Active data ≈ 100 GB
Available effective memory is insufficient
```

Possible optimization sequence:

```text
1. Remove unused indexes
2. Reduce document projections
3. Improve query selectivity
4. Add missing query-specific indexes
5. Archive cold historical data
6. Evaluate memory increase
7. Evaluate storage performance
8. Re-measure
```

The correct solution may be a combination rather than simply adding RAM.

## Working Set Optimization Strategies

### Reduce the Data Read

Use:

- Projection
- Selective filters
- Efficient pagination
- Covered queries
- Query-specific indexes

### Reduce the Data Stored

Use:

- Bounded arrays
- Archiving
- TTL where appropriate
- Historical-data lifecycle policies
- Smaller documents

### Reduce Query Frequency

Use:

- Redis caching
- Application-level caching
- Response caching
- Precomputed results
- Batch processing

### Reduce Query Cost

Use:

- Proper indexes
- Efficient aggregation
- Query-shape analysis
- Avoiding unnecessary `$lookup`
- Avoiding unbounded scans

### Improve Infrastructure

When software optimization is insufficient:

- Increase memory
- Improve storage performance
- Increase IOPS
- Scale reads appropriately
- Revisit sharding

Infrastructure scaling should follow measurement.

## Monitoring Strategy

Monitor the relationship between workload and resources.

### Application Metrics

Track:

- Request rate
- p50 latency
- p95 latency
- p99 latency
- MongoDB operation latency
- Cache hit rate
- Error rate
- Connection-pool wait time

### MongoDB Metrics

Track:

- Memory utilization
- WiredTiger cache behavior
- Eviction activity
- Storage latency
- IOPS
- Throughput
- Query execution time
- Collection growth
- Index growth
- Connections
- Replication lag
- CPU utilization

### Capacity Metrics

Track trends over time:

```text
Data growth
Index growth
Memory usage
Working-set growth
Query latency
Storage latency
Traffic growth
```

A database that is healthy today may become memory-bound after six months of data growth.

## Capacity Planning

A production capacity model should consider:

```text
Current workload
      +
Expected traffic growth
      +
Data growth
      +
Index growth
      +
Working-set growth
      +
Replication overhead
      +
Operational headroom
```

Example:

```text
Current active working set = 80 GB
Expected annual growth     = 40 GB
Operational headroom       = 30 GB

Planning target ≈ 150 GB+
```

This is only an illustrative model. Real sizing should be validated with workload measurements.

## Working Set and Disaster Recovery

Memory is transient.

A MongoDB restart does not mean the persistent data disappears, but the cache must become warm again.

After restart:

```text
MongoDB restart
      ↓
Cache initially cold
      ↓
Application traffic
      ↓
Storage reads
      ↓
Frequently used pages become hot
      ↓
Performance stabilizes
```

This is commonly called a **cold-cache** condition.

Production planning should therefore account for post-restart performance.

## Cold Cache After Failover

Replica-set failover can move application traffic to a node whose cache state differs from the old primary.

```text
Primary A
   ↓
Failure
   ↓
Primary B
   ↓
Application traffic
   ↓
Different cache state
   ↓
Temporary storage pressure
```

This can produce a latency increase after failover even when the new primary is healthy.

Monitor post-failover performance rather than evaluating only steady-state behavior.

## Warm-Up Strategies

Applications should generally avoid relying on a manual "load the entire database into RAM" process.

Instead:

- Use representative traffic
- Maintain appropriate indexes
- Keep frequently used data compact
- Use controlled warm-up queries only where justified
- Monitor cache recovery after restart

Be cautious with aggressive warm-up jobs because they can compete with real production traffic.

## Common Mistakes

### Assuming the Entire Database Must Fit in RAM

**Problem:** Database size and working-set size are different.

**Fix:** Measure actual access patterns, hot data, index size, and cache behavior.

### Ignoring Index Memory

**Problem:** Large indexes can consume significant memory and affect cache efficiency.

**Fix:** Measure index sizes and remove indexes that do not support real workloads.

### Treating More RAM as the Universal Fix

**Problem:** CPU, storage, query design, or connection concurrency may be the real bottleneck.

**Fix:** Correlate memory metrics with query latency, CPU, and storage metrics.

### Storing Unbounded Arrays

**Problem:** Documents grow continuously and become expensive to read and update.

**Fix:** Use bounded arrays or separate collections for unbounded child data.

### Returning Entire Documents

**Problem:** Large payloads increase memory, network, and application processing costs.

**Fix:** Use projection and return only required fields.

### Using Large `skip()` Values

**Problem:** Large offsets can require substantial work.

**Fix:** Prefer cursor-based pagination for large collections.

### Ignoring Working-Set Skew

**Problem:** A small number of tenants, products, or documents may dominate traffic.

**Fix:** Measure workload distribution and identify hot data.

### Ignoring Cold-Cache Behavior

**Problem:** Performance after restart or failover may be substantially worse temporarily.

**Fix:** Test restart/failover scenarios and monitor cache warm-up.

### Ignoring Historical Data

**Problem:** Old data can increase storage and index size even when rarely queried.

**Fix:** Implement appropriate archival or lifecycle strategies.

### Creating Too Many Indexes

**Problem:** Indexes increase storage, memory pressure, and write overhead.

**Fix:** Create indexes from measured query patterns.

## Production Pitfalls

| Pitfall | Impact | Better approach |
|---|---|---|
| Large unbounded documents | Memory and I/O pressure | Bound document growth |
| Huge indexes | Cache pressure | Review index usage |
| Full-document reads | Network and memory overhead | Use projection |
| Random scans | Poor locality | Improve query/index design |
| Large offset pagination | Increasing query cost | Cursor pagination |
| Unbounded aggregation | Large intermediate state | Filter early |
| Excessive caching | Memory and consistency complexity | Cache measured hot paths |
| Ignoring tenant skew | Hot data/shards | Measure workload distribution |
| No capacity trend monitoring | Unexpected saturation | Track growth over time |
| Testing only warm cache | Production surprises after restart | Test cold-cache behavior |

## Security Considerations

Memory optimization must not weaken security.

Do not:

- Cache sensitive data without appropriate controls.
- Log complete documents merely for performance debugging.
- Copy credentials into diagnostic scripts.
- Expose database statistics publicly.
- Disable authorization to simplify profiling.

When profiling production workloads:

- Minimize sensitive data exposure.
- Restrict diagnostic access.
- Use sanitized datasets for load tests.
- Follow organizational data-retention requirements.

## Reliability Considerations

A memory-optimized system should remain stable during:

- Traffic spikes
- MongoDB restarts
- Replica-set elections
- Failovers
- Cache warm-up
- Data growth
- Index builds
- Background workloads

A good performance design is not merely fast under ideal conditions.

It should degrade predictably under pressure.

## Interview Traps

### "MongoDB requires the entire database to fit in RAM."

Incorrect.

The important concept is the active working set and the behavior of the storage/cache hierarchy.

### "More RAM always makes MongoDB faster."

Not necessarily.

The bottleneck may be:

- Query design
- Indexes
- CPU
- Storage
- Network
- Connection concurrency

### "Indexes only consume disk."

Incorrect.

Indexes require memory/cache resources and also add write-maintenance overhead.

### "A small result set means a query is cheap."

Not necessarily.

A query returning 10 documents may scan a large amount of data before producing those 10 documents.

Use `explain("executionStats")` to inspect actual work.

### "Adding Redis fixes MongoDB memory pressure."

Not automatically.

Redis can reduce repeated MongoDB reads, but it introduces another cache with its own memory and consistency characteristics.

### "After a MongoDB restart, performance should immediately return to normal."

Not necessarily.

The cache may initially be cold and need to warm based on real workload.

## Senior-Level Performance Checklist

Before changing infrastructure, verify:

### Data

- Is the working set growing?
- Are documents larger than necessary?
- Are arrays bounded?
- Is historical data still active?

### Indexes

- Which indexes are actually used?
- How large are the indexes?
- Are queries selective?
- Are there redundant indexes?

### Queries

- Are filters selective?
- Are queries covered where appropriate?
- Is projection used?
- Is pagination efficient?
- Are aggregation stages reducing data early?

### Infrastructure

- Is memory sufficient?
- Is storage latency acceptable?
- Is CPU saturated?
- Is network bandwidth sufficient?

### Workload

- Is traffic growing?
- Is there tenant skew?
- Are there hot documents?
- Are batch workloads competing with APIs?

### Reliability

- Has cold-cache behavior been tested?
- Has failover behavior been tested?
- Is post-restart performance acceptable?
- Is there sufficient capacity headroom?

## Practical Diagnostic Commands

Inspect collection statistics:

```javascript
db.orders.stats()
```

Inspect indexes:

```javascript
db.orders.getIndexes()
```

Inspect index sizes:

```javascript
db.orders.stats().indexSizes
```

Inspect server statistics:

```javascript
db.serverStatus()
```

Inspect WiredTiger cache information:

```javascript
db.serverStatus().wiredTiger.cache
```

Inspect a query plan:

```javascript
db.orders.find({
    tenant_id: "tenant-42",
    status: "pending"
}).explain("executionStats")
```

Inspect database statistics:

```javascript
db.stats()
```

These commands are diagnostic tools, not substitutes for continuous production monitoring.

## Troubleshooting Methodology

```text
Symptom
↓
Latency or throughput degradation
↓
Possible causes
↓
Memory pressure / large working set / large indexes / storage latency / inefficient queries
↓
Isolation strategy
↓
Separate application latency from MongoDB execution latency
↓
Diagnostic commands
↓
db.stats() / db.collection.stats() / db.serverStatus() / explain()
↓
Root cause
↓
Identify cache, query, index, storage, or workload bottleneck
↓
Corrective action
↓
Optimize data model, query, indexes, memory, storage, or workload
↓
Prevention
↓
Capacity monitoring + load testing + growth forecasting
```

## Key Takeaways

- **MongoDB performance depends on the active working set, not simply the total size of the database; frequently accessed documents and indexes should have efficient access to memory.**
- **Indexes are part of the performance-critical working set, so index size, selectivity, document size, and query patterns must be analyzed together.**
- **Reduce memory and I/O pressure through efficient data modeling, selective queries, projection, appropriate indexes, cursor pagination, bounded documents, and lifecycle management for cold data.**
- **Diagnose memory pressure alongside CPU, storage latency, query execution, connection concurrency, and workload skew rather than treating RAM as the universal performance solution.**
- **Production capacity planning must account for working-set growth, index growth, cold-cache behavior, failover, traffic growth, and sufficient operational headroom.**