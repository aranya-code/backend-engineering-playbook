# 06 - Batch Operations

## Overview

In production systems, applications rarely read or write one item at a time.

Examples include:

- Importing thousands of products
- Processing orders
- Synchronizing inventory
- Migrating customer data
- Loading cache
- ETL pipelines

Making thousands of individual API calls introduces unnecessary latency, increases network overhead, and reduces throughput.

Amazon DynamoDB provides **batch operations** that allow multiple items to be processed in a single request.

The two primary batch APIs are:

- BatchGetItem
- BatchWriteItem

Understanding when—and when **not**—to use these APIs is critical for building high-performance backend systems.

---

# Learning Objectives

After completing this chapter, you'll understand:

- BatchGetItem
- BatchWriteItem
- batch_writer()
- Request limits
- Unprocessed Items
- Retry strategies
- Performance optimization
- Production best practices
- Common mistakes
- Interview questions

---

# Why Batch Operations?

Without batching:

```text
Application

↓

1,000 Requests

↓

1,000 Network Calls

↓

Higher Latency
```

With batching:

```text
Application

↓

10 Batch Requests

↓

10 Network Calls

↓

Lower Latency
```

Fewer network round trips significantly improve performance.

---

# Batch Operations Overview

| Operation | Purpose |
|------------|----------|
| BatchGetItem | Read multiple items |
| BatchWriteItem | Insert/Delete multiple items |
| batch_writer() | High-level write helper |

---

# BatchGetItem

Reads multiple items from one or more tables.

Example:

```python
import boto3

client = boto3.client("dynamodb")

response = client.batch_get_item(
    RequestItems={
        "Orders": {
            "Keys": [
                {"order_id": {"S": "ORD-1001"}},
                {"order_id": {"S": "ORD-1002"}},
                {"order_id": {"S": "ORD-1003"}}
            ]
        }
    }
)
```

Execution

```text
Application

↓

BatchGetItem

↓

Read Multiple Keys

↓

Return Items
```

---

# BatchGetItem Limits

Maximum:

- 100 items
- 16 MB response size

```text
100 Items

↓

Single Request

↓

Response
```

Requests exceeding these limits must be split into multiple batches.

---

# BatchGetItem Across Tables

BatchGetItem supports multiple tables.

```text
Orders

Customers

Products

↓

One API Call
```

Useful for aggregation services.

---

# BatchWriteItem

Writes multiple items in one request.

Supported operations:

- PutItem
- DeleteItem

Not supported:

- UpdateItem

---

Example:

```python
client.batch_write_item(
    RequestItems={
        "Orders": [
            {
                "PutRequest": {
                    "Item": {
                        "order_id": {"S": "ORD-1001"}
                    }
                }
            }
        ]
    }
)
```

---

# BatchWriteItem Limits

Maximum:

- 25 write requests
- 16 MB request size

```text
25 Items

↓

One Request

↓

DynamoDB
```

---

# Why UpdateItem Isn't Supported

Updating requires reading existing attributes and applying update expressions.

BatchWriteItem is designed only for:

- Put
- Delete

For updates:

```text
Use UpdateItem
```

---

# High-Level batch_writer()

Boto3 provides a simpler interface.

```python
import boto3

table = boto3.resource("dynamodb").Table("Orders")

with table.batch_writer() as batch:

    batch.put_item(
        Item={
            "order_id": "ORD-1001"
        }
    )

    batch.put_item(
        Item={
            "order_id": "ORD-1002"
        }
    )
```

The context manager automatically batches requests behind the scenes.

---

# Internal Flow

```text
Application

↓

batch_writer()

↓

Collect Items

↓

BatchWriteItem

↓

Retry Failed Writes

↓

Success
```

---

# Automatic Retry

One of the biggest advantages of `batch_writer()`:

It automatically retries:

```text
UnprocessedItems
```

until they succeed.

Manual retry logic is usually unnecessary.

---

# Unprocessed Items

DynamoDB may temporarily reject some requests due to:

- Throttling
- Capacity limits
- Internal scaling

Returned response:

```text
UnprocessedItems
```

Example flow:

```text
25 Writes

↓

22 Success

↓

3 Unprocessed

↓

Retry
```

---

# Manual Retry Strategy

When using the low-level client:

