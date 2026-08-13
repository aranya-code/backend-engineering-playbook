# Introduction

This cheat sheet provides a quick reference for Amazon Kinesis concepts, architecture, limits, APIs, monitoring metrics, security, and best practices.

Use it as a revision guide for interviews, AWS certifications, and day-to-day development.

---

# Amazon Kinesis Services

| Service | Purpose |
|----------|----------|
| Kinesis Data Streams | Real-time data streaming |
| Kinesis Data Firehose | Managed data delivery |
| Kinesis Data Analytics | Real-time stream analytics |
| Kinesis Video Streams | Video ingestion and processing |

---

# Core Components

```
Producer

↓

Kinesis Stream

↓

Shard

↓

Record

↓

Consumer
```

---

# Record Structure

```
Record

├── Partition Key

├── Sequence Number

├── Data

└── Approximate Arrival Timestamp
```

---

# Stream Architecture

```
Applications

↓

Amazon Kinesis Stream

↓

Multiple Shards

↓

Consumers
```

---

# Shard Capacity

| Property | Value |
|----------|-------|
| Write Throughput | **1 MB/sec or 1,000 records/sec** |
| Read Throughput | **2 MB/sec** |

---

# Record Limits

| Property | Value |
|----------|-------|
| Maximum Record Size | **1 MB** |
| Default Retention | **24 Hours** |
| Maximum Retention | **365 Days** |

---

# Capacity Modes

## Provisioned Mode

- Manual shard management
- Predictable workloads
- Lower operational cost

---

## On-Demand Mode

- Automatic scaling
- No shard planning
- Ideal for unpredictable workloads

---

# Shard Operations

```
Scale Out

↓

Split Shard

----------------

Scale In

↓

Merge Shards
```

---

# Partition Key

Purpose:

- Select shard
- Maintain ordering
- Distribute traffic

Good Example

```
customer-101
```

Poor Example

```
Orders
```

---

# Sequence Number

Generated automatically.

Used for:

- Ordering
- Checkpointing
- Record identification

---

# Producer APIs

| API | Purpose |
|------|---------|
| PutRecord | Send one record |
| PutRecords | Send multiple records |

---

# Consumer APIs

| API | Purpose |
|------|---------|
| GetShardIterator | Obtain iterator |
| GetRecords | Read records |

---

# Shard Iterator Types

| Type | Description |
|------|-------------|
| LATEST | Read new records |
| TRIM_HORIZON | Read oldest available records |
| AT_SEQUENCE_NUMBER | Start at a sequence number |
| AFTER_SEQUENCE_NUMBER | Start after a sequence number |
| AT_TIMESTAMP | Start at a timestamp |

---

# Consumer Models

## Shared Fan-Out

- Shared throughput
- Lower cost

---

## Enhanced Fan-Out

- Dedicated throughput
- Lower latency
- Independent consumers

---

# Kinesis Data Firehose

Purpose:

- Managed delivery
- Buffering
- Compression
- Format conversion

Supported Destinations:

- Amazon S3
- Amazon Redshift
- Amazon OpenSearch Service
- Snowflake
- Splunk
- HTTP Endpoints

---

# Kinesis Data Analytics

Supports:

- SQL
- Apache Flink

Common Use Cases:

- Fraud detection
- IoT analytics
- Clickstream analysis
- Real-time dashboards

---

# CloudWatch Metrics

| Metric | Purpose |
|----------|----------|
| IncomingBytes | Producer throughput |
| IncomingRecords | Producer activity |
| OutgoingBytes | Consumer throughput |
| OutgoingRecords | Records delivered |
| IteratorAgeMilliseconds | Consumer lag |
| WriteProvisionedThroughputExceeded | Write throttling |
| ReadProvisionedThroughputExceeded | Read throttling |

---

# Important AWS CLI Commands

## Create Stream

```bash
aws kinesis create-stream \
    --stream-name OrderStream \
    --shard-count 1
```

---

## List Streams

```bash
aws kinesis list-streams
```

---

## Describe Stream

```bash
aws kinesis describe-stream-summary \
    --stream-name OrderStream
```

---

## Put Record

```bash
aws kinesis put-record \
    --stream-name OrderStream \
    --partition-key customer-101 \
    --data "Hello"
```

---

## Delete Stream

```bash
aws kinesis delete-stream \
    --stream-name OrderStream
```

---

## Increase Retention

```bash
aws kinesis increase-stream-retention-period \
    --stream-name OrderStream \
    --retention-period-hours 168
```

---

## Update Shard Count

```bash
aws kinesis update-shard-count \
    --stream-name OrderStream \
    --target-shard-count 2 \
    --scaling-type UNIFORM_SCALING
```

