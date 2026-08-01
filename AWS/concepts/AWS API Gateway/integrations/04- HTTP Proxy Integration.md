# HTTP Proxy Integration

## Overview

**HTTP Proxy Integration** allows Amazon API Gateway to forward incoming HTTP requests directly to an existing HTTP backend with **minimal processing**.

Unlike Custom HTTP Integration, API Gateway does **not** use Mapping Templates to transform the request or response. Instead, it acts as a **reverse proxy**, passing the client's request almost unchanged to the backend and returning the backend's response to the client.

HTTP Proxy Integration is commonly used when you already have applications running on:

- Amazon EC2
- Amazon ECS
- Amazon EKS
- Application Load Balancer (ALB)
- Network Load Balancer (NLB)
- On-premises servers
- Third-party HTTP APIs

It is the recommended choice for integrating existing REST APIs with API Gateway.

---

# Architecture

```text
                 Client
                    │
                    ▼
           Amazon API Gateway
                    │
                    ▼
             HTTP Backend
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
      FastAPI     Django     Spring Boot
```

API Gateway forwards the request without modifying its structure.

---

# Request Flow

```text
Client

↓

HTTP Request

↓

API Gateway

↓

HTTP Proxy

↓

Backend Server

↓

HTTP Response

↓

API Gateway

↓

Client
```

Notice that API Gateway performs almost no transformation.

---

# How It Works

Suppose a client sends:

```http
GET /products/100?page=2
```

Headers:

```http
Authorization: Bearer abc123

Content-Type: application/json
```

API Gateway forwards:

- HTTP Method
- URL
- Headers
- Query Parameters
- Path Parameters
- Request Body

directly to the backend.

Backend receives exactly what the client sent.

---

# Example Architecture

```text
               Internet
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
        Application Load Balancer
                   │
          ┌────────┴────────┐
          ▼                 ▼
     FastAPI            Django
```

API Gateway provides security and monitoring, while the backend application handles business logic.

---

# Supported HTTP Methods

HTTP Proxy supports all standard HTTP methods.

```text
GET

POST

PUT

PATCH

DELETE

OPTIONS

HEAD
```

The backend application determines how each method is processed.

---

# URL Forwarding

Suppose API Gateway exposes:

```text
GET /users/{id}
```

Client request:

```http
GET /users/100
```

Backend receives:

```http
GET /users/100
```

The path is preserved.

---

# Query Parameters

Client request:

```http
GET /products?page=5&sort=price
```

Backend receives:

```http
GET /products?page=5&sort=price
```

No transformation occurs.

---

# Headers

Client sends:

```http
Authorization: Bearer abc

Content-Type: application/json
```

Backend receives the same headers.

Additional headers can be configured if required.

---

# Request Body

Client request:

```json
{
    "name": "Laptop",
    "price": 50000
}
```

Backend receives exactly the same JSON body.

---

# Response Flow

Backend returns:

```http
HTTP/1.1 200 OK
```

```json
{
    "id":100,
    "name":"Laptop"
}
```

API Gateway forwards the response directly to the client.

No response mapping occurs.

---

# Advantages

## Very Simple

Minimal configuration is required.

No Mapping Templates.

No VTL.

---

## High Performance

Since API Gateway performs little processing, latency is lower.

---

## Existing Applications

Works well with existing REST APIs.

No application changes are required.

---

## Easy Migration

Legacy applications can be exposed through API Gateway without rewriting backend code.

---

## Backend Controls Everything

Business logic remains inside the backend service.

---

# Disadvantages

## No Request Transformation

Requests cannot be modified before reaching the backend.

---

## No Response Transformation

Backend responses cannot be filtered or reshaped.

---

## Backend Must Handle Validation

The backend is responsible for:

- Input validation
- Error handling
- Response formatting

---

# Typical Use Cases

HTTP Proxy Integration is commonly used for:

