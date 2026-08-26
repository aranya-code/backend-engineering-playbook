# 03 - Sessions, Clients & Resources

## Overview

Boto3 provides three fundamental building blocks for interacting with AWS services:

- Sessions
- Clients
- Resources

Understanding the differences between these components is essential for writing clean, scalable, and production-ready Python applications.

Many developers start using Boto3 with a few examples copied from documentation, but senior backend engineers understand **when to use each abstraction** and how to structure applications around them.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What Sessions are
- What Clients are
- What Resources are
- Client vs Resource
- When to use each
- Thread safety
- Session management
- Production architecture
- Best practices
- Interview questions

---

# Boto3 Architecture

```text
Python Application

        │

        ▼

      Session

        │

 ┌──────┴────────┐

 ▼               ▼

Client       Resource

        │

        ▼

AWS REST APIs

        │

        ▼

DynamoDB
```

Everything begins with a **Session**.

---

# What is a Session?

A Session represents an AWS configuration.

It stores:

- Credentials
- Region
- Profile
- Configuration
- Retry settings

Example:

```python
import boto3

session = boto3.Session()
```

Think of it as your authenticated connection to AWS.

---

# Session Lifecycle

```text
Application

↓

Create Session

↓

Load Credentials

↓

Load Configuration

↓

Create Client

↓

Call AWS APIs
```

---

# Creating a Session

Default session:

```python
import boto3

session = boto3.Session()
```

---

Using a named profile:

```python
session = boto3.Session(
    profile_name="development"
)
```

---

Using a specific region:

```python
session = boto3.Session(
    region_name="us-east-1"
)
```

---

# Why Use Sessions?

Sessions allow different applications—or even different parts of the same application—to use different AWS accounts or regions.

Example:

```text
Session A

↓

Development Account

────────────

Session B

↓

Production Account
```

---

# What is a Client?

A Client provides a **low-level interface** to AWS.

```python
client = boto3.client("dynamodb")
```

or

```python
client = session.client("dynamodb")
```

A Client maps almost one-to-one with AWS APIs.

---

# Client Architecture

```text
Python

↓

Client

↓

AWS API

↓

JSON

↓

Python Dictionary
```

Every Client operation closely mirrors the AWS API documentation.

---

# Example Client Operations

```python
client.get_item()

client.put_item()

client.update_item()

client.delete_item()

client.query()

client.scan()
```

Clients return dictionaries that closely resemble the raw AWS API responses.

---

# Client Advantages

- Full AWS API coverage
- Latest AWS features available first
- Precise control
- Lower-level access
- Better for advanced operations

---

# Client Disadvantages

- Verbose syntax
- Manual attribute formatting
- More complex code
- Less Pythonic

---

# What is a Resource?

A Resource is a **higher-level object-oriented abstraction** built on top of Clients.

Example:

```python
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")
```

Resources simplify common application development tasks.

---

# Resource Architecture

```text
Python

↓

Resource

↓

Client

↓

AWS API

↓

DynamoDB
```

Resources internally use Clients.

---

# Example Resource Operations

```python
table.put_item()

table.get_item()

table.update_item()

table.delete_item()

table.query()
```

Notice the code is cleaner because you're working with a table object rather than repeatedly specifying table details.

---

# Resource Advantages

- Cleaner syntax
- Object-oriented design
- Easier to read
- Better developer experience
- Ideal for CRUD applications

---

# Resource Limitations

Resources do **not** expose every AWS feature.

New DynamoDB capabilities usually appear in the Client API first.

When a feature is unavailable in Resources, use Clients.

---

# Client vs Resource

| Feature | Client | Resource |
|----------|---------|----------|
| Level | Low | High |
| Object-Oriented | No | Yes |
| API Coverage | Complete | Partial |
| Easier Syntax | No | Yes |
| Best For | Advanced features | Business applications |
| Returns | Dictionaries | Python objects |

---

# Which Should You Use?

For most backend applications:

```text
FastAPI

↓

Resource

↓

DynamoDB
```

For infrastructure automation or advanced DynamoDB features:

```text
Automation Script

↓

Client

↓

AWS APIs
```

Many production applications use **both**.

---

# Creating Clients from Sessions

```python
session = boto3.Session()

client = session.client("dynamodb")
```

Advantages:

- Explicit configuration
- Easier testing
- Better dependency injection
- Multi-account support

