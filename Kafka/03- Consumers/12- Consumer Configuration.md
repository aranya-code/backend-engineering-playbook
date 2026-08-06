# Consumer Configuration

## Overview

Kafka consumers expose numerous configuration properties that determine how they connect to the cluster, fetch records, manage offsets, participate in consumer groups, and recover from failures.

These configurations directly affect:

- Reliability
- Throughput
- Latency
- Scalability
- Fault tolerance
- Resource utilization

A well-configured consumer can efficiently process millions of messages while maintaining low latency and high reliability.

This chapter focuses on the most important consumer configurations used in real-world Kafka applications.

---

# Why Consumer Configuration Matters

Different applications have different requirements.

A log processing application may prioritize:

- High throughput
- Low latency

A banking application prioritizes:

- Reliable processing
- No message loss
- Controlled offset commits

Kafka allows consumer behavior to be tuned according to these requirements.

---

# Consumer Configuration Categories

Consumer properties can be grouped into:

```text
Connection

↓

Consumer Group

↓

Offset Management

↓

Polling

↓

Fetching

↓

Performance

↓

Timeouts

↓

Security
```

---

# Connection Configuration

## bootstrap.servers

Defines the Kafka brokers used for the initial connection.

Example:

```properties
bootstrap.servers=broker1:9092,broker2:9092,broker3:9092
```

Only one reachable broker is required.

After connecting, Kafka automatically discovers the remaining brokers.

---

## client.id

Identifies the consumer instance.

Example:

```properties
client.id=inventory-consumer
```

Useful for:

- Logging
- Monitoring
- Metrics
- Troubleshooting

---

# Consumer Group Configuration

## group.id

Defines the Consumer Group.

Example:

```properties
group.id=inventory-service
```

Consumers with the same Group ID share partitions.

Consumers with different Group IDs consume independently.

---

## group.instance.id

Enables Static Membership.

Example:

```properties
group.instance.id=consumer-1
```

Benefits:

- Fewer rebalances
- Stable partition ownership
- Faster recovery

---

# Offset Management

## enable.auto.commit

Controls automatic offset commits.

Example:

```properties
enable.auto.commit=true
```

Production recommendation:

```properties
enable.auto.commit=false
```

Use Manual Commit for business-critical systems.

---

## auto.commit.interval.ms

Commit interval when Auto Commit is enabled.

Example:

```properties
auto.commit.interval.ms=5000
```

Equivalent:

```text
5 Seconds
```

---

## auto.offset.reset

Determines where reading starts when no committed offset exists.

Possible values:

```text
earliest

latest

none
```

### earliest

```text
Read From Beginning
```

### latest

```text
Read Only New Messages
```

### none

```text
Throw Exception
```

Recommended:

- `earliest` for replay or analytics
- `latest` for live event processing

---

# Poll Configuration

## max.poll.records

Maximum records returned in one poll.

Example:

```properties
max.poll.records=500
```

Higher values:

- Better throughput

Lower values:

- Faster processing
- Lower memory usage

---

## max.poll.interval.ms

Maximum time allowed between two poll calls.

Example:

```properties
max.poll.interval.ms=300000
```

Equivalent:

```text
5 Minutes
```

If exceeded:

```text
Consumer Removed

↓

Rebalance
```

---

# Heartbeat Configuration

## heartbeat.interval.ms

Interval between heartbeat messages.

Example:

```properties
heartbeat.interval.ms=3000
```

Equivalent:

```text
3 Seconds
```

Heartbeats keep the consumer active in the group.

---

## session.timeout.ms

Maximum time Kafka waits before declaring a consumer dead.

Example:

```properties
session.timeout.ms=45000
```

Equivalent:

```text
45 Seconds
```

If heartbeats stop before this timeout:

```text
Consumer Removed

↓

Rebalance
```

---

# Fetch Configuration

## fetch.min.bytes

Minimum amount of data returned by the broker.

Example:

```properties
fetch.min.bytes=1
```

Higher values:

- Better throughput
- Higher latency

---

## fetch.max.wait.ms

Maximum wait time for accumulating fetch data.

Example:

```properties
fetch.max.wait.ms=500
```

Equivalent:

```text
500 ms
```

---

## max.partition.fetch.bytes

Maximum bytes fetched from a single partition.

Example:

```properties
max.partition.fetch.bytes=1048576
```

Equivalent:

```text
1 MB
```

---

# Partition Assignment

## partition.assignment.strategy

Defines the partition assignment algorithm.

Example:

```properties
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
```

Common strategies:

- Range Assignor
- Round Robin Assignor
- Sticky Assignor
- Cooperative Sticky Assignor

Recommended:

```text
Cooperative Sticky Assignor
```

---

# Request Configuration

## request.timeout.ms

