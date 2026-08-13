# 13 - Building a Production Repository Layer

## Overview

Most DynamoDB tutorials stop after demonstrating CRUD operations.

Real production systems are significantly more complex.

Instead of calling `table.put_item()` throughout the codebase, enterprise applications implement a **Repository Layer** that centralizes:

- Database access
- Error handling
- Retries
- Logging
- Metrics
- Transactions
- Pagination
- Configuration

This creates applications that are easier to test, maintain, and extend.

This chapter walks through designing a production-ready repository layer suitable for FastAPI, Django, microservices, and enterprise backend systems.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why a Repository Layer exists
- Repository architecture
- Base repositories
- Generic repositories
- Domain repositories
- Dependency Injection
- Service integration
- Error handling
- Logging
- Retry wrappers
- Pagination support
- Transaction support
- Testing strategies
- Production best practices

---

# Why Build a Repository Layer?

Small projects often look like this:

```text
API

↓

Boto3

↓

DynamoDB
```

As applications grow:

- Code duplication
- Inconsistent retries
- Logging everywhere
- Difficult testing
- Tight coupling

A repository solves these problems.

---

# Production Architecture

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

             FastAPI / Django

                   │

                   ▼

             Service Layer

                   │

                   ▼

         Repository Layer

                   │

                   ▼

       Retry + Logging + Metrics

                   │

                   ▼

              Boto3 SDK

                   │

                   ▼

          Amazon DynamoDB
```

---

# Responsibilities of the Repository

A repository should:

- Hide Boto3
- Execute CRUD operations
- Handle retries
- Translate exceptions
- Support pagination
- Execute transactions
- Log database activity
- Collect metrics

A repository should **not** contain business rules.

---

# Layer Responsibilities

| Layer | Responsibility |
|---------|---------------|
| Controller | HTTP handling |
| Service | Business logic |
| Repository | Data access |
| Boto3 | AWS SDK |
| DynamoDB | Database |

Each layer has one responsibility.

---

# Project Structure

```text
project/

├── app/

│   ├── api/
│   ├── services/
│   ├── repositories/
│   │
│   ├── models/
│   ├── schemas/
│   ├── config/
│   ├── database/
│   └── utils/

└── tests/
```

---

# Repository Package

Example:

```text
repositories/

├── base.py
├── customer_repository.py
├── order_repository.py
├── inventory_repository.py
└── payment_repository.py
```

Each repository owns one aggregate.

---

# Base Repository

A base repository provides reusable functionality.

```python
class BaseRepository:

    def __init__(self, table):

        self.table = table
```

Every repository inherits from it.

---

# Generic CRUD Methods

Example:

```python
class BaseRepository:

    def get(self, key):

        return self.table.get_item(
            Key=key
        )

    def put(self, item):

        return self.table.put_item(
            Item=item)
```

Shared logic reduces duplication.

---

# Domain Repository

```python
class OrderRepository(BaseRepository):

    def get_order(self, order_id):

        return self.get({
            "order_id": order_id
        })
```

The domain repository exposes business-friendly methods.

---

# Dependency Injection

Avoid:

```python
repository = OrderRepository(...)
```

inside every endpoint.

Instead:

```text
Application Startup

↓

Create Repository

↓

Inject Repository

↓

Reuse Everywhere
```

This improves testing and maintainability.

---

# Service Integration

```python
class OrderService:

    def __init__(self, repository):

        self.repository = repository

    def create(self, order):

        self.repository.save(order)
```

The service doesn't know anything about Boto3.

---

# Configuration Layer

Centralize configuration.

```text
Environment

↓

AWS Region

↓

Credentials

↓

Table Names

↓

Repository
```

Avoid hardcoded values.

---

# Logging

Every repository operation should log:

```text
Operation

↓

Table

↓

Duration

↓

Success

↓

Failure
```

Example log:

```text
PUT Orders

Latency: 18 ms

Success
```

---

# Error Translation

Instead of exposing AWS exceptions:

```text
ClientError
```

Translate them.

Example:

```text
ConditionalCheckFailedException

↓

DuplicateOrderException
```

The service layer works with domain exceptions.

---

# Retry Wrapper

```text
Repository

↓

Retry

↓

Backoff

↓

Boto3
```

Retry logic belongs in one place.

---

# Metrics

Track:

- Read latency
- Write latency
- Retry count
- Failures
- Transaction duration

Repository metrics simplify production monitoring.

---

# Pagination Support

Example:

```python
repository.list_orders(
    customer_id,
    cursor
)
```

Internally:

```text
Cursor

