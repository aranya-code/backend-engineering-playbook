# Introduction

Even well-designed streaming applications can experience operational issues.

Common problems include:

- Write throttling
- Read throttling
- Consumer lag
- Hot shards
- Permission errors
- Encryption failures
- Scaling issues

Understanding how to identify and resolve these issues is essential for operating Amazon Kinesis in production.

---

# Troubleshooting Workflow

```
Application Issue

↓

Identify Symptoms

↓

CloudWatch Metrics

↓

CloudTrail Logs

↓

Root Cause

↓

Implement Fix

↓

Verify Resolution
```

---

# Problem 1 - Write Throttling

## Symptoms

- Producers receive exceptions
- Increased write latency
- Missing records
- Failed API requests

---

## Error

```text
ProvisionedThroughputExceededException
```

---

## Cause

The producer is writing more data than the shard can handle.

Each shard supports:

- 1 MB/sec write throughput
- 1,000 records/sec

---

## Architecture

```
Producer

↓

Too Many Records

↓

Shard Limit Exceeded

↓

Write Throttling
```

---

## Resolution

- Increase shard count
- Switch to On-Demand Mode
- Batch records using `PutRecords()`
- Improve Partition Key distribution

---

# Problem 2 - Read Throttling

## Symptoms

- Consumers process records slowly
- High latency
- Read failures

---

## Error

```text
ProvisionedThroughputExceededException
```

---

## Cause

Consumers exceed shard read capacity.

---

## Resolution

- Increase shards
- Reduce polling frequency
- Use Enhanced Fan-Out
- Optimize consumer processing

---

# Problem 3 - High Iterator Age

## Symptoms

CloudWatch metric:

```
IteratorAgeMilliseconds

Increasing...
```

---

## Cause

Consumers cannot process incoming records quickly enough.

```
Producer

↓

Kinesis

↓

Consumer

↓

Slow Processing
```

---

## Resolution

- Scale consumers
- Optimize business logic
- Increase shard count
- Use Enhanced Fan-Out

---

# Problem 4 - Hot Shards

## Symptoms

- One shard reaches capacity
- Other shards remain idle
- Uneven throughput

---

## Example

```
Shard 1

██████████

Shard 2

██

Shard 3

█
```

---

## Cause

Poor Partition Key selection.

Example

```
Partition Key

↓

Orders
```

All records hash to the same shard.

---

## Resolution

Use high-cardinality Partition Keys.

Good

```
customer-101

customer-102

customer-103
```

---

# Problem 5 - Access Denied

## Error

```text
AccessDeniedException
```

---

## Cause

IAM permissions are missing.

---

## Resolution

Verify IAM policy includes required actions.

Example

```json
{
    "Effect": "Allow",
    "Action": [
        "kinesis:PutRecord",
        "kinesis:GetRecords"
    ],
    "Resource": "*"
}
```

Use least privilege in production.

---

# Problem 6 - Stream Not Found

## Error

```text
ResourceNotFoundException
```

---

## Cause

- Incorrect stream name
- Wrong AWS Region
- Stream deleted

---

## Resolution

Verify:

```bash
aws kinesis list-streams
```

Confirm the correct Region and stream name.

---

# Problem 7 - Encryption Errors

## Symptoms

Applications cannot write to encrypted streams.

---

## Cause

Missing AWS KMS permissions.

---

## Resolution

Grant permissions such as:

- kms:Encrypt
- kms:Decrypt
- kms:GenerateDataKey

Ensure the IAM role can use the KMS key.

---

# Problem 8 - Consumer Processing Duplicates

## Symptoms

Business logic executes twice.

Examples:

- Duplicate payments
- Duplicate notifications

---

## Cause

Consumers retried processing after a failure.

Amazon Kinesis provides **at-least-once processing**, so duplicates are possible.

---

## Resolution

Implement idempotent consumers.

```
Receive Record

↓

Already Processed?

↓

Yes

↓

Ignore
```

---

# Problem 9 - Records Expired

## Symptoms

Historical records cannot be replayed.

---

## Cause

Retention period expired.

```
Retention

↓

24 Hours

↓

Expired

↓

Deleted
```

