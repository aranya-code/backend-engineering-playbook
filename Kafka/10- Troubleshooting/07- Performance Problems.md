# Performance Problems

## Overview

Apache Kafka is designed to handle millions of messages per second with low latency and high throughput. However, poorly configured clusters, inefficient applications, hardware limitations, or infrastructure bottlenecks can significantly degrade performance.

Performance issues rarely originate from a single component. They may involve:

- Producers
- Consumers
- Brokers
- Storage
- Network
- JVM
- Operating System
- Application Design

This chapter explains common Kafka performance problems, how to diagnose them, and recommended solutions.

---

# Symptoms of Performance Problems

A slow Kafka cluster may exhibit:

- High producer latency
- High consumer lag
- Slow message delivery
- Increased request latency
- Low throughput
- High CPU utilization
- High disk usage
- Frequent timeouts
- Long garbage collection pauses

Performance degradation usually develops gradually before becoming critical.

---

# Kafka Performance Pipeline

```text
Producer

↓

Network

↓

Broker

↓

Disk

↓

Replication

↓

Consumer

↓

Application
```

A bottleneck at any stage impacts the entire pipeline.

---

# Performance Bottlenecks

Common bottlenecks include:

- Producer
- Consumer
- Broker
- Disk
- CPU
- Memory
- Network
- Replication
- Serialization
- Database

Performance tuning should begin by identifying the bottleneck.

---

# High Producer Latency

### Symptoms

```text
Send()

↓

Slow Response
```

---

### Possible Causes

- Slow brokers
- Large messages
- High network latency
- Disk bottlenecks
- Excessive acknowledgements

---

### Solution

Check:

- Producer latency
- Broker health
- Disk performance
- Network latency

---

# High Consumer Lag

Symptoms:

```text
Producer

↓

Consumer Behind
```

---

### Causes

- Slow processing
- Database bottlenecks
- External APIs
- Too few consumers

---

### Solution

Optimize consumer processing before scaling infrastructure.

---

# Low Throughput

Example:

Expected:

```text
500 MB/sec
```

Actual:

```text
80 MB/sec
```

---

### Possible Causes

- Small batches
- Too many acknowledgements
- Network bottlenecks
- Slow disks

---

### Solution

Tune:

- Batch size
- Compression
- Partitions
- Network

---

# High CPU Usage

### Symptoms

```text
CPU

95%
```

---

### Causes

- Compression
- Encryption
- Serialization
- Excessive requests
- Too many partitions

---

### Solution

Monitor:

- JVM
- Request rate
- Compression settings

Scale brokers if required.

---

# High Memory Usage

Symptoms:

```text
Memory Increasing
```

---

### Causes

- Large heap
- Too many partitions
- Memory leaks
- Large requests

---

### Solution

Monitor:

- Heap
- Page cache
- Garbage collection

Tune JVM carefully.

---

# Disk Bottlenecks

Kafka relies heavily on disk performance.

Symptoms:

```text
High Disk Latency
```

Effects:

- Slow replication
- Slow consumers
- High producer latency

---

### Solution

Use:

- NVMe SSD
- Enterprise SSD

Avoid slow HDDs for production workloads.

---

# Network Bottlenecks

Symptoms:

- Producer retries
- Slow fetch requests
- High latency

---

### Diagnosis

Check:

- Bandwidth
- Packet loss
- Network utilization

---

### Solution

Upgrade networking or reduce unnecessary traffic.

---

# Too Many Partitions

Example:

```text
100 Topics

↓

500 Partitions Each
```

Result:

```text
50,000 Partitions
```

Effects:

- High memory usage
- Controller overhead
- Slow startup

---

### Solution

Reduce unnecessary partitions.

Plan partition count carefully.

---

# Too Few Partitions

Example:

```text
2 Partitions

↓

20 Consumers
```

Most consumers remain idle.

---

### Solution

Increase partition count based on throughput requirements.

---

# Large Messages

Symptoms:

```text
RecordTooLargeException

OR

High Latency
```

Large messages increase:

- Serialization time
- Network traffic
- Disk usage

---

### Solution

Keep messages reasonably small.

Store large files externally.

---

# Compression Problems

Compression reduces bandwidth but increases CPU usage.

Example:

```text
Producer

↓

Compression

↓

Broker
```

---

### Recommendation

Use:

