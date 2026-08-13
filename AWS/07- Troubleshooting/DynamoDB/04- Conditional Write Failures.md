# 04 - Conditional Write Failures

## Overview

Conditional writes are one of DynamoDB's most powerful features for maintaining data integrity in distributed systems.

Instead of blindly updating data, an application can specify a condition that **must be true** before the write succeeds.

This enables:

- Optimistic locking
- Idempotent APIs
- Duplicate prevention
- Inventory management
- State machine enforcement
- Concurrency control

When the condition evaluates to **false**, DynamoDB rejects the request with:

```text
ConditionalCheckFailedException
```

Unlike many other exceptions, this is **usually expected behavior**, not a system failure.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What conditional writes are
- Why they fail
- Common production scenarios
- Optimistic locking
- Idempotency
- Debugging techniques
- Retry strategies
- Best practices

---

# What is a Conditional Write?

Instead of writing directly:

```text
Application

↓

Update Item
```

The application sends:

```text
Update Item

↓

Check Condition

↓

True?

↓

Update
```

Otherwise:

```text
Condition False

↓

Reject Request
```

---

# Conditional Write Flow

```text
Application

      │

      ▼

Condition Expression

      │

      ▼

Evaluate

 ┌─────────────┐
 │             │
 ▼             ▼

TRUE         FALSE

 │             │

 ▼             ▼

Update      Exception
```

---

# Common Exception

```text
ConditionalCheckFailedException
```

This indicates:

> The request was valid, but the condition evaluated to **false**.

---

# Common Causes

Conditional write failures commonly occur because of:

- Duplicate inserts
- Optimistic locking conflicts
- Concurrent updates
- Invalid state transitions
- Inventory already consumed
- Business rule violations

---

# Scenario 1 — Prevent Duplicate Orders

Suppose an API creates orders.

Condition:

```text
attribute_not_exists(order_id)
```

Workflow:

```text
Order Exists?

↓

Yes

↓

Reject

↓

ConditionalCheckFailedException
```

This prevents duplicate records.

---

# CLI Example

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item file://order.json \
    --condition-expression \
        "attribute_not_exists(order_id)"
```

---

# Scenario 2 — Optimistic Locking

Current version:

```text
version = 7
```

Client updates:

```text
Expected Version = 7
```

Condition:

```text
version = :expected
```

If another user already updated:

```text
Database

version = 8
```

Result:

```text
ConditionalCheckFailedException
```

---

# Optimistic Locking Workflow

```text
Read Item

↓

Version = 5

↓

Update

↓

Version Still 5?

      │

 ┌────┴────┐

 ▼         ▼

Yes        No

 │         │

 ▼         ▼

Update   Reject
```

---

# Scenario 3 — State Machine

Order:

```text
PENDING
```

Allowed:

```text
PENDING

↓

SHIPPED
```

Not allowed:

```text
DELIVERED

↓

PENDING
```

Condition:

```text
status = :pending
```

---

# Scenario 4 — Inventory

Inventory:

```text
Stock = 5
```

Purchase:

```text
Quantity = 2
```

Condition:

```text
stock >= :quantity
```

If:

```text
Stock = 1
```

Result:

```text
ConditionalCheckFailedException
```

---

# Scenario 5 — Idempotent APIs

Client retries:

```text
POST /payments
```

Request ID:

```text
ABC123
```

Condition:

```text
attribute_not_exists(request_id)
```

Duplicate request:

```text
Rejected
```

Payment processed only once.

---

# Common Debugging Workflow

```text
Exception

↓

Retrieve Current Item

↓

Evaluate Condition

↓

Application Bug?

↓

Concurrency?

↓

Expected Failure?
```

---

# Application Logs

Always log:

- Partition key
- Condition expression
- Expected values
- Current values
- Request ID
- Timestamp

Avoid logging sensitive data.

---

# Retrieve Current Item

CLI:

```bash
aws dynamodb get-item \
    --table-name Orders \
    --key file://key.json
```

Compare:

```text
Expected

↓

Actual

↓

Mismatch
```

---

# Retry Strategy

Not every conditional failure should be retried.

Decision tree:

```text
Condition Failed

      │

      ▼

