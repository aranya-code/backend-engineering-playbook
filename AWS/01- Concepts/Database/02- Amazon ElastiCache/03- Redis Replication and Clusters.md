# Redis Replication and Clusters

To run Amazon ElastiCache for Redis at production scale, you must design for high availability and data scalability. Redis achieves this through **Master-Replica Replication** (for HA and read scaling) and **Redis Cluster** (for horizontal write scaling and sharding).

Understanding the differences between Cluster Mode Disabled and Cluster Mode Enabled configurations is critical for planning database capacities and handling high-throughput caching workloads.

---

# Master-Replica Replication

In a basic replication setup, one node is designated as the primary (master) node, and up to 5 nodes are configured as read-only replicas.

```text
       Client Application
       ├── Writes ──────────────────────────┐
       └── Reads (Load Balanced) ────┐      │
                                     ▼      ▼
┌──────────────────┐               ┌──────────────────┐
│   Read Replica   │               │   Primary Node   │
│   (Read-Only)    │               │   (Writable)     │
└────────▲─────────┘               └────────┬─────────┘
         │                                  │
         └───── Asynchronous Replication ───┘
```

- **Asynchronous Replication**: Writes to the primary are acknowledged to the application immediately. The data changes are then propagated asynchronously to the replicas.
- **Failover**: If the primary node fails, ElastiCache automatically detects the failure, promotes a read replica to primary, updates DNS endpoints, and restores service.
- **Multi-AZ**: Always deploy replicas in different Availability Zones than the primary to ensure resilience against AZ outages.

---

# ElastiCache Redis Deployment Modes

ElastiCache provides two primary clustering configurations:

## 1. Cluster Mode Disabled (Single Shard)

The database consists of **exactly one shard** containing one primary node and up to 5 read replicas.

- **Data Partitioning**: No sharding. The entire database dataset must fit within the memory of a single primary node.
- **Scaling Writes**: You cannot scale write capacity horizontally. To scale writes, you must scale the instance class vertically (e.g., from `cache.m5.large` to `cache.m5.xlarge`).
- **Scaling Reads**: You can scale read capacity horizontally by adding up to 5 read replicas.
- **End-Points**: Provides a **Primary Endpoint** (for writes) and a **Reader Endpoint** (for load-balanced reads).

---

## 2. Cluster Mode Enabled (Multi-Shard)

The database is partitioned (sharded) across multiple primary nodes (shards). Each shard has its own primary node and up to 5 read replicas.

- **Data Partitioning**: Data is distributed across shards using **Hash Slots** (16,384 total slots). A hashing function (`CRC16(key) mod 16384`) determines which shard stores a specific key.
- **Scalability**: Can scale up to **500 shards** (meaning 500 primary nodes), allowing you to scale database memory and write capacity horizontally to hundreds of terabytes.
- **Failover Isolation**: If a node in Shard 1 fails, only the keys mapped to Shard 1 are affected during the failover. The other shards continue processing writes and reads normally.
- **Configuration Endpoint**: Instead of primary/reader endpoints, applications use a single **Configuration Endpoint** and a cluster-aware client library that automatically routes queries to the correct shard based on the hash slot of the key.

```text
Cluster Mode Enabled (3 Shards, 1 Replica each):

Client Configuration Endpoint
              │
              ▼
┌────────────────────────────────────────────────────────┐
│               Hash Slots (0 - 16383)                   │
├───────────────────┬───────────────────┬────────────────┤
│ Shard 1 (0-5460)  │ Shard 2 (5461-10k)│ Shard 3 (10k+) │
│ ┌───────────────┐ │ ┌───────────────┐ │ ┌────────────┐ │
│ │ Primary 1 (W) │ │ │ Primary 2 (W) │ │ │Primary 3(W)│ │
│ └───────┬───────┘ │ └───────┬───────┘ │ └─────┬──────┘ │
│         │         │         │         │       │        │
│         ▼         │         ▼         │       ▼        │
│ ┌───────────────┐ │ ┌───────────────┐ │ ┌────────────┐ │
│ │ Replica 1 (R) │ │ │ Replica 2 (R) │ │ │Replica 3(R)│ │
│ └───────────────┘ │ └───────────────┘ │ └────────────┘ │
└───────────────────┴───────────────────┴────────────────┘
```

---

# Cluster Mode Disabled vs. Cluster Mode Enabled

| Metric / Feature | Cluster Mode Disabled | Cluster Mode Enabled |
|------------------|-----------------------|----------------------|
| **Number of Shards**| 1 | 1 to 500 |
| **Max Primary Nodes**| 1 | Up to 500 |
| **Data Partitioning**| No (Single Node) | Yes (Hash Slots) |
| **Write Scaling** | Vertical only | Horizontal (Add shards) |
| **Read Scaling** | Add replicas (Max 5) | Add replicas per shard (Max 5) |
| **Max Memory Limit**| Size of largest single node | Unlimited (Sum of all shards) |
| **Client Requirement**| Standard Redis client | Cluster-aware Redis client |
| **Multi-Key Operations**| Full support | Restricted (keys must hash to same slot) |

---

# Multi-Key Operations and Hash Tags (Important Constraint)

In Cluster Mode Enabled, multi-key operations (like `MGET`, transactional blocks, or join operations) require all keys involved to reside on the **same shard (hash slot)**. If keys map to different shards, the engine returns a `CROSSSLOT Keys in request don't hash to the same slot` error.

## The Solution: Hash Tags

You can force specific keys to hash to the same slot by wrapping the common part of the key in curly braces `{}`.

- Key 1: `{user100}:profile`
- Key 2: `{user100}:orders`
- Key 3: `{user100}:settings`

Because the hashing function only hashes the content inside `{}` (i.e., `user100`), all three keys are guaranteed to map to the exact same hash slot and reside on the same shard, allowing atomic multi-key operations to succeed.

---

# Key Takeaways

- **Master-Replica Replication** provides high availability and read scaling through asynchronous data mirroring.
- **Cluster Mode Disabled** is suitable for databases that can fit on a single node and do not require write scaling.
- **Cluster Mode Enabled** provides horizontal sharding across up to 500 shards, scaling database writes and memory indefinitely.
- Multi-key operations in clustered Redis require **Hash Tags** `{}` to prevent cross-slot routing errors.
- Deploy replication groups across multiple Availability Zones to ensure automatic failover resilience.

---
