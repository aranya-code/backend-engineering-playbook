# Monitoring Kafka

## Overview

Monitoring is one of the most important aspects of operating a production Kafka cluster. Even a well-designed Kafka deployment can experience issues such as increasing consumer lag, disk exhaustion, broker failures, or replication problems. Without proper monitoring, these problems may go unnoticed until they begin affecting applications.

A production monitoring solution should provide visibility into:

- Broker Health
- Consumer Health
- Producer Performance
- Topic Activity
- Replication Status
- System Resources
- Network Performance

The goal is to detect issues early, resolve them quickly, and maintain a healthy Kafka cluster.

---

# Why Monitoring Matters

Without monitoring:

```text
Broker Failure

↓

Consumers Stop

↓

Applications Fail
```

Nobody notices until users report problems.

With monitoring:

```text
Broker Failure

↓

Alert Generated

↓

Operations Team

↓

Issue Resolved
```

Problems are detected before they become outages.

---

# What Should Be Monitored?

A Kafka production environment should monitor:

- Brokers
- Topics
- Partitions
- Producers
- Consumers
- Consumer Groups
- JVM
- Operating System
- Network
- Storage

Every layer contributes to cluster health.

---

# Monitoring Architecture

```text
Kafka Cluster

↓

JMX Metrics

↓

Prometheus

↓

Grafana

↓

Alerts

↓

Operations Team
```

This is one of the most common monitoring architectures.

---

# Broker Health

Every broker should be monitored.

Important metrics:

- Broker status
- CPU usage
- Memory usage
- Disk usage
- Network throughput
- Request latency

Healthy brokers are essential for cluster stability.

---

# Consumer Lag

Consumer lag is one of the most important Kafka metrics.

Formula:

```text
Lag

=

Log End Offset

-

Committed Offset
```

Example:

```text
Latest Offset

1000

Committed Offset

980

Lag

20
```

---

# Why Consumer Lag Matters

Small lag:

```text
Producer

↓

Consumer

↓

Healthy
```

Large lag:

```text
Producer

↓

Consumer Falling Behind
```

Increasing lag often indicates performance problems.

---

# Under Replicated Partitions

A healthy partition:

```text
Leader

↓

Follower

↓

Follower
```

All replicas remain synchronized.

---

Problem:

```text
Leader

↓

Follower

↓

Offline
```

Kafka reports:

```text
Under Replicated Partition
```

This should trigger an alert.

---

# In-Sync Replica (ISR)

Monitor ISR size.

Healthy:

```text
Leader

↓

Broker 2

↓

Broker 3
```

Shrinking ISR may indicate:

- Slow disks
- Network problems
- Broker failures

---

# Offline Partitions

Example:

```text
Partition

↓

No Leader
```

Consumers cannot read.

Producers cannot write.

This is a critical issue.

---

# Active Controller

Kafka should always have one active controller.

Healthy:

```text
Controller

↓

Broker 2
```

Unexpected controller changes may indicate instability.

---

# Disk Usage

Kafka stores data on disk.

Monitor:

- Free space
- Used space
- Growth rate

Avoid:

```text
100% Full
```

Running out of disk space can stop producers from writing new data.

---

# Network Throughput

Monitor:

- Incoming bytes/sec
- Outgoing bytes/sec
- Network errors
- Packet loss

Kafka performance depends heavily on network bandwidth.

---

# Producer Metrics

Important producer metrics:

- Requests/sec
- Batch size
- Compression ratio
- Retry rate
- Error rate
- Request latency

High retry rates often indicate broker or network issues.

---

# Consumer Metrics

Monitor:

- Records/sec
- Poll latency
- Processing latency
- Commit latency
- Consumer lag

These metrics help identify slow consumers.

---

# Topic Metrics

Track:

- Message rate
- Topic size
- Retention usage
- Partition count

Unexpected changes may indicate abnormal workloads.

---

# Partition Metrics

Monitor:

- Partition size
- Leader distribution
- Replica status
- Throughput

