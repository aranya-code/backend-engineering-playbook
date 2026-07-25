# 14 - Async Access with aioboto3

## Overview

Modern backend applications increasingly rely on **asynchronous programming** to maximize throughput and efficiently handle thousands of concurrent requests.

Frameworks such as:

- FastAPI
- Starlette
- Sanic
- AIOHTTP

are built around Python's `asyncio` event loop.

Although **Boto3** is the official AWS SDK for Python, it is **synchronous**. This means each DynamoDB request blocks the current thread until the response is received.

For asynchronous applications, developers often use **aioboto3**, an asynchronous wrapper around Boto3 and aiobotocore that provides an async interface while maintaining a familiar API.

This chapter explores how to integrate DynamoDB with asynchronous Python applications in a production-ready manner.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why async matters
- Boto3 vs aioboto3
- Event Loop fundamentals
- Async Sessions
- Async Resources
- Async CRUD operations
- Async Queries
- Connection management
- Error handling
- Performance considerations
- Production architecture
- Interview questions

---

# Why Async?

Traditional synchronous execution looks like this:

```text
Request

↓

Database Call

↓

Wait...

↓

Response

↓

Next Request
```

During the wait time, the thread remains blocked.

---

# Async Execution

With asynchronous programming:

```text
Request A

↓

Waiting

───────────────

Request B

↓

Executing

───────────────

Request C

↓

Executing
```

While one request waits for DynamoDB, other requests continue processing.

---

# Boto3 vs aioboto3

| Feature | Boto3 | aioboto3 |
|----------|--------|-----------|
| Official AWS SDK | ✅ | Wrapper |
| Synchronous | ✅ | ❌ |
| Async/Await | ❌ | ✅ |
| FastAPI Friendly | Limited | Excellent |
| API Similarity | Native | Very High |

---

# When Should You Use aioboto3?

Recommended:

- FastAPI
- Starlette
- Async microservices
- High concurrency APIs
- Event-driven systems

Usually unnecessary for:

- Django (traditional synchronous views)
- Small scripts
- AWS Lambda functions that don't use async

---

# Installation

```bash
pip install aioboto3
```

---

# Creating a Session

```python
import aioboto3

session = aioboto3.Session()
```

Unlike Boto3, sessions are commonly used inside async context managers.

---

# Creating a DynamoDB Resource

```python
import aioboto3

session = aioboto3.Session()

async with session.resource(
    "dynamodb"
) as dynamodb:

    table = await dynamodb.Table(
        "Orders"
    )
```

Notice the use of:

- `async with`
- `await`

---

# Async CRUD Example

```python
async def create_order(order):

    async with session.resource(
        "dynamodb"
    ) as dynamodb:

        table = await dynamodb.Table(
            "Orders"
        )

        await table.put_item(
            Item=order
        )
```

Execution is non-blocking.

---

# Async GetItem

```python
async def get_order(order_id):

    async with session.resource(
        "dynamodb"
    ) as dynamodb:

        table = await dynamodb.Table(
            "Orders"
        )

        response = await table.get_item(
            Key={
                "order_id": order_id
            }
        )

        return response.get("Item")
```

---

# Async Query

```python
from boto3.dynamodb.conditions import Key

response = await table.query(

    KeyConditionExpression=
        Key("customer_id").eq("C100")
)
```

Almost identical to Boto3.

---

# Async Scan

```python
response = await table.scan()
```

Remember:

Even asynchronously, scans remain expensive.

Prefer `Query`.

---

# Async Update

```python
await table.update_item(

    Key={
        "order_id": "1001"
    },

    UpdateExpression=
        "SET status = :s",

    ExpressionAttributeValues={
        ":s": "SHIPPED"
    }
)
```

---

# Async Delete

```python
await table.delete_item(

    Key={
        "order_id": "1001"
    }
)
```

---

# Async Pagination

```python
items = []

response = await table.query(
    KeyConditionExpression=...
)

items.extend(response["Items"])

while "LastEvaluatedKey" in response:

    response = await table.query(

        KeyConditionExpression=...,

        ExclusiveStartKey=
            response["LastEvaluatedKey"]
    )

    items.extend(response["Items"])
```

Pagination works exactly like Boto3.

---

# Async Architecture

```text
               Client

                  │

                  ▼

             FastAPI API

                  │

                  ▼

          Async Endpoint

                  │

                  ▼

         Async Repository

                  │

                  ▼

             aioboto3

                  │

                  ▼

          Amazon DynamoDB
```

---

# Async Repository Pattern

```python
class OrderRepository:

    def __init__(self, table):

        self.table = table

    async def get_order(self, order_id):

        response = await self.table.get_item(

            Key={
                "order_id": order_id
            }
        )

        return response.get("Item")
```