Expected Conflict?

      │

 ┌────┴─────┐

 ▼          ▼

Yes        No

 │          │

 ▼          ▼

Handle     Investigate
```

---

# Should You Retry?

Generally:

| Scenario | Retry? |
|----------|---------|
| Optimistic Lock | ✅ After rereading data |
| Duplicate Request | ❌ |
| Business Rule Failure | ❌ |
| Inventory Conflict | Depends |
| Temporary Network Error | ✅ |

---

# Bad Retry Pattern

```text
Failure

↓

Retry

↓

Failure

↓

Retry Forever
```

Creates unnecessary load.

---

# Better Retry Pattern

```text
Failure

↓

Read Latest Item

↓

Re-evaluate

↓

Retry If Appropriate
```

---

# Monitoring

Useful metrics:

- Failed updates
- Conflict rate
- Retry count
- API failures
- Latency

Sudden increases often indicate:

- Increased concurrency
- Application bugs
- Deployment issues

---

# Production Example

Shopping cart:

```text
Customer

↓

Checkout

↓

Reserve Inventory

↓

Update Stock

↓

Condition Check
```

If another customer already purchased:

```text
Reject

↓

Out of Stock
```

---

# Banking Example

Account:

```text
Balance = $500
```

Withdrawal:

```text
$700
```

Condition:

```text
balance >= amount
```

Without condition:

```text
Negative Balance
```

With condition:

```text
Rejected
```

---

# Distributed System Example

Two services:

```text
Inventory Service

↓

Order Service

↓

Same Product
```

Both attempt update.

Condition ensures:

```text
Only One Update Wins
```

---

# Production Architecture

```text
Application

      │

      ▼

Conditional Write

      │

      ▼

Amazon DynamoDB

      │

 ┌────┴────┐

 ▼         ▼

Success   Condition Failed

           │

           ▼

Application Logic
```

---

# Performance Considerations

- Conditional writes require DynamoDB to evaluate expressions before applying changes.
- Avoid unnecessary condition expressions.
- Use optimistic locking only where concurrency is expected.
- Design retry logic carefully.
- Monitor conflict rates.

---

# Best Practices

- Expect conditional failures.
- Never treat every failure as a server error.
- Log enough information for debugging.
- Use optimistic locking for concurrent updates.
- Use condition expressions to enforce business rules.
- Build idempotent APIs.

---

# Common Mistakes

## Treating Every Failure as an Exception

Many conditional failures are expected business outcomes.

---

## Infinite Retry

Retrying without rereading data causes repeated failures.

---

## Ignoring Concurrency

Multiple clients updating the same item simultaneously require optimistic locking.

---

## Missing Idempotency

Without condition expressions, duplicate API requests may create duplicate records.

---

# Interview Notes

### What is `ConditionalCheckFailedException`?

It occurs when a DynamoDB condition expression evaluates to false. The request is valid, but the specified business rule or concurrency condition was not satisfied.

---

### Why use conditional writes?

To enforce business rules, prevent duplicate data, implement optimistic locking, maintain inventory consistency, and build idempotent APIs.

---

### Should `ConditionalCheckFailedException` always be retried?

No. It depends on the scenario. Duplicate requests or business rule violations should not be retried, while optimistic locking conflicts may succeed after rereading the latest item.

---

### How does optimistic locking work in DynamoDB?

Each item contains a version attribute. Updates succeed only if the version matches the expected value. If another client has already modified the item, the condition fails, preventing lost updates.

---

### Why are conditional writes important in distributed systems?

They provide atomic validation and updates without requiring external locking mechanisms, helping maintain consistency across concurrent operations.

---

# Key Takeaways

- Conditional writes enforce business rules directly within DynamoDB.
- `ConditionalCheckFailedException` is often an expected result of optimistic concurrency control rather than a system failure.
- Common use cases include duplicate prevention, optimistic locking, inventory management, and idempotent APIs.
- Proper logging, conflict handling, and retry strategies are essential for building resilient distributed systems.
- Senior backend engineers design applications that anticipate and correctly handle conditional write failures rather than treating them as unexpected errors.