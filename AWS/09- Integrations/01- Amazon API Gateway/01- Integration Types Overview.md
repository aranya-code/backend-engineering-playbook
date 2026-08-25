# Integration Types Overview

## Overview

An API Gateway is useful only when it is connected to a backend service. The process of connecting an API Gateway method to a backend is called an **Integration**.

When a client sends a request, API Gateway receives it and forwards it to the configured backend integration.

Amazon API Gateway supports multiple integration types depending on the application architecture and the amount of request/response transformation required.

Choosing the right integration type affects:

- Performance
- Complexity
- Cost
- Flexibility
- Maintainability

---

# What is an Integration?

An integration defines **where API Gateway sends an incoming request** and **how it communicates with the backend**.

```text
             Client
                │
                ▼
         Amazon API Gateway
                │
                ▼
         Integration Type
                │
                ▼
        Backend Service
```

The backend can be:

- AWS Lambda
- ECS
- EC2
- Application Load Balancer
- Network Load Balancer
- Any HTTP Endpoint
- AWS Services (SQS, SNS, Step Functions, etc.)

---

# Available Integration Types

API Gateway supports four primary integration types.

| Integration | Backend | Mapping Templates | Typical Use Case |
|-------------|----------|-------------------|------------------|
| Lambda Proxy | Lambda | Not Required | Modern Serverless APIs |
| Lambda Non-Proxy | Lambda | Yes | Legacy or transformed requests |
| HTTP Proxy | HTTP Backend | Not Required | Existing REST services |
| HTTP Custom | HTTP Backend | Yes | Backend transformation |
| AWS Service Integration | AWS Services | Optional | SQS, SNS, Step Functions, DynamoDB |
| Mock Integration | None | Optional | Testing and prototyping |

> **Note:** In AWS documentation, Lambda Proxy and Lambda Non-Proxy are both Lambda integrations. Similarly, HTTP Proxy and HTTP Custom are HTTP integrations.

---

# High-Level Architecture

```text
                  Client
                     │
                     ▼
              Amazon API Gateway
                     │
     ┌───────────────┼────────────────┐
     │               │                │
     ▼               ▼                ▼
 Lambda        HTTP Backend      AWS Service
     │               │                │
     ▼               ▼                ▼
 Business      Existing API      SQS / SNS
```

API Gateway selects the configured integration for each method.

---

# Request Processing

Every integration follows the same general flow.

```text
Client

↓

API Gateway

↓

Authentication

↓

Validation

↓

Integration

↓

Backend

↓

Integration Response

↓

Client
```

The difference lies in **how API Gateway communicates with the backend**.

---

# Integration Categories

Broadly speaking, integrations fall into three categories.

## 1. Lambda Integrations

Backend:

```text
AWS Lambda
```

Example:

```text
Client

↓

API Gateway

↓

Lambda

↓

Database
```

Most common for serverless applications.

---

## 2. HTTP Integrations

Backend:

```text
REST API

Microservice

Spring Boot

Django

FastAPI

Node.js

Go

Java
```

Example:

```text
Client

↓

API Gateway

↓

HTTP Backend

↓

Database
```

Useful when applications already expose HTTP endpoints.

---

## 3. AWS Service Integrations

API Gateway can invoke AWS services directly.

Example:

```text
Client

↓

API Gateway

↓

Amazon SQS
```

No Lambda function is required.

Supported services include:

- SQS
- SNS
- Step Functions
- EventBridge
- DynamoDB
- Kinesis

---

# Proxy vs Non-Proxy Integrations

One of the biggest architectural decisions is whether to use **Proxy** or **Non-Proxy** integrations.

---

## Proxy Integration

API Gateway forwards the request almost exactly as received.

```text
Client

↓

API Gateway

↓

Entire HTTP Request

↓

Backend
```

The backend is responsible for:

- Validation
- Business logic
- Response generation

API Gateway performs minimal transformation.

---

## Non-Proxy Integration

API Gateway transforms the request before sending it.

```text
Client

↓

API Gateway

↓

Mapping Template

↓

Backend
```

