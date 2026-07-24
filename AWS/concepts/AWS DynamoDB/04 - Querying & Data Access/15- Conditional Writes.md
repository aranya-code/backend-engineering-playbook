# 15 - Conditional Writes

## Overview

A **Conditional Write** is a write operation that is executed **only if one or more specified conditions are satisfied**.

Instead of blindly writing data, DynamoDB first evaluates a condition against the current item. If the condition evaluates to **true**, the write succeeds. If it evaluates to **false**, the write fails and no data is modified.

Conditional writes are one of the most powerful features of DynamoDB because they allow applications to implement **optimistic concurrency control**, **business rule validation**, and **idempotent operations** without requiring distributed locks.

Typical use cases include:

- Preventing duplicate records
- Optimistic locking
- Inventory management
- Payment processing
- Reservation systems
- User registration
- Leaderboards
- Financial transactions

---

# Why Conditional Writes Exist

Consider an online shopping application.

Current inventory:

```text
Laptop

Stock = 1
```

Two customers purchase the laptop simultaneously.

Without conditional writes:

```text
Customer A

↓

Update Stock = 0

──────────────

Customer B

↓

Update Stock = 0
```

Result:

```text
Two Orders

One Product
```

Overselling occurs.

With conditional writes:

```text
Condition

Stock > 0

↓

If True

↓

Update Stock

Else

Reject Write
```

Only one purchase succeeds.

---

# Internal Workflow

```text
                Application

                      │

                Write Request

                      │

          Evaluate Condition

                      │

         ┌────────────┴────────────┐

         ▼                         ▼

   Condition True           Condition False

         │                         │

         ▼                         ▼

   Execute Write           Reject Write

         │

         ▼

     Return Success
```

The condition is evaluated **atomically** by DynamoDB before the write is applied.

---

# Supported Operations

Conditional expressions can be used with:

- PutItem
- UpdateItem
- DeleteItem
- TransactWriteItems

They cannot be used with:

- BatchWriteItem

---

# Condition Expressions

A condition expression evaluates one or more conditions before executing a write.

Examples include:

```text
attribute_exists()
```

```text
attribute_not_exists()
```

```text
Stock > 0
```

```text
Version = 5
```

```text
Status = 'ACTIVE'
```

---

# Preventing Duplicate Records

Suppose usernames must be unique.

Without a condition:

```text
Create User

↓

User Already Exists

↓

Overwrite
```

With:

```text
attribute_not_exists(UserID)
```

Workflow:

```text
User Exists?

↓

No

↓

Create User

Yes

↓

Reject Write
```

This guarantees uniqueness.

---

# Optimistic Locking

Applications often maintain a version number.

Current item:

```text
Version = 7
```

Application reads:

```text
Version = 7
```

Update request:

```text
Condition

Version = 7

↓

Update

Version = 8
```

If another application already updated the record:

```text
Version = 8
```

The condition fails.

This prevents lost updates.

---

# Inventory Management

Current stock:

```text
Stock = 5
```

Condition:

```text
Stock >= QuantityRequested
```

Workflow:

```text
Customer Orders

3 Items

↓

Stock = 5

↓

Condition True

↓

Stock = 2
```

If stock becomes:

```text
Stock = 2
```

Request:

```text
Buy 3
```

Condition fails.

---

# Preventing Status Changes

Suppose only active users can be modified.

Condition:

```text
Status = ACTIVE
```

Workflow:

```text
Update Email

↓

Status ACTIVE?

↓

Yes

↓

Update

No

↓

Reject
```

Business rules are enforced inside DynamoDB.

---

# Idempotent Operations

Suppose a payment request has an ID.

Current table:

```text
Payment123
```

Before creating:

```text
attribute_not_exists(PaymentID)
```

If the payment already exists:

```text
Duplicate Request

↓

Rejected
```

This prevents duplicate processing during retries.

---

# Conditional Delete

Delete an order only if:

```text
Status = PENDING
```

Workflow:

```text
Delete Request

↓

Pending?

↓

Yes

↓

Delete

No

↓

Reject
```

Completed orders remain protected.

---

# Conditional Update

Example:

Current balance:

```text
100
```

Withdraw:

```text
80
```

Condition:

```text
Balance >= 80
```

If true:

```text
Balance = 20
```

If false:

```text
Insufficient Funds
```

No application-side locking is required.

---

# Multiple Conditions

Conditions may be combined.

Example:

```text
Stock > 0

AND

Status = ACTIVE
```

Or:

```text
Role = Admin

OR

Owner = User
```

Logical operators:

- AND
- OR
- NOT

are fully supported.

---

# Failure Behavior

When a condition fails:

```text
Write

↓

Not Executed

↓

ConditionalCheckFailedException
```

No data is modified.

Applications should catch this exception and respond appropriately.

