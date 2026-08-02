# Redis Cluster

## Overview

As applications grow, a single Redis server eventually becomes a bottleneck. Even with replication and Sentinel providing high availability, every piece of data still resides on one Primary node. CPU, memory, and network bandwidth are limited by that single machine.

Redis Cluster solves this problem by distributing data across **multiple Redis nodes**, enabling horizontal scaling while also providing high availability through automatic failover.

Unlike Redis Sentinel, which focuses only on availability, Redis Cluster provides both:

- Horizontal scaling
- Automatic failover

Redis Cluster is designed for large-scale production systems handling millions of keys, high request throughput, and datasets that exceed the memory capacity of a single server.

---

# Why Redis Cluster?

Consider an application with:

- 500 million users
- 2 TB of cached data
- Millions of requests per second

A single Redis server may have:

```
Memory

↓

256 GB
```

The dataset cannot fit into one machine.

Redis Cluster distributes data across multiple servers.

---

# The Problem with a Single Redis Server

Traditional deployment:

```
            Application
                  │
                  │
             +----v----+
             |  Redis  |
             +---------+
```

Everything is stored on one machine.

Limitations:

- Memory limit
- CPU limit
- Network limit
- Single write bottleneck

Scaling vertically eventually becomes expensive.

---

# Horizontal Scaling

Instead of buying a larger server:

```
Server A

+

Server B

+

Server C

+

Server D
```

Each server stores part of the dataset.

```
Total Capacity

=

Sum of All Servers
```

---

# What is Redis Cluster?

Redis Cluster partitions data across multiple Redis nodes.

```
Application

↓

Redis Cluster

↓

Node A

Node B

Node C

Node D
```

Every node owns only a subset of the data.

---

# Data Partitioning

Suppose the application stores:

```
User 1

User 2

User 3

User 4

User 5
```

Instead of placing everything on one server:

```
Node A

↓

User 1

User 2
```

```
Node B

↓

User 3
```

```
Node C

↓

User 4

User 5
```

Each node stores only part of the data.

---

# Hash Slots

Redis Cluster does **not** distribute keys randomly.

Instead, every key belongs to one of:

```
16,384 Hash Slots
```

Conceptually:

```
Key

↓

Hash Function

↓

Hash Slot

↓

Redis Node
```

The slot determines where the key is stored.

---

# Slot Distribution

Suppose a cluster contains four nodes.

```
Node A

↓

Slots

0–4095
```

```
Node B

↓

4096–8191
```

```
Node C

↓

8192–12287
```

```
Node D

↓

12288–16383
```

Every slot belongs to exactly one Primary node.

---

# Key Placement

Example:

```
user:100

↓

Hash

↓

Slot 3520

↓

Node A
```

Another key:

```
product:500

↓

Hash

↓

Slot 9800

↓

Node C
```

Applications do not calculate this manually.

Redis clients perform routing automatically.

---

# Cluster Architecture

A production Redis Cluster:

```
                 Application
                      │
          +-----------+-----------+
          │                       │
     Redis Client          Cluster Metadata
                      │
     +----------------+----------------+
     │        │        │        │
+----v----+ +--v---+ +--v---+ +--v---+
|Primary A| |Primary B| |Primary C| |Primary D|
+----+----+ +----+----+ +----+----+ +----+----+
     │            │            │            │
+----v----+ +----v----+ +----v----+ +----v----+
|Replica A| |Replica B| |Replica C| |Replica D|
+---------+ +---------+ +---------+ +---------+
```

Every Primary typically has at least one Replica.

---

# Automatic Failover

Suppose:

```
Primary B

↓

Crash
```

Redis Cluster detects the failure.

```
Replica B

↓

Promoted

↓

New Primary
```

Applications continue working.

---

# Cluster Topology

Each node knows about every other node.

```
Node A

↓

Node B

↓

Node C

↓

Node D
```

This peer-to-peer architecture eliminates a central coordinator.

---

# Cluster Communication

Nodes exchange heartbeat messages.

```
Node A

↓

PING

↓

Node B
```

```
Node B

↓

PONG
```

This allows nodes to detect failures quickly.

---

# Client Communication

Applications connect to any cluster node.

```
Application

↓

Redis Node
```

If the requested key belongs elsewhere:

```
Redirect

↓

Correct Node
```

Modern Redis client libraries handle these redirects transparently.

---

# Rebalancing

As data grows, new servers can be added.

Before:

```
Node A

50%

Node B

50%
```

After adding another node:

```
Node A

33%

Node B

33%

Node C

34%
```

Hash slots are redistributed.

This process is called **rebalancing**.

---

# Scaling Out

```
Cluster

↓

4 Nodes

↓

Add 2 Nodes

↓

6 Nodes
```

Memory and throughput increase without replacing existing hardware.

---

# Scaling In

Unused servers can also be removed.

