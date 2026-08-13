# 05 - Querying Data

## Overview

Retrieving data efficiently is one of the most important aspects of designing a DynamoDB application.

Amazon DynamoDB provides two primary methods for retrieving multiple items:

- Query
- Scan

Although they may appear similar, they have **vastly different performance characteristics**.

A poorly designed application that relies on `Scan` can become expensive, slow, and difficult to scale, while an application designed around `Query` can serve millions of requests with predictable performance.

Understanding when and how to use `Query` is one of the key skills that separates junior developers from senior backend engineers.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Query vs Scan
- KeyConditionExpression
- FilterExpression
- ProjectionExpression
- Pagination
- Sorting
- Querying GSIs
- Querying LSIs
- Performance optimization
- Production best practices
- Interview questions

---

# Query Architecture

```text
Application

        │

        ▼

   Query Request

        │

        ▼

Partition Key

        │

        ▼

Matching Partition

        │

        ▼

Return Matching Items
```

Query is optimized because DynamoDB already knows which partition contains the data.

---

# Scan Architecture

```text
Application

        │

        ▼

 Scan Request

        │

        ▼

Partition 1

↓

Partition 2

↓

Partition 3

↓

Partition N

↓

Return Matches
```

Every partition must be read.

---

# Query vs Scan

| Feature | Query | Scan |
|----------|--------|------|
| Uses Partition Key | ✅ | ❌ |
| Reads Entire Table | ❌ | ✅ |
| Fast | ✅ | ❌ |
| Low Cost | ✅ | ❌ |
| Production Friendly | ✅ | Rarely |
| Scalable | ✅ | Poor |

---

# The Query Operation

Query retrieves items sharing the same partition key.

Example table:

| order_id | created_at | status |
|-----------|------------|---------|
| ORD-1001 | 2026-01-01 | Pending |
| ORD-1001 | 2026-01-02 | Completed |
| ORD-1002 | 2026-01-03 | Pending |

Query:

```python
response = table.query(
    KeyConditionExpression=
        Key("order_id").eq("ORD-1001")
)
```

Only items belonging to `ORD-1001` are read.

---

# Importing Key

```python
from boto3.dynamodb.conditions import Key
```

The `Key` helper builds key condition expressions.

---

# KeyConditionExpression

The most important part of every Query.

```python
response = table.query(
    KeyConditionExpression=
        Key("order_id").eq("ORD-1001")
)
```

Execution

```text
Partition Key

↓

Find Partition

↓

Read Matching Items

↓

Return Results
```

---

# Querying with Sort Keys

Suppose the table has:

```text
Partition Key

customer_id

Sort Key

order_date
```

Query orders after a date.

```python
response = table.query(
    KeyConditionExpression=
        Key("customer_id").eq("C100") &
        Key("order_date").gt("2026-01-01")
)
```

---

# Sort Key Operators

Supported operators:

```text
=

<

<=

>

>=

BETWEEN

begins_with()
```

Example:

```python
Key("date").between(
    "2026-01-01",
    "2026-01-31"
)
```

---

# Query Results are Sorted

Items are automatically sorted by the sort key.

Ascending:

```python
ScanIndexForward=True
```

Descending:

```python
ScanIndexForward=False
```

Example

```python
response = table.query(
    KeyConditionExpression=...,
    ScanIndexForward=False
)
```

---

# FilterExpression

A filter is applied **after** the items have been read.

Example:

```python
from boto3.dynamodb.conditions import Attr

response = table.query(
    KeyConditionExpression=
        Key("customer_id").eq("C100"),

    FilterExpression=
        Attr("status").eq("Pending")
)
```

Execution

```text
Query

↓

Read Items

↓

Apply Filter

↓

Return Remaining Items
```

---

# FilterExpression Does NOT Reduce Cost

This is one of the biggest DynamoDB misconceptions.

```text
Read 1,000 Items

↓

Filter 995

↓

Return 5
```

You are still charged for reading all 1,000 items.

---

# ProjectionExpression

Retrieve only required attributes.

Instead of

```json
Entire Item
```

retrieve only

```text
customer_name

status

amount
```

Example

```python
response = table.query(
    KeyConditionExpression=...,
    ProjectionExpression=
        "customer_name, status"
)
```

Benefits:

- Less network traffic
- Faster responses
- Lower application memory usage

---

# Querying a Global Secondary Index

```python
response = table.query(
    IndexName="StatusIndex",

    KeyConditionExpression=
        Key("status").eq("Pending")
)
```

Execution

```text
Application

↓

StatusIndex

↓

Matching Items
```

---

# Querying a Local Secondary Index

