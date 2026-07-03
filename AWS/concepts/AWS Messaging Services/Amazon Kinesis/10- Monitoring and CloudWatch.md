# Introduction

Monitoring is essential for operating Amazon Kinesis in production.

Streaming workloads are continuous, high-throughput, and time-sensitive. Even a small issue—such as throttling, consumer lag, or failed record processing—can quickly impact downstream systems.

Amazon Kinesis integrates with:

- Amazon CloudWatch
- AWS CloudTrail
- AWS CloudWatch Alarms
- AWS CloudWatch Dashboards

These services help monitor stream health, throughput, latency, errors, and application performance.

---

# Monitoring Architecture

```
              Producers

                  │

                  ▼

        Amazon Kinesis Stream

                  │

      ┌───────────┼────────────┐

      ▼           ▼            ▼

 CloudWatch   CloudTrail   Applications
   Metrics      Logs
```

CloudWatch monitors performance.

CloudTrail records API activity.

---

# Amazon CloudWatch

Amazon CloudWatch automatically collects operational metrics for Kinesis.

These metrics help answer questions such as:

- Are producers sending records?
- Are consumers keeping up?
- Are shards overloaded?
- Are applications being throttled?

---

# Monitoring Categories

CloudWatch metrics fall into three categories.

```
Kinesis Metrics

│

├── Producer Metrics

├── Consumer Metrics

└── Stream Metrics
```

---

# Producer Metrics

These metrics monitor incoming data.

| Metric | Description |
|----------|-------------|
| IncomingBytes | Total bytes written |
| IncomingRecords | Total records written |
| WriteProvisionedThroughputExceeded | Write throttling events |

---

# IncomingBytes

Tracks the total amount of data written.

```
Producer

↓

IncomingBytes

↓

CloudWatch
```

A sudden increase may indicate higher application traffic.

---

# IncomingRecords

Tracks the number of records written.

```
Producer

↓

Records

↓

IncomingRecords
```

Useful for capacity planning.

---

# WriteProvisionedThroughputExceeded

Occurs when producers exceed shard write capacity.

```
Producer

↓

Shard Limit

↓

Throttled

↓

Metric +1
```

Frequent occurrences indicate that additional shards may be required.

---

# Consumer Metrics

Consumer metrics monitor record retrieval.

| Metric | Description |
|----------|-------------|
| GetRecords.Bytes | Bytes read |
| GetRecords.Success | Successful reads |
| ReadProvisionedThroughputExceeded | Read throttling |
| IteratorAgeMilliseconds | Consumer lag |

---

# IteratorAgeMilliseconds

One of the most important Kinesis metrics.

It measures how far behind a consumer is compared to the latest record.

```
Latest Record

↓

Consumer

↓

Lag
```

Lower values indicate healthy processing.

Increasing values indicate consumer delays.

---

# GetRecords.Bytes

Tracks the amount of data consumers retrieve.

```
Consumer

↓

Read Records

↓

Bytes
```

---

# ReadProvisionedThroughputExceeded

Occurs when consumers exceed shard read limits.

```
Consumer

↓

Too Many Reads

↓

Throttled
```

Possible solutions:

- Add shards
- Reduce polling
- Use Enhanced Fan-Out

---

# Stream Metrics

General stream health metrics include:

| Metric | Description |
|----------|-------------|
| IncomingBytes | Data ingestion |
| IncomingRecords | Record ingestion |
| OutgoingBytes | Data delivered |
| OutgoingRecords | Records delivered |

---

# CloudWatch Dashboard

Create dashboards to visualize stream performance.

```
Amazon Kinesis Dashboard

──────────────────────────

Incoming Records

Incoming Bytes

Outgoing Records

Consumer Lag

Write Throttling

Read Throttling

──────────────────────────
```

Dashboards provide a centralized operational view.

---

# CloudWatch Alarms

CloudWatch Alarms notify administrators when metrics exceed thresholds.

Example

