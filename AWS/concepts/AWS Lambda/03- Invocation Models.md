# 03- Lambda Invocation Models.md

# Lambda Invocation Models

AWS Lambda supports multiple invocation models depending on how the event source communicates with the function.

Choosing the correct invocation model is one of the most important architectural decisions when building serverless applications because it directly impacts:

- Performance
- Reliability
- Retry behavior
- Error handling
- Cost
- User experience

AWS Lambda supports three primary invocation models:

1. **Synchronous Invocation**
2. **Asynchronous Invocation**
3. **Poll-Based Invocation (Event Source Mapping)**

---

# High-Level Architecture

```text
                Lambda Invocation Models

                 +--------------------+
                 |     AWS Lambda     |
                 +--------------------+
                           ▲
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        │                  │                  │
Synchronous         Asynchronous        Poll-Based
(Request/Response)  (Event Queue)      (Event Source Mapping)
```

Each model behaves differently.

---

# 1. Synchronous Invocation

In synchronous invocation, the caller waits until Lambda finishes execution.

```text
Client

   │

Invoke Lambda

   │

Lambda Executes

   │

Return Response

   │

Client Continues
```

The caller blocks until the function returns.

---

## Characteristics

- Immediate execution
- Caller waits
- Immediate response
- Suitable for APIs
- Errors returned directly

---

## Common AWS Services

- API Gateway
- ALB
- Function URL
- AWS SDK
- AWS CLI

---

## Example

```text
Browser

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

Response
```

---

## Python Example

```python
def handler(event, context):

    return {
        "statusCode": 200,
        "body": "Hello World"
    }
```

The caller immediately receives:

```json
{
  "statusCode":200,
  "body":"Hello World"
}
```

---

## Error Handling

If Lambda fails:

```text
API Gateway

↓

Lambda

↓

Exception

↓

500 Returned
```

No automatic retries occur.

The client must retry if necessary.

---

## Advantages

- Simple request-response flow
- Immediate feedback
- Easy debugging
- Good for REST APIs

---

## Disadvantages

- Client waits
- User experiences latency
- Timeout affects user
- Not suitable for long-running work

---

# Production Example

```text
Customer Login

↓

API Gateway

↓

Lambda

↓

Validate Credentials

↓

Return JWT
```

The client requires an immediate response.

---

# 2. Asynchronous Invocation

With asynchronous invocation, Lambda immediately accepts the event and places it into an internal AWS queue.

The caller receives success before the function executes.

```text
Application

      │

Invoke Lambda

      │

Event Accepted

      │

200 OK Returned

      │

Internal Queue

      │

Lambda Executes Later
```

The caller never waits.

---

# Internal Workflow

```text
Event

↓

Lambda Service

↓

Internal Queue

↓

Worker

↓

Lambda Function
```

AWS manages the queue automatically.

---

# Characteristics

- Caller returns immediately
- Event stored internally
- Automatic retries
- Better fault tolerance
- Good for background processing

---

# Common AWS Services

- S3
- SNS
- EventBridge
- CloudWatch Events
- CodeCommit
- CodePipeline

---

# Production Example

```text
Image Uploaded

↓

S3

↓

Lambda Queue

↓

Resize Image

↓

Store Thumbnail
```

The user doesn't wait for image processing.

---

# Retry Behavior

If Lambda fails:

```text
Event

↓

Queue

↓

Attempt 1

↓

Failed

↓

Retry

↓

Attempt 2

↓

Retry

↓

Attempt 3

↓

DLQ / Destination
```

AWS retries asynchronous invocations automatically.

---

# Dead Letter Queue (DLQ)

If retries fail:

```text
Lambda

↓

Failure

↓

SNS

or

SQS
```

This prevents event loss.

---

# Lambda Destinations

Instead of DLQs, Lambda can send results to destinations.

Successful execution:

```text
Lambda

↓

Success Destination
```

Failed execution:

```text
Lambda

↓

Failure Destination
```

Destinations support:

- EventBridge
- Lambda
- SNS
- SQS

---

# Advantages

- Caller doesn't wait
- Automatic retries
- Reliable
- High throughput
- Event-driven architecture

---

# Disadvantages

- Eventual consistency
- Delayed processing
- Harder debugging
- Duplicate events possible

---

# Production Example

```text
Customer Places Order

↓

Order Service

↓

EventBridge

↓

Lambda

↓

Send Email

↓

Update Analytics

↓

Notify Warehouse
```

Each task happens independently.

---

# 3. Poll-Based Invocation (Event Source Mapping)

This is often misunderstood.

Lambda is **not directly invoked** by services like SQS or Kinesis.

Instead:

AWS creates an **Event Source Mapping**.

The mapping continuously polls the source.

```text
SQS Queue

↓

Event Source Mapping

↓

Lambda
```

---

# Supported Poll-Based Sources

- SQS
- SQS FIFO
- DynamoDB Streams
- Kinesis Data Streams
- Amazon MSK
- Self-managed Kafka
- Amazon MQ
- DocumentDB Change Streams

