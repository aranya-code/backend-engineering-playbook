# 01 - DynamoDB + AWS Lambda

## Overview

Amazon DynamoDB and AWS Lambda are one of the most common serverless combinations in AWS. Together they enable highly scalable, event-driven applications without provisioning or managing servers.

DynamoDB acts as the highly available NoSQL database, while Lambda executes business logic in response to:

- API requests
- DynamoDB Stream events
- Scheduled events
- SQS messages
- EventBridge events
- SNS notifications

This integration is the foundation for many modern serverless architectures.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why Lambda and DynamoDB work well together
- Common integration patterns
- Request-response architecture
- Event-driven processing
- DynamoDB Streams integration
- Error handling
- Performance optimization
- Security considerations
- Production best practices
- Interview questions

---

# Why Use Lambda with DynamoDB?

Lambda provides compute.

DynamoDB provides storage.

```text
             Client

                │

                ▼

          API Gateway

                │

                ▼

           AWS Lambda

                │

                ▼

           DynamoDB Table
```

Benefits include:

- No server management
- Automatic scaling
- Pay-per-use pricing
- High availability
- Loose coupling

---

# Common Integration Patterns

Lambda and DynamoDB are commonly used for:

- REST APIs
- CRUD applications
- Event processing
- User registration
- Order management
- Inventory updates
- Background processing
- Audit logging
- Notifications

---

# Pattern 1 — REST API

The most common architecture.

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

Workflow:

```text
HTTP Request

↓

Lambda

↓

GetItem()

↓

Return JSON
```

---

# CRUD Operations

Lambda can perform:

```text
PutItem

GetItem

UpdateItem

DeleteItem

Query

BatchWriteItem

BatchGetItem
```

using the AWS SDK (Boto3).

---

# Example Request Flow

Create Order

```text
Client

↓

POST /orders

↓

Lambda

↓

Validation

↓

PutItem()

↓

Return 201
```

---

# Read Request

```text
Client

↓

GET /orders/123

↓

Lambda

↓

GetItem()

↓

JSON Response
```

---

# Pattern 2 — Event Processing

Instead of being called by an API, Lambda can process DynamoDB Streams.

```text
Application

↓

PutItem()

↓

DynamoDB

↓

Streams

↓

Lambda
```

This enables asynchronous workflows.

---

# Example

Customer places an order.

```text
Order Saved

↓

Stream Event

↓

Lambda

↓

Send Email

↓

Update Analytics

↓

Notify Warehouse
```

The original application remains fast because downstream work is asynchronous.

---

# Pattern 3 — CQRS

Separate writes from reads.

```text
Application

↓

Write

↓

DynamoDB

↓

Streams

↓

Lambda

↓

Search Index
```

Lambda updates the read model automatically.

---

# Pattern 4 — Fan-Out Processing

One database event can trigger multiple systems.

```text
Order Created

↓

Lambda

├── Email

├── Analytics

├── Billing

└── Inventory
```

This is a common event-driven microservices pattern.

---

# Lambda Execution Lifecycle

```text
Invoke

↓

Initialize Runtime

↓

Execute Function

↓

Access DynamoDB

↓

Return Response
```

For warm invocations, the initialization step is skipped.

---

# Boto3 Integration

Typical operations include:

```python
table.get_item()

table.put_item()

table.update_item()

table.delete_item()

table.query()

table.scan()
```

Avoid using `Scan()` unless absolutely necessary.

---

# Connection Reuse

Initialize the DynamoDB resource outside the Lambda handler.

```text
Cold Start

↓

Create DynamoDB Client

↓

Reuse Across Invocations
```

Benefits:

- Lower latency
- Reduced initialization time
- Better performance

---

# Error Handling

Common DynamoDB exceptions:

- ConditionalCheckFailedException
- ProvisionedThroughputExceededException
- ResourceNotFoundException
- ValidationException
- AccessDeniedException

Lambda should:

- Log the error
- Retry when appropriate
- Return meaningful responses

---

# Retry Strategy

Example:

```text
Throttle

↓

Retry

↓

Exponential Backoff

↓

Success
```

Avoid immediate retries.

---

# IAM Permissions

Grant only the required permissions.

