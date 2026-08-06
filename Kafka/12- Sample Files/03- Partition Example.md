# Partition Example

## Overview

Partitions are the foundation of Kafka's scalability and parallel processing capabilities. Every Kafka topic is divided into one or more partitions, and every message written to a topic is stored inside one of those partitions.

Understanding how partitions work is much easier through practical examples than theory alone.

This chapter demonstrates how Kafka distributes messages across partitions, how ordering is maintained, how Consumer Groups process partitions, and how partition design impacts scalability.

---

# Example 1: Single Partition

Suppose we create a topic:

```text
orders
```

With:

```text
1 Partition
```

Architecture:

```text
Orders Topic

↓

Partition 0
```

Messages:

```text
Offset 0 → Order 101

Offset 1 → Order 102

Offset 2 → Order 103

Offset 3 → Order 104
```

Everything is stored in one partition.

---

# Processing

Consumer:

```text
Consumer A

↓

Partition 0
```

Processing order:

```text
101

↓

102

↓

103

↓

104
```

Ordering is guaranteed.

---

# Limitation

Only one consumer can process the partition.

```text
Partition 0

↓

Consumer A
```

Maximum parallelism:

```text
1
```

---

# Example 2: Multiple Partitions

Now create:

```text
Orders Topic

↓

4 Partitions
```

Architecture:

```text
Orders

├── Partition 0

├── Partition 1

├── Partition 2

└── Partition 3
```

Kafka now supports parallel processing.

---

# Example Data

Messages:

```text
Order 101

Order 102

Order 103

Order 104

Order 105

Order 106
```

---

# Without Message Keys

Kafka distributes messages.

Example:

```text
Partition 0

101

105

----------------

Partition 1

102

----------------

Partition 2

103

106

----------------

Partition 3

104
```

Distribution is approximately balanced.

---

# Parallel Consumers

Consumer Group:

```text
Consumer A

Consumer B

Consumer C

Consumer D
```

Assignments:

```text
Consumer A

↓

Partition 0

----------------

Consumer B

↓

Partition 1

----------------

Consumer C

↓

Partition 2

----------------

Consumer D

↓

Partition 3
```

All four consumers process data simultaneously.

---

# Increased Throughput

Instead of:

```text
1 Consumer

↓

100 Messages/sec
```

Now:

```text
4 Consumers

↓

400 Messages/sec
```

Parallelism improves throughput.

---

# Example 3: Using Message Keys

Producer sends:

```text
Order ID = 5001
```

Hash:

```text
5001

↓

Hash

↓

Partition 2
```

Every event with the same key goes to Partition 2.

---

# Order Events

Events:

```text
Order Created

Order Paid

Order Packed

Order Delivered
```

Kafka stores:

```text
Partition 2

↓

Created

↓

Paid

↓

Packed

↓

Delivered
```

Ordering is preserved.

---

# Example 4: Different Orders

Producer:

```text
Order 5001

↓

Partition 2
```

Producer:

```text
Order 8008

↓

Partition 1
```

Producer:

```text
Order 9010

↓

Partition 3
```

Different orders can be processed independently.

---

# Example 5: Consumer Group

Suppose:

```text
Topic

↓

6 Partitions
```

Consumers:

```text
Consumer A

Consumer B

Consumer C
```

Assignments:

```text
Consumer A

↓

Partition 0

Partition 1

----------------

Consumer B

↓

Partition 2

Partition 3

----------------

Consumer C

↓

Partition 4

Partition 5
```

Each consumer owns multiple partitions.

---

# Example 6: More Consumers Than Partitions

Suppose:

```text
4 Partitions
```

Consumers:

```text
Consumer A

Consumer B

Consumer C

Consumer D

Consumer E

Consumer F
```

Assignments:

```text
Partition 0 → Consumer A

Partition 1 → Consumer B

Partition 2 → Consumer C

Partition 3 → Consumer D

Consumer E → Idle

Consumer F → Idle
```

Extra consumers remain idle.

---

# Example 7: Consumer Failure

Before failure:

```text
Consumer A

↓

Partition 0

----------------

Consumer B

↓

Partition 1
```

Consumer B crashes.

Kafka performs:

```text
Rebalance
```

After rebalance:

```text
Consumer A

↓

Partition 0

↓

Partition 1
```

Processing continues.

---

# Example 8: Hot Partition

Poor key:

```text
Country
```

Messages:

```text
India

India

India

India

India
```

Hash:

```text
Partition 0
```

Result:

```text
Partition 0

95% Traffic
```

Other partitions remain mostly idle.

---

# Better Key

Instead:

```text
Order ID
```

Values:

```text
1001

1002

1003

1004

1005
```

Distribution:

```text
Partition 0

Partition 1

Partition 2

Partition 3
```

Traffic becomes balanced.

---

# Example 9: Ordering

Partition:

```text
Offset 0

↓

Offset 1

↓

Offset 2

↓

Offset 3
```

Consumer always reads:

```text
0

↓

1

↓

2

↓

3
```

Ordering is guaranteed within a partition.

---

# Across Partitions

Suppose:

```text
Partition 0

Order A

↓

Order C

----------------

Partition 1

Order B

↓

Order D
```

Kafka **does not guarantee**:

```text
A

↓

B

↓

C

↓

D
```

Global ordering does not exist.

---

# Example 10: Scaling

Current cluster:

```text
3 Brokers

↓

6 Partitions
```

Traffic doubles.

Solution:

```text
Add Brokers

↓

Increase Partitions

↓

Add Consumers
```

Horizontal scaling maintains performance.

---

# Real-World Example

E-commerce platform:

```text
Customer

↓

Order Service

↓

Kafka

↓

Orders Topic

↓

8 Partitions

↓

Inventory

↓

Payment

↓

Shipping

↓

Analytics
```

Each service processes partitions independently.

---

# Partition Design Guidelines

Choose partition keys that:

- Have high cardinality
- Evenly distribute traffic
- Preserve required ordering
- Avoid hotspots

Good examples:

- Order ID
- Customer ID
- User ID
- Transaction ID

Poor examples:

- Country
- Status
- Payment Type
- Boolean values

---

# Best Practices

- Design partition count for future growth.
- Use meaningful message keys.
- Keep related events in the same partition.
- Monitor partition distribution.
- Avoid hot partitions.
- Scale consumers according to partition count.
- Balance partitions across brokers.
- Review partition strategy before production deployment.
- Monitor partition-level throughput.
- Revisit partition sizing as workloads evolve.

---

# Common Mistakes

- Using only one partition for high-volume workloads.
- Creating thousands of unnecessary partitions.
- Choosing low-cardinality keys.
- Assuming Kafka guarantees global ordering.
- Adding consumers without increasing partitions.
- Ignoring partition imbalance.
- Using random keys when ordering is required.
- Changing partition counts without understanding the impact on key distribution.

---

# Summary

Partitions are the primary mechanism that allows Kafka to scale horizontally while preserving ordering within related streams of data. By distributing messages across multiple partitions, Kafka enables parallel processing, higher throughput, and fault-tolerant architectures. Choosing appropriate partition counts and message keys is one of the most important design decisions in any Kafka deployment, as it directly affects scalability, ordering guarantees, and overall system performance.

---

# Key Takeaways

- Topics are divided into one or more partitions.
- Partitions enable horizontal scalability and parallel processing.
- Ordering is guaranteed only within a partition.
- Message keys determine partition selection.
- One partition can be processed by only one consumer within a Consumer Group.
- High-cardinality keys provide better load distribution.
- Poor partitioning strategies can create hotspots and reduce throughput.
- Careful partition design is essential for building scalable Kafka systems.