---

## Resolution

Increase retention.

```bash
aws kinesis increase-stream-retention-period \
    --stream-name OrderStream \
    --retention-period-hours 168
```

---

# Problem 10 - Low Throughput

## Symptoms

- Slow writes
- Slow reads
- Increased latency

---

## Cause

Insufficient shards.

---

## Resolution

Increase shard count.

```
2 Shards

↓

4 Shards

↓

8 Shards
```

---

# Problem 11 - High Costs

## Symptoms

Unexpected AWS bill.

---

## Possible Causes

- Too many shards
- Long retention period
- Enhanced Fan-Out enabled
- High data volume

---

## Resolution

- Merge underutilized shards
- Reduce retention if appropriate
- Review consumer architecture
- Monitor CloudWatch usage metrics

---

# Problem 12 - Uneven Record Distribution

## Symptoms

Some shards are idle while others are overloaded.

---

## Cause

Partition Keys do not distribute traffic evenly.

---

## Resolution

Use values with high cardinality.

Examples

Good

```
customerId
```

Bad

```
Orders
```

---

# Problem 13 - Lambda Consumer Timeout

## Symptoms

Lambda invocation fails.

---

## Error

```text
Task timed out
```

---

## Cause

Record processing exceeds Lambda timeout.

---

## Resolution

- Increase Lambda timeout
- Optimize processing
- Process records in batches
- Offload heavy work to downstream services

---

# Problem 14 - Firehose Delivery Failure

## Symptoms

Records are not delivered to Amazon S3 or Amazon Redshift.

---

## Cause

- Destination unavailable
- IAM permission issues
- Invalid configuration

---

## Resolution

- Review Firehose error logs
- Verify destination permissions
- Configure S3 backup bucket
- Check CloudWatch metrics

---

# Problem 15 - Slow Stream Processing

## Symptoms

Real-time dashboards update slowly.

---

## Cause

- Consumer bottlenecks
- Large records
- Network latency
- Complex business logic

---

## Resolution

- Optimize application code
- Scale consumers
- Reduce record size
- Use Enhanced Fan-Out

---

# Troubleshooting Checklist

Before investigating further, verify:

- Stream exists
- Correct AWS Region
- IAM permissions
- KMS permissions
- Stream encryption
- Shard utilization
- Consumer lag
- CloudWatch metrics
- CloudTrail logs
- Retention period

---

# Useful AWS CLI Commands

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

## List Tags

```bash
aws kinesis list-tags-for-stream \
    --stream-name OrderStream
```

---

# CloudWatch Metrics to Check

| Metric | Purpose |
|---------|---------|
| IncomingBytes | Producer throughput |
| IncomingRecords | Producer activity |
| OutgoingBytes | Consumer throughput |
| IteratorAgeMilliseconds | Consumer lag |
| WriteProvisionedThroughputExceeded | Write throttling |
| ReadProvisionedThroughputExceeded | Read throttling |

---

# Best Practices

- Monitor CloudWatch continuously.
- Configure CloudWatch alarms.
- Enable CloudTrail auditing.
- Use meaningful Partition Keys.
- Batch writes using `PutRecords()`.
- Monitor IteratorAgeMilliseconds.
- Design idempotent consumers.
- Scale before throttling occurs.
- Archive important data to Amazon S3.

---

# Common Mistakes

## Ignoring Consumer Lag

High Iterator Age often indicates downstream bottlenecks.

---

## Waiting Until Streams Fail

Scale proactively based on CloudWatch metrics.

---

## Using One Partition Key

This creates hot shards and uneven utilization.

---

## Forgetting KMS Permissions

Encrypted streams require appropriate KMS access.

---

## Assuming Records Never Expire

Records are deleted after the configured retention period.

---

# Summary

Most Amazon Kinesis production issues are related to throughput limits, shard utilization, consumer lag, permissions, encryption, or retention settings. By monitoring CloudWatch metrics, reviewing CloudTrail logs, selecting effective Partition Keys, implementing idempotent consumers, and scaling streams proactively, engineers can quickly diagnose and resolve operational issues while maintaining highly available and reliable real-time streaming applications.