# ZooKeeper vs KRaft

## Overview

For many years, Apache Kafka relied on **Apache ZooKeeper** to manage cluster metadata, broker coordination, leader election, and configuration management.

Starting with **Apache Kafka 2.8**, Kafka introduced **KRaft (Kafka Raft Metadata Mode)**, and beginning with **Kafka 4.0**, ZooKeeper was completely removed from Kafka.

Today, **all new Kafka deployments should use KRaft**.

Understanding the differences between ZooKeeper and KRaft is important because you will encounter both in documentation, interview questions, and legacy production environments.

---

# Why Did Kafka Need ZooKeeper?

Early versions of Kafka were designed to be lightweight.

Instead of implementing their own distributed coordination system, Kafka delegated cluster management to ZooKeeper.

Architecture:

```text
                Producer
                    │
                    ▼
             Kafka Brokers
                    │
                    ▼
              Apache ZooKeeper
```

ZooKeeper became the central authority for managing the Kafka cluster.

---

# Responsibilities of ZooKeeper

ZooKeeper managed several critical tasks.

- Broker registration
- Cluster metadata
- Leader election
- Controller election
- Topic configuration
- Access control metadata
- Cluster coordination

Without ZooKeeper, older Kafka clusters could not function.

---

# ZooKeeper Architecture

A typical Kafka deployment looked like this.

```text
                 Producer
                     │
                     ▼
            ┌────────────────┐
            │ Kafka Broker 1 │
            └────────────────┘
                     │
            ┌────────────────┐
            │ Kafka Broker 2 │
            └────────────────┘
                     │
            ┌────────────────┐
            │ Kafka Broker 3 │
            └────────────────┘
                     │
                     ▼
          ┌────────────────────┐
          │    ZooKeeper       │
          └────────────────────┘
```

Every broker communicated with ZooKeeper.

---

# Limitations of ZooKeeper

Although ZooKeeper was reliable, it introduced several challenges.

## Additional Infrastructure

A Kafka deployment required:

- Kafka Brokers
- ZooKeeper Servers

This increased operational complexity.

---

## More Maintenance

Administrators had to:

- Install ZooKeeper
- Configure ZooKeeper
- Monitor ZooKeeper
- Upgrade ZooKeeper
- Secure ZooKeeper

Managing two distributed systems increased operational overhead.

---

## Performance Bottleneck

As clusters became larger:

- Metadata increased.
- Controller operations became slower.
- Leader elections became more expensive.

ZooKeeper eventually became a scalability limitation.

---

## Operational Complexity

Large organizations often deployed:

```text
3 Kafka Brokers

+

3 ZooKeeper Nodes
```

or

```text
9 Kafka Brokers

+

5 ZooKeeper Nodes
```

Operating both clusters increased infrastructure costs.

---

# What is KRaft?

KRaft stands for:

```text
Kafka Raft Metadata Mode
```

Instead of relying on ZooKeeper, Kafka now stores cluster metadata internally.

Kafka brokers themselves manage metadata using the **Raft Consensus Algorithm**.

---

# KRaft Architecture

Modern Kafka deployments are much simpler.

```text
                Producer
                    │
                    ▼
        ┌──────────────────────┐
        │    Kafka Cluster     │
        │                      │
        │ Broker 1             │
        │ Broker 2             │
        │ Broker 3             │
        │ Controller Nodes     │
        └──────────────────────┘
```

No external coordination system is required.

---

# What is the Raft Algorithm?

Raft is a distributed consensus algorithm.

Its purpose is to ensure that multiple nodes agree on the same metadata.

Example:

```text
Controller 1

↓

Controller 2

↓

Controller 3

↓

Consensus
```

Only after consensus is reached does Kafka update cluster metadata.

This keeps the cluster consistent.

---

# Responsibilities of KRaft

KRaft manages everything ZooKeeper previously handled.

- Broker registration
- Cluster metadata
- Controller election
- Leader election
- Topic metadata
- Configuration management
- Metadata replication

