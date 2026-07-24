# Cluster Problems

## Overview

Redis Cluster provides **horizontal scalability** and **high availability** by distributing data across multiple Redis nodes using **hash slots**.

Unlike Redis Sentinel, which manages failover for a single primary, Redis Cluster partitions data across multiple primaries and replicas.

While this architecture provides scalability, it also introduces operational challenges such as:

- Hash slot issues
- MOVED errors
- ASK errors
- Node failures
- Cluster state failures
- Slot migration problems
- Replica synchronization issues
- Network partitions

Understanding how Redis Cluster works is essential for operating large-scale production deployments.

---

# Redis Cluster Architecture

```
                    Clients
                       │
                       ▼
               +----------------+
               | Cluster Client |
               +----------------+
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    +---------+   +---------+   +---------+
    |Master A |   |Master B |   |Master C |
    +---------+   +---------+   +---------+
        │             │             │
        ▼             ▼             ▼
   Replica A     Replica B     Replica C
```

Each master owns a subset of the **16,384 hash slots**.

---

# How Redis Cluster Stores Data

```
Key

↓

CRC16 Hash

↓

Hash Slot

↓

Master Node
```

Example

```
user:100

↓

Hash Slot 8500

↓

Master B
```

Redis automatically routes requests based on the hash slot.

---

# Cluster Workflow

```
Client

↓

Hash Key

↓

Determine Slot

↓

Locate Master

↓

Execute Command
```

Modern Redis clients perform this automatically.

---

# Common Cluster Problems

| Problem | Symptoms |
|----------|----------|
| MOVED error | Wrong node contacted |
| ASK error | Slot migration in progress |
| Cluster down | Requests rejected |
| Missing slots | Cluster inconsistent |
| Node failure | Reduced availability |
| Slot imbalance | Uneven load |
| Replica failure | Reduced fault tolerance |
| Network partition | Cluster split |

---

# Verify Cluster Health

Run

```bash
redis-cli --cluster check 10.0.0.10:6379
```

Example

```text
All 16384 slots covered.
```

Healthy clusters should report:

- All slots assigned
- All nodes reachable
- No open slots

---

# Cluster Information

```bash
CLUSTER INFO
```

Example

```text
cluster_state:ok

cluster_slots_assigned:16384
```

Important fields

- cluster_state
- cluster_known_nodes
- cluster_size
- cluster_slots_assigned
- cluster_slots_ok
- cluster_slots_fail

---

# View Cluster Nodes

```bash
CLUSTER NODES
```

Example

```text
Node ID

IP

Role

Slots
```

Verify

- Primary nodes
- Replica nodes
- Slot ownership
- Node status

---

# MOVED Error

Example

```text
(error) MOVED 8500 10.0.0.11:6379
```

Meaning

```
Client

↓

Wrong Node

↓

Correct Node Returned
```

Modern Redis clients automatically reconnect.

Older clients often fail.

---

# ASK Error

Occurs during slot migration.

```
Slot Moving

↓

Temporary Redirect

↓

ASK
```

Unlike MOVED, ASK is temporary.

---

# Slot Migration

```
Master A

↓

Move Slot

↓

Master B

↓

Cluster Updated
```

Migration should be carefully monitored to avoid temporary request failures.

---

# Open Slots

```
Slot

↓

No Owner

↓

Cluster Error
```

Verify

```bash
redis-cli --cluster check
```

Open slots should be repaired immediately.

---

# Slot Imbalance

Example

```
Master A

8000 Slots

Master B

4000 Slots

Master C

4384 Slots
```

Uneven slot distribution causes uneven CPU and memory usage.

---

# Rebalancing

Redis supports automatic slot balancing.

Run

```bash
redis-cli --cluster rebalance 10.0.0.10:6379
```

Rebalancing distributes slots more evenly across masters.

---

# Node Failure

```
Master Offline

↓

Replica Promotion

↓

Cluster Updated
```

If no replica exists,

```
Cluster

↓

Reduced Availability
```

---

# Replica Failure

```
Replica Offline

↓

No Backup

↓

Lower Fault Tolerance
```

Always maintain at least one replica per master.

---

# Cluster Down

Example

```text
CLUSTERDOWN Hash slot not served
```

Possible causes

- Missing masters
- Slot ownership issues
- Multiple failures
- Network partition

---

# Network Partition

```
Cluster

↓

Network Split

↓

Nodes Cannot Communicate
```

Cluster may reject writes to avoid split-brain.

---

# Cluster Bus

Redis nodes communicate over

```
Data Port

6379
```

Cluster Bus

```
16379
```

Both ports must remain accessible.

---

# Firewall Issues

Verify

- TCP 6379
- TCP 16379

Firewalls blocking the cluster bus can prevent node communication.

