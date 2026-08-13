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

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to Indexes](./01-%20Introduction%20to%20Indexes.md) | Learn why DynamoDB secondary indexes exist, how they differ from SQL indexes, and how they enable efficient access patterns in NoSQL databases. |
| [02 - Global Secondary Index (GSI)](./02-%20Global%20Secondary%20Index%20(GSI).md) | Understand Global Secondary Indexes, independent partitioning, eventual consistency, throughput, and production use cases. |
| [03 - Local Secondary Index (LSI)](./03-%20Local%20Secondary%20Index%20(LSI).md) | Learn how Local Secondary Indexes work, their strong consistency model, shared partitions, and limitations. |
| [04 - GSI vs LSI](./04-%20GSI%20vs%20LSI.md) | Compare GSIs and LSIs across architecture, consistency, scalability, throughput, storage, and real-world design decisions. |
| [05 - Sparse Indexes](./05-%20Sparse%20Indexes.md) | Learn how Sparse Indexes reduce storage costs, improve query performance, and optimize DynamoDB workloads. |
| [06 - Composite Index Design](./06-%20Composite%20Index%20Design.md) | Master composite partition and sort key design to support multiple business access patterns using a single index. |
| [07 - Index Projection Types](./07-%20Index%20Projection%20Types.md) | Explore KEYS_ONLY, INCLUDE, and ALL projection types and understand their impact on storage, performance, and cost. |
| [08 - Consistency Model of Indexes](./08-%20Consistency%20Model%20of%20Indexes.md) | Understand strong consistency, eventual consistency, GSI replication, and read-after-write behavior in secondary indexes. |
| [09 - Index Capacity & Cost](./09-%20Index%20Capacity%20%26%20Cost.md) | Learn how secondary indexes consume storage, read/write capacity, and influence DynamoDB pricing and operational costs. |
| [10 - Index Performance & Optimization](./10-%20Index%20Performance%20%26%20Optimization.md) | Optimize partition keys, sort keys, projections, and query patterns for scalable, low-latency DynamoDB applications. |
| [11 - Common Index Design Patterns](./11-%20Common%20Index%20Design%20Patterns.md) | Explore proven production design patterns including Lookup, Time-Series, Sparse, Composite, Hierarchical, Multi-Tenant, and Event Sourcing indexes. |
| [12 - Index Anti-Patterns](./12-%20Index%20Anti-Patterns.md) | Identify common index design mistakes that cause hot partitions, throttling, high costs, and poor scalability. |
| [13 - Production Best Practices](./13-%20Production%20Best%20Practices.md) | Learn enterprise best practices for designing, monitoring, optimizing, and maintaining DynamoDB indexes in production environments. |
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

