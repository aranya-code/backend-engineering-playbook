# 06 - DynamoDB + API Gateway

## Overview

Amazon API Gateway and Amazon DynamoDB form one of the most widely used serverless architectures on AWS.

API Gateway exposes secure HTTP APIs to clients, while DynamoDB provides a highly scalable NoSQL database for storing application data.

In most production systems, API Gateway integrates with DynamoDB through AWS Lambda, although direct AWS Service Integrations are also supported for simple use cases.

Typical architecture:

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

               AWS Lambda

                   │

                   ▼

               DynamoDB
```

This architecture powers:

- REST APIs
- Mobile backends
- SaaS platforms
- Internal APIs
- Microservices
- Serverless applications

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why API Gateway and DynamoDB are used together
- Request-response architecture
- CRUD APIs
- Direct integrations
- Authentication
- Authorization
- API throttling
- Caching
- Production architectures
- Best practices
- Interview questions

---

# Why Combine API Gateway with DynamoDB?

Without API Gateway:

```text
Client

↓

Direct Database Access
```

Problems:

- No authentication
- No validation
- No authorization
- Database exposed publicly
- Difficult to monitor

---

With API Gateway:

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

Benefits:

- Secure API layer
- Authentication
- Authorization
- Validation
- Logging
- Rate limiting

---

# High-Level Architecture

```text
               Mobile App

                     │

                     ▼

              API Gateway

                     │

                     ▼

               AWS Lambda

                     │

        ┌────────────┴────────────┐

        ▼                         ▼

   DynamoDB                 CloudWatch
```

---

# Request Flow

```text
Client

↓

HTTP Request

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

Lambda

↓

API Gateway

↓

HTTP Response
```

---

# CRUD Example

Create

```text
POST /orders
```

↓

```text
Lambda

↓

PutItem()
```

---

Read

```text
GET /orders/{id}
```

↓

```text
Lambda

↓

GetItem()
```

---

Update

```text
PUT /orders/{id}
```

↓

```text
UpdateItem()
```

---

Delete

```text
DELETE /orders/{id}
```

↓

```text
DeleteItem()
```

---

# API Design Example

```text
/users

/users/{id}

/orders

/orders/{id}

/products

/products/{id}
```

Keep resources noun-based.

Avoid:

```text
/createUser

/getOrder

/deleteItem
```

---

# REST API Example

```text
POST /orders

↓

Validate Request

↓

Save Order

↓

Return 201
```

---

# Query Example

```text
GET /orders?customerId=1001
```

↓

```text
Lambda

↓

Query()

↓

Partition Key
```

Avoid using `Scan()` for API endpoints.

---

# Authentication

API Gateway supports multiple authentication methods.

```text
Client

↓

JWT Token

↓

API Gateway

↓

Authorized?
```

Common options:

- IAM
- Amazon Cognito
- Lambda Authorizers
- JWT Authorizers

---

# Authorization

Authentication identifies the user.

Authorization determines what they can access.

Example:

```text
Customer A

↓

GET /orders/101

↓

Own Order?

↓

Allow
```

---

# Request Validation

Validate input before reaching Lambda.

Example:

```text
POST

↓

JSON Schema Validation

↓

Lambda
```

Benefits:

- Lower Lambda invocations
- Reduced cost
- Better security

---

# API Gateway Caching

Frequently requested data can be cached.

```text
Client

↓

API Gateway Cache

↓

Cache Hit?

↓

YES

↓

Return Response

────────────

NO

↓

Lambda

↓

DynamoDB
```

Caching reduces:

- Latency
- DynamoDB reads
- Lambda invocations

---

# API Throttling

Protect backend services.

```text
Client

↓

10000 Requests

↓

API Gateway

↓

Throttle

↓

Allowed Requests
```

Benefits:

- Prevent abuse
- Protect DynamoDB
- Maintain availability

---

# Error Handling

```text
API Gateway

↓

Lambda Error

↓

HTTP Status Code

↓

Client
```

Common responses:

| Status | Meaning |
|---------|----------|
| 200 | Success |
| 201 | Resource Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

# Direct DynamoDB Integration

API Gateway supports direct AWS service integration.

```text
Client

↓

API Gateway

↓

DynamoDB
```

Advantages:

- No Lambda cost
- Lower latency
- Simpler architecture

Limitations:

- Limited business logic
- More difficult validation
- Complex request mapping

Recommended for simple CRUD APIs only.

---

# Lambda Integration

Most production systems use Lambda.

```text
API Gateway

