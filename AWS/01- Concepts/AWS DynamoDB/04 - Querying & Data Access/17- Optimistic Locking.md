# 17 - Optimistic Locking

## Overview

**Optimistic Locking** is a concurrency control technique that prevents multiple clients from accidentally overwriting each other's changes.

Instead of locking an item while it is being modified, DynamoDB assumes that write conflicts are relatively rare. Before updating an item, the application verifies that the item has **not changed since it was last read**.

This is typically implemented using:

- Version numbers
- Timestamps
- Condition Expressions

Optimistic locking is widely used in high-concurrency distributed systems because it provides data consistency **without introducing distributed locks**.

Common use cases include:

- User profile updates
- Banking systems
- Inventory management
- Collaborative editing
- Order processing
- Configuration management

---

# Why Optimistic Locking Exists

Consider two users editing the same profile.

Current record:

```text
Version = 5

Name = Alice
```

User A:

```text
Read Version = 5
```

User B:

```text
Read Version = 5
```

Both users modify the record.

Without optimistic locking:

```text
User A

↓

Update

↓

Success

──────────────

User B

↓

Update

↓

Success
```

User A's changes are lost.

This is called a **Lost Update**.

---

# Optimistic Locking Workflow

Using a version attribute:

```text
Current Version = 5
```

User A:

```text
Condition

Version = 5

↓

Update

↓

Version = 6
```

User B:

```text
Condition

Version = 5

↓

Fails

↓

Version Already Changed
```

The second update is rejected.

---

# Internal Architecture

```text
                Application

                      │

                  Read Item

                      │

                Store Version

                      │

               Update Request

                      │

          Condition Version = X

                      │

        ┌─────────────┴─────────────┐

        ▼                           ▼

  Version Matches            Version Changed

        │                           │

        ▼                           ▼

   Apply Update              Reject Update

        │

        ▼

 Increase Version Number
```

The version check and update occur atomically inside DynamoDB.

---

# Version Numbers

Optimistic locking commonly uses a numeric version attribute.

Example:

```text
Version = 1
```

After update:

```text
Version = 2
```

Every successful update increments the version.

---

# Timestamp-Based Locking

Some applications use timestamps instead of version numbers.

Example:

```text
LastUpdated

2026-07-24T15:30:10Z
```

Before updating:

```text
Condition

LastUpdated = OriginalTimestamp
```

If another update occurred:

```text
Timestamp Changed

↓

Reject Update
```

Version numbers are generally preferred because they avoid issues with clock synchronization.

---

# Optimistic Locking Using Condition Expressions

Optimistic locking relies on a conditional update.

Example:

```text
Current Version = 8
```

Condition:

```text
Version = 8
```

Update:

```text
Set Version = 9
```

If another client has already updated the item:

```text
Version = 9

↓

Condition Fails
```

No overwrite occurs.

---

# Failure Behavior

When the version check fails:

```text
Update

↓

Rejected

↓

ConditionalCheckFailedException
```

The application should:

- Reload the latest item
- Resolve conflicts if necessary
- Retry the update

---

# Conflict Resolution

Applications can handle conflicts in different ways.

## Retry Automatically

```text
Read Latest Item

↓

Apply Changes Again

↓

Retry Update
```

Useful for simple counters or background jobs.

---

## Ask the User

Collaborative applications often notify users.

```text
Another User Updated This Record

↓

Reload Latest Version
```

Useful for documents or profile editing.

---

## Merge Changes

If updates affect different attributes:

```text
User A

Changed Email

──────────────

User B

Changed Phone
```

The application may merge both updates before retrying.

---

# Optimistic Locking vs Pessimistic Locking

| Feature | Optimistic Locking | Pessimistic Locking |
|----------|-------------------|---------------------|
| Locks Records | ❌ | ✅ |
| High Performance | ✅ | ❌ |
| Suitable for Distributed Systems | ✅ | Difficult |
| Conflict Detection | During Write | Before Write |
| Scalability | Excellent | Limited |

DynamoDB is designed for optimistic concurrency rather than database locks.

---

# Optimistic Locking vs Transactions

| Feature | Optimistic Locking | Transaction |
|----------|-------------------|-------------|
| Single Item | ✅ | ✅ |
| Multiple Items | ❌ | ✅ |
| Lightweight | ✅ | ❌ |
| ACID Across Tables | ❌ | ✅ |

For updates to a single item, optimistic locking is usually the preferred approach.

---

# Optimistic Locking vs Conditional Writes

Optimistic locking is **built on top of** conditional writes.

Relationship:

```text
Conditional Write

↓

Version Check

↓

Optimistic Locking
```

