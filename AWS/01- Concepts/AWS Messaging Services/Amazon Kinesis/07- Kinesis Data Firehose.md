# Introduction

Collecting streaming data is only one part of a real-time data pipeline.

Organizations also need to:

- Store streaming data
- Transform records
- Compress data
- Convert data formats
- Load data into analytics platforms

Amazon **Kinesis Data Firehose** is a fully managed service that automatically delivers streaming data to AWS storage and analytics services without requiring consumers to manage infrastructure.

Unlike Kinesis Data Streams, Firehose focuses on **data delivery**, not custom stream processing.

---

# What is Kinesis Data Firehose?

Amazon Kinesis Data Firehose is a fully managed data delivery service.

It automatically captures, buffers, transforms, and delivers streaming data to supported destinations.

```
Data Producer

↓

Firehose Delivery Stream

↓

Transform (Optional)

↓

Destination
```

Firehose eliminates the need to build custom consumers.

---

# Why Use Firehose?

Imagine thousands of applications generating logs every second.

Without Firehose:

```
Applications

↓

Custom Consumer

↓

Buffer Data

↓

Compress

↓

Store in S3
```

You must build and maintain the delivery application.

---

With Firehose:

```
Applications

↓

Firehose

↓

Amazon S3
```

AWS handles everything automatically.

---

# Firehose Architecture

```
Applications

↓

Kinesis Data Firehose

↓

Buffer

↓

(Optional Lambda)

↓

Compress

↓

Destination
```

---

# Supported Data Sources

Firehose accepts data from:

- Direct Put
- Amazon Kinesis Data Streams
- Amazon MSK (Managed Kafka)
- Amazon CloudWatch Logs
- AWS IoT

---

# Supported Destinations

Firehose can automatically deliver data to:

- Amazon S3
- Amazon Redshift
- Amazon OpenSearch Service
- Amazon OpenSearch Serverless
- Splunk
- Snowflake
- HTTP Endpoints

---

# Data Flow

```
Producer

↓

Firehose

↓

Buffer

↓

Transform

↓

Compress

↓

Destination
```

---

# Buffering

Firehose temporarily buffers records before delivery.

```
Incoming Records

↓

Buffer

↓

Delivery
```

Buffering reduces API calls and improves delivery efficiency.

---

## Buffer Conditions

Firehose delivers data when either condition is met:

- Buffer Size
- Buffer Time

Example

```
5 MB

OR

300 Seconds
```

Whichever occurs first triggers delivery.

---

# Data Transformation

Firehose can invoke AWS Lambda before delivering records.

```
Producer

↓

Firehose

↓

Lambda

↓

Modified Record

↓

Amazon S3
```

---

## Common Transformations

- JSON validation
- Field masking
- Data enrichment
- Data cleansing
- Timestamp formatting

---

# Data Compression

Firehose supports automatic compression.

Supported formats include:

- GZIP
- ZIP
- Snappy
- Hadoop Snappy

Benefits:

- Reduced storage costs
- Faster analytics
- Lower network bandwidth

---

# Data Format Conversion

Firehose can automatically convert formats.

Example

```
JSON

↓

Apache Parquet

↓

Amazon S3
```

Supported output formats:

- Parquet
- ORC

These formats improve analytical query performance.

---

# Delivery Stream

Unlike Data Streams, Firehose uses a **Delivery Stream**.

```
Producer

↓

Delivery Stream

↓

Destination
```

Applications write records to the delivery stream.

---

# Creating a Delivery Stream

## AWS CLI

```bash
aws firehose create-delivery-stream \
    --delivery-stream-name order-stream \
    --delivery-stream-type DirectPut
```

---

## Boto3

```python
import boto3

firehose = boto3.client("firehose")
```

---

# Sending Records

## AWS CLI

```bash
aws firehose put-record \
    --delivery-stream-name order-stream \
    --record Data="Order Created"
```

---

## Boto3

