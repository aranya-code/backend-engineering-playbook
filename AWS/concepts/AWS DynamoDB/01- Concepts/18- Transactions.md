# 18 - Transactions

## Overview

One of the biggest criticisms of early NoSQL databases was the lack of **ACID transactions**.

Traditional relational databases like PostgreSQL, MySQL, and Oracle allow multiple operations to succeed or fail together as a single unit.

For example:

- Debit one bank account
- Credit another account
- Record the transaction history

Either **all operations succeed**, or **none of them do**.

Early versions of DynamoDB did not support multi-item transactions because they were optimized for massive scalability and low latency.

Today, DynamoDB supports **ACID Transactions**, allowing multiple operations across one or more tables to execute atomically while preserving consistency.

This enables developers to build financial systems, inventory management systems, booking platforms, and other applications requiring strict data integrity.

---

# Why Transactions Exist

Consider a banking application.

Customer A transfers:

```text
$500
```

to Customer B.

Without transactions:

```text
Step 1

↓

Debit Customer A

✓ Success
```

```text
Step 2

↓

Credit Customer B

❌ Failed
```

Result:

```text
Money Disappears
```

The database is now inconsistent.

With transactions:

```text
Debit

+

Credit

↓

Commit Together
```

If any operation fails:

```text
Rollback Everything
```

Consistency is preserved.

---

# ACID Properties

Transactions in DynamoDB follow the traditional ACID model.

## Atomicity

Either:

```text
All Operations

↓

Success
```

or

```text
None
```

There is no partial completion.

---

## Consistency

The database always moves from one valid state to another.

Example:

```text
Inventory

10 Units

↓

Purchase

↓

9 Units
```

The inventory never becomes negative because of partially completed operations.

---

## Isolation

Concurrent transactions do not interfere with each other.

Each transaction behaves as though it is executing alone.

---

## Durability

Once a transaction commits successfully:

```text
Data

↓

Persisted
```

Even if servers fail afterward.

---

# Transaction APIs

DynamoDB provides two transaction APIs.

## TransactWriteItems

Executes multiple write operations atomically.

Supports:

- PutItem
- UpdateItem
- DeleteItem
- ConditionCheck

---

## TransactGetItems

Retrieves multiple items consistently within a single transaction.

Useful when multiple related items must be read together.

---

# Transaction Workflow

```text
Application

↓

Transaction Request

↓

Validate Conditions

↓

Lock Resources Internally

↓

Execute Operations

↓

Commit

↓

Return Success
```

If validation fails:

```text
Rollback

↓

No Changes Persist
```

---

# Example 1 — Bank Transfer

Before transaction:

```text
Customer A

$2000
```

```text
Customer B

$500
```

Transaction:

```text
Debit A

$500

+

Credit B

$500
```

After:

```text
Customer A

$1500
```

```text
Customer B

$1000
```

If either operation fails:

```text
Both Cancelled
```

---

# Example 2 — Inventory Management

Customer purchases:

```text
Laptop
```

Inventory:

```text
Stock

5 Units
```

Transaction:

```text
Reduce Inventory

+

Create Order

+

Record Payment
```

Either:

```text
All Three Succeed
```

or

```text
None Execute
```

---

# Example 3 — Airline Seat Booking

Without transactions:

```text
Reserve Seat

↓

Payment Failed
```

Now:

```text
Seat Reserved

No Payment
```

Another customer cannot book the seat.

With transactions:

```text
Reserve Seat

+

Charge Card

↓

Commit Together
```

No inconsistent booking occurs.

---

# Condition Checks

Transactions can include validation rules.

Example:

```text
Inventory

>

0
```

Only proceed if stock remains.

If:

```text
Inventory = 0
```

Entire transaction fails automatically.

This prevents overselling.

---

# Multiple Tables

Transactions are not limited to one table.

Example:

```text
Orders Table

↓

Update
```

```text
Inventory Table

↓

Update
```

```text
Payments Table

↓

Insert
```

All three operations succeed or fail together.

---

# Transaction Isolation

Suppose two customers attempt to purchase the last product simultaneously.

Without transactions:

```text
Customer A

↓

Purchase
```

```text
Customer B

↓

Purchase
```

Both succeed.

Inventory becomes:

