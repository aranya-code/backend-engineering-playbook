# Amazon DynamoDB

A comprehensive, senior-level reference covering every aspect of Amazon DynamoDB — from core concepts and internal architecture to production data modeling, performance tuning, security hardening, AWS integration patterns, and hands-on Python SDK usage.

---

## Why DynamoDB?

DynamoDB is AWS's fully managed NoSQL database delivering **single-digit millisecond latency at any scale**. It eliminates operational overhead (no patching, no capacity planning, no replication management) while providing built-in high availability across three AZs, automatic scaling, encryption at rest, point-in-time recovery, and global replication.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        DynamoDB Architecture                        │
│                                                                     │
│   Client Request                                                    │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐    ┌──────────────┐    ┌─────────────────────────┐  │
│   │  Request  │───▶│   Router /   │───▶│   Storage Nodes         │  │
│   │  Router   │    │  Partition   │    │   (3 replicas per       │  │
│   │           │    │  Map         │    │    partition across     │  │
│   └──────────┘    └──────────────┘    │    3 Availability Zones)│  │
│                                       └─────────────────────────┘  │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Each partition:  10 GB data  │  3,000 RCU  │  1,000 WCU    │  │
│   │  Auto-splits when limits exceeded                            │  │
│   └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**When DynamoDB is the right choice:**
- Predictable, single-digit millisecond latency at any scale
- Key-value or document access patterns (known at design time)
- Serverless or event-driven architectures with Lambda
- Applications requiring 99.999% availability (Global Tables)
- High write throughput (IoT telemetry, gaming leaderboards, session stores)

**When DynamoDB is NOT the right choice:**
- Ad-hoc analytical queries across the entire dataset → use Redshift / Athena
- Complex multi-table JOINs and transactions spanning dozens of items → use RDS / Aurora
- Full-text search → use OpenSearch
- Graph traversal queries → use Neptune

---

## Module Index

This knowledge base contains **151 files** across **10 modules**, organized as a progressive learning path from fundamentals to production mastery.

| # | Module | Files | Focus |
|---|--------|-------|-------|
| 01 | [Concepts](./01-%20Concepts/) | 25 | Core architecture, data model, partitioning, consistency, capacity, CRUD, streams, TTL, transactions, global tables, security, PITR, architecture deep dive |
| 02 | [Data Modelling](./02-%20Data%20Modelling/) | 16 | Access-pattern-first design, single-table design, relationship patterns (1:1, 1:N, M:N), adjacency lists, sparse indexes, time-series, multi-tenant, write sharding, event sourcing |
| 03 | [Indexes](./03-%20Indexes/) | 13 | GSI vs LSI internals, sparse indexes, composite index design, projection types, index capacity/cost, optimization, anti-patterns |
| 04 | [Querying & Data Access](./04%20-%20Querying%20%26%20Data%20Access/) | 19 | Query vs Scan, expressions (key condition, filter, projection, condition), pagination, batch operations, transactions, conditional writes, atomic counters, optimistic locking, error handling |
| 05 | [Advanced Features](./05-%20Advanced%20Features/) | 13 | Streams, TTL, DAX, Global Tables, PITR, backup/restore, S3 export/import, PartiQL, design patterns for TTL/Streams/Global Tables |
| 06 | [Security](./06-%20Security/) | 7 | IAM authentication, fine-grained access control (FGAC), KMS encryption, VPC endpoints, CloudTrail/CloudWatch auditing, compliance |
| 07 | [Monitoring & Performance](./07-%20Monitoring%20%26%20Performance/) | 9 | Capacity modes, RCU/WCU deep dive, auto scaling, hot partitions, adaptive capacity, CloudWatch monitoring, performance troubleshooting, cost optimization |
| 08 | [Integration Patterns](./08-%20Integration%20Patterns/) | 10 | Lambda, SQS, SNS, EventBridge, Step Functions, API Gateway, Kinesis, CQRS, event-driven microservices |
| 09 | [Python SDK](./09-%20Python%20SDK/) | 18 | Boto3 fundamentals, CRUD, queries, batch ops, transactions, pagination, error handling, async with aioboto3, production repository layer, unit testing, DynamoDB Local |
| 10 | [Interview Questions](./10-%20Interview%20Questions/) | 11 | Fundamentals, data modeling, indexes, performance, transactions, advanced features, security, production scenarios, system design, Boto3 coding, mock senior interview |