Example:

```text
Lambda

↓

IAM Role

↓

DynamoDB

↓

GetItem

PutItem

UpdateItem
```

Avoid:

```text
dynamodb:*
```

Follow the principle of least privilege.

---

# Monitoring

Monitor both services.

Lambda:

- Duration
- Errors
- Concurrent Executions
- Throttles

DynamoDB:

- RCUs
- WCUs
- Latency
- Throttling

---

# Performance Optimization

## Reuse Clients

Good:

```python
dynamodb = boto3.resource("dynamodb")
```

outside the handler.

---

## Avoid Scan

Poor:

```text
Lambda

↓

Scan

↓

Entire Table
```

Better:

```text
Lambda

↓

Query

↓

Partition Key
```

---

## Batch Operations

Instead of:

```text
100 GetItem()
```

Use:

```text
BatchGetItem()
```

Benefits:

- Lower latency
- Fewer API calls

---

## Minimize Payload Size

Retrieve only required attributes.

```text
Projection Expression

↓

Smaller Response

↓

Lower Latency
```

---

# Security Best Practices

- Use IAM roles.
- Encrypt tables using AWS KMS.
- Enable CloudTrail.
- Use VPC endpoints if required.
- Never hardcode credentials.
- Validate all API input.
- Enable least privilege.

---

# Production Architecture

```text
                   Users

                      │

                API Gateway

                      │

                      ▼

                 AWS Lambda

          ┌───────────┼────────────┐

          ▼           ▼            ▼

     DynamoDB      CloudWatch    X-Ray

          │

          ▼

   DynamoDB Streams

          │

          ▼

     Background Lambda

          │

     ┌────┼────┐

     ▼    ▼    ▼

 Email Analytics Inventory
```

---

# Production Considerations

Large production systems often include:

- API Gateway
- Lambda
- DynamoDB
- CloudWatch
- AWS X-Ray
- EventBridge
- SQS
- SNS
- Secrets Manager

This provides observability, resilience, and scalability.

---

# Best Practices

- Initialize Boto3 clients outside the handler.
- Prefer Query over Scan.
- Use Projection Expressions.
- Handle retries with exponential backoff.
- Keep Lambda functions stateless.
- Grant least-privilege IAM permissions.
- Use Streams for asynchronous processing.
- Monitor latency and throttling.
- Keep functions small and focused.

---

# Common Mistakes

## Creating Clients Inside the Handler

Creates unnecessary overhead on every invocation.

---

## Using Scan for Every Request

This increases latency and RCU consumption.

---

## Long-Running Lambda Functions

Move expensive processing to asynchronous workflows.

---

## Ignoring Idempotency

Lambda may retry failed invocations.

Functions should safely handle duplicate events.

---

## Overly Broad IAM Policies

Avoid granting unrestricted DynamoDB permissions.

---

# Interview Notes

A common interview question is:

> **Why are DynamoDB and Lambda commonly used together?**

Lambda provides serverless compute while DynamoDB provides scalable NoSQL storage. Together they create highly scalable, pay-per-use applications without server management.

---

Another common question is:

> **How should a Lambda function access DynamoDB efficiently?**

Initialize the DynamoDB client outside the handler, use Query instead of Scan, batch requests where appropriate, and retrieve only required attributes.

---

Another common question is:

> **How do you process DynamoDB changes asynchronously?**

Enable DynamoDB Streams and configure a Lambda function as the stream consumer. The Lambda function processes item-level changes as they occur.

---

Another common question is:

> **How do you secure Lambda access to DynamoDB?**

Assign an IAM execution role with only the required DynamoDB permissions, enable encryption, and avoid embedding credentials in code.

---

# Key Takeaways

- Lambda and DynamoDB form one of AWS's most widely used serverless architectures.
- Lambda can be invoked synchronously through APIs or asynchronously through DynamoDB Streams.
- Initialize SDK clients outside the handler for better performance.
- Prefer Query over Scan and use batch operations when appropriate.
- Implement retries, idempotency, and least-privilege IAM policies for production-grade applications.
- Combining Lambda, DynamoDB, Streams, and CloudWatch provides a scalable, event-driven backend architecture.