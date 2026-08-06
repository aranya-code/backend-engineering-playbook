# Partition Planning

## Overview

Partitions are one of the most important design decisions in Apache Kafka. They determine how data is distributed across brokers, how consumers process data in parallel, and how the cluster scales as traffic grows.

Choosing the correct number of partitions is critical because:

- Too few partitions limit scalability.
- Too many partitions increase operational overhead.
- Changing partition counts later can impact message ordering and consumer behavior.

Partition planning should therefore be performed before deploying Kafka to production.

---

# Why Partition Planning Matters

Partitions directly affect:

- Throughput
- Consumer parallelism
- Broker utilization
- Storage distribution
- Scalability
- Failover performance

Poor partition planning often becomes one of the biggest bottlenecks in Kafka deployments.

---

# What is a Partition?

A partition is an ordered, append-only log within a topic.

Example:

```text
Orders Topic

├── Partition 0
├── Partition 1
├── Partition 2
└── Partition 3
```

Each partition can be stored on a different broker.

---

# Partition Distribution

Example cluster:

```text
                Kafka Cluster

Broker 1       Broker 2       Broker 3

P0             P1             P2

P3             P4             P5
```

Kafka spreads partitions across brokers for scalability.

---

# Why Multiple Partitions?

Suppose:

```text
Orders Topic

↓

1 Partition
```

Only one consumer can process messages.

With:

```text
Orders Topic

↓

6 Partitions
```

Up to six consumers can process messages simultaneously.

---

# Consumer Parallelism

Example:

```text
Orders Topic

↓

6 Partitions

↓

Consumer A

Consumer B

Consumer C
```

Kafka distributes partitions among consumers.

Higher partition counts increase potential parallelism.

---

# Partition Count vs Consumers

Example:

```text
6 Partitions

↓

6 Consumers
```

Each consumer processes one partition.

---

Now consider:

```text
6 Partitions

↓

10 Consumers
```

Only six consumers receive work.

Four consumers remain idle.

Consumer count cannot exceed partition count for active parallel processing.

---

# Throughput

Partitions increase throughput.

Instead of:

```text
1 Producer

↓

1 Partition
```

Kafka can process:

```text
Multiple Producers

↓

Multiple Partitions

↓

Multiple Brokers
```

Traffic is distributed across the cluster.

---

# Partition Key

Kafka selects partitions using a key.

Example:

```text
Order ID

↓

Hash Function

↓

Partition 2
```

Messages with the same key always reach the same partition.

---

# Why Keys Matter

Suppose:

```text
Order 101

↓

Created

↓

Paid

↓

Shipped
```

Using:

```text
Key = Order ID
```

All events remain in the same partition.

Ordering is preserved.

---

# No Key

Without a key:

```text
Producer

↓

Sticky Partitioner

↓

Random Partition
```

Messages are distributed automatically.

Ordering between related messages is no longer guaranteed.

---

# Ordering

Kafka guarantees ordering **within a partition only**.

Example:

```text
Partition 0

↓

Offset 1

↓

Offset 2

↓

Offset 3
```

Across partitions:

```text
Partition 0

↓

Offset 50

----------------

Partition 1

↓

Offset 12
```

Global ordering does not exist.

---

# Choosing the Number of Partitions

Consider:

- Expected throughput
- Consumer count
- Future growth
- Ordering requirements
- Broker count

There is no universal "correct" number.

---

# Estimating Partition Count

Example:

Expected throughput:

```text
200 MB/sec
```

Single partition capacity:

```text
20 MB/sec
```

Estimated partitions:

```text
200 / 20

=

10 Partitions
```

Always include additional capacity for future growth.

---

# Future Growth

Suppose today's workload:

```text
10 Consumers
```

Next year:

```text
40 Consumers
```

Planning additional partitions early avoids future reconfiguration.

---

# Increasing Partitions

Kafka allows partition count to increase.

Example:

```text
Orders

↓

4 Partitions

↓

Increase

↓

8 Partitions
```

However:

Ordering for existing keys may change.

Partition increases should be planned carefully.

---

# Reducing Partitions

Kafka cannot reduce partition count.

```text
8 Partitions

↓

Cannot Shrink

↓

Create New Topic
```

Reducing partitions requires topic migration.

---

# Hot Partitions

Suppose one key dominates traffic.

```text
Customer 100

↓

Partition 1

↓

95% Traffic
```

Other partitions remain mostly idle.

This is called a **hot partition**.

---

# Avoiding Hot Partitions

Choose keys with high cardinality.

Good:

```text
Order ID
```

Poor:

```text
Country

Status

Region
```

These values often create uneven traffic.

---

# Broker Balance

Partitions should be evenly distributed.

Good:

```text
Broker 1

4 Partitions

Broker 2

4 Partitions

Broker 3

4 Partitions
```

Poor:

```text
Broker 1

10 Partitions

Broker 2

1 Partition

Broker 3

1 Partition
```

Uneven distribution creates bottlenecks.

---

# Replication Impact

Each partition also has replicas.

Example:

```text
Partition 0

↓

Leader

↓

Follower

↓

Follower
```

More partitions mean more replica management.

---

# Too Few Partitions

Problems:

- Limited scalability
- Low consumer parallelism
- Future expansion difficult
- Higher producer contention

---

# Too Many Partitions

Problems:

- Increased memory usage
- More open file handles
- Longer leader elections
- Slower startup
- Higher controller overhead
- Increased metadata

More partitions are not always better.

---

# Partition Planning Workflow

```text
Estimate Throughput

↓

Estimate Consumers

↓

Estimate Growth

↓

Choose Keys

↓

Choose Partitions

↓

Deploy

↓

Monitor

↓

Adjust When Necessary
```

---

# Example: E-Commerce

```text
Orders Topic

12 Partitions

↓

Broker 1

P0 P3 P6 P9

↓

Broker 2

P1 P4 P7 P10

↓

Broker 3

P2 P5 P8 P11
```

Consumers:

```text
Inventory

Shipping

Analytics

Billing
```

Each Consumer Group can scale independently.

---

# Monitoring Partitions

Monitor:

- Partition size
- Throughput
- Consumer lag
- Leader distribution
- Replica health
- Hot partitions

These metrics indicate whether partition planning remains effective.

---

# Best Practices

- Plan partitions before production deployment.
- Design for future growth.
- Use high-cardinality keys.
- Distribute partitions evenly across brokers.
- Monitor partition utilization regularly.
- Increase partitions cautiously.
- Keep ordering requirements in mind.
- Balance throughput with operational complexity.

---

# Common Mistakes

- Starting with one partition for every topic.
- Creating thousands of unnecessary partitions.
- Choosing poor partition keys.
- Ignoring future scalability.
- Assuming Kafka guarantees global ordering.
- Increasing partitions without considering ordering implications.
- Allowing hot partitions to develop unnoticed.

---

# Summary

Partition planning is one of the most important aspects of designing a production Kafka cluster. The number of partitions directly influences scalability, throughput, consumer parallelism, and operational complexity. By carefully estimating workload, selecting appropriate partition keys, balancing partitions across brokers, and planning for future growth, engineers can build Kafka deployments that remain efficient and scalable as business demands evolve.

---

# Key Takeaways

- Partitions determine Kafka's scalability and parallelism.
- Consumer parallelism is limited by the number of partitions.
- Ordering is guaranteed only within a partition.
- Choose partition keys carefully to avoid hot partitions.
- Increasing partitions is possible, but reducing them is not.
- Plan partition counts based on throughput, consumers, and future growth.
- Monitor partition utilization continuously in production.
- Effective partition planning is essential for long-term Kafka performance and scalability.