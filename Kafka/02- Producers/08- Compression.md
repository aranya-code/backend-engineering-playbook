# Compression

## Overview

As Kafka applications scale, producers may send millions of messages every minute. Transmitting every message in its original size increases:

- Network bandwidth
- Storage usage
- Disk I/O
- Broker load

To improve efficiency, Kafka producers support **Compression**, which reduces the size of message batches before they are transmitted to brokers.

Compression allows Kafka to:

- Send more messages with less bandwidth
- Store less data on disk
- Improve overall throughput
- Reduce infrastructure costs

One of Kafka's key optimizations is that it compresses **entire batches**, not individual messages, resulting in significantly better compression ratios.

---

# What is Compression?

Compression is the process of reducing the size of a batch before sending it to Kafka.

Without compression:

```text
Batch

↓

120 KB

↓

Network
```

With compression:

```text
Batch

↓

Compression

↓

35 KB

↓

Network
```

The producer sends fewer bytes across the network.

---

# Why is Compression Needed?

Suppose a producer sends:

```text
1 Million Messages
```

Average message size:

```text
1 KB
```

Without compression:

```text
1 GB

↓

Network
```

With compression:

```text
300 MB

↓

Network
```

Bandwidth usage decreases dramatically.

---

# Producer Workflow with Compression

Compression occurs after batching.

```text
Application

↓

Create Message

↓

Serialize

↓

Partition

↓

Batch

↓

Compress

↓

Broker
```

The broker stores the compressed batch and decompresses it only when necessary.

---

# Why Kafka Compresses Batches

Kafka compresses batches instead of individual messages.

Without batching:

```text
Message 1

↓

Compress

-----------------

Message 2

↓

Compress

-----------------

Message 3

↓

Compress
```

With batching:

```text
Batch

Message 1

Message 2

Message 3

↓

Compress Once
```

Advantages:

- Better compression ratio
- Less CPU overhead
- Higher throughput

---

# Compression Algorithms

Kafka supports several compression algorithms.

- none
- gzip
- snappy
- lz4
- zstd

Each offers different trade-offs between compression ratio, CPU usage, and speed.

---

# No Compression

Configuration:

```properties
compression.type=none
```

Workflow:

```text
Batch

↓

Broker
```

Advantages:

- No CPU cost
- Lowest producer latency

Disadvantages:

- Highest bandwidth usage
- Largest storage requirement

Suitable only for very small workloads or low-latency scenarios.

---

# GZIP Compression

Configuration:

```properties
compression.type=gzip
```

Characteristics:

- High compression ratio
- Slower compression
- Moderate decompression speed

Advantages:

- Excellent storage savings

Disadvantages:

- Higher CPU usage

Suitable for:

- Archival workloads
- Log storage
- Lower message rates

---

# Snappy Compression

Configuration:

```properties
compression.type=snappy
```

Characteristics:

- Fast compression
- Fast decompression
- Moderate compression ratio

Advantages:

- Low CPU usage
- High throughput

Suitable for:

- General-purpose Kafka workloads

---

# LZ4 Compression

Configuration:

```properties
compression.type=lz4
```

Characteristics:

- Very fast compression
- Very fast decompression
- Good compression ratio

Advantages:

- Low latency
- Excellent throughput

Suitable for:

- Real-time event streaming
- Low-latency systems

---

# Zstandard (ZSTD)

Configuration:

```properties
compression.type=zstd
```

Characteristics:

- Excellent compression ratio
- Fast compression
- Fast decompression

Advantages:

- Lower bandwidth usage
- Lower storage usage
- Excellent overall performance

ZSTD is the recommended choice for most modern Kafka deployments.

---

# Compression Comparison

| Algorithm | Compression Ratio | Compression Speed | CPU Usage | Recommended |
|------------|------------------:|------------------:|----------:|-------------|
| none | None | Fastest | Lowest | Development only |
| gzip | Highest | Slow | High | Storage-heavy workloads |
| snappy | Medium | Fast | Low | General purpose |
| lz4 | High | Very Fast | Low | Low-latency systems |
| zstd | Very High | Fast | Medium | Most production systems |