Every optimistic locking implementation uses a condition expression, but not every conditional write is optimistic locking.

---

# Real-World Example — Banking

Current balance:

```text
Version = 42
```

Two ATMs attempt to update the account.

ATM A:

```text
Version = 42

↓

Update

↓

Version = 43
```

ATM B:

```text
Version = 42

↓

Rejected
```

No transaction is overwritten.

---

# Real-World Example — User Profiles

Current profile:

```text
Version = 12
```

User edits:

```text
Email
```

Meanwhile another device edits:

```text
Phone Number
```

Version mismatch:

```text
Update Rejected

↓

Reload Profile
```

The application avoids losing data.

---

# Real-World Example — Inventory

Current item:

```text
Version = 100

Stock = 15
```

Warehouse system updates inventory.

If another process already modified stock:

```text
Condition Failed

↓

Retry
```

Inventory remains consistent.

---

# Real-World Example — Collaborative Editing

Two editors modify the same document.

Workflow:

```text
Editor A

↓

Save

↓

Version = 8

──────────────

Editor B

↓

Save

↓

Version Conflict
```

The editor can prompt the user to merge changes.

---

# Capacity Consumption

Optimistic locking uses:

- `UpdateItem`
- Condition Expressions

Capacity usage is similar to a conditional update.

When the version check fails:

- The write is not applied.
- Capacity is still consumed to evaluate the condition.

---

# Performance Considerations

Optimistic locking performs well because:

- No locks are held.
- Updates remain highly scalable.
- Only conflicting writes fail.

However, applications with extremely frequent concurrent updates may experience increased retry rates.

---

# Best Practices

- Maintain a dedicated version attribute.
- Increment the version after every successful update.
- Catch `ConditionalCheckFailedException`.
- Retry only after reading the latest version.
- Use optimistic locking for single-item concurrency.
- Use transactions only for multi-item consistency.

---

# Common Mistakes

## Forgetting to Increment the Version

Incorrect:

```text
Version = 5

↓

Update

↓

Version = 5
```

The version must always be incremented after a successful update.

---

## Ignoring Update Failures

Applications should always handle:

```text
ConditionalCheckFailedException
```

Silently retrying without reloading the latest item may overwrite valid data.

---

## Using Transactions for Single-Item Updates

If only one item is being modified, optimistic locking is usually simpler and more efficient than a transaction.

---

## Sharing Version Numbers Across Items

Each item should maintain its own version attribute.

Never use one version number to control multiple records.

---

# Architecture Perspective

```text
                Client Reads Item

                      │

             Store Version Number

                      │

             Client Sends Update

                      │

          Version Condition Check

         ┌────────────┴────────────┐

         ▼                         ▼

   Version Matches          Version Changed

         │                         │

         ▼                         ▼

  Apply Update              Reject Update

         │

         ▼

 Increment Version
```

Optimistic locking ensures that no update silently overwrites another update.

---

# Production Considerations

Optimistic locking is the preferred concurrency mechanism for most DynamoDB applications because it avoids the complexity and scalability limitations of distributed locks.

It is commonly used in:

- Banking systems
- Inventory management
- Customer profiles
- Shopping carts
- Order processing
- Configuration services
- Workflow engines
- Content management systems

AWS SDKs such as the **Java Enhanced Client** and **DynamoDBMapper** provide built-in support for optimistic locking using version attributes, simplifying implementation.

---

# Interview Notes

A common interview question is:

> **What is optimistic locking?**

Optimistic locking is a concurrency control mechanism that prevents lost updates by ensuring an item has not changed since it was last read before allowing an update.

Another common question is:

> **How is optimistic locking implemented in DynamoDB?**

It is implemented using a version attribute (or timestamp) combined with a Condition Expression. The update succeeds only if the stored version matches the expected version.

Another common question is:

> **What happens when two clients update the same item simultaneously?**

The first update succeeds and increments the version. The second update fails with a `ConditionalCheckFailedException` because its expected version no longer matches.

Another common question is:

> **When should optimistic locking be preferred over transactions?**

For single-item updates where preventing lost updates is the primary concern. Transactions should be reserved for atomic updates involving multiple related items.

---

# Key Takeaways

- Optimistic locking prevents lost updates without using database locks.
- It is typically implemented using a version attribute and Condition Expressions.
- The version check and update are performed atomically by DynamoDB.
- Conflicting updates fail with `ConditionalCheckFailedException`.
- Optimistic locking is lightweight, highly scalable, and ideal for distributed systems.
- For multi-item atomic operations, use `TransactWriteItems` instead.