# Scalability Patterns — Database Scaling

Compute scales horizontally in a fairly straightforward way; databases are the harder problem, since data has to live somewhere consistent.

## Read Replicas

Copies of the primary database that serve read-only traffic, replicated asynchronously (typically) from the primary.

```text
Writes → Primary DB
Reads → Read Replica(s)
```

**Trade-off:** scales read capacity well (common for read-heavy workloads), but replication lag means replicas can serve slightly stale data — an application that writes then immediately reads its own write may not see it yet if that read hits a lagging replica.

## Connection Pooling

Databases have a hard limit on concurrent connections. In a horizontally-scaled application, every instance opening its own direct connection pool can exhaust that limit quickly. A connection pooler (e.g., RDS Proxy) sits between the application fleet and the database, multiplexing many application-side connections onto a smaller number of actual database connections.

**Why this matters more with serverless:** Lambda functions that each open a direct database connection can very quickly exhaust a database's connection limit under concurrent load, since Lambda can scale to many concurrent executions almost instantly. RDS Proxy exists largely to solve this specific problem.

## Sharding (Horizontal Partitioning)

Splitting a dataset across multiple database instances based on a shard key (e.g., customer ID range, geographic region), so no single database instance holds the entire dataset.

**Trade-off:** enables write scaling beyond what a single instance can handle, but cross-shard queries (joining data that lives on different shards) become significantly harder, and rebalancing shards as data grows unevenly is a real operational undertaking.

## Read/Write Splitting at the Application Layer

Explicitly routing write queries to the primary and read queries to replicas within application code (or via a proxy) — a prerequisite for actually benefiting from read replicas, since simply having replicas doesn't route traffic to them automatically.

## NoSQL as a Scaling Strategy

DynamoDB and similar NoSQL databases are designed to scale horizontally by default via partitioning, trading relational query flexibility (joins, ad hoc queries) for predictable, near-constant-time performance at scale — a deliberate architectural choice, not just "a different kind of database."

## Senior-Level Considerations

- Read replica lag is often invisible until a specific bug ("I just saved this and it's not there") makes it visible — session-consistency requirements (read-your-own-writes) sometimes require deliberately routing certain reads to the primary
- Sharding is a one-way architectural door in practice — un-sharding a dataset later is far more painful than sharding it from the start when growth is genuinely anticipated, but premature sharding adds real complexity for data that may never need it
- Connection pooling issues often masquerade as "the database is slow" when the actual bottleneck is connection exhaustion, not query performance — worth checking early in a performance investigation