---

## Learning Path

```text
                    ┌──────────────────────┐
                    │  01- Concepts        │  Start here
                    │  (Fundamentals)      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  02- Data Modelling  │  Design your schema
                    │  (Access Patterns)   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  03- Indexes         │  Optimize access
                    │  (GSI, LSI)          │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  04- Querying &      │  Read/Write mastery
                    │  Data Access         │
                    └──────────┬───────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
    ┌──────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────────┐
    │ 05- Advanced    │ │ 06- Security│ │ 07- Monitoring & │
    │ Features        │ │             │ │ Performance      │
    └──────────┬──────┘ └──────┬──────┘ └──────┬──────────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  08- Integration     │  Connect with AWS
                    │  Patterns            │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  09- Python SDK      │  Hands-on code
                    │  (Boto3 / aioboto3)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  10- Interview       │  Validate knowledge
                    │  Questions           │
                    └──────────────────────┘
```

---

## Module Breakdown

### 01 — Concepts (25 files)

The foundational module covering DynamoDB from first principles to architecture internals.

| # | File | Topic |
|---|------|-------|
| 01 | [Introduction](./01-%20Concepts/01-%20Introduction.md) | What DynamoDB is, architecture overview, use cases |
| 02 | [NoSQL Fundamentals](./01-%20Concepts/02-%20NoSQL%20Fundamentals.md) | CAP theorem, eventual consistency, key-value vs document |
| 03 | [Tables, Items and Attributes](./01-%20Concepts/03-%20Tables,%20Items%20and%20Attributes.md) | Core data model building blocks |
| 04 | [Data Types](./01-%20Concepts/04-%20Data%20Types.md) | Scalar, document, and set types |
| 05 | [Primary Keys](./01-%20Concepts/05-%20Primary%20Keys.md) | Simple vs composite primary keys |
| 06 | [Partition Keys and Sort Keys](./01-%20Concepts/06-%20Partition%20Keys%20and%20Sort%20Keys.md) | Key design and query patterns |
| 07 | [Partitions and Data Distribution](./01-%20Concepts/07-%20Partitions%20and%20Data%20Distribution.md) | Partition splitting, data distribution internals |
| 08 | [Read Consistency Models](./01-%20Concepts/08-%20Read%20Consistency%20Models.md) | Strong vs eventual consistency |
| 09 | [RCU and WCU](./01-%20Concepts/09-%20Read%20Capacity%20Units%20(RCU)%20and%20Write%20Capacity%20Units%20(WCU).md) | Throughput measurement and calculation |
| 10 | [Capacity Modes](./01-%20Concepts/10-%20Capacity%20Modes.md) | Provisioned vs On-Demand |
| 11 | [CRUD Operations](./01-%20Concepts/11-%20CRUD%20Operations.md) | PutItem, GetItem, UpdateItem, DeleteItem |
| 12 | [Adaptive Capacity](./01-%20Concepts/12-%20Adaptive%20Capacity.md) | Automatic throughput balancing |
| 13 | [Hot Partitions](./01-%20Concepts/13-%20Hot%20Partitions.md) | Causes, impact, and prevention |
| 14 | [Auto Scaling](./01-%20Concepts/14-%20Auto%20Scaling.md) | Target tracking policies |
| 15 | [DAX](./01-%20Concepts/15-%20DynamoDB%20Accelerator%20(DAX).md) | In-memory caching layer |
| 16 | [Streams](./01-%20Concepts/16-%20Streams.md) | Change data capture |
| 17 | [TTL](./01-%20Concepts/17-%20Time%20To%20Live%20(TTL).md) | Automatic item expiration |
| 18 | [Transactions](./01-%20Concepts/18-%20Transactions.md) | ACID transactions |
| 19 | [Global Tables](./01-%20Concepts/19-%20Global%20Tables.md) | Multi-region replication |
| 20 | [PartiQL](./01-%20Concepts/20-%20PartiQL.md) | SQL-compatible query language |
| 21 | [Backup, Restore and Export](./01-%20Concepts/21-%20Backup,%20Restore%20and%20Export.md) | DR strategies |
| 22 | [Security and Encryption](./01-%20Concepts/22-%20Security%20and%20Encryption.md) | IAM, KMS, encryption |
| 23 | [PITR](./01-%20Concepts/23-%20Point-in-Time%20Recovery%20(PITR).md) | Continuous backups |
| 24 | [Architecture Deep Dive](./01-%20Concepts/24-%20DynamoDB%20Architecture%20Deep%20Dive.md) | Request routing, replication, storage internals |
| 25 | [Best Practices and Anti-Patterns](./01-%20Concepts/25-%20Best%20Practices%20and%20Anti-Patterns.md) | Production recommendations |

