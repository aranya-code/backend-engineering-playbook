# Introduction

Amazon Kinesis is a popular topic in interviews for:

- Backend Engineers
- Cloud Engineers
- DevOps Engineers
- Data Engineers
- Solution Architects
- AWS Certification Exams

This chapter contains frequently asked interview questions ranging from beginner to advanced levels.

---

# Beginner Level Questions

## 1. What is Amazon Kinesis?

Amazon Kinesis is a fully managed AWS service for collecting, processing, and analyzing real-time streaming data at scale.

It enables applications to process data continuously with low latency.

---

## 2. What problems does Amazon Kinesis solve?

Amazon Kinesis solves problems related to:

- Real-time analytics
- Continuous data ingestion
- Log processing
- IoT telemetry
- Clickstream analytics
- Fraud detection

---

## 3. What are the components of Amazon Kinesis?

Amazon Kinesis consists of:

- Kinesis Data Streams
- Kinesis Data Firehose
- Kinesis Data Analytics
- Kinesis Video Streams

---

## 4. What is a Kinesis Data Stream?

A Kinesis Data Stream is a scalable stream of continuously arriving records.

Applications write records into the stream while consumers read and process them independently.

---

## 5. What is a shard?

A shard is the basic unit of capacity in Kinesis Data Streams.

Each shard provides:

- 1 MB/sec write throughput (or 1,000 records/sec)
- 2 MB/sec read throughput

---

## 6. What is a record?

A record is the smallest unit of data stored in a stream.

A record contains:

- Partition Key
- Sequence Number
- Data
- Approximate Arrival Timestamp

---

## 7. What is a Partition Key?

The Partition Key determines which shard stores a record.

It is hashed using MD5 and mapped to a shard automatically.

---

## 8. What is a Sequence Number?

A Sequence Number is a unique identifier assigned to every record.

It preserves ordering within a shard.

---

## 9. What is the maximum size of a record?

```
1 MB
```

---

## 10. What is the default retention period?

```
24 Hours
```

Maximum retention:

```
365 Days
```

---

# Intermediate Level Questions

## 11. What is resharding?

Resharding is the process of changing the number of shards.

It includes:

- Split Shard
- Merge Shards

---

## 12. What causes hot shards?

Hot shards occur when most records use the same Partition Key, causing uneven traffic distribution.

---

## 13. How can hot shards be avoided?

- Choose high-cardinality Partition Keys
- Monitor CloudWatch metrics
- Split overloaded shards
- Distribute traffic evenly

---

## 14. Difference between PutRecord() and PutRecords()

| PutRecord | PutRecords |
|------------|------------|
| One record | Multiple records |
| More API calls | Fewer API calls |
| Lower throughput | Higher throughput |

---

## 15. What is IteratorAgeMilliseconds?

It measures consumer lag.

Higher values indicate consumers are processing records more slowly than producers are writing them.

---

## 16. What is Enhanced Fan-Out?

Enhanced Fan-Out gives each registered consumer dedicated read throughput, reducing latency and avoiding read contention.

---

## 17. Shared Fan-Out vs Enhanced Fan-Out

| Shared Fan-Out | Enhanced Fan-Out |
|----------------|------------------|
| Shared throughput | Dedicated throughput |
| Higher latency | Lower latency |
| Lower cost | Higher cost |

---

## 18. What is On-Demand Capacity Mode?

On-Demand Mode automatically scales stream capacity based on incoming traffic.

No manual shard management is required.

---

## 19. What is Provisioned Capacity Mode?

Provisioned Mode requires manually configuring and managing shard count.

It is suitable for predictable workloads.

---

## 20. What is consumer lag?

Consumer lag is the delay between the latest record in the stream and the record currently being processed.

---

# Advanced Level Questions

## 21. How does Kinesis guarantee ordering?

Ordering is guaranteed **only within a single shard**.

Ordering across different shards is not guaranteed.

---

## 22. Can multiple consumers read the same data?

Yes.

Multiple consumers can independently read and process the same stream.

---

## 23. Why is Kinesis suitable for analytics?

Because it supports:

- Continuous ingestion
- Multiple consumers
- Replay
- Real-time processing

---

## 24. Difference between Kinesis Data Streams and Firehose?

| Data Streams | Firehose |
|---------------|-----------|
| Custom processing | Managed delivery |
| Replay supported | No replay |
| Multiple consumers | Single delivery pipeline |
| Shard management | No shard management |

---

## 25. Difference between Kinesis and Amazon SQS?

| Amazon Kinesis | Amazon SQS |
|----------------|------------|
| Streaming platform | Message queue |
| Multiple consumers | One consumer processes each message |
| Replay supported | Messages deleted after processing |
| Ordered within shard | FIFO queue only |

---

## 26. Difference between Kinesis and Amazon SNS?

| Amazon Kinesis | Amazon SNS |
|----------------|------------|
| Streaming platform | Notification service |
| Pull model | Push model |
| Stores records temporarily | No message storage |
| Supports replay | No replay |

