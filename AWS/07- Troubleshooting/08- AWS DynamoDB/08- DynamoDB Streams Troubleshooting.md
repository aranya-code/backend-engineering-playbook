# 07 - DynamoDB Streams Troubleshooting

## Overview

Amazon DynamoDB Streams capture item-level changes in a DynamoDB table and make them available for downstream consumers.

Streams are widely used in production for:

- Event-driven architectures
- AWS Lambda triggers
- Audit logging
- Search indexing
- Cache invalidation
- Analytics pipelines
- Cross-region replication

When Streams stop working correctly, downstream systems may become inconsistent even though DynamoDB itself continues operating normally.

This chapter explains common DynamoDB Streams issues, how to troubleshoot them, and production best practices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How DynamoDB Streams work
- Common stream failures
- Lambda integration issues
- Missing events
- Duplicate event handling
- Stream lag
- Monitoring
- Production troubleshooting

---

# DynamoDB Streams Architecture

```text
Application

      │

      ▼

Amazon DynamoDB

      │

      ▼

DynamoDB Stream

      │

      ▼

Lambda

      │

      ▼

Other AWS Services
```

---

# Stream Lifecycle

```text
Item Created

↓

Item Updated

↓

Item Deleted

↓

Record Written

↓

Consumer Reads Record
```

---

# Common Problems

Production issues usually involve:

- Stream disabled
- Lambda not triggering
- Event processing failures
- Duplicate processing
- Consumer lag
- IAM permission failures
- Batch failures
- Iterator expiration

---

# Problem 1 — Stream Not Enabled

Symptoms:

- No events
- Lambda never executes

Check table configuration:

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Verify:

```text
StreamSpecification

↓

Enabled = true
```

---

# Stream View Types

Supported options:

```text
KEYS_ONLY

NEW_IMAGE

OLD_IMAGE

NEW_AND_OLD_IMAGES
```

Incorrect selection often causes missing attributes.

---

# Example

Application expects:

```text
Customer Name
```

Stream:

```text
KEYS_ONLY
```

Result:

```text
Attribute Missing
```

---

# Problem 2 — Lambda Never Executes

Architecture:

```text
DynamoDB

↓

Stream

↓

Lambda
```

Possible causes:

- Event source mapping disabled
- Lambda permission issues
- Stream disabled
- Wrong stream ARN
- Deleted trigger

---

# Verify Event Source Mapping

CLI:

```bash
aws lambda list-event-source-mappings
```

Check:

- State
- UUID
- LastProcessingResult
- Function ARN

---

# Problem 3 — Lambda Errors

Common symptoms:

```text
Retries

↓

Errors

↓

Backlog
```

Check:

- CloudWatch Logs
- Lambda metrics
- Exception stack traces

---

# Debugging Workflow

```text
No Processing

↓

Stream Enabled?

↓

Lambda Trigger?

↓

CloudWatch Logs?

↓

IAM?

↓

Root Cause
```

---

# Problem 4 — Duplicate Events

Streams provide:

```text
At-Least-Once Delivery
```

Meaning:

```text
One Event

↓

May Be Delivered

↓

More Than Once
```

Applications must be idempotent.

---

# Duplicate Processing Example

Bad:

```text
Process Payment

↓

Retry

↓

Charge Again
```

Better:

```text
Check Request ID

↓

Already Processed?

↓

Ignore Duplicate
```

---

# Problem 5 — Stream Lag

Symptoms:

```text
Database Updated

↓

Consumer Executes

↓

Several Minutes Later
```

Possible causes:

- Lambda throttling
- Slow processing
- Batch failures
- Downstream dependencies

---

# Monitoring Lag

Monitor:

- IteratorAge
- Lambda Duration
- Lambda Errors
- Concurrent Executions

High IteratorAge indicates consumers are falling behind.

---

# Problem 6 — Batch Failures

Lambda receives records in batches.

```text
Batch

↓

Record 1

Record 2

Record 3
```

If processing fails:

```text
Entire Batch

↓

Retry
```

Poor error handling can repeatedly process successful records.