---

### 02 — Data Modelling (16 files)

The most critical module for production DynamoDB — schema design driven by access patterns.

| # | File | Topic |
|---|------|-------|
| 01 | [Data Modeling Principles](./02-%20Data%20Modelling/01-%20Data%20Modeling%20Principles.md) | Foundational design philosophy |
| 02 | [Access Patterns First Design](./02-%20Data%20Modelling/02-%20Access%20Patterns%20First%20Design.md) | Query-driven schema design |
| 03 | [Single Table Design](./02-%20Data%20Modelling/03-%20Single%20Table%20Design.md) | Combining entities in one table |
| 04 | [One-to-One Relationships](./02-%20Data%20Modelling/04-%20One-to-One%20Relationships.md) | Modeling 1:1 patterns |
| 05 | [One-to-Many Relationships](./02-%20Data%20Modelling/05-%20One-to-Many%20Relationships.md) | Modeling 1:N patterns |
| 06 | [Many-to-Many Relationships](./02-%20Data%20Modelling/06-%20Many-to-Many%20Relationships.md) | Modeling M:N patterns |
| 07 | [Composite Key Design Patterns](./02-%20Data%20Modelling/07-%20Composite%20Key%20Design%20Patterns.md) | Hierarchical keys, overloaded sort keys |
| 08 | [Adjacency List Pattern](./02-%20Data%20Modelling/08-%20Adjacency%20List%20Pattern.md) | Graph-like relationships |
| 09 | [Sparse Index Pattern](./02-%20Data%20Modelling/09-%20Sparse%20Index%20Pattern.md) | Indexing only matching items |
| 10 | [Time-Series Data Modeling](./02-%20Data%20Modelling/10-%20Time-Series%20Data%20Modeling.md) | IoT, logs, events |
| 11 | [Multi-Tenant Data Modeling](./02-%20Data%20Modelling/11-%20Multi-Tenant%20Data%20Modeling.md) | SaaS partition isolation |
| 12 | [Version Control Pattern](./02-%20Data%20Modelling/12-%20Version%20Control%20Pattern.md) | Item versioning and history |
| 13 | [Materialized Graph Pattern](./02-%20Data%20Modelling/13-%20Materialized%20Graph%20Pattern.md) | Pre-computed graph queries |
| 14 | [Write Sharding Pattern](./02-%20Data%20Modelling/14-%20Write%20Sharding%20Pattern.md) | Distributing hot keys |
| 15 | [Event Sourcing Pattern](./02-%20Data%20Modelling/15-%20Event%20Sourcing%20Pattern.md) | Append-only event stores |
| 16 | [Data Modeling Best Practices](./02-%20Data%20Modelling/16-%20Data%20Modeling%20Best%20Practices.md) | Production guidelines |

