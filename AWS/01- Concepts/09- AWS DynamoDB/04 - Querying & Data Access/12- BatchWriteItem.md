# 12 - BatchWriteItem

## Overview

`BatchWriteItem` is a DynamoDB operation that allows an application to **write or delete multiple items in a single request**.

Instead of sending numerous individual `PutItem` or `DeleteItem` requests, BatchWriteItem combines them into one API call, reducing:

- Network round trips
- API overhead
- Client-side latency
- Connection management costs

Unlike **BatchGetItem**, BatchWriteItem **does not support updates**.

Each operation inside a batch can only be:

- PutItem
- DeleteItem

BatchWriteItem is commonly used for:

- Bulk imports
- Data migration
- ETL pipelines
- Batch cleanup
- Initial data loading

---

# Why BatchWriteItem Exists

Suppose an application needs to insert:

```text
100 Products
```

Without BatchWriteItem:

```text
PutItem

↓

PutItem

↓

PutItem

↓

...

↓

100 Requests
```

With BatchWriteItem:

```text
Application

↓

BatchWriteItem

↓

25 Writes
```

Fewer network calls improve throughput.

---

# Internal Architecture

```text
             Application

                    │

                    ▼

            BatchWriteItem

                    │

      ┌─────────────┼─────────────┐

      ▼             ▼             ▼

  Put Item A   Put Item B   Delete Item C

      └─────────────┼─────────────┘

                    ▼

          Execute Independently

                    ▼

           Return Batch Result
```

Each write is processed independently.

---

# Supported Operations

BatchWriteItem supports:

```text
PutItem
```

and

```text
DeleteItem
```

It does **not** support:

- UpdateItem
- Condition Expressions
- Transactions

---

# Maximum Batch Size

A single BatchWriteItem request can contain:

```text
25 Write Operations
```

Maximum payload size:

```text
16 MB
```

Maximum item size:

```text
400 KB
```

---

# Request Example

Suppose we insert three users.

```text
User101

User102

User103
```

Workflow:

```text
BatchWriteItem

↓

Put User101

Put User102

Put User103
```

Single request.

---

# Batch Delete Example

Delete multiple expired sessions.

```text
Session001

Session002

Session003
```

Application:

```text
BatchWriteItem

↓

Delete Session001

Delete Session002

Delete Session003
```

---

# Capacity Consumption

BatchWriteItem consumes:

```text
Write Capacity Units (WCUs)
```

exactly as if each write were performed individually.

Example:

```text
20 PutItems
```

Consumes:

```text
Sum of

20 Individual Writes
```

Batching improves network efficiency—not write cost.

---

# No Atomicity

A common misconception is that BatchWriteItem is transactional.

It is not.

Example:

```text
25 Writes
```

Result:

```text
22 Success

3 Failed
```

Successful writes remain committed.

Failed writes are not automatically rolled back.

---

# UnprocessedItems

If DynamoDB cannot process every request because of:

- Throttling
- Capacity limits
- Internal retries

It returns:

```text
UnprocessedItems
```

Example:

```text
25 Writes

↓

21 Success

↓

4 UnprocessedItems
```

Applications should retry only those items.

---

# Retry Workflow

```text
BatchWriteItem

↓

Receive

UnprocessedItems

↓

Exponential Backoff

↓

Retry

↓

Success
```

Retrying immediately may increase throttling.

---

# BatchWriteItem vs PutItem

| Feature | PutItem | BatchWriteItem |
|----------|----------|----------------|
| Single Write | ✅ | ❌ |
| Multiple Writes | ❌ | ✅ |
| Supports Delete | ❌ | ✅ |
| Supports Conditions | ✅ | ❌ |
| Transactional | ❌ | ❌ |

---

# BatchWriteItem vs TransactWriteItems

| Feature | BatchWriteItem | TransactWriteItems |
|----------|----------------|--------------------|
| Atomic | ❌ | ✅ |
| Max Operations | 25 | 100 |
| Conditions | ❌ | ✅ |
| Rollback | ❌ | ✅ |
| Performance | Higher | Slightly Lower |

BatchWriteItem favors throughput over consistency.

---

