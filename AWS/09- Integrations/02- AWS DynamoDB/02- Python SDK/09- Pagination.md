# 09 - Pagination

## Overview

Amazon DynamoDB is designed to scale to virtually unlimited amounts of data.

Instead of returning every matching item in a single response, DynamoDB returns **pages** of results.

Every `Query` and `Scan` operation can return **a maximum of 1 MB of data** in a single request.

If additional data exists, DynamoDB returns a **LastEvaluatedKey**, which allows the application to continue reading the next page.

Understanding pagination is critical for building:

- REST APIs
- Infinite scrolling
- Data exports
- Batch processing
- ETL pipelines
- Reporting systems

Many production bugs occur because developers process only the **first page** and ignore the remaining data.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why DynamoDB uses pagination
- LastEvaluatedKey
- ExclusiveStartKey
- Query pagination
- Scan pagination
- Page size vs item count
- Building paginated APIs
- Performance optimization
- Production best practices
- Interview questions

---

# Why Pagination?

Suppose a table contains:

```text
10 Million Orders
```

Returning everything at once would:

- Consume excessive memory
- Increase latency
- Cause request timeouts
- Create massive network traffic

Instead DynamoDB returns data in manageable pages.

---

# Pagination Architecture

```text
Application

       │

       ▼

Query Request

       │

       ▼

First 1 MB

       │

       ▼

LastEvaluatedKey

       │

       ▼

Next Request

       │

       ▼

Next 1 MB

       │

       ▼

Continue Until Finished
```

---

# Maximum Response Size

Each Query or Scan returns at most:

```text
1 MB
```

This is **data size**, not item count.

For example:

```text
100 Small Items

OR

5 Large Items

↓

1 MB
```

---

# First Query

```python
from boto3.dynamodb.conditions import Key

response = table.query(
    KeyConditionExpression=
        Key("customer_id").eq("C100")
)
```

The response contains:

```python
response["Items"]
```

and possibly:

```python
response["LastEvaluatedKey"]
```

---

# LastEvaluatedKey

If additional data exists:

```python
response["LastEvaluatedKey"]
```

might return:

```python
{
    "customer_id": "C100",
    "order_date": "2026-01-15"
}
```

This is **not another item**.

It is a pointer to where DynamoDB should resume reading.

---

# Query Flow

```text
Query

↓

1 MB Returned

↓

More Data?

↓

YES

↓

LastEvaluatedKey

↓

Next Query
```

---

# ExclusiveStartKey

To continue reading:

```python
response = table.query(

    KeyConditionExpression=
        Key("customer_id").eq("C100"),

    ExclusiveStartKey=last_key
)
```

Execution:

```text
Previous Page

↓

LastEvaluatedKey

↓

ExclusiveStartKey

↓

Next Page
```

---

# Complete Pagination Loop

```python
from boto3.dynamodb.conditions import Key

items = []

response = table.query(
    KeyConditionExpression=
        Key("customer_id").eq("C100")
)

items.extend(response["Items"])

while "LastEvaluatedKey" in response:

    response = table.query(

        KeyConditionExpression=
            Key("customer_id").eq("C100"),

        ExclusiveStartKey=
            response["LastEvaluatedKey"]
    )

    items.extend(response["Items"])
```

This pattern ensures that **every page** is retrieved.

---

# Scan Pagination

The same approach applies to scans.

```python
response = table.scan()

while "LastEvaluatedKey" in response:

    response = table.scan(
        ExclusiveStartKey=
            response["LastEvaluatedKey"]
    )
```

Remember:

Scanning large tables is expensive.

---

# Limit Parameter

Limit controls the maximum number of items DynamoDB **evaluates**, not necessarily the number returned after filtering.

Example:

```python
response = table.query(

    KeyConditionExpression=
        Key("customer_id").eq("C100"),

    Limit=25
)
```

Useful for building API endpoints.

---

# Limit vs Pagination

Suppose:

```text
1,000 Items
```

Using:

```python
Limit=100
```

Results in:

```text
Page 1

100 Items

↓

Page 2

100 Items

↓

Page 3

...
```

---

# FilterExpression Interaction

Consider:

```python
response = table.query(

    KeyConditionExpression=...,

    FilterExpression=...
)
```

Execution:

```text
Read Items

↓

Apply Filter

↓

Return Results
```

Pagination occurs **before** filtering is complete across the full dataset.

This can produce pages with fewer items than expected.

---

# ProjectionExpression

Retrieve only required attributes.

```python
ProjectionExpression=
"customer_name, status"
```

Benefits:

- Smaller payloads
- Faster responses
- Lower network usage

---

# Building REST APIs

Typical API:

```text
GET

/orders?page=2
```

DynamoDB does **not** support page numbers.

