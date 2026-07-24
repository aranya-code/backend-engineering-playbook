# Redis Cluster Interview Questions

## Overview

As applications scale to hundreds of gigabytes or even terabytes of data, a single Redis server is no longer sufficient.

Limitations of a single Redis instance include:

- Memory capacity
- CPU resources
- Network bandwidth
- Single write bottleneck

Redis Cluster solves these problems by distributing data across multiple Redis nodes while maintaining high availability.

Senior backend interviews commonly focus on:

- Redis Cluster Architecture
- Sharding
- Hash Slots
- Cluster Failover
- Resharding
- Scaling
- Client Routing
- Cluster Limitations
- Production Best Practices

This chapter covers the most commonly asked Redis Cluster interview questions.

---

# Q1. What is Redis Cluster?

### Answer

Redis Cluster is Redis's native horizontal scaling solution.

It automatically distributes data across multiple Redis nodes.

Architecture

```
                Clients

                   │

                   ▼

        ----------------------

        | Redis Cluster      |

        ----------------------

         │       │       │

         ▼       ▼       ▼

      Node A  Node B  Node C
```

Each node stores only part of the total dataset.

---

# Q2. Why do we need Redis Cluster?

### Answer

A single Redis server has limitations.

- Memory
- CPU
- Network throughput
- Single point of failure

Redis Cluster provides

- Horizontal scaling
- Fault tolerance
- Automatic failover
- Higher throughput

---

# Q3. What is Sharding?

### Answer

Sharding means dividing data across multiple servers.

Instead of

```
One Server

↓

All Data
```

Redis Cluster uses

```
Server A

↓

Users

Server B

↓

Products

Server C

↓

Orders
```

In reality,

Redis automatically distributes keys rather than assigning them by business entity.

---

# Q4. What are Hash Slots?

### Answer

Redis Cluster divides the keyspace into

```
16,384

Hash Slots
```

Every key belongs to exactly one hash slot.

Example

```
user:101

↓

Hash Function

↓

Slot 5291
```

---

# Q5. Why exactly 16,384 slots?

### Answer

Redis uses 16,384 slots because they provide:

- Efficient distribution
- Small metadata
- Fast calculations
- Easy migration

Every node owns a range of slots.

Example

```
Node A

0-5000

Node B

5001-10000

Node C

10001-16383
```

---

# Q6. How does Redis decide where a key belongs?

### Answer

Redis computes

```
CRC16(Key)

↓

Modulo 16384

↓

Hash Slot
```

The client sends the request to the correct node.

---

# Q7. Can multiple keys belong to the same slot?

### Answer

Yes.

Many keys can map to the same slot.

Only the slot number determines which node stores the key.

---

# Q8. What are Hash Tags?

### Answer

Hash Tags force multiple keys into the same slot.

Example

```
user:{100}:name

user:{100}:orders

user:{100}:cart
```

Everything inside

```
{}
```

is hashed.

All three keys belong to the same slot.

---

# Q9. Why are Hash Tags useful?

### Answer

Redis Cluster supports multi-key operations only when all keys belong to the same hash slot.

Example

```
MGET

MSET

SUNION

SINTER
```

Hash Tags make these operations possible.

---

# Q10. What happens if keys are in different slots?

### Answer

Redis returns

```
CROSSSLOT Keys in request don't hash to the same slot
```

Example

```
MGET

user:1

user:2

↓

Different Slots

↓

Error
```

---

# Q11. How many Primary nodes can Redis Cluster have?

### Answer

There is no fixed limit.

Production clusters often have

- 3 Primaries
- 6 Primaries
- 9 Primaries
- More

depending on workload.

---

# Q12. Does every Primary need a Replica?

### Answer

It is strongly recommended.

Example

```
Primary A

↓

Replica A

Primary B

↓

Replica B

Primary C

↓

Replica C
```

If a primary fails,

its replica can be promoted.

---

# Q13. What happens when a Primary fails?

### Answer

Workflow

```
Primary Down

↓

Replica Election

↓

Replica Promoted

↓

Clients Continue
```

Failover is automatic.

---

# Q14. How does Redis Cluster detect failures?

### Answer

Nodes continuously exchange heartbeat messages.

If a node becomes unreachable,

other nodes vote on whether it has failed.

---

# Q15. Does Redis Cluster require Sentinel?

### Answer

No.

Redis Cluster has built-in

- Failure detection
- Leader election
- Automatic failover

Sentinel is not used with Redis Cluster.

---

# Q16. What is Cluster Bus?

### Answer

Cluster Bus is an internal communication channel used by cluster nodes.

It carries

- Heartbeats
- Slot information
- Failover messages
- Configuration updates

Applications never communicate through the Cluster Bus.

---

# Q17. What happens when a client connects to the wrong node?

### Answer

The node returns

```
MOVED
```

Example

```
Client

↓

Wrong Node

↓

MOVED

↓

Correct Node
```

Modern Redis clients automatically follow the redirect.

---

# Q18. What is ASK redirection?

### Answer

During slot migration,

Redis may return

```
ASK
```

Unlike

```
MOVED
```

ASK is temporary.

It tells the client where the slot is currently being migrated.

---

# Q19. What is Resharding?

### Answer

Resharding moves hash slots between nodes.

