# 05 - Transaction Issues

## Overview

Amazon DynamoDB supports ACID-compliant transactions through the **TransactWriteItems** and **TransactGetItems** APIs.

Transactions allow multiple operations across one or more tables to either:

- Complete successfully together
- Or fail completely

This guarantees atomicity and consistency, making transactions useful for financial systems, inventory management, order processing, and other business-critical workflows.

However, transaction failures are among the more difficult production issues to troubleshoot because multiple operations may participate in a single request.

This chapter explains common transaction failures, how to investigate them, and production best practices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- DynamoDB transactions
- ACID guarantees
- Transaction limits
- TransactionCanceledException
- Transaction conflicts
- Retry strategies
- Production debugging
- Best practices

---

# What is a DynamoDB Transaction?

Without transactions:

```text
Update A

↓

Success

↓

Update B

↓

Failure
```

Database becomes inconsistent.

---

With transactions:

```text
Update A

↓

Update B

↓

Update C

↓

Commit

↓

Success
```

or

```text
Update A

↓

Update B

↓

Failure

↓

Rollback Everything
```

---

# ACID Properties

Transactions provide:

| Property | Meaning |
|----------|----------|
| Atomicity | All operations succeed or none do |
| Consistency | Database remains valid |
| Isolation | Concurrent transactions do not interfere |
| Durability | Committed changes are permanent |

---

# Transaction Architecture

```text
Application

      │

      ▼

TransactWriteItems

      │

      ▼

Operation 1

Operation 2

Operation 3

      │

      ▼

Commit

OR

Rollback
```

---

# Common Exception

```text
TransactionCanceledException
```

This is the most common transaction-related error.

---

# Why Transactions Fail

Typical causes include:

- Conditional check failure
- Item conflicts
- Concurrent updates
- Validation errors
- Transaction size limits
- Capacity throttling

---

# Transaction Conflict

Two services attempt to modify the same item.

```text
Service A

      │

      ▼

Update Customer

──────────────

Service B

      │

      ▼

Update Customer
```

Only one transaction succeeds.

The other fails.

---

# Production Example

Inventory:

```text
Stock = 10
```

Two users purchase simultaneously.

```text
Customer A

↓

Reserve Stock

────────────

Customer B

↓

Reserve Stock
```

One transaction commits.

The other receives:

```text
TransactionCanceledException
```

---

# Banking Example

Transfer money:

```text
Debit Account

↓

Credit Account

↓

Create Audit Record
```

If:

```text
Audit Record

↓

Fails
```

Entire transaction rolls back.

No partial transfer occurs.

---

# Conditional Check Failure

Inside a transaction:

```text
Condition

↓

False
```

Result:

```text
Entire Transaction

↓

Rollback
```

Even if every other operation is valid.

---

# Transaction Limits

Current limits include:

- Maximum **100 operations** per transaction.
- Aggregate request size up to **4 MB**.
- An individual item can only appear once within the same transaction.

Design workflows accordingly.

---

# Large Transaction Example

Poor:

```text
Update

250 Items
```

Not allowed.

Better:

```text
Batch Workflow

↓

Multiple Transactions
```

---

# Transaction Debugging Workflow

```text
Failure

↓

Read Exception

↓

Identify Failed Operation

↓

Review Condition

↓

Check Conflicts

↓

Retry?
```

---

# Application Logging

Log:

- Transaction ID
- Request ID
- Partition keys
- Table names
- Condition expressions
- Retry count
- Timestamp

Avoid logging sensitive business data.

---

# Retry Strategy

Decision tree:

```text
Transaction Failed

      │

      ▼

Transient?

      │

 ┌────┴─────┐

 ▼          ▼

Yes         No

 │           │

 ▼           ▼

Retry     Investigate
```

---

# Exponential Backoff

Correct approach:

```text
Failure

↓

Wait

↓

Retry

↓

Longer Wait

↓

Retry
```

Avoid immediate retries.

---

# Retry with Jitter

Better:

```text
Failure

↓

Random Delay

↓

Retry
```

