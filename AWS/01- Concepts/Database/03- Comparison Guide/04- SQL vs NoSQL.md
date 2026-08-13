# SQL vs NoSQL

Two fundamentally different philosophies for storing and retrieving data. SQL databases are **model-first** — you design the schema, then write queries. NoSQL databases are **query-first** — you design around access patterns, then model the data to serve them. Picking wrong costs you a rewrite. Picking right saves you years of scaling pain.

---

## Data Modeling Philosophy

**SQL (Model-First)**
You normalize data into tables with strict relationships. Third normal form is the goal. You trust the query optimizer to figure out how to JOIN things efficiently at read time. The schema enforces correctness — the database is the source of truth for data integrity.

**NoSQL (Query-First)**
You start with your access patterns and denormalize aggressively. Data duplication is expected. You pre-compute answers into the structure itself. There is no query optimizer saving you — if you didn't model for the query, it's a full table scan or a redesign.

```
SQL Approach:
  Requirements → Entity Relationships → Normalize → Schema → Queries

NoSQL Approach:
  Requirements → Access Patterns → Denormalize → Schema → Queries
```

---

## Schema, Transactions, Scaling, JOINs

**Schema Rigidity**
SQL enforces schema-on-write. Every row in a table has the same columns. Migrations are required for changes — `ALTER TABLE` on a billion-row table is an operational event. NoSQL uses schema-on-read. Each item can have different attributes. You shift validation to the application layer.

**Transaction Guarantees**
SQL gives you full ACID transactions out of the box. Multi-row, multi-table operations with rollback. NoSQL varies — DynamoDB offers `TransactWriteItems` for up to 100 items across tables, but it's not the default path. Most NoSQL operations are single-item atomic by default.

**Scaling Patterns**
SQL scales vertically first. You buy bigger instances. Read replicas help with read-heavy workloads, but writes hit a single primary. Aurora pushes this further with up to 15 read replicas and storage auto-scaling to 128 TiB. NoSQL scales horizontally by design. DynamoDB partitions data automatically across nodes. You go from 10 RCU to 10 million RCU without architectural changes.

**JOIN Support**
SQL supports JOINs natively — INNER, LEFT, RIGHT, CROSS, SELF. The optimizer handles execution plans. NoSQL has no JOINs. You either denormalize data into single items, use composite keys to co-locate related data, or handle joins in application code.

---

## AWS Service Mapping

| Category | SQL Services | NoSQL Services |
|----------|-------------|----------------|
| Relational | RDS (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server), Aurora | — |
| Key-Value | — | DynamoDB |
| Document | — | DocumentDB (MongoDB-compatible) |
| Wide-Column | — | Keyspaces (Cassandra-compatible) |
| Graph | — | Neptune |
| In-Memory | ElastiCache (Redis/Valkey) | ElastiCache (Redis/Valkey) |
| Time-Series | Timestream | Timestream |
| Ledger | QLDB | — |

Aurora sits at the boundary — it's relational SQL with cloud-native storage that behaves more like a distributed system under the hood. DocumentDB is MongoDB wire-compatible but not open-source MongoDB — know this for interviews and migrations.

---

## Polyglot Persistence Pattern

Real production systems rarely use one database. You use the right engine for each access pattern.

```
┌─────────────────────────────────────────────────────┐
│                   Application Layer                 │
├──────────┬──────────┬───────────┬──────────┬────────┤
│  Aurora  │ DynamoDB │  Neptune  │  Redis   │  S3    │
│ (Orders) │ (Sessions│ (Social   │ (Cache)  │(Media) │
│          │  Carts)  │  Graph)   │          │        │
└──────────┴──────────┴───────────┴──────────┴────────┘

Each service handles what it's best at:
- Aurora:    Complex queries, transactions, reporting
- DynamoDB:  Sub-ms key lookups, session state, high throughput
- Neptune:   Relationship traversal, recommendation engines
- Redis:     Hot data caching, leaderboards, pub/sub
- S3:        Binary objects, backups, data lake
```

The cost is operational complexity — more engines means more monitoring, more failure modes, more team expertise required. Don't adopt polyglot persistence until you've proven a single engine can't meet your access pattern needs.

---

## Decision Tree