```python
response = table.query(
    IndexName="CreatedAtIndex",

    KeyConditionExpression=
        Key("customer_id").eq("C100") &
        Key("created_at").between(...)
)
```

LSIs allow alternative sort keys within the same partition key.

---

# Pagination

DynamoDB returns up to **1 MB** of data per Query request.

```text
Query

↓

1 MB Returned

↓

LastEvaluatedKey

↓

Next Query
```

---

# LastEvaluatedKey

If more data exists:

```python
response["LastEvaluatedKey"]
```

will contain the key needed to continue reading.

Example:

```python
response = table.query(
    ...,
    ExclusiveStartKey=last_key
)
```

---

# Limiting Results

Retrieve only the first few items.

```python
response = table.query(
    KeyConditionExpression=...,
    Limit=10
)
```

Useful for dashboards and APIs.

---

# Eventually Consistent Queries

Default behavior:

```text
Eventually Consistent
```

Lower cost.

Higher throughput.

---

# Strongly Consistent Queries

```python
response = table.query(
    KeyConditionExpression=...,
    ConsistentRead=True
)
```

Available only on:

- Base Table
- Local Secondary Index

Not supported for GSIs.

---

# Scan Operation

Example:

```python
response = table.scan()
```

Execution

```text
Entire Table

↓

Read Every Item

↓

Return Matches
```

Avoid this in production unless absolutely necessary.

---

# Parallel Scan

Large tables may use parallel scanning.

```text
Worker 1

Worker 2

Worker 3

Worker N
```

Each worker scans different table segments.

Although faster than a normal Scan, it still reads the entire table.

---

# Repository Pattern Example

```python
class OrderRepository:

    def get_orders(self, customer_id):

        return self.table.query(
            KeyConditionExpression=
                Key("customer_id").eq(customer_id)
        )
```

Business logic should not construct DynamoDB expressions directly.

---

# Production Architecture

```text
                FastAPI

                   │

                   ▼

            Service Layer

                   │

                   ▼

        Repository Layer

                   │

                   ▼

         Query / GSI / LSI

                   │

                   ▼

             Amazon DynamoDB
```

---

# Performance Considerations

Always design tables around Query access patterns.

Prefer:

- Query
- ProjectionExpression
- GSIs
- LSIs
- Pagination

Avoid:

- Full table scans
- Large filters
- Multiple sequential scans

---

# Security Best Practices

- Validate user input before constructing expressions.
- Restrict access using IAM policies.
- Avoid exposing internal attribute names directly through APIs.
- Log slow queries for performance tuning.
- Monitor consumed read capacity.

---

# Best Practices

- Model tables around Query operations.
- Use GSIs instead of Scans whenever possible.
- Keep partitions balanced.
- Return only required attributes.
- Handle pagination correctly.
- Use FilterExpression sparingly.
- Prefer Query over Scan in production.

---

# Common Mistakes

## Using Scan as a Search API

Poor:

```python
table.scan()
```

Better:

Design an index that supports the required Query.

---

## Expecting Filters to Reduce Cost

Incorrect assumption:

```text
Filter

↓

Lower Cost
```

Reality:

```text
Filter

↓

Same Read Cost
```

---

## Ignoring Pagination

Applications often process only the first page of results and silently ignore the remaining data.

Always check:

```python
LastEvaluatedKey
```

---

## Returning Entire Items

Fetching unnecessary attributes increases network usage and application memory consumption.

Use:

```python
ProjectionExpression
```

---

# Interview Notes

A common interview question is:

> **What is the difference between Query and Scan?**

`Query` retrieves items using the partition key and reads only the matching partitions, making it fast and cost-efficient. `Scan` reads every item in the table regardless of whether it matches the requested criteria, making it slower and more expensive.

---

Another common question is:

> **Does FilterExpression reduce DynamoDB read costs?**

No. DynamoDB applies the filter after reading the matching items, so read capacity is consumed before filtering occurs.

---

Another common question is:

> **Why is Query preferred over Scan in production?**

Query scales predictably because it targets specific partitions using the partition key, whereas Scan reads the entire table, increasing latency, cost, and resource consumption.

---

Another common question is:

> **What is LastEvaluatedKey?**

`LastEvaluatedKey` indicates that additional results are available. It is used as the `ExclusiveStartKey` in the next Query request to continue pagination.

---

# Key Takeaways

- `Query` is the preferred data retrieval operation in DynamoDB because it reads only the required partitions.
- `Scan` should be avoided for production workloads except for administrative tasks or infrequent maintenance operations.
- `FilterExpression` filters results after they are read and does not reduce read capacity consumption.
- Use `ProjectionExpression` to retrieve only the attributes your application requires.
- Design your data model and secondary indexes around access patterns so your application can rely on efficient Query operations instead of expensive Scans.