---

### 03 — Indexes (13 files)

Deep dive into Global Secondary Indexes (GSI) and Local Secondary Indexes (LSI).

| # | File | Topic |
|---|------|-------|
| 01 | [Introduction to Indexes](./03-%20Indexes/01-%20Introduction%20to%20Indexes.md) | Why and when to use indexes |
| 02 | [Global Secondary Index (GSI)](./03-%20Indexes/02-%20Global%20Secondary%20Index%20(GSI).md) | GSI internals, eventually consistent |
| 03 | [Local Secondary Index (LSI)](./03-%20Indexes/03-%20Local%20Secondary%20Index%20(LSI).md) | LSI internals, strongly consistent |
| 04 | [GSI vs LSI](./03-%20Indexes/04-%20GSI%20vs%20LSI.md) | Feature comparison and decision guide |
| 05 | [Sparse Indexes](./03-%20Indexes/05-%20Sparse%20Indexes.md) | Indexing subsets of items |
| 06 | [Composite Index Design](./03-%20Indexes/06-%20Composite%20Index%20Design.md) | Overloaded GSI patterns |
| 07 | [Index Projection Types](./03-%20Indexes/07-%20Index%20Projection%20Types.md) | KEYS_ONLY, INCLUDE, ALL |
| 08 | [Consistency Model of Indexes](./03-%20Indexes/08-%20Consistency%20Model%20of%20Indexes.md) | Propagation lag and trade-offs |
| 09 | [Index Capacity & Cost](./03-%20Indexes/09-%20Index%20Capacity%20%26%20Cost.md) | RCU/WCU cost of indexes |
| 10 | [Index Performance & Optimization](./03-%20Indexes/10-%20Index%20Performance%20%26%20Optimization.md) | Query planning and tuning |
| 11 | [Common Index Design Patterns](./03-%20Indexes/11-%20Common%20Index%20Design%20Patterns.md) | Inverted index, GSI overloading |
| 12 | [Index Anti-Patterns](./03-%20Indexes/12-%20Index%20Anti-Patterns.md) | Common mistakes to avoid |
| 13 | [Production Best Practices](./03-%20Indexes/13-%20Production%20Best%20Practices.md) | Index management in production |

---

### 04 — Querying & Data Access (19 files)

Everything about reading and writing data efficiently.

| # | File | Topic |
|---|------|-------|
| 01 | [Query vs Scan](./04%20-%20Querying%20%26%20Data%20Access/01-%20Query%20vs%20Scan.md) | When to use each operation |
| 02 | [Query Operation](./04%20-%20Querying%20%26%20Data%20Access/02-%20Query%20Operation.md) | Query API deep dive |
| 03 | [Scan Operation](./04%20-%20Querying%20%26%20Data%20Access/03-%20Scan%20Operation.md) | Full-table scans and parallel scan |
| 04 | [Key Condition Expressions](./04%20-%20Querying%20%26%20Data%20Access/04-%20Key%20Condition%20Expressions.md) | Filtering on partition/sort key |
| 05 | [Filter Expressions](./04%20-%20Querying%20%26%20Data%20Access/05-%20Filter%20Expressions.md) | Post-query filtering |
| 06 | [Projection Expressions](./04%20-%20Querying%20%26%20Data%20Access/06-%20Projection%20Expressions.md) | Selecting specific attributes |
| 07 | [Condition Expressions](./04%20-%20Querying%20%26%20Data%20Access/07-%20Condition%20Expressions.md) | Conditional writes and updates |
| 08 | [Pagination](./04%20-%20Querying%20%26%20Data%20Access/08-%20Pagination.md) | ExclusiveStartKey patterns |
| 09 | [Reading Data](./04%20-%20Querying%20%26%20Data%20Access/09-%20Reading%20Data.md) | GetItem, Query, Scan strategies |
| 10 | [Writing Data](./04%20-%20Querying%20%26%20Data%20Access/10-%20Writing%20Data.md) | PutItem, UpdateItem, DeleteItem |
| 11 | [BatchGetItem](./04%20-%20Querying%20%26%20Data%20Access/11-%20BatchGetItem.md) | Batch reads (up to 100 items) |
| 12 | [BatchWriteItem](./04%20-%20Querying%20%26%20Data%20Access/12-%20BatchWriteItem.md) | Batch writes (up to 25 items) |
| 13 | [TransactGetItems](./04%20-%20Querying%20%26%20Data%20Access/13-%20TransactGetItems.md) | Transactional reads |
| 14 | [TransactWriteItems](./04%20-%20Querying%20%26%20Data%20Access/14-%20TransactWriteItems.md) | Transactional writes |
| 15 | [Conditional Writes](./04%20-%20Querying%20%26%20Data%20Access/15-%20Conditional%20Writes.md) | Write-if conditions |
| 16 | [Atomic Counters](./04%20-%20Querying%20%26%20Data%20Access/16-%20Atomic%20Counters.md) | Thread-safe increment/decrement |
| 17 | [Optimistic Locking](./04%20-%20Querying%20%26%20Data%20Access/17-%20Optimistic%20Locking.md) | Version-based concurrency control |
| 18 | [Error Handling & Retries](./04%20-%20Querying%20%26%20Data%20Access/18-%20Error%20Handling%20%26%20Retries.md) | Exponential backoff, throttling |
| 19 | [Query Performance Best Practices](./04%20-%20Querying%20%26%20Data%20Access/19-%20Query%20Performance%20Best%20Practices.md) | Production query optimization |