Balanced partitions improve performance.

---

# JVM Metrics

Kafka runs on the JVM.

Monitor:

- Heap usage
- Garbage Collection
- Thread count
- GC pause time

Long GC pauses can affect broker responsiveness.

---

# CPU Usage

Monitor:

```text
CPU %

```

High sustained CPU may indicate:

- Heavy producer load
- Compression overhead
- Excessive requests

---

# Memory Usage

Monitor:

- Heap memory
- Page cache
- Swap usage

Avoid excessive swapping.

Kafka performs best when the operating system can efficiently use page cache.

---

# File Descriptors

Kafka opens many files.

Monitor:

```text
Open File Descriptors
```

Running out of file descriptors can prevent brokers from functioning correctly.

---

# Request Latency

Track:

- Produce latency
- Fetch latency
- Metadata request latency

Increasing latency often precedes performance problems.

---

# Error Rates

Monitor:

- Failed requests
- Authentication failures
- Authorization failures
- Produce failures
- Consumer failures

Unexpected increases should trigger investigation.

---

# Monitoring Tools

Common tools include:

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection |
| Grafana | Dashboards |
| JMX Exporter | Kafka metrics |
| Alertmanager | Alerting |
| Elasticsearch | Log storage |
| Kibana | Log visualization |

These tools are widely used in production Kafka deployments.

---

# Example Monitoring Stack

```text
Kafka Brokers

↓

JMX Exporter

↓

Prometheus

↓

Grafana

↓

Alertmanager

↓

Slack / Email / PagerDuty
```

This provides complete observability.

---

# Important Alerts

Create alerts for:

- Broker Down
- Consumer Lag
- Under Replicated Partitions
- Offline Partitions
- Disk Usage > 80%
- JVM Heap > 90%
- High Request Latency
- Authentication Failures
- Controller Changes
- Replication Failures

Alerts should be actionable.

---

# Dashboard Example

A production dashboard may include:

```text
Broker Status

Consumer Lag

ISR Count

CPU

Memory

Disk

Network

Requests/sec

Topic Throughput
```

A single dashboard provides an overview of cluster health.

---

# Monitoring Workflow

```text
Collect Metrics

↓

Store Metrics

↓

Visualize

↓

Alert

↓

Investigate

↓

Resolve

↓

Verify Recovery
```

This is a typical operational workflow.

---

# Capacity Trends

Monitoring is also useful for capacity planning.

Track:

- Storage growth
- Message volume
- Throughput trends
- Consumer growth

Historical data helps predict future infrastructure needs.

---

# Best Practices

- Monitor every broker continuously.
- Alert on consumer lag.
- Monitor ISR health.
- Track disk growth.
- Create dashboards for operations teams.
- Monitor producer and consumer latency.
- Store historical metrics.
- Test alerts regularly.
- Review dashboards during deployments.
- Investigate anomalies before they become outages.

---

# Common Mistakes

- Monitoring only broker availability.
- Ignoring consumer lag.
- Not tracking disk usage.
- Missing alerts for under replicated partitions.
- Ignoring JVM metrics.
- Creating too many noisy alerts.
- Monitoring without defining response procedures.
- Failing to retain historical metrics.

---

# Summary

Monitoring is essential for operating Kafka reliably in production. By continuously observing brokers, producers, consumers, replication, storage, networking, and JVM performance, teams can detect issues early and maintain cluster stability. Combined with dashboards, alerts, and historical metrics, an effective monitoring strategy enables proactive operations, faster incident response, and better capacity planning.

---

# Key Takeaways

- Monitoring is a core operational requirement for Kafka production environments.
- Consumer lag is one of the most important health indicators.
- Monitor brokers, partitions, producers, consumers, JVM, storage, and networking.
- Track under replicated partitions and ISR health.
- Use Prometheus, Grafana, and JMX Exporter for observability.
- Configure actionable alerts for critical failures.
- Historical metrics support capacity planning and troubleshooting.
- Continuous monitoring improves reliability, availability, and operational efficiency.