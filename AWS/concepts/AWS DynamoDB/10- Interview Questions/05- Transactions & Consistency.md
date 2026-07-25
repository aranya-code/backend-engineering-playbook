# 05 - Transactions & Consistency

## Overview

Transactions and consistency are among the most important topics in senior DynamoDB interviews.

Interviewers want to know whether you understand:

- ACID guarantees
- Optimistic locking
- Conditional writes
- Strong vs eventual consistency
- Distributed systems trade-offs
- Transaction limitations
- Production design decisions

A common interview question is:

> "How would you prevent two users from updating the same record simultaneously?"

This chapter prepares you for those discussions.

---

# Learning Objectives

After completing this chapter, you'll be able to answer interview questions about:

- ACID transactions
- TransactWriteItems
- TransactGetItems
- Conditional writes
- Optimistic locking
- Strong consistency
- Eventual consistency
- Conflict detection
- Production best practices

---

# Question 1

## Does DynamoDB support transactions?

### Expected Answer

Yes.

DynamoDB supports fully managed ACID transactions across multiple items and tables within the same AWS account and Region.

Supported APIs include:

- TransactWriteItems
- TransactGetItems

Transactions ensure that either:

```text
All Operations

↓

Success
```

or

```text
Any Failure

↓

Everything Rolls Back
```

---

## Interview Tip

Mention:

- ACID
- Atomicity
- Rollback
- Multiple items
- Multiple tables

---

# Question 2

## What operations are supported inside TransactWriteItems?

### Expected Answer

A transaction can contain:

- Put
- Update
- Delete
- ConditionCheck

Example:

```text
Update Account

↓

Insert Payment

↓

Delete Cart

↓

Commit
```

If any operation fails, none of the changes are committed.

---

# Question 3

## What is TransactGetItems?

### Expected Answer

TransactGetItems retrieves multiple items atomically.

The application receives a consistent snapshot of all requested items.

Example:

```text
Customer

Order

Invoice

↓

Single Transaction
```

---

# Question 4

## What is a conditional write?

### Expected Answer

A conditional write executes only if a specified condition is true.

Example:

```text
Update Balance

ONLY IF

Version = 10
```

Otherwise:

```text
ConditionalCheckFailedException
```

is returned.

---

# Question 5

## Why are conditional writes important?

### Expected Answer

They prevent accidental overwrites.

Example:

```text
User A

↓

Update
```

```text
User B

↓

Update
```

Without conditions:

```text
Last Writer Wins
```

With conditional writes:

```text
Conflict Detected
```

---

# Question 6

## What is optimistic locking?

### Expected Answer

Optimistic locking uses a version number.

Example:

```text
Version = 5
```

Application updates:

```text
IF Version = 5
```

Successful update:

```text
Version = 6
```

If another application already modified the item:

```text
Condition Failed
```

---

## Production Benefit

Optimistic locking prevents lost updates without locking the entire record.

---

# Question 7

## How does DynamoDB implement optimistic locking?

### Expected Answer

Applications maintain a version attribute.

Workflow:

```text
Read Item

↓

Version = 7

↓

Update IF Version = 7

↓

Version = 8
```

Any concurrent modification causes the update to fail.

---

# Question 8

## What happens if two transactions modify the same item?

### Expected Answer

One transaction succeeds.

The other transaction fails because DynamoDB detects the conflict.

The application should retry if appropriate.

---

# Question 9

## What is strong consistency?

### Expected Answer

Strongly consistent reads always return the latest committed value.

Example:

```text
Write

↓

Read

↓

Latest Value
```

---

# Question 10

## What is eventual consistency?

### Expected Answer

Eventually consistent reads may temporarily return stale data while replicas synchronize.

Workflow:

```text
Write

↓

Replica Synchronization

↓

Eventually Updated
```

This is the default behavior for DynamoDB reads.

---

# Question 11

## Which operations support strong consistency?

### Expected Answer

Strong consistency is supported for:

- GetItem
- Query
- Scan

when reading from:

- Base table
- Local Secondary Index (LSI)

Strong consistency is **not** available on:

- Global Secondary Indexes (GSIs)
- DynamoDB Streams

---

# Question 12

## When should strong consistency be used?

### Expected Answer

Use it when the latest committed data is required.

Examples:

- Banking
- Inventory management
- Payment processing
- Reservation systems

Otherwise, eventual consistency usually provides better scalability and lower cost.

---

# Question 13

## Does strong consistency improve performance?

### Expected Answer

No.

Strong consistency typically reduces read scalability compared to eventual consistency because reads cannot be served from stale replicas.

