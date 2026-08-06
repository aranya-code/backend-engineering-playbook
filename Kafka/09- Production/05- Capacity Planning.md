# Capacity Planning

## Overview

Capacity planning is the process of estimating the infrastructure required to run Kafka reliably as workloads grow. A well-planned Kafka cluster should have sufficient storage, CPU, memory, network bandwidth, and partitions to support both current and future traffic.

Poor capacity planning often results in:

- Full disks
- Slow consumers
- High latency
- Frequent broker failures
- Expensive emergency scaling

Good capacity planning allows Kafka to scale predictably while maintaining high availability and performance.

---

# Why Capacity Planning Matters

Suppose today's workload is:

```text
100 GB/day
```

Six months later:

```text
2 TB/day
```

If the cluster was designed only for today's traffic:

```text
Disk Full

↓

Broker Failure

↓

Application Downtime
```

Capacity planning prevents these situations.

---

# Capacity Planning Components

A Kafka cluster must be planned across multiple dimensions.

```text
Storage

↓

CPU

↓

Memory

↓

Network

↓

Partitions

↓

Replication

↓

Future Growth
```

Each component influences overall cluster performance.

---

# Planning Workflow

```text
Estimate Traffic

↓

Estimate Storage

↓

Estimate Throughput

↓

Estimate Brokers

↓

Estimate Partitions

↓

Deploy

↓

Monitor

↓

Scale
```

Capacity planning is an ongoing process rather than a one-time activity.

---

# Estimate Message Volume

Start by estimating the number of messages.

Example:

```text
100 Million Messages

Per Day
```

Also estimate:

- Peak traffic
- Average traffic
- Seasonal traffic

Peak load is often more important than average load.

---

# Estimate Message Size

Average message size:

```text
2 KB
```

Daily storage:

```text
100 Million

×

2 KB

=

200 GB
```

Always use realistic production data.

---

# Daily Storage Requirement

Example:

```text
Daily Traffic

200 GB
```

Retention:

```text
7 Days
```

Storage required:

```text
200 GB

×

7

=

1.4 TB
```

---

# Replication Impact

Suppose:

```text
Replication Factor = 3
```

Storage becomes:

```text
1.4 TB

×

3

=

4.2 TB
```

Replication significantly increases storage requirements.

---

# Storage Formula

A simplified estimate:

```text
Storage

=

Daily Data

×

Retention

×

Replication Factor
```

Always include additional free space.

---

# Free Disk Space

Never run Kafka disks near full capacity.

Recommended:

```text
Maximum Disk Usage

70–80%
```

Leave room for:

- Traffic spikes
- Rebalancing
- Recovery
- Broker replacement

---

# Throughput Planning

Estimate:

```text
Messages/sec
```

Example:

```text
50,000 Messages/sec
```

Or:

```text
250 MB/sec
```

These values help determine broker count.

---

# Peak Throughput

Always size for peak traffic.

Example:

Average:

```text
100 MB/sec
```

Peak:

```text
500 MB/sec
```

Infrastructure should support peak load.

---

# Broker Sizing

Broker count depends on:

- Storage
- Throughput
- Replication
- Availability

Typical production clusters:

```text
3 Brokers

↓

Small

----------------

5 Brokers

↓

Medium

----------------

7+

↓

Large
```

---

# CPU Planning

Monitor expected CPU usage.

High CPU consumers:

- Compression
- Encryption
- Serialization
- Replication

Aim to keep sustained CPU utilization below approximately:

```text
70%
```

to allow headroom for spikes.

---

# Memory Planning

Kafka uses memory for:

- JVM Heap
- Page Cache
- Network Buffers

Example server:

```text
64 GB RAM

↓

6 GB Heap

↓

58 GB Page Cache
```

Kafka benefits more from page cache than a very large JVM heap.

---

# Network Planning

Kafka is network intensive.

Estimate:

- Producer traffic
- Consumer traffic
- Replication traffic

Replication also consumes bandwidth.

---

# Network Example

Suppose:

```text
Incoming

200 MB/sec
```

Replication Factor:

```text
3
```

Actual network traffic becomes significantly higher due to replication.

---

# Disk Performance

Kafka performs sequential writes.