```text
-1
```

With transactions:

One succeeds.

The other receives:

```text
TransactionCanceledException
```

Inventory remains correct.

---

# Optimistic Concurrency Control

Many applications combine transactions with version numbers.

Example:

```text
Version

5
```

Update only if:

```text
Version = 5
```

Otherwise:

```text
Reject Update
```

This prevents lost updates caused by concurrent writers.

---

# Transaction Limits

Transactions are powerful but not unlimited.

Current limits include:

- Up to **100 operations** per transaction.
- Aggregate request size of **4 MB**.
- Cannot reference the same item multiple times with conflicting operations in one transaction.

Architects should avoid designing extremely large transactions.

---

# Performance Considerations

Transactions require additional coordination.

Compared to normal writes:

```text
PutItem

↓

Fast
```

Transaction:

```text
Validate

↓

Coordinate

↓

Commit

↓

Return
```

As a result:

- Higher latency
- Higher throughput consumption
- Greater internal complexity

Use transactions only when atomicity is required.

---

# Transactions vs Batch Operations

These features are often confused.

| Feature | Transactions | Batch Operations |
|----------|--------------|------------------|
| Atomic | ✅ Yes | ❌ No |
| Rollback | ✅ Yes | ❌ No |
| Partial Success Possible | ❌ | ✅ |
| ACID Guarantees | ✅ | ❌ |
| Performance | Lower | Higher |

Batch operations optimize throughput.

Transactions guarantee consistency.

---

# Transactions vs Conditional Writes

Conditional writes protect a **single item**.

Example:

```text
Update Balance

Only If

Version = 5
```

Transactions coordinate **multiple items**.

```text
Account A

+

Account B

+

Ledger
```

Choose the simplest mechanism that satisfies the business requirement.

---

# Real-World Example

An online retailer processes an order.

Transaction:

```text
Create Order

+

Reduce Inventory

+

Record Payment

+

Create Shipment
```

If payment fails:

```text
Everything Rolls Back
```

The customer never sees a partially completed order.

---

# Best Practices

- Keep transactions as small as possible.
- Use transactions only when atomicity is required.
- Prefer conditional writes for single-item updates.
- Design applications to retry failed transactions safely.
- Monitor transaction cancellation metrics.
- Avoid long-running business workflows inside transactions.

---

# Common Mistakes

## Using Transactions Everywhere

Many DynamoDB workloads do not require ACID guarantees.

Unnecessary transactions increase cost and latency.

---

## Confusing Batch Operations with Transactions

Batch operations improve efficiency.

They do not guarantee all-or-nothing execution.

---

## Ignoring Retry Logic

Transactions may fail due to contention or transient issues.

Applications should implement retries with exponential backoff.

---

## Creating Large Transactions

Very large transactions increase contention and reduce throughput.

Smaller transactions are easier to scale.

---

# Architecture Perspective

A typical production workflow:

```text
Client

↓

API Gateway

↓

Lambda / ECS

↓

TransactWriteItems

↓

Orders Table

Inventory Table

Payments Table

↓

Commit
```

The transaction ensures all related business entities remain synchronized.

---

# Interview Notes

A common interview question is:

> **When should you use DynamoDB Transactions instead of conditional writes?**

Use **conditional writes** when validating or updating a single item.

Use **transactions** when multiple items—or multiple tables—must be updated atomically.

For example:

- Updating one account balance → Conditional Write
- Transferring money between two accounts → Transaction

Another common question is:

> **Why shouldn't every write be a transaction?**

Because transactions introduce additional coordination, consume more capacity, increase latency, and reduce throughput. DynamoDB is optimized for simple, independent operations. Transactions should be reserved for business operations where data consistency across multiple items is essential.

---

# Key Takeaways

- DynamoDB Transactions provide full ACID guarantees across multiple items and tables.
- Transactions execute all operations atomically—either everything succeeds or everything rolls back.
- `TransactWriteItems` performs atomic writes, while `TransactGetItems` performs consistent multi-item reads.
- Transactions support condition checks to enforce business rules.
- They incur higher latency and throughput costs than standard operations.
- Conditional writes are often sufficient for single-item concurrency control.
- Transactions are best suited for financial systems, inventory management, booking systems, and other workflows requiring strict consistency.