- zstd
- lz4

Balance CPU usage against bandwidth savings.

---

# Frequent Rebalancing

Frequent rebalances cause:

```text
Pause Consumption

↓

Consumer Lag

↓

Lower Throughput
```

---

### Solution

Use:

- Static membership
- Cooperative rebalancing

Avoid unnecessary consumer restarts.

---

# Slow Replication

Symptoms:

```text
ISR Shrinking
```

Possible causes:

- Slow disks
- Network latency
- Busy brokers

---

### Solution

Monitor replication metrics continuously.

---

# JVM Garbage Collection

Long GC pauses:

```text
Stop The World

↓

Broker Pauses

↓

High Latency
```

---

### Solution

Monitor:

- Heap usage
- GC frequency
- GC duration

Avoid excessively large JVM heaps.

---

# Page Cache

Kafka benefits from the operating system page cache.

Too little available memory reduces cache efficiency.

```text
Disk

↓

Page Cache

↓

Consumer
```

Maintain sufficient free RAM for caching.

---

# Producer Configuration

Performance-related settings:

```properties
batch.size

linger.ms

compression.type

acks
```

These settings significantly affect throughput.

---

# Consumer Configuration

Important settings:

```properties
fetch.min.bytes

fetch.max.bytes

max.poll.records
```

Tune them according to workload characteristics.

---

# Broker Configuration

Important broker settings include:

- Log retention
- Replica fetch size
- Network threads
- I/O threads

Incorrect values can limit throughput.

---

# Monitoring Performance

Monitor:

- Request latency
- Throughput
- Consumer lag
- Producer retries
- CPU
- Memory
- Disk
- Network
- JVM
- ISR

Performance tuning should always be based on measurable metrics.

---

# Performance Troubleshooting Workflow

```text
Performance Issue

↓

Collect Metrics

↓

Identify Bottleneck

↓

CPU?

↓

Memory?

↓

Disk?

↓

Network?

↓

Producer?

↓

Consumer?

↓

Fix

↓

Validate
```

Always verify improvements after making changes.

---

# Quick Diagnosis Table

| Problem | Possible Cause | Recommended Action |
|----------|----------------|--------------------|
| High Producer Latency | Slow broker | Check broker health |
| High Consumer Lag | Slow consumers | Optimize processing |
| Low Throughput | Small batches | Tune producer configuration |
| High CPU | Compression | Monitor CPU and tune settings |
| High Memory | Too many partitions | Reduce partition count |
| Slow Replication | Disk bottleneck | Improve storage |
| Frequent Rebalances | Consumer instability | Stabilize Consumer Group |
| Long GC Pauses | Large heap | Tune JVM |

---

# Best Practices

- Monitor performance continuously.
- Use SSD or NVMe storage.
- Plan partitions carefully.
- Keep messages small.
- Enable compression appropriately.
- Batch producer requests.
- Optimize consumer processing.
- Monitor JVM metrics.
- Tune producers, consumers, and brokers together.
- Validate every performance change with benchmarks.

---

# Common Mistakes

- Tuning Kafka without collecting metrics.
- Blaming Kafka when downstream systems are slow.
- Creating excessive partitions.
- Ignoring disk performance.
- Sending oversized messages.
- Increasing JVM heap unnecessarily.
- Restarting brokers instead of finding the bottleneck.
- Optimizing one component while ignoring the rest of the pipeline.

---

# Summary

Kafka performance depends on the combined behavior of producers, brokers, consumers, storage, networking, JVM configuration, and application design. Performance issues should be diagnosed systematically using metrics rather than assumptions. By identifying bottlenecks, optimizing configurations, using appropriate hardware, and continuously monitoring key performance indicators, engineers can build Kafka clusters capable of delivering high throughput and low latency under production workloads.

---

# Key Takeaways

- Performance bottlenecks can occur anywhere in the Kafka pipeline.
- Always diagnose issues using metrics before tuning.
- Disk, network, CPU, and memory are the most common infrastructure bottlenecks.
- Producer batching, compression, and consumer optimization significantly affect throughput.
- Monitor request latency, consumer lag, JVM metrics, and replication health.
- Plan partition counts carefully to balance scalability and operational overhead.
- Validate tuning changes with benchmarks and production metrics.
- Continuous monitoring is essential for maintaining high Kafka performance.