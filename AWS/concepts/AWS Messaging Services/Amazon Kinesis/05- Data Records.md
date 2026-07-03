# Introduction

Everything stored in Amazon Kinesis Data Streams is called a **Record**.

A record represents a single unit of streaming data produced by an application.

Examples include:

- A website click
- A payment transaction
- An IoT sensor reading
- A log entry
- A GPS location
- A stock market update

Understanding the structure and lifecycle of a record is essential for designing scalable streaming applications.

---

# What is a Record?

A record is the smallest unit of data stored inside a Kinesis Data Stream.

Each record consists of:

- Partition Key
- Sequence Number
- Data
- Arrival Timestamp

```
Kinesis Record

├── Partition Key

├── Sequence Number

├── Data

└── Timestamp
```

---

# Record Lifecycle

Every record follows a lifecycle.

```
Producer

↓

Create Record

↓

PutRecord()

↓

Kinesis Stream

↓

Stored in Shard

↓

Consumer Reads

↓

Processed

↓

Record Expires
```

---

# Record Structure

```
+------------------------------------+

Partition Key

--------------------------------------

Sequence Number

--------------------------------------

Data

--------------------------------------

Approximate Arrival Timestamp

+------------------------------------+
```

---

# Partition Key

Every record must contain a **Partition Key**.

Purpose:

- Determines the destination shard
- Maintains ordering
- Balances workload

Example

```
customer-101
```

---

# Sequence Number

Each record receives a unique Sequence Number.

```
Record

↓

Sequence Number

↓

4964873482734238
```

Sequence Numbers are generated automatically by Amazon Kinesis.

---

## Purpose

- Preserve ordering
- Identify records
- Support checkpointing
- Resume processing

---

# Data

The Data field contains the actual payload.

Examples

```json
{
    "orderId": 101,
    "status": "CREATED"
}
```

---

```json
{
    "temperature": 32.5
}
```

---

```json
{
    "page": "/products"
}
```

Applications define the payload format.

---

# Arrival Timestamp

Amazon Kinesis records the approximate arrival time.

```
Producer

↓

Kinesis

↓

Arrival Timestamp

↓

2026-07-03T15:10:25Z
```

Useful for:

- Auditing
- Analytics
- Debugging
- Event ordering

---

# Record Flow

```
Producer

↓

Create Record

↓

PutRecord()

↓

Shard

↓

Consumer

↓

Business Logic
```

---

# Record Example

```
Partition Key

↓

customer-101

----------------------

Sequence Number

↓

49583746572834

----------------------

Data

↓

{
    "orderId":101
}
```

---

# Maximum Record Size

A single record can contain:

```
Maximum

1 MB
```

This includes:

- Data
- Partition Key

Applications should avoid sending unnecessarily large records.

---

# Data Encoding

Amazon Kinesis stores data as binary.

Applications typically serialize data as:

- JSON
- CSV
- Avro
- Protocol Buffers
- Apache Parquet (after downstream processing)

Most applications use JSON.

---

# JSON Example

```json
{
    "customerId": 101,
    "productId": 5001,
    "quantity": 2,
    "price": 199.99
}
```

---

# Writing a Record

Records are written using PutRecord.

```
Application

↓

PutRecord()

↓

Kinesis
```

---

## AWS CLI Example

```bash
aws kinesis put-record \
    --stream-name OrderStream \
    --partition-key customer-101 \
    --data '{"orderId":101}'
```

---

## Boto3 Example

```python
import json
import boto3

kinesis = boto3.client("kinesis")

kinesis.put_record(
    StreamName="OrderStream",
    PartitionKey="customer-101",
    Data=json.dumps({
        "orderId":101
    })
)
```

---

# Batch Records

Applications can send multiple records together.

```
Producer

↓

10 Records

↓

PutRecords()

↓

Kinesis
```

Benefits

- Lower latency
- Lower cost
- Higher throughput

---

# Reading Records

Consumers retrieve records using:

```
Consumer

↓

GetRecords()

↓

Process
```

Each record contains:

- Partition Key
- Sequence Number
- Data

---

## Boto3 Example

```python
response = kinesis.get_records(
    ShardIterator=iterator
)

for record in response["Records"]:
    print(record["Data"])
```

---

# Record Ordering

Ordering is preserved **within a shard**.

```
Order Created

↓

Payment Received

↓

Order Packed

↓

Order Shipped
```

Applications reading the same shard receive records in this order.

---

Ordering is **not guaranteed across shards**.

---

# Record Retention

Records remain available for replay.

Retention period:

```
Minimum

24 Hours

↓

Maximum

365 Days
```

After expiration,

records are permanently removed.

---

# Replay Records

Consumers can replay historical data.

```
Old Records

↓

TRIM_HORIZON

↓

Replay

↓

Analytics
```

Useful for:

- Debugging
- Reprocessing
- Machine Learning
- Data Recovery

---

# Duplicate Records

Applications should assume duplicate records are possible.

Reasons include:

- Producer retries
- Consumer retries
- Network failures

Consumers should implement idempotent processing.

---

# Compression

Large payloads can be compressed.

```
Application

↓

Compress

↓

Kinesis

↓

Consumer

↓

Decompress
```

Compression reduces bandwidth usage.

---

# Real-World Example

A food delivery platform generates order events.

```
Customer Places Order

↓

Record Created

↓

Kinesis Stream

↓

Analytics

↓

Billing

↓

Notifications
```

Each order becomes an individual Kinesis record.

---

# Monitoring Records

Useful CloudWatch metrics include:

- IncomingRecords
- IncomingBytes
- GetRecords.Bytes
- GetRecords.Success
- IteratorAgeMilliseconds

These metrics help monitor record throughput and consumer performance.

---

# Best Practices

- Keep records as small as possible.
- Use JSON for readability unless a more compact format is required.
- Compress large payloads.
- Batch records using PutRecords.
- Choose meaningful Partition Keys.
- Design consumers to handle duplicate records.
- Configure retention based on business requirements.
- Archive historical data to Amazon S3 for long-term storage.

---

# Common Mistakes

## Sending Large Payloads

Large records reduce throughput.

Store large objects in Amazon S3 and stream only references when appropriate.

---

## Ignoring Ordering Rules

Ordering is guaranteed only within a shard.

---

## Assuming Records Are Stored Forever

Records expire after the configured retention period.

---

## Forgetting Idempotency

Consumers should safely process duplicate records.

---

## Using Poor Serialization Formats

Choose serialization formats that balance readability, size, and processing efficiency.

---

# Summary

A record is the fundamental unit of data in Amazon Kinesis Data Streams. Each record contains a Partition Key, Sequence Number, Data, and Arrival Timestamp. Records are written by producers, stored within shards, and processed by one or more consumers. Understanding record structure, retention, ordering, batching, and replay capabilities is essential for building scalable, low-latency streaming applications on AWS.