---

# Compression and Network Usage

Without compression:

```text
Producer

↓

100 MB

↓

Broker
```

With compression:

```text
Producer

↓

30 MB

↓

Broker
```

Network traffic decreases significantly.

---

# Compression and Storage

Compressed batches are stored on disk.

Example:

```text
Original

500 GB

↓

Compressed

180 GB
```

Kafka stores the compressed representation until consumers request the data.

---

# Compression and Consumers

Consumers automatically decompress batches.

```text
Compressed Batch

↓

Consumer

↓

Decompress

↓

Messages
```

Applications do not need to perform decompression manually.

---

# Compression and Replication

Kafka replicates compressed batches.

```text
Leader

↓

Compressed Batch

↓

Follower

↓

Compressed Batch
```

Followers do not decompress the data before replication.

This reduces replication traffic between brokers.

---

# Compression and Throughput

Compression often increases throughput.

Without compression:

```text
Large Payload

↓

More Network Time
```

With compression:

```text
Smaller Payload

↓

Less Network Time

↓

Higher Throughput
```

Although compression requires CPU time, network savings usually outweigh the cost.

---

# Compression and CPU Usage

Compression requires additional CPU.

Example:

```text
Compress

↓

CPU Work
```

Trade-off:

```text
Higher CPU

↓

Lower Network Usage

↓

Higher Overall Performance
```

Modern CPUs handle compression efficiently.

---

# Producer Configuration

Enable compression:

```properties
compression.type=zstd
```

Example production configuration:

```properties
compression.type=zstd

batch.size=65536

linger.ms=5
```

Batching and compression work together to maximize performance.

---

# Real-World Example

Suppose an application sends:

```text
Order Events

↓

Batch

↓

ZSTD Compression

↓

Kafka Broker
```

Benefits:

- Lower bandwidth costs
- Smaller storage footprint
- Faster replication
- Better throughput

---

# Choosing the Right Algorithm

| Scenario | Recommended Compression |
|-----------|-------------------------|
| Learning | none |
| General Production | zstd |
| Low Latency | lz4 |
| Legacy Systems | snappy |
| Maximum Compression | gzip |

---

# Advantages

- Reduced bandwidth usage
- Lower storage costs
- Faster replication
- Better throughput
- Efficient batching
- Improved broker performance

---

# Limitations

- Additional CPU usage
- Slight increase in producer processing time
- Different algorithms have different trade-offs

These costs are generally outweighed by the reduction in network and storage overhead.

---

# Best Practices

- Enable compression in production.
- Prefer `zstd` for modern Kafka clusters.
- Combine compression with batching.
- Monitor CPU utilization.
- Test compression algorithms with real workloads.
- Avoid disabling compression for high-volume topics.

---

# Common Mistakes

- Compressing individual messages instead of batches (Kafka already handles batching automatically).
- Assuming compression always reduces latency.
- Ignoring CPU utilization.
- Using `none` for high-volume production workloads.
- Choosing an algorithm without benchmarking.

---

# Summary

Compression reduces the size of Kafka message batches before they are transmitted to brokers. By compressing batches rather than individual messages, Kafka significantly reduces network bandwidth, storage requirements, and replication traffic while improving throughput. Kafka supports multiple compression algorithms, including GZIP, Snappy, LZ4, and Zstandard (ZSTD), each offering different trade-offs between compression ratio, CPU usage, and speed. For most modern production deployments, ZSTD provides the best overall balance between performance and efficiency.

---

# Key Takeaways

- Kafka compresses batches, not individual messages.
- Compression reduces network bandwidth and storage usage.
- Compression occurs after batching and before network transmission.
- Consumers automatically decompress received batches.
- Brokers replicate compressed batches without decompressing them.
- ZSTD is the recommended compression algorithm for most production systems.
- Compression increases CPU usage but usually improves overall throughput.
- Combining batching and compression is one of Kafka's most effective performance optimizations.