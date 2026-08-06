# Kafka Topics

Topics are the central abstraction in Apache Kafka. Every message produced to Kafka is written to a topic, and every consumer reads messages from one or more topics. Well-designed topics form the foundation of scalable, maintainable, and event-driven systems.

Designing Kafka topics involves much more than simply creating a topic. Decisions such as topic naming, partition strategy, retention policies, and log compaction directly impact scalability, throughput, storage requirements, consumer behavior, and long-term maintainability.

This section covers the architectural principles and best practices required to design production-ready Kafka topics.

---

# Folder Structure

```text
04-Topics/
│
├── 01- Topic Design.md
├── 02- Naming Conventions.md
├── 03- Partition Strategy.md
├── 04- Retention Strategy.md
├── 05- Compacted Topics.md
└── README.md
```

---

# Navigation

## Topic Design

- [01- Topic Design](./01-%20Topic%20Design.md)
- [02- Naming Conventions](./02-%20Naming%20Conventions.md)

---

## Topic Architecture

- [03- Partition Strategy](./03-%20Partition%20Strategy.md)

---

## Data Retention & Storage

- [04- Retention Strategy](./04-%20Retention%20Strategy.md)
- [05- Compacted Topics](./05-%20Compacted%20Topics.md)

---

# Learning Path

Study the chapters in the following order:

```text
Topic Design
      │
      ▼
Naming Conventions
      │
      ▼
Partition Strategy
      │
      ▼
Retention Strategy
      │
      ▼
Compacted Topics
```

Each chapter builds upon the previous one, progressing from topic modeling to storage optimization.

---

# Topics Covered

This section explains:

- Designing Kafka topics around business domains
- Topic naming standards
- Partition planning and scalability
- Message distribution strategies
- Retention policies
- Time-based and size-based retention
- Storage planning
- Log compaction
- Tombstone records
- State-based topics

---

# Prerequisites

Before studying this section, you should understand:

- Kafka Architecture
- Brokers
- Topics
- Partitions
- Offsets
- Producers
- Consumers

---

# Skills You'll Gain

After completing this section, you will be able to:

- Design Kafka topics for production systems.
- Create meaningful topic naming conventions.
- Choose appropriate partition counts.
- Select effective partition keys.
- Design scalable event streams.
- Configure retention policies.
- Estimate Kafka storage requirements.
- Decide when to use Log Compaction.
- Build topics for event sourcing and state management.
- Design maintainable Kafka architectures.

---

# Real-World Applications

The concepts in this section are used in:

- Event-Driven Microservices
- E-commerce Platforms
- Banking Systems
- Payment Processing
- Inventory Management
- Audit Logging
- Event Sourcing
- Configuration Management
- IoT Platforms
- Streaming Analytics
- Distributed State Management

---

# Best Practices

- Design topics around business domains rather than database tables.
- Use meaningful and consistent topic names.
- Plan partition strategy before production deployment.
- Choose message keys carefully to preserve ordering and distribute load.
- Configure retention based on business and compliance requirements.
- Use Log Compaction only for state-oriented data.
- Estimate storage requirements before increasing retention periods.
- Document every topic with ownership, schema, and retention settings.
- Monitor topic growth and partition distribution over time.
- Design topics with future scalability in mind.

---

# Common Mistakes

- Creating generic topics such as `events` or `data`.
- Using inconsistent naming conventions.
- Choosing arbitrary partition counts.
- Using poor partition keys that create hot partitions.
- Confusing Retention with Log Compaction.
- Using compacted topics for immutable event streams.
- Ignoring storage planning.
- Frequently changing topic names in production.
- Designing topics around technical implementations instead of business events.
- Failing to document topic ownership and purpose.

---

# Summary

Kafka Topics are the foundation of every Kafka-based application. Proper topic design determines how events are organized, distributed, retained, and consumed throughout the system. By understanding topic architecture, naming conventions, partition strategy, retention policies, and log compaction, you can build scalable, maintainable, and production-ready event streaming platforms that support high throughput, efficient storage, and reliable data processing.