# Multi Broker Cluster

## Overview

A single Kafka broker is sufficient for learning the basics of Kafka, but it does not represent how Kafka is used in production. Real-world Kafka deployments run as **clusters of multiple brokers** to achieve high availability, scalability, fault tolerance, and better performance.

A **Kafka Cluster** consists of multiple brokers working together to store and replicate data. Topics are divided into partitions, and these partitions are distributed across brokers. If one broker fails, another broker can continue serving client requests.

Running a multi-broker cluster locally using Docker Compose is an excellent way to understand Kafka's distributed architecture before deploying production systems.

---

# Why Multiple Brokers?

Suppose there is only one broker.

```text
Producer

↓

Broker

↓

Consumer
```

If the broker crashes:

```text
Broker Offline

↓

Kafka Unavailable
```

All producers and consumers stop working.

---

Now consider three brokers.

```text
Producer

↓

Broker 1

↓

Broker 2

↓

Broker 3

↓

Consumer
```

If one broker fails:

```text
Broker 2

↓

Offline

↓

Broker 1 & Broker 3 Continue
```

Kafka remains available.

---

# What is a Kafka Cluster?

A Kafka Cluster is a collection of brokers that work together.

Example:

```text
Kafka Cluster

├── Broker 1
├── Broker 2
└── Broker 3
```

Clients connect to the cluster rather than an individual broker.

---

# Multi Broker Architecture

```text
                    Producer
                        │
                        ▼
                 Kafka Cluster
      ┌────────────┬────────────┬────────────┐
      ▼            ▼            ▼
 Broker 1      Broker 2      Broker 3
      │            │            │
      └────────────┼────────────┘
                   ▼
               Consumers
```

Each broker stores a portion of the data.

---

# Why Brokers Share Data

Suppose:

```text
Orders Topic

↓

12 Partitions
```

Instead of storing all partitions on one broker:

```text
Broker 1

P0

P3

P6

P9

----------------

Broker 2

P1

P4

P7

P10

----------------

Broker 3

P2

P5

P8

P11
```

Workload is distributed evenly.

---

# Replication

Kafka protects data using replication.

Example:

```text
Partition 0

Leader

↓

Broker 1

Followers

↓

Broker 2

Broker 3
```

If Broker 1 fails:

```text
Broker 2

↓

Leader
```

Processing continues.

---

# Cluster Components

A production cluster typically includes:

- Multiple Brokers
- KRaft Controller (or ZooKeeper in older versions)
- Topics
- Partitions
- Replicas
- Producers
- Consumers

---

# Docker Compose Architecture

A local multi-broker environment might contain:

```text
Docker Compose

├── Broker 1
├── Broker 2
├── Broker 3
└── Kafka UI
```

All containers communicate over the same Docker network.

---

# Broker IDs

Every broker has a unique identifier.

Example:

```text
Broker 1

Broker 2

Broker 3
```

These IDs help Kafka identify brokers within the cluster.

---

# Bootstrap Servers

Applications connect using one or more bootstrap servers.

Example:

```properties
bootstrap.servers=broker1:9092,broker2:9092,broker3:9092
```

Kafka discovers the remaining brokers automatically.

Only one reachable broker is required to establish a connection.

---

# Partition Distribution

Suppose:

```text
Topic

6 Partitions
```

Kafka distributes them:

```text
Broker 1

P0

P3

----------------

Broker 2

P1

P4

----------------

Broker 3

P2

P5
```

No broker stores every partition.

---

# Leader Distribution

Each partition has exactly one leader.

Example:

```text
Broker 1

Leader

P0

P4

----------------

Broker 2

Leader

P1

P5

----------------

Broker 3

Leader

P2

P3
```

Leadership is spread across brokers to balance load.

---

# Producer Workflow

```text
Producer

↓

Bootstrap Server

↓

Cluster Metadata

↓

Partition Leader

↓

Write Message
```

The producer communicates directly with the partition leader.

---

# Consumer Workflow

```text
Consumer

↓

Bootstrap Server

↓

Metadata

↓

Partition Leader

↓

Read Records
```

Consumers also communicate directly with leaders.

---

# Broker Failure

Suppose:

```text
Broker 2

↓

Offline
```

Kafka detects the failure.

```text
Follower Replica

↓

Leader Election

↓

Continue Processing
```

Clients reconnect automatically.

---

# Scaling the Cluster

Suppose the workload increases.

Before:

```text
3 Brokers
```

After:

```text
5 Brokers
```

New partitions can be distributed across additional brokers.

This increases storage capacity and throughput.

---

# Broker Communication

Brokers continuously exchange metadata.

```text
Broker 1

↔

Broker 2

↔

Broker 3
```

They coordinate:

- Replication
- Leader election
- Cluster metadata
- Health monitoring

---

# Docker Network

Compose automatically creates a shared network.

```text
Broker 1

↓

Docker Network

↓

Broker 2

↓

Broker 3

↓

Kafka UI
```

Containers communicate using service names.

---

# Viewing the Cluster

Kafka UI displays:

- Brokers
- Topics
- Partitions
- Leaders
- Replicas
- Consumer Groups

This provides an excellent visualization of cluster health.

---

# Typical Development Workflow

```text
Start Docker Compose

↓

Start Three Brokers

↓

Create Topic

↓

Produce Messages

↓

Consume Messages

↓

View Cluster in Kafka UI
```

This closely resembles a production deployment.

---

# Advantages of a Multi-Broker Cluster

- High availability
- Fault tolerance
- Better scalability
- Higher throughput
- Distributed storage
- Load balancing
- Production-like environment

---

# Limitations

- More containers to manage.
- Higher memory consumption.
- More complex networking.
- Requires additional configuration.

These trade-offs are worthwhile for learning distributed Kafka behavior.

---

# Best Practices

- Use at least three brokers when learning replication.
- Distribute partition leaders evenly.
- Configure an appropriate replication factor.
- Monitor broker health continuously.
- Use Docker Compose for local clusters.
- Test broker failures regularly.
- Keep broker configurations consistent.

---

# Common Mistakes

- Running all partitions on a single broker.
- Assuming one broker is representative of production.
- Forgetting to configure replication.
- Connecting applications to only one hardcoded broker.
- Ignoring broker failures during testing.
- Using insufficient system resources for multiple brokers.

---

# Summary

A multi-broker Kafka cluster provides the scalability, reliability, and fault tolerance that make Kafka suitable for production workloads. By distributing partitions across brokers, replicating data, and automatically electing new leaders during failures, Kafka continues operating even when individual brokers become unavailable. Running a multi-broker cluster locally with Docker Compose gives developers valuable hands-on experience with Kafka's distributed architecture and prepares them for real-world deployments.

---

# Key Takeaways

- Production Kafka deployments consist of multiple brokers.
- Brokers work together as a Kafka Cluster.
- Partitions are distributed across brokers for scalability.
- Replication protects data from broker failures.
- Producers and consumers connect using bootstrap servers.
- Leader election enables automatic recovery after failures.
- Docker Compose makes it easy to simulate production-like clusters locally.
- Understanding multi-broker architecture is essential for designing reliable Kafka systems.