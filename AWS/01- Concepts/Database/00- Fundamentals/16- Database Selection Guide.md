# Database Selection Guide for AWS

Choosing the wrong database is one of the most expensive mistakes in system design. It is rarely a problem on day one — it surfaces at scale, when migration costs are highest. This guide provides a structured framework for selecting the right AWS database service based on workload characteristics, not vendor marketing.

---

## Decision Framework

The right database depends on the access pattern, not the data. Start with these questions:

1. **What is the query pattern?** — Complex joins and aggregations, or simple key lookups?
2. **What is the consistency requirement?** — Strong consistency, or eventual is acceptable?
3. **What is the scale trajectory?** — Predictable steady growth, or unpredictable spiky traffic?
4. **What is the data relationship complexity?** — Flat records, hierarchical documents, or dense graphs?
5. **Is this OLTP or OLAP?** — Serving live user requests, or running analytical queries?

---

## Decision Tree

```
                        What is your primary workload?
                                    │
            ┌───────────┬───────────┼───────────┬──────────────┐
            ▼           ▼           ▼           ▼              ▼
       Relational    Key-Value   Analytical   Specialized    Caching
        (OLTP)       / Document   (OLAP)      Workload
            │           │           │           │              │
            ▼           ▼           ▼           │              ▼
    Need managed    Access by     Data         │        ElastiCache
    MySQL/Postgres? primary key?  warehouse?   │        (Redis/Memcached)
      │       │       │              │         │
      ▼       ▼       ▼              ▼         ├── Graph relationships?
   Aurora    RDS   DynamoDB      Redshift      │       → Neptune
                                               │
                                               ├── Time-series IoT/metrics?
                                               │       → Timestream
                                               │
                                               ├── Immutable audit ledger?
                                               │       → QLDB
                                               │
                                               └── MongoDB-compatible docs?
                                                       → DocumentDB
```

**Aurora vs RDS**: Default to Aurora unless you need a specific engine that Aurora does not support (e.g., Oracle, SQL Server). Aurora provides 5x MySQL and 3x PostgreSQL throughput, automatic storage scaling, and faster failover.

**DynamoDB vs DocumentDB**: DynamoDB is for high-throughput key-value and simple document access. DocumentDB is for complex document queries with MongoDB-compatible aggregation pipelines. If your queries are by primary key or a known set of indexes, DynamoDB wins. If you need ad-hoc queries across nested document fields, consider DocumentDB.

---

## Service Comparison

| Service | Engine | Scaling Model | Consistency | Max Throughput | Pricing Model |
|---------|--------|---------------|-------------|----------------|---------------|
| **Aurora** | MySQL, PostgreSQL | Vertical + read replicas (up to 15) | Strong (primary), eventual (replicas) | 200K writes/s, 1M reads/s | Instance-hour + I/O + storage |
| **RDS** | MySQL, PostgreSQL, Oracle, SQL Server, MariaDB | Vertical + read replicas (up to 15) | Strong (primary), eventual (replicas) | Instance-dependent | Instance-hour + storage + I/O |
| **DynamoDB** | Proprietary (key-value/document) | Horizontal (automatic, unlimited) | Strong or eventual (per-request) | Virtually unlimited (partitioned) | On-demand (per request) or provisioned (capacity units) |
| **DocumentDB** | MongoDB-compatible | Vertical + read replicas (up to 15) | Strong (primary), eventual (replicas) | Instance-dependent | Instance-hour + I/O + storage |
| **Neptune** | Property graph + RDF (Gremlin, SPARQL, openCypher) | Vertical + read replicas (up to 15) | Strong (primary), eventual (replicas) | Instance-dependent | Instance-hour + I/O + storage |
| **Timestream** | Proprietary (time-series) | Serverless (automatic) | Eventual | Millions of data points/s | Pay per write, storage, query |
| **QLDB** | Proprietary (ledger) | Serverless (automatic) | Strong (serializable) | ~30K transactions/s | Pay per I/O + storage + data transfer |
| **Redshift** | PostgreSQL-based (columnar) | Horizontal (node-based clusters) | Strong within cluster | Petabyte-scale analytics | Node-hour + storage (or Serverless per RPU-hour) |
| **ElastiCache** | Redis, Memcached | Vertical + sharding (Redis cluster) | Eventual (replication), strong (single node) | Millions of ops/s | Node-hour |

---

## Polyglot Persistence

Production systems rarely use a single database. Different data has different access patterns, and forcing everything into one engine creates performance bottlenecks and scaling pain.

**Polyglot persistence** means using the right database for each workload within the same system.