---

# DNS Problems

Cluster nodes should use stable addresses.

Avoid dynamic IP changes without updating cluster configuration.

---

# Memory Imbalance

Different masters may consume different amounts of memory.

Check

```bash
INFO memory
```

on every node.

Do not assume balanced slot counts imply balanced memory usage.

---

# CPU Imbalance

Monitor

```bash
INFO cpu
```

One overloaded master can slow part of the cluster.

---

# Cluster Resharding

```
Old Slot Owner

↓

Move Slots

↓

New Owner

↓

Update Clients
```

Perform resharding during low-traffic periods whenever possible.

---

# Docker Deployment

```
Cluster Nodes

↓

Docker Network

↓

Stable Networking
```

Avoid changing container IP addresses after cluster creation.

---

# Kubernetes Deployment

Prefer

- StatefulSets
- Headless Services
- Persistent Volumes

Avoid Deployments for Redis Cluster nodes because stable identities are required.

---

# AWS ElastiCache

Monitor

- Cluster Status
- Node Failures
- CPU Utilization
- Memory Usage
- Network Throughput
- Failover Events

CloudWatch should alert on degraded cluster health.

---

# Useful Commands

Cluster status

```bash
CLUSTER INFO
```

Cluster nodes

```bash
CLUSTER NODES
```

Cluster slots

```bash
CLUSTER SLOTS
```

Check cluster

```bash
redis-cli --cluster check host:6379
```

Rebalance

```bash
redis-cli --cluster rebalance host:6379
```

---

# Diagnostic Workflow

```
Cluster Problem

        │

        ▼

CLUSTER INFO

        │

        ▼

cluster_state = ok ?

        │

 ┌──────┴────────┐

 │               │

No              Yes

 │               │

Check Nodes   Check MOVED

 │               │

 ▼               ▼

Check Slots   Client Config

 │

 ▼

Check Replicas

 │

 ▼

Check Network

 │

 ▼

Restore Cluster
```

---

# Common Mistakes

## Using Non-Cluster Clients

Applications must use Redis Cluster-aware clients.

Otherwise,

```
MOVED

↓

Application Failure
```

---

## No Replicas

Running only primary nodes significantly increases the risk of downtime.

---

## Ignoring Slot Distribution

Uneven slot allocation creates resource hotspots.

---

## Blocking Cluster Bus

Opening only port

```
6379
```

is insufficient.

The cluster bus requires

```
16379
```

to remain accessible.

---

## Manual Slot Assignment

Manual changes without proper tooling can leave the cluster in an inconsistent state.

Use official cluster management commands.

---

# Best Practices

- Maintain at least one replica for every primary node.
- Monitor cluster health continuously.
- Keep slot distribution balanced.
- Use Redis Cluster-aware client libraries.
- Protect both Redis and cluster bus ports.
- Perform resharding during maintenance windows.
- Monitor CPU, memory, and slot ownership together.
- Regularly test node failure and recovery scenarios.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Slot Distribution | Balance evenly |
| Replicas | One or more per primary |
| Cluster Bus | Keep low-latency networking |
| Monitoring | Track cluster state continuously |
| Clients | Use cluster-aware libraries |
| Scaling | Rebalance after adding nodes |

---

# Production Considerations

For production deployments:

- Continuously monitor `cluster_state`, slot coverage, and node health.
- Configure alerts for `CLUSTERDOWN`, failed nodes, and slot inconsistencies.
- Use StatefulSets (Kubernetes) or equivalent stable infrastructure for cluster nodes.
- Validate cluster health before and after scaling or maintenance operations.
- Test resharding and failover procedures in staging environments.
- Ensure firewall rules permit both Redis client traffic (6379) and cluster bus traffic (16379).
- Maintain documented recovery procedures for node failures, slot recovery, and cluster rebuilds.

---

# Summary

Redis Cluster enables horizontal scaling by distributing data across multiple primary nodes using hash slots. While it offers excellent scalability and availability, it introduces operational complexity around slot management, node communication, failover, and client routing. Regular health checks, balanced slot distribution, cluster-aware clients, and proactive monitoring are essential for maintaining a stable production cluster.

---

# Key Takeaways

- Redis Cluster distributes data across **16,384 hash slots**.
- Use cluster-aware clients to handle `MOVED` and `ASK` redirects automatically.
- Monitor `CLUSTER INFO`, `CLUSTER NODES`, and slot coverage regularly.
- Maintain at least one replica for every primary node.
- Keep both Redis (6379) and cluster bus (16379) ports accessible.
- Rebalance slots after scaling to prevent uneven resource utilization.
- Test node failures and recovery procedures before production incidents.
- A healthy Redis Cluster requires continuous monitoring, stable networking, and disciplined operational practices.