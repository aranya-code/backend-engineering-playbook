# DynamoDB Indexes

Master Amazon DynamoDB Secondary Indexes from a **Senior Backend Engineer** perspective.

Indexes are the foundation of efficient DynamoDB data retrieval. Unlike relational databases where indexes are often added after schema design, DynamoDB indexes are designed **around application access patterns**. Understanding when and how to use Global Secondary Indexes (GSIs), Local Secondary Indexes (LSIs), projection types, and composite index strategies is essential for building scalable, low-latency, and cost-efficient applications.

This section covers everything from index fundamentals to production optimization, common design patterns, anti-patterns, and enterprise best practices.

---

# Learning Objectives

After completing this section, you will understand:

- Why secondary indexes exist in DynamoDB
- Differences between GSIs and LSIs
- How index consistency works
- Choosing the right projection type
- Designing efficient composite indexes
- Optimizing index performance
- Reducing storage and write costs
- Common production index design patterns
- Avoiding expensive anti-patterns
- Enterprise best practices for operating indexes at scale

---

# Folder Structure

```text
03- Indexes
│
├── 01- Introduction to Indexes.md
├── 02- Global Secondary Index (GSI).md
├── 03- Local Secondary Index (LSI).md
├── 04- GSI vs LSI.md
├── 05- Sparse Indexes.md
├── 06- Composite Index Design.md
├── 07- Index Projection Types.md
├── 08- Consistency Model of Indexes.md
├── 09- Index Capacity & Cost.md
├── 10- Index Performance & Optimization.md
├── 11- Common Index Design Patterns.md
├── 12- Index Anti-Patterns.md
├── 13- Production Best Practices.md
└── README.md
```

---

# Learning Path

## Foundations

| Chapter | Description |
|----------|-------------|
| **01 - Introduction to Indexes** | Learn why secondary indexes exist, how they differ from SQL indexes, and how DynamoDB uses indexes to support multiple access patterns. |
| **02 - Global Secondary Index (GSI)** | Understand GSIs, independent partitioning, asynchronous replication, capacity planning, and common production use cases. |
| **03 - Local Secondary Index (LSI)** | Learn how LSIs share partitions with the base table, support strong consistency, and where they fit in production systems. |
| **04 - GSI vs LSI** | Compare architecture, scalability, consistency, limitations, and decision criteria for selecting the right index type. |

---

## Index Design

| Chapter | Description |
|----------|-------------|
| **05 - Sparse Indexes** | Design lightweight indexes that contain only relevant items, reducing storage and write costs. |
| **06 - Composite Index Design** | Build reusable indexes using composite partition and sort keys to support multiple business queries. |
| **07 - Index Projection Types** | Compare KEYS_ONLY, INCLUDE, and ALL projections and understand their impact on storage, performance, and cost. |

---

## Performance & Operations

| Chapter | Description |
|----------|-------------|
| **08 - Consistency Model of Indexes** | Understand strong consistency vs eventual consistency, GSI replication, and read-after-write behavior. |
| **09 - Index Capacity & Cost** | Learn how indexes consume storage and throughput, calculate write amplification, and optimize operational costs. |
| **10 - Index Performance & Optimization** | Optimize partition keys, sort keys, projections, and query patterns for predictable low-latency performance. |

---

## Production Architecture

| Chapter | Description |
|----------|-------------|
| **11 - Common Index Design Patterns** | Explore proven production patterns such as Lookup, Time-Series, Sparse, Composite, Hierarchical, Multi-Tenant, and Event Sourcing indexes. |
| **12 - Index Anti-Patterns** | Identify common mistakes that lead to hot partitions, excessive costs, throttling, and poor scalability. |
| **13 - Production Best Practices** | Learn enterprise strategies for designing, monitoring, reviewing, and continuously optimizing indexes in large-scale systems. |

---

# Recommended Learning Order

```text
Introduction
      │
      ▼
GSI & LSI
      │
      ▼
Projection Types
      │
      ▼
Composite Index Design
      │
      ▼
Consistency
      │
      ▼
Capacity & Cost
      │
      ▼
Performance Optimization
      │
      ▼
Design Patterns
      │
      ▼
Anti-Patterns
      │
      ▼
Production Best Practices
```

---

# Key Concepts Covered

## Secondary Index Types

- Global Secondary Index (GSI)
- Local Secondary Index (LSI)
- Sparse Indexes
- Composite Indexes

## Index Architecture

- Independent partitions
- Shared partitions
- Replication model
- Projection types
- Item collections
- Read consistency

## Performance Optimization

- High-cardinality partition keys
- Composite sort keys
- Query optimization
- Pagination
- Adaptive Capacity
- Hot partition avoidance

## Cost Optimization

- Write amplification
- Storage optimization
- Projection strategies
- Sparse indexes
- Capacity planning
- CloudWatch monitoring

## Production Design

- Lookup patterns
- Time-series indexes
- Leaderboards
- Multi-tenant architectures
- Analytics indexes
- Event sourcing
- Workflow queues

---

# Production Skills You'll Gain

After completing this module, you'll be able to:

- Design scalable GSIs and LSIs
- Model indexes around business access patterns
- Eliminate Scan operations using efficient Query designs
- Prevent hot partitions with high-cardinality keys
- Minimize storage and write costs through projection optimization
- Build reusable composite indexes supporting multiple queries
- Monitor and optimize index performance in production
- Identify and resolve common DynamoDB index bottlenecks
- Design enterprise-grade indexing strategies for high-scale applications

---

# Common Interview Topics

Senior backend interviews frequently cover:

- GSI vs LSI
- Strong vs eventual consistency
- Read-after-write behavior
- Projection types
- Sparse indexes
- Composite key design
- Index cost calculation
- Write amplification
- Hot partitions
- Query vs Scan
- Index optimization strategies
- Production troubleshooting

---

