# Introduction

Amazon Kinesis Data Streams (KDS) is the core streaming service within Amazon Kinesis.

It enables applications to continuously collect, process, and analyze streaming data with low latency.

Unlike traditional messaging systems, Kinesis Data Streams is designed to handle **continuous, high-volume data streams** where multiple applications can process the same data independently.

---

# What is Kinesis Data Streams?

Amazon Kinesis Data Streams is a scalable data streaming service that captures gigabytes of streaming data every second.

Applications continuously write data into a stream.

Consumers then read and process the records independently.

```
Producers

↓

Kinesis Data Stream

↓

Consumers
```

---

# Why Use Kinesis Data Streams?

Imagine a large online shopping platform.

Every second, the application generates:

- User clicks
- Product searches
- Shopping cart updates
- Payments
- Orders
- Application logs

Instead of storing these events and processing them later,

Kinesis allows applications to process them immediately.

```
Application

↓

Kinesis Data Stream

↓

Real-Time Analytics

↓

Dashboard
```

---

# Data Stream Architecture

```
              Producers

      ┌────────┼────────┐

      ▼        ▼        ▼

 Web App   Mobile App   IoT Device

                │

                ▼

      Amazon Kinesis Data Stream

      ┌────────┼────────┬─────────┐

      ▼        ▼        ▼

 Lambda   Analytics   Storage
```

Multiple producers and multiple consumers can operate simultaneously.

---

# Components of a Data Stream

A Kinesis Data Stream consists of:

- Stream
- Shards
- Records
- Producers
- Consumers

```
Kinesis Data Stream

│

├── Shard 1

├── Shard 2

└── Shard 3
```

---

# Stream

A stream is a collection of shards.

Applications write records into the stream.

```
Application

↓

Stream

↓

Records
```

---

# Shards

A shard is the fundamental unit of capacity within a Kinesis Data Stream.

Each shard provides:

- Write capacity
- Read capacity

Multiple shards increase throughput.

```
Stream

├── Shard A

├── Shard B

└── Shard C
```

Shards are covered in detail in the next chapter.

---

# Records

A record is the smallest unit of data stored in a stream.

Each record contains:

- Partition Key
- Sequence Number
- Data Blob

```
Record

↓

Partition Key

↓

Sequence Number

↓

Data
```

---

# Producers

Producers continuously send records into a stream.

Examples:

- Web applications
- Mobile applications
- IoT devices
- Backend services
- Amazon EC2
- Amazon ECS

---

# Consumers

Consumers read records from the stream.

Examples:

- AWS Lambda
- Apache Flink
- Custom applications
- Analytics platforms

---

# Data Flow

```
Producer

↓

PutRecord()

↓

Kinesis Stream

↓

Consumer

↓

Process Data
```

---

# Writing Data

Applications send records using:

- PutRecord
- PutRecords

```
Application

↓

PutRecord()

↓

Stream
```

---

## PutRecord

Writes one record at a time.

### AWS CLI Example

```bash
aws kinesis put-record \
    --stream-name OrderStream \
    --partition-key customer-101 \
    --data "Order Created"
```

---

### Boto3 Example

```python
import boto3

kinesis = boto3.client("kinesis")

kinesis.put_record(
    StreamName="OrderStream",
    Data="Order Created",
    PartitionKey="customer-101"
)
```

---

# PutRecords

Writes multiple records in one request.

Benefits:

- Higher throughput
- Lower API cost
- Better performance

---

### AWS CLI

The AWS CLI does not provide a simple inline command for sending multiple records.

Instead, use the AWS SDKs such as Boto3.

---

### Boto3 Example

```python
kinesis.put_records(
    StreamName="OrderStream",
    Records=[
        {
            "Data": "Order 101",
            "PartitionKey": "customer-101"
        },
        {
            "Data": "Order 102",
            "PartitionKey": "customer-102"
        }
    ]
)
```

---

# Reading Data

Consumers retrieve records using:

- GetShardIterator
- GetRecords

```
Consumer

↓

GetRecords()

↓

Process Records
```

---

### Boto3 Example

```python
iterator = kinesis.get_shard_iterator(
    StreamName="OrderStream",
    ShardId="shardId-000000000000",
    ShardIteratorType="LATEST"
)

records = kinesis.get_records(
    ShardIterator=iterator["ShardIterator"]
)
```

---

# Data Retention

Kinesis stores records temporarily.

Retention can be configured from:

```
24 Hours

↓

365 Days
```

Longer retention allows applications to replay historical data.

---

# Multiple Consumers

One of the biggest advantages of Kinesis Data Streams is that multiple consumers can process the same records.

```
Producer

↓

Kinesis Stream

↓

Analytics

↓

Lambda

↓

Monitoring
```

Each consumer reads independently.

---

# Ordering

Records with the same Partition Key remain ordered.

```
Customer-101

↓

Order Created

↓

Payment Received

↓

Order Shipped
```

Ordering is preserved within a shard.

---

# Scaling

As traffic grows,

additional shards can be added.

```
2 Shards

↓

4 Shards

↓

8 Shards
```

This increases stream capacity.

---

# Real-World Example

A ride-sharing application generates GPS updates.

```
Driver App

↓

Kinesis Data Stream

↓

Route Analytics

↓

Fraud Detection

↓

Real-Time Dashboard
```

Each consumer processes the same stream independently.

---

# Kinesis Data Streams vs Amazon SQS

| Kinesis Data Streams | Amazon SQS |
|-----------------------|------------|
| Streaming platform | Message queue |
| Multiple consumers | One consumer per message |
| Ordered within shards | FIFO only |
| Continuous data | Discrete messages |
| Replay supported | No replay after deletion |

---

# Kinesis Data Streams vs Amazon SNS

| Kinesis Data Streams | Amazon SNS |
|----------------------|------------|
| Data streaming | Event broadcasting |
| Pull model | Push model |
| Temporary retention | No storage |
| Replay capability | No replay |
| Analytics workloads | Notification workloads |

---

# Best Practices

- Choose meaningful stream names.
- Use batch operations whenever possible.
- Select good Partition Keys for even data distribution.
- Monitor stream throughput with CloudWatch.
- Increase shard count before reaching capacity limits.
- Archive long-term data to Amazon S3.
- Implement retry logic for throttled requests.

---

# Common Mistakes

## Using One Partition Key

Sending every record with the same Partition Key creates a hot shard.

Distribute traffic evenly.

---

## Ignoring Stream Capacity

Insufficient shard capacity causes throttling.

Monitor utilization and scale proactively.

---

## Choosing Kinesis for Background Jobs

Kinesis is optimized for continuous streaming.

For background processing, Amazon SQS is often a better choice.

---

## Forgetting Retention Requirements

Increase retention if applications need to replay historical records.

---

# Summary

Amazon Kinesis Data Streams enables applications to ingest, process, and analyze continuous streams of data with low latency. By organizing records into streams and shards, supporting multiple independent consumers, and allowing configurable data retention, Kinesis Data Streams provides a scalable foundation for real-time analytics, event processing, IoT telemetry, and large-scale streaming applications.