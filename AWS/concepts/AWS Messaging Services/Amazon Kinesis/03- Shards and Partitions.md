# Introduction

A Kinesis Data Stream is made up of one or more **Shards**.

Shards are the fundamental building blocks of Amazon Kinesis Data Streams.

Every record written to a stream is stored inside a shard.

Understanding shards, partition keys, sequence numbers, and resharding is essential for designing scalable and high-throughput streaming applications.

---

# What is a Shard?

A shard is the basic unit of capacity in Amazon Kinesis Data Streams.

Each shard provides:

- Write throughput
- Read throughput
- Ordered data storage

```
Kinesis Stream

├── Shard 1

├── Shard 2

└── Shard 3
```

Applications scale by increasing or decreasing the number of shards.

---

# Why Do We Need Shards?

Imagine an application generating millions of events every second.

A single storage unit cannot process all incoming records.

Instead,

Amazon Kinesis distributes the workload across multiple shards.

```
Applications

↓

Kinesis Stream

↓

Shard 1

Shard 2

Shard 3

Shard 4
```

Each shard processes part of the traffic.

---

# Shard Capacity

Each shard provides fixed throughput.

| Operation | Capacity per Shard |
|------------|-------------------|
| Write | **1 MB/sec** or **1,000 records/sec** |
| Read | **2 MB/sec** |

If throughput exceeds these limits,

applications receive throttling errors.

---

# Stream Capacity

The total stream capacity depends on the number of shards.

Example

```
1 Shard

↓

Write

1 MB/sec

--------------------

4 Shards

↓

Write

4 MB/sec
```

Increasing shards increases throughput.

---

# Shard Architecture

```
               Kinesis Stream

      ┌────────┼────────┬────────┐

      ▼        ▼        ▼

   Shard 1  Shard 2  Shard 3

      │        │        │

      ▼        ▼        ▼

  Records   Records   Records
```

Each shard stores an ordered sequence of records.

---

# What is a Partition Key?

Every record written to Kinesis requires a **Partition Key**.

The Partition Key determines which shard stores the record.

```
Producer

↓

Partition Key

↓

Hash Function

↓

Shard
```

---

# Why is the Partition Key Important?

The Partition Key controls:

- Data distribution
- Ordering
- Load balancing

A good Partition Key distributes records evenly across all shards.

---

# Example

```
Customer-101

↓

Hash

↓

Shard 1

------------------

Customer-202

↓

Hash

↓

Shard 3
```

Different Partition Keys may be stored in different shards.

---

# Hashing Process

Amazon Kinesis uses the Partition Key to generate a hash value.

```
Partition Key

↓

MD5 Hash

↓

Hash Value

↓

Shard
```

Applications do not choose the shard directly.

Amazon Kinesis automatically maps the hash value to the correct shard.

---

# Sequence Number

Every record receives a unique **Sequence Number**.

```
Record

↓

Sequence Number

↓

4964387423847283
```

Sequence Numbers:

- Identify records
- Preserve ordering
- Support checkpointing

---

# Record Ordering

Ordering is guaranteed **within a shard**.

Example

```
Shard A

↓

Order Created

↓

Payment Received

↓

Order Shipped
```

The consumer always reads records in this order.

---

Ordering is **not guaranteed across different shards**.

```
Shard A

↓

Customer A

----------------

Shard B

↓

Customer B
```

Each shard has its own ordered sequence.

---

# Hot Shards

A hot shard occurs when one shard receives significantly more traffic than others.

```
Stream

↓

Shard 1

██████████

Shard 2

██

Shard 3

█
```

This causes:

- Throttling
- Increased latency
- Poor performance

---

# Causes of Hot Shards

Common causes include:

- Using a single Partition Key
- Uneven data distribution
- High-volume customers
- Poor key design

Example

```
Partition Key

↓

Orders
```

Every record is stored in the same shard.

---

# Good Partition Keys

Examples

```
customer-101

customer-102

customer-103

customer-104
```

Traffic is distributed evenly.

---

# Poor Partition Keys

Examples

```
Orders

Payments

Logs
```

Many records may hash to the same shard.

---

# Scaling Shards

As throughput increases,

additional shards can be added.

```
2 Shards

↓

4 Shards

↓

8 Shards
```

This process is called **Resharding**.

---

# Split Shard

A busy shard can be divided into two smaller shards.

```
Shard 1

↓

Split

↓

Shard 1

+

Shard 2
```

Benefits

- Higher throughput
- Better load balancing

---

# Merge Shards

Two low-utilization shards can be merged.

```
Shard A

+

Shard B

↓

Merged Shard
```

Benefits

- Lower cost
- Better resource utilization

---

# Resharding

Resharding changes the number of shards in a stream.

```
Current Stream

↓

Reshard

↓

Updated Stream
```

Reasons to reshard:

- Increased traffic
- Reduced traffic
- Cost optimization

---

# Consumer Reading

Consumers read records from one shard at a time.

```
Consumer

↓

Shard Iterator

↓

Shard

↓

Records
```

Multiple consumers can process the same stream independently.

---

# Example Architecture

```
Web App

↓

Kinesis Stream

↓

Shard 1

↓

Lambda

----------------

Shard 2

↓

Analytics

----------------

Shard 3

↓

Monitoring
```

---

# Monitoring Shards

Amazon CloudWatch provides shard-related metrics.

Important metrics include:

- IncomingBytes
- IncomingRecords
- OutgoingBytes
- OutgoingRecords
- ReadProvisionedThroughputExceeded
- WriteProvisionedThroughputExceeded

These metrics help identify throughput bottlenecks.

---

# Real-World Example

A ride-sharing platform receives GPS updates.

```
Driver Apps

↓

Partition Key

↓

Driver ID

↓

Kinesis Stream

↓

Multiple Shards

↓

Analytics
```

Using **Driver ID** as the Partition Key distributes traffic evenly.

---

# Best Practices

- Choose high-cardinality Partition Keys.
- Avoid using constant Partition Keys.
- Monitor shard utilization regularly.
- Scale shards before reaching throughput limits.
- Use CloudWatch to detect hot shards.
- Design for even data distribution.
- Test throughput under production-like workloads.

---

# Common Mistakes

## Using One Partition Key

This creates hot shards and limits throughput.

---

## Ignoring Shard Limits

Each shard has fixed read and write capacity.

Monitor throughput continuously.

---

## Assuming Ordering Across Shards

Ordering is guaranteed only **within a single shard**.

---

## Delaying Resharding

Waiting too long to increase shard count can lead to throttling and application delays.

---

# Summary

Shards are the core building blocks of Amazon Kinesis Data Streams, providing the read and write capacity needed to process streaming data. Partition Keys determine how records are distributed across shards, while Sequence Numbers preserve record ordering within each shard. Proper shard sizing, balanced Partition Key selection, and proactive monitoring are essential for building scalable, high-throughput, and reliable streaming applications.