Choose it only when required by business rules.

---

# Question 14

## What are transaction conflicts?

### Expected Answer

A transaction conflict occurs when multiple transactions attempt to modify the same item simultaneously.

Example:

```text
Transaction A

↓

Update Balance
```

```text
Transaction B

↓

Update Balance
```

One transaction succeeds.

The other fails and must retry if appropriate.

---

# Question 15

## How should applications handle transaction failures?

### Expected Answer

Recommended approach:

- Catch the exception
- Log the failure
- Retry using exponential backoff where appropriate
- Avoid unlimited retries
- Surface meaningful errors to users

---

# Question 16

## Are transactions always the best solution?

### Expected Answer

No.

Transactions introduce additional latency and consume more resources than single-item operations.

Many workloads can be implemented safely using:

- Conditional writes
- Idempotent operations
- Careful application logic

---

# Question 17

## How do you prevent duplicate order creation?

### Expected Answer

One common approach is to use a conditional write.

Example:

```text
PutItem

IF attribute_not_exists(OrderID)
```

If the order already exists:

```text
Conditional Check Failed
```

No duplicate order is created.

---

# Question 18

## What is idempotency?

### Expected Answer

An idempotent operation produces the same final result even if it is executed multiple times.

Example:

```text
Payment Request

↓

Network Retry

↓

Same Payment

NOT

Duplicate Payment
```

Idempotency is critical for distributed systems where retries are common.

---

# Question 19

## How would you design a payment workflow?

### Expected Answer

A typical production design includes:

- Idempotency key
- Conditional writes
- Transaction for related updates
- Retry with exponential backoff
- Audit logging

Example:

```text
Receive Payment

↓

Validate Idempotency Key

↓

Transaction

↓

Update Balance

↓

Insert Payment Record

↓

Commit
```

---

# Question 20

## Explain DynamoDB transactions in one minute.

### Sample Answer

> DynamoDB supports ACID transactions through TransactWriteItems and TransactGetItems, allowing multiple operations across one or more tables within the same Region to succeed or fail atomically. For simpler concurrency control, conditional writes and optimistic locking are often preferred because they provide lower latency and lower cost. Strongly consistent reads are available on base tables and LSIs, while GSIs always provide eventual consistency. Choosing between these mechanisms depends on business requirements, performance goals, and scalability considerations.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| ACID transactions supported? | Yes |
| Write transaction API? | TransactWriteItems |
| Read transaction API? | TransactGetItems |
| Conditional update? | Yes |
| Optimistic locking? | Version attribute |
| Strong consistency on GSI? | No |
| Strong consistency on LSI? | Yes |
| Default read consistency? | Eventual |
| Duplicate prevention? | Conditional write |
| Transaction rollback? | Automatic |

---

# Senior Interview Tips

A strong candidate should explain:

- When transactions are necessary
- When conditional writes are sufficient
- Cost and latency trade-offs
- Retry strategies
- Idempotency
- Concurrency control

Avoid saying:

> "I always use transactions."

Instead explain:

> "I use transactions only when multiple writes must succeed or fail together. For single-item updates, conditional writes are usually simpler and more efficient."

---

# Common Mistakes

## Using Transactions for Every Update

Transactions add overhead.

Prefer simpler operations when atomicity across multiple items is unnecessary.

---

## Ignoring Conditional Writes

Many concurrency problems can be solved without full transactions.

---

## Forgetting Retry Logic

Transaction conflicts are expected under concurrent workloads.

Applications should retry carefully using exponential backoff.

---

## Misunderstanding Strong Consistency

Strong consistency guarantees the latest committed data but does not eliminate application-level race conditions or replace proper concurrency control.

---

# Interview Cheat Sheet

```text
Concurrent Updates

↓

Conditional Write

↓

Optimistic Locking

↓

Transactions

↓

ACID

↓

Rollback

↓

Strong Consistency

↓

Eventual Consistency

↓

Retry Logic

↓

Idempotency
```

---

# Key Takeaways

- DynamoDB supports ACID transactions through `TransactWriteItems` and `TransactGetItems`, but they should be used only when multiple operations must succeed or fail together.
- Conditional writes and optimistic locking are often more efficient solutions for preventing concurrent update conflicts.
- Strongly consistent reads are available only on base tables and LSIs, while GSIs always return eventually consistent results.
- Idempotency, retry strategies, and concurrency control are essential design considerations for production systems.
- Senior interviewers expect candidates to discuss trade-offs between correctness, latency, scalability, and operational complexity rather than simply listing DynamoDB features.