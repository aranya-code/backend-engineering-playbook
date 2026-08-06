# Producer Batching

## Overview

One of the biggest reasons Kafka achieves extremely high throughput is **Batching**.

Instead of sending every message individually over the network, Kafka producers collect multiple messages together into a **batch** and send them as a single request.

Batching significantly reduces:

- Network overhead
- CPU usage
- System calls
- Broker load

while dramatically increasing:

- Throughput
- Resource utilization
- Overall performance

Without batching, Kafka would require a network request for every message, making it impossible to achieve millions of messages per second.

---

# What is Batching?

Batching is the process of grouping multiple messages into a single request before sending them to Kafka.

Without batching:

```text
Producer

↓

Message 1

↓

Broker

--------------------

Producer

↓

Message 2

↓

Broker

--------------------

Producer

↓

Message 3

↓

Broker
```

Three messages require three network requests.

With batching:

```text
Producer

↓

Batch

Message 1

Message 2

Message 3

↓

Broker
```

Only one network request is required.

---

# Why is Batching Needed?

Network communication is expensive.

Every request requires:

- TCP communication
- Network latency
- Broker processing
- Response handling

Suppose an application produces:

```text
100,000 Messages
```

Without batching:

```text
100,000 Network Requests
```

With batching:

```text
100,000 Messages

↓

2,000 Batches

↓

2,000 Network Requests
```

The improvement is substantial.

---

# Producer Workflow with Batching

```text
Application

↓

Create Message

↓

Serialize

↓

Choose Partition

↓

Record Accumulator

↓

Batch

↓

Compress

↓

Broker
```

Batching occurs after buffering and before compression.

---

# Record Accumulator

The Record Accumulator is responsible for batching.

```text
Producer

↓

Record Accumulator

↓

Batch

↓

Sender Thread
```

Messages destined for the same partition are grouped together.

---

# Partition-Based Batching

Each partition has its own batches.

Example:

```text
Orders Topic

Partition 0

Batch A

----------------

Partition 1

Batch B

----------------

Partition 2

Batch C
```

Kafka never mixes messages from different partitions into the same batch.

---

# Batch Lifecycle

```text
Create Batch

↓

Add Messages

↓

Batch Full?

↓

Yes

↓

Send

↓

Create New Batch
```

This cycle repeats continuously while the producer is running.

---

# When Does Kafka Send a Batch?

Kafka sends a batch when one of the following occurs:

- Batch reaches its maximum size.
- The configured wait time expires.
- The producer is flushed.
- The producer is closed.

---

# batch.size

The maximum size of a batch.

Example:

```properties
batch.size=16384
```

Equivalent to:

```text
16 KB
```

Workflow:

```text
Messages

↓

16 KB Reached

↓

Send Batch
```

Larger values increase throughput but consume more memory.

---

# linger.ms

Kafka does not immediately send a partially filled batch.

Instead, it can wait briefly for additional messages.

Example:

```properties
linger.ms=5
```

Workflow:

```text
Message Arrives

↓

Wait

5 ms

↓

More Messages?

↓

Yes

↓

Larger Batch
```

This improves batching efficiency.

---

# Example Timeline

Suppose:

```properties
linger.ms=10
```

Timeline:

```text
0 ms

Message A

↓

4 ms

Message B

↓

8 ms

Message C

↓

10 ms

Send Batch
```

Instead of three requests:

```text
One Batch
```

---

# Large Batch Example

Suppose:

```properties
batch.size=64 KB
```

Kafka continues adding messages until:

```text
64 KB

↓

Send Batch
```

Even if `linger.ms` has not expired.

---

# Small Batch Example

Suppose:

```properties
batch.size=1 KB
```

Kafka creates many small batches.

```text
Message

↓

Small Batch

↓

Network
```

Advantages:

- Lower latency

Disadvantages:

- Higher network overhead

---

# Large Batch Example

Suppose:

```properties
batch.size=128 KB
```

Advantages:

- Higher throughput
- Better compression
- Fewer requests

Disadvantages:

- Higher memory usage
- Slightly higher latency

---

# Batching and Compression

Compression occurs after batching.

```text
Messages

↓

Batch

↓

Compression

↓

Broker
```

Compressing an entire batch is much more efficient than compressing individual messages.

---

# Batching and Throughput

Without batching:

```text
1000 Messages

↓

1000 Requests
```

With batching:

```text
1000 Messages

↓

20 Requests
```

The producer spends less time performing network operations.

---

# Batching and Latency

Batching introduces a small delay.

Example:

```text
Message Arrives

↓

Wait 5 ms

↓

Send
```

The delay is intentional.

It allows Kafka to build larger batches.

Trade-off:

```text
Higher Throughput

↓

Slightly Higher Latency
```

---

# Batching and Ordering

Batching does **not** affect message ordering.

Example:

```text
Message A

↓

Message B

↓

Message C
```

Kafka preserves their order inside the batch.

Ordering within a partition remains guaranteed.

---

# Producer Flush

Sometimes applications need to send batches immediately.

Example:

```text
Producer

↓

flush()

↓

Send All Batches
```

This forces the producer to transmit every buffered message without waiting.

Common use cases:

- Application shutdown
- Critical events
- Testing

---

# Producer Close

When a producer shuts down:

```text
Producer

↓

Flush Remaining Batches

↓

Close Connections
```

Kafka ensures buffered messages are sent before closing.

---

# Configuration Example

```properties
batch.size=65536

linger.ms=5

compression.type=zstd
```

This combination provides:

- Good throughput
- Efficient compression
- Reasonable latency

---

# Performance Trade-offs

| Smaller Batches | Larger Batches |
|-----------------|----------------|
| Lower latency | Higher throughput |
| More requests | Fewer requests |
| Less memory | More memory |
| Less efficient compression | Better compression |

Choose settings based on application requirements.

---

# Advantages

- Higher throughput
- Reduced network traffic
- Lower CPU overhead
- Better compression
- Improved broker efficiency
- Lower operating costs

---

# Best Practices

- Enable batching for production workloads.
- Use a reasonable `linger.ms` value (typically 5–20 ms).
- Tune `batch.size` based on message size.
- Combine batching with compression.
- Monitor batch size metrics.
- Avoid disabling batching unless extremely low latency is required.

---

# Common Mistakes

- Assuming every `send()` immediately contacts Kafka.
- Setting `linger.ms` excessively high.
- Using very small batch sizes.
- Ignoring memory usage when increasing `batch.size`.
- Forgetting that batching happens separately for each partition.

---

# Summary

Producer batching groups multiple messages into a single network request before sending them to Kafka. By reducing the number of requests, batching significantly improves throughput, lowers network overhead, and increases overall efficiency. Kafka performs batching automatically using the Record Accumulator, with behavior controlled primarily by the `batch.size` and `linger.ms` configurations. Combined with compression, batching is one of the key reasons Kafka can process millions of messages per second.

---

# Key Takeaways

- Batching groups multiple messages into a single request.
- The Record Accumulator builds batches in memory.
- Kafka creates separate batches for each partition.
- `batch.size` controls the maximum batch size.
- `linger.ms` controls how long Kafka waits for additional messages.
- Larger batches improve throughput but increase latency slightly.
- Compression is applied after batching.
- Batching is one of Kafka's most important performance optimizations.