---

## 27. When should you use Kinesis?

Use Kinesis for:

- Real-time analytics
- Streaming ETL
- Fraud detection
- IoT telemetry
- Clickstream analysis
- Monitoring

---

## 28. When should you not use Kinesis?

Avoid Kinesis for:

- Background job queues
- Email notifications
- Simple asynchronous messaging

Amazon SQS or Amazon SNS are better choices for these workloads.

---

## 29. What AWS services commonly integrate with Kinesis?

- AWS Lambda
- Amazon S3
- Amazon Redshift
- Amazon OpenSearch Service
- Amazon EMR
- AWS Glue
- Amazon CloudWatch

---

## 30. How does Kinesis provide durability?

Records are replicated across multiple Availability Zones within an AWS Region.

---

# Scenario-Based Questions

## 31. Your producers are receiving `ProvisionedThroughputExceededException`. What would you do?

Possible solutions:

- Increase shard count
- Switch to On-Demand Mode
- Batch records with `PutRecords()`
- Improve Partition Key distribution

---

## 32. Consumer lag is continuously increasing. How would you investigate?

Check:

- IteratorAgeMilliseconds
- Consumer processing time
- Business logic
- Shard capacity
- Read throttling

Scale consumers or shards if necessary.

---

## 33. One shard is overloaded while others are idle. What is the likely cause?

A poor Partition Key causing uneven traffic distribution (hot shard).

---

## 34. Why would you choose Enhanced Fan-Out?

When multiple applications require low-latency, independent access to the same stream.

---

## 35. How would you securely access Kinesis from an EC2 instance?

Use:

- IAM Role attached to the EC2 instance
- HTTPS
- AWS KMS encryption
- Least-privilege IAM policies

Avoid hardcoded access keys.

---

# Coding Questions

## 36. Write a Boto3 example to publish a record.

```python
import boto3

client = boto3.client("kinesis")

client.put_record(
    StreamName="OrderStream",
    PartitionKey="customer-101",
    Data="Order Created"
)
```

---

## 37. How do you send multiple records?

Use:

```python
put_records()
```

---

## 38. How do consumers start reading from the latest record?

Use the shard iterator type:

```text
LATEST
```

---

## 39. Which iterator type reads from the oldest available record?

```text
TRIM_HORIZON
```

---

## 40. Which CloudWatch metric indicates consumer lag?

```text
IteratorAgeMilliseconds
```

---

# Architecture Questions

## 41. Design a real-time clickstream analytics platform.

A good answer should include:

- Web Applications
- Kinesis Data Streams
- Apache Flink or Kinesis Data Analytics
- Amazon S3
- Amazon Redshift
- QuickSight
- CloudWatch

---

## 42. Design a fraud detection system using Kinesis.

Expected architecture:

```
Payment Gateway

↓

Kinesis Data Streams

↓

Analytics

↓

Fraud Detection

↓

Alert

↓

Dashboard
```

---

## 43. Design a log aggregation system.

Example architecture:

```
Application Logs

↓

Kinesis Data Firehose

↓

Amazon S3

↓

Athena

↓

QuickSight
```

---

## 44. How would you handle seasonal traffic spikes?

- Use On-Demand Mode
- Monitor CloudWatch
- Scale consumers
- Archive historical data

---

## 45. Explain the complete lifecycle of a Kinesis record.

```
Producer

↓

PutRecord()

↓

Partition Key

↓

Shard

↓

Consumer

↓

Process

↓

Retention

↓

Expiration
```

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Default retention | 24 Hours |
| Maximum retention | 365 Days |
| Max record size | 1 MB |
| Write throughput per shard | 1 MB/sec or 1,000 records/sec |
| Read throughput per shard | 2 MB/sec |
| Supports replay | Yes |
| Supports ordering | Within a shard |
| Supports multiple consumers | Yes |
| Supports encryption | Yes |
| Supports IAM | Yes |
| Supports CloudWatch | Yes |
| Supports CloudTrail | Yes |

---

# Interview Tips

- Explain why Kinesis is chosen over SQS or SNS.
- Discuss shard sizing and Partition Key selection.
- Mention CloudWatch metrics such as `IteratorAgeMilliseconds`.
- Understand Shared Fan-Out and Enhanced Fan-Out.
- Be comfortable designing real-time architectures.
- Know the differences between Data Streams, Firehose, and Data Analytics.
- Explain common production issues such as hot shards and throttling.
- Highlight security using IAM, AWS KMS, and CloudTrail.

---

# Summary

Amazon Kinesis interview questions typically focus on stream architecture, shards, partition keys, producers and consumers, scaling, security, monitoring, and real-world streaming use cases. A strong understanding of how records flow through a stream, how shard capacity affects performance, and how Kinesis integrates with other AWS services will prepare you for both technical interviews and AWS certification exams.