---

### 05 — Advanced Features (13 files)

Production features beyond CRUD — streams, caching, global replication, and data lifecycle.

| # | File | Topic |
|---|------|-------|
| 01 | [DynamoDB Streams](./05-%20Advanced%20Features/01-%20DynamoDB%20Streams.md) | Change data capture |
| 02 | [Time To Live (TTL)](./05-%20Advanced%20Features/02-%20Time%20To%20Live%20(TTL).md) | Automatic item expiration |
| 03 | [DAX](./05-%20Advanced%20Features/03-%20DynamoDB%20Accelerator%20(DAX).md) | In-memory caching |
| 04 | [Global Tables](./05-%20Advanced%20Features/04-%20Global%20Tables.md) | Multi-region active-active |
| 05 | [PITR](./05-%20Advanced%20Features/05-%20Point-in-Time%20Recovery%20(PITR).md) | Continuous backups |
| 06 | [Backup & Restore](./05-%20Advanced%20Features/06-%20Backup%20%26%20Restore.md) | On-demand and scheduled backups |
| 07 | [Export to S3](./05-%20Advanced%20Features/07-%20Export%20to%20Amazon%20S3.md) | Full table export for analytics |
| 08 | [Import from S3](./05-%20Advanced%20Features/08-%20Import%20from%20Amazon%20S3.md) | Bulk data loading |
| 09 | [PartiQL](./05-%20Advanced%20Features/09-%20PartiQL.md) | SQL-compatible queries |
| 10 | [TTL Design Patterns](./05-%20Advanced%20Features/10-%20Time-to-Live%20Design%20Patterns.md) | Advanced expiration strategies |
| 11 | [Streams Design Patterns](./05-%20Advanced%20Features/11-%20Streams%20Design%20Patterns.md) | Event-driven architectures |
| 12 | [Global Tables Best Practices](./05-%20Advanced%20Features/12-%20Global%20Tables%20Best%20Practices.md) | Multi-region production patterns |
| 13 | [Advanced DynamoDB Patterns](./05-%20Advanced%20Features/13-%20Advanced%20DynamoDB%20Patterns.md) | Expert-level design patterns |

---

### 06 — Security (7 files)

Securing DynamoDB from IAM policies to encryption and compliance.

