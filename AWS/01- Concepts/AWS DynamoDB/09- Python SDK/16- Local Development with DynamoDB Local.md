# 16 - Local Development with DynamoDB Local

## Overview

Developing directly against AWS during local development has several drawbacks:

- Requires AWS credentials
- Consumes AWS resources
- Incurs costs
- Depends on internet connectivity
- Makes automated testing difficult

Amazon provides **DynamoDB Local**, a downloadable version of DynamoDB that runs entirely on your local machine.

It behaves almost identically to the managed DynamoDB service, making it ideal for:

- Local development
- Unit testing
- Integration testing
- CI/CD pipelines
- Offline development

This chapter explains how to build a professional local development workflow using DynamoDB Local.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What DynamoDB Local is
- Benefits of local development
- Installation options
- Docker setup
- Connecting with Boto3
- Table creation
- Running tests locally
- Switching environments
- Limitations
- Best practices
- Interview questions

---

# Why DynamoDB Local?

Without DynamoDB Local:

```text
Developer

↓

Internet

↓

AWS Account

↓

DynamoDB
```

Problems:

- Internet dependency
- AWS credentials
- Cost
- Slower development

---

With DynamoDB Local:

```text
Developer

↓

Local Machine

↓

Docker

↓

DynamoDB Local
```

Development becomes:

- Faster
- Offline
- Safer
- Cheaper

---

# DynamoDB Local Architecture

```text
             FastAPI

                │

                ▼

        Repository Layer

                │

                ▼

             Boto3 SDK

                │

                ▼

        localhost:8000

                │

                ▼

         DynamoDB Local
```

Only the endpoint changes.

Application code remains the same.

---

# Installation Options

There are several ways to run DynamoDB Local.

- Docker (recommended)
- Java JAR
- Docker Compose
- CI/CD containers

Most production teams prefer Docker.

---

# Running with Docker

```bash
docker run -d \
    --name dynamodb-local \
    -p 8000:8000 \
    amazon/dynamodb-local
```

Verify:

```bash
docker ps
```

You should see:

```text
amazon/dynamodb-local
```

---

# Docker Compose

```yaml
version: "3.9"

services:

  dynamodb:

    image: amazon/dynamodb-local

    container_name: dynamodb-local

    ports:
      - "8000:8000"

    command: "-jar DynamoDBLocal.jar -sharedDb"
```

Start:

```bash
docker compose up -d
```

---

# Verify the Service

```bash
aws dynamodb list-tables \
    --endpoint-url http://localhost:8000
```

Initially:

```json
{
  "TableNames": []
}
```

---

# Connecting with Boto3

```python
import boto3

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)
```

Dummy credentials satisfy the SDK even though authentication is not enforced locally.

---

# Why Dummy Credentials?

Boto3 expects credentials.

Even though DynamoDB Local ignores authentication, the SDK still requires values.

Example:

```python
aws_access_key_id="dummy"
aws_secret_access_key="dummy"
```

---

# Creating a Table

```python
table = dynamodb.create_table(

    TableName="Orders",

    KeySchema=[
        {
            "AttributeName": "order_id",
            "KeyType": "HASH"
        }
    ],

    AttributeDefinitions=[
        {
            "AttributeName": "order_id",
            "AttributeType": "S"
        }
    ],

    BillingMode="PAY_PER_REQUEST"
)
```

The API is identical to AWS DynamoDB.

---

# Listing Tables

```python
client = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8000"
)

response = client.list_tables()

print(response["TableNames"])
```

---

# CRUD Operations

Nothing changes.

```python
table.put_item(
    Item={
        "order_id": "1001"
    }
)
```

```python
table.get_item(
    Key={
        "order_id": "1001"
    }
)
```

Your application code remains portable.

---

# Environment Configuration

Development:

```text
DYNAMODB_ENDPOINT=http://localhost:8000
```

Production:

```text
DYNAMODB_ENDPOINT=None
```

Your repository should read this configuration instead of hardcoding endpoints.

---

# Configuration Example

```python
import os

endpoint = os.getenv(
    "DYNAMODB_ENDPOINT"
)

resource = boto3.resource(
    "dynamodb",
    endpoint_url=endpoint
)
```

The same code works locally and in AWS.

---

# Using DynamoDB Local in FastAPI

```text
FastAPI

↓

Repository

↓

Boto3

↓

Environment Variable

↓

Local or AWS
```

No changes are required in business logic.

---

# Running Integration Tests

```text
Pytest

↓

Repository

↓

DynamoDB Local

↓

Assertions
```

Integration tests become:

- Repeatable
- Fast
- Offline

---

# CI/CD Integration

Typical pipeline:

