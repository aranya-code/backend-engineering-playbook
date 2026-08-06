# Producer Configuration

## Overview

Kafka producers expose a rich set of configuration properties that control how messages are published to the Kafka cluster. These configurations influence nearly every aspect of producer behavior, including:

- Reliability
- Performance
- Throughput
- Latency
- Memory usage
- Network utilization
- Fault tolerance

A well-configured producer can reliably process millions of messages per second while maintaining low latency and high durability.

This chapter focuses on the most important producer configurations used in production environments and explains how they work together.

---

# Why Producer Configuration Matters

Consider two different applications.

### Logging System

Requirements:

- Maximum throughput
- Low latency
- Occasional message loss acceptable

---

### Banking System

Requirements:

- Zero message loss
- No duplicate messages
- High durability

Although both applications use Kafka producers, their configurations should be completely different.

Kafka allows producers to be tuned according to business requirements.

---

# Producer Configuration Categories

Kafka producer properties can be grouped into several categories.

```text
Connection

↓

Serialization

↓

Reliability

↓

Performance

↓

Memory

↓

Timeouts

↓

Security
```

Understanding these categories makes producer tuning much easier.

---

# Connection Configuration

## bootstrap.servers

Defines the initial Kafka brokers used to connect to the cluster.

Example:

```properties
bootstrap.servers=broker1:9092,broker2:9092,broker3:9092
```

The producer only needs one reachable broker.

After connecting, Kafka automatically discovers the remaining brokers.

---

## client.id

Identifies the producer instance.

Example:

```properties
client.id=order-service
```

Useful for:

- Logging
- Monitoring
- Metrics
- Troubleshooting

---

# Serialization Configuration

## key.serializer

Specifies how message keys are converted into bytes.

Example:

```properties
key.serializer=org.apache.kafka.common.serialization.StringSerializer
```

---

## value.serializer

Specifies how message values are serialized.

Example:

```properties
value.serializer=org.springframework.kafka.support.serializer.JsonSerializer
```

Both serializers are mandatory.

Without them, the producer cannot send data.

---

# Reliability Configuration

## acks

Controls when Kafka acknowledges a message.

Example:

```properties
acks=all
```

Options:

| Value | Description |
|--------|-------------|
| 0 | No acknowledgement |
| 1 | Leader acknowledgement |
| all | All ISR replicas acknowledge |

Recommended:

```properties
acks=all
```

---

## retries

Specifies how many times Kafka retries failed requests.

Example:

```properties
retries=Integer.MAX_VALUE
```

Retries improve reliability during temporary failures.

---

## enable.idempotence

Prevents duplicate writes.

Example:

```properties
enable.idempotence=true
```

Recommended for all production applications.

---

## transactional.id

Required for transactional producers.

Example:

```properties
transactional.id=payment-service
```

Only needed when using Kafka Transactions.

---

# Performance Configuration

## batch.size

Maximum batch size before sending.

Example:

```properties
batch.size=65536
```

Equivalent:

```text
64 KB
```

Larger batches improve throughput.

---

## linger.ms

Maximum wait time before sending a partially filled batch.

Example:

```properties
linger.ms=5
```

Kafka waits briefly to create larger batches.

---

## compression.type

Compresses batches before transmission.

Example:

```properties
compression.type=zstd
```

Supported values:

- none
- gzip
- snappy
- lz4
- zstd

Recommended:

```properties
compression.type=zstd
```

---

# Memory Configuration

## buffer.memory

Maximum memory available for buffering records.

Example:

```properties
buffer.memory=67108864
```

Equivalent:

```text
64 MB
```

If the buffer becomes full:

```text
Application

↓

Wait

or

↓

Exception
```

depending on timeout settings.

---

## max.request.size

Maximum size of a producer request.

Example:

```properties
max.request.size=1048576
```

Equivalent:

```text
1 MB
```

Messages exceeding this size are rejected.

---

# Timeout Configuration

## request.timeout.ms

Maximum time to wait for a broker response.

Example:

```properties
request.timeout.ms=30000
```

Equivalent:

```text
30 Seconds
```

---

## delivery.timeout.ms

Maximum time allowed for successful delivery.

Example:

```properties
delivery.timeout.ms=120000
```

Equivalent:

```text
120 Seconds
```

Retries continue until this timeout expires.

---

## retry.backoff.ms

Delay between retry attempts.

Example:

```properties
retry.backoff.ms=100
```

Equivalent:

```text
100 Milliseconds
```

Prevents overwhelming recovering brokers.

