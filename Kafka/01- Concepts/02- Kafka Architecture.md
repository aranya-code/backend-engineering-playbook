# Kafka Architecture

## Overview

Apache Kafka is built as a distributed system where multiple servers work together to provide high availability, fault tolerance, and scalability. Unlike traditional messaging systems that rely on a single server, Kafka distributes data across multiple machines called brokers.

Understanding Kafka's architecture is essential because every Kafka operation—producing messages, consuming events, replication, and fault recovery—depends on how these components interact.

The architecture is designed around a few simple building blocks that together create one of the most scalable event streaming platforms available today.

---

# High-Level Architecture

A simplified Kafka architecture looks like this:

```text
                Producer
                    │
                    ▼
        ┌───────────────────────┐
        │     Kafka Cluster     │
        │                       │
        │  ┌─────┐ ┌─────┐ ┌─────┐
        │  │ B1  │ │ B2  │ │ B3  │
        │  └─────┘ └─────┘ └─────┘
        │        Topics          │
        └───────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   Consumer Group A      Consumer Group B
```

A producer sends messages to the Kafka cluster.

The cluster stores those messages.

Consumers retrieve messages independently.

---

# Main Components

Kafka architecture consists of several core components.

- Producers
- Consumers
- Brokers
- Topics
- Partitions
- Consumer Groups
- ZooKeeper (legacy)
- KRaft Controller (modern Kafka)

Each component has a specific responsibility.

---

# Producer

A producer is an application that publishes messages to Kafka.

Examples include:

- Order Service
- Payment Service
- Mobile Application
- IoT Device
- Web Application
- Log Collector

Example:

```text
Order Service
      │
      ▼
Kafka Topic
```

The producer does not know who will consume the message.

Its only responsibility is to send data to Kafka.

---

# Consumer

Consumers read messages from Kafka topics.

Examples:

- Email Service
- Analytics Service
- Inventory Service
- Shipping Service

```text
Kafka Topic
      │
      ▼
Inventory Service
```

Multiple consumers can read the same topic independently.

---

# Broker

A Kafka Broker is a Kafka server.

Every broker stores data and handles client requests.

Example cluster:

```text
Kafka Cluster

Broker 1

Broker 2

Broker 3
```

Responsibilities of a broker include:

- Store messages
- Serve producers
- Serve consumers
- Replicate data
- Participate in leader election

A Kafka cluster typically contains multiple brokers.

---

# Kafka Cluster

A Kafka Cluster is a collection of brokers working together.

Example:

```text
        Kafka Cluster

 ┌────────┐
 │Broker 1│
 └────────┘

 ┌────────┐
 │Broker 2│
 └────────┘

 ┌────────┐
 │Broker 3│
 └────────┘
```

Benefits of a cluster include:

- High availability
- Load balancing
- Horizontal scalability
- Fault tolerance

---

# Topic

A Topic is a logical category where related events are stored.

Examples:

```text
orders

payments

users

notifications

logs
```

Applications publish events to topics.

Consumers subscribe to topics.

Topics organize data but do not physically store it in one place.

Instead, data is divided into partitions.

---

# Partition

Each topic is divided into one or more partitions.

```text
Orders Topic

Partition 0

Partition 1

Partition 2
```

Partitions enable:

- Parallel processing
- Horizontal scaling
- High throughput

Every message belongs to exactly one partition.

---

# Offset

Every message inside a partition receives a sequential number called an offset.

```text
Partition 0

Offset 0

Offset 1

Offset 2

Offset 3

Offset 4
```

Offsets uniquely identify messages within a partition.

Consumers use offsets to keep track of what has already been processed.

---

# Consumer Group

Consumers often work together as a team.

This team is called a Consumer Group.

```text
Orders Topic

        │

Consumer Group

 ┌────────────┐
 │Consumer 1  │
 └────────────┘

 ┌────────────┐
 │Consumer 2  │
 └────────────┘
```

Kafka automatically distributes partitions among consumers in the same group.