---

# Common Boto3 Methods

| Method | Purpose |
|----------|----------|
| create_stream() | Create stream |
| delete_stream() | Delete stream |
| list_streams() | List streams |
| describe_stream_summary() | Stream details |
| put_record() | Send one record |
| put_records() | Send multiple records |
| get_shard_iterator() | Get iterator |
| get_records() | Read records |
| update_shard_count() | Scale stream |
| start_stream_encryption() | Enable encryption |

---

# Security Checklist

✅ IAM Roles

✅ Least Privilege

✅ HTTPS

✅ AWS KMS

✅ CloudTrail

✅ CloudWatch

✅ VPC Endpoints

---

# Monitoring Checklist

Monitor:

- IncomingBytes
- IncomingRecords
- IteratorAgeMilliseconds
- Write Throttling
- Read Throttling
- Consumer Health

---

# Best Partition Keys

Good

```
customerId

deviceId

userId

orderId
```

Poor

```
Orders

Payments

Logs

Events
```

---

# Common Errors

## Write Throttling

```
ProvisionedThroughputExceededException
```

Cause

- Too much write traffic

Solution

- Add shards
- Batch writes

---

## Read Throttling

```
ProvisionedThroughputExceededException
```

Solution

- Enhanced Fan-Out
- More shards

---

## Access Denied

```
AccessDeniedException
```

Solution

- Verify IAM permissions

---

## Stream Missing

```
ResourceNotFoundException
```

Solution

- Verify stream name
- Verify AWS Region

---

# Kinesis vs SQS vs SNS

| Feature | Kinesis | SQS | SNS |
|----------|----------|-----|-----|
| Streaming | ✅ | ❌ | ❌ |
| Queue | ❌ | ✅ | ❌ |
| Pub/Sub | ❌ | ❌ | ✅ |
| Multiple Consumers | ✅ | ❌ | ✅ |
| Replay | ✅ | ❌ | ❌ |
| Ordering | Within Shard | FIFO Queue | FIFO Topic |
| Analytics | ✅ | ❌ | ❌ |

---

# Firehose vs Data Streams

| Data Streams | Firehose |
|--------------|----------|
| Custom processing | Managed delivery |
| Replay | Yes |
| Multiple consumers | Yes |
| Automatic delivery | No |

---

# Typical Architecture

```
Applications

↓

Amazon Kinesis

↓

Lambda

↓

Analytics

↓

Amazon S3

↓

QuickSight
```

---

# Production Checklist

```
☐ Capacity Mode Selected

☐ Partition Keys Reviewed

☐ Encryption Enabled

☐ IAM Configured

☐ CloudWatch Monitoring Enabled

☐ CloudTrail Enabled

☐ Consumer Retry Logic

☐ Checkpointing Implemented

☐ Data Archived

☐ Infrastructure as Code
```

---

# Best Practices

- Batch records.
- Keep records small.
- Use good Partition Keys.
- Monitor CloudWatch continuously.
- Enable KMS encryption.
- Use IAM Roles.
- Scale before throttling.
- Archive historical data.
- Design idempotent consumers.
- Use On-Demand Mode for unpredictable traffic.

---

# Common Mistakes

- Using one Partition Key
- Ignoring IteratorAgeMilliseconds
- Hardcoding AWS credentials
- Waiting for throttling before scaling
- Sending unnecessarily large records
- Forgetting CloudTrail
- Ignoring retention settings

---

# Exam & Interview Facts

| Question | Answer |
|----------|--------|
| Max Record Size | 1 MB |
| Default Retention | 24 Hours |
| Max Retention | 365 Days |
| Write Throughput | 1 MB/sec or 1,000 records/sec per shard |
| Read Throughput | 2 MB/sec per shard |
| Ordering | Within a shard |
| Multiple Consumers | Yes |
| Replay | Yes |
| Encryption | AWS KMS |
| Monitoring | CloudWatch |
| Auditing | CloudTrail |

---

# Decision Tree

```
Need a Queue?

↓

Yes

↓

Amazon SQS

----------------------

Need Pub/Sub?

↓

Yes

↓

Amazon SNS

----------------------

Need Real-Time Streaming?

↓

Yes

↓

Amazon Kinesis
```

---

# Summary

Amazon Kinesis is AWS's fully managed real-time streaming platform for ingesting, processing, and analyzing continuous streams of data. Understanding shards, partition keys, producers, consumers, scaling, security, monitoring, and service integrations enables you to build reliable, low-latency, and highly scalable streaming applications. This cheat sheet serves as a quick reference for the most important concepts, APIs, limits, metrics, and best practices used in production environments.