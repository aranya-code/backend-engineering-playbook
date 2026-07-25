# 10 - Error Handling & Retries

## Overview

Distributed systems are inherently unreliable.

When working with Amazon DynamoDB, failures can occur due to:

- Network interruptions
- Service throttling
- Temporary AWS outages
- Invalid requests
- Missing permissions
- Conditional write failures
- Transaction conflicts

A production-ready application must assume that failures **will happen** and be designed to recover gracefully.

This chapter explores how to build resilient DynamoDB applications using proper exception handling, retries, exponential backoff, idempotency, and circuit breaker patterns.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Common DynamoDB exceptions
- ClientError handling
- Retry strategies
- Exponential Backoff
- Jitter
- Retryable vs Non-Retryable errors
- Idempotent operations
- Circuit Breakers
- Production logging
- Best practices
- Interview questions

---

# Why Error Handling Matters

Without proper handling:

```text
Client

↓

Network Timeout

↓

Application Crash
```

With proper handling:

```text
Client

↓

Network Timeout

↓

Retry

↓

Success
```

Resilient applications recover automatically whenever possible.

---

# Categories of Errors

Errors generally fall into two categories.

## Retryable Errors

Temporary failures.

Examples:

- Throttling
- Network timeout
- Internal server error
- Service unavailable

Usually safe to retry.

---

## Non-Retryable Errors

Permanent failures.

Examples:

- Invalid request
- Validation error
- Missing permissions
- Resource not found

Retrying will not solve these problems.

---

# Common DynamoDB Exceptions

| Exception | Retry? | Cause |
|-----------|---------|------|
| ProvisionedThroughputExceededException | ✅ | Throttling |
| ThrottlingException | ✅ | Rate exceeded |
| InternalServerError | ✅ | AWS internal failure |
| RequestLimitExceeded | ✅ | Too many requests |
| ConditionalCheckFailedException | ❌ | Business rule failed |
| ValidationException | ❌ | Invalid request |
| ResourceNotFoundException | ❌ | Missing table |
| AccessDeniedException | ❌ | IAM permissions |
| TransactionCanceledException | Depends | Transaction failure |

---

# Catching Exceptions

Most DynamoDB exceptions are wrapped inside:

```python
ClientError
```

Example:

```python
from botocore.exceptions import ClientError

try:

    table.put_item(Item=item)

except ClientError as error:

    print(error.response["Error"]["Code"])
```

Always inspect the AWS error code.

---

# Reading the Error Code

Example:

```python
try:

    table.put_item(Item=item)

except ClientError as error:

    code = error.response["Error"]["Code"]

    if code == "ConditionalCheckFailedException":
        print("Duplicate order")
```

Never compare against exception messages.

---

# Retryable Errors

Typical retryable failures:

```text
Request

↓

Network Timeout

↓

Retry

↓

Success
```

Examples:

- InternalServerError
- ThrottlingException
- RequestTimeout

---

# Non-Retryable Errors

Example:

```text
Request

↓

ValidationException

↓

Fix Code
```

Retrying wastes resources.

---

# Exponential Backoff

Never retry immediately.

Poor:

```text
Retry

↓

Retry

↓

Retry
```

Better:

```text
1 Second

↓

2 Seconds

↓

4 Seconds

↓

8 Seconds

↓

16 Seconds
```

This reduces pressure on DynamoDB.

---

# Exponential Backoff Example

```python
import time

delay = 1

for _ in range(5):

    try:

        table.put_item(Item=item)

        break

    except ClientError:

        time.sleep(delay)

        delay *= 2
```

Simple but effective.

---

# Why Jitter Matters

Suppose 500 Lambda functions retry simultaneously.

Without jitter:

```text
500 Clients

↓

Retry Same Time

↓

Another Failure
```

---

With jitter:

```text
500 Clients

↓

Random Delay

↓

Retries Spread Out

↓

Higher Success Rate
```

AWS strongly recommends adding jitter to retry algorithms.

---

# Retry with Jitter

Example:

```python
import random
import time

delay = 1

for _ in range(5):

    try:

        table.put_item(Item=item)

        break

    except ClientError:

        time.sleep(
            delay + random.random()
        )

        delay *= 2
```

---

# SDK Automatic Retries

Boto3 automatically retries many transient failures.

Typical retryable conditions include:

- Throttling
- Internal server errors
- Connection failures

Developers should understand what the SDK retries automatically and where application-level retries are still appropriate, especially for business workflows.

---

# Configuring Retry Behavior

Boto3 allows retry configuration through `botocore.config.Config`.

Example:

```python
from botocore.config import Config
import boto3

config = Config(
    retries={
        "max_attempts": 10,
        "mode": "standard"
    }
)

dynamodb = boto3.resource(
    "dynamodb",
    config=config
)
```

Retry modes include:

- legacy
- standard
- adaptive

Production workloads generally use **standard** or **adaptive** mode.

---

# Handling Conditional Failures

Example:

