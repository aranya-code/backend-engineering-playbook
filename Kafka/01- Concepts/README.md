# Kafka Concepts

Master the core concepts of **Apache Kafka**, the distributed event streaming platform used to build scalable, fault-tolerant, and real-time data pipelines.

This section introduces the fundamental building blocks of Kafka, including topics, partitions, brokers, producers, consumers, replication, delivery guarantees, message ordering, retention, log compaction, and modern Kafka architecture with KRaft.

These concepts form the foundation for everything that follows, including Kafka CLI, Python applications, production deployments, and event-driven microservices.

---

# Folder Structure

```text
01- Concepts
│
├── 01- Introduction.md
├── 02- Kafka Architecture.md
├── 03- Topics.md
├── 04- Partitions.md
├── 05- Offsets.md
├── 06- Producers.md
├── 07- Consumers.md
├── 08- Consumer Groups.md
├── 09- Message Keys.md
├── 10- Brokers.md
├── 11- Leaders, Followers & ISR.md
├── 12- Replication.md
├── 13- Delivery Guarantees.md
├── 14- Message Ordering.md
├── 15- Log Segments.md
├── 16- Retention Policies.md
├── 17- Log Compaction.md
├── 18- ZooKeeper vs KRaft.md
└── README.md
```

---

# Learning Path

Read the chapters in the following order.

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [01- Introduction.md](01-%20Introduction.md) | Introduction to Apache Kafka and event streaming. |
| 2 | [02- Kafka Architecture.md](02-%20Kafka%20Architecture.md) | Understand how Kafka components work together. |
| 3 | [03- Topics.md](03-%20Topics.md) | Learn what Kafka topics are and how data is organized. |
| 4 | [04- Partitions.md](04-%20Partitions.md) | Understand scalability through partitioning. |
| 5 | [05- Offsets.md](05-%20Offsets.md) | Learn how Kafka tracks messages and consumer progress. |
| 6 | [06- Producers.md](06-%20Producers.md) | Learn how applications publish messages to Kafka. |
| 7 | [07- Consumers.md](07-%20Consumers.md) | Learn how applications read and process messages. |
| 8 | [08- Consumer Groups.md](08-%20Consumer%20Groups.md) | Understand horizontal scaling and workload distribution. |
| 9 | [09- Message Keys.md](09-%20Message%20Keys.md) | Learn how Kafka determines partitions and preserves ordering. |
| 10 | [10- Brokers.md](10-%20Brokers.md) | Understand Kafka servers and cluster architecture. |
| 11 | [11- Leaders, Followers & ISR.md](11-%20Leaders,%20Followers%20&%20ISR.md) | Learn Kafka replication and leader election. |
| 12 | [12- Replication.md](12-%20Replication.md) | Deep dive into fault tolerance and high availability. |
| 13 | [13- Delivery Guarantees.md](13-%20Delivery%20Guarantees.md) | Understand At Most Once, At Least Once, and Exactly Once semantics. |
| 14 | [14- Message Ordering.md](14-%20Message%20Ordering.md) | Learn how Kafka guarantees ordering within partitions. |
| 15 | [15- Log Segments.md](15-%20Log%20Segments.md) | Explore Kafka's storage engine and log structure. |
| 16 | [16- Retention Policies.md](16-%20Retention%20Policies.md) | Learn how Kafka manages message lifecycle. |
| 17 | [17- Log Compaction.md](17-%20Log%20Compaction.md) | Understand stateful topics and compaction. |
| 18 | [18- ZooKeeper vs KRaft.md](18-%20ZooKeeper%20vs%20KRaft.md) | Learn the evolution from ZooKeeper to KRaft. |

---

# Concepts Covered

After completing this section, you will understand:

- Event Streaming fundamentals
- Kafka Architecture
- Topics and Partitions
- Producers and Consumers
- Consumer Groups
- Brokers
- Message Keys
- Offsets
- Replication
- Leaders, Followers, and ISR
- Delivery Guarantees
- Message Ordering
- Log Segments
- Retention Policies
- Log Compaction
- ZooKeeper
- KRaft Architecture

---

# Prerequisites

Before starting these notes, you should have:

- Basic programming knowledge
- Familiarity with APIs
- Basic understanding of distributed systems (helpful but not required)

No prior Kafka experience is required.

---

# After Completing This Section

You will be ready to learn:

- Kafka CLI
- Topic Administration
- Producer & Consumer Commands
- Broker Management
- Python Kafka Development
- FastAPI + Kafka Integration
- Django + Kafka Integration
- Event-Driven Microservices
- Production Kafka Deployments

---

# Recommended Reading Strategy

For each chapter:

1. Read the theory carefully.
2. Study the diagrams.
3. Understand the real-world examples.
4. Relate each concept to distributed systems you already know.
5. Continue to the Kafka CLI section and practice the concept immediately.

Combining theory with hands-on practice is the fastest way to become proficient with Kafka.

---

# Key Takeaways

- This section builds the conceptual foundation of Apache Kafka.
- Topics, partitions, brokers, producers, and consumers are the core building blocks.
- Replication and ISR provide fault tolerance.
- Offsets and consumer groups enable scalable message processing.
- Delivery guarantees and message ordering determine application reliability.
- Log segments, retention, and compaction explain Kafka's storage model.
- KRaft is the modern architecture replacing ZooKeeper.
- Mastering these concepts makes the CLI, Python APIs, and production deployments much easier to understand.