| # | File | Topic |
|---|------|-------|
| 01 | [IAM Authentication & Authorization](./06-%20Security/01-%20IAM%20Authentication%20%26%20Authorization.md) | Table/item-level IAM policies |
| 02 | [Fine-Grained Access Control](./06-%20Security/02-%20Fine-Grained%20Access%20Control%20(FGAC).md) | Row-level and attribute-level security |
| 03 | [Encryption & KMS](./06-%20Security/03-%20Encryption%20%26%20AWS%20KMS.md) | At-rest and in-transit encryption |
| 04 | [VPC Endpoints](./06-%20Security/04-%20VPC%20Endpoints.md) | Private connectivity without internet |
| 05 | [CloudTrail & Auditing](./06-%20Security/05-%20CloudTrail,%20CloudWatch%20%26%20Auditing.md) | API logging and compliance auditing |
| 06 | [Data Protection & Compliance](./06-%20Security/06-%20Data%20Protection%20%26%20Compliance.md) | GDPR, HIPAA, SOC considerations |
| 07 | [Security Best Practices](./06-%20Security/07-%20Security%20Best%20Practices.md) | Production security checklist |

---

### 07 — Monitoring & Performance (9 files)

Capacity planning, performance tuning, cost optimization, and troubleshooting.

| # | File | Topic |
|---|------|-------|
| 01 | [Capacity Modes](./07-%20Monitoring%20%26%20Performance/01-%20Capacity%20Modes.md) | Provisioned vs On-Demand deep dive |
| 02 | [RCU & WCU](./07-%20Monitoring%20%26%20Performance/02-%20Read%20%26%20Write%20Capacity%20Units.md) | Throughput calculation and planning |
| 03 | [Auto Scaling Deep Dive](./07-%20Monitoring%20%26%20Performance/03-%20Auto%20Scaling%20Deep%20Dive.md) | Target tracking and scaling behavior |
| 04 | [Hot Partitions & Adaptive Capacity](./07-%20Monitoring%20%26%20Performance/04-%20Hot%20Partitions%20%26%20Adaptive%20Capacity.md) | Diagnosing and resolving hotspots |
| 05 | [Performance Optimization](./07-%20Monitoring%20%26%20Performance/05-%20Performance%20Optimization%20Best%20Practices.md) | Query tuning and throughput optimization |
| 06 | [CloudWatch Monitoring](./07-%20Monitoring%20%26%20Performance/06-%20Monitoring%20with%20CloudWatch.md) | Metrics, alarms, and dashboards |
| 07 | [Performance Troubleshooting](./07-%20Monitoring%20%26%20Performance/07-%20Performance%20Troubleshooting.md) | Diagnosing throttling and latency |
| 08 | [Cost Optimization](./07-%20Monitoring%20%26%20Performance/08-%20Cost%20Optimization.md) | Reserved capacity, right-sizing |
| 09 | [Production Performance Patterns](./07-%20Monitoring%20%26%20Performance/09-%20Production%20Performance%20Patterns.md) | Real-world performance architectures |

---

### 08 — Integration Patterns (10 files)

Building event-driven and serverless architectures with DynamoDB.

| # | File | Topic |
|---|------|-------|
| 01 | [DynamoDB + Lambda](./08-%20Integration%20Patterns/01-%20DynamoDB%20+%20AWS%20Lambda.md) | Streams triggers and direct invocation |
| 02 | [DynamoDB + SQS](./08-%20Integration%20Patterns/02-%20DynamoDB%20+%20Amazon%20SQS.md) | Queue-based decoupling |
| 03 | [DynamoDB + SNS](./08-%20Integration%20Patterns/03-%20DynamoDB%20+%20Amazon%20SNS.md) | Fan-out notifications |
| 04 | [DynamoDB + EventBridge](./08-%20Integration%20Patterns/04-%20DynamoDB%20+%20Amazon%20EventBridge.md) | Event routing and filtering |
| 05 | [DynamoDB + Step Functions](./08-%20Integration%20Patterns/05-%20DynamoDB%20+%20AWS%20Step%20Functions.md) | Orchestrated workflows |
| 06 | [DynamoDB + API Gateway](./08-%20Integration%20Patterns/06-%20DynamoDB%20+%20API%20Gateway.md) | Direct integration (no Lambda) |
| 07 | [DynamoDB + Kinesis](./08-%20Integration%20Patterns/07-%20DynamoDB%20+%20Kinesis.md) | Real-time stream processing |
| 08 | [CQRS with DynamoDB](./08-%20Integration%20Patterns/08-%20CQRS%20with%20DynamoDB.md) | Command/Query separation |
| 09 | [Event-Driven Microservices](./08-%20Integration%20Patterns/09-%20Event-Driven%20Microservices.md) | DynamoDB as event source |
| 10 | [Production Integration Patterns](./08-%20Integration%20Patterns/10-%20Production%20Integration%20Patterns.md) | Battle-tested architectures |

