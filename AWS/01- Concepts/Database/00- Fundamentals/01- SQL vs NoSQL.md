# SQL vs NoSQL

# Introduction

Choosing the correct database paradigm is one of the most impactful architectural decisions in backend engineering. The choice between SQL (relational) and NoSQL (non-relational) databases determines how data is modeled, how it scales, how transactions are handled, and how the system evolves over time.

This is not a question of which paradigm is better. It is a question of which paradigm is correct for the specific workload, data relationships, consistency requirements, and scaling demands of your application.

---

# SQL Databases (Relational)

## What Are SQL Databases?

SQL databases store data in structured tables with predefined schemas. Tables consist of rows (records) and columns (attributes). Relationships between tables are expressed through foreign keys, and data is queried using Structured Query Language (SQL).

## Core Characteristics

- Fixed Schema: Every row in a table must conform to the same column definitions. Schema changes (ALTER TABLE) require careful migration planning in production systems.
- ACID Transactions: SQL databases provide Atomicity, Consistency, Isolation, and Durability guarantees for transactions, ensuring data integrity even during failures.
- Referential Integrity: Foreign key constraints enforce valid relationships between tables, preventing orphaned records.
- Complex Queries: SQL supports JOINs, aggregations, subqueries, window functions, and CTEs (Common Table Expressions) for sophisticated data retrieval.
- Vertical Scaling: SQL databases primarily scale by adding more CPU, RAM, and faster storage to a single server (scale-up).

## AWS SQL Database Services

```text
Amazon RDS          → Managed relational database (PostgreSQL, MySQL, MariaDB, Oracle, SQL Server)
Amazon Aurora       → Cloud-optimized relational database (MySQL/PostgreSQL compatible)
Amazon Redshift     → Columnar data warehouse for analytical queries (OLAP)
```

## Ideal Workloads

- Financial and banking systems requiring strict transaction guarantees
- E-commerce order management with multi-table relationships
- ERP and CRM systems with complex, unpredictable queries
- Applications with strong data integrity requirements

---

# NoSQL Databases (Non-Relational)

## What Are NoSQL Databases?

NoSQL databases store data in formats other than traditional relational tables. They are designed for flexibility, horizontal scalability, and high-throughput access patterns. NoSQL encompasses several data models including key-value, document, wide-column, and graph databases.

## Core Characteristics

- Flexible Schema: Documents or records in the same collection can have different attributes. Schema evolution does not require table migrations.
- Horizontal Scaling: NoSQL databases are designed to scale by distributing data across many commodity servers (scale-out).
- High Throughput: Optimized for single-digit millisecond access patterns on massive datasets.
- Eventual Consistency: Many NoSQL systems default to eventual consistency to maximize availability and partition tolerance (see CAP Theorem).
- Access Pattern Driven Design: NoSQL data modeling requires knowing your query patterns upfront. You model data around how it will be accessed, not how it is structured.

## NoSQL Data Models

```text
Key-Value Store
┌──────────────────────────────────┐
│ Key: "user:1001"                 │
│ Value: { name: "Alice", age: 30 }│
└──────────────────────────────────┘
Example: Amazon DynamoDB, Redis

Document Store
┌──────────────────────────────────┐
│ {                                │
│   "_id": "order_5001",           │
│   "items": [...],                │
│   "status": "shipped",           │
│   "address": { ... }             │
│ }                                │
└──────────────────────────────────┘
Example: Amazon DocumentDB, MongoDB

Wide-Column Store
┌──────────────────────────────────┐
│ Row Key → Column Family → Columns│
│ "user:1001" → profile → {name,  │
│                           email} │
│             → activity → {last,  │
│                           count} │
└──────────────────────────────────┘
Example: Apache Cassandra, Amazon Keyspaces

Graph Database
┌──────────────────────────────────┐
│ (Alice) ──FOLLOWS──► (Bob)       │
│ (Alice) ──LIKES────► (Post:42)   │
│ (Bob)   ──WROTE────► (Post:42)   │
└──────────────────────────────────┘
Example: Amazon Neptune
```