```text
Duplicate Order

↓

ConditionalCheckFailedException

↓

Return HTTP 409
```

This is **not** a server failure.

It represents a business rule violation.

---

# Transaction Failures

Example:

```text
Transaction

↓

Inventory Changed

↓

TransactionCanceledException
```

Retry only if appropriate.

Investigate the cancellation reason before retrying.

---

# Idempotent Operations

Suppose a client times out.

```text
Client

↓

Timeout

↓

Retry

↓

Duplicate Order ❌
```

Better:

```text
Client

↓

Idempotency Key

↓

Retry

↓

Single Order ✅
```

Always combine retries with idempotency for write operations.

---

# Circuit Breaker Pattern

Repeated failures shouldn't overwhelm DynamoDB.

```text
Application

↓

Failures

↓

Circuit Opens

↓

Reject Requests

↓

Recovery

↓

Circuit Closes
```

Circuit breakers prevent cascading failures across distributed systems.

---

# Timeout Handling

Avoid waiting indefinitely.

Example:

```text
Request

↓

Timeout

↓

Retry

↓

Fail Gracefully
```

Always define reasonable client-side timeouts.

---

# Logging Errors

Every production application should log:

- Error code
- Request ID
- Table name
- Retry count
- Latency
- Operation type

Avoid logging:

- AWS credentials
- Personal data
- Secrets

---

# Monitoring

CloudWatch metrics to monitor:

- ThrottledRequests
- SuccessfulRequestLatency
- SystemErrors
- UserErrors
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits

Sudden increases often indicate scaling issues or inefficient access patterns.

---

# Repository Pattern

```python
class OrderRepository:

    def save(self, order):

        try:

            self.table.put_item(Item=order)

        except ClientError as error:

            raise
```

The repository should encapsulate DynamoDB-specific exceptions and expose meaningful domain-level errors to the service layer.

---

# Production Architecture

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

              FastAPI API

                   │

                   ▼

            Service Layer

                   │

                   ▼

         Repository Layer

                   │

                   ▼

      Retry + Backoff + Logging

                   │

                   ▼

          Amazon DynamoDB
```

---

# Retry Decision Flow

```text
Exception

↓

Retryable?

│

├── Yes

│      ↓

│ Exponential Backoff

│      ↓

│ Retry

│

└── No

       ↓

Return Error
```

---

# Performance Considerations

Retries improve reliability but also:

- Increase latency
- Consume additional capacity
- Increase network traffic

Retry only transient failures.

Never retry indefinitely.

---

# Security Best Practices

- Never expose AWS error messages directly to clients.
- Sanitize logs before writing them.
- Use least-privilege IAM policies.
- Log security-related failures separately.
- Protect retry endpoints from abuse.

---

# Best Practices

- Catch `ClientError` instead of generic exceptions.
- Retry only transient failures.
- Use exponential backoff with jitter.
- Configure SDK retry behavior appropriately.
- Combine retries with idempotency.
- Log request IDs for debugging.
- Monitor CloudWatch metrics continuously.

---

# Common Mistakes

## Retrying Every Exception

Poor:

```text
Every Failure

↓

Retry
```

Better:

```text
Retryable?

↓

Yes

↓

Retry
```

---

## Immediate Retries

Poor:

```text
Retry

↓

Retry

↓

Retry
```

Better:

```text
Retry

↓

Backoff

↓

Retry
```

---

## Ignoring Conditional Failures

A conditional failure usually means the business rule prevented an invalid operation.

Treat it differently from infrastructure failures.

---

## Infinite Retry Loops

Never retry forever.

Always define:

- Maximum attempts
- Maximum timeout
- Fallback behavior

---

## Returning AWS Errors Directly

Avoid exposing internal DynamoDB exception details to API consumers.

Instead, translate them into appropriate application-level responses.

---

# Interview Notes

A common interview question is:

> **What exceptions should be retried in DynamoDB?**

Retry temporary failures such as `ProvisionedThroughputExceededException`, `ThrottlingException`, and transient network or internal server errors. Do not retry validation errors or permission issues.

---

Another common question is:

> **Why is exponential backoff important?**

Exponential backoff reduces contention by spacing out retry attempts, allowing DynamoDB time to recover and reducing the likelihood of repeated failures.

---

Another common question is:

> **What is jitter, and why should it be used?**

Jitter introduces a random delay into retry intervals so that many clients do not retry simultaneously, reducing retry storms and improving overall system stability.

---

Another common question is:

> **Why should retries be combined with idempotency?**

Without idempotency, a retried write request could create duplicate records or perform the same business operation multiple times. Idempotency ensures repeated requests produce the same result safely.

---

# Key Takeaways

- Production applications should assume transient failures will occur and implement robust error handling.
- Distinguish between retryable and non-retryable exceptions.
- Use exponential backoff with jitter to retry transient failures safely.
- Configure Boto3 retry behavior appropriately and monitor CloudWatch metrics for operational visibility.
- Combine retries with idempotent operations and meaningful logging to build resilient, production-ready DynamoDB applications.