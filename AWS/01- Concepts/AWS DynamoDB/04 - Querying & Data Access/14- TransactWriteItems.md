# 14 - TransactWriteItems

## Overview

`TransactWriteItems` is DynamoDB's transactional write operation that allows multiple write operations to execute **atomically** across one or more tables.

Unlike `BatchWriteItem`, which executes writes independently, `TransactWriteItems` guarantees that:

- Either **every operation succeeds**
- Or **every operation fails**

There is **no partial success**.

This makes it suitable for workloads that require ACID transaction guarantees, such as:

- Banking systems
- Financial ledgers
- Inventory management
- Reservation systems
- Order processing
- Payment processing

---

# Why TransactWriteItems Exists

Consider an online banking application.

A customer transfers:

```text
$500

From

Account A

To

Account B
```

Without transactions:

```text
Update Account A

↓

Success

↓

Update Account B

↓

Failure
```

Result:

```text
Money Lost
```

The system becomes inconsistent.

With `TransactWriteItems`:

```text
Begin Transaction

↓

Debit Account A

↓

Credit Account B

↓

Commit
```

If either operation fails:

```text
Rollback

↓

No Changes
```

---

# ACID Properties

DynamoDB transactions provide ACID guarantees.

| Property | Meaning |
|----------|----------|
| Atomicity | All operations succeed or none do |
| Consistency | Data remains valid after the transaction |
| Isolation | Concurrent transactions do not interfere |
| Durability | Committed changes survive failures |

---

# Internal Architecture

```text
                 Application

                       │

                       ▼

            TransactWriteItems

                       │

              Begin Transaction

                       │

      ┌────────────┼────────────┐

      ▼            ▼            ▼

   Write A     Update B     Delete C

      └────────────┼────────────┘

                   ▼

        Validate All Operations

                   ▼

        Commit or Rollback Entire Transaction
```

---

# Supported Operations

A transaction may contain:

- Put
- Update
- Delete
- ConditionCheck

Example:

```text
Put Customer

↓

Update Account

↓

Delete Session

↓

ConditionCheck Inventory
```

All execute as one transaction.

---

# Maximum Operations

A single transaction supports:

```text
100 Operations
```

across one or more tables.

---

# Multiple Tables

Transactions are not limited to a single table.

Example:

```text
Customers

Orders

Payments

Inventory
```

One transaction can modify all four.

---

# Condition Checks

Transactions support validation before writing.

Example:

```text
Inventory > 0
```

If:

```text
False
```

Entire transaction fails.

Example workflow:

```text
Check Stock

↓

Stock Available?

↓

Yes

↓

Continue Transaction

No

↓

Rollback
```

---

# Transaction Commit

Workflow:

```text
Begin Transaction

↓

Execute Operations

↓

Validate Conditions

↓

Commit

↓

Success
```

---

# Transaction Rollback

If any operation fails:

```text
Begin Transaction

↓

Write A

↓

Write B

↓

Condition Failed

↓

Rollback

↓

No Changes Persist
```

This guarantees consistency.

---

# Capacity Consumption

Transactions consume more capacity than ordinary writes.

Reasons:

- Internal coordination
- Distributed consensus
- Atomic commit protocol

Therefore:

```text
TransactWriteItems

>

BatchWriteItem
```

for latency and resource usage.

---

# Transaction Conflicts

Two concurrent transactions modifying the same item may conflict.

Example:

```text
Transaction A

↓

Update Account
```

```text
Transaction B

↓

Update Same Account
```

One transaction may fail with a transaction conflict, allowing the application to retry safely.

---

# TransactWriteItems vs BatchWriteItem

| Feature | BatchWriteItem | TransactWriteItems |
|----------|----------------|--------------------|
| Atomic | ❌ | ✅ |
| Rollback | ❌ | ✅ |
| Conditions | ❌ | ✅ |
| Multiple Tables | ✅ | ✅ |
| Performance | Faster | Slightly Slower |

---

# TransactWriteItems vs UpdateItem

| Feature | UpdateItem | TransactWriteItems |
|----------|------------|--------------------|
| One Item | ✅ | ❌ |
| Multiple Items | ❌ | ✅ |
| Atomic Across Tables | ❌ | ✅ |
| Condition Checks | ✅ | ✅ |

---

# TransactWriteItems vs BatchGetItem

| Feature | BatchGetItem | TransactWriteItems |
|----------|--------------|--------------------|
| Reads | ✅ | ❌ |
| Writes | ❌ | ✅ |
| Atomic | ❌ | ✅ |
| Multiple Tables | ✅ | ✅ |

