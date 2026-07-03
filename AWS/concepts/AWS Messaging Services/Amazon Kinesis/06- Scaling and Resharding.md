# Introduction

Data streaming workloads are rarely constant.

An application may process:

- Thousands of records per second today
- Millions of records per second tomorrow

Amazon Kinesis Data Streams is designed to scale as your workload changes.

Scaling is achieved by changing the number of **Shards** in a stream.

This process is known as **Resharding**.

---

# Why Scaling is Required

Imagine an e-commerce application during a normal day.

```
Traffic

↓

2 Shards

↓

Healthy
```

Now consider a major shopping event.

```
Black Friday

↓

10x Traffic

↓

2 Shards

↓

Throttling
```

The existing shards cannot handle the increased throughput.

Additional shards are required.

---

# What is Scaling?

Scaling means increasing or decreasing stream capacity by changing the number of shards.

```
Current Stream

↓

2 Shards

↓

Scale

↓

6 Shards
```

More shards provide more throughput.

---

# Types of Scaling

Amazon Kinesis supports two scaling approaches.

- Scale Out
- Scale In

---

# Scale Out

Scale Out increases the number of shards.

```
2 Shards

↓

Split

↓

4 Shards
```

Benefits

- Higher write throughput
- Higher read throughput
- Better load distribution

---

# Scale In

Scale In decreases the number of shards.

```
4 Shards

↓

Merge

↓

2 Shards
```

Benefits

- Lower AWS cost
- Better resource utilization

---

# What is Resharding?

Resharding is the process of changing shard count.

```
Stream

↓

Split

or

Merge

↓

Updated Stream
```

Resharding allows Kinesis to adapt to changing workloads.

---

# Split Shard

A heavily utilized shard can be divided into two.

```
Before

────────────

Shard A

────────────

↓

Split

↓

────────────

Shard A1

Shard A2

────────────
```

---

## Why Split a Shard?

Split when:

- Write throughput is high
- Read throughput is high
- Hot shard detected
- Application growth

---

# Merge Shards

Two lightly utilized shards can be merged.

```
Before

Shard A

Shard B

↓

Merge

↓

Shard AB
```

---

## Why Merge Shards?

Merge when:

- Traffic decreases
- Costs need optimization
- Resources are underutilized

---

# Resharding Workflow

```
Monitor Stream

↓

Detect High Utilization

↓

Split Shard

↓

Traffic Distributed

↓

Performance Improved
```

---

# Scaling Example

Initial architecture

```
Applications

↓

Kinesis Stream

↓

Shard 1

Shard 2
```

After scaling

```
Applications

↓

Kinesis Stream

↓

Shard 1

Shard 2

Shard 3

Shard 4

Shard 5
```

---

# Hot Shards

A Hot Shard receives much more traffic than other shards.

```
Shard 1

████████████

Shard 2

██

Shard 3

█
```

Symptoms

- High latency
- Throttling
- Slow consumers

---

# Causes of Hot Shards

Common reasons include:

- Poor Partition Key selection
- One customer generating most traffic
- Uneven workload
- Fixed Partition Keys

Example

```
Partition Key

↓

Orders
```

Every record hashes to the same shard.

---

# Avoiding Hot Shards

Use high-cardinality Partition Keys.

Good

```
customer-101

customer-102

customer-103
```

Poor

```
Orders
```

---

# Manual Scaling

Developers manually update shard count.

Workflow

```
CloudWatch

↓

High Utilization

↓

Split Shard

↓

Increase Capacity
```

Suitable for predictable workloads.

---

# On-Demand Mode

Amazon Kinesis also supports **On-Demand Capacity Mode**.

```
Traffic Increases

↓

Amazon Kinesis

↓

Automatic Scaling
```

No shard planning is required.

---

## Benefits

- No capacity planning
- Automatic scaling
- Handles unpredictable workloads
- Simplified operations

---

## Best For

- Startup applications
- Seasonal traffic
- Unknown workloads
- Rapidly growing systems

---

# Provisioned Mode

Provisioned Mode requires developers to manage shard count.

```
Developer

↓

Create Stream

↓

Specify Shards

↓

Manage Capacity
```

---

## Best For

- Predictable workloads
- Stable traffic
- Cost optimization

---

# Provisioned vs On-Demand

| Feature | Provisioned | On-Demand |
|----------|-------------|-----------|
| Capacity Planning | Required | Not Required |
| Shard Management | Manual | Automatic |
| Predictable Workloads | Excellent | Good |
| Unpredictable Workloads | Moderate | Excellent |
| Operational Effort | Higher | Lower |

---

# Monitoring Scaling

CloudWatch metrics help determine when scaling is required.

Important metrics include:

- IncomingBytes
- IncomingRecords
- OutgoingBytes
- OutgoingRecords
- WriteProvisionedThroughputExceeded
- ReadProvisionedThroughputExceeded

---

# Write Throttling

If producers exceed shard capacity,

Amazon Kinesis returns:

```
ProvisionedThroughputExceededException
```

Workflow

```
Producer

↓

Too Many Records

↓

Shard Limit Exceeded

↓

Throttling
```

---

# Read Throttling

Consumers can also exceed read limits.

```
Consumer

↓

Too Many Reads

↓

Read Limit Exceeded
```

Solutions

- Increase shards
- Reduce polling frequency
- Use Enhanced Fan-Out

---

# Enhanced Fan-Out

Enhanced Fan-Out reduces read contention.

```
Shard

↓

Dedicated Throughput

↓

Consumer A

----------------

Dedicated Throughput

↓

Consumer B
```

Useful when multiple consumers process the same stream.

---

# Scaling Strategy

```
Monitor

↓

CloudWatch

↓

Detect Bottleneck

↓

Scale Out

↓

Monitor Again
```

Scaling should be continuous.

---

# Real-World Example

A sports streaming platform receives millions of events during a live match.

```
Users

↓

Kinesis

↓

Traffic Spike

↓

Automatic Scaling

↓

Analytics

↓

Dashboard
```

The stream scales without downtime.

---

# Best Practices

- Use On-Demand mode for unpredictable workloads.
- Monitor CloudWatch continuously.
- Scale before reaching throughput limits.
- Design Partition Keys carefully.
- Avoid hot shards.
- Batch writes using `PutRecords`.
- Use Enhanced Fan-Out for multiple high-throughput consumers.
- Review shard utilization regularly.

---

# Common Mistakes

## Waiting Until Throttling Occurs

Scale proactively rather than reacting to failures.

---

## Using Poor Partition Keys

Uneven distribution creates hot shards and wastes capacity.

---

## Ignoring CloudWatch Metrics

CloudWatch provides early indicators of throughput issues.

---

## Over-Provisioning Shards

Too many shards increase costs unnecessarily.

Review utilization and merge underused shards.

---

## Choosing the Wrong Capacity Mode

Use:

- **Provisioned Mode** for predictable workloads.
- **On-Demand Mode** for variable or unknown traffic patterns.

---

# Summary

Scaling is a core capability of Amazon Kinesis Data Streams. By increasing or decreasing the number of shards through resharding, applications can adapt to changing workloads while maintaining low latency and high throughput. Features such as On-Demand Capacity Mode, Enhanced Fan-Out, and CloudWatch monitoring simplify stream management and help build resilient, production-ready streaming systems capable of handling millions of events per second.