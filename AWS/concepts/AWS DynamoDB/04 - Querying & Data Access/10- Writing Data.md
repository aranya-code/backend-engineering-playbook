# 10 - Writing Data

## Overview

Writing data is one of the most critical aspects of designing scalable DynamoDB applications. Unlike traditional relational databases that rely on SQL `INSERT`, `UPDATE`, and `DELETE` statements, DynamoDB provides multiple write APIs, each optimized for a specific use case.

Choosing the appropriate write operation impacts:

- Performance
- Cost
- Data consistency
- Concurrency
- Scalability
- Application reliability

A well-designed DynamoDB application minimizes unnecessary writes while selecting the appropriate write API for each workload.

---

# The DynamoDB Write APIs

DynamoDB provides several write operations.

| API | Purpose |
|------|----------|
| PutItem | Create or completely replace an item |
| UpdateItem | Modify specific attributes of an existing item |
| DeleteItem | Remove an item |
| BatchWriteItem | Perform multiple Put or Delete operations |
| TransactWriteItems | Execute multiple writes atomically |
| Condition Expressions | Write only when conditions are satisfied |
| Atomic Counters | Safely increment or decrement numeric values |

Each operation serves a different purpose.

---

# Choosing the Correct Write Operation

```text
                     Need to Write Data

                             │

          ┌──────────────────┼──────────────────┐

          ▼                                     ▼

    One Item?                           Multiple Items?

          │                                     │

         Yes                                   Yes

          │                                     │

          ▼                                     ▼

 Modify Entire Item?                   Atomic Required?

      │       │                             │       │

     Yes      No                           Yes      No

      │        │                            │        │

      ▼        ▼                            ▼        ▼

 PutItem   UpdateItem             TransactWrite   BatchWrite

          │

          ▼

 Delete?

          │

         Yes

          │

          ▼

      DeleteItem
```

Understanding this decision flow helps developers choose the most efficient API for their workload.

---

# PutItem

`PutItem` creates a new item or completely replaces an existing one.

Example:

```text
User

↓

UserID = 101

Name = Alice

City = Boston
```

If the item already exists:

```text
Entire Item

↓

Replaced
```

Ideal for:

- Creating new records
- Full object replacement
- Import jobs

---

# UpdateItem

`UpdateItem` modifies only selected attributes.

Example:

Current item:

```text
Name = Alice

Age = 30

City = Boston
```

Update:

```text
Age = 31
```

Result:

```text
Name = Alice

Age = 31

City = Boston
```

Only the specified attribute changes.

Ideal for:

- User profile updates
- Status changes
- Inventory updates
- Counters

---

# DeleteItem

Deletes one item using its primary key.

Example:

```text
Delete

UserID = 101
```

The item is permanently removed.

Common use cases:

- Session expiration
- Account deletion
- Soft-delete cleanup
- Administrative operations

---

# BatchWriteItem

Performs multiple writes in one request.

Supports:

- PutItem
- DeleteItem

Does **not** support:

- UpdateItem
- Transactions
- Condition Expressions

Example:

```text
25 Products

↓

BatchWriteItem

↓

Single API Call
```

Ideal for:

- Data migration
- Bulk imports
- ETL pipelines
- Batch cleanup

---

# TransactWriteItems

Executes multiple write operations atomically.

Example:

```text
Debit Account

↓

Credit Account

↓

Create Ledger Entry
```

If any operation fails:

```text
Rollback

↓

Nothing Changes
```

Ideal for:

- Banking
- Financial systems
- Inventory reservations
- Order processing

---

# Condition Expressions

Condition Expressions allow writes only if specified conditions are satisfied.

Example:

```text
Update Inventory

Only If

Stock > 0
```

If the condition fails:

```text
Write Rejected
```

They help prevent:

- Lost updates
- Duplicate records
- Race conditions

---

# Atomic Counters

DynamoDB supports atomic increment and decrement operations.

Example:

```text
Page Views

100

↓

Increment

↓

101
```

No application-side locking is required.

Common uses:

- Likes
- Downloads
- Inventory counts
- View counters

---

# Internal Write Architecture

```text
                 Application

                       │

                 Write Request

                       │

      ┌────────┼───────────┼────────────┐

      ▼        ▼           ▼            ▼

   PutItem  UpdateItem  DeleteItem  Transaction

      └────────┼───────────┼────────────┘

               ▼

       DynamoDB Storage Engine

               ▼

          Persist Changes
```

Every write operation follows a different execution path but ultimately persists data in DynamoDB's distributed storage layer.

---

# Capacity Consumption

Write operations consume **Write Capacity Units (WCUs)**.

| Operation | WCU Consumption |
|------------|-----------------|
| PutItem | Based on item size |
| UpdateItem | Based on new item size |
| DeleteItem | Based on deleted item size |
| BatchWriteItem | Sum of individual writes |
| TransactWriteItems | Higher than ordinary writes |

Larger items consume more WCUs.

---

# SQL Comparison

Relational databases rely on SQL statements such as:

