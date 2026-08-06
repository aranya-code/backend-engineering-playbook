# Brokers

## Overview

A **Kafka Broker** is a server that stores, manages, and serves Kafka data. Every Kafka cluster consists of one or more brokers working together to provide scalability, fault tolerance, and high availability.

When a producer sends a message, it is written to a broker. When a consumer requests messages, it reads them from a broker. In other words, brokers are the backbone of every Kafka deployment.

As applications grow, additional brokers can be added to the cluster, allowing Kafka to scale horizontally with minimal disruption.

---

# What is a Broker?

A broker is a Kafka server responsible for:

- Receiving messages from producers
- Storing messages on disk
- Serving messages to consumers
- Replicating data
- Managing partitions
- Participating in leader elections

A broker runs as an independent process.

Example:

```text
Producer

      │

      ▼

Kafka Broker

      │

      ▼

Store Messages
```

---

# Single Broker Cluster

A small development environment often consists of a single broker.

```text
Kafka Cluster

┌───────────────────┐
│ Broker 1          │
│                   │
│ Orders Topic      │
│ Payments Topic    │
│ Users Topic       │
└───────────────────┘
```

This setup is suitable for:

- Learning
- Development
- Testing

However, it provides no fault tolerance.

---

# Multi-Broker Cluster

Production systems typically use multiple brokers.

```text
                 Kafka Cluster

┌──────────┐   ┌──────────┐   ┌──────────┐
│ Broker 1 │   │ Broker 2 │   │ Broker 3 │
└──────────┘   └──────────┘   └──────────┘
```

Advantages include:

- High availability
- Fault tolerance
- Better performance
- Horizontal scaling

---

# Broker Responsibilities

A Kafka broker performs several critical tasks.

## Store Messages

The broker persists messages on disk.

```text
Producer

↓

Broker

↓

Disk Storage
```

Kafka is designed for disk-based storage rather than in-memory storage.

---

## Serve Producers

Producers send messages directly to brokers.

```text
Producer

↓

Broker
```

The broker validates and stores incoming messages.

---

## Serve Consumers

Consumers request messages from brokers.

```text
Consumer

↓

Broker

↓

Messages
```

The broker retrieves messages from the appropriate partition.

---

## Manage Partitions

A broker owns one or more partitions.

Example:

```text
Broker 1

Orders P0

Orders P3

Payments P1
```

Different brokers manage different partitions.

---

## Replicate Data

Brokers replicate partitions to one another.

```text
Broker 1

Leader

↓

Broker 2

Follower

↓

Broker 3

Follower
```

Replication protects against broker failures.

---

# Broker IDs

Each broker has a unique identifier.

Example:

```text
Broker 1

ID = 1

----------------

Broker 2

ID = 2

----------------

Broker 3

ID = 3
```

Kafka uses Broker IDs internally when managing the cluster.

---

# Brokers and Topics

A topic is distributed across brokers.

Example:

```text
Orders Topic

Partition 0

↓

Broker 1

--------------------

Partition 1

↓

Broker 2

--------------------

Partition 2

↓

Broker 3
```

No single broker necessarily stores the entire topic.

---

# Brokers and Partitions

A broker can own many partitions.

```text
Broker 1

Orders P0

Orders P4

Payments P2

Logs P1
```

Similarly, one topic can span multiple brokers.

---

# Producer Communication

How does a producer know where to send a message?

Step 1

The producer connects to any broker.

```text
Producer

↓

Broker
```

Step 2

The broker returns cluster metadata.

```text
Topics

Partitions

Leaders
```

Step 3

The producer sends messages directly to the leader broker responsible for the target partition.

---

# Consumer Communication

Consumers also retrieve metadata.

```text
Consumer

↓

Broker

↓

Metadata
```

Kafka tells the consumer:

- Which broker is the leader
- Which partitions belong to the consumer
- Where messages are stored

The consumer then communicates directly with the correct broker.

---

# Broker Failure

Suppose Broker 2 crashes.

Before failure:

```text
Broker 1

Leader

----------------

Broker 2

Leader

----------------

Broker 3

Follower
```

After failure:

```text
Broker 1

Leader

----------------

Broker 2

Offline

----------------

Broker 3

New Leader
```

Kafka automatically elects a new leader from the available replicas.

Applications continue working with minimal interruption.

---

# Adding More Brokers

Kafka scales horizontally.

Example:

Before:

```text
Broker 1

Broker 2
```

After:

```text
Broker 1

Broker 2

Broker 3

Broker 4

Broker 5
```

As new brokers join:

- New partitions can be assigned.
- Storage capacity increases.
- Network traffic is distributed.
- Processing capacity improves.

---

# Broker Storage

Kafka stores messages on disk.

Example:

```text
Broker

↓

Topic

↓

Partition

↓

Log Files
```

Each partition is stored as a sequence of append-only log files.

This design provides excellent write performance.

---

# Brokers and KRaft

Modern Kafka clusters use **KRaft** instead of ZooKeeper.

```text
Producer

↓

Broker

↓

KRaft Controller
```

KRaft manages:

- Cluster metadata
- Broker registration
- Leader election
- Controller management

This simplifies Kafka deployments.

---

# Broker vs Cluster

| Broker | Cluster |
|----------|----------|
| Single Kafka server | Collection of brokers |
| Stores partitions | Stores all topics collectively |
| Handles client requests | Provides scalability and fault tolerance |
| Has a unique Broker ID | Has multiple Broker IDs |

---

# Best Practices

- Use at least three brokers in production.
- Distribute partitions evenly.
- Monitor broker health.
- Enable replication.
- Avoid storing all partitions on one broker.
- Monitor disk usage and network utilization.
- Plan for future scaling.

---

# Common Mistakes

- Running production with only one broker.
- Uneven partition distribution.
- Ignoring broker disk space.
- Assuming brokers store complete topics.
- Not configuring replication.
- Overloading a single broker.

---

# Summary

A Kafka broker is a server responsible for storing, managing, and serving Kafka data. Brokers receive messages from producers, store them in partitions, serve them to consumers, and replicate data across the cluster for fault tolerance. Multiple brokers form a Kafka cluster, allowing Kafka to scale horizontally while maintaining high availability and reliability.

---

# Key Takeaways

- A broker is a Kafka server.
- Brokers store partitions and manage client requests.
- A Kafka cluster consists of multiple brokers.
- Topics are distributed across brokers.
- Producers and consumers communicate with brokers.
- Brokers replicate data for fault tolerance.
- Kafka automatically handles broker failures through leader election.
- Adding brokers increases storage capacity and processing scalability.
- Modern Kafka deployments use KRaft for cluster management.
- Brokers are the foundation of Kafka's distributed architecture.