# 07 - DynamoDB + Amazon Kinesis

## Overview

Amazon DynamoDB and Amazon Kinesis are commonly used together to build **real-time data processing systems** capable of handling millions of events per second.

While DynamoDB is optimized for serving low-latency application data, Amazon Kinesis is designed for ingesting, transporting, and processing continuous streams of data.

Together they enable architectures for:

- Real-time analytics
- Streaming ETL
- Live dashboards
- Fraud detection
- IoT platforms
- Log processing
- Clickstream analysis
- Machine learning pipelines

A typical production architecture is:

```text
Application

↓

DynamoDB

↓

DynamoDB Streams

↓

AWS Lambda

↓

Amazon Kinesis Data Streams

↓

Consumers

↓

Analytics / Data Lake / ML
```

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why integrate DynamoDB with Kinesis
- Streaming architectures
- Real-time event processing
- Kinesis Data Streams
- Kinesis Data Firehose
- Shards and scaling
- Consumer applications
- Production architectures
- Best practices
- Interview questions

---

# Why Combine DynamoDB with Kinesis?

Imagine an online shopping platform.

Every second:

- Orders are created
- Products are updated
- Customers browse items
- Payments are completed

Business teams want dashboards updating instantly.

Instead of querying DynamoDB continuously:

```text
Dashboard

↓

Query Database

↓

Repeat Every Second
```

A better solution:

```text
Application

↓

DynamoDB

↓

Kinesis

↓

Real-Time Dashboard
```

The database remains optimized for transactional workloads while analytics are handled separately.

---

# High-Level Architecture

```text
                Users

                   │

                   ▼

            Backend Service

                   │

                   ▼

              DynamoDB Table

                   │

          DynamoDB Streams

                   │

                   ▼

              AWS Lambda

                   │

                   ▼

        Amazon Kinesis Streams

         ┌─────────┼─────────┐

         ▼         ▼         ▼

   Analytics   ML Models   Data Lake
```

---

# Common Use Cases

DynamoDB and Kinesis are widely used for:

- Real-time analytics
- Fraud detection
- Recommendation engines
- IoT telemetry
- Clickstream analytics
- Security monitoring
- Financial transactions
- Operational dashboards

---

# Pattern 1 — Real-Time Dashboard

```text
Order Created

↓

DynamoDB

↓

Streams

↓

Lambda

↓

Kinesis

↓

Dashboard
```

Business metrics update within seconds.

---

# Pattern 2 — Fraud Detection

```text
Payment

↓

DynamoDB

↓

Kinesis

↓

Fraud Engine

↓

Alert
```

Suspicious transactions can be detected immediately.

---

# Pattern 3 — Clickstream Analytics

```text
Website

↓

User Click

↓

Kinesis

↓

Processing

↓

Analytics Database
```

This enables near real-time user behavior analysis.

---

# Pattern 4 — IoT Platform

```text
Devices

↓

Sensor Data

↓

Kinesis

↓

Processing

↓

DynamoDB
```

Applications can store the latest device state in DynamoDB while processing continuous telemetry through Kinesis.

---

# Data Flow

```text
Application

↓

Write Item

↓

DynamoDB

↓

Streams

↓

Lambda

↓

Kinesis

↓

Consumers
```

The application performs only the database write.

Streaming is handled asynchronously.

---

# Kinesis Components

Amazon Kinesis provides several services.

## Kinesis Data Streams

Designed for real-time event streaming.

```text
Producer

↓

Stream

↓

Consumers
```

---

## Kinesis Data Firehose

Automatically delivers streaming data to destinations.

```text
Stream

↓

Firehose

↓

Amazon S3

↓

Redshift

↓

OpenSearch
```

No infrastructure management is required.

---

## Kinesis Data Analytics

Processes streaming data using SQL or Apache Flink.

```text
Kinesis

↓

Analytics

↓

Aggregated Results
```

---

# Shards

A Kinesis Data Stream is divided into **shards**.

```text
Kinesis Stream

├── Shard 1

├── Shard 2

├── Shard 3

└── Shard 4
```

Each shard provides:

- Independent throughput
- Parallel processing
- Horizontal scalability

Increasing shards increases stream capacity.

---

# Multiple Consumers

Several applications can consume the same stream.

```text
Kinesis

      │

 ┌────┼────┐

 ▼    ▼    ▼

ML Dashboard Archive
```

Each consumer processes the same events independently.

---

# Ordering

Within a shard:

