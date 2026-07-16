# 05- Lambda Event Source Mapping (ESM).md

# Lambda Event Source Mapping (ESM)

One of the most commonly asked AWS Lambda interview topics is **Event Source Mapping (ESM)**.

Many developers believe services like **Amazon SQS**, **Kinesis**, or **DynamoDB Streams** directly invoke Lambda.

**This is incorrect.**

Instead, AWS creates an **Event Source Mapping**, which acts as a managed polling service between the event source and the Lambda function.

Understanding Event Source Mapping is essential for designing scalable, reliable, and cost-effective serverless applications.

---

# What is Event Source Mapping?

An **Event Source Mapping (ESM)** is an AWS-managed resource that continuously polls an event source on behalf of your Lambda function.

Instead of:

```text
SQS

↓

Lambda
```

The actual architecture is:

```text
SQS Queue

      │

      ▼

Event Source Mapping

      │

      ▼

AWS Poller

      │

      ▼

Lambda
```

The Lambda function **never polls the queue directly**.

AWS manages the polling infrastructure.

---

# Why Does AWS Need Event Source Mapping?

Services like:

- Amazon SQS
- DynamoDB Streams
- Kinesis
- Amazon MQ
- Kafka

store events until they are consumed.

Unlike API Gateway or S3, these services do not "push" events.

Someone must continuously check for new records.

AWS performs this work using Event Source Mapping.

---

# Supported Event Sources

Lambda Event Source Mapping supports:

| Service | Supported |
|----------|------------|
| Amazon SQS | ✅ |
| Amazon SQS FIFO | ✅ |
| DynamoDB Streams | ✅ |
| Kinesis Data Streams | ✅ |
| Amazon MSK | ✅ |
| Self Managed Kafka | ✅ |
| Amazon MQ | ✅ |
| Amazon DocumentDB Change Streams | ✅ |

These services all require polling.

---

# High-Level Architecture

```text
              Messages

                  │

                  ▼

          Event Source

                  │

                  ▼

      Event Source Mapping

                  │

                  ▼

          AWS Polling Service

                  │

                  ▼

             Lambda Function
```

The Event Source Mapping is fully managed by AWS.

---

# Responsibilities of Event Source Mapping

The Event Source Mapping performs several important tasks.

It:

- Polls the event source
- Reads new records
- Creates batches
- Invokes Lambda
- Handles retries
- Tracks checkpoints
- Manages concurrency
- Handles failures

Without ESM, developers would need to build their own polling service.

---

# Polling Workflow

Example using Amazon SQS:

```text
Application

↓

Send Message

↓

SQS Queue

↓

Event Source Mapping

↓

Read Messages

↓

Batch Messages

↓

Invoke Lambda

↓

Delete Successful Messages
```

---

# Event Source Mapping Lifecycle

```text
Create Mapping

↓

Start Polling

↓

Receive Records

↓

Create Batch

↓

Invoke Lambda

↓

Success?

      │

 ┌────┴────┐

 │         │

Yes       No

 │         │

Delete    Retry

Records
```

---

# Creating an Event Source Mapping

When configuring Lambda with SQS:

```text
Lambda

↓

Add Trigger

↓

Amazon SQS

↓

AWS Creates

↓

Event Source Mapping
```

The mapping becomes an independent AWS resource.

---

# Viewing Event Source Mappings

AWS CLI:

```bash
aws lambda list-event-source-mappings
```

Example output:

```json
{
  "UUID": "1234abcd",
  "State": "Enabled",
  "BatchSize": 10
}
```

---

# Important Configuration Options

When creating an Event Source Mapping, several settings can be configured.

---

# Batch Size

Defines how many records Lambda receives in one invocation.

Example:

```
Batch Size = 10
```

Queue:

```
100 Messages
```

Execution:

```text
Batch 1

10 Messages

↓

Lambda

Batch 2

10 Messages

↓

Lambda
```

Advantages:

- Lower cost
- Fewer invocations
- Better throughput

Disadvantages:

- Higher latency
- Larger retries

---

# Batch Window

AWS can wait before invoking Lambda.

Example:

```
Maximum Batching Window

5 Seconds
```

Workflow:

```text
Message Arrives

↓

Wait

↓

More Messages Arrive

↓

Batch Full

↓

Invoke Lambda
```

This improves efficiency for burst traffic.

---

# Maximum Concurrency

Event Source Mapping can limit the number of concurrent Lambda executions.

Example:

```
Maximum Concurrency = 20
```

Even if the queue contains:

```
500,000 Messages
```

AWS invokes at most:

```
20 Concurrent Lambdas
```

Useful for protecting downstream systems.

---

# Enabled / Disabled State

Mappings can be enabled or disabled.

```text
Enabled

↓

Polling Active
```

```text
Disabled

↓

Polling Stops
```

Messages remain in the queue.

---

# Starting Position

Applies to stream sources.

Options:

```
LATEST
```

Read only new records.

```
TRIM_HORIZON
```

Read from the oldest available record.

Example:

```text
Stream

Record1

Record2

Record3

Record4

LATEST

↓

Start at Record4
```