```
Start: What are your primary requirements?
  │
  ├── Complex queries, JOINs, reporting?
  │     → SQL (Aurora/RDS)
  │
  ├── Sub-millisecond latency at any scale?
  │     → DynamoDB (with DAX if needed)
  │
  ├── Flexible document schema, MongoDB workloads?
  │     → DocumentDB
  │
  ├── Relationship traversal, graph queries?
  │     → Neptune
  │
  ├── Wide-column, Cassandra migration?
  │     → Keyspaces
  │
  └── Unknown or evolving access patterns?
        → Start with SQL (Aurora PostgreSQL)
        → Easier to refactor later
```

When in doubt, start relational. SQL databases are more forgiving of access pattern changes because the query optimizer adapts. NoSQL databases punish you for not knowing your patterns upfront.

---

## Detailed Comparison Table

| Dimension | SQL (RDS/Aurora) | NoSQL (DynamoDB) |
|-----------|-----------------|------------------|
| Data Model | Tables, rows, columns | Items, attributes, key-value |
| Schema | Strict, schema-on-write | Flexible, schema-on-read |
| Query Language | SQL (SELECT, JOIN, subqueries) | PartiQL, GetItem, Query, Scan |
| Transactions | Full ACID, multi-table | TransactWriteItems (25 items) |
| Scaling | Vertical + read replicas | Horizontal, automatic partitioning |
| Max Storage | Aurora: 128 TiB | Unlimited |
| Latency | Single-digit ms (typical) | Single-digit ms (consistent) |
| JOINs | Native, optimized | Not supported |
| Consistency | Strong by default | Eventually consistent default, strong optional |
| Pricing | Instance-based (hourly) | On-demand or provisioned (RCU/WCU) |
| Backup | Automated snapshots, PITR | Continuous backups, PITR |
| Global | Aurora Global Database | DynamoDB Global Tables |
| Connection Model | Connection-based (pooling needed) | HTTP API (no connection limits) |
| Indexing | B-tree, hash, GIN, GiST | GSI, LSI (max 20 GSIs) |

---

## When SQL Wins

- Complex reporting with ad-hoc queries across multiple dimensions
- Financial systems requiring strict ACID transactions across entities
- Workloads where access patterns change frequently or are unknown at design time
- Teams with deep SQL expertise and existing relational schemas
- Data with heavy relationships and frequent multi-table operations

## When NoSQL Wins

- Consistent single-digit millisecond latency at any throughput level
- Massive write throughput (millions of writes/sec with on-demand)
- Simple key-value or document access patterns that are well-defined
- Serverless architectures where connection pooling is impractical
- IoT, gaming, mobile backends with unpredictable traffic spikes

## When You Need Both

- E-commerce: Aurora for orders/inventory + DynamoDB for sessions/carts
- Social platforms: Aurora for user profiles + Neptune for social graph + DynamoDB for activity feeds
- SaaS: Aurora for tenant configuration + DynamoDB for high-throughput event ingestion

---

## Interview-Ready Explanation

> "SQL databases are model-first — you normalize data and let the query optimizer handle access patterns. NoSQL databases are query-first — you design the schema around specific access patterns and accept denormalization. On AWS, Aurora gives you relational power with cloud-native scaling up to 128 TiB and 15 read replicas. DynamoDB gives you consistent single-digit millisecond latency at any scale with automatic partitioning. In practice, most production systems use polyglot persistence — Aurora for complex queries and transactions, DynamoDB for high-throughput key lookups, and ElastiCache for hot data. The decision comes down to whether your access patterns are known and simple (NoSQL) or complex and evolving (SQL)."

---

## Key Takeaways

1. **Model-first vs query-first** is the fundamental divide — SQL adapts to new queries, NoSQL requires you to know them upfront
2. **Aurora** is the go-to SQL choice on AWS — cloud-native storage, up to 15 replicas, Global Database for cross-region
3. **DynamoDB** is the go-to NoSQL choice — serverless, automatic scaling, single-digit ms latency guaranteed
4. **Polyglot persistence** is the production reality — use each engine for what it does best
5. **Start relational when uncertain** — it's cheaper to add a NoSQL layer later than to retrofit JOINs onto DynamoDB
6. **Connection model matters** — RDS needs connection pooling (RDS Proxy), DynamoDB uses HTTP APIs with no connection limits
7. **Cost model differs** — RDS charges per instance-hour, DynamoDB charges per request or provisioned capacity
