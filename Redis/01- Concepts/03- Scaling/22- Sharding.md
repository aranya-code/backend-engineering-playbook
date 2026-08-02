# Sharding

## Overview

As applications grow, the amount of data they generate eventually exceeds the capacity of a single Redis server. Even the largest machines have limits on memory, CPU, and network bandwidth. At this point, simply upgrading the hardware (vertical scaling) becomes expensive and inefficient.

**Sharding** is a technique for distributing data across multiple Redis servers, allowing the database to scale horizontally. Instead of storing every key on one machine, each server stores only a subset of the total dataset.

Sharding is one of the most important concepts in distributed databases and forms the foundation of Redis Cluster. While Redis Cluster automates sharding, understanding the concept itself is essential for designing scalable distributed systems.

---

# Why Sharding?

Imagine an application with:

- 500 million users
- 5 billion cache entries
- 10 TB of data

A single Redis server might have:

```
Memory

↓

512 GB
```

The dataset simply cannot fit into one machine.

Instead:

```
10 TB

↓

Multiple Redis Servers
```

The workload is distributed.

---

# The Problem with a Single Server

Traditional architecture:

```
          Application

                │

          +-----v-----+

          |   Redis   |

          +-----------+
```

Everything depends on one server.

Limitations include:

- Limited memory
- CPU bottleneck
- Network saturation
- Single write bottleneck

---

# What is Sharding?

Sharding divides a large dataset into smaller pieces.

Each piece is called a **Shard**.

Example:

```
Entire Dataset

↓

Shard A

Shard B

Shard C

Shard D
```

Each shard is stored on a different Redis server.

---

# Conceptual Architecture

```
                 Application

                      │

         +------------+------------+

         │                         │

      Router / Client

         │

+--------+--------+--------+--------+

│                 │                 │

Shard A       Shard B          Shard C

Redis 1       Redis 2          Redis 3
```

Instead of one large server, multiple smaller servers work together.

---

# Data Distribution

Suppose we have users:

```
User1

User2

User3

User4

User5

User6
```

Sharded storage:

```
Redis 1

↓

User1

User2
```

```
Redis 2

↓

User3

User4
```

```
Redis 3

↓

User5

User6
```

Each server stores only part of the dataset.

---

# Benefits of Sharding

Sharding provides:

- More memory
- More CPU capacity
- Higher throughput
- Better scalability
- Reduced server load

Instead of:

```
1 Server

↓

100%
```

We have:

```
4 Servers

↓

25% Each
```

---

# Horizontal Scaling

Vertical Scaling:

```
More RAM

↓

Bigger CPU

↓

Bigger Server
```

Horizontal Scaling:

```
Server A

+

Server B

+

Server C

+

Server D
```

Horizontal scaling is usually more cost-effective.

---

# Types of Sharding

There are two major approaches.

```
Sharding

↓

Manual

↓

Automatic
```

---

# Manual Sharding

The application decides where data should be stored.

Example:

```
Application

↓

Customer ID

↓

Redis Server
```

The application contains the routing logic.

Advantages:

- Simple architecture
- Complete control

Disadvantages:

- Difficult maintenance
- Complex scaling
- Manual data migration

---

# Automatic Sharding

Redis Cluster performs sharding automatically.

```
Application

↓

Cluster

↓

Correct Redis Node
```

Applications no longer need custom routing logic.

This is the preferred production approach.

---

# Hash-Based Sharding

The most common strategy.

```
Key

↓

Hash Function

↓

Shard
```

Example:

```
User100

↓

Hash

↓

Redis 2
```

Every key consistently maps to the same server.

---

# Range-Based Sharding

Data is divided by ranges.

Example:

```
User IDs

1–10000

↓

Shard A
```

```
10001–20000

↓

Shard B
```

Simple but can lead to uneven load if one range is much more active than others.

---

# Directory-Based Sharding

A lookup service stores the location of each key.

```
Key

↓

Directory

↓

Redis Node
```

Advantages:

- Flexible

Disadvantages:

- Extra lookup
- Additional infrastructure
- Single point of failure if not replicated

---

# Consistent Hashing

Traditional hashing has a drawback.

Suppose:

```
3 Servers
```

One server is added.

```
4 Servers
```

Most keys need to move.

Consistent Hashing minimizes this movement.

Conceptually:

```
Hash Ring

↓

Server A

↓

Server B

↓

Server C
```

Adding a new server only affects nearby keys.

This approach is widely used in distributed systems.

---

# Rebalancing

As the cluster grows:

```
New Server

↓

Redistributes Data
```

Example:

Before:

```
Server A

50%
```

```
Server B

50%
```

After:

```
Server A

33%
```

```
Server B

33%
```

```
Server C

34%
```

This process is called **Rebalancing**.

---

# Replication with Sharding

Production systems rarely use only sharding.

Instead:

```
Primary A

↓

Replica A
```

```
Primary B

↓

Replica B
```

```
Primary C

↓

Replica C
```