---

# Real-World Example — Banking

Transfer:

```text
Debit

↓

Credit
```

Workflow:

```text
Update Account A

↓

Update Account B

↓

Commit
```

If either update fails:

```text
Rollback Entire Transaction
```

No money disappears.

---

# Real-World Example — E-commerce

Customer purchases:

```text
Laptop
```

Transaction:

```text
Decrease Inventory

↓

Create Order

↓

Record Payment

↓

Create Shipment
```

If shipment creation fails:

```text
Rollback Everything
```

Inventory remains accurate.

---

# Real-World Example — Airline Reservation

Booking:

```text
Reserve Seat

↓

Charge Credit Card

↓

Issue Ticket
```

Transaction:

```text
Seat Reserved?

↓

Yes

↓

Payment Success?

↓

Yes

↓

Commit

No

↓

Rollback
```

No double booking occurs.

---

# Real-World Example — Healthcare

Patient Admission:

```text
Create Patient

↓

Assign Bed

↓

Update Doctor Schedule

↓

Reserve Equipment
```

All changes succeed together or fail together.

---

# Performance Considerations

Transactions introduce:

- Additional network coordination
- Internal locking
- Serializable isolation
- Commit validation

Therefore:

```text
Higher Latency

than

BatchWriteItem
```

Use transactions only when consistency requirements justify the overhead.

---

# Best Practices

- Use transactions only for related business operations.
- Keep transactions as small as possible.
- Handle transaction conflicts with retries.
- Combine Condition Checks with writes.
- Avoid unnecessary cross-table transactions.
- Monitor transaction latency and failures in CloudWatch.

---

# Common Mistakes

## Using Transactions for Every Write

Transactions are more expensive than ordinary writes.

Simple operations should continue using:

```text
PutItem

UpdateItem

DeleteItem
```

---

## Large Transactions

Although DynamoDB supports up to 100 operations, very large transactions increase:

- Latency
- Conflict probability
- Retry costs

Smaller transactions generally perform better.

---

## Ignoring Transaction Conflicts

Concurrent writes can generate transaction conflicts.

Applications should retry failed transactions using exponential backoff.

---

## Mixing Unrelated Operations

Do not place unrelated business operations inside the same transaction.

Keep transactional boundaries aligned with business requirements.

---

# Architecture Perspective

```text
                  Application

                        │

               TransactWriteItems

                        │

             Begin Transaction

                        │

        ┌──────────┼──────────┐

        ▼          ▼          ▼

     Write A   Update B   Delete C

        └──────────┼──────────┘

                   ▼

         Validate Conditions

                   ▼

        Commit or Rollback

                   ▼

              Success
```

Every write succeeds together or fails together.

---

# Production Considerations

`TransactWriteItems` is commonly used in enterprise systems that require strong consistency.

Typical workloads include:

- Banking transfers
- Financial ledgers
- Inventory reservations
- Payment processing
- Order fulfillment
- Healthcare workflows
- Airline booking systems

Most CRUD APIs **do not require transactions**. Using ordinary `PutItem`, `UpdateItem`, or `BatchWriteItem` generally provides better performance.

Use transactions only when multiple related writes must succeed or fail as a single unit.

---

# Interview Notes

A common interview question is:

> **What is the difference between BatchWriteItem and TransactWriteItems?**

BatchWriteItem groups multiple write operations for efficiency but allows partial success. TransactWriteItems provides atomic execution, ensuring that either all operations succeed or all fail.

Another common question is:

> **When should you use TransactWriteItems?**

When multiple related write operations must be committed together, such as financial transfers, inventory updates, or order processing.

Another common question is:

> **Can TransactWriteItems span multiple DynamoDB tables?**

Yes. A single transaction can include operations across multiple tables within the same AWS account and Region.

Another common question is:

> **Why are DynamoDB transactions slower than ordinary writes?**

Transactions require additional coordination, condition validation, and an atomic commit protocol to guarantee ACID properties.

---

# Key Takeaways

- `TransactWriteItems` provides **ACID-compliant atomic writes** across one or more DynamoDB tables.
- It supports up to **100 operations** in a single transaction.
- Supported operations include `Put`, `Update`, `Delete`, and `ConditionCheck`.
- If any operation fails, the **entire transaction is rolled back**, ensuring data consistency.
- Transactions introduce additional latency and capacity overhead compared to ordinary writes.
- Use `TransactWriteItems` for business-critical workflows where consistency is more important than maximum throughput.