Similarly, backend responses can also be transformed before being returned.

---

# Proxy vs Non-Proxy Comparison

| Feature | Proxy | Non-Proxy |
|----------|-------|-----------|
| Request Mapping | ❌ | ✅ |
| Response Mapping | ❌ | ✅ |
| Simpler Configuration | ✅ | ❌ |
| Backend Flexibility | High | Medium |
| API Gateway Logic | Minimal | Extensive |
| Recommended for New APIs | ✅ | Situational |

Most modern applications use proxy integrations unless request or response transformation is required.

---

# Integration Selection Flow

```text
Need Lambda?

│

├── Yes

│      │

│      ├── Need request transformation?

│      │          │

│      │          ├── Yes → Lambda Non-Proxy

│      │          └── No → Lambda Proxy

│

└── No

       │

       ├── Existing HTTP API?

       │          │

       │          ├── Yes

       │          │      │

       │          │      ├── Need transformation?

       │          │      │

       │          │      ├── Yes → HTTP Custom

       │          │      └── No → HTTP Proxy

       │

       └── AWS Service?

                  │

                  └── AWS Service Integration
```

---

# Real-World Examples

## Example 1

A FastAPI backend running on ECS.

```text
Client

↓

API Gateway

↓

HTTP Proxy

↓

FastAPI
```

Recommended because FastAPI already handles routing and validation.

---

## Example 2

A serverless image-processing application.

```text
Client

↓

API Gateway

↓

Lambda Proxy

↓

S3
```

Simple and highly scalable.

---

## Example 3

Customer registration should place a message directly into Amazon SQS.

```text
Client

↓

API Gateway

↓

Amazon SQS
```

No Lambda function required.

---

## Example 4

Legacy XML backend.

Client sends JSON.

Backend expects XML.

```text
Client

↓

JSON

↓

API Gateway

↓

Mapping Template

↓

XML

↓

Legacy System
```

HTTP Custom Integration is appropriate because API Gateway can transform the request.

---

# Which Integration Should You Choose?

| Scenario | Recommended Integration |
|----------|--------------------------|
| New Lambda Application | Lambda Proxy |
| Existing REST API | HTTP Proxy |
| Need Request Transformation | Lambda Non-Proxy or HTTP Custom |
| Send Messages to SQS | AWS Service Integration |
| Testing API without Backend | Mock Integration |

---

# Common Interview Questions

### Which integration type is most commonly used today?

**Answer:**

Lambda Proxy Integration and HTTP Proxy Integration are the most common because they are simple, require little configuration, and allow backend applications to manage request and response processing.

---

### When should you use Non-Proxy Integration?

**Answer:**

Use Non-Proxy Integration when API Gateway must transform requests or responses, such as converting JSON to XML, renaming fields, adding headers, or supporting legacy backend systems.

---

### Can API Gateway invoke AWS services without Lambda?

**Answer:**

Yes. API Gateway supports direct AWS Service Integrations with services such as Amazon SQS, Amazon SNS, Step Functions, EventBridge, and DynamoDB, eliminating the need for an intermediary Lambda function in many scenarios.

---

### Which integration type would you use for an existing Django or FastAPI application?

**Answer:**

HTTP Proxy Integration, because the application already exposes HTTP endpoints and can handle routing, validation, and response generation.

---

# Best Practices

- Prefer **Lambda Proxy Integration** for new serverless applications.
- Prefer **HTTP Proxy Integration** for existing web services.
- Use **AWS Service Integrations** to reduce unnecessary Lambda functions.
- Use **Non-Proxy Integrations** only when request or response transformation is required.
- Keep API Gateway focused on API management and let backend services handle business logic whenever possible.

---

# Key Takeaways

- An integration defines how API Gateway communicates with backend services.
- API Gateway supports Lambda, HTTP, AWS Service, and Mock integrations.
- Proxy integrations forward requests with minimal processing and are recommended for most modern applications.
- Non-Proxy integrations enable request and response transformation using mapping templates.
- Selecting the appropriate integration type improves application simplicity, performance, and maintainability.