↓

Lambda

↓

Business Logic

↓

DynamoDB
```

Advantages:

- Validation
- Authorization
- Logging
- Complex workflows
- External integrations

---

# Monitoring

Monitor:

API Gateway

- Requests
- Latency
- 4XX errors
- 5XX errors
- Cache hit ratio

Lambda

- Duration
- Errors
- Concurrent executions

DynamoDB

- RCUs
- WCUs
- Throttling
- Latency

---

# Production Architecture

```text
                      Users

                         │

                   Route 53

                         │

                         ▼

                 Amazon CloudFront

                         │

                         ▼

                  Amazon API Gateway

                         │

                 Lambda Authorizer

                         │

                         ▼

                    AWS Lambda

          ┌──────────────┼──────────────┐

          ▼              ▼              ▼

     DynamoDB      EventBridge     CloudWatch

          │

          ▼

   DynamoDB Streams

          │

          ▼

      Background Lambda
```

---

# Performance Considerations

To build high-performance APIs:

- Use Query instead of Scan.
- Enable API Gateway caching for read-heavy endpoints.
- Minimize response payloads.
- Use Projection Expressions.
- Reuse SDK clients in Lambda.
- Batch reads and writes when appropriate.
- Optimize partition key design.

---

# Security Best Practices

- Never expose DynamoDB directly to clients.
- Enable authentication on every endpoint.
- Apply least-privilege IAM roles.
- Validate all request payloads.
- Encrypt DynamoDB with AWS KMS.
- Enable AWS WAF for public APIs.
- Log API requests using CloudWatch.

---

# Best Practices

- Design RESTful APIs around resources.
- Use Lambda for business logic.
- Validate requests at API Gateway.
- Use Query instead of Scan.
- Return appropriate HTTP status codes.
- Implement pagination for large datasets.
- Enable throttling and caching.
- Monitor latency and error rates.

---

# Common Mistakes

## Exposing DynamoDB Directly

Poor:

```text
Client

↓

DynamoDB
```

Better:

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

---

## Using Scan in APIs

```text
GET /products

↓

Scan()
```

This performs poorly on large tables.

Prefer:

```text
Query()

↓

Indexed Access
```

---

## Missing Authentication

Never expose production APIs without authentication.

---

## Returning Entire Items

Instead of:

```text
SELECT *
```

Use:

```text
Projection Expression
```

Return only required attributes.

---

## No Rate Limiting

Public APIs should always enforce throttling to prevent abuse.

---

# Production Considerations

Enterprise architectures commonly include:

```text
API Gateway

↓

Lambda

↓

DynamoDB

↓

EventBridge

↓

SNS

↓

SQS

↓

Step Functions

↓

CloudWatch

↓

AWS X-Ray
```

This enables secure, observable, and highly scalable serverless applications.

---

# Interview Notes

A common interview question is:

> **Why use API Gateway with DynamoDB?**

API Gateway provides a secure HTTP interface with authentication, authorization, validation, throttling, and monitoring, while DynamoDB handles scalable data storage. Together they form the foundation of many serverless APIs.

---

Another common question is:

> **Should API Gateway connect directly to DynamoDB?**

For simple CRUD operations, direct AWS service integration can reduce latency and cost. However, most production systems use Lambda between API Gateway and DynamoDB to implement validation, business logic, and integrations with other services.

---

Another common question is:

> **How do you improve API performance when using DynamoDB?**

Use efficient partition key design, prefer `Query` over `Scan`, enable API Gateway caching for read-heavy endpoints, use Projection Expressions, batch requests when appropriate, and reuse AWS SDK clients inside Lambda.

---

Another common question is:

> **How do you secure an API backed by DynamoDB?**

Enable authentication (IAM, Cognito, or JWT), authorize access using least-privilege IAM policies, validate requests at API Gateway, encrypt DynamoDB using AWS KMS, protect public APIs with AWS WAF, and monitor access using CloudWatch and CloudTrail.

---

# Key Takeaways

- API Gateway provides the secure entry point for applications, while DynamoDB stores application data.
- The most common architecture is **API Gateway → Lambda → DynamoDB**.
- Direct API Gateway to DynamoDB integration is suitable for simple CRUD APIs, but Lambda offers greater flexibility for production systems.
- Features such as authentication, request validation, caching, throttling, and monitoring are essential for production-grade APIs.
- Combining API Gateway with Lambda, DynamoDB, EventBridge, and CloudWatch creates a scalable, secure, and observable serverless platform.