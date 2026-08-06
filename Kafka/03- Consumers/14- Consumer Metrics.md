# Consumer Metrics

## Overview

Building a Kafka consumer is only the first step. Running it reliably in production requires continuously monitoring its health, performance, and processing efficiency.

Kafka exposes a comprehensive set of consumer metrics that help answer important operational questions such as:

- Is the consumer keeping up with incoming messages?
- Is consumer lag increasing?
- Are poll requests becoming slower?
- Are fetch requests efficient?
- Are commits succeeding?
- Is the consumer rebalancing too frequently?

Monitoring these metrics allows engineers to detect issues before they impact applications.

---

# Why Consumer Metrics Matter

Consider an Order Processing Service.

Everything appears normal.

```text
Producer

↓

Kafka

↓

Consumer

↓

Database
```

However:

- Database becomes slow.
- Consumer lag increases.
- Rebalances occur frequently.

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

# Consumer Metrics Categories

Consumer metrics can be grouped into several categories.

```text
Consumer Lag

↓

Poll Metrics

↓

Fetch Metrics

↓

Commit Metrics

↓

Processing Metrics

↓

Rebalance Metrics

↓

Network Metrics

↓

Error Metrics
```

Each category measures a different aspect of consumer performance.

---

# Consumer Lag

Consumer Lag is the most important Kafka consumer metric.

It measures:

```text
Latest Offset

-

Committed Offset
```

Example:

```text
Latest Offset

5000

Committed Offset

4700

Lag

300
```

The consumer is 300 messages behind.

---

# Why Consumer Lag Matters

Large lag indicates:

- Slow processing
- Insufficient consumers
- Database bottlenecks
- Network problems
- Frequent rebalancing

Healthy consumers maintain consistently low lag.

---

# Lag Example

```text
Broker

Latest Offset

1000

↓

Consumer

Committed Offset

995

↓

Lag

5
```

Healthy.

Now:

```text
Latest Offset

1000

Committed Offset

650

↓

Lag

350
```

Consumer cannot keep up.

---

# Poll Metrics

Polling drives the consumer.

Important metrics include:

- Poll Rate
- Poll Latency
- Records Per Poll

Healthy workflow:

```text
Poll

↓

Process

↓

Poll

↓

Process
```

---

# Poll Rate

Measures:

```text
Poll Calls

↓

Per Second
```

Example:

```text
20 Polls/sec
```

A decreasing poll rate often indicates slow processing.

---

# Poll Latency

Measures:

```text
poll()

↓

Response Time
```

High poll latency may indicate:

- Broker overload
- Network congestion
- Slow fetch operations

---

# Records Per Poll

Measures:

```text
Average Records

↓

Per Poll
```

Example:

```text
450 Records
```

Very small batches may indicate inefficient fetching.

---

# Fetch Metrics

Consumers fetch records from brokers.

Important metrics:

- Fetch Rate
- Fetch Latency
- Fetch Size

---

# Fetch Rate

Measures:

```text
Fetch Requests

↓

Per Second
```

Example:

```text
80 Fetches/sec
```

Helps evaluate network utilization.

---

# Fetch Latency

Measures:

```text
Fetch Request

↓

Broker Response
```

Increasing latency may indicate:

- Broker pressure
- Network problems
- Disk bottlenecks

---

# Fetch Size

Measures:

```text
Average Bytes

↓

Per Fetch
```

Example:

```text
2 MB
```

Useful for tuning:

```properties
fetch.min.bytes
```

---

# Commit Metrics

Consumers periodically commit offsets.

Important metrics:

- Commit Rate
- Commit Latency
- Commit Failures

---

# Commit Rate

Measures:

```text
Offset Commits

↓

Per Second
```

Very high commit rates often indicate:

```text
Commit Every Record
```

which is usually inefficient.

---

# Commit Latency

Measures:

```text
Commit Request

↓

Broker Response
```

High latency slows recovery and may affect throughput.

---

# Processing Metrics

Business logic often becomes the bottleneck.

Useful metrics include:

- Processing Time
- Messages Processed
- Processing Errors

Example:

```text
Average Processing

15 ms
```

Monitor these metrics together with consumer lag.

---

# Rebalance Metrics

Rebalancing affects availability.

Important metrics:

- Rebalance Count
- Rebalance Duration
- Partition Revocations

