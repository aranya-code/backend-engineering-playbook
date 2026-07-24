# 18 - Error Handling & Retries

## Overview

Distributed systems are designed with the assumption that failures will occur. Network interruptions, temporary service unavailability, throttling, and concurrent updates are inevitable in any large-scale application.

DynamoDB is a highly available managed service, but applications interacting with it must still be designed to handle transient failures gracefully.

Proper error handling and retry strategies improve:

- Availability
- Reliability
- Throughput
- User experience
- Cost efficiency

A poorly implemented retry mechanism can easily make a temporary problem significantly worse by overwhelming DynamoDB with additional requests.

---

# Why Error Handling Matters

Consider an e-commerce application.

A customer places an order.

```text
Application

↓

Update Inventory

↓

Network Timeout
```

Did the write fail?

Or did DynamoDB successfully process it while the response was lost?

Without proper retry logic:

```text
Retry Immediately

↓

Duplicate Order

OR

Lost Order
```

Robust error handling prevents these problems.

---

# Common DynamoDB Errors

Applications commonly encounter the following exceptions.

| Exception | Meaning | Retry? |
|-----------|----------|---------|
| ProvisionedThroughputExceededException | Table or partition is throttled | ✅ Yes |
| ThrottlingException | Request rate exceeded | ✅ Yes |
| InternalServerError | Temporary AWS service issue | ✅ Yes |
| RequestLimitExceeded | AWS API request limit exceeded | ✅ Yes |
| ConditionalCheckFailedException | Condition expression failed | ❌ No |
| TransactionCanceledException | Transaction failed | Depends |
| ResourceNotFoundException | Table or item does not exist | ❌ No |
| ValidationException | Invalid request | ❌ No |

Understanding which errors are transient versus permanent is critical.

---

# Error Categories

Errors generally fall into two categories.

## Retryable Errors

Temporary failures.

Examples:

```text
Network Timeout

↓

Retry
```

```text
Throttling

↓

Retry
```

```text
Internal Error

↓

Retry
```

---

## Non-Retryable Errors

Application mistakes.

Examples:

```text
Wrong Table Name
```

```text
Missing Partition Key
```

```text
Invalid Condition
```

Retrying these requests will never succeed until the underlying problem is fixed.

---

# Throttling

The most common production error is throttling.

```text
Application

↓

10,000 Writes/sec

↓

Table Capacity

↓

5,000 Writes/sec
```

Result:

```text
ThrottlingException
```

DynamoDB protects itself by rejecting excess requests.

---

# Retry Workflow

```text
Application

↓

Request

↓

Temporary Failure

↓

Wait

↓

Retry

↓

Success
```

The waiting period is critical.

Immediate retries often increase throttling.

---

# Exponential Backoff

Instead of retrying continuously:

Poor:

```text
Retry

↓

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

100 ms

↓

Retry

↓

200 ms

↓

Retry

↓

400 ms

↓

Retry
```

The delay grows after every failure.

---

# Exponential Backoff with Jitter

AWS recommends using **Exponential Backoff with Jitter**.

Instead of:

```text
100

200

400

800
```

Use:

```text
135

276

418

907
```

The random delay prevents thousands of clients from retrying simultaneously.

---

# Internal Retry Architecture

```text
                 Application

                       │

                DynamoDB Request

                       │

                Temporary Error

                       │

         Calculate Backoff Delay

                       │

               Wait + Jitter

                       │

                    Retry

                       │

                  Success
```

This approach minimizes retry storms during traffic spikes.

---

# ConditionalCheckFailedException

This exception indicates:

```text
Business Rule Failed
```

Example:

```text
Inventory >= RequestedQuantity
```

If:

```text
False
```

The write is rejected.

Retrying immediately is useless because nothing has changed.

The application should instead:

- Inform the user
- Reload the latest data
- Allow another attempt if appropriate

---

# TransactionCanceledException

Transactions may fail because of:

- Condition failures
- Transaction conflicts
- Capacity limits

Workflow:

```text
Transaction

↓

Conflict

↓

Rollback

↓

Retry Later
```

Applications should inspect the cancellation reason before retrying.

---

# Network Timeouts

Sometimes the client never receives a response.

```text
Request

↓

Processed?

↓

Unknown
```

The application cannot immediately determine whether DynamoDB committed the operation.

Solutions:

- Idempotent writes
- Client request tokens
- Conditional writes

---

# Idempotent Retries

An idempotent request produces the same result even if executed multiple times.

Example:

```text
PaymentID

12345
```

Before inserting:

```text
attribute_not_exists(PaymentID)
```

If the first request succeeded but the response was lost:

```text
Retry

↓

Duplicate Prevented
```

This is a common production pattern.

---

# AWS SDK Automatic Retries

