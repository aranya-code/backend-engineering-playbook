# Introduction

Amazon Kinesis can be managed using multiple interfaces.

- AWS Management Console
- AWS CLI
- Boto3 (Python SDK)
- CloudFormation
- Terraform
- AWS CDK

This chapter serves as a quick reference for the most commonly used **AWS CLI commands** and **Boto3 methods** for Amazon Kinesis Data Streams.

---

# AWS CLI Configuration

Verify AWS CLI installation.

```bash
aws --version
```

---

Configure AWS credentials.

```bash
aws configure
```

---

Verify the active AWS account.

```bash
aws sts get-caller-identity
```

---

# Stream Operations

## Create Stream

```bash
aws kinesis create-stream \
    --stream-name OrderStream \
    --shard-count 2
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

## Delete Stream

```bash
aws kinesis delete-stream \
    --stream-name OrderStream
```

---

# Shard Operations

## List Shards

```bash
aws kinesis list-shards \
    --stream-name OrderStream
```

---

## Update Shard Count

```bash
aws kinesis update-shard-count \
    --stream-name OrderStream \
    --target-shard-count 4 \
    --scaling-type UNIFORM_SCALING
```

---

# Retention Operations

## Increase Retention

```bash
aws kinesis increase-stream-retention-period \
    --stream-name OrderStream \
    --retention-period-hours 168
```

---

## Decrease Retention

```bash
aws kinesis decrease-stream-retention-period \
    --stream-name OrderStream \
    --retention-period-hours 24
```

---

# Encryption Operations

## Enable Server-Side Encryption

```bash
aws kinesis start-stream-encryption \
    --stream-name OrderStream \
    --encryption-type KMS \
    --key-id alias/aws/kinesis
```

---

## Disable Server-Side Encryption

```bash
aws kinesis stop-stream-encryption \
    --stream-name OrderStream \
    --encryption-type KMS \
    --key-id alias/aws/kinesis
```

---

# Producer Operations

## Put Record

```bash
aws kinesis put-record \
    --stream-name OrderStream \
    --partition-key customer-101 \
    --data "Order Created"
```

---

## Put Multiple Records

The AWS CLI does not provide a simple inline command for batch record submission.

Use the AWS SDKs such as **Boto3** for `PutRecords()`.

---

# Consumer Operations

## List Shards

```bash
aws kinesis list-shards \
    --stream-name OrderStream
```

---

## Get Shard Iterator

```bash
aws kinesis get-shard-iterator \
    --stream-name OrderStream \
    --shard-id shardId-000000000000 \
    --shard-iterator-type LATEST
```

---

## Read Records

```bash
aws kinesis get-records \
    --shard-iterator SHARD_ITERATOR
```

---

# Tag Operations

## Add Tags

```bash
aws kinesis add-tags-to-stream \
    --stream-name OrderStream \
    --tags Environment=Development
```

---

## List Tags

```bash
aws kinesis list-tags-for-stream \
    --stream-name OrderStream
```

---

## Remove Tags

```bash
aws kinesis remove-tags-from-stream \
    --stream-name OrderStream \
    --tag-keys Environment
```

---

# Monitoring Commands

## List CloudWatch Metrics

```bash
aws cloudwatch list-metrics \
    --namespace AWS/Kinesis
```

---

## Get Metric Statistics

```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/Kinesis \
    --metric-name IncomingRecords \
    --start-time 2026-07-01T00:00:00Z \
    --end-time 2026-07-02T00:00:00Z \
    --period 300 \
    --statistics Sum
```

---

# Boto3 Configuration

Install Boto3.

```bash
pip install boto3
```

---

Create a client.

```python
import boto3

kinesis = boto3.client("kinesis")
```

---

# Create Stream

```python
kinesis.create_stream(
    StreamName="OrderStream",
    ShardCount=2
)
```

---

# List Streams

```python
response = kinesis.list_streams()

print(response["StreamNames"])
```

---

# Describe Stream

```python
response = kinesis.describe_stream_summary(
    StreamName="OrderStream"
)