Preferred storage:

- NVMe SSD
- Enterprise SSD

Avoid:

- Slow HDDs
- Shared network storage
- High-latency disks

Disk performance directly affects throughput.

---

# Partition Planning

Capacity planning also includes partitions.

Consider:

- Consumer parallelism
- Future scaling
- Broker count
- Expected throughput

Too many partitions increase metadata and memory usage.

---

# Topic Growth

Estimate future topics.

Today:

```text
20 Topics
```

Next year:

```text
100 Topics
```

Infrastructure should support expected growth.

---

# Consumer Growth

Today:

```text
5 Consumers
```

Next year:

```text
50 Consumers
```

Ensure sufficient partitions for future scaling.

---

# Retention Planning

Longer retention requires more storage.

Example:

```text
7 Days

↓

1 TB

----------------

30 Days

↓

4.3 TB
```

Retention is one of the largest contributors to storage requirements.

---

# Capacity Example

Suppose:

Daily traffic:

```text
300 GB
```

Retention:

```text
14 Days
```

Replication:

```text
3
```

Storage:

```text
300

×

14

×

3

=

12.6 TB
```

Additional free space:

```text
20%

↓

≈15 TB Recommended
```

---

# Growth Planning

Always estimate future growth.

```text
Year 1

↓

1 TB

↓

Year 2

↓

3 TB

↓

Year 3

↓

6 TB
```

Scaling plans should anticipate business growth.

---

# Monitoring Capacity

Track:

- Storage growth
- Throughput
- Partition growth
- Consumer growth
- CPU usage
- Memory usage
- Network utilization

Historical metrics improve forecasting accuracy.

---

# Scaling Strategy

When capacity limits are reached:

```text
Add Brokers

↓

Rebalance Partitions

↓

Increase Capacity
```

Horizontal scaling is preferred over replacing servers with significantly larger machines.

---

# Capacity Planning Checklist

Verify:

| Item | Status |
|------|--------|
| Traffic estimated | ✅ |
| Peak throughput estimated | ✅ |
| Message size calculated | ✅ |
| Storage estimated | ✅ |
| Replication included | ✅ |
| Retention included | ✅ |
| Broker count planned | ✅ |
| Partition count planned | ✅ |
| CPU capacity estimated | ✅ |
| Memory capacity estimated | ✅ |
| Network capacity estimated | ✅ |
| Future growth estimated | ✅ |

---

# Capacity Planning Tools

Useful tools include:

- Prometheus
- Grafana
- JMX Metrics
- Kafka Exporter
- Cloud Monitoring Services

These tools help validate planning assumptions using real production metrics.

---

# Best Practices

- Plan for peak traffic rather than average traffic.
- Include replication in storage calculations.
- Keep disk utilization below 80%.
- Leave headroom for future growth.
- Monitor capacity continuously.
- Scale horizontally by adding brokers.
- Revisit capacity plans regularly.
- Validate estimates using production metrics.
- Consider retention policies when estimating storage.
- Document all capacity assumptions.

---

# Common Mistakes

- Planning only for current traffic.
- Ignoring replication overhead.
- Filling disks close to 100%.
- Underestimating network bandwidth.
- Creating too many partitions.
- Ignoring seasonal traffic spikes.
- Using average throughput instead of peak throughput.
- Neglecting long-term business growth.

---

# Summary

Capacity planning ensures that a Kafka cluster has sufficient resources to support current workloads while accommodating future growth. By estimating message volume, throughput, storage, replication overhead, retention requirements, and infrastructure resources, organizations can build scalable Kafka deployments that avoid costly outages and emergency expansions. Regular monitoring and periodic reassessment keep capacity plans aligned with changing business demands.

---

# Key Takeaways

- Capacity planning is essential for reliable Kafka operations.
- Estimate storage using message volume, retention, and replication.
- Size infrastructure based on peak throughput rather than average traffic.
- Monitor CPU, memory, network, and disk usage continuously.
- Keep disk utilization below recommended limits to allow operational headroom.
- Plan partitions and brokers for future scalability.
- Validate planning assumptions with production metrics.
- Capacity planning should be an ongoing operational process rather than a one-time exercise.