```
IteratorAgeMilliseconds

>

60000

↓

CloudWatch Alarm

↓

Amazon SNS

↓

Operations Team
```

---

# Alarm Workflow

```
CloudWatch Metric

↓

Threshold

↓

Alarm

↓

Amazon SNS

↓

Email

↓

Operations Team
```

---

# Monitoring Throughput

Monitor shard utilization.

```
Incoming Records

↓

Shard Capacity

↓

CloudWatch

↓

Healthy

or

Throttled
```

---

# Monitoring Consumer Lag

Healthy consumers

```
Producer

↓

Consumer

↓

Iterator Age

↓

Low
```

Unhealthy consumers

```
Producer

↓

Consumer

↓

Iterator Age

↓

High
```

High lag indicates consumers cannot process records quickly enough.

---

# Monitoring Scaling

CloudWatch helps determine when to reshard.

Monitor:

- IncomingBytes
- IncomingRecords
- WriteProvisionedThroughputExceeded

If these metrics continue increasing,

consider adding more shards.

---

# CloudTrail Integration

CloudTrail records all Kinesis API calls.

Examples include:

- CreateStream
- DeleteStream
- PutRecord
- PutRecords
- GetRecords
- UpdateShardCount
- StartStreamEncryption

---

# CloudTrail Architecture

```
Developer

↓

AWS API

↓

CloudTrail

↓

Audit Log
```

Useful for:

- Security
- Compliance
- Troubleshooting

---

# Example CloudTrail Event

```json
{
    "eventName":"PutRecords",
    "eventSource":"kinesis.amazonaws.com"
}
```

CloudTrail records:

- IAM identity
- Timestamp
- AWS Region
- Source IP
- API parameters

---

# AWS Config

AWS Config monitors stream configuration changes.

Examples:

- Encryption disabled
- Retention updated
- Shard count changed
- Stream deleted

Useful for governance and compliance.

---

# Monitoring Enhanced Fan-Out

Applications using Enhanced Fan-Out should monitor:

- Consumer throughput
- Processing latency
- Iterator age
- Consumer health

Each consumer receives dedicated throughput.

---

# Example Dashboard

```
Amazon Kinesis

──────────────────────────────

Incoming Records

Incoming Bytes

Outgoing Records

Consumer Lag

Write Throttling

Read Throttling

Shard Count

──────────────────────────────
```

---

# Real-World Example

A stock trading platform processes market data.

```
Trading Platform

↓

Kinesis

↓

Analytics

↓

CloudWatch

↓

Alarm

↓

Operations Team
```

If consumer lag increases,

CloudWatch automatically notifies the operations team.

---

# Best Practices

- Monitor every production stream.
- Create CloudWatch Dashboards.
- Configure alarms for throttling events.
- Monitor IteratorAgeMilliseconds continuously.
- Monitor shard utilization before reaching capacity.
- Enable CloudTrail for auditing.
- Review CloudTrail logs regularly.
- Use AWS Config for compliance monitoring.
- Investigate sustained increases in consumer lag.

---

# Common Mistakes

## Ignoring Iterator Age

Consumer lag often indicates downstream processing bottlenecks.

---

## Monitoring Only Producers

Consumers should also be monitored continuously.

---

## Ignoring Throttling Metrics

Repeated throttling indicates insufficient shard capacity.

---

## No CloudWatch Alarms

Without alarms,

production failures may go unnoticed.

---

## Ignoring CloudTrail

CloudTrail is essential for auditing administrative operations.

---

# Summary

Amazon Kinesis integrates with Amazon CloudWatch, AWS CloudTrail, and AWS Config to provide comprehensive monitoring, alerting, and auditing capabilities. CloudWatch metrics help monitor producer throughput, consumer performance, shard utilization, throttling events, and consumer lag, while CloudWatch Alarms enable proactive operational response. Together with CloudTrail and AWS Config, these services provide the visibility required to operate secure, scalable, and production-ready real-time streaming applications.