print(response)
```

---

# Delete Stream

```python
kinesis.delete_stream(
    StreamName="OrderStream"
)
```

---

# Put Record

```python
kinesis.put_record(
    StreamName="OrderStream",
    Data="Order Created",
    PartitionKey="customer-101"
)
```

---

# Put Multiple Records

```python
kinesis.put_records(
    StreamName="OrderStream",
    Records=[
        {
            "Data":"Order 101",
            "PartitionKey":"customer-101"
        },
        {
            "Data":"Order 102",
            "PartitionKey":"customer-102"
        }
    ]
)
```

---

# List Shards

```python
response = kinesis.list_shards(
    StreamName="OrderStream"
)

print(response["Shards"])
```

---

# Get Shard Iterator

```python
iterator = kinesis.get_shard_iterator(
    StreamName="OrderStream",
    ShardId="shardId-000000000000",
    ShardIteratorType="LATEST"
)
```

---

# Read Records

```python
records = kinesis.get_records(
    ShardIterator=iterator["ShardIterator"]
)

print(records["Records"])
```

---

# Increase Retention

```python
kinesis.increase_stream_retention_period(
    StreamName="OrderStream",
    RetentionPeriodHours=168
)
```

---

# Decrease Retention

```python
kinesis.decrease_stream_retention_period(
    StreamName="OrderStream",
    RetentionPeriodHours=24
)
```

---

# Enable Encryption

```python
kinesis.start_stream_encryption(
    StreamName="OrderStream",
    EncryptionType="KMS",
    KeyId="alias/aws/kinesis"
)
```

---

# Disable Encryption

```python
kinesis.stop_stream_encryption(
    StreamName="OrderStream",
    EncryptionType="KMS",
    KeyId="alias/aws/kinesis"
)
```

---

# Update Shard Count

```python
kinesis.update_shard_count(
    StreamName="OrderStream",
    TargetShardCount=4,
    ScalingType="UNIFORM_SCALING"
)
```

---

# Common Boto3 Methods

| Method | Description |
|----------|-------------|
| create_stream() | Create a stream |
| delete_stream() | Delete a stream |
| list_streams() | List streams |
| describe_stream_summary() | Describe a stream |
| list_shards() | List shards |
| put_record() | Write one record |
| put_records() | Write multiple records |
| get_shard_iterator() | Create shard iterator |
| get_records() | Read records |
| update_shard_count() | Scale a stream |
| increase_stream_retention_period() | Increase retention |
| decrease_stream_retention_period() | Decrease retention |
| start_stream_encryption() | Enable encryption |
| stop_stream_encryption() | Disable encryption |

---

# Common AWS CLI Commands

| Command | Purpose |
|----------|----------|
| create-stream | Create stream |
| list-streams | List streams |
| describe-stream-summary | Describe stream |
| delete-stream | Delete stream |
| put-record | Write a record |
| get-records | Read records |
| get-shard-iterator | Create iterator |
| update-shard-count | Scale stream |
| increase-stream-retention-period | Increase retention |
| start-stream-encryption | Enable encryption |

---

# Developer Workflow

```
Create Stream

↓

Write Records

↓

Read Records

↓

Monitor CloudWatch

↓

Scale Stream

↓

Enable Encryption

↓

Delete Resources
```

---

# Best Practices

- Batch writes using `PutRecords()`.
- Reuse the Boto3 client instead of creating a new client for every request.
- Use IAM Roles instead of hardcoded AWS credentials.
- Monitor stream metrics with Amazon CloudWatch.
- Enable Server-Side Encryption using AWS KMS.
- Handle `ProvisionedThroughputExceededException` with exponential backoff.
- Use Infrastructure as Code (CloudFormation, Terraform, or CDK) to provision Kinesis resources.
- Validate stream status before sending or reading records.

---

# Summary

The AWS CLI and Boto3 SDK provide comprehensive tools for managing Amazon Kinesis Data Streams. Engineers can create streams, publish records, consume data, scale shard capacity, configure retention, enable encryption, and automate operations programmatically. Mastering these commands and APIs is essential for building, operating, and troubleshooting production-grade real-time streaming applications on AWS.