---

# Retry Behavior

Retry behavior depends on the event source.

---

## Amazon SQS

```text
Queue

↓

Lambda

↓

Failure

↓

Visibility Timeout

↓

Queue Again
```

Message becomes visible again.

---

## Kinesis

Failed batches are retried.

```text
Shard

↓

Batch

↓

Lambda

↓

Failure

↓

Retry
```

The shard pauses until processing succeeds or records expire.

---

## DynamoDB Streams

Exactly the same model as Kinesis.

Ordering is preserved.

---

# Batch Processing Example

Queue:

```
100 Messages
```

Batch size:

```
10
```

Lambda executions:

```
10 Invocations
```

Instead of:

```
100 Invocations
```

Batching greatly reduces costs.

---

# Partial Batch Response

Older behavior:

```text
Batch

↓

10 Records

↓

Record 7 Fails

↓

Entire Batch Retries
```

Problem:

Records 1-6 are processed again.

---

Modern Lambda supports Partial Batch Response.

```text
Batch

↓

Record 1 Success

Record 2 Success

Record 3 Failed

↓

Retry Only Record 3
```

This significantly reduces duplicate processing.

---

# Scaling Behavior

Event Source Mapping automatically scales polling.

Example:

```text
Queue

10 Messages

↓

1 Lambda
```

Later:

```text
Queue

100,000 Messages

↓

Many Pollers

↓

Many Lambdas
```

Scaling depends on:

- Queue depth
- Account concurrency
- Reserved concurrency
- Event source type

---

# Event Source Mapping vs Direct Invocation

| Feature | Direct Invocation | Event Source Mapping |
|----------|------------------|----------------------|
| Polling | No | Yes |
| Batching | No | Yes |
| Retry Management | Service Specific | AWS Managed |
| Ordering | Depends | Depends on Source |
| Queue Reading | No | Yes |
| Checkpoint Tracking | No | Yes |

---

# Production Example

Order Processing

```text
Customer

↓

Checkout

↓

SQS Queue

↓

Event Source Mapping

↓

Lambda

↓

Inventory Service

↓

Payment Service

↓

Shipping
```

Lambda never polls SQS directly.

AWS manages polling.

---

# Common Mistakes

## Assuming Lambda Polls the Queue

Incorrect:

```text
Lambda

↓

Read Queue
```

Correct:

```text
Queue

↓

AWS Poller

↓

Lambda
```

---

## Very Large Batch Sizes

Large batches:

Advantages:

- Fewer invocations

Disadvantages:

- Longer retries
- Higher memory usage
- More duplicate work if failures occur

Choose an appropriate batch size for your workload.

---

## Ignoring Partial Batch Response

Without Partial Batch Response:

```
1 Failed Record

↓

Entire Batch Retries
```

This increases costs and duplicate processing.

---

## Unlimited Concurrency

A sudden queue spike can overwhelm downstream databases.

Always consider:

- Reserved Concurrency
- Maximum Concurrency
- Batch Size

---

# Best Practices

✅ Use batch processing for throughput.

✅ Enable Partial Batch Response when supported.

✅ Configure DLQs for failed messages.

✅ Limit concurrency when downstream services have capacity constraints.

✅ Monitor queue depth and Lambda metrics.

✅ Design handlers to be idempotent.

---

# Senior Backend Engineering Perspective

Event Source Mapping is far more than a "trigger."

It is an AWS-managed polling engine responsible for:

- Reading records
- Creating batches
- Scaling pollers
- Managing retries
- Tracking checkpoints
- Invoking Lambda efficiently

A senior backend engineer understands that tuning **Batch Size**, **Batch Window**, **Maximum Concurrency**, and **Retry Policies** directly impacts system throughput, latency, downstream load, and overall cost.

In high-scale architectures processing millions of events, properly configured Event Source Mappings are often the difference between a resilient system and one that suffers from duplicate processing, throttling, or database overload.

---

# Interview Questions

### Beginner

- What is Event Source Mapping?
- Which AWS services require Event Source Mapping?
- Why is Event Source Mapping needed?

### Intermediate

- Does Lambda poll SQS directly?
- What is Batch Size?
- What is Maximum Batching Window?
- How does Event Source Mapping scale?

### Senior

- How would you tune Event Source Mapping for a queue processing 5 million messages per day?
- How would you prevent database overload using Maximum Concurrency?
- Why is Partial Batch Response important?
- How does Event Source Mapping maintain ordering for Kinesis and DynamoDB Streams?
- How would you optimize Event Source Mapping for low latency versus high throughput?

---

# Key Takeaways

- Event Source Mapping is an AWS-managed resource that polls queues and streams on behalf of Lambda.
- It is required for poll-based event sources such as SQS, DynamoDB Streams, Kinesis, Kafka, Amazon MQ, and DocumentDB Change Streams.
- Event Source Mapping manages polling, batching, retries, concurrency, and checkpoint tracking.
- Proper configuration of Batch Size, Batch Window, Maximum Concurrency, and Partial Batch Response is essential for building scalable and cost-efficient serverless applications.