---

### 09 — Python SDK (18 files)

Hands-on Boto3 and aioboto3 usage — from basics to production-grade repository patterns.

| # | File | Topic |
|---|------|-------|
| 01 | [Boto3 Introduction](./09-%20Python%20SDK/01-%20Boto3%20Introduction.md) | Client vs Resource API |
| 02 | [AWS Credentials](./09-%20Python%20SDK/02-%20Configuring%20AWS%20Credentials.md) | Credential chain and profiles |
| 03 | [Sessions, Clients & Resources](./09-%20Python%20SDK/03-%20Sessions,%20Clients%20%26%20Resources.md) | Connection management |
| 04 | [CRUD with Boto3](./09-%20Python%20SDK/04-%20CRUD%20Operations%20with%20Boto3.md) | Put, Get, Update, Delete |
| 05 | [Querying Data](./09-%20Python%20SDK/05-%20Querying%20Data.md) | Query and Scan with Boto3 |
| 06 | [Batch Operations](./09-%20Python%20SDK/06-%20Batch%20Operations.md) | BatchGetItem, BatchWriteItem |
| 07 | [Conditional Writes](./09-%20Python%20SDK/07-%20Conditional%20Writes.md) | ConditionExpression patterns |
| 08 | [Transactions](./09-%20Python%20SDK/08-%20Transactions.md) | TransactWriteItems / GetItems |
| 09 | [Pagination](./09-%20Python%20SDK/09-%20Pagination.md) | Paginator and manual pagination |
| 10 | [Error Handling & Retries](./09-%20Python%20SDK/10-%20Error%20Handling%20%26%20Retries.md) | Botocore retry configuration |
| 11 | [Performance Optimization](./09-%20Python%20SDK/11-%20Performance%20Optimization.md) | Connection pooling, batch tuning |
| 12 | [Advanced Boto3 Patterns](./09-%20Python%20SDK/12-%20Advanced%20Boto3%20Patterns.md) | Expert-level techniques |
| 13 | [Production Repository Layer](./09-%20Python%20SDK/13-%20Building%20a%20Production%20Repository%20Layer.md) | Clean architecture with DynamoDB |
| 14 | [Async with aioboto3](./09-%20Python%20SDK/14-%20Async%20Access%20with%20aioboto3.md) | Async/await DynamoDB access |
| 15 | [Unit Testing](./09-%20Python%20SDK/15-%20Unit%20Testing%20DynamoDB%20Code.md) | Mocking and moto library |
| 16 | [DynamoDB Local](./09-%20Python%20SDK/16-%20Local%20Development%20with%20DynamoDB%20Local.md) | Local development setup |
| 17 | [Production Best Practices](./09-%20Python%20SDK/17-%20Production%20Best%20Practices.md) | SDK configuration for production |
| 18 | [Interview Questions](./09-%20Python%20SDK/18-%20Interview%20Questions.md) | Boto3-specific interview prep |

---

### 10 — Interview Questions (11 files)

Comprehensive interview preparation covering every DynamoDB topic.

