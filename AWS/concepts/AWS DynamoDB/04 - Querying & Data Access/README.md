# Querying & Data Access

DynamoDB is fundamentally an **access-pattern-driven database**. Unlike relational databases where queries are written after the schema is designed, DynamoDB requires developers to design the schema around how the application will read and write data.

This section explores every major DynamoDB data access operation—from simple `GetItem` requests to ACID-compliant transactions—along with the performance implications of each operation. It explains not only **how** each API works, but **why** it exists, **when** it should be used, and the trade-offs involved in real-world production systems.

By the end of this section, you will understand how to build scalable, low-latency data access layers capable of serving millions of requests per second while minimizing read and write costs.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand how DynamoDB processes read and write requests internally.
- Select the correct API for every access pattern.
- Design highly efficient Query operations.
- Avoid expensive Scan operations in production.
- Build scalable pagination mechanisms.
- Implement optimistic concurrency control.
- Handle retries and transient failures safely.
- Design idempotent write operations.
- Build ACID-compliant transactional workflows.
- Optimize latency, throughput, and DynamoDB costs.

---

# Prerequisites

Before starting this section, you should already understand:

- DynamoDB Tables
- Items and Attributes
- Primary Keys
- Partition Keys
- Sort Keys
- Secondary Indexes (GSI & LSI)
- Read Consistency Models
- Capacity Modes
- RCUs and WCUs

If not, complete the following sections first:

- **01 - Concepts**
- **02 - Data Modeling**
- **03 - Indexes**

---

# What You'll Learn

This module is divided into nineteen chapters that gradually progress from basic data retrieval to advanced production techniques.

The journey begins by comparing **Query** and **Scan**, helping you understand why Query is the preferred operation in nearly every production workload.

You will then learn how Query, Scan, Key Condition Expressions, Filter Expressions, Projection Expressions, and Pagination work internally before exploring complete read and write workflows.

The second half focuses on advanced production features including:

- Batch Operations
- Transactions
- Conditional Writes
- Atomic Counters
- Optimistic Locking
- Error Handling
- Retry Strategies
- Query Performance Optimization

Finally, you'll learn the best practices used by senior backend engineers to build highly scalable DynamoDB applications.

---

# Folder Structure

```text
04 - Querying & Data Access
│
├── 01- Query vs Scan.md
├── 02- Query Operation.md
├── 03- Scan Operation.md
├── 04- Key Condition Expressions.md
├── 05- Filter Expressions.md
├── 06- Projection Expressions.md
├── 07- Condition Expressions.md
├── 08- Pagination.md
├── 09- Reading Data.md
├── 10- Writing Data.md
├── 11- BatchGetItem.md
├── 12- BatchWriteItem.md
├── 13- TransactGetItems.md
├── 14- TransactWriteItems.md
├── 15- Conditional Writes.md
├── 16- Atomic Counters.md
├── 17- Optimistic Locking.md
├── 18- Error Handling & Retries.md
├── 19- Query Performance Best Practices.md
└── README.md
```

---

# Learning Path

```text
Basic Reads

        │

        ▼

Query vs Scan

        │

        ▼

Query Operations

        │

        ▼

Filtering & Projection

        │

        ▼

Pagination

        │

        ▼

Reading & Writing APIs

        │

        ▼

Batch Operations

        │

        ▼

Transactions

        │

        ▼

Conditional Writes

        │

        ▼

Concurrency Control

        │

        ▼

Retry Strategies

        │

        ▼

Performance Optimization
```

Each chapter builds upon concepts introduced earlier, providing a gradual progression from fundamental operations to enterprise-scale design patterns.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Query vs Scan](./01-%20Query%20vs%20Scan.md) | Compare Query and Scan, understand their internal behavior, costs, and production use cases. |
| [02 - Query Operation](./02-%20Query%20Operation.md) | Learn efficient item retrieval using Partition Keys and Sort Keys. |
| [03 - Scan Operation](./03-%20Scan%20Operation.md) | Understand full table scans, Parallel Scan, and why Scan should be avoided in most production APIs. |
| [04 - Key Condition Expressions](./04-%20Key%20Condition%20Expressions.md) | Build efficient queries using Key Conditions and Sort Key operators. |
| [05 - Filter Expressions](./05-%20Filter%20Expressions.md) | Learn filtering behavior, supported operators, and performance implications. |
| [06 - Projection Expressions](./06-%20Projection%20Expressions.md) | Retrieve only required attributes to reduce payload size and latency. |
| [07 - Condition Expressions](./07-%20Condition%20Expressions.md) | Apply business rules and conditional validation to DynamoDB operations. |
| [08 - Pagination](./08-%20Pagination.md) | Master paginated reads using LastEvaluatedKey and ExclusiveStartKey. |
| [09 - Reading Data](./09-%20Reading%20Data.md) | Overview of all DynamoDB read APIs and how to choose the correct one. |
| [10 - Writing Data](./10-%20Writing%20Data.md) | Overview of all DynamoDB write APIs and their production use cases. |
| [11 - BatchGetItem](./11-%20BatchGetItem.md) | Retrieve multiple items efficiently in a single request. |
| [12 - BatchWriteItem](./12-%20BatchWriteItem.md) | Perform high-throughput batch write and delete operations. |
| [13 - TransactGetItems](./13-%20TransactGetItems.md) | Execute transactional reads with ACID guarantees. |
| [14 - TransactWriteItems](./14-%20TransactWriteItems.md) | Execute atomic multi-item write transactions. |
| [15 - Conditional Writes](./15-%20Conditional%20Writes.md) | Prevent race conditions and enforce business rules during writes. |
| [16 - Atomic Counters](./16-%20Atomic%20Counters.md) | Safely increment and decrement numeric attributes under heavy concurrency. |
| [17 - Optimistic Locking](./17-%20Optimistic%20Locking.md) | Prevent lost updates using version-based concurrency control. |
| [18 - Error Handling & Retries](./18-%20Error%20Handling%20%26%20Retries.md) | Build resilient applications using retries, exponential backoff, jitter, and idempotency. |
| [19 - Query Performance Best Practices](./19-%20Query%20Performance%20Best%20Practices.md) | Optimize Query performance, minimize RCUs, avoid hot partitions, and design scalable access patterns. |

---

# Production Skills You'll Gain

After completing this section, you'll be able to:

- Design DynamoDB APIs for high-performance backend systems.
- Build scalable microservices using efficient access patterns.
- Optimize Query latency and DynamoDB capacity consumption.
- Implement ACID transactions where required.
- Prevent race conditions without distributed locks.
- Design idempotent APIs that safely handle retries.
- Build reliable distributed systems capable of handling millions of requests with predictable performance.

---