Healthy systems experience infrequent rebalances.

Frequent rebalancing often indicates unstable consumers.

---

# Heartbeat Metrics

Consumers periodically send heartbeats.

Metrics include:

- Heartbeat Rate
- Heartbeat Response Time

Missing heartbeats eventually trigger:

```text
Consumer Removed

↓

Rebalance
```

---

# Network Metrics

Useful metrics:

- Bytes Received
- Network Rate
- Request Rate

These metrics help identify:

- Slow networks
- Bandwidth limitations
- Communication bottlenecks

---

# Error Metrics

Monitor:

- Deserialization Errors
- Commit Failures
- Authentication Errors
- Authorization Errors
- Timeout Errors

Ideally:

```text
Errors

↓

Zero
```

---

# Throughput Metrics

Important throughput metrics:

- Records Consumed/sec
- Bytes Consumed/sec
- Fetch Requests/sec

Example:

```text
Consumer

↓

40,000 Records/sec
```

Useful for capacity planning.

---

# Consumer Metrics Dashboard

A typical monitoring dashboard contains:

```text
Consumer Lag

↓

Poll Rate

↓

Fetch Latency

↓

Commit Latency

↓

Processing Time

↓

Rebalances

↓

Errors
```

Together these metrics provide a complete view of consumer health.

---

# Monitoring Tools

Kafka consumer metrics are commonly collected using:

- JMX
- Prometheus
- Grafana
- Micrometer
- OpenTelemetry
- Datadog
- New Relic

These tools generate dashboards and alerts.

---

# Example Alert Rules

Consumer Lag:

```text
>

1000 Messages
```

---

Poll Latency:

```text
>

200 ms
```

---

Commit Failure:

```text
>

0
```

---

Rebalances:

```text
>

5 Per Hour
```

---

Error Rate:

```text
>

1%
```

Thresholds should be adjusted based on workload.

---

# Capacity Planning

Historical metrics help answer questions like:

- Should more consumers be added?
- Should more partitions be created?
- Is processing becoming slower?
- Is traffic increasing?

Trend analysis is more valuable than isolated measurements.

---

# Troubleshooting Example

Suppose users report delays.

Metrics show:

```text
Consumer Lag

↑

Poll Rate

↓

Processing Time

↑

Commit Rate

↓

```

Possible conclusion:

```text
Database

↓

Slow Processing

↓

Consumer Lag
```

Metrics make root cause analysis significantly easier.

---

# Important Consumer Metrics

| Metric | Why It Matters |
|---------|----------------|
| Consumer Lag | Processing backlog |
| Poll Rate | Consumer activity |
| Poll Latency | Poll responsiveness |
| Fetch Rate | Broker communication |
| Fetch Latency | Network and broker health |
| Commit Rate | Offset management |
| Commit Latency | Commit performance |
| Processing Time | Business logic speed |
| Rebalance Count | Consumer stability |
| Error Rate | Consumer health |

---

# Best Practices

- Monitor Consumer Lag continuously.
- Alert on frequent rebalances.
- Track poll and fetch latency.
- Monitor commit failures.
- Watch processing time trends.
- Build dashboards for operational visibility.
- Use historical metrics for capacity planning.
- Correlate Kafka metrics with database and application metrics.

---

# Common Mistakes

- Monitoring only broker metrics.
- Ignoring Consumer Lag.
- Tracking averages without maximum values.
- Failing to investigate frequent rebalances.
- Not setting alert thresholds.
- Assuming Kafka is always the bottleneck.

---

# Summary

Consumer metrics provide visibility into the health, performance, and efficiency of Kafka consumers. By monitoring consumer lag, polling behavior, fetch performance, offset commits, processing time, rebalances, and error rates, engineers can quickly identify bottlenecks, optimize consumer performance, and maintain reliable message processing. Effective monitoring is an essential part of operating Kafka consumers in production.

---

# Key Takeaways

- Consumer Lag is the most important Kafka consumer metric.
- Poll and fetch metrics measure consumer responsiveness.
- Commit metrics evaluate offset management performance.
- Processing metrics often reveal application bottlenecks.
- Rebalance metrics indicate consumer group stability.
- Network and error metrics help diagnose infrastructure issues.
- Monitoring dashboards should combine multiple metrics for a complete operational view.
- Continuous monitoring enables proactive troubleshooting and capacity planning.