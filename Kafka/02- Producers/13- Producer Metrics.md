# Producer Metrics

## Overview

Building a Kafka producer is only half the job. In production, it is equally important to **monitor the health and performance** of the producer.

Kafka producers expose a rich set of metrics that help answer questions such as:

- Is the producer keeping up with incoming traffic?
- Are messages being sent successfully?
- Are retries increasing?
- Is the network becoming a bottleneck?
- Are batches large enough?
- Is producer latency increasing?

Monitoring these metrics allows engineers to detect problems before they affect applications.

---

# Why Producer Metrics Matter

Consider an order processing system.

Everything appears to be working.

```text
Application

↓

Kafka Producer

↓

Kafka Cluster
```

However, behind the scenes:

- Retries increase.
- Latency doubles.
- Network bandwidth becomes saturated.

Without monitoring:

```text
Problem

↓

Users Notice
```

With monitoring:

```text
Problem

↓

Alert

↓

Fix Before Failure
```

---

# Producer Metrics Categories

Kafka producer metrics can be grouped into several categories.

```text
Throughput

↓

Latency

↓

Requests

↓

Retries

↓

Errors

↓

Batching

↓

Buffer Usage

↓

Network
```

Each category measures a different aspect of producer performance.

---

# Throughput Metrics

Throughput measures how much data the producer sends.

Common metrics include:

- Record Send Rate
- Record Send Total
- Byte Rate

Example:

```text
Producer

↓

50,000 Messages / Second
```

High throughput generally indicates efficient producer operation.

---

# Record Send Rate

Measures:

```text
Messages Sent

↓

Per Second
```

Example:

```text
20,000 Records/sec
```

Sudden drops may indicate:

- Broker issues
- Network problems
- Producer bottlenecks

---

# Record Send Total

Measures the cumulative number of messages sent.

Example:

```text
Messages Sent

↓

5,200,000
```

Useful for:

- Capacity planning
- Traffic analysis
- Long-term monitoring

---

# Byte Rate

Measures the amount of data transmitted.

Example:

```text
150 MB/sec
```

Useful for:

- Network utilization
- Compression effectiveness
- Capacity planning

---

# Latency Metrics

Latency measures how long the producer waits before receiving an acknowledgement.

Workflow:

```text
Producer

↓

Send

↓

Broker

↓

ACK

↓

Producer
```

Important metrics include:

- Request Latency
- Average Latency
- Maximum Latency

---

# Average Request Latency

Example:

```text
Average

8 ms
```

Consistently increasing latency may indicate:

- Broker overload
- Network congestion
- Storage bottlenecks

---

# Maximum Latency

Example:

```text
Maximum

350 ms
```

High spikes often indicate temporary failures or broker recovery.

---

# Request Metrics

Kafka tracks every request sent to brokers.

Important metrics:

- Request Rate
- Request Size
- Request Time

Example:

```text
Producer

↓

500 Requests/sec
```

These metrics help evaluate batching efficiency.

---

# Batch Metrics

Batching has a major impact on producer performance.

Useful metrics include:

- Batch Size Average
- Batch Size Maximum
- Records Per Batch

Example:

```text
Average Batch

60 KB
```

Small batches usually indicate poor batching efficiency.

---

# Compression Metrics

Compression effectiveness can also be measured.

Example:

```text
Original Batch

100 KB

↓

Compressed Batch

35 KB
```

Compression Ratio:

```text
65%
```

A better compression ratio reduces:

- Network usage
- Disk storage
- Replication traffic

---

# Retry Metrics

Retries indicate temporary failures.

Example:

```text
Retry Count

↓

150
```

Occasional retries are normal.

Constant retries may indicate:

- Broker instability
- Network issues
- Incorrect timeout settings

---

# Error Metrics

Producer errors should be monitored continuously.

Examples include:

- Send failures
- Timeout errors
- Serialization failures
- Authentication failures

Example:

```text
Errors/minute

↓

0
```