```
                    ┌─────────────────────────────┐
                    │     Application Services     │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              ▼                   ▼                    ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Aurora (RDS)   │ │    DynamoDB      │ │   ElastiCache   │
    │                  │ │                  │ │    (Redis)       │
    │ - User accounts  │ │ - Session data   │ │ - Hot query      │
    │ - Orders         │ │ - Shopping carts  │ │   results cache  │
    │ - Inventory      │ │ - Activity feeds  │ │ - Rate limiting  │
    │ - Financial txns │ │ - Event tracking  │ │ - Leaderboards   │
    │                  │ │ - Feature flags   │ │                  │
    │ ACID, complex    │ │ Single-digit ms   │ │ Sub-ms latency   │
    │ queries, joins   │ │ at any scale      │ │ ephemeral data   │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Rules for polyglot persistence:**

- Each service owns its data — no shared databases across services
- Use events or APIs for cross-database data synchronization
- Accept that cross-database transactions are not atomic — design for eventual consistency
- Centralize observability: every database must emit metrics to the same monitoring system

---

## Real-World Architecture: E-Commerce Platform

A mid-scale e-commerce platform (100K daily active users, 5K orders/day) using three databases:

```
                           ┌─────────────┐
                           │   Route 53   │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │     ALB      │
                           └──────┬──────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼              ▼
             ┌───────────┐ ┌──────────┐  ┌────────────┐
             │  Product  │ │  Order   │  │   User     │
             │  Service  │ │  Service │  │  Service   │
             └─────┬─────┘ └────┬─────┘  └─────┬──────┘
                   │            │               │
         ┌────────┘     ┌──────┘               │
         ▼              ▼                      ▼
  ┌────────────┐  ┌───────────┐         ┌───────────┐
  │ ElastiCache│  │  Aurora    │         │ DynamoDB  │
  │  (Redis)   │  │ PostgreSQL│         │           │
  │            │  │           │         │ - Profiles │
  │ - Product  │  │ - Orders  │         │ - Sessions │
  │   catalog  │  │ - Payment │         │ - Prefs    │
  │   cache    │  │ - Inventory│        │ - Cart     │
  │ - Session  │  │           │         │            │
  │   store    │  │ ACID for  │         │ Low-latency│
  │            │  │ financial │         │ key-value  │
  └────────────┘  └───────────┘         └───────────┘
```

**Why this combination works:**

- **Aurora PostgreSQL** handles orders, payments, and inventory — these require ACID transactions, complex joins (order + line items + payment + shipping), and strong consistency. Financial data demands relational integrity.
- **DynamoDB** handles user profiles, sessions, shopping carts, and preferences — these are accessed by a single key (user ID), change frequently, and must respond in single-digit milliseconds. No joins required.
- **ElastiCache (Redis)** caches product catalog queries and stores ephemeral session tokens — sub-millisecond reads reduce load on Aurora and DynamoDB. Cache invalidation fires on product catalog updates via SNS.

---

## Common Mistakes

1. **Using RDS for everything.** Relational databases handle 80% of workloads acceptably. They handle the remaining 20% terribly. High-velocity event streams, session stores, and caching patterns are painful in SQL.
2. **Choosing DynamoDB without understanding access patterns.** DynamoDB is exceptional when you know your queries upfront. It is miserable when you need ad-hoc analytics, complex filters, or retroactive index changes on large tables.
3. **Adding a cache before optimizing the database.** Caching hides bad queries. Fix slow queries first, then add caching for genuinely hot paths. A cache in front of a broken query is a ticking time bomb.
4. **Ignoring total cost of ownership.** DynamoDB on-demand pricing looks cheap at 100 requests/second. At 50,000 requests/second, provisioned capacity with reserved pricing is 10x cheaper.
5. **Skipping proof-of-concept testing.** Never select a database based on documentation alone. Build a realistic load test with production-like data volumes and access patterns before committing.

---

## Interview Questions

**Q1: Your team stores user orders in DynamoDB with user_id as partition key and order_id as sort key. Product management now wants a report of all orders placed in the last 24 hours across all users. How do you handle this?**

A full table scan filtered by timestamp is expensive and slow on DynamoDB. The correct approach is to create a Global Secondary Index (GSI) with a time-based partition key (e.g., order_date) and order_id as sort key. Alternatively, stream order events to Redshift or S3 via DynamoDB Streams + Kinesis for analytical queries — keep DynamoDB for OLTP and use a proper analytics engine for OLAP.

**Q2: You are building a social media feed. Each user follows hundreds of other users, and the feed must show the latest 50 posts from all followed users, sorted by timestamp. Which AWS database(s) would you use and why?**

Use DynamoDB for storing posts (partition key: user_id, sort key: timestamp) and a fan-out-on-write pattern where new posts are written to each follower's feed timeline (a separate DynamoDB table with partition key: follower_id, sort key: timestamp). Use ElastiCache (Redis) sorted sets for the hot feed cache of active users. For celebrity accounts with millions of followers, use a fan-out-on-read approach to avoid write amplification.

**Q3: Your Aurora PostgreSQL cluster handles 10K transactions/second during business hours. Overnight batch analytics jobs run complex aggregation queries that degrade OLTP performance. What is your recommended architecture change?**

Offload analytics to Redshift. Use Aurora zero-ETL integration with Redshift to replicate data in near-real-time without building ETL pipelines. Alternatively, use Aurora read replicas dedicated to analytics queries — but this still shares Aurora I/O credits. Redshift's columnar storage is purpose-built for aggregation queries and will outperform Aurora by 10-100x on analytical workloads.

**Q4: When would you choose DocumentDB over DynamoDB for a document workload?**

Choose DocumentDB when you need MongoDB-compatible query syntax, rich aggregation pipelines across nested document fields, ad-hoc queries without predefined indexes, or are migrating an existing MongoDB application. Choose DynamoDB when access patterns are well-defined, you need unlimited horizontal scale, single-digit millisecond latency at any volume, and your queries use primary key or GSI lookups.

---

## Key Takeaways

- **Start with the access pattern, not the data model.** The way you query data determines the right database — not the shape of the data itself.
- **Default to Aurora for relational OLTP, DynamoDB for key-value/document, and Redshift for analytics.** These three cover 90% of production workloads on AWS.
- **Polyglot persistence is the norm in production.** Using multiple databases is not over-engineering — it is matching each workload to the engine optimized for it.
- **DynamoDB requires upfront access pattern design.** It rewards careful planning and punishes ad-hoc query requirements. Model your queries before modeling your tables.
- **Always run a proof-of-concept with realistic data.** Benchmarks in documentation do not reflect your workload. Test with production-scale data volumes and concurrent access patterns.
- **Total cost of ownership includes operational complexity.** A managed serverless database at 2x the compute cost may be cheaper than a self-managed instance when you factor in engineering time for patching, scaling, and monitoring.
