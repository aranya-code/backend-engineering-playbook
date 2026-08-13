# Introduction

The best way to learn Amazon Kinesis is by building a complete streaming pipeline.

In this lab, you will:

- Create a Kinesis Data Stream
- Send records using AWS CLI
- Send records using Boto3
- Read records from the stream
- Scale the stream
- Enable encryption
- Monitor using CloudWatch
- Delete the resources

This lab requires only an AWS account and the AWS CLI.

---

# Lab Architecture

```
Application

↓

Amazon Kinesis Data Stream

↓

Consumer

↓

CloudWatch
```

---

# Prerequisites

Before starting, ensure you have:

- AWS Account
- AWS CLI Installed
- Python 3.x
- Boto3 Installed
- IAM User or Role with Kinesis permissions

Verify AWS CLI.

```bash
aws --version
```

Verify credentials.

```bash
aws sts get-caller-identity
```

---

# Step 1 — Create a Stream

Create a stream named **OrderStream**.

```bash
aws kinesis create-stream \
    --stream-name OrderStream \
    --shard-count 1
```

---

## Verify Stream

```bash
aws kinesis list-streams
```

Expected output:

```text
OrderStream
```

---

## Describe Stream

```bash
aws kinesis describe-stream-summary \
    --stream-name OrderStream
```

Verify:

- Stream Status
- Open Shards
- Encryption Status

---

# Step 2 — Put Your First Record

```bash
aws kinesis put-record \
    --stream-name OrderStream \
    --partition-key customer-101 \
    --data "First Order"
```

Expected output:

```json
{
    "SequenceNumber":"...",
    "ShardId":"shardId-000000000000"
}
```

---

# Step 3 — Put Multiple Records

Create a Python file.

```python
import boto3

client = boto3.client("kinesis")

client.put_records(
    StreamName="OrderStream",
    Records=[
        {
            "Data":"Order 101",
            "PartitionKey":"customer-101"
        },
        {
            "Data":"Order 102",
            "PartitionKey":"customer-102"
        },
        {
            "Data":"Order 103",
            "PartitionKey":"customer-103"
        }
    ]
)

print("Records Sent")
```

Run:

```bash
python producer.py
```

---

# Step 4 — Read Records

List shards.

```bash
aws kinesis list-shards \
    --stream-name OrderStream
```

Copy the ShardId.

---

## Get Shard Iterator

```bash
aws kinesis get-shard-iterator \
    --stream-name OrderStream \
    --shard-id shardId-000000000000 \
    --shard-iterator-type TRIM_HORIZON
```

Copy the iterator.

---

## Read Records

```bash
aws kinesis get-records \
    --shard-iterator SHARD_ITERATOR
```

Expected output:

```text
Order 101

Order 102

Order 103
```

---

# Step 5 — Read Records Using Python

```python
import boto3

client = boto3.client("kinesis")

response = client.list_shards(
    StreamName="OrderStream"
)

shard_id = response["Shards"][0]["ShardId"]

iterator = client.get_shard_iterator(
    StreamName="OrderStream",
    ShardId=shard_id,
    ShardIteratorType="TRIM_HORIZON"
)

records = client.get_records(
    ShardIterator=iterator["ShardIterator"]
)

for record in records["Records"]:
    print(record["Data"])
```

---

# Step 6 — Increase Retention

Increase retention to 7 days.

```bash
aws kinesis increase-stream-retention-period \
    --stream-name OrderStream \
    --retention-period-hours 168
```

Verify:

```bash
aws kinesis describe-stream-summary \
    --stream-name OrderStream
```

---

# Step 7 — Scale the Stream

Increase shard count.

```bash
aws kinesis update-shard-count \
    --stream-name OrderStream \
    --target-shard-count 2 \
    --scaling-type UNIFORM_SCALING
```

Verify:

```bash
aws kinesis describe-stream-summary \
    --stream-name OrderStream
```

---

# Step 8 — Enable Encryption

Enable Server-Side Encryption.

```bash
aws kinesis start-stream-encryption \
    --stream-name OrderStream \
    --encryption-type KMS \
    --key-id alias/aws/kinesis
```