---

# Partial Batch Response

Modern Lambda integrations support reporting only failed records.

Benefits:

- Reduced retries
- Faster recovery
- Lower cost

Use partial batch responses whenever appropriate.

---

# Problem 7 — IAM Issues

Lambda execution role requires permissions.

Typical permissions:

```text
dynamodb:GetRecords

dynamodb:GetShardIterator

dynamodb:DescribeStream

dynamodb:ListStreams
```

Missing permissions prevent stream consumption.

---

# Problem 8 — Stream Retention

DynamoDB Streams retain records for:

```text
24 Hours
```

If consumers fall behind longer than the retention period:

```text
Records Lost
```

---

# Iterator Expired

Example:

```text
ExpiredIteratorException
```

Occurs when:

- Consumer waits too long
- Iterator expires
- New iterator required

Normally handled automatically by AWS SDKs and Lambda integrations.

---

# CloudWatch Investigation

Useful metrics:

```text
IteratorAge

Errors

Invocations

Duration

Throttles
```

Monitor these continuously.

---

# Production Example

Order created.

```text
Order Service

↓

DynamoDB

↓

Stream

↓

Lambda

↓

Notification Service
```

If Lambda fails:

```text
Customer

↓

Never Receives Email
```

Order still exists.

---

# Another Production Example

Inventory updates.

```text
Inventory Table

↓

Stream

↓

Search Index
```

If stream processing stops:

```text
Inventory Updated

↓

Search Results

↓

Outdated
```

---

# Common Investigation Checklist

```text
Event Missing

↓

Table Streams Enabled?

↓

Correct View Type?

↓

Lambda Trigger?

↓

CloudWatch Logs?

↓

IAM Permissions?

↓

IteratorAge?

↓

Root Cause
```

---

# Performance Considerations

- Keep Lambda execution time short.
- Process batches efficiently.
- Use partial batch responses.
- Avoid synchronous downstream calls where possible.
- Design consumers to be idempotent.
- Monitor IteratorAge continuously.

---

# Best Practices

- Enable Streams only when needed.
- Choose the correct Stream View Type.
- Build idempotent consumers.
- Enable CloudWatch alarms.
- Monitor Lambda concurrency.
- Keep event processing lightweight.
- Handle duplicate events gracefully.

---

# Common Mistakes

## Assuming Exactly-Once Delivery

DynamoDB Streams provide **at-least-once** delivery.

Applications must tolerate duplicate events.

---

## Long-Running Lambda Functions

Slow processing increases:

- IteratorAge
- Retry frequency
- Operational costs

---

## Ignoring Failed Batches

Repeated batch failures can create processing backlogs.

---

## Using the Wrong Stream View

Choosing `KEYS_ONLY` when the application requires item attributes leads to incomplete processing.

---

## Ignoring CloudWatch Metrics

IteratorAge is one of the earliest indicators of stream processing problems.

---

# Interview Notes

### What are DynamoDB Streams?

A change data capture (CDC) feature that records item-level modifications and enables downstream event processing.

---

### How long are stream records retained?

Approximately **24 hours**.

---

### Why might Lambda not receive stream events?

Common causes include:

- Streams disabled
- Event source mapping disabled
- IAM permission issues
- Incorrect Stream ARN
- Lambda execution failures

---

### Why can duplicate events occur?

DynamoDB Streams guarantee **at-least-once delivery**, so consumers must be idempotent.

---

### Which CloudWatch metric is most useful for identifying stream lag?

`IteratorAge`

It measures how far behind the stream consumer is in processing records.

---

# Key Takeaways

- DynamoDB Streams enable event-driven architectures by capturing item-level changes.
- Most production issues involve disabled streams, Lambda integration problems, IAM permissions, or slow consumers.
- Applications should always be designed for **at-least-once delivery** and implement idempotent processing.
- CloudWatch metrics such as `IteratorAge`, Lambda errors, and invocation metrics are critical for monitoring stream health.
- Senior backend engineers treat Streams as an asynchronous integration layer and build resilient consumers that can recover gracefully from failures.