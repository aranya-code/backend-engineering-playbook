# 07 - Conditional Writes

## Overview

In distributed systems, multiple users or services may attempt to modify the same item simultaneously.

Consider the following scenarios:

- Two users purchasing the last product in stock
- Multiple workers processing the same queue message
- Two APIs updating the same customer profile
- Multiple Lambda functions writing to the same record

Without safeguards, these concurrent operations can lead to:

- Lost updates
- Duplicate records
- Race conditions
- Data corruption

Amazon DynamoDB provides **Conditional Writes**, allowing write operations to succeed **only when specified conditions are met**.

Conditional writes are one of the most powerful features of DynamoDB and are heavily used in production systems to enforce business rules without requiring distributed locks.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What Conditional Writes are
- Condition Expressions
- Conditional PutItem
- Conditional UpdateItem
- Conditional DeleteItem
- Optimistic Locking
- Compare-and-Swap (CAS)
- Idempotency
- Production patterns
- Best practices
- Interview questions

---

# Why Conditional Writes?

Imagine two users trying to reserve the same seat.

Without conditions:

```text
User A

        │
        ▼
 Read Seat

        │
        ▼
Available

──────────────

User B

        │
        ▼
 Read Seat

        │
        ▼
Available

──────────────

User A → Reserve

User B → Reserve

↓

Seat Reserved Twice ❌
```

Conditional writes prevent this.

---

# How Conditional Writes Work

```text
Application

        │

        ▼

Write Request

        │

        ▼

Evaluate Condition

        │

 ┌──────┴──────┐

 ▼             ▼

TRUE         FALSE

 │              │

 ▼              ▼

Write       Reject Write
```

The condition is evaluated atomically by DynamoDB.

---

# ConditionExpression

Every conditional write uses a `ConditionExpression`.

Example:

```python
ConditionExpression="attribute_not_exists(order_id)"
```

The write succeeds only if the condition evaluates to `TRUE`.

---

# Conditional PutItem

Suppose we want to insert a new order.

```python
table.put_item(
    Item={
        "order_id": "ORD-1001",
        "status": "Pending"
    },
    ConditionExpression=
        "attribute_not_exists(order_id)"
)
```

Execution:

```text
Order Exists?

      │

 ┌────┴────┐

 ▼         ▼

No        Yes

 │          │

 ▼          ▼

Insert    Reject
```

This prevents accidental overwrites.

---

# Duplicate Prevention

Without condition:

```text
Insert

↓

Overwrite Existing Record
```

With condition:

```text
Insert

↓

Already Exists?

↓

ConditionalCheckFailedException
```

This is the preferred approach for creating unique records.

---

# Conditional Update

Only update if the current status is `Pending`.

```python
table.update_item(
    Key={
        "order_id": "ORD-1001"
    },
    UpdateExpression="SET #s=:status",
    ConditionExpression="#s=:pending",
    ExpressionAttributeNames={
        "#s": "status"
    },
    ExpressionAttributeValues={
        ":status": "Completed",
        ":pending": "Pending"
    }
)
```

Execution:

```text
Status = Pending?

      │

 ┌────┴────┐

 ▼         ▼

Yes        No

 │          │

 ▼          ▼

Update    Reject
```

---

# Conditional Delete

Delete only if payment has been refunded.

```python
table.delete_item(
    Key={
        "order_id": "ORD-1001"
    },
    ConditionExpression=
        "#status=:value",
    ExpressionAttributeNames={
        "#status":"status"
    },
    ExpressionAttributeValues={
        ":value":"Refunded"
    }
)
```

This prevents accidental deletion.

---

# Common Condition Functions

## attribute_exists()

```python
ConditionExpression=
"attribute_exists(order_id)"
```

Used when updating existing records.

---

## attribute_not_exists()

```python
ConditionExpression=
"attribute_not_exists(order_id)"
```

Used when inserting new records.

---

## begins_with()

```python
begins_with(customer_id, "VIP")
```

Useful for string-based conditions.

---

## contains()

```python
contains(tags, "Premium")
```

Checks whether a collection contains a value.

---

## size()

```python
size(description) < 500
```

Validates attribute length.

---

# Comparison Operators

Supported operators include:

```text
=

<

<=

>

>=

<>

BETWEEN

IN
```

These can be combined with logical operators.

---

# Logical Operators

Examples:

```text
AND

OR

NOT
```

Example:

```python
ConditionExpression=
"attribute_exists(order_id) AND #status=:status"
```

---

# Optimistic Locking

One of the most common production use cases.

Every item stores a version number.

```json
{
    "order_id":"ORD-1001",
    "version":3
}
```

Workflow:

```text
Read Version = 3

↓

Update

↓

Condition

Version == 3

↓

Increment Version
```

