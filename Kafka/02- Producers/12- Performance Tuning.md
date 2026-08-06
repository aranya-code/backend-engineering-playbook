# Performance Tuning

## Overview

Kafka producers are designed to deliver extremely high throughput with low latency. However, achieving optimal performance requires careful tuning of producer configurations based on the application's workload.

Performance tuning is not about making Kafka "faster" by changing a single property. Instead, it involves balancing:

- Throughput
- Latency
- Reliability
- CPU utilization
- Memory usage
- Network bandwidth

Different applications have different goals.

For example:

- A logging system may prioritize maximum throughput.
- A payment system may prioritize reliability.
- A trading platform may prioritize the lowest possible latency.

Understanding how producer configurations interact is essential for building efficient Kafka applications.

---

# Performance Goals

Producer tuning usually focuses on one of three goals.

```text
Maximum Throughput

↓

Maximum Reliability

↓

Lowest Latency
```

Improving one often affects the others.

---

# Throughput vs Latency

Increasing throughput usually means waiting longer to build larger batches.

```text
Larger Batches

↓

Higher Throughput

↓

Slightly Higher Latency
```

Reducing latency usually means sending messages immediately.

```text
Immediate Send

↓

Lower Latency

↓

More Network Requests
```

Choose the trade-off based on business requirements.

---

# Producer Performance Pipeline

```text
Application

↓

Serialization

↓

Buffer

↓

Batch

↓

Compression

↓

Network

↓

Broker
```

Each stage contributes to overall producer performance.

---

# Batch Size

The `batch.size` configuration determines the maximum batch size.

Example:

```properties
batch.size=65536
```

Larger batches:

- Better throughput
- Better compression
- Fewer network requests

Smaller batches:

- Lower latency
- More network overhead

---

# Linger Time

`linger.ms` determines how long Kafka waits for additional messages.

Example:

```properties
linger.ms=5
```

Workflow:

```text
Message Arrives

↓

Wait

↓

More Messages

↓

Create Larger Batch
```

Typical production values:

```text
5–20 ms
```

---

# Compression

Compression reduces network traffic.

Recommended:

```properties
compression.type=zstd
```

Benefits:

- Smaller payloads
- Lower bandwidth
- Better throughput

Trade-off:

```text
More CPU

↓

Less Network Traffic
```

---

# Buffer Memory

Producer buffering is controlled by:

```properties
buffer.memory
```

Example:

```properties
buffer.memory=67108864
```

Equivalent:

```text
64 MB
```

Larger buffers help during traffic spikes but consume more memory.

---

# Acknowledgements

Acknowledgement settings influence performance.

```text
acks=0

↓

Fastest

----------------

acks=1

↓

Balanced

----------------

acks=all

↓

Most Reliable
```

Higher reliability introduces additional latency.

---

# Retries

Retries improve reliability but can increase latency during failures.

Recommended:

```properties
retries=Integer.MAX_VALUE
```

Combined with:

```properties
enable.idempotence=true
```

retries become safe and reliable.

---

# Serialization Performance

Serialization format affects CPU usage.

| Format | Speed | Message Size |
|----------|------:|-------------:|
| String | Very Fast | Large |
| JSON | Fast | Large |
| Avro | Fast | Small |
| Protobuf | Very Fast | Very Small |

Binary formats generally provide better throughput.

---

# Message Size

Large messages reduce producer performance.

Example:

```text
100 Bytes

↓

Very Efficient
```

versus

```text
10 MB

↓

Slow

↓

High Memory Usage
```

Kafka performs best with relatively small messages.

---

# Partition Distribution

Uneven partition usage reduces throughput.

Good distribution:

```text
P0

25%

P1

25%

P2

25%

P3

25%
```

Poor distribution:

```text
P0

90%

P1

5%

P2

3%

P3

2%
```

This creates a hot partition.

---

# Network Considerations

High network latency affects producer performance.

Optimization techniques:

- Enable compression
- Increase batch size
- Use larger buffers
- Deploy brokers close to producers

---

# Hardware Considerations

Producer performance also depends on:

- CPU speed
- Available memory
- Network bandwidth
- Disk performance (broker side)

No amount of tuning can compensate for inadequate hardware.

---

# Monitoring Performance

Monitor producer metrics such as:

- Request latency
- Batch size
- Compression ratio
- Retry rate
- Record send rate
- Error rate
- Buffer utilization

Performance tuning should always be driven by measurements rather than assumptions.

---

# Recommended Configurations

## High Throughput

```properties
acks=1

batch.size=65536

linger.ms=10

compression.type=zstd

buffer.memory=67108864
```

Suitable for:

- Logging
- Analytics
- Monitoring

---

## High Reliability

```properties
acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE

compression.type=zstd
```

Suitable for:

- Orders
- Payments
- Banking

---

## Low Latency

```properties
linger.ms=0

batch.size=16384

compression.type=lz4

acks=1
```

Suitable for:

- Real-time dashboards
- Live notifications
- Trading systems

---

# Performance Tuning Workflow

```text
Measure Current Performance

↓

Identify Bottleneck

↓

Change One Configuration

↓

Benchmark

↓

Repeat
```

Avoid changing many settings simultaneously.

---

# Common Bottlenecks

| Bottleneck | Possible Solution |
|------------|-------------------|
| High Network Usage | Enable compression |
| Small Batches | Increase `batch.size` |
| Too Many Requests | Increase `linger.ms` |
| Duplicate Messages | Enable idempotence |
| High Retry Rate | Investigate broker or network issues |
| Hot Partition | Improve partition key selection |

---

# Best Practices

- Benchmark before tuning.
- Change one configuration at a time.
- Enable compression in production.
- Tune batching before increasing hardware.
- Keep idempotence enabled.
- Monitor producer metrics continuously.
- Avoid sending very large messages.
- Choose tuning goals based on business requirements.

---

# Common Mistakes

- Optimizing without measuring performance.
- Increasing every configuration value unnecessarily.
- Ignoring message size.
- Disabling batching for high-volume systems.
- Using unreliable acknowledgement settings for critical data.
- Assuming the same configuration works for every workload.

---

# Summary

Producer performance tuning involves balancing throughput, latency, reliability, and resource utilization. Kafka provides numerous configuration options—including batching, compression, acknowledgements, retries, and buffering—that work together to optimize message publishing. Effective tuning should always be based on real performance measurements and aligned with the application's business requirements rather than relying on generic settings.

---

# Key Takeaways

- Performance tuning is a balance between throughput, latency, and reliability.
- Batching and compression provide the largest throughput improvements.
- `linger.ms` and `batch.size` should be tuned together.
- Compression reduces bandwidth while increasing CPU usage.
- Message size and partition distribution significantly affect performance.
- Monitor producer metrics before making tuning decisions.
- Benchmark every configuration change.
- There is no universal "best" configuration—optimal settings depend on the workload.