---

# Metadata Configuration

## metadata.max.age.ms

Controls how often producer metadata is refreshed.

Example:

```properties
metadata.max.age.ms=300000
```

Equivalent:

```text
5 Minutes
```

Metadata refresh detects:

- New brokers
- Leader changes
- New partitions

---

# Network Configuration

## connections.max.idle.ms

Maximum idle connection time.

Example:

```properties
connections.max.idle.ms=540000
```

Idle connections are automatically closed.

---

## send.buffer.bytes

TCP send buffer size.

Example:

```properties
send.buffer.bytes=131072
```

Typically left at the default value.

---

## receive.buffer.bytes

TCP receive buffer size.

Example:

```properties
receive.buffer.bytes=32768
```

Usually tuned only for high-throughput environments.

---

# Security Configuration

When security is enabled, producers require additional settings.

Common examples:

```properties
security.protocol=SASL_SSL
```

```properties
ssl.truststore.location=/path/truststore.jks
```

```properties
sasl.mechanism=SCRAM-SHA-512
```

Security configuration depends on the Kafka deployment.

---

# Production Configuration Example

```properties
bootstrap.servers=broker1:9092,broker2:9092,broker3:9092

client.id=order-service

key.serializer=org.apache.kafka.common.serialization.StringSerializer

value.serializer=org.springframework.kafka.support.serializer.JsonSerializer

acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE

batch.size=65536

linger.ms=5

compression.type=zstd

buffer.memory=67108864

delivery.timeout.ms=120000

request.timeout.ms=30000

retry.backoff.ms=100
```

This configuration provides an excellent balance between reliability and performance.

---

# Configuration Trade-offs

| Goal | Recommended Configuration |
|------|----------------------------|
| Lowest Latency | Small batches, `linger.ms=0`, `acks=1` |
| Highest Throughput | Larger batches, compression, `linger.ms=5-20` |
| Maximum Reliability | `acks=all`, retries, idempotence |
| Financial Systems | Transactions + Idempotence + `acks=all` |
| Logging | Compression + batching + relaxed acknowledgements |

---

# Configuration Relationships

Some settings work together.

```text
acks=all

↓

Requires

↓

Replication

↓

Retries

↓

Idempotence
```

Similarly:

```text
Batching

↓

Compression

↓

Higher Throughput
```

Understanding these relationships is more important than memorizing individual properties.

---

# Most Important Properties

For interviews and production work, remember these first:

| Property | Purpose |
|-----------|---------|
| `bootstrap.servers` | Connect to Kafka |
| `key.serializer` | Serialize keys |
| `value.serializer` | Serialize values |
| `acks` | Delivery guarantee |
| `retries` | Automatic retries |
| `enable.idempotence` | Prevent duplicates |
| `batch.size` | Batch size |
| `linger.ms` | Batch wait time |
| `compression.type` | Reduce bandwidth |
| `buffer.memory` | Producer buffer |
| `delivery.timeout.ms` | Maximum delivery time |
| `transactional.id` | Enable transactions |

These are the configurations most frequently encountered in real-world Kafka applications.

---

# Best Practices

- Configure multiple bootstrap servers.
- Use `acks=all` in production.
- Keep idempotence enabled.
- Enable compression.
- Tune batching before increasing hardware.
- Monitor producer metrics regularly.
- Keep messages reasonably small.
- Load-test configuration changes before deploying them.

---

# Common Mistakes

- Connecting to only one broker.
- Disabling retries in production.
- Using `acks=0` for business-critical data.
- Forgetting serializers.
- Sending very large messages.
- Changing multiple performance settings without benchmarking.
- Assuming default values are optimal for every workload.

---

# Summary

Producer configuration determines how Kafka sends messages to the cluster and directly influences performance, reliability, scalability, and fault tolerance. Key settings such as acknowledgements, retries, batching, compression, buffering, and idempotence work together to provide efficient and reliable message delivery. Rather than tuning properties in isolation, they should be configured as a balanced set based on the application's business and performance requirements.

---

# Key Takeaways

- Producer configuration controls every stage of message publication.
- Reliability is primarily influenced by acknowledgements, retries, and idempotence.
- Performance depends on batching, compression, and memory settings.
- Timeouts control retry behavior and delivery guarantees.
- Metadata settings help producers adapt to cluster changes.
- Security properties protect communication with Kafka clusters.
- A small set of configuration properties accounts for most production tuning.
- Understanding how configuration properties interact is more valuable than memorizing every available option.