Each shard has one or more replicas.

This provides:

- Fault tolerance
- High availability
- Automatic failover

---

# Query Routing

When an application requests a key:

```
Application

↓

Hash Function

↓

Correct Shard

↓

Redis Server
```

Modern Redis clients perform this automatically.

---

# Hot Keys

One challenge of sharding is the **Hot Key** problem.

Suppose:

```
Celebrity Profile

↓

Millions of Requests
```

Even though data is distributed:

```
One Shard

↓

Heavy Load
```

That server becomes a bottleneck.

Solutions include:

- Replication
- Local caching
- Request throttling
- Data partitioning

---

# Uneven Data Distribution

Poor hash functions can create imbalance.

```
Shard A

80%
```

```
Shard B

10%
```

```
Shard C

10%
```

This wastes resources.

Good hashing algorithms distribute keys evenly.

---

# Cross-Shard Operations

Suppose:

```
User Data

↓

Shard A
```

```
Orders

↓

Shard B
```

Joining data across shards becomes expensive.

Applications should design data models to minimize cross-shard operations.

---

# Advantages

Sharding offers many benefits.

- Horizontal scalability
- Larger datasets
- Higher throughput
- Better resource utilization
- Lower infrastructure costs
- Improved fault isolation

---

# Challenges

Sharding introduces complexity.

- Data distribution
- Cross-shard queries
- Rebalancing
- Monitoring
- Operational overhead
- Backup strategies
- Data migration

Applications must be designed carefully.

---

# Sharding vs Replication

| Feature | Sharding | Replication |
|----------|-----------|-------------|
| Goal | Scale Capacity | Improve Availability |
| Data Stored | Partial | Complete Copy |
| Horizontal Scaling | Yes | No |
| Failover | No | Yes |
| More Memory | Yes | No |

Sharding increases capacity.

Replication increases resilience.

---

# Sharding vs Redis Cluster

| Feature | Manual Sharding | Redis Cluster |
|----------|----------------|---------------|
| Routing | Application | Automatic |
| Failover | Manual | Automatic |
| Scaling | Manual | Automatic |
| Hash Slots | No | Yes |
| Client Complexity | High | Low |

Redis Cluster is essentially automated sharding with built-in high availability.

---

# Common Production Use Cases

Sharding is widely used in:

- Social media platforms
- E-commerce websites
- Banking applications
- Gaming platforms
- Recommendation engines
- IoT platforms
- Analytics systems
- Streaming services
- AI feature stores
- SaaS platforms

---

# Common Mistakes

## Uneven Key Distribution

Improper hashing leads to overloaded shards.

Monitor key distribution continuously.

---

## Ignoring Hot Keys

One heavily accessed key can overload a single shard.

Use replication or caching to distribute read traffic.

---

## Excessive Cross-Shard Queries

Frequent cross-shard operations reduce performance.

Keep related data together whenever possible.

---

## Manual Routing Logic

Hardcoding shard locations increases maintenance costs.

Prefer automated solutions like Redis Cluster.

---

# Best Practices

- Use automatic sharding whenever possible.
- Choose a good hashing strategy.
- Monitor shard utilization.
- Plan for future growth.
- Minimize cross-shard operations.
- Replicate every shard.
- Test rebalancing procedures before production.

---

# Production Considerations

When deploying sharded Redis environments:

- Monitor memory usage per shard.
- Balance data evenly across nodes.
- Track hot keys and skewed workloads.
- Use cluster-aware clients.
- Regularly validate replication health.
- Automate backups for every shard.
- Test node failures and recovery procedures.

---

# Sharding in Microservice Architecture

```
                 API Gateway
                      │
        +-------------+-------------+
        │                           │
   User Service              Order Service
        │                           │
        +-------------+-------------+
                      │
                Redis Cluster
                      │
      +---------------+---------------+
      │               │               │
   Shard A         Shard B         Shard C
      │               │               │
  Replica A       Replica B       Replica C
```

Each microservice accesses the Redis Cluster through a cluster-aware client. The client automatically routes requests to the appropriate shard based on the key's hash slot, allowing the system to scale horizontally without application-level routing logic.

---

# Summary

Sharding is a fundamental scaling technique that distributes data across multiple Redis servers, enabling applications to store larger datasets and process higher workloads than a single machine can support. While manual sharding requires application-level routing and operational complexity, Redis Cluster automates data partitioning, routing, rebalancing, and failover. Understanding sharding is essential for designing scalable distributed systems, even when Redis Cluster handles most of the implementation details.

---

# Key Takeaways

- Sharding distributes data across multiple Redis servers.
- It enables horizontal scaling of memory, CPU, and throughput.
- Hash-based sharding is the most common distribution strategy.
- Redis Cluster provides automatic sharding using **16,384 hash slots**.
- Replication complements sharding by providing high availability.
- Monitor for hot keys, uneven distribution, and cross-shard operations.
- Sharding is the foundation of large-scale Redis deployments.