AWS SDKs automatically retry many transient failures.

Typical retryable errors include:

- Throttling
- Internal server errors
- Network interruptions

Applications should avoid implementing aggressive retry loops on top of the SDK's built-in behavior without understanding the retry configuration.

---

# Retry Decision Matrix

| Error | Retry? | Reason |
|--------|---------|--------|
| Network Timeout | ✅ | Temporary |
| Throttling | ✅ | Capacity spike |
| InternalServerError | ✅ | Service issue |
| RequestLimitExceeded | ✅ | Temporary AWS limit |
| ConditionalCheckFailedException | ❌ | Business rule failure |
| ValidationException | ❌ | Invalid request |
| ResourceNotFoundException | ❌ | Configuration issue |

---

# Real-World Example — Inventory Service

Current stock:

```text
Stock = 5
```

Customer requests:

```text
10 Items
```

Condition:

```text
Stock >= 10
```

Fails.

Application:

```text
Display

Out of Stock
```

Do not retry.

---

# Real-World Example — Payment Processing

Workflow:

```text
Charge Card

↓

Network Timeout
```

Retry:

```text
Condition

PaymentID Does Not Exist

↓

Safe Retry
```

No duplicate charges occur.

---

# Real-World Example — High Traffic Sale

Flash sale:

```text
100,000 Requests

↓

Capacity Spike

↓

Throttling
```

Applications:

```text
Exponential Backoff

↓

Retry

↓

Success
```

This prevents overwhelming the table.

---

# Real-World Example — Banking

Money transfer transaction:

```text
Conflict

↓

TransactionCanceledException
```

Application:

```text
Reload

↓

Retry Transaction
```

Only after verifying the cause.

---

# Best Practices

- Implement exponential backoff with jitter.
- Retry only transient failures.
- Never retry validation errors.
- Use idempotent request patterns.
- Catch and log all DynamoDB exceptions.
- Monitor throttling metrics using CloudWatch.
- Design applications to tolerate temporary failures.

---

# Common Mistakes

## Immediate Retries

Poor:

```text
Retry

↓

Retry

↓

Retry

↓

Retry
```

This amplifies throttling.

Always introduce a delay.

---

## Retrying Conditional Failures

Incorrect:

```text
Condition Failed

↓

Retry Immediately
```

Nothing has changed.

Instead:

- Reload data
- Resolve the business conflict

---

## Ignoring Retry Limits

Applications should limit retry attempts.

Infinite retry loops can consume resources indefinitely.

---

## Treating Every Error Equally

Different errors require different handling strategies.

Business validation failures should not be treated like transient infrastructure failures.

---

# Architecture Perspective

```text
                 Client Request

                       │

                DynamoDB Service

                       │

          ┌────────────┼────────────┐

          ▼                         ▼

     Success                  Exception

                                    │

                  ┌─────────────────┴─────────────────┐

                  ▼                                   ▼

          Retryable Error                     Permanent Error

                  │                                   │

                  ▼                                   ▼

      Backoff + Jitter Retry                 Return Failure

                  │

                  ▼

              Success
```

A resilient application distinguishes between transient and permanent failures, retrying only when appropriate.

---

# Production Considerations

Production systems should implement a layered resilience strategy.

This typically includes:

- AWS SDK automatic retries
- Exponential backoff with jitter
- Idempotent write operations
- Conditional writes
- Optimistic locking
- Circuit breakers
- Dead-letter queues (DLQs) for asynchronous processing
- Monitoring and alerting using CloudWatch

These patterns help maintain application availability even during infrastructure failures or traffic spikes.

---

# Interview Notes

A common interview question is:

> **Which DynamoDB errors should be retried?**

Retry transient errors such as throttling, network timeouts, internal server errors, and temporary AWS service limits. Do not retry validation errors or failed condition expressions.

Another common question is:

> **Why is exponential backoff recommended?**

It reduces request bursts during failures, giving DynamoDB time to recover and preventing retry storms.

Another common question is:

> **What is jitter?**

Jitter adds a random delay to exponential backoff so that many clients do not retry at exactly the same time, improving system stability.

Another common question is:

> **How do you safely retry a write after a network timeout?**

Use idempotent request patterns, such as unique request IDs combined with conditional writes, so repeated requests do not create duplicate records.

---

# Key Takeaways

- Not every DynamoDB error should be retried.
- Retry only transient failures such as throttling and temporary service issues.
- Use exponential backoff with jitter to avoid retry storms.
- Do not retry `ConditionalCheckFailedException` or validation errors without addressing the underlying issue.
- Design idempotent APIs to safely handle retries after uncertain failures.
- Combining retries with monitoring, conditional writes, and optimistic locking creates resilient production-grade DynamoDB applications.