Ideally, error rates should remain close to zero.

---

# Buffer Metrics

The producer maintains an internal buffer.

Useful metrics include:

- Buffer Available
- Buffer Utilization
- Waiting Threads

Example:

```text
Buffer

64 MB

↓

Used

18 MB
```

Consistently full buffers may indicate:

- Slow brokers
- Network congestion
- Insufficient producer resources

---

# Connection Metrics

Monitor producer connections.

Examples:

- Active Connections
- Connection Creation Rate
- Connection Close Rate

Frequent reconnections may indicate:

- Network instability
- Broker failures
- Firewall issues

---

# Metadata Metrics

Kafka producers periodically refresh cluster metadata.

Monitor:

- Metadata Refresh Count
- Metadata Age

Frequent refreshes may indicate:

- Leader elections
- Broker restarts
- Cluster topology changes

---

# Producer Metrics Dashboard

A typical monitoring dashboard contains:

```text
Producer

↓

Throughput

↓

Latency

↓

Retries

↓

Errors

↓

Batch Size

↓

Compression

↓

Buffer Usage
```

This provides a complete picture of producer health.

---

# Common Monitoring Tools

Kafka producer metrics are commonly collected using:

- JMX
- Prometheus
- Grafana
- Micrometer
- OpenTelemetry
- Datadog
- New Relic

These tools visualize trends and generate alerts.

---

# Example Alert Rules

Examples:

```text
Retry Rate

>

100/minute
```

```text
Average Latency

>

100 ms
```

```text
Error Rate

>

1%
```

```text
Buffer Usage

>

90%
```

These thresholds vary depending on the workload.

---

# Metrics for Capacity Planning

Historical metrics help answer questions such as:

- When will additional brokers be needed?
- Is producer traffic increasing?
- Are batches becoming larger?
- Is compression reducing bandwidth effectively?

Capacity planning should be based on long-term trends rather than short-term spikes.

---

# Metrics and Troubleshooting

Suppose users report delays.

Metrics show:

```text
Latency

↑

Retries

↑

Batch Size

↓

Network Usage

↑
```

Possible conclusion:

```text
Network Bottleneck
```

Metrics allow faster root cause analysis.

---

# Important Producer Metrics

| Metric | Why It Matters |
|---------|----------------|
| Record Send Rate | Producer throughput |
| Byte Rate | Network usage |
| Request Latency | Producer responsiveness |
| Retry Rate | Temporary failures |
| Error Rate | Producer health |
| Batch Size | Batching efficiency |
| Compression Ratio | Bandwidth savings |
| Buffer Utilization | Memory pressure |
| Request Rate | Broker communication |

---

# Best Practices

- Monitor producer metrics continuously.
- Alert on increasing retry rates.
- Investigate latency spikes promptly.
- Monitor buffer utilization.
- Review batching efficiency regularly.
- Track compression effectiveness.
- Build dashboards for operational visibility.
- Use historical metrics for capacity planning.

---

# Common Mistakes

- Monitoring only broker metrics.
- Ignoring producer retry rates.
- Investigating only average latency instead of maximum latency.
- Failing to establish alert thresholds.
- Making configuration changes without comparing metrics before and after.

---

# Summary

Producer metrics provide visibility into the performance, reliability, and health of Kafka producers. By monitoring throughput, latency, batching, retries, errors, compression, and buffer usage, engineers can detect problems early, optimize producer configurations, and ensure reliable message delivery. Effective monitoring is an essential part of operating Kafka in production environments.

---

# Key Takeaways

- Producer metrics reveal the health and efficiency of Kafka producers.
- Throughput metrics measure how much data is being published.
- Latency metrics indicate producer responsiveness.
- Retry and error metrics help identify failures.
- Batch and compression metrics evaluate performance optimizations.
- Buffer metrics reveal memory pressure inside the producer.
- Monitoring dashboards should combine multiple metrics for complete visibility.
- Continuous monitoring enables proactive troubleshooting and capacity planning.