---

# Architecture

```text
Messages

↓

Queue

↓

Lambda Poller

↓

Batch

↓

Lambda
```

Notice:

Lambda itself never polls.

AWS pollers do.

---

# Event Source Mapping

An Event Source Mapping is an AWS-managed resource.

Responsibilities:

- Poll queue
- Read stream
- Batch records
- Invoke Lambda
- Manage retries
- Handle failures

---

# Batch Processing

Instead of invoking Lambda once per message:

```text
100 Messages

↓

One Batch

↓

Lambda
```

Much cheaper.

Example:

```
Batch Size = 10

100 Messages

↓

10 Lambda Invocations
```

---

# Batch Window

Lambda can wait before invoking.

```text
Message

↓

Wait

↓

More Messages Arrive

↓

Batch Full

↓

Invoke
```

This improves efficiency.

---

# Error Handling

Suppose:

```text
Batch

↓

10 Messages

↓

Message 7 Fails
```

Without partial batch response:

Entire batch retries.

```text
Retry

↓

Messages 1-10
```

Duplicates occur.

---

# Partial Batch Response

Modern Lambda supports partial batch response.

```text
Batch

↓

Messages 1-9 Success

↓

Message 10 Failed

↓

Retry Only Message 10
```

This greatly improves efficiency.

---

# Stream Processing

For Kinesis and DynamoDB Streams:

```text
Shard

↓

Records

↓

Lambda

↓

Checkpoint
```

Records remain in the stream.

Lambda simply tracks checkpoints.

---

# Ordering

Kinesis:

Ordering maintained **per shard**.

SQS FIFO:

Ordering maintained **per message group**.

Standard SQS:

No ordering guarantee.

---

# Retry Behavior

## SQS

Failed messages become visible again after the visibility timeout expires.

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

---

## Kinesis

Entire batch retries until:

- Success
- Record expires

---

## DynamoDB Streams

Same behavior as Kinesis.

---

# Comparison

| Feature | Synchronous | Asynchronous | Poll-Based |
|----------|-------------|--------------|------------|
| Caller Waits | Yes | No | No |
| Immediate Response | Yes | Yes | No Client |
| Automatic Retry | No | Yes | Yes |
| Internal Queue | No | Yes | Source Queue |
| Batch Processing | No | No | Yes |
| Event Source Mapping | No | No | Yes |
| Ordering Support | Depends | No | Depends on Source |

---

# Which Invocation Model Should You Choose?

| Use Case | Best Choice |
|-----------|-------------|
| REST API | Synchronous |
| Login | Synchronous |
| Payment Validation | Synchronous |
| Email Sending | Asynchronous |
| Thumbnail Generation | Asynchronous |
| Analytics | Asynchronous |
| Queue Workers | Poll-Based |
| Log Processing | Poll-Based |
| Stream Processing | Poll-Based |
| CDC Pipelines | Poll-Based |

---

# Common Mistakes

## Waiting for Background Tasks

Bad:

```text
User

↓

Lambda

↓

Send Email

↓

Generate PDF

↓

Resize Images

↓

Return
```

The user waits unnecessarily.

---

Better:

```text
User

↓

Lambda

↓

EventBridge

↓

Background Workers
```

---

## Using Synchronous for Large Processing

Avoid processing:

- Videos
- Reports
- Machine learning
- Large imports

Synchronously.

---

## Ignoring Duplicate Events

Asynchronous and poll-based invocations can deliver duplicate events.

Always design Lambda functions to be **idempotent**.

---

# Senior Backend Engineering Perspective

A senior backend engineer selects the invocation model based on business requirements rather than convenience:

- **Synchronous** for user-facing APIs requiring immediate responses.
- **Asynchronous** for event-driven workflows where the caller should not block.
- **Poll-Based** for high-throughput processing from queues and streams, leveraging batching and controlled concurrency.

Understanding retry behavior, ordering guarantees, and failure handling for each model is critical to building resilient serverless systems.

---

# Interview Questions

### Beginner

- What are the different Lambda invocation models?
- What is synchronous invocation?
- Which AWS services invoke Lambda asynchronously?

### Intermediate

- What is Event Source Mapping?
- How does Lambda process SQS messages?
- How does Lambda process DynamoDB Streams?
- What is batch processing?

### Senior

- How would you design an idempotent SQS consumer?
- Why doesn't Lambda poll SQS directly?
- How does partial batch response reduce duplicate processing?
- When would you choose EventBridge over SQS?
- How would you process millions of events with Lambda while preserving ordering?

---

# Key Takeaways

- Lambda supports three invocation models: synchronous, asynchronous, and poll-based.
- Synchronous invocations are best for request-response APIs.
- Asynchronous invocations use an internal AWS queue with automatic retries.
- Poll-based invocations rely on Event Source Mappings to read from queues and streams.
- Choosing the correct invocation model is fundamental to designing scalable, fault-tolerant, and cost-effective serverless applications.