Applications continue using Kafka exactly as before.

Only the internal architecture changes.

---

# Metadata Quorum

Instead of ZooKeeper, Kafka now maintains a metadata quorum.

```text
Metadata Controllers

Controller 1

Controller 2

Controller 3
```

These controllers replicate metadata using Raft.

---

# Broker Roles in KRaft

Kafka nodes can have different roles.

## Broker

Handles:

- Producers
- Consumers
- Message storage

```text
Broker

↓

Store Messages
```

---

## Controller

Handles:

- Metadata
- Leader election
- Cluster management

```text
Controller

↓

Manage Cluster
```

---

## Combined Mode

In development environments:

```text
Broker

+

Controller
```

can run on the same node.

Production environments often separate these roles.

---

# ZooKeeper vs KRaft

| ZooKeeper | KRaft |
|------------|--------|
| External dependency | Built into Kafka |
| Separate cluster required | No external cluster |
| More operational overhead | Simpler deployment |
| Additional monitoring | Easier monitoring |
| More complex upgrades | Simpler upgrades |
| Higher infrastructure cost | Lower infrastructure cost |
| Legacy architecture | Modern architecture |

---

# Deployment Comparison

## ZooKeeper Mode

```text
Producer

↓

Kafka Brokers

↓

ZooKeeper Cluster
```

---

## KRaft Mode

```text
Producer

↓

Kafka Brokers

↓

Metadata Controllers
```

Notice that ZooKeeper is completely removed.

---

# Why Kafka Switched to KRaft

Kafka adopted KRaft because it offers:

- Simpler deployment
- Better scalability
- Lower operational cost
- Faster controller failover
- Reduced infrastructure
- Better metadata management
- Easier upgrades

---

# Which Version Should You Learn?

For modern backend engineering:

| Kafka Version | Recommendation |
|---------------|----------------|
| Kafka 2.x | Learn ZooKeeper conceptually |
| Kafka 3.x | Understand both |
| Kafka 4.x+ | Learn KRaft in depth |

Even though ZooKeeper is no longer used, understanding it is valuable because many organizations still operate legacy Kafka clusters.

---

# Interview Perspective

A common interview question is:

> **Does Kafka still require ZooKeeper?**

Correct answer:

- Older Kafka versions required ZooKeeper.
- Kafka introduced KRaft in version 2.8.
- Kafka 4.0 completely removed ZooKeeper.
- New Kafka deployments should use KRaft.

---

# Best Practices

- Use KRaft for all new Kafka deployments.
- Understand ZooKeeper for maintaining legacy systems.
- Separate controller and broker roles in large production clusters.
- Monitor metadata quorum health.
- Keep controller nodes highly available.

---

# Common Mistakes

- Assuming ZooKeeper is still required for modern Kafka.
- Confusing brokers with controllers.
- Believing KRaft changes producer or consumer APIs.
- Ignoring controller node availability.
- Thinking ZooKeeper and KRaft can both manage the same cluster simultaneously.

---

# Summary

ZooKeeper was originally responsible for coordinating Kafka clusters, managing metadata, leader elections, and broker registration. While reliable, it increased operational complexity by requiring a separate distributed system. Kafka introduced KRaft to eliminate this dependency by managing metadata internally using the Raft consensus algorithm. Modern Kafka deployments are simpler, easier to maintain, and more scalable with KRaft, making it the recommended architecture for all new Kafka clusters.

---

# Key Takeaways

- Older Kafka versions relied on Apache ZooKeeper for cluster coordination.
- KRaft replaces ZooKeeper with an internal metadata management system.
- KRaft uses the Raft consensus algorithm to replicate metadata.
- Modern Kafka deployments no longer require ZooKeeper.
- KRaft simplifies deployment, maintenance, and scaling.
- Kafka brokers and controllers have distinct responsibilities in KRaft mode.
- Kafka 4.0 completely removed ZooKeeper support.
- Learn ZooKeeper for legacy systems, but focus on KRaft for modern backend engineering.