```python
firehose.put_record(
    DeliveryStreamName="order-stream",
    Record={
        "Data": b"Order Created"
    }
)
```

---

# Batch Records

Firehose supports sending multiple records together.

```
Application

↓

PutRecordBatch()

↓

Firehose
```

Batching improves throughput and reduces API calls.

---

## Boto3 Example

```python
firehose.put_record_batch(
    DeliveryStreamName="order-stream",
    Records=[
        {"Data": b"Order 101"},
        {"Data": b"Order 102"}
    ]
)
```

---

# Firehose to Amazon S3

One of the most common architectures.

```
Applications

↓

Firehose

↓

Amazon S3

↓

Athena

↓

QuickSight
```

Streaming data becomes immediately available for analytics.

---

# Firehose to Amazon Redshift

```
Applications

↓

Firehose

↓

Amazon S3

↓

COPY

↓

Amazon Redshift
```

Firehose stages data in Amazon S3 before loading it into Redshift.

---

# Firehose to OpenSearch

```
Applications

↓

Firehose

↓

OpenSearch

↓

Dashboards
```

Useful for:

- Log analytics
- Security monitoring
- Operational dashboards

---

# Firehose Monitoring

Amazon CloudWatch provides delivery metrics.

Common metrics:

- IncomingRecords
- IncomingBytes
- DeliveryToS3.Success
- DeliveryToS3.DataFreshness
- DeliveryToRedshift.Success
- DeliveryToOpenSearch.Success

---

# Error Handling

Failed records can be stored in an S3 backup bucket.

```
Delivery Failed

↓

Backup Bucket

↓

Retry
```

This prevents data loss.

---

# Kinesis Data Streams vs Firehose

| Data Streams | Firehose |
|---------------|-----------|
| Real-time stream processing | Managed data delivery |
| Multiple consumers | Single delivery pipeline |
| Custom applications | Automatic delivery |
| Replay supported | No replay |
| Shard management | No shard management |

---

# Firehose vs Data Streams

Choose **Kinesis Data Streams** when:

- Custom processing is required
- Multiple consumers exist
- Replay capability is needed
- Low-latency processing is critical

Choose **Firehose** when:

- Data needs to be stored automatically
- Minimal operational effort is desired
- ETL pipelines are required
- Analytics is the primary goal

---

# Real-World Example

A web application generates access logs.

```
Web Servers

↓

Firehose

↓

Lambda

↓

Compress

↓

Parquet

↓

Amazon S3

↓

Athena

↓

QuickSight
```

No custom delivery application is required.

---

# Best Practices

- Use Firehose for managed data delivery.
- Enable compression to reduce storage costs.
- Convert JSON to Parquet for analytics workloads.
- Use Lambda for lightweight transformations.
- Configure S3 backup for failed records.
- Monitor delivery metrics with CloudWatch.
- Select appropriate buffer sizes based on workload.

---

# Common Mistakes

## Using Firehose for Custom Stream Processing

Firehose is designed for delivery, not complex stream processing.

Use Kinesis Data Streams or Apache Flink when custom processing is required.

---

## Ignoring Compression

Compression significantly reduces storage costs.

Always enable it when appropriate.

---

## Choosing Small Buffer Sizes

Very small buffers increase delivery frequency and costs.

Tune buffering based on latency requirements.

---

## Not Configuring Backup Storage

Without an S3 backup bucket, failed records may be harder to investigate.

---

## Using Firehose When Replay Is Required

Firehose cannot replay delivered records.

Use Kinesis Data Streams if replay functionality is needed.

---

# Summary

Amazon Kinesis Data Firehose is a fully managed streaming data delivery service that automatically captures, buffers, transforms, compresses, and delivers streaming data to destinations such as Amazon S3, Amazon Redshift, OpenSearch Service, and Snowflake. By eliminating infrastructure management and supporting built-in data transformation and format conversion, Firehose enables organizations to build reliable, scalable, and low-maintenance data ingestion pipelines for analytics and data lake architectures.