The service layer remains clean.

---

# Using Dependency Injection

FastAPI dependency:

```python
async def get_repository():

    session = aioboto3.Session()

    async with session.resource(
        "dynamodb"
    ) as dynamodb:

        table = await dynamodb.Table(
            "Orders"
        )

        yield OrderRepository(table)
```

Each request receives a properly configured repository.

---

# Concurrency Example

Multiple queries can execute concurrently.

```text
Request A

──────────────

Request B

──────────────

Request C

──────────────

Await

↓

Complete Independently
```

This significantly improves throughput for I/O-bound workloads.

---

# Error Handling

Error handling remains similar.

```python
from botocore.exceptions import ClientError

try:

    await table.put_item(Item=item)

except ClientError as error:

    print(error.response["Error"]["Code"])
```

Use the same retry strategies discussed earlier.

---

# Resource Management

Always use:

```python
async with
```

instead of manually opening resources.

This ensures:

- Connections are released
- Resources are cleaned up
- Memory leaks are avoided

---

# Performance Considerations

Async programming improves:

- Throughput
- Concurrency
- Thread utilization
- Resource efficiency

However:

It does **not** make DynamoDB itself faster.

The database latency remains unchanged.

---

# Common Misconception

Many developers think:

```text
Async

↓

Lower Database Latency
```

Incorrect.

Actual benefit:

```text
Async

↓

More Concurrent Requests

↓

Higher Overall Throughput
```

---

# Production Folder Structure

```text
app/

├── api/
├── services/
├── repositories/
├── database/
├── config/
└── main.py
```

Example:

```text
repositories/

└── order_repository.py

database/

└── dynamodb.py
```

---

# Production Architecture

```text
                Client

                   │

                   ▼

             Load Balancer

                   │

                   ▼

              FastAPI

                   │

                   ▼

        Async Service Layer

                   │

                   ▼

       Async Repository Layer

                   │

                   ▼

              aioboto3

                   │

                   ▼

         Amazon DynamoDB
```

---

# Security Best Practices

- Continue using IAM Roles instead of access keys.
- Store AWS configuration outside source code.
- Apply least-privilege permissions.
- Validate all user inputs before persistence.
- Avoid logging sensitive data.
- Close sessions properly using `async with`.

---

# Best Practices

- Use aioboto3 only in asynchronous applications.
- Prefer dependency injection for repositories.
- Reuse Sessions where appropriate.
- Always use `async with`.
- Use `await` for all DynamoDB operations.
- Continue using retries and exponential backoff.
- Keep business logic separate from data access.

---

# Common Mistakes

## Mixing Sync and Async

Poor:

```python
await table.put_item(...)

table.get_item(...)
```

Mixing synchronous and asynchronous APIs can block the event loop and reduce scalability.

---

## Forgetting await

Poor:

```python
table.put_item(...)
```

Correct:

```python
await table.put_item(...)
```

---

## Creating Sessions Repeatedly

Avoid creating a new session for every database operation.

Instead:

```text
Application

↓

Shared Session

↓

Repositories
```

Reuse sessions whenever practical.

---

## Assuming Async Makes DynamoDB Faster

Async improves concurrency, not database execution speed.

---

# Interview Notes

A common interview question is:

> **Why use aioboto3 instead of Boto3?**

Boto3 is synchronous and blocks the executing thread during network calls. aioboto3 provides an asynchronous interface that integrates naturally with FastAPI and other asyncio-based frameworks, improving application throughput under high concurrency.

---

Another common question is:

> **Does aioboto3 improve DynamoDB latency?**

No. DynamoDB latency remains the same. aioboto3 improves the application's ability to process many concurrent requests while waiting for I/O operations to complete.

---

Another common question is:

> **When should you use aioboto3?**

Use aioboto3 for asynchronous Python frameworks such as FastAPI or Starlette. For synchronous applications or simple scripts, Boto3 is usually sufficient.

---

Another common question is:

> **What is the biggest advantage of asynchronous database access?**

The primary advantage is improved scalability through better utilization of the event loop, allowing the application to handle many concurrent I/O-bound requests without blocking worker threads.

---

# Key Takeaways

- aioboto3 provides an asynchronous interface to DynamoDB for asyncio-based Python applications.
- Use `async with` and `await` to manage resources and execute operations correctly.
- Async programming improves throughput and concurrency but does not reduce DynamoDB latency.
- Combine aioboto3 with dependency injection, repository patterns, retries, and proper resource management for production-grade applications.
- Choose aioboto3 only when your application architecture is asynchronous; otherwise, the official Boto3 SDK remains the preferred choice.