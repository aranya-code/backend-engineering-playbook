# Introduction to API Gateway

## Overview

Modern applications rarely consist of a single backend service. Instead, they are built using multiple microservices, serverless functions, databases, and third-party APIs. Exposing each service directly to clients creates security risks, increases complexity, and makes API management difficult.

Amazon API Gateway solves this problem by acting as a fully managed API management service. It provides a single entry point for client applications and handles request routing, authentication, authorization, throttling, monitoring, caching, and traffic management before forwarding requests to backend services.

Instead of every client knowing where every backend service is located, clients only communicate with API Gateway, which becomes the front door of your application.

---

# Why API Gateway?

Without an API Gateway, every client must communicate directly with backend services.

```text
                Without API Gateway

           Mobile App
                 │
                 ├────────► User Service
                 │
Web App ─────────┼────────► Order Service
                 │
                 ├────────► Payment Service
                 │
                 ├────────► Inventory Service
                 │
                 └────────► Notification Service
```

Problems with this approach:

- Clients must know every backend endpoint.
- Authentication must be implemented separately for each service.
- Difficult to apply rate limiting.
- No centralized logging.
- Tight coupling between clients and services.
- Backend changes affect clients.

---

With API Gateway:

```text
                  With API Gateway

              Mobile App
                    │
                    │
              Web Application
                    │
                    ▼
             Amazon API Gateway
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
 User Service   Order Service   Payment Service
     │              │              │
     ├──────────────┼──────────────┤
     ▼              ▼              ▼
 Inventory      Notification     Lambda
```

Benefits:

- Single API endpoint
- Centralized authentication
- Request validation
- Rate limiting
- Monitoring
- Logging
- Caching
- Easier version management

---

# What is Amazon API Gateway?

Amazon API Gateway is a fully managed AWS service that allows developers to:

- Create APIs
- Publish APIs
- Secure APIs
- Monitor APIs
- Maintain APIs at any scale

It supports REST APIs, HTTP APIs, and WebSocket APIs.

API Gateway automatically scales with incoming traffic, eliminating the need to manage API servers.

---

# Where Does API Gateway Fit?

A typical AWS architecture looks like this:

```text
                    Internet
                        │
                        ▼
                Amazon API Gateway
                        │
      ┌─────────────────┼──────────────────┐
      │                 │                  │
      ▼                 ▼                  ▼
    Lambda            ECS/Fargate         EC2
      │                 │                  │
      └──────────────┬──┴──────────────┬───┘
                     ▼                 ▼
                DynamoDB          Amazon RDS
```

API Gateway simply routes requests to the appropriate backend.

---

# Backend Services Supported

API Gateway can integrate with many AWS and external services.

| Backend | Supported |
|----------|-----------|
| AWS Lambda | ✅ |
| Amazon ECS | ✅ |
| Amazon EC2 | ✅ |
| Elastic Load Balancer (ALB/NLB) | ✅ |
| AWS Step Functions | ✅ |
| Amazon SQS | ✅ |
| Amazon SNS | ✅ |
| DynamoDB | ✅ |
| External HTTP APIs | ✅ |

---

# Core Responsibilities

API Gateway does much more than route HTTP requests.

Its primary responsibilities include:

- Request routing
- Authentication
- Authorization
- Request validation
- Response transformation
- Rate limiting
- API versioning
- Monitoring
- Logging
- Caching
- Traffic management

Think of API Gateway as the security guard and traffic controller sitting in front of your backend.

---

# Typical Request Flow

```text
Browser / Mobile App
          │
          ▼
   Amazon API Gateway
          │
          │ Authentication
          │ Authorization
          │ Request Validation
          │ Throttling
          │ Logging
          ▼
     Backend Service
          │
          ▼
      Database
          │
          ▼
   Response returned
          │
          ▼
      API Gateway
          │
          ▼
        Client
```

---

# Real-World Example

Imagine an e-commerce application.

Instead of exposing multiple backend URLs:

```text
users.company.com

orders.company.com

inventory.company.com

payment.company.com
```

Users access a single API:

```text
https://api.company.com
```

API Gateway internally routes requests:

```text
GET /users
        │
        ▼
User Service

GET /orders
        │
        ▼
Order Service

POST /payments
        │
        ▼
Payment Service

GET /products
        │
        ▼
Inventory Service
```

The client never needs to know where these services are hosted.

---

# Advantages of API Gateway

## Simplified Client Applications

Clients only need one endpoint.

---

## Improved Security

Authentication and authorization can be handled centrally using:

- IAM
- Amazon Cognito
- Lambda Authorizers
- JWT Tokens
- Resource Policies

---

## Better Scalability

API Gateway automatically scales based on incoming traffic.

No infrastructure management is required.

---

## Built-in Monitoring

Integrated with:

- Amazon CloudWatch
- AWS X-Ray
- Access Logs

This makes troubleshooting much easier.

---

## Cost Effective

You only pay for:

- API requests
- Data transferred
- Optional caching

There are no servers to manage.

---

# Common Use Cases

API Gateway is commonly used for:

- Serverless applications
- Microservices
- Mobile backends
- Single Page Applications (SPA)
- Public REST APIs
- Internal enterprise APIs
- Third-party integrations
- SaaS platforms

---

# When Should You Use API Gateway?

Use API Gateway when you need:

- A single entry point for multiple services
- Secure public APIs
- Serverless architectures
- Authentication and authorization
- Request throttling
- API monitoring
- API versioning
- Custom domains
- Usage plans and API keys

Avoid using API Gateway if your application only exposes a simple internal HTTP service and does not require API management features. In such cases, a direct Application Load Balancer (ALB) may be sufficient.

---

# API Gateway vs Application Load Balancer

| Feature | API Gateway | Application Load Balancer |
|----------|------------|---------------------------|
| API Management | ✅ | ❌ |
| Authentication | ✅ | Limited |
| Request Validation | ✅ | ❌ |
| API Keys | ✅ | ❌ |
| Usage Plans | ✅ | ❌ |
| WebSocket Support | ✅ | ✅ |
| Rate Limiting | ✅ | ❌ |
| Caching | ✅ | ❌ |
| Lambda Integration | Native | Via Target Groups |
| Pricing Model | Per Request | Per Hour + LCU |

---

# Interview Tips

A common interview question is:

> **Why not expose microservices directly?**

A strong answer is:

- Clients should not know backend service locations.
- Centralized authentication improves security.
- API Gateway provides request validation, throttling, logging, caching, and monitoring.
- Backend services can evolve independently without affecting clients.
- It simplifies client development by providing a single entry point.

---

# Key Takeaways

- Amazon API Gateway is the front door for applications hosted on AWS.
- It provides a single, secure entry point for backend services.
- API Gateway supports REST, HTTP, and WebSocket APIs.
- It integrates with Lambda, ECS, EC2, ALB, SQS, SNS, DynamoDB, Step Functions, and external HTTP services.
- It simplifies authentication, authorization, monitoring, throttling, caching, and request routing.
- API Gateway is a foundational service for serverless and microservices architectures.