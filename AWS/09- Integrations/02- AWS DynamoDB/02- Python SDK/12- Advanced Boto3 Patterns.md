# 12 - Advanced Boto3 Patterns

## Overview

Most tutorials teach developers how to call:

- `put_item()`
- `get_item()`
- `query()`

directly from their API endpoints.

While this works for small projects, it quickly becomes difficult to maintain in production.

Senior backend engineers design systems that are:

- Maintainable
- Testable
- Scalable
- Loosely coupled
- Easy to monitor
- Easy to extend

This chapter covers production-grade Boto3 usage patterns commonly found in enterprise Django, FastAPI, and microservice applications.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Repository Pattern
- Service Layer
- Dependency Injection
- Singleton Boto3 Resources
- Configuration Management
- Factory Pattern
- Retry Wrappers
- Generic Repository Design
- Clean Architecture
- Production Folder Structure
- Interview Questions

---

# From CRUD to Architecture

Small applications often look like this:

```text
FastAPI

↓

table.put_item()

↓

DynamoDB
```

As applications grow, this becomes difficult to maintain.

A better architecture is:

```text
FastAPI

↓

Service Layer

↓

Repository

↓

Boto3

↓

DynamoDB
```

---

# Why Direct Boto3 Calls Are Bad

Poor example:

```python
@app.post("/orders")
def create_order():

    table.put_item(...)

    table.update_item(...)

    table.query(...)
```

Problems:

- Business logic mixed with database code
- Difficult to test
- Difficult to replace DynamoDB
- Large API functions
- Duplicate code

---

# Repository Pattern

The Repository Pattern isolates database access.

```text
Application

↓

Repository

↓

Database
```

Instead of:

```text
Business Logic

↓

DynamoDB
```

---

# Repository Example

```python
class OrderRepository:

    def __init__(self, table):
        self.table = table

    def get(self, order_id):

        return self.table.get_item(
            Key={
                "order_id": order_id
            }
        ).get("Item")

    def save(self, order):

        self.table.put_item(Item=order)
```

Notice that Boto3 is hidden inside the repository.

---

# Service Layer

Business rules belong here.

```text
API

↓

Service

↓

Repository

↓

DynamoDB
```

Example:

```python
class OrderService:

    def __init__(self, repository):

        self.repository = repository

    def create_order(self, order):

        # Business validation

        self.repository.save(order)
```

---

# Benefits of Service Layer

Business logic becomes independent of:

- DynamoDB
- Boto3
- AWS

If the database changes later:

```text
DynamoDB

↓

PostgreSQL
```

only the repository changes.

---

# Dependency Injection

Instead of:

```python
class OrderService:

    repository = OrderRepository(...)
```

Inject it.

```python
service = OrderService(repository)
```

Benefits:

- Easier testing
- Mock repositories
- Better modularity

---

# Singleton Boto3 Resource

Poor:

```python
def handler():

    resource = boto3.resource("dynamodb")
```

called thousands of times.

Better:

```python
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")
```

Reuse the resource across the application.

---

# Factory Pattern

Create AWS resources in one place.

```python
import boto3

class DynamoFactory:

    @staticmethod
    def table(name):

        resource = boto3.resource(
            "dynamodb"
        )

        return resource.Table(name)
```

Usage:

```python
table = DynamoFactory.table(
    "Orders"
)
```

---

# Configuration Management

Avoid:

```python
boto3.resource(
    "dynamodb",
    region_name="us-east-1"
)
```

everywhere.

Instead:

```text
Settings

↓

Region

↓

Credentials

↓

Table Names
```

Centralize configuration.

---

# Environment-Based Configuration

Development

```text
Orders-Dev
```

Production

```text
Orders-Prod
```

Repository code remains identical.

---

# Generic Repository

Large systems often create reusable repositories.

Example:

```python
class DynamoRepository:

    def __init__(self, table):

        self.table = table

    def get(self, key):

        return self.table.get_item(
            Key=key
        )

    def put(self, item):

        return self.table.put_item(
            Item=item
        )
```

Application repositories inherit from this base.

---

# Retry Wrapper

Instead of repeating retry logic:

```python
table.put_item(...)
```

Wrap it.

```text
Repository

↓

Retry Wrapper

↓

Boto3

↓

DynamoDB
```

Every repository automatically gains:

- Retries
- Logging
- Metrics

---

# Logging Wrapper

Another common pattern:

```text
Repository

↓

Logger

↓

Retry

↓

Boto3
```

Each operation logs:

- Duration
- Table
- Operation
- Request ID

without duplicating code.

---

# Metrics Wrapper

Collect metrics automatically.

```text
Repository

↓

Metrics

↓

CloudWatch
```