Random delays reduce contention.

---

# Detecting Transaction Conflicts

Symptoms:

- Increasing transaction failures
- High retry count
- Increased latency
- Frequent conditional failures

Often caused by:

- Hot partitions
- Shared resources
- Poor application design

---

# Monitoring

Useful CloudWatch metrics:

```text
SuccessfulRequestLatency

WriteThrottleEvents

ReadThrottleEvents

ConsumedWriteCapacityUnits

ConsumedReadCapacityUnits
```

Monitor alongside application logs.

---

# CLI Example

Transaction:

```bash
aws dynamodb transact-write-items \
    --transact-items file://transaction.json
```

Always validate:

- JSON syntax
- Conditions
- Item keys
- Attribute values

---

# Common Production Scenario

Checkout system:

```text
Customer

↓

Create Order

↓

Reserve Inventory

↓

Record Payment

↓

Commit
```

Failure:

```text
Inventory Reserved

Payment Failed
```

Transaction ensures:

```text
Rollback Everything
```

---

# Distributed Microservices Example

```text
Order Service

      │

      ▼

Inventory Service

      │

      ▼

Payment Service

      │

      ▼

DynamoDB Transaction
```

Ensures all related updates succeed together.

---

# Common Design Mistake

Using transactions for every write.

Poor:

```text
Update User Name

↓

Transaction
```

Better:

```text
Simple UpdateItem
```

Reserve transactions for operations requiring atomicity across multiple items.

---

# Performance Impact

Transactions are more expensive than individual operations.

Reasons:

- Multiple items
- Lock coordination
- Additional validation
- Atomic commit protocol

Use only when necessary.

---

# Production Architecture

```text
API

      │

      ▼

Business Logic

      │

      ▼

Transaction Manager

      │

      ▼

Amazon DynamoDB

      │

 ┌────┴────┐

 ▼         ▼

Commit   Rollback
```

---

# Performance Considerations

- Keep transactions small.
- Minimize item contention.
- Avoid long-running workflows.
- Use simple writes whenever possible.
- Monitor retry rates.
- Design partition keys to reduce conflicts.

---

# Best Practices

- Use transactions only when atomicity is required.
- Keep the number of operations as small as possible.
- Design for low contention.
- Log transaction metadata.
- Implement exponential backoff with jitter.
- Monitor transaction failure rates.

---

# Common Mistakes

## Wrapping Every Operation in a Transaction

Transactions introduce additional latency and cost.

Simple operations should use:

```text
PutItem

UpdateItem

DeleteItem
```

---

## Infinite Retries

Repeated retries without backoff increase contention.

---

## Ignoring Conditional Failures

Many transaction failures are caused by condition expressions rather than DynamoDB service issues.

---

## Large Transactions

Large transactions:

- Increase latency
- Increase conflict probability
- Increase rollback frequency

Keep transactions focused.

---

# Interview Notes

### What exception is commonly associated with DynamoDB transactions?

`TransactionCanceledException`

---

### Why would a transaction fail?

Common reasons include:

- Conditional check failure
- Concurrent updates
- Validation errors
- Capacity throttling
- Transaction size limits

---

### When should you use DynamoDB transactions?

When multiple items or tables must be updated atomically and partial success is unacceptable.

---

### Are DynamoDB transactions ACID compliant?

Yes. DynamoDB transactions provide Atomicity, Consistency, Isolation, and Durability.

---

### Are transactions faster than normal writes?

No. Transactions require additional coordination and validation, making them slower and more resource-intensive than individual write operations.

---

# Key Takeaways

- DynamoDB transactions provide ACID guarantees across multiple items and tables.
- `TransactionCanceledException` is the primary indicator of transaction failures and often results from conflicts or failed condition checks.
- Transactions should be reserved for workflows requiring strict consistency, such as financial transfers, inventory reservation, and order processing.
- Small, focused transactions with proper retry logic and monitoring are more reliable and performant than large, highly contended transactions.
- Senior engineers balance the need for atomicity against the additional latency, cost, and operational complexity introduced by transactions.