## AWS NoSQL Database Services

```text
Amazon DynamoDB     → Managed key-value and document database (serverless, millisecond latency)
Amazon DocumentDB   → Managed document database (MongoDB compatible)
Amazon Keyspaces    → Managed wide-column database (Cassandra compatible)
Amazon Neptune      → Managed graph database (Gremlin/SPARQL)
```

---

# SQL vs NoSQL Detailed Comparison

| Feature | SQL (Relational) | NoSQL (Non-Relational) |
|---------|------------------|------------------------|
| Data Model | Tables with rows and columns | Key-value, Document, Wide-column, Graph |
| Schema | Fixed (defined upfront) | Flexible (schema-on-read) |
| Query Language | SQL (Standardized) | API calls, proprietary query languages |
| Transactions | Full ACID support | Varies (some support ACID per-item) |
| Joins | Native multi-table JOINs | Typically not supported (denormalize instead) |
| Scaling | Vertical (scale-up) | Horizontal (scale-out) |
| Consistency | Strong consistency by default | Eventual consistency by default (configurable) |
| Schema Changes | Requires ALTER TABLE migrations | Flexible, no migration needed |
| Write Throughput | Limited by single primary node | Distributed across partitions |
| Best For | Complex queries, data integrity | High scale, simple access patterns |

---

# Data Modeling Philosophy

The fundamental difference between SQL and NoSQL extends beyond technology into how engineers think about data.

## SQL: Model First, Query Later

```text
1. Analyze entity relationships
2. Normalize data into tables (3NF)
3. Define foreign keys and constraints
4. Query with flexible SQL JOINs

You can model data without knowing all queries upfront.
Queries adapt to the model.
```

## NoSQL: Query First, Model Later

```text
1. Identify all access patterns (reads and writes)
2. Design partition keys and sort keys around access patterns
3. Denormalize data to avoid joins
4. Store related data together in single items

You MUST know all access patterns before modeling data.
The model adapts to the queries.
```

This difference is critical. Migrating from a SQL database to a NoSQL database (or vice versa) often requires a complete redesign of the data model, not just a schema translation.

---

# Real-World Decision Framework

```text
Decision Tree:

Does the workload require multi-table JOINs and complex ad-hoc queries?
   ├── YES ──► SQL (RDS / Aurora)
   └── NO
        │
Are ACID transactions critical across multiple entities?
   ├── YES ──► SQL (RDS / Aurora)
   └── NO
        │
Is horizontal scaling to millions of requests/sec required?
   ├── YES ──► NoSQL (DynamoDB)
   └── NO
        │
Is schema flexibility important (frequently changing attributes)?
   ├── YES ──► NoSQL (DocumentDB / DynamoDB)
   └── NO  ──► Either can work. Default to SQL for operational simplicity.
```

---

# Common Mistakes

- Choosing NoSQL because it is trending without analyzing access patterns.
- Forcing JOINs in a NoSQL database by making multiple queries and merging in application code (defeats the purpose).
- Not considering operational overhead. SQL databases on RDS are fully managed and require less application-layer complexity than properly modeling DynamoDB.
- Over-normalizing in SQL to the point where every query requires 5+ JOINs, creating performance bottlenecks.

---

# Interview Questions

1. When would you choose DynamoDB over Aurora for a new microservice?
2. How does data modeling differ between SQL and NoSQL databases?
3. Can you perform JOINs in DynamoDB? If not, what is the alternative?
4. What does schema-on-read mean and how does it impact application code?

---

# Key Takeaways

- SQL databases are optimized for data integrity, complex queries, and ACID transactions.
- NoSQL databases are optimized for horizontal scale, flexible schemas, and predictable access patterns.
- SQL models data first and queries adapt. NoSQL models queries first and data adapts.
- AWS provides managed services for both paradigms. Choose based on workload requirements, not popularity.
- Most production architectures use both (polyglot persistence). Use SQL for transactional data, NoSQL for high-scale access.

---