Example

Before

```
Node A

8000 Slots

Node B

8384 Slots
```

After adding another node

```
Node A

5500

Node B

5500

Node C

5384
```

---

# Q20. Can Redis Cluster be scaled without downtime?

### Answer

Yes.

Nodes can be added or removed while the cluster continues serving requests.

Redis automatically migrates hash slots.

---

# Q21. What are the benefits of Redis Cluster?

### Answer

- Horizontal scaling
- Automatic failover
- High availability
- Large datasets
- Better throughput
- Fault tolerance

---

# Q22. What are the limitations of Redis Cluster?

### Answer

Limitations include

- Multi-key operations require the same slot.
- Lua scripts are limited across slots.
- Transactions cannot span multiple slots.
- Increased operational complexity.

---

# Q23. Does Redis Cluster improve write throughput?

### Answer

Yes.

Because writes are distributed across multiple primary nodes.

Example

```
Primary A

1000 Writes/sec

Primary B

1000 Writes/sec

Primary C

1000 Writes/sec

↓

3000 Writes/sec Total
```

---

# Q24. Can Redis Cluster store the same key on multiple nodes?

### Answer

No.

Each key belongs to exactly one primary node.

Replication copies that key only to its replica(s).

---

# Q25. What happens if an entire node fails permanently?

### Answer

If a replica exists,

it becomes the new primary.

If no replica exists,

the affected hash slots become unavailable until recovered.

---

# Q26. What monitoring metrics are important?

### Answer

Monitor

- Slot distribution
- Node health
- Replication lag
- Memory usage
- CPU usage
- Network traffic
- Cluster state
- Failover events

---

# Q27. What is a typical production Redis Cluster architecture?

### Answer

```
                     Clients

                        │

                        ▼

        ----------------------------------

              Redis Cluster

        ----------------------------------

         │          │          │

         ▼          ▼          ▼

      Primary    Primary    Primary

         │          │          │

         ▼          ▼          ▼

      Replica    Replica    Replica
```

---

# Q28. What is the difference between Redis Cluster and Sentinel?

### Answer

| Redis Cluster | Redis Sentinel |
|---------------|----------------|
| Horizontal Scaling | High Availability |
| Data Sharding | No Sharding |
| Hash Slots | No Hash Slots |
| Multiple Primaries | Single Primary |
| Automatic Failover | Automatic Failover |
| Large Datasets | Small to Medium Datasets |

---

# Q29. What are common interview mistakes?

### Answer

Candidates often

- Confuse Sentinel with Cluster.
- Think Cluster requires Sentinel.
- Forget Hash Slots.
- Ignore Hash Tags.
- Assume multi-key operations always work.

---

# Q30. When should Redis Cluster be used?

### Answer

Redis Cluster is appropriate when applications require

- Horizontal scaling
- Large datasets
- High write throughput
- High availability
- Automatic failover
- Multi-node architecture

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Total hash slots? | 16,384 |
| Horizontal scaling? | Redis Cluster |
| Automatic failover? | Yes |
| Multi-key operations across slots? | No |
| Hash function? | CRC16 |
| Slot migration? | Resharding |
| Wrong node response? | MOVED |
| Temporary redirect? | ASK |

---

# Senior Interview Tips

Interviewers frequently ask:

> Why did Redis choose hash slots instead of consistent hashing?

A strong answer should include

- Simpler slot migration
- Easier resharding
- Smaller metadata
- Faster client routing
- Better operational management

This demonstrates an understanding of Redis internals rather than just knowing commands.

---

# Common Mistakes

## Confusing Cluster with Replication

Replication provides high availability.

Cluster provides both high availability and horizontal scaling.

---

## Ignoring Hash Tags

Without Hash Tags, many multi-key operations fail across different slots.

---

## Thinking Cluster Eliminates All Downtime

Although Redis Cluster minimizes downtime through automatic failover, brief interruptions can still occur during failover or slot migration.

---

## Forgetting Operational Complexity

Redis Cluster introduces additional operational responsibilities, including monitoring slot distribution, rebalancing, and cluster health.

---

# Best Practices

- Deploy at least three primary nodes with corresponding replicas.
- Distribute hash slots evenly across nodes.
- Use Hash Tags for related keys requiring multi-key operations.
- Monitor cluster state and failover events continuously.
- Test failover and resharding in staging before production.
- Use cluster-aware Redis clients that automatically handle MOVED and ASK redirects.

---

# Summary

Redis Cluster enables horizontal scaling by distributing data across multiple primary nodes using 16,384 hash slots. It provides built-in replication, automatic failover, and high availability without requiring Redis Sentinel. Understanding hash slots, resharding, client redirection, and cluster limitations is essential for designing scalable Redis deployments and succeeding in senior backend interviews.

---

# Key Takeaways

- Redis Cluster is Redis's native horizontal scaling solution.
- Data is distributed using 16,384 hash slots.
- Every key belongs to exactly one hash slot and one primary node.
- Replicas provide high availability through automatic failover.
- Hash Tags enable multi-key operations by forcing related keys into the same slot.
- Cluster-aware clients automatically handle MOVED and ASK redirections.
- Redis Cluster is designed for large-scale, high-throughput production systems requiring both scalability and fault tolerance.