↓

ExclusiveStartKey

↓

Query
```

The repository hides DynamoDB implementation details.

---

# Transaction Support

Example:

```python
repository.place_order(
    order,
    payment,
    inventory
)
```

Internally:

```text
Repository

↓

TransactWriteItems

↓

Commit
```

Business logic remains clean.

---

# Batch Operations

Repository method:

```python
repository.save_orders(
    orders
)
```

Internally:

```text
batch_writer()

↓

Multiple Writes
```

The caller doesn't need to know the implementation.

---

# Mapping Domain Objects

Application:

```text
Order Object
```

Repository:

```text
Dictionary
```

DynamoDB:

```text
JSON Attributes
```

Serialization should happen inside the repository.

---

# Repository Flow

```text
HTTP Request

↓

Controller

↓

Service

↓

Repository

↓

Boto3

↓

DynamoDB

↓

Repository

↓

Service

↓

Controller

↓

HTTP Response
```

---

# Unit Testing

Repositories can be mocked.

```text
Mock Repository

↓

Service Test

↓

No AWS Required
```

Example:

```python
repository = MockOrderRepository()

service = OrderService(repository)
```

---

# Integration Testing

```text
Repository

↓

DynamoDB Local

↓

Real Queries

↓

Assertions
```

Test the repository separately from business logic.

---

# Production Example

```text
Customer Places Order

↓

OrderService

↓

OrderRepository

↓

Transaction

↓

Orders Table

↓

Inventory Table

↓

Payments Table

↓

Commit
```

---

# Repository Checklist

A production repository should provide:

✓ CRUD operations

✓ Queries

✓ Pagination

✓ Transactions

✓ Retries

✓ Logging

✓ Metrics

✓ Exception translation

✓ Configuration management

✓ Testability

---

# Performance Considerations

- Reuse Boto3 resources.
- Keep repositories lightweight.
- Avoid unnecessary object creation.
- Batch operations where possible.
- Support pagination for large datasets.
- Minimize network round trips.

---

# Security Best Practices

- Never expose AWS credentials.
- Apply least-privilege IAM roles.
- Validate data before persistence.
- Sanitize logs.
- Encrypt sensitive attributes.
- Audit repository operations.

---

# Best Practices

- One repository per aggregate.
- Keep business rules in the service layer.
- Centralize retry logic.
- Translate infrastructure exceptions.
- Inject repositories using dependency injection.
- Write unit tests with mocked repositories.
- Write integration tests against DynamoDB Local.

---

# Common Mistakes

## Mixing Business Logic

Poor:

```text
Repository

↓

Calculate Discount

↓

Save Order
```

Better:

```text
Service

↓

Calculate Discount

↓

Repository

↓

Save Order
```

---

## Returning Raw Boto3 Responses

Return domain objects instead of SDK responses.

---

## Creating Multiple Repository Instances

Repositories should generally be created once and reused throughout the application's lifecycle.

---

## Hardcoding Table Names

Avoid:

```python
Table("Orders")
```

throughout the codebase.

Load configuration centrally.

---

# Interview Notes

A common interview question is:

> **Why use a Repository Layer with DynamoDB?**

The Repository Layer separates persistence logic from business logic, improving maintainability, testability, and flexibility. It encapsulates Boto3-specific implementation details and provides a consistent interface for data access.

---

Another common question is:

> **What responsibilities should a repository have?**

A repository should manage data access, retries, exception translation, logging, metrics, pagination, and transactions. It should not contain business rules or HTTP logic.

---

Another common question is:

> **How does a repository improve testing?**

Repositories can be mocked during unit tests, allowing business logic to be tested without connecting to DynamoDB. Integration tests can validate repository behavior using DynamoDB Local.

---

Another common question is:

> **Why translate AWS exceptions into domain exceptions?**

Domain exceptions make the service layer independent of AWS SDK implementation details and produce clearer, business-oriented error handling.

---

# Key Takeaways

- A production Repository Layer encapsulates all DynamoDB interactions and shields the rest of the application from SDK details.
- Keep business logic in the Service Layer and persistence logic in repositories.
- Centralize retries, logging, metrics, transactions, and pagination to avoid duplication.
- Use dependency injection and configuration management to build modular, testable applications.
- Well-designed repositories are a hallmark of scalable, enterprise-grade backend systems.