```
Node Removed

↓

Slots Migrated

↓

Cluster Continues
```

This flexibility makes Redis Cluster suitable for cloud environments.

---

# Cross-Slot Operations

One limitation of Redis Cluster:

Suppose:

```
Key A

↓

Node A
```

```
Key B

↓

Node C
```

Certain multi-key operations cannot execute because the keys reside on different nodes.

Redis refers to this as a **Cross-Slot** operation.

---

# Hash Tags

Redis provides **Hash Tags** to place related keys in the same slot.

Conceptually:

```
order:{100}:items

order:{100}:status

order:{100}:payment
```

All keys containing the same hash tag:

```
{100}
```

are stored on the same node.

This allows multi-key operations on related data.

---

# Cluster vs Sentinel

| Feature | Redis Cluster | Redis Sentinel |
|----------|---------------|----------------|
| Horizontal Scaling | Yes | No |
| High Availability | Yes | Yes |
| Automatic Failover | Yes | Yes |
| Data Sharding | Yes | No |
| Multiple Primaries | Yes | No |
| Dataset | Partitioned | Fully Replicated |

Choose Sentinel for high availability of a single dataset.

Choose Cluster when scaling beyond a single machine.

---

# Cluster vs Replication

| Feature | Replication | Cluster |
|----------|-------------|----------|
| Copies Entire Dataset | Yes | No |
| Horizontal Scaling | No | Yes |
| Multiple Primaries | No | Yes |
| Automatic Partitioning | No | Yes |

Replication improves availability.

Cluster improves both availability and scalability.

---

# Advantages

Redis Cluster provides:

- Horizontal scaling
- Automatic failover
- Large memory capacity
- High throughput
- No single write bottleneck
- Fault tolerance
- Dynamic scaling

---

# Limitations

Redis Cluster also introduces complexity.

- Cross-slot restrictions
- More operational overhead
- More complex client libraries
- Slot migration during scaling
- Additional monitoring requirements

Applications must be designed with partitioning in mind.

---

# Common Production Use Cases

Redis Cluster is commonly used for:

- Large-scale caching
- Session storage
- Gaming platforms
- Social media platforms
- Recommendation engines
- Real-time analytics
- IoT platforms
- Financial trading systems
- Machine learning feature stores
- Large e-commerce platforms

---

# Common Mistakes

## Using Sentinel Instead of Cluster

Sentinel provides:

```
High Availability
```

It does **not** increase memory or throughput.

---

## Ignoring Cross-Slot Restrictions

Applications should group related keys using Hash Tags when multi-key operations are required.

---

## Uneven Slot Distribution

Improper rebalancing may overload certain nodes while others remain underutilized.

Monitor slot allocation regularly.

---

## Too Few Replicas

Every Primary should have at least one Replica to ensure automatic failover.

---

# Best Practices

- Deploy at least one Replica per Primary.
- Monitor slot distribution.
- Use Hash Tags for related keys.
- Plan for future scaling.
- Test node failures regularly.
- Monitor replication lag.
- Use cluster-aware Redis clients.

---

# Production Considerations

When deploying Redis Cluster:

- Distribute nodes across different availability zones.
- Monitor cluster health continuously.
- Automate failover testing.
- Benchmark throughput after scaling.
- Plan maintenance windows for rebalancing operations.
- Integrate monitoring with Prometheus and Grafana.
- Keep client libraries updated for cluster compatibility.

---

# Redis Cluster in Microservice Architecture

```
                API Gateway
                     │
        +------------+------------+
        │                         │
   User Service             Order Service
        │                         │
        +------------+------------+
                     │
               Redis Cluster
                     │
     +---------------+---------------+
     │       │       │       │
 Primary A Primary B Primary C Primary D
     │       │       │       │
 Replica  Replica  Replica  Replica
```

Each service communicates with the cluster through a cluster-aware client, allowing requests to be routed automatically to the correct node based on hash slots.

---

# Summary

Redis Cluster is Redis's native solution for horizontal scaling and high availability. By partitioning data into 16,384 hash slots distributed across multiple Primary nodes, Redis Cluster enables applications to store datasets much larger than a single server can handle while also improving throughput. Replicas provide automatic failover, ensuring continued availability even when nodes fail. Although Cluster introduces operational complexity and cross-slot limitations, it is the preferred architecture for large-scale production systems that require both scalability and resilience.

---

# Key Takeaways

- Redis Cluster provides both horizontal scaling and automatic failover.
- Data is distributed across **16,384 hash slots**.
- Each Primary node owns a subset of the hash slots.
- Replicas are promoted automatically if a Primary fails.
- Cluster-aware clients automatically route requests to the correct node.
- Hash Tags allow related keys to reside on the same node for multi-key operations.
- Redis Cluster is ideal for applications whose datasets or throughput exceed the capacity of a single Redis server.