---

# Conditional Writes vs Ordinary Writes

| Feature | Ordinary Write | Conditional Write |
|----------|----------------|-------------------|
| Always Executes | ✅ | ❌ |
| Validates Business Rules | ❌ | ✅ |
| Prevents Lost Updates | ❌ | ✅ |
| Prevents Duplicate Records | ❌ | ✅ |
| Atomic Validation | ❌ | ✅ |

---

# Conditional Writes vs Transactions

| Feature | Conditional Write | Transaction |
|----------|-------------------|-------------|
| One Item | ✅ | ✅ |
| Multiple Items | ❌ | ✅ |
| Business Rule Validation | ✅ | ✅ |
| Atomic Across Tables | ❌ | ✅ |
| Performance | Faster | Slightly Slower |

---

# Real-World Example — Banking

Withdrawal:

```text
Balance = 1000
```

Withdraw:

```text
1500
```

Condition:

```text
Balance >= 1500
```

Fails.

Balance remains unchanged.

---

# Real-World Example — Airline Booking

Seat:

```text
Available
```

Condition:

```text
Status = AVAILABLE
```

Customer A:

```text
Reserve Seat

↓

Success
```

Customer B:

```text
Reserve Same Seat

↓

Condition Failed
```

No double booking occurs.

---

# Real-World Example — User Registration

Create account:

```text
Username

johnsmith
```

Condition:

```text
attribute_not_exists(Username)
```

Duplicate usernames are automatically rejected.

---

# Real-World Example — Inventory Reservation

Warehouse:

```text
Stock = 20
```

Reserve:

```text
15 Units
```

Condition:

```text
Stock >= 15
```

Inventory never becomes negative.

---

# Capacity Consumption

Conditional writes consume WCUs similarly to ordinary writes.

However, DynamoDB must first evaluate the condition before applying the write.

If the condition fails:

- No write occurs
- No item is modified

The request still consumes capacity for evaluating the condition.

---

# Best Practices

- Use conditional writes to enforce business rules.
- Prefer optimistic locking over distributed locking.
- Always handle `ConditionalCheckFailedException`.
- Keep condition expressions simple.
- Use transactions only when multiple items must be updated atomically.
- Design idempotent APIs using `attribute_not_exists()`.

---

# Common Mistakes

## Ignoring Conditional Failures

Applications should never assume every conditional write succeeds.

Always handle:

```text
ConditionalCheckFailedException
```

---

## Replacing Optimistic Locking

Some developers overwrite records directly.

Better:

```text
Version Check

↓

Update
```

This prevents lost updates.

---

## Using Transactions Unnecessarily

If only one item is being modified, a conditional write is usually simpler and faster than a transaction.

---

## Overly Complex Conditions

Very large condition expressions make application logic harder to understand and maintain.

Prefer simple, business-focused validations.

---

# Architecture Perspective

```text
                Client Request

                      │

             Conditional Write

                      │

            Evaluate Condition

         ┌────────────┴────────────┐

         ▼                         ▼

   Condition True           Condition False

         │                         │

         ▼                         ▼

    Persist Change          Reject Request

         │

         ▼

     Return Success
```

Unlike application-side validation, the condition is evaluated atomically within DynamoDB, eliminating race conditions between the validation and the write.

---

# Production Considerations

Conditional writes are heavily used in distributed systems because they provide lightweight concurrency control without introducing external locking mechanisms.

Common production workloads include:

- User registration
- Shopping carts
- Financial transactions
- Inventory reservation
- Payment processing
- API idempotency
- Optimistic locking
- Distributed job scheduling

Most high-scale DynamoDB applications rely extensively on conditional writes to maintain data integrity while preserving throughput.

---

# Interview Notes

A common interview question is:

> **What is a conditional write in DynamoDB?**

A conditional write is a write operation that executes only if a specified condition evaluates to true. If the condition fails, the write is rejected and no data is modified.

Another common question is:

> **How do conditional writes prevent race conditions?**

The condition evaluation and the write are performed atomically by DynamoDB, preventing another client from modifying the item between validation and the write.

Another common question is:

> **What exception is returned when a condition fails?**

`ConditionalCheckFailedException`.

Another common question is:

> **When should you use a conditional write instead of a transaction?**

Use a conditional write when validating and modifying a single item. Use `TransactWriteItems` when multiple related items must be updated atomically.

---

# Key Takeaways

- Conditional writes execute only when specified conditions are satisfied.
- DynamoDB evaluates the condition and performs the write atomically.
- They are commonly used to prevent duplicate records, enforce business rules, implement optimistic locking, and build idempotent APIs.
- Failed conditions do not modify data and return a `ConditionalCheckFailedException`.
- Conditional writes provide lightweight concurrency control and are significantly more efficient than transactions for single-item updates.
```