```text
Event A

↓

Event B

↓

Event C
```

Ordering is preserved.

Across multiple shards, ordering is **not guaranteed**.

---

# Checkpointing

Consumers record progress.

```text
Event

↓

Process

↓

Checkpoint

↓

Next Event
```

If a consumer restarts, it resumes from the last checkpoint.

---

# Monitoring

Monitor:

Kinesis

- Incoming records
- Incoming bytes
- Read throughput
- Write throughput
- Iterator age
- Throttling

Lambda

- Errors
- Duration
- Concurrent executions

DynamoDB

- Streams health
- Latency
- RCUs
- WCUs

---

# Production Architecture

```text
                     Users

                        │

                  API Gateway

                        │

                        ▼

                 Backend Service

                        │

                        ▼

                  DynamoDB Table

                        │

                 DynamoDB Streams

                        │

                        ▼

                    AWS Lambda

                        │

                        ▼

            Amazon Kinesis Streams

       ┌────────────┼────────────┐

       ▼            ▼            ▼

  Dashboard     Fraud Engine   Firehose

                                     │

                                     ▼

                               Amazon S3

                                     │

                                     ▼

                              Amazon Athena
```

---

# Performance Considerations

For production workloads:

- Partition data evenly across shards.
- Avoid hot shards.
- Batch records where appropriate.
- Keep events lightweight.
- Monitor iterator age.
- Scale shards as throughput increases.
- Design consumers for horizontal scaling.

---

# Security Best Practices

- Encrypt streams using AWS KMS.
- Apply least-privilege IAM policies.
- Enable CloudTrail.
- Restrict producer and consumer permissions.
- Encrypt sensitive payloads before streaming.
- Enable VPC endpoints where required.

---

# Best Practices

- Publish immutable business events.
- Keep event payloads small.
- Use Kinesis for streaming, not as a database.
- Design consumers to be idempotent.
- Scale shards proactively.
- Monitor throughput continuously.
- Archive historical events using Firehose and Amazon S3.
- Separate transactional workloads from analytics workloads.

---

# Common Mistakes

## Querying DynamoDB for Analytics

Poor:

```text
Dashboard

↓

Repeated Scan()
```

Better:

```text
DynamoDB

↓

Kinesis

↓

Analytics
```

---

## Large Event Payloads

Instead of:

```text
Entire Customer Record
```

Publish:

```text
CustomerID

↓

Consumer

↓

Retrieve Details
```

---

## Ignoring Shard Limits

Too much traffic on one shard leads to throttling.

Design partition keys to distribute load evenly.

---

## Treating Kinesis as Permanent Storage

Kinesis is a streaming platform, not a long-term database.

Persist historical data to Amazon S3, Redshift, or another storage system.

---

# Production Considerations

Large-scale architectures commonly use:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

Kinesis

↓

Firehose

↓

Amazon S3

↓

Athena

↓

QuickSight

↓

Machine Learning
```

This architecture enables real-time operational processing while maintaining an efficient analytics pipeline.

---

# Interview Notes

A common interview question is:

> **Why integrate DynamoDB with Amazon Kinesis?**

DynamoDB efficiently handles transactional workloads, while Kinesis processes continuous streams of events in real time. Together they separate operational data storage from streaming analytics.

---

Another common question is:

> **What is the difference between DynamoDB Streams and Kinesis Data Streams?**

DynamoDB Streams capture changes made to a DynamoDB table and retain them for 24 hours. Kinesis Data Streams is a general-purpose streaming platform that supports multiple producers, configurable retention, and large-scale real-time processing.

---

Another common question is:

> **Why use Lambda between DynamoDB Streams and Kinesis?**

Lambda transforms DynamoDB stream records into business events before publishing them to Kinesis. This decouples database changes from downstream analytics systems.

---

Another common question is:

> **What are Kinesis shards?**

A shard is the basic unit of throughput in a Kinesis Data Stream. Shards determine the stream's read and write capacity and enable parallel processing of streaming data.

---

# Key Takeaways

- DynamoDB and Amazon Kinesis enable scalable real-time data processing architectures.
- A common production pattern is **DynamoDB Streams → Lambda → Kinesis Data Streams**.
- Kinesis distributes events across shards for parallel, high-throughput processing.
- Use DynamoDB for transactional storage and Kinesis for streaming analytics and event pipelines.
- Combining Kinesis with Firehose, Amazon S3, Athena, and QuickSight creates a powerful real-time analytics ecosystem.