Track:

- Read latency
- Write latency
- Failures
- Retry count

---

# Domain Models

Avoid passing dictionaries throughout the application.

Instead:

```text
Order Object

↓

Repository

↓

Dictionary

↓

DynamoDB
```

Serialization occurs only inside the repository.

---

# Clean Architecture

```text
                API

                 │

                 ▼

             Controller

                 │

                 ▼

              Service

                 │

                 ▼

            Repository

                 │

                 ▼

         Boto3 Adapter Layer

                 │

                 ▼

            Amazon DynamoDB
```

Dependencies point inward.

---

# Recommended Project Structure

```text
project/

│

├── app/

│   ├── api/

│   ├── services/

│   ├── repositories/

│   ├── models/

│   ├── schemas/

│   ├── config/

│   ├── database/

│   └── utils/

│

└── tests/
```

Keep DynamoDB access inside the repository package.

---

# Unit Testing

Because the repository is isolated:

```text
Mock Repository

↓

Service Tests

↓

No AWS Calls
```

Testing becomes significantly easier.

---

# Multi-Table Repositories

One service may interact with multiple tables.

```text
Order Repository

↓

Orders Table

────────────

Inventory Repository

↓

Inventory Table
```

Each repository owns one aggregate.

---

# Multi-Account Applications

Repository factory:

```text
Profile

↓

Session

↓

Repository

↓

DynamoDB
```

Useful in enterprise environments with multiple AWS accounts.

---

# Production Architecture

```text
                 Client

                    │

                    ▼

               API Gateway

                    │

                    ▼

               FastAPI API

                    │

                    ▼

             Controller Layer

                    │

                    ▼

              Service Layer

                    │

                    ▼

            Repository Layer

                    │

                    ▼

          Retry / Logging / Metrics

                    │

                    ▼

             Boto3 Resource

                    │

                    ▼

            Amazon DynamoDB
```

---

# Performance Considerations

- Reuse Sessions and Resources.
- Centralize retry logic.
- Minimize object creation.
- Keep repositories lightweight.
- Cache frequently used configuration.
- Avoid repeated AWS initialization.

---

# Security Best Practices

- Never expose Boto3 outside repositories.
- Use IAM Roles instead of access keys.
- Centralize credential management.
- Audit repository operations.
- Encrypt sensitive attributes.
- Validate inputs before persistence.

---

# Best Practices

- Use the Repository Pattern.
- Separate business logic into a Service Layer.
- Inject dependencies instead of creating them.
- Reuse Boto3 resources.
- Centralize AWS configuration.
- Build reusable repository components.
- Add logging, retries, and metrics through wrappers rather than duplicating code.

---

# Common Mistakes

## Calling Boto3 Directly from Controllers

Poor:

```text
Controller

↓

Boto3
```

Better:

```text
Controller

↓

Service

↓

Repository
```

---

## Creating Resources Repeatedly

Creating a new `boto3.resource()` for every request increases initialization overhead and complicates testing.

---

## Mixing Business Rules with Database Logic

Business decisions should live in the Service Layer, not inside Boto3 calls.

---

## Hardcoding Configuration

Avoid scattering:

- Table names
- Regions
- Credentials

throughout the codebase.

Centralize configuration.

---

# Interview Notes

A common interview question is:

> **Why use the Repository Pattern with DynamoDB?**

The Repository Pattern separates data access from business logic, making applications easier to test, maintain, and evolve. It also hides Boto3 implementation details from the rest of the application.

---

Another common question is:

> **Why shouldn't controllers call Boto3 directly?**

Direct Boto3 calls tightly couple HTTP handlers to the database, making testing difficult and spreading persistence logic throughout the application. Controllers should delegate to services, which use repositories.

---

Another common question is:

> **Why should Boto3 resources be reused?**

Creating Sessions, Clients, and Resources repeatedly introduces unnecessary overhead. Reusing them improves performance, reduces initialization cost, and simplifies dependency management.

---

Another common question is:

> **How would you structure a production FastAPI application using DynamoDB?**

A common architecture consists of Controllers (or API routes), a Service Layer for business logic, Repository classes encapsulating Boto3 interactions, centralized configuration, dependency injection, and shared retry/logging/metrics components.

---

# Key Takeaways

- Production applications should isolate DynamoDB access using the **Repository Pattern**.
- Business logic belongs in a **Service Layer**, not alongside Boto3 calls.
- Reuse Boto3 Sessions, Clients, and Resources throughout the application's lifecycle.
- Centralize configuration, retries, logging, and metrics to reduce duplication and improve maintainability.
- A clean architecture with dependency injection and well-defined layers produces applications that are easier to test, scale, and evolve.