# Replication

## Overview

Replication is one of Apache Kafka's most important features. It ensures that data remains available even if one or more brokers fail.

Instead of storing a partition on a single broker, Kafka stores multiple copies (replicas) of the partition across different brokers. If one broker becomes unavailable, another replica can immediately take over, allowing producers and consumers to continue working with little or no downtime.

Replication provides:

- High availability
- Fault tolerance
- Data durability
- Disaster recovery
- Reliable event processing

Without replication, Kafka would become a single point of failure.

---

# What is Replication?

Replication is the process of maintaining multiple copies of a partition across different brokers.

Consider a topic with one partition.

Without replication:

```text
Orders Topic

Partition 0

↓

Broker 1
```

If Broker 1 crashes, the partition becomes unavailable.

With replication:

```text
Orders Topic

Partition 0

↓

Broker 1 (Leader)

↓

Broker 2 (Follower)

↓

Broker 3 (Follower)
```

Now Kafka has three copies of the same data.

---

# Why Replication is Needed

Imagine an e-commerce application.

```text
Customer

↓

Place Order

↓

Kafka
```

Without replication:

```text
Broker Failure

↓

Orders Lost

↓

Business Failure
```

With replication:

```text
Broker Failure

↓

Replica Takes Over

↓

No Data Loss
```

Replication protects business-critical events.

---

# Replication Factor

The **Replication Factor (RF)** determines how many copies of each partition Kafka maintains.

Example:

```text
Replication Factor = 3
```

Means:

```text
Partition

↓

Leader

↓

Follower

↓

Follower
```

Three total copies exist.

One Leader.

Two Followers.

---

# Replication Factor Examples

## RF = 1

```text
Broker 1

Leader
```

Advantages:

- Minimal storage

Disadvantages:

- No fault tolerance

---

## RF = 2

```text
Broker 1

Leader

↓

Broker 2

Follower
```

Advantages:

- Basic fault tolerance

Disadvantages:

- Lower redundancy

---

## RF = 3

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

Advantages:

- High availability
- Better durability
- Production ready

This is the most common production configuration.

---

# Replication Across Brokers

Replicas are distributed across different brokers.

Example:

```text
Kafka Cluster

Broker 1

Orders P0 (Leader)

Payments P1 (Follower)

------------------------

Broker 2

Orders P0 (Follower)

Payments P1 (Leader)

------------------------

Broker 3

Orders P0 (Follower)

Payments P1 (Follower)
```

Kafka avoids storing all replicas on the same broker.

---

# Message Replication Flow

Consider a producer sending a message.

```text
Producer

↓

Leader

↓

Follower 1

↓

Follower 2
```

Step-by-step:

1. Producer sends the message.
2. Leader writes the message.
3. Followers copy the message.
4. Followers acknowledge the replication.
5. Leader responds to the producer based on the ACK configuration.

---

# Replication and Producers

The producer always communicates with the Leader.

```text
Producer

↓

Leader

↓

Followers
```

Producers never send messages directly to Followers.

---

# Replication and Consumers

Consumers also communicate only with the Leader.

```text
Consumer

↓

Leader

↓

Messages
```

Followers exist solely for replication and recovery.

---

# What Happens When a Broker Fails?

Suppose Broker 1 hosts the Leader.

Before failure:

```text
Broker 1

Leader

-------------------

Broker 2

Follower

-------------------

Broker 3

Follower
```

Broker 1 crashes.

```text
Broker 1

Offline

-------------------

Broker 2

Leader

-------------------

Broker 3

Follower
```

Kafka promotes one of the synchronized Followers to become the new Leader.

Applications continue working.

---

# Replica Synchronization

Followers continuously copy data from the Leader.

```text
Leader

Offset 100

↓

Follower

Offset 100

↓

Follower

Offset 100
```

All replicas remain synchronized.

If a follower falls behind:

```text
Leader

Offset 120

↓

Follower

Offset 120

↓

Follower

Offset 95
```

Kafka removes the lagging replica from the ISR until it catches up.

---

# Replication and Durability

Replication improves durability.

Without replication:

```text
Disk Failure

↓

Data Lost
```

With replication:

```text
Disk Failure

↓

Replica Available

↓

Data Preserved
```

---

# Replication and ACKs

Replication works closely with producer acknowledgements.

### acks = 0

```text
Producer

↓

Leader

(No Waiting)
```

Fastest.

Lowest reliability.

---

### acks = 1

```text
Producer

↓

Leader

↓

ACK
```

Leader confirms immediately.

Followers may still be replicating.

---

### acks = all

```text
Producer

↓

Leader

↓

ISR

↓

ACK
```

Producer waits until all in-sync replicas acknowledge.

Highest reliability.

---

# Replication Factor vs Number of Brokers

Replication factor cannot exceed the number of brokers.

Example:

| Brokers | Maximum Replication Factor |
|---------:|---------------------------:|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 5 | 5 |

Example:

```text
3 Brokers

↓

Maximum RF = 3
```

Kafka cannot create three replicas if only two brokers exist.

---

# Storage Cost of Replication

Replication increases storage usage.

Suppose:

```text
Partition Size

100 GB
```

With RF = 3

```text
100 GB

↓

300 GB Total Storage
```

More replicas improve durability but require additional disk space.

---

# Advantages of Replication

- High availability
- Automatic recovery
- Fault tolerance
- Better durability
- Continuous operation
- Reduced risk of data loss

---

# Limitations

- Increased storage requirements
- Higher network traffic
- Additional replication overhead
- Slightly higher write latency
- More operational complexity

These trade-offs are generally worthwhile for production systems.

---

# Best Practices

- Use a replication factor of three in production.
- Distribute replicas across different brokers.
- Use `acks=all` for critical workloads.
- Monitor ISR health.
- Monitor broker disk usage.
- Avoid a replication factor of one in production.

---

# Common Mistakes

- Assuming replication is a backup strategy.
- Setting the replication factor higher than the number of brokers.
- Running production systems with RF = 1.
- Ignoring lagging replicas.
- Confusing partitions with replicas.

---

# Replication vs Partitioning

These two concepts are often confused.

| Partitioning | Replication |
|--------------|-------------|
| Improves scalability | Improves reliability |
| Splits data into multiple partitions | Creates copies of partitions |
| Enables parallel processing | Enables fault tolerance |
| Distributes workload | Protects against failures |

Both are essential, but they solve different problems.

---

# Summary

Replication allows Kafka to maintain multiple copies of every partition across different brokers. One replica acts as the Leader while the remaining replicas act as Followers. If a broker fails, Kafka automatically promotes an in-sync replica to become the new Leader, ensuring minimal disruption. Replication is fundamental to Kafka's durability, fault tolerance, and high availability.

---

# Key Takeaways

- Replication creates multiple copies of a partition.
- The replication factor determines the number of replicas.
- Producers and consumers communicate only with the Leader.
- Followers continuously replicate the Leader's data.
- Replication protects against broker failures.
- `acks=all` provides the highest level of durability.
- A replication factor of three is commonly used in production.
- Replication improves reliability, while partitioning improves scalability.
```