---

# Creating Resources from Sessions

```python
session = boto3.Session()

resource = session.resource("dynamodb")
```

Recommended for production applications.

---

# Thread Safety

## Clients

Clients are generally thread-safe.

```text
Application

↓

Shared Client

↓

Multiple Threads
```

One client instance can typically be reused across threads.

---

## Sessions

Sessions are **not intended to be shared across threads**.

Instead:

```text
Thread

↓

Own Session

↓

Shared Client
```

or initialize sessions during application startup.

---

# Connection Reuse

Creating Clients repeatedly wastes time.

Poor:

```python
def get_order():
    client = boto3.client("dynamodb")
```

Better:

```python
client = boto3.client("dynamodb")

def get_order():
    ...
```

This reduces initialization overhead.

---

# Dependency Injection

FastAPI example:

```text
Application Startup

↓

Create Session

↓

Create Resource

↓

Inject Repository

↓

Business Service
```

This keeps AWS configuration centralized.

---

# Repository Pattern

A common production architecture:

```text
FastAPI

↓

Service Layer

↓

Repository

↓

Boto3 Resource

↓

DynamoDB
```

The service layer should never call Boto3 directly.

---

# Multi-Region Applications

Sessions make multi-region architectures straightforward.

```python
us_session = boto3.Session(region_name="us-east-1")

eu_session = boto3.Session(region_name="eu-west-1")
```

Useful for:

- Global Tables
- Disaster recovery
- Multi-region deployments

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

             Boto3 Resource

                  │

                  ▼

             DynamoDB Table
```

AWS access remains isolated inside the repository layer.

---

# Performance Considerations

For high-performance applications:

- Create Sessions once during startup.
- Reuse Clients and Resources.
- Avoid repeatedly constructing AWS objects.
- Use Resources for CRUD-heavy services.
- Use Clients when advanced APIs are required.

---

# Security Best Practices

- Use IAM Roles.
- Never embed credentials in code.
- Apply least-privilege permissions.
- Centralize AWS configuration.
- Log failures without exposing sensitive information.

---

# Best Practices

- Prefer Sessions over implicit global configuration.
- Reuse Clients and Resources.
- Use Resources for application development.
- Use Clients for advanced operations.
- Separate AWS code into repository classes.
- Initialize AWS objects during application startup.
- Keep business logic independent of Boto3.

---

# Common Mistakes

## Creating Sessions Repeatedly

Poor:

```python
def handler():
    session = boto3.Session()
```

Better:

Create one Session during startup and reuse it.

---

## Mixing Business Logic with AWS Code

Avoid:

```text
Business Logic

↓

Boto3 Calls

↓

Business Logic
```

Instead:

```text
Business Logic

↓

Repository

↓

Boto3
```

---

## Using Resources for Unsupported APIs

If a required feature is unavailable through Resources, switch to the Client interface rather than trying to work around the limitation.

---

## Recreating Clients on Every Request

This adds unnecessary latency and resource usage.

---

# Interview Notes

A common interview question is:

> **What is the difference between a Boto3 Session, Client, and Resource?**

A Session stores AWS configuration such as credentials and region. A Client provides a low-level interface that maps directly to AWS APIs, while a Resource provides a higher-level, object-oriented abstraction for supported services.

---

Another common question is:

> **When should you use a Client instead of a Resource?**

Use a Client when you need access to all AWS API operations, newly released features, or fine-grained control over requests. Use a Resource for simpler, object-oriented application development.

---

Another common question is:

> **Should Boto3 Clients and Sessions be recreated for every request?**

No. Sessions, Clients, and Resources should generally be created during application startup and reused throughout the application's lifecycle to reduce initialization overhead and improve performance.

---

Another common question is:

> **How would you structure Boto3 access in a FastAPI or Django application?**

A common approach is to create a Session during application startup, initialize reusable Clients or Resources, encapsulate AWS interactions in a Repository layer, and let the Service layer call the Repository instead of interacting with Boto3 directly.

---

# Key Takeaways

- Sessions manage AWS configuration, credentials, and regions.
- Clients provide complete, low-level access to AWS APIs.
- Resources offer a cleaner, object-oriented interface for common application development tasks.
- Reuse Sessions, Clients, and Resources instead of recreating them for every request.
- Encapsulate Boto3 access within a Repository layer to keep business logic clean, testable, and maintainable.