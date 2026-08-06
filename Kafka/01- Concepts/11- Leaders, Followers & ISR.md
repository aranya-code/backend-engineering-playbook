# Leaders, Followers & ISR

## Overview

Apache Kafka achieves high availability and fault tolerance through **replication**. Every partition in Kafka has one **Leader** replica and zero or more **Follower** replicas. Together, they ensure that data remains available even if one or more brokers fail.

Kafka also maintains a special list called the **In-Sync Replicas (ISR)**. The ISR contains all replicas that are fully synchronized with the leader and are eligible to become the next leader if a failure occurs.

Understanding Leaders, Followers, and ISR is essential because they directly affect:

- Data durability
- Fault tolerance
- High availability
- Producer acknowledgements
- Leader election

These concepts form the backbone of Kafka's replication mechanism.

---

# Why Do We Need Replicas?

Imagine a Kafka topic with only one broker.

```text
Producer

     │

     ▼

Broker 1

Partition 0
```

If Broker 1 crashes:

- Messages become unavailable.
- Producers cannot write.
- Consumers cannot read.
- Data may be permanently lost.

This creates a single point of failure.

Kafka solves this problem using replication.

---

# Replicated Partition

Instead of storing a partition on only one broker, Kafka stores multiple copies.

```text
Partition 0

        │

        ▼

Broker 1

Leader

        │

 ┌──────┴──────┐

 ▼             ▼

Broker 2    Broker 3

Follower    Follower
```

Now, even if one broker fails, another replica can continue serving requests.

---

# Leader Replica

Each partition has exactly **one Leader**.

Example:

```text
Orders Topic

Partition 0

↓

Leader

Broker 1
```

The Leader is responsible for:

- Receiving messages from producers.
- Serving consumers.
- Coordinating replication.
- Managing offsets for the partition.

Every read and write operation goes through the Leader.

---

# Follower Replica

Followers maintain copies of the leader's data.

Example:

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

Followers do **not** normally serve producers or consumers.

Instead, they continuously copy data from the Leader.

---

# How Replication Works

Consider the following sequence.

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

1. Producer sends a message.
2. Leader writes the message.
3. Followers replicate the message.
4. Followers confirm replication.
5. Leader acknowledges the producer (depending on ACK configuration).

---

# Leader Handles All Reads and Writes

Even though multiple replicas exist, producers and consumers communicate only with the Leader.

```text
Producer

↓

Leader

↓

Follower

Follower
```

Similarly,

```text
Consumer

↓

Leader

↓

Message Returned
```

Followers are not used for normal client requests.

---

# What is ISR?

ISR stands for **In-Sync Replicas**.

It is the set of replicas that are fully synchronized with the Leader.

Example:

```text
Partition 0

Leader

Broker 1

--------------------

ISR

Broker 1

Broker 2

Broker 3
```

All three replicas contain the latest committed data.

---

# Why is ISR Important?

Suppose one follower falls behind.

```text
Leader

Broker 1

-------------------

Follower

Broker 2

Up-to-date

-------------------

Follower

Broker 3

Lagging
```

Kafka removes Broker 3 from the ISR.

```text
ISR

Broker 1

Broker 2
```

Only replicas inside the ISR are considered safe for leader election.

---

# Leader Failure

Suppose the leader crashes.

Before failure:

```text
Broker 1

Leader

----------------

Broker 2

Follower

----------------

Broker 3

Follower
```

After failure:

```text
Broker 1

Offline

----------------

Broker 2

New Leader

----------------

Broker 3

Follower
```

Kafka automatically promotes one of the ISR replicas to become the new Leader.

Applications continue working with minimal interruption.

---

# Follower Failure

Now suppose a follower crashes.

Before failure:

```text
Leader

Broker 1

Follower

Broker 2

Follower

Broker 3
```

After failure:

```text
Leader

Broker 1

Follower

Broker 2

Broker 3

Offline
```

The partition remains available because the Leader is still running.

When Broker 3 recovers, it synchronizes with the Leader before rejoining the ISR.

---

# Leader Election

Leader election occurs when:

- The current leader fails.
- The broker hosting the leader shuts down.
- Planned maintenance occurs.
- Cluster rebalancing happens.

Kafka selects a new leader from the ISR.

```text
ISR

Broker 2

Broker 3

↓

Broker 2

Becomes Leader
```

This process is automatic.

---

# Why Doesn't Kafka Choose Any Replica?

Suppose Broker 3 is significantly behind.

```text
Leader

Offset 120

------------------

Follower

Offset 120

------------------

Follower

Offset 90
```

Choosing Broker 3 as the new Leader would lose messages.

Therefore, Kafka selects leaders only from replicas that are fully synchronized.

---

# ISR Changes Over Time

The ISR is dynamic.

Example:

Initially:

```text
ISR

Broker 1

Broker 2

Broker 3
```

Broker 3 slows down.

```text
ISR

Broker 1

Broker 2
```

Broker 3 catches up.

```text
ISR

Broker 1

Broker 2

Broker 3
```

Kafka automatically updates the ISR.

---

# Leaders, Followers and ACKs

The producer acknowledgement setting determines when Kafka confirms a write.

### acks = 0

```text
Producer

↓

Leader

(No Waiting)
```

No replication guarantee.

---

### acks = 1

```text
Producer

↓

Leader

↓

ACK
```

Only the Leader confirms.

Followers may not yet have replicated the message.

---

### acks = all

```text
Producer

↓

Leader

↓

ISR Replicas

↓

ACK
```

Kafka waits for every ISR replica before acknowledging the producer.

This provides the highest durability.

---

# Advantages of Replication

- High availability
- Fault tolerance
- Data durability
- Automatic recovery
- Continuous operation
- Reliable leader election

---

# Common Misconceptions

### "Followers serve consumers."

Incorrect.

Consumers always read from the Leader.

---

### "Every replica can become Leader."

Incorrect.

Only replicas inside the ISR are eligible.

---

### "More replicas always improve performance."

Not necessarily.

More replicas increase:

- Storage
- Network traffic
- Replication overhead

Choose an appropriate replication factor.

---

# Best Practices

- Use a replication factor of at least three in production.
- Prefer `acks=all` for critical workloads.
- Monitor ISR size.
- Investigate replicas that frequently leave the ISR.
- Avoid running production clusters with a replication factor of one.
- Monitor leader distribution across brokers.

---

# Common Mistakes

- Confusing replicas with partitions.
- Assuming followers serve client requests.
- Ignoring shrinking ISR lists.
- Using a replication factor of one in production.
- Not understanding how acknowledgements interact with replication.

---

# Summary

Kafka ensures reliability by replicating every partition across multiple brokers. Each partition has one Leader that handles all client requests and one or more Followers that continuously replicate the Leader's data. Kafka tracks synchronized replicas using the ISR (In-Sync Replicas) list and selects new Leaders only from this set during failures. This architecture enables Kafka to provide high availability, durability, and fault tolerance while maintaining consistent data across the cluster.

---

# Key Takeaways

- Every partition has one Leader and zero or more Followers.
- Producers and consumers communicate only with the Leader.
- Followers continuously replicate the Leader's data.
- ISR contains replicas that are fully synchronized with the Leader.
- Only ISR members are eligible for leader election.
- Kafka automatically elects a new Leader when the current Leader fails.
- Producer acknowledgement settings work closely with replication.
- Leaders, Followers, and ISR are fundamental to Kafka's fault tolerance and high availability.