# Versions, Aliases & Event Sources

> Learn how AWS Lambda Versions, Aliases, and Event Sources enable safe deployments, version management, traffic shifting, and event-driven architectures. This chapter covers publishing versions, creating aliases, configuring event source mappings, asynchronous invocations, and production deployment strategies using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Lambda Versions
- Create and manage Aliases
- Publish immutable function versions
- Configure Event Source Mappings
- Understand synchronous and asynchronous invocation
- Configure retry behavior
- Build production deployment strategies

---

# Why Versions Matter

Every Lambda function begins with a special version.

```text
$LATEST
```

The `$LATEST` version is mutable.

Whenever code is updated:

```text
Update Code

↓

$LATEST Changes
```

Production systems should avoid invoking `$LATEST` directly.

---

# Lambda Version Lifecycle

```text
Develop

↓

$LATEST

↓

Publish Version

↓

Version 1

↓

Version 2

↓

Version 3
```

Each published version is immutable.

---

# Publish a Version

```bash
aws lambda publish-version \
--function-name payment-api
```

Example response:

```text
Version: 3
```

The published version cannot be modified.

---

# List Versions

```bash
aws lambda list-versions-by-function \
--function-name payment-api
```

Returns:

- Version Number
- Description
- Last Modified

---

# Why Use Versions?

Versions provide:

- Stable deployments
- Rollback capability
- Safe production releases
- Auditability

Without versions:

```text
Production

↓

$LATEST

↓

Accidental Deployment
```

With versions:

```text
Production

↓

Version 5

↓

Safe Deployment
```

---

# Lambda Aliases

Aliases provide friendly names for versions.

Instead of:

```text
Version 12
```

Use:

```text
Production

Staging

Development

Testing
```

Aliases simplify deployments.

---

# Alias Architecture

```text
Lambda

│

├── Version 1

├── Version 2

├── Version 3

│

└── Production Alias

        │

        ▼

    Version 3
```

---

# Create an Alias

```bash
aws lambda create-alias \
--function-name payment-api \
--name Production \
--function-version 3
```

---

# List Aliases

```bash
aws lambda list-aliases \
--function-name payment-api
```

---

# Update an Alias

Deploy a new version.

```bash
aws lambda update-alias \
--function-name payment-api \
--name Production \
--function-version 4
```

Traffic immediately moves to Version 4.

---

# Delete an Alias

```bash
aws lambda delete-alias \
--function-name payment-api \
--name Production
```

---

# Blue/Green Deployment

Instead of replacing production directly:

```text
Version 3

↓

Version 4

↓

Switch Alias

↓

Production
```

This minimizes deployment risk.

---

# Canary Deployment

Traffic can be split.

Example:

```text
90%

↓

Version 3

10%

↓

Version 4
```

Monitor the new version before full rollout.

---

# Event Sources

Lambda executes when triggered by an event.

Common event sources include:

- API Gateway
- S3
- SNS
- SQS
- DynamoDB Streams
- Kinesis
- EventBridge
- CloudWatch Logs

---

# Event Source Architecture

```text
AWS Service

↓

Event

↓

Lambda

↓

Business Logic
```

---

# Event Source Mapping

Some services require an Event Source Mapping.

Examples:

- SQS
- DynamoDB Streams
- Kinesis
- Amazon MQ
- MSK

---

# Create Event Source Mapping

Example:

```bash
aws lambda create-event-source-mapping \
--function-name payment-api \
--event-source-arn arn:aws:sqs:ap-south-1:123456789012:orders
```

---

# List Event Source Mappings

```bash
aws lambda list-event-source-mappings
```

---

# Delete Event Source Mapping

```bash
aws lambda delete-event-source-mapping \
--uuid uuid-value
```

---

# Invocation Types

Lambda supports three invocation models.

```text
Synchronous

Asynchronous

Poll-based
```

---

# Synchronous Invocation

Example:

```text
Client

↓

API Gateway

↓

Lambda

↓

Response
```

The caller waits for the response.

---

# Asynchronous Invocation

Example:

```text
Application

↓

SNS

↓

Lambda

↓

Background Processing
```

The caller does not wait.

---

# Poll-based Invocation

Example:

```text
SQS Queue

↓

Lambda Poller

↓

Lambda
```

Lambda automatically polls the queue.

---

# Retry Behavior

Asynchronous invocations retry automatically.

Typical workflow:

```text
Invoke

↓

Failure

↓

Retry

↓

Failure

↓

Dead Letter Queue
```

---

# Dead Letter Queues (DLQ)

Failed events can be sent to:

- Amazon SQS
- Amazon SNS

This prevents event loss.

---

# Event Filtering

Event Source Mappings support filtering.

```text
Incoming Events

↓

Filter

↓

Relevant Events

↓

Lambda
```

Filtering reduces unnecessary executions.

---

# Concurrency and Event Sources

Each event source can invoke multiple Lambda instances simultaneously.

```text
100 Queue Messages

↓

100 Lambda Invocations
```

Concurrency limits help control scaling.

---

# Common Errors

## ResourceConflictException

Occurs when:

- Alias already exists
- Version being updated
- Mapping already exists

---

## InvalidParameterValueException

Possible causes:

- Invalid ARN
- Invalid version
- Invalid alias

---

## Event Source Disabled

Verify:

- Event Source Mapping
- IAM permissions
- Trigger configuration

---

# Production Best Practices

- Never invoke `$LATEST` in production.
- Always deploy immutable versions.
- Use aliases for environments.
- Perform canary or blue/green deployments.
- Configure Dead Letter Queues.
- Enable event filtering.
- Monitor event source mappings.
- Test rollback procedures.

---

# Real-World Workflow

```text
Developer

↓

Deploy Code

↓

Publish Version

↓

Update Alias

↓

Production Traffic

↓

Monitor CloudWatch

↓

Rollback if Needed
```

---

# Architecture Note

```text
Client
      │
      ▼
API Gateway / SQS / EventBridge
      │
      ▼
Lambda Alias
      │
      ▼
Published Version
      │
      ▼
Business Logic
```

Aliases provide a stable endpoint while allowing the underlying version to change safely.

---

# Interview Note

### Question

**What is the difference between a Lambda Version and an Alias?**

### Answer

A **Version** is an immutable snapshot of a Lambda function's code and configuration at a specific point in time. Once published, it cannot be modified. An **Alias** is a named pointer to a specific version, such as `Production` or `Staging`. Aliases simplify deployments, support blue/green and canary releases, and allow applications to reference stable names instead of version numbers.

---

# Key Takeaways

- `$LATEST` is mutable and should not be used for production traffic.
- Published Versions are immutable snapshots.
- Aliases provide stable names for deployed versions.
- Event Source Mappings connect Lambda to services like SQS and DynamoDB Streams.
- Lambda supports synchronous, asynchronous, and poll-based invocation models.
- Dead Letter Queues help prevent event loss.
- Canary and blue/green deployments improve release safety.