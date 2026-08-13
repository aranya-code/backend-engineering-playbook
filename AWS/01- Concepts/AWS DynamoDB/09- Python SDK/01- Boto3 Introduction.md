# 01 - Boto3 Introduction

## Overview

Boto3 is the official AWS SDK for Python. It enables Python applications to interact with AWS services programmatically, including Amazon DynamoDB.

Whether you're building:

- REST APIs
- Serverless applications
- Background workers
- Data pipelines
- Automation scripts
- Infrastructure tools

Boto3 is the standard way to communicate with DynamoDB from Python.

For backend engineers using Django, FastAPI, Flask, or AWS Lambda, Boto3 is an essential library.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What Boto3 is
- How Boto3 communicates with AWS
- Clients vs Resources
- Authentication
- Sessions
- Request lifecycle
- Error handling
- Best practices
- Production considerations
- Interview questions

---

# What is Boto3?

Boto3 is the **official Python Software Development Kit (SDK)** for AWS.

It allows Python code to call AWS APIs without manually creating HTTP requests.

Instead of:

```text
Python

↓

HTTP Request

↓

AWS REST API

↓

JSON Response
```

Boto3 abstracts the HTTP layer.

```text
Python Code

↓

Boto3

↓

AWS API

↓

AWS Service
```

---

# Installing Boto3

Install using pip.

```bash
pip install boto3
```

Verify the installation.

```bash
python -c "import boto3; print(boto3.__version__)"
```

---

# Boto3 Architecture

```text
Python Application

        │

        ▼

      Boto3

        │

        ▼

Botocore Library

        │

        ▼

AWS REST APIs

        │

        ▼

AWS Services
```

---

# How Boto3 Communicates with DynamoDB

```text
Application

↓

table.get_item()

↓

Boto3

↓

AWS Signature V4

↓

HTTPS Request

↓

DynamoDB

↓

JSON Response

↓

Python Dictionary
```

Developers interact with Python objects while Boto3 handles request signing, retries, serialization, and authentication.

---

# Core Components

Boto3 mainly exposes:

- Sessions
- Clients
- Resources

---

# Sessions

A session represents AWS configuration.

It stores:

- Credentials
- Region
- Profile
- Configuration

```python
import boto3

session = boto3.Session()
```

---

# Clients

Clients provide a **low-level** interface.

```python
client = boto3.client("dynamodb")
```

Characteristics:

- Maps closely to AWS APIs
- Returns dictionaries
- Supports every AWS operation
- Best for advanced features

---

# Resources

Resources provide a **higher-level object-oriented interface**.

```python
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")
```

Characteristics:

- Easier to read
- Object-oriented
- Common choice for application development
- Available for selected AWS services

---

# Client vs Resource

| Feature | Client | Resource |
|----------|---------|----------|
| API Level | Low-level | High-level |
| Ease of Use | Moderate | Easy |
| Object-Oriented | No | Yes |
| Full API Coverage | Yes | Partial |
| Typical Use | Advanced operations | Application development |

---

# Authentication

Boto3 automatically searches for AWS credentials in a predefined order.

Typical sources include:

```text
Environment Variables

↓

AWS Credentials File

↓

AWS Config File

↓

IAM Role

↓

EC2 Instance Profile

↓

Lambda Execution Role
```

Applications running on AWS should typically use IAM roles instead of hardcoded credentials.

---

# Request Lifecycle

```text
Application

↓

Boto3

↓

Credentials

↓

Sign Request

↓

HTTPS

↓

AWS API

↓

Response
```

---

# Typical DynamoDB Operations

Using Boto3, common operations include:

```python
table.put_item()

table.get_item()

table.update_item()

table.delete_item()

table.query()

table.scan()
```

These methods correspond to DynamoDB API operations.

---

# Exception Handling

Boto3 raises exceptions when requests fail.

Typical reasons include:

- Missing table
- Invalid request
- Permission denied
- Throughput exceeded
- Validation errors

Applications should catch expected exceptions and log sufficient context for troubleshooting.

---

# Logging

A production application should log:

- Request IDs
- Error messages
- Retry attempts
- Failed operations
- Latency

Avoid logging sensitive information such as credentials or confidential data.

---

# Production Architecture

```text
             FastAPI / Django

                    │

                    ▼

                 Boto3

                    │

                    ▼

             DynamoDB Table

                    │

                    ▼

              CloudWatch Logs
```

The same architecture applies to Lambda functions and background workers.

---

# Performance Considerations

To maximize performance:

- Reuse Boto3 clients and resources.
- Avoid creating new sessions for every request.
- Prefer `Query` over `Scan`.
- Batch reads and writes when possible.
- Retrieve only required attributes.
- Handle retries using exponential backoff.

---

# Security Best Practices

- Use IAM roles whenever possible.
- Never hardcode AWS credentials.
- Rotate long-lived access keys.
- Apply least-privilege IAM policies.
- Encrypt DynamoDB tables using AWS KMS.
- Enable CloudTrail for auditing.

---

# Best Practices

- Reuse clients across requests.
- Separate AWS access into service classes or repositories.
- Handle expected exceptions gracefully.
- Keep AWS configuration outside application code.
- Use environment-specific IAM roles.
- Monitor latency and throttling.

---

# Common Mistakes

## Creating a New Client for Every Request

Poor:

```python
def handler():
    client = boto3.client("dynamodb")
```

Better:

```python
client = boto3.client("dynamodb")

def handler():
    ...
```

---

## Hardcoding Credentials

Never store AWS access keys in source code.

Use IAM roles or secure credential providers instead.

---

## Using Scan Unnecessarily

Prefer `Query` whenever an appropriate partition key is available.

---

## Ignoring Exceptions

Always handle AWS service errors and provide meaningful logs.

---

# Interview Notes

A common interview question is:

> **What is Boto3?**

Boto3 is the official AWS SDK for Python. It provides a Python interface for interacting with AWS services such as DynamoDB, S3, Lambda, and SQS.

---

Another common question is:

> **What is the difference between a Boto3 client and a resource?**

A client provides a low-level interface that maps directly to AWS APIs and supports all operations. A resource provides a higher-level, object-oriented abstraction that simplifies common tasks for supported services.

---

Another common question is:

> **How does Boto3 authenticate with AWS?**

Boto3 uses the AWS credential provider chain, checking environment variables, shared credentials files, IAM roles, and other configured providers until valid credentials are found.

---

Another common question is:

> **Why should Boto3 clients be reused?**

Creating clients repeatedly adds unnecessary overhead. Reusing clients improves performance, reduces initialization costs, and is especially beneficial in long-running applications and AWS Lambda execution environments.

---

# Key Takeaways

- Boto3 is the official Python SDK for AWS and the standard way to access DynamoDB from Python.
- It provides both low-level **clients** and higher-level **resources**.
- Authentication is handled automatically through the AWS credential provider chain.
- Reusing clients, applying least-privilege IAM policies, and handling exceptions properly are essential production practices.
- Mastering Boto3 is fundamental for building Python applications that interact with AWS services.