- Django applications
- FastAPI applications
- Spring Boot APIs
- Express.js applications
- ASP.NET APIs
- Legacy REST APIs
- Containerized applications
- Existing enterprise services

---

# Example: FastAPI

```text
Client

↓

API Gateway

↓

FastAPI

↓

PostgreSQL
```

API Gateway secures the API.

FastAPI handles routing and business logic.

---

# Example: Django REST Framework

```text
Client

↓

API Gateway

↓

Django REST Framework

↓

MySQL
```

No Mapping Templates are required.

---

# Example: ECS

```text
Client

↓

API Gateway

↓

Application Load Balancer

↓

Amazon ECS

↓

Container
```

A common production architecture for microservices.

---

# HTTP Proxy vs HTTP Custom Integration

| Feature | HTTP Proxy | HTTP Custom |
|----------|------------|-------------|
| Mapping Templates | ❌ | ✅ |
| Request Transformation | ❌ | ✅ |
| Response Transformation | ❌ | ✅ |
| Simplicity | High | Medium |
| Performance | Higher | Slightly Lower |
| Recommended | ✅ | Only if Needed |

---

# HTTP Proxy vs Lambda Proxy

| Feature | HTTP Proxy | Lambda Proxy |
|----------|------------|--------------|
| Backend | HTTP Server | AWS Lambda |
| Infrastructure | Managed by You | Serverless |
| Scaling | Backend Responsibility | Automatic |
| Request Forwarding | Direct HTTP | Lambda Event |
| Business Logic | Backend | Lambda Function |

Choose HTTP Proxy when your backend already exposes HTTP endpoints.

Choose Lambda Proxy for serverless architectures.

---

# Security

API Gateway can still provide:

- IAM Authentication
- JWT Authentication
- Cognito Authorizers
- Lambda Authorizers
- API Keys (REST API)
- Rate Limiting
- Logging
- Monitoring
- WAF Integration

The backend does not need to implement these features unless application-specific authorization is required.

---

# Real-World Example

A company already has a Django application running behind an Application Load Balancer.

Instead of exposing the ALB directly:

```text
Internet

↓

ALB

↓

Django
```

They expose:

```text
Internet

↓

API Gateway

↓

ALB

↓

Django
```

Benefits:

- Better security
- Authentication
- Monitoring
- Rate limiting
- Centralized API management

No changes to the Django application are necessary.

---

# Common Interview Questions

### What is HTTP Proxy Integration?

HTTP Proxy Integration forwards incoming HTTP requests directly to an HTTP backend with minimal processing and no request or response transformation.

---

### Does HTTP Proxy Integration use Mapping Templates?

No.

Requests and responses are forwarded almost exactly as they are received.

---

### When should you use HTTP Proxy Integration?

When integrating existing HTTP applications such as Django, FastAPI, Spring Boot, Express.js, or any REST API that already performs its own validation and response generation.

---

### Why is HTTP Proxy Integration commonly used with microservices?

Because each microservice already exposes HTTP endpoints. API Gateway provides centralized API management while allowing services to continue handling their own business logic.

---

# Best Practices

- Use HTTP Proxy Integration for existing REST APIs.
- Keep business logic inside the backend service.
- Let API Gateway handle authentication, throttling, monitoring, and logging.
- Avoid unnecessary request transformations.
- Place an Application Load Balancer in front of multiple backend instances for high availability.
- Use HTTPS between API Gateway and backend services whenever possible.

---

# Key Takeaways

- HTTP Proxy Integration forwards requests directly to HTTP backends with minimal processing.
- It requires no Mapping Templates or Velocity Template Language (VTL).
- It is ideal for existing web applications such as Django, FastAPI, Spring Boot, and other REST services.
- API Gateway continues to provide authentication, authorization, monitoring, throttling, and API management.
- HTTP Proxy Integration is the preferred choice for exposing existing HTTP-based microservices through Amazon API Gateway.