Maximum time to wait for broker responses.

Example:

```properties
request.timeout.ms=30000
```

Equivalent:

```text
30 Seconds
```

---

## default.api.timeout.ms

Maximum duration for consumer API operations.

Example:

```properties
default.api.timeout.ms=60000
```

Equivalent:

```text
60 Seconds
```

---

# Network Configuration

## receive.buffer.bytes

TCP receive buffer size.

Example:

```properties
receive.buffer.bytes=65536
```

Normally left at the default value.

---

## connections.max.idle.ms

Maximum idle connection time.

Example:

```properties
connections.max.idle.ms=540000
```

Idle connections are closed automatically.

---

# Deserialization Configuration

## key.deserializer

Converts message keys from bytes.

Example:

```properties
key.deserializer=org.apache.kafka.common.serialization.StringDeserializer
```

---

## value.deserializer

Converts message values from bytes.

Example:

```properties
value.deserializer=org.springframework.kafka.support.serializer.JsonDeserializer
```

Without deserializers, consumers cannot interpret Kafka records.

---

# Security Configuration

Secure Kafka clusters require additional settings.

Example:

```properties
security.protocol=SASL_SSL
```

```properties
ssl.truststore.location=/path/truststore.jks
```

```properties
sasl.mechanism=SCRAM-SHA-512
```

Security settings depend on the Kafka deployment.

---

# Production Configuration Example

```properties
bootstrap.servers=broker1:9092,broker2:9092,broker3:9092

group.id=inventory-service

client.id=inventory-consumer

enable.auto.commit=false

auto.offset.reset=earliest

max.poll.records=500

max.poll.interval.ms=300000

heartbeat.interval.ms=3000

session.timeout.ms=45000

fetch.min.bytes=1

fetch.max.wait.ms=500

max.partition.fetch.bytes=1048576

partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor

key.deserializer=org.apache.kafka.common.serialization.StringDeserializer

value.deserializer=org.springframework.kafka.support.serializer.JsonDeserializer
```

---

# Configuration Trade-offs

| Goal | Recommended Configuration |
|------|----------------------------|
| Lowest Latency | Small fetch size, low `fetch.max.wait.ms` |
| Highest Throughput | Larger batches, higher `max.poll.records` |
| Maximum Reliability | Manual Commit, longer poll interval, Cooperative Sticky Assignor |
| Historical Replay | `auto.offset.reset=earliest` |
| Live Streaming | `auto.offset.reset=latest` |

---

# Most Important Consumer Properties

| Property | Purpose |
|----------|---------|
| `bootstrap.servers` | Connect to Kafka |
| `group.id` | Consumer Group |
| `enable.auto.commit` | Offset commit strategy |
| `auto.offset.reset` | Initial reading position |
| `max.poll.records` | Records per poll |
| `max.poll.interval.ms` | Maximum processing interval |
| `heartbeat.interval.ms` | Consumer heartbeat |
| `session.timeout.ms` | Failure detection |
| `partition.assignment.strategy` | Partition assignment algorithm |
| `key.deserializer` | Deserialize keys |
| `value.deserializer` | Deserialize values |

These are the properties most frequently configured in production systems.

---

# Best Practices

- Use meaningful `group.id` values.
- Disable Auto Commit for business-critical applications.
- Prefer Manual Commit in production.
- Use Cooperative Sticky Assignor.
- Tune `max.poll.records` based on processing speed.
- Keep processing within `max.poll.interval.ms`.
- Monitor consumer lag and rebalance frequency.
- Load-test configuration changes before production deployment.

---

# Common Mistakes

- Using Auto Commit for transactional workloads.
- Setting `max.poll.records` too high for slow consumers.
- Choosing `latest` when historical data must be processed.
- Ignoring heartbeat and session timeout settings.
- Leaving all configuration values at defaults without benchmarking.

---

# Summary

Consumer configuration controls how Kafka consumers connect to brokers, join consumer groups, fetch records, commit offsets, and recover from failures. Properties such as `group.id`, `enable.auto.commit`, `max.poll.records`, `auto.offset.reset`, heartbeat settings, and partition assignment strategies directly affect the consumer's reliability and performance. Selecting the right combination of settings is essential for building scalable, fault-tolerant, and efficient Kafka consumer applications.

---

# Key Takeaways

- Consumer configuration determines reliability, performance, and scalability.
- `group.id` identifies the Consumer Group.
- Manual Commit is preferred for production systems.
- `auto.offset.reset` controls the initial reading position.
- Polling and fetch settings influence throughput and latency.
- Heartbeat and session timeout settings maintain group membership.
- Cooperative Sticky Assignor minimizes rebalancing disruptions.
- Consumer configurations should be tuned based on workload rather than relying solely on defaults.