```text
GitHub Actions

↓

Start DynamoDB Local

↓

Run Tests

↓

Stop Container

↓

Deploy
```

No AWS account is required for repository testing.

---

# Local Development Workflow

```text
Start Docker

↓

Run DynamoDB Local

↓

Create Tables

↓

Run Application

↓

Develop

↓

Run Tests

↓

Stop Container
```

---

# Switching Between Environments

```text
Environment

│

├── Local

│      ↓

│ localhost:8000

│

└── Production

       ↓

AWS DynamoDB Endpoint
```

Environment variables make switching seamless.

---

# Repository Architecture

```text
Controller

↓

Service

↓

Repository

↓

Boto3

↓

Environment

↓

AWS

OR

Local
```

The repository remains environment-independent.

---

# Limitations of DynamoDB Local

Although highly compatible, DynamoDB Local is **not** a perfect replacement for the managed AWS service.

Some differences include:

- No IAM authentication
- No CloudWatch metrics
- No Auto Scaling
- No DynamoDB Streams
- No Global Tables
- No PITR (Point-in-Time Recovery)
- No CloudTrail integration

Always perform final validation against real AWS before production deployment.

---

# Local vs AWS

| Feature | DynamoDB Local | AWS DynamoDB |
|----------|----------------|--------------|
| Internet Required | ❌ | ✅ |
| Cost | Free | Usage-based |
| IAM | ❌ | ✅ |
| Auto Scaling | ❌ | ✅ |
| Streams | ❌ | ✅ |
| Global Tables | ❌ | ✅ |
| CI/CD Friendly | ✅ | Limited |
| Local Development | Excellent | Poor |

---

# Production Architecture

```text
             Developer

                 │

                 ▼

            FastAPI API

                 │

                 ▼

          Repository Layer

                 │

                 ▼

              Boto3 SDK

                 │

        ┌────────┴────────┐

        ▼                 ▼

DynamoDB Local      AWS DynamoDB

Development         Production
```

---

# Performance Considerations

DynamoDB Local is intended for development and testing.

Do not use it to:

- Benchmark production performance
- Estimate AWS latency
- Measure cloud throughput

Performance characteristics differ from the managed service.

---

# Security Best Practices

- Never use production credentials locally.
- Keep local and production configurations separate.
- Store environment variables outside source code.
- Do not commit local configuration files containing secrets.
- Validate production deployments against real AWS resources.

---

# Best Practices

- Use Docker for local development.
- Configure endpoints through environment variables.
- Use DynamoDB Local for integration testing.
- Keep production and local configurations separate.
- Create tables automatically during test setup.
- Destroy test data after each test suite.

---

# Common Mistakes

## Hardcoding Local Endpoints

Poor:

```python
endpoint_url="http://localhost:8000"
```

Better:

```python
endpoint_url=os.getenv(
    "DYNAMODB_ENDPOINT"
)
```

---

## Using Production Tables During Development

Never develop directly against production tables.

Always use:

- DynamoDB Local
- Development AWS accounts
- Sandbox environments

---

## Assuming Feature Parity

Some AWS features are unavailable locally.

Always validate:

- IAM permissions
- Streams
- Global Tables
- Auto Scaling

against real AWS.

---

## Sharing Local Databases

Each developer should have an isolated local environment to avoid conflicts and ensure reproducible testing.

---

# Interview Notes

A common interview question is:

> **What is DynamoDB Local?**

DynamoDB Local is a downloadable version of Amazon DynamoDB that runs on a developer's machine, enabling local development, testing, and CI/CD without connecting to AWS.

---

Another common question is:

> **Why use DynamoDB Local instead of AWS during development?**

It reduces cost, removes internet dependency, speeds up development, and enables deterministic integration testing without affecting cloud resources.

---

Another common question is:

> **How does an application switch between DynamoDB Local and AWS?**

The application should externalize the endpoint configuration (typically through environment variables). The repository or database configuration layer chooses the appropriate endpoint without changing business logic.

---

Another common question is:

> **Can DynamoDB Local completely replace AWS DynamoDB?**

No. DynamoDB Local lacks several managed-service capabilities such as IAM, Streams, Global Tables, Auto Scaling, CloudWatch integration, and Point-in-Time Recovery. Final validation should always occur against the real AWS service.

---

# Key Takeaways

- DynamoDB Local enables fast, offline, and cost-effective development and integration testing.
- The Boto3 API remains nearly identical; only the endpoint configuration changes.
- Docker is the recommended way to run DynamoDB Local in professional development environments.
- Externalize configuration so the same codebase works with both local and AWS environments.
- Use DynamoDB Local for development and testing, but validate production-specific features against the managed AWS service.