Instead:

```text
Client

↓

Receives Token

↓

Sends Token Back

↓

Next Page
```

---

# Cursor-Based Pagination

Modern APIs use cursor pagination.

Example response:

```json
{
    "items": [...],
    "next_cursor": "eyJjdXN0b21lcl9pZCI6IkMxMDAifQ=="
}
```

Internally:

```text
next_cursor

↓

LastEvaluatedKey
```

The cursor is often encoded (for example, Base64 or signed) before being returned to clients.

---

# Offset Pagination vs Cursor Pagination

| Feature | Offset | Cursor |
|----------|---------|---------|
| Page Numbers | ✅ | ❌ |
| Large Dataset Performance | Poor | Excellent |
| Duplicate Risk | Higher | Lower |
| DynamoDB Support | ❌ | ✅ |

Cursor pagination is the recommended approach.

---

# Production Repository Example

```python
class OrderRepository:

    def get_orders(
        self,
        customer_id,
        last_key=None
    ):

        params = {
            "KeyConditionExpression":
                Key("customer_id").eq(customer_id)
        }

        if last_key:
            params["ExclusiveStartKey"] = last_key

        return self.table.query(**params)
```

---

# Infinite Scroll

Common architecture:

```text
Mobile App

↓

API

↓

DynamoDB

↓

20 Items

↓

Next Cursor

↓

Load More
```

This minimizes memory usage and network traffic.

---

# Export Jobs

Large exports should never load all records into memory.

Preferred approach:

```text
Read Page

↓

Process Page

↓

Write Output

↓

Read Next Page
```

Memory usage remains constant.

---

# Production Architecture

```text
                Client

                   │

                   ▼

              FastAPI API

                   │

                   ▼

         Repository Layer

                   │

                   ▼

         Query + Pagination

                   │

                   ▼

          Amazon DynamoDB
```

---

# Performance Considerations

Pagination improves:

- Memory utilization
- Response time
- Network efficiency
- Scalability

Avoid loading millions of items into memory.

Process results incrementally whenever possible.

---

# Security Best Practices

- Validate pagination tokens.
- Do not expose raw internal keys directly if they reveal sensitive information.
- Sign or encode cursors before returning them to clients.
- Limit maximum page sizes to prevent abuse.
- Apply IAM least-privilege permissions.

---

# Best Practices

- Always check for `LastEvaluatedKey`.
- Use cursor-based pagination.
- Keep page sizes reasonable.
- Process data incrementally.
- Use `ProjectionExpression` to reduce payload size.
- Combine pagination with efficient Query operations rather than Scan.

---

# Common Mistakes

## Ignoring LastEvaluatedKey

Poor:

```text
Read First Page

↓

Stop
```

Better:

```text
Read First Page

↓

LastEvaluatedKey?

↓

Continue Reading
```

---

## Building Page Number APIs

DynamoDB doesn't naturally support:

```text
?page=15
```

Use cursor-based pagination instead.

---

## Loading Entire Tables

Poor:

```text
Read 5 Million Records

↓

Store In Memory
```

Better:

```text
Read

↓

Process

↓

Read Next Page
```

---

## Returning Raw Keys

Avoid exposing raw `LastEvaluatedKey` values directly to API consumers. Encode or sign them before returning them as cursors.

---

# Interview Notes

A common interview question is:

> **Why does DynamoDB use pagination?**

DynamoDB limits each Query or Scan response to a maximum of 1 MB of data to improve scalability, reduce latency, and avoid excessively large responses.

---

Another common question is:

> **What is LastEvaluatedKey?**

`LastEvaluatedKey` is a pointer returned by DynamoDB when additional matching data exists. It is passed back as `ExclusiveStartKey` in the next request to continue reading.

---

Another common question is:

> **What is the difference between offset pagination and cursor pagination?**

Offset pagination retrieves records based on page numbers and becomes inefficient for large datasets. Cursor pagination uses a continuation token (derived from `LastEvaluatedKey`), providing better performance and consistency for DynamoDB workloads.

---

Another common question is:

> **How would you implement pagination in a FastAPI application using DynamoDB?**

A repository method should execute a Query, return the retrieved items along with an encoded cursor derived from `LastEvaluatedKey`, and accept that cursor in subsequent requests to continue reading with `ExclusiveStartKey`.

---

# Key Takeaways

- DynamoDB paginates Query and Scan results with a maximum response size of **1 MB**.
- `LastEvaluatedKey` indicates that additional results are available and is used as `ExclusiveStartKey` in the next request.
- Cursor-based pagination is the preferred strategy for DynamoDB-backed APIs.
- Process results page by page rather than loading large datasets into memory.
- Proper pagination handling is essential for building scalable APIs, exports, and background processing systems.