| # | File | Topic |
|---|------|-------|
| 01 | [DynamoDB Fundamentals](./10-%20Interview%20Questions/01-%20DynamoDB%20Fundamentals.md) | Core concepts and architecture |
| 02 | [Data Modeling](./10-%20Interview%20Questions/02-%20Data%20Modeling.md) | Schema design questions |
| 03 | [Indexes (GSI & LSI)](./10-%20Interview%20Questions/03-%20Indexes%20(GSI%20%26%20LSI).md) | Index design and trade-offs |
| 04 | [Querying & Performance](./10-%20Interview%20Questions/04-%20Querying%20%26%20Performance.md) | Query optimization questions |
| 05 | [Transactions & Consistency](./10-%20Interview%20Questions/05-%20Transactions%20%26%20Consistency.md) | ACID and consistency models |
| 06 | [Streams, TTL & Advanced](./10-%20Interview%20Questions/06-%20Streams,%20TTL%20%26%20Advanced%20Features.md) | Advanced feature questions |
| 07 | [Security & IAM](./10-%20Interview%20Questions/07-%20Security%20%26%20IAM.md) | Security scenario questions |
| 08 | [Production Scenarios](./10-%20Interview%20Questions/08-%20Production%20Scenarios.md) | Real-world debugging scenarios |
| 09 | [System Design Scenarios](./10-%20Interview%20Questions/09-%20System%20Design%20Scenarios.md) | Architecture design questions |
| 10 | [Coding & Boto3](./10-%20Interview%20Questions/10-%20Coding%20%26%20Boto3%20Questions.md) | Hands-on coding questions |
| 11 | [Mock Senior Interview](./10-%20Interview%20Questions/11-%20Mock%20Senior%20Backend%20Interview.md) | Full mock interview simulation |

---

## Quick Reference

### DynamoDB Limits

| Resource | Limit |
|----------|-------|
| Max item size | 400 KB |
| Max partition key length | 2,048 bytes |
| Max sort key length | 1,024 bytes |
| Max GSIs per table | 20 |
| Max LSIs per table | 5 |
| Max BatchGetItem | 100 items / 16 MB |
| Max BatchWriteItem | 25 items / 16 MB |
| Max TransactWriteItems | 100 items / 4 MB |
| Max partition throughput | 3,000 RCU / 1,000 WCU |
| Max partition data | 10 GB |

### RCU / WCU Calculation

```text
Read Capacity Unit (RCU):
  1 RCU = 1 strongly consistent read/sec for items up to 4 KB
  1 RCU = 2 eventually consistent reads/sec for items up to 4 KB
  Transactional reads cost 2x

Write Capacity Unit (WCU):
  1 WCU = 1 write/sec for items up to 1 KB
  Transactional writes cost 2x

Example: 10 items/sec × 6 KB each, strongly consistent
  = 10 × ceil(6/4) = 10 × 2 = 20 RCU
```

### Key Design Principles

```text
1. Know your access patterns BEFORE designing the schema
2. Design for queries, not for data normalization
3. Use composite sort keys for hierarchical data
4. Prefer GSI over Scan — always
5. Use sparse indexes to index subsets efficiently
6. Single Table Design reduces cost and latency
7. Use TTL for automatic cleanup — it's free
8. Enable PITR from day one — it costs almost nothing
9. Use On-Demand for unpredictable workloads
10. Monitor ConsumedCapacity and ThrottledRequests in CloudWatch
```

---

## Prerequisites

- Basic database concepts and SQL fundamentals
- REST API design experience
- AWS IAM basics
- Basic cloud computing concepts
- Python experience (for SDK module)

No prior NoSQL experience is required.

---

## Who These Notes Are For

- Senior Backend Engineers designing data-intensive systems
- DevOps / Cloud Engineers managing DynamoDB in production
- Solutions Architects evaluating NoSQL vs relational
- Software Engineers preparing for system design interviews
- AWS certification candidates (Developer, Solutions Architect, DevOps Professional)

---