If another application already updated the item:

```text
Current Version = 4

↓

Condition Fails

↓

Retry
```

---

# Optimistic Locking Example

```python
table.update_item(
    Key={
        "order_id":"ORD-1001"
    },
    UpdateExpression=
        "SET version = version + :one",
    ConditionExpression=
        "version = :expected",
    ExpressionAttributeValues={
        ":one":1,
        ":expected":3
    }
)
```

Only one update succeeds.

---

# Compare-and-Swap (CAS)

Conditional writes implement the Compare-and-Swap pattern.

```text
Read Value

↓

Compare

↓

Same?

↓

Swap

↓

Done
```

CAS is widely used in distributed databases.

---

# Idempotency

Consider a payment API.

Client retries due to timeout.

Without conditions:

```text
Payment

↓

Retry

↓

Duplicate Payment ❌
```

With conditions:

```python
ConditionExpression=
"attribute_not_exists(payment_id)"
```

Only one payment is recorded.

---

# Reservation Pattern

Inventory example.

```text
Stock = 1

↓

Two Users Buy

↓

Condition

Stock > 0

↓

Only One Success
```

---

# Conditional Counters

Example:

```python
UpdateExpression=
"SET quantity = quantity - :one"

ConditionExpression=
"quantity > :zero"
```

Inventory never becomes negative.

---

# Error Handling

Conditional failures raise:

```python
from botocore.exceptions import ClientError

try:
    table.put_item(...)
except ClientError as e:

    if e.response["Error"]["Code"] == \
        "ConditionalCheckFailedException":

        print("Condition failed")
```

Treat this as an expected business outcome, not necessarily a system failure.

---

# Production Architecture

```text
               Client

                  │

                  ▼

            FastAPI Service

                  │

                  ▼

          Repository Layer

                  │

                  ▼

        Conditional Write

                  │

                  ▼

          Amazon DynamoDB
```

Business rules remain close to the data.

---

# Performance Considerations

Conditional writes:

- Require one write request.
- Are evaluated server-side.
- Eliminate many race conditions.
- Reduce application complexity.
- Scale better than distributed locks.

---

# Security Best Practices

- Validate incoming requests before issuing conditional writes.
- Log failed conditions for auditing.
- Use least-privilege IAM permissions.
- Avoid exposing internal condition logic through public APIs.
- Combine conditional writes with idempotency keys for financial or payment systems.

---

# Best Practices

- Always use conditional writes for record creation.
- Use optimistic locking for concurrent updates.
- Prevent duplicate API requests using idempotency keys.
- Handle `ConditionalCheckFailedException` gracefully.
- Keep business rules inside the repository or data access layer.

---

# Common Mistakes

## Blind Overwrites

Poor:

```python
table.put_item(Item=item)
```

Better:

```python
ConditionExpression=
"attribute_not_exists(order_id)"
```

---

## Treating Condition Failures as System Errors

A failed condition often means the business rule worked correctly.

Example:

```text
Seat Already Reserved

↓

Condition Failed

↓

Expected Result
```

---

## Ignoring Concurrency

Without version checks:

```text
User A Update

↓

User B Update

↓

Lost Update
```

Use optimistic locking instead.

---

## Implementing Locks in the Application

Avoid external locking mechanisms when a simple conditional write can enforce the same business rule atomically.

---

# Interview Notes

A common interview question is:

> **What are Conditional Writes in DynamoDB?**

Conditional writes allow `PutItem`, `UpdateItem`, and `DeleteItem` operations to execute only if a specified condition evaluates to true. They help enforce business rules and prevent race conditions.

---

Another common question is:

> **How do you prevent duplicate records in DynamoDB?**

Use a `ConditionExpression` with `attribute_not_exists(partition_key)` during `PutItem`. If the item already exists, DynamoDB throws a `ConditionalCheckFailedException`.

---

Another common question is:

> **What is Optimistic Locking?**

Optimistic locking uses a version attribute to detect concurrent updates. An update succeeds only if the stored version matches the expected version, preventing lost updates.

---

Another common question is:

> **Why are Conditional Writes preferred over distributed locks?**

Conditional writes are evaluated atomically within DynamoDB, eliminating the need for external lock management while providing better scalability, lower latency, and simpler application architecture.

---

# Key Takeaways

- Conditional writes execute only when specified conditions evaluate to true.
- `ConditionExpression` is supported by `PutItem`, `UpdateItem`, and `DeleteItem`.
- `attribute_not_exists()` is commonly used to prevent duplicate records.
- Optimistic locking with version numbers prevents lost updates in concurrent systems.
- Conditional writes are a fundamental building block for implementing idempotency, enforcing business rules, and maintaining data consistency in production DynamoDB applications.