# BatchWriteItem vs UpdateItem

BatchWriteItem cannot update attributes.

Example:

```text
User

↓

Age = 25
```

Need:

```text
Age = 26
```

Use:

```text
UpdateItem
```

Not:

```text
BatchWriteItem
```

---

# Real-World Example — Product Import

Import:

```text
10,000 Products
```

Workflow:

```text
CSV

↓

Split

↓

25 Items

↓

BatchWriteItem

↓

Repeat
```

This is much faster than individual writes.

---

# Real-World Example — Log Cleanup

Expired logs:

```text
100,000 Items
```

Application:

```text
Delete

25 at a Time

↓

BatchWriteItem
```

Efficient bulk deletion.

---

# Real-World Example — ETL Pipeline

Workflow:

```text
Read

↓

Transform

↓

BatchWriteItem

↓

New DynamoDB Table
```

Common during migrations.

---

# Real-World Example — Cache Warm-Up

Application startup:

```text
Load

Configuration

↓

BatchWriteItem

↓

Cache Table
```

Allows fast initialization.

---

# Performance Considerations

BatchWriteItem reduces:

- HTTP requests
- TCP overhead
- Network latency

It does **not** reduce:

- WCUs
- Item size
- Write throughput requirements

---

# Best Practices

- Group writes into batches of up to 25 items.
- Retry only `UnprocessedItems`.
- Use exponential backoff.
- Monitor throttling in CloudWatch.
- Split very large imports into multiple batches.
- Use TransactWriteItems when atomicity is required.

---

# Common Mistakes

## Assuming BatchWriteItem is Transactional

Incorrect.

Some writes may succeed while others fail.

Applications must handle partial success.

---

## Ignoring UnprocessedItems

Never assume every write succeeded.

Always inspect:

```text
UnprocessedItems
```

and retry them.

---

## Using BatchWriteItem for Updates

BatchWriteItem supports only:

- PutItem
- DeleteItem

For modifying attributes, use:

```text
UpdateItem
```

---

## Sending Oversized Batches

Requests exceeding:

- 25 operations
- 16 MB payload

will fail.

Split large workloads into smaller batches.

---

# Architecture Perspective

```text
                 Application

                       │

                BatchWriteItem

                       │

       ┌───────────────┼───────────────┐

       ▼               ▼               ▼

    Put Item      Delete Item      Put Item

       └───────────────┼───────────────┘

                       ▼

              Execute Independently

                       ▼

         Success + UnprocessedItems
```

Each operation is independent, allowing high throughput but not transactional guarantees.

---

# Production Considerations

BatchWriteItem is widely used for high-volume write workloads, including:

- Bulk imports
- ETL jobs
- Log ingestion
- Data synchronization
- Migration between tables
- Batch cleanup operations

Production systems should:

- Retry `UnprocessedItems`
- Implement exponential backoff
- Monitor write throttling
- Avoid assuming all writes succeed

If business consistency is more important than throughput, `TransactWriteItems` is usually the better choice.

---

# Interview Notes

A common interview question is:

> **When should you use BatchWriteItem?**

Use BatchWriteItem when inserting or deleting many independent items efficiently. It is ideal for bulk operations where atomicity is not required.

Another common question is:

> **Is BatchWriteItem transactional?**

No. Individual operations may succeed or fail independently. DynamoDB does not automatically roll back successful writes if others fail.

Another common question is:

> **What should you do with `UnprocessedItems`?**

Retry only those items using exponential backoff. They typically occur because of throttling or temporary capacity constraints.

Another common question is:

> **Can BatchWriteItem update existing items?**

No. It only supports `PutItem` and `DeleteItem`. Attribute updates require `UpdateItem`.

---

# Key Takeaways

- `BatchWriteItem` performs multiple `PutItem` and `DeleteItem` operations in a single request.
- It supports up to **25 write operations** and a **16 MB** request payload.
- It improves throughput by reducing network overhead but does **not** reduce WCU consumption.
- BatchWriteItem is **not transactional**; partial success is possible.
- Always check for `UnprocessedItems` and retry them using exponential backoff.
- Use `TransactWriteItems` instead when atomicity and consistency across multiple writes are required.