```text
Batch Request

↓

Unprocessed Items?

↓

YES

↓

Exponential Backoff

↓

Retry
```

Never ignore unprocessed items.

---

# Exponential Backoff

Poor:

```text
Retry Immediately
```

Better:

```text
1 second

↓

2 seconds

↓

4 seconds

↓

8 seconds
```

This prevents overwhelming DynamoDB during throttling events.

---

# Reading Large Datasets

Suppose 5,000 records are required.

Instead of:

```text
5,000 GetItem Requests
```

Use:

```text
50 BatchGetItem Requests

↓

100 Items Each
```

This dramatically reduces network overhead.

---

# Writing Large Datasets

Suppose 50,000 products need to be imported.

Poor:

```text
50,000 PutItem Calls
```

Better:

```text
batch_writer()

↓

Automatic Batching

↓

Automatic Retry
```

---

# Repository Example

```python
class OrderRepository:

    def save_orders(self, orders):

        with self.table.batch_writer() as batch:

            for order in orders:
                batch.put_item(Item=order)
```

The service layer remains unaware of batching implementation details.

---

# Batch Operations vs Transactions

| Feature | Batch | Transaction |
|----------|--------|------------|
| Atomic | ❌ | ✅ |
| Faster | ✅ | ❌ |
| Lower Cost | ✅ | ❌ |
| Rollback | ❌ | ✅ |
| Best For | Bulk Import | Financial Operations |

Choose the API based on consistency requirements.

---

# Production Architecture

```text
CSV

↓

FastAPI

↓

Import Service

↓

Repository

↓

batch_writer()

↓

Amazon DynamoDB
```

This pattern is common for bulk import APIs.

---

# Performance Considerations

Batch operations reduce:

- Network latency
- TCP overhead
- Connection establishment costs
- SDK serialization overhead

They increase:

- Throughput
- Resource utilization
- Import performance

---

# Security Best Practices

- Validate data before batching.
- Apply IAM least-privilege permissions.
- Log failed batches.
- Encrypt data at rest.
- Monitor throttling metrics.
- Retry only idempotent operations.

---

# Best Practices

- Prefer `batch_writer()` for bulk inserts.
- Retry unprocessed items.
- Split large imports into valid batch sizes.
- Monitor consumed write capacity.
- Keep batches reasonably sized.
- Use batch operations only when atomicity is unnecessary.

---

# Common Mistakes

## Ignoring Unprocessed Items

Poor:

```text
Batch Response

↓

Ignore Failures
```

Better:

```text
Retry Until Success
```

---

## Using BatchWriteItem for Updates

Incorrect:

```text
Update Existing Records
```

BatchWriteItem does not support updates.

Use:

```text
UpdateItem
```

---

## Assuming Batch Operations Are Atomic

Incorrect assumption:

```text
All Success

OR

All Failure
```

Reality:

Some items may succeed while others fail.

---

## Using Batch APIs for Small Operations

Reading two items?

Use:

```text
GetItem
```

Batch APIs provide the most value for larger workloads.

---

# Interview Notes

A common interview question is:

> **What is the difference between BatchWriteItem and batch_writer()?**

`BatchWriteItem` is the low-level DynamoDB API where the developer manages batching and retries. `batch_writer()` is a high-level Boto3 helper that automatically batches requests and retries unprocessed items.

---

Another common question is:

> **Why does DynamoDB return UnprocessedItems?**

Items may be returned as unprocessed when DynamoDB throttles requests due to capacity limits or temporary internal conditions. Applications should retry these items using exponential backoff.

---

Another common question is:

> **Are batch operations atomic?**

No. Batch operations are not atomic. Some items may succeed while others fail. If atomicity is required, use DynamoDB transactions instead.

---

Another common question is:

> **When should you use BatchGetItem?**

Use `BatchGetItem` when reading many known items by primary key. It reduces the number of network calls compared to issuing multiple individual `GetItem` requests.

---

# Key Takeaways

- Batch APIs improve throughput by reducing the number of network round trips.
- `BatchGetItem` reads up to 100 items, while `BatchWriteItem` writes up to 25 items per request.
- `batch_writer()` is the preferred Boto3 interface for bulk writes because it automatically handles batching and retries.
- Always process and retry `UnprocessedItems` using exponential backoff.
- Batch operations are optimized for performance but are **not atomic**; use transactions when consistency guarantees are required.