This allows applications to process messages in parallel.

---

# Leader and Followers

Every partition has one Leader.

It may also have multiple Followers.

```text
Partition 0

Leader

↓

Follower

↓

Follower
```

The leader handles all reads and writes.

Followers continuously replicate data from the leader.

If the leader fails, one follower becomes the new leader.

This ensures high availability.

---

# Replication

Replication means storing copies of data on multiple brokers.

Example:

```text
Broker 1

Partition 0 (Leader)

↓

Broker 2

Partition 0 (Follower)

↓

Broker 3

Partition 0 (Follower)
```

Benefits:

- Data durability
- Fault tolerance
- Disaster recovery

---

# Metadata

Kafka stores metadata about:

- Topics
- Brokers
- Partitions
- Leaders
- Replicas
- Consumer Groups

Clients retrieve this metadata before producing or consuming messages.

This allows producers and consumers to communicate with the correct broker.

---

# ZooKeeper (Legacy)

Older Kafka versions relied on ZooKeeper.

ZooKeeper managed:

- Cluster metadata
- Broker registration
- Leader election
- Configuration
- Controller election

Architecture:

```text
Producer

↓

Kafka Brokers

↓

ZooKeeper
```

Modern Kafka deployments no longer require ZooKeeper.

---

# KRaft (Kafka Raft)

Modern Kafka replaces ZooKeeper with KRaft.

Architecture:

```text
Producer

↓

Kafka Brokers

↓

KRaft Controller
```

Advantages:

- Simpler deployment
- Fewer components
- Better scalability
- Faster startup
- Easier maintenance

New Kafka installations should use KRaft mode.

---

# End-to-End Message Flow

The following diagram shows the complete lifecycle of a message.

```text
Producer
    │
    ▼
Kafka Broker
    │
    ▼
Topic
    │
    ▼
Partition
    │
    ▼
Consumer Group
    │
 ┌──┴────┐
 ▼       ▼
Consumer Consumer
```

Step-by-step flow:

1. Producer creates a message.
2. Producer sends the message to a topic.
3. Kafka stores the message in a partition.
4. The leader replicates the message to follower replicas.
5. Consumers poll Kafka for new messages.
6. Kafka returns messages from the assigned partitions.
7. Consumers process the messages.
8. Consumers commit offsets after processing.

---

# How Components Work Together

```text
Producer
    │
    ▼
Kafka Cluster
    │
    ├──────────────┐
    │              │
Topic A        Topic B
    │              │
Partitions    Partitions
    │              │
Consumer      Consumer
Group A       Group B
```

Each component has a single responsibility.

Together they create a scalable and fault-tolerant messaging platform.

---

# Why Kafka Architecture Scales

Kafka scales because:

- Brokers distribute storage.
- Topics organize data.
- Partitions enable parallelism.
- Consumer Groups distribute workloads.
- Replication provides reliability.
- KRaft removes external dependencies.
- Producers and consumers remain loosely coupled.

This architecture allows Kafka clusters to process millions of events per second while maintaining reliability.

---

# Summary

Kafka architecture is built around distributed components that work together to provide reliable event streaming. Producers publish events to topics hosted by brokers. Topics are divided into partitions for scalability, while replication ensures fault tolerance. Consumers retrieve events independently through consumer groups, allowing multiple applications to process the same data efficiently. Modern Kafka deployments use KRaft instead of ZooKeeper, simplifying cluster management and improving scalability.

---

# Key Takeaways

- Kafka is a distributed event streaming platform.
- A Kafka Cluster consists of multiple brokers.
- Producers publish messages to topics.
- Topics are divided into partitions for scalability.
- Offsets uniquely identify messages within a partition.
- Consumers read messages independently.
- Consumer Groups enable parallel message processing.
- Leaders handle reads and writes, while followers replicate data.
- Replication provides durability and fault tolerance.
- Modern Kafka uses KRaft instead of ZooKeeper for cluster management.
```