```sql
INSERT INTO Users VALUES (...);

UPDATE Users SET Age = 31;

DELETE FROM Users WHERE UserID = 101;
```

In DynamoDB:

| SQL | DynamoDB |
|------|-----------|
| INSERT | PutItem |
| UPDATE | UpdateItem |
| DELETE | DeleteItem |
| Bulk INSERT | BatchWriteItem |
| Transaction | TransactWriteItems |

DynamoDB separates these operations into dedicated APIs optimized for distributed storage.

---

# Choosing Between Write APIs

| Requirement | Recommended API |
|--------------|-----------------|
| Create one item | PutItem |
| Modify attributes | UpdateItem |
| Delete one item | DeleteItem |
| Bulk insert/delete | BatchWriteItem |
| Atomic business transaction | TransactWriteItems |
| Prevent overwrites | Condition Expressions |
| Increment counters | Atomic Counters |

---

# Production Example — E-commerce

Customer places an order.

Workflow:

```text
Create Order

↓

Update Inventory

↓

Update Loyalty Points

↓

Create Shipment
```

Possible implementation:

- PutItem → Order
- UpdateItem → Inventory
- UpdateItem → Loyalty Points

Or:

```text
TransactWriteItems
```

for guaranteed consistency.

---

# Production Example — Banking

Money transfer:

```text
Debit Savings

↓

Credit Checking

↓

Insert Ledger Record
```

Recommended:

```text
TransactWriteItems
```

Never use BatchWriteItem for financial transfers.

---

# Production Example — IoT

Sensor updates:

```text
Device001

↓

Temperature

↓

Humidity

↓

Battery
```

Only changing values:

```text
UpdateItem
```

Avoid replacing the entire item.

---

# Production Example — Analytics

Nightly import:

```text
CSV

↓

Transform

↓

BatchWriteItem

↓

Repeat
```

Efficient for millions of records.

---

# Best Practices

- Prefer `UpdateItem` when modifying only a few attributes.
- Use `PutItem` only when replacing or creating an item.
- Group bulk operations using `BatchWriteItem`.
- Use `TransactWriteItems` only when atomicity is required.
- Combine Condition Expressions with writes to prevent race conditions.
- Keep item sizes small to reduce WCU consumption.
- Design idempotent write operations for retry safety.

---

# Common Mistakes

## Replacing Entire Items Unnecessarily

Poor:

```text
PutItem

↓

Replace Entire Record

↓

One Attribute Changed
```

Better:

```text
UpdateItem
```

---

## Using BatchWriteItem for Transactions

BatchWriteItem is **not atomic**.

Partial success is possible.

Use:

```text
TransactWriteItems
```

for business-critical operations.

---

## Ignoring Condition Expressions

Concurrent updates can overwrite each other.

Use Condition Expressions or Optimistic Locking to prevent lost updates.

---

## Writing Large Items Frequently

Large items:

- Increase WCUs
- Increase latency
- Increase costs

Store only the attributes that are frequently accessed together.

---

# Architecture Perspective

```text
                  Client Request

                        │

                Determine Write Type

                        │

      ┌────────┼────────────┼────────────┐

      ▼        ▼            ▼            ▼

   PutItem UpdateItem DeleteItem Transaction

      └────────┼────────────┼────────────┘

               ▼

       DynamoDB Storage Engine

               ▼

          Persist Changes
```

Selecting the appropriate write API minimizes latency, improves throughput, and reduces costs.

---

# Production Considerations

Most production applications primarily use:

- PutItem
- UpdateItem
- DeleteItem

Bulk operations are typically handled using:

- BatchWriteItem

Business-critical workflows use:

- TransactWriteItems

High-concurrency applications frequently combine:

- UpdateItem
- Condition Expressions
- Atomic Counters
- Optimistic Locking

to safely handle concurrent writes.

---

# Interview Notes

A common interview question is:

> **What is the difference between PutItem and UpdateItem?**

`PutItem` creates or completely replaces an item, while `UpdateItem` modifies only the specified attributes without replacing the entire item.

Another common question is:

> **When should BatchWriteItem be used?**

For high-throughput bulk inserts or deletes where atomicity is not required.

Another common question is:

> **Why shouldn't BatchWriteItem be used for financial transactions?**

Because it allows partial success. Some writes may succeed while others fail, leading to inconsistent business data.

Another common question is:

> **When should TransactWriteItems be used?**

When multiple related writes must either all succeed or all fail, such as money transfers, order processing, or inventory reservations.

---

# Key Takeaways

- DynamoDB provides specialized write APIs optimized for different workloads.
- `PutItem` creates or replaces an entire item.
- `UpdateItem` modifies only selected attributes and is preferred for partial updates.
- `DeleteItem` removes items by primary key.
- `BatchWriteItem` improves throughput for bulk writes but is **not transactional**.
- `TransactWriteItems` provides ACID-compliant atomic writes across one or more tables.
- Condition Expressions and Atomic Counters help build safe, concurrent, production-grade applications.