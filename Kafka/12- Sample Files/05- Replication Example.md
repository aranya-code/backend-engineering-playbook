# Replication Example

## Overview

Replication is Kafka's mechanism for ensuring **high availability**, **fault tolerance**, and **data durability**. Instead of storing a partition on only one broker, Kafka stores multiple copies (replicas) across different brokers.

If one broker fails, another replica can immediately take over, allowing producers and consumers to continue operating with minimal interruption.

This chapter explains Kafka replication using practical examples to demonstrate leader replicas, follower replicas, In-Sync Replicas (ISR), leader election, and failure recovery.

---

# What is Replication?

Replication means keeping multiple copies of the same partition.

Example:

```text
Orders Topic

↓

Partition 0

↓

Broker 1

Broker 2

Broker 3
```

Each broker stores a copy of the partition.

---

# Example 1: Replication Factor = 1

Topic configuration:

```text
Replication Factor

1
```

Architecture:

```text
Broker 1

↓

Partition 0
```

Only one copy exists.

---

# What Happens if Broker 1 Fails?

```text
Broker 1

↓

Failure
```

Result:

```text
Partition Lost
```

Consumers cannot read.

Producers cannot write.

Data may be permanently lost.

---

# Example 2: Replication Factor = 3

Now configure:

```text
Replication Factor

3
```

Architecture:

```text
          Partition 0

        Leader (Broker 1)

         /            \

Follower (Broker 2)

Follower (Broker 3)
```

Three copies exist.

---

# Leader Replica

Every partition has exactly one leader.

Example:

```text
Broker 1

↓

Leader
```

Responsibilities:

- Accept producer writes
- Serve consumer reads
- Coordinate replication

Only the leader receives client requests.

---

# Follower Replicas

Followers copy data from the leader.

```text
Leader

↓

Follower

↓

Follower
```

Followers remain synchronized.

---

# Example 3: Producer Write

Producer:

```text
Order Created
```

Flow:

```text
Producer

↓

Leader

↓

Follower

↓

Follower
```

The leader appends the record first.

Followers fetch the new data.

---

# Example 4: Replication

Suppose:

```text
Partition 0

Offset 100
```

Leader:

```text
Offset 101
```

Followers fetch:

```text
Offset 101
```

Eventually:

```text
Leader

101

Follower

101

Follower

101
```

All replicas become synchronized.

---

# Example 5: In-Sync Replicas (ISR)

Current replicas:

```text
Leader

↓

Follower

↓

Follower
```

All replicas are synchronized.

ISR:

```text
Leader

Follower

Follower
```

ISR size:

```text
3
```

---

# Example 6: Replica Falls Behind

Suppose:

```text
Leader

Offset 500
```

Follower:

```text
Offset 480
```

The follower is too far behind.

Kafka removes it from ISR.

Current ISR:

```text
Leader

↓

Follower
```

Fault tolerance decreases.

---

# Example 7: Broker Failure

Current cluster:

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

Broker 1 crashes.

---

# Leader Election

Kafka performs:

```text
Leader Failure

↓

Leader Election

↓

Broker 2

New Leader
```

Consumers continue reading.

Producers continue writing.

---

# Example 8: Producer During Failure

Producer:

```text
Send Message
```

Leader fails.

Producer:

```text
Retry

↓

New Leader

↓

Success
```

Retries hide temporary failures from the application.

---

# Example 9: Consumer During Failure

Consumer:

```text
Read Messages
```

Leader fails.

Kafka:

```text
Leader Election

↓

Consumer Fetches

↓

New Leader
```

Consumption resumes automatically.

---

# Example 10: Under Replicated Partition

Current state:

```text
Leader

↓

Follower

↓

Offline
```

Kafka reports:

```text
Under Replicated Partition
```

The cluster remains available but has reduced redundancy.

---

# Example 11: ISR Shrinks

Initially:

```text
Leader

Follower

Follower
```

One follower becomes slow.

ISR:

```text
Leader

Follower
```

The cluster still functions, but fault tolerance decreases.

---

# Example 12: ISR Expands

The slow follower catches up.

Before:

```text
Leader

Follower
```

After synchronization:

```text
Leader

Follower

Follower
```

ISR returns to full size.

---

# Example 13: `acks=1`

Producer:

```properties
acks=1
```

Flow:

```text
Producer

↓

Leader ACK

↓

Success
```

Followers may not yet have copied the data.

If the leader fails immediately, the latest message could be lost.

---

# Example 14: `acks=all`

Producer:

```properties
acks=all
```

Flow:

```text
Producer

↓

Leader

↓

ISR Replication

↓

ACK
```

Provides stronger durability.

---

# Example 15: `min.insync.replicas`

Configuration:

```properties
min.insync.replicas=2
```

Current ISR:

```text
Leader

↓

Follower
```

Producer:

```properties
acks=all
```

Result:

```text
Write Accepted
```

If ISR becomes:

```text
Leader Only
```

Result:

```text
Write Rejected
```

Kafka protects against data loss.

---

# Example 16: Broker Recovery

Broker returns.

```text
Broker Restart

↓

Replica Fetch

↓

Catch Up

↓

Join ISR
```

Replication returns to normal.

---

# Example 17: Multi-Broker Cluster

```text
Broker 1

Leader P0

Follower P1

Leader P2

----------------

Broker 2

Follower P0

Leader P1

Follower P2

----------------

Broker 3

Follower P0

Follower P1

Leader P2
```

Leadership is distributed across brokers.

Load becomes balanced.

---

# Example 18: Cross-Rack Replication

```text
Rack A

↓

Broker 1

----------------

Rack B

↓

Broker 2

----------------

Rack C

↓

Broker 3
```

A rack failure does not remove every replica.

---

# Example 19: Disaster Recovery

Primary cluster:

```text
Region A

↓

Kafka Cluster
```

Replication:

```text
MirrorMaker 2

↓

Region B
```

Entire regional failures can be survived.

---

# Replication Workflow

```text
Producer

↓

Leader

↓

Follower Replication

↓

ISR Updated

↓

ACK

↓

Consumer Reads
```

---

# Best Practices

- Use Replication Factor = 3 for production.
- Configure `acks=all` for important topics.
- Set an appropriate `min.insync.replicas`.
- Monitor Under Replicated Partitions.
- Monitor ISR changes.
- Replace failed brokers quickly.
- Balance leaders across brokers.
- Distribute replicas across availability zones.
- Test broker failure scenarios regularly.
- Monitor replication latency continuously.

---

# Common Mistakes

- Using Replication Factor = 1 in production.
- Assuming replication is the same as backup.
- Ignoring Under Replicated Partitions.
- Ignoring shrinking ISR.
- Running all replicas on one rack.
- Using `acks=1` for critical financial events.
- Leaving failed brokers offline for long periods.
- Never testing disaster recovery.

---

# Summary

Replication is the foundation of Kafka's fault tolerance and high availability. By maintaining multiple synchronized copies of each partition, Kafka ensures that data remains accessible even during broker failures. Concepts such as leader replicas, follower replicas, ISR, leader election, and acknowledgements work together to provide durable and resilient message storage. Understanding these mechanisms is essential for designing reliable production Kafka clusters.

---

# Key Takeaways

- Replication stores multiple copies of each partition.
- Every partition has one leader and one or more followers.
- Producers write only to the leader replica.
- Followers continuously replicate data from the leader.
- ISR contains replicas that are fully synchronized.
- Leader election enables automatic recovery from broker failures.
- `acks=all` provides stronger durability than `acks=1`.
- Replication improves availability but should always be complemented with a backup strategy.