Verify:

```bash
aws kinesis describe-stream-summary \
    --stream-name OrderStream
```

Encryption should now be enabled.

---

# Step 9 — Monitor the Stream

Open:

```
AWS Console

↓

CloudWatch

↓

Metrics

↓

Kinesis
```

Observe:

- IncomingBytes
- IncomingRecords
- IteratorAgeMilliseconds
- WriteProvisionedThroughputExceeded

---

# Step 10 — Create a CloudWatch Alarm

Create an alarm for:

```
IteratorAgeMilliseconds

>

60000
```

Notification target:

```
Amazon SNS
```

---

# Step 11 — Generate More Records

Modify producer.

```python
import boto3
import random
import time

client = boto3.client("kinesis")

while True:

    client.put_record(
        StreamName="OrderStream",
        PartitionKey=str(random.randint(1,1000)),
        Data="Live Event"
    )

    time.sleep(1)
```

Run:

```bash
python producer.py
```

Observe CloudWatch metrics increasing.

---

# Step 12 — Test Multiple Consumers

Consumer A

```
Analytics
```

Consumer B

```
Fraud Detection
```

Consumer C

```
Dashboard
```

All consumers should read the same records independently.

---

# Step 13 — View CloudTrail Logs

Navigate:

```
AWS Console

↓

CloudTrail

↓

Event History
```

Search:

```
PutRecord
```

Observe:

- IAM Identity
- Time
- Region
- Source IP

---

# Step 14 — Test IAM Permissions

Remove:

```
kinesis:PutRecord
```

Attempt:

```bash
aws kinesis put-record ...
```

Expected error:

```text
AccessDeniedException
```

Restore the permission.

---

# Step 15 — Clean Up

Delete the stream.

```bash
aws kinesis delete-stream \
    --stream-name OrderStream
```

Verify:

```bash
aws kinesis list-streams
```

The stream should no longer exist.

---

# Bonus Exercise 1

Build an IoT simulator.

```
Temperature

↓

Kinesis

↓

Analytics

↓

Dashboard
```

Generate random sensor values every second.

---

# Bonus Exercise 2

Build a clickstream processor.

```
Website

↓

Kinesis

↓

Amazon S3

↓

Athena

↓

QuickSight
```

Analyze page views.

---

# Bonus Exercise 3

Build a payment processing pipeline.

```
Payment API

↓

Kinesis

↓

Fraud Detection

↓

Amazon S3

↓

Dashboard
```

---

# Bonus Exercise 4

Integrate AWS Lambda.

```
Producer

↓

Kinesis

↓

Lambda

↓

CloudWatch Logs
```

Every incoming record should invoke Lambda automatically.

---

# Expected Learning Outcomes

After completing this lab, you should be able to:

- Create Kinesis Data Streams
- Publish records using AWS CLI
- Publish records using Boto3
- Read streaming data
- Scale streams
- Increase retention
- Enable encryption
- Monitor using CloudWatch
- Audit with CloudTrail
- Delete AWS resources safely

---

# Best Practices

- Delete unused streams to avoid charges.
- Batch writes using `PutRecords()`.
- Use meaningful Partition Keys.
- Monitor CloudWatch metrics continuously.
- Enable Server-Side Encryption for production.
- Archive long-term data to Amazon S3.
- Implement retry logic for producers and consumers.

---

# Common Mistakes

## Using One Partition Key

Creates hot shards.

---

## Forgetting to Delete Resources

Unused streams continue to incur charges.

---

## Ignoring CloudWatch

Always monitor throughput and consumer lag.

---

## Not Testing IAM Policies

Verify permissions before deploying to production.

---

# Summary

This hands-on lab demonstrated the complete lifecycle of working with Amazon Kinesis Data Streams. You created a stream, published records using the AWS CLI and Boto3, consumed records, increased retention, scaled shard capacity, enabled server-side encryption, monitored performance using CloudWatch, audited API calls with CloudTrail, and safely cleaned up resources. Completing these exercises provides practical experience with the core operations required to build and manage real-time streaming applications on AWS.