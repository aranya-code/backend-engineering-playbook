# API Gateway + Microservices

## Overview

Modern applications are increasingly built using **Microservices Architecture**, where an application is divided into multiple small, independent services.

Instead of exposing every microservice directly to clients, organizations place **Amazon API Gateway** in front of all services.

API Gateway becomes the **single entry point** for every client request, handling concerns such as:

- Authentication
- Authorization
- Request Routing
- Rate Limiting
- Monitoring
- API Versioning
- Request Validation

Each microservice focuses only on business logic.

This architecture is widely used by companies such as Netflix, Amazon, Uber, Spotify, and Airbnb.

---

# Why API Gateway?

Without API Gateway:

```text
              Client

      ┌────────┼────────┐

      ▼        ▼        ▼

 Users API Orders API Payments API
```

Problems:

- Multiple endpoints
- Authentication in every service
- Tight client coupling
- Difficult API versioning
- Increased attack surface

---

With API Gateway:

```text
Client

↓

Amazon API Gateway

↓

Microservices
```

Benefits:

- Single endpoint
- Centralized security
- Simplified clients
- Better monitoring
- Independent services

---

# High-Level Architecture

```text
                  Client

                     │

                     ▼

            Amazon API Gateway

                     │

      ┌──────────────┼──────────────┐

      ▼              ▼              ▼

 User Service   Order Service   Payment Service

      │              │              │

      ▼              ▼              ▼

 DynamoDB       PostgreSQL       Stripe
```

Each service owns its own business logic and data.

---

# Request Flow

```text
Client

↓

API Gateway

↓

Authentication

↓

Request Validation

↓

Route Request

↓

Microservice

↓

Response

↓

API Gateway

↓

Client
```

---

# Single Entry Point

Instead of:

```text
users.company.com

orders.company.com

payments.company.com
```

Clients call:

```text
api.company.com
```

API Gateway routes requests internally.

---

# Service Routing

Example:

```text
/users/*

↓

User Service

-------------------

/orders/*

↓

Order Service

-------------------

/payments/*

↓

Payment Service
```

Routing is handled by API Gateway.

---

# Service Independence

Each service can use different technologies.

```text
User Service

↓

Python

--------------------

Order Service

↓

Java

--------------------

Payment Service

↓

Go

--------------------

Notification Service

↓

Node.js
```

API Gateway provides a unified interface regardless of implementation.

---

# Independent Deployment

Services can be deployed separately.

```text
User Service

↓

Version 2

------------------

Order Service

↓

Version 1
```

Other services remain unaffected.

---

# Database per Service

Each microservice owns its own database.

```text
User Service

↓

User Database

--------------------

Order Service

↓

Order Database

--------------------

Inventory Service

↓

Inventory Database
```

Avoid sharing databases across services.

---

# Authentication

Authentication happens once.

```text
Client

↓

JWT

↓

API Gateway

↓

Microservices
```

Individual services don't need to validate tokens repeatedly unless additional authorization is required.

---

# Authorization

API Gateway verifies access.

Example:

```text
Admin

↓

Delete User

↓

Allowed

------------------

Customer

↓

Delete User

↓

Denied
```

Unauthorized requests never reach services.

---

# Request Validation

Example:

```json
{
}
```

Expected:

```json
{
    "email":"john@example.com"
}
```

API Gateway rejects invalid requests before forwarding them.

---

# Service Discovery

Clients never discover services directly.

```text
Client

↓

API Gateway

↓

Routing

↓

Correct Service
```

Backend changes remain transparent to clients.

---

# Load Balancing

Each microservice can scale independently.

```text
API Gateway

↓

Order Service

↓

Load Balancer

↓

Container 1

Container 2

Container 3
```

Only busy services scale.

---

# Failure Isolation

Suppose:

```text
Payment Service

↓

Unavailable
```

Other services continue operating.

```text
Users

✓

Orders

✓

Inventory

✓
```

Failures remain isolated.

---

# API Versioning

Different services may expose different versions.

```text
/v1/users

↓

User Service

----------------------

/v2/orders

↓

Order Service
```

Versioning can evolve independently.

---

# Communication Between Services

API Gateway is **not** used for internal service-to-service communication.

Typical architecture:

```text
Client

↓

API Gateway

↓

User Service

↓

Order Service

↓

Inventory Service
```

Internal communication commonly uses:

- REST
- gRPC
- Amazon SQS
- Amazon SNS
- Amazon EventBridge
- Apache Kafka

---

# Observability

Monitor:

API Gateway:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors

Each service:

- CPU
- Memory
- Response Time
- Application Metrics

Use AWS X-Ray for distributed tracing.

---

# Logging

Logs originate from:

```text
API Gateway

↓

CloudWatch Logs

--------------------

Service Logs

↓

CloudWatch Logs
```

Request IDs enable end-to-end troubleshooting.

---

# Scaling

Example:

```text
Traffic

↓

API Gateway

↓

Orders

↓

Auto Scaling

↓

More Containers
```

Other services remain unchanged.

---

# Advantages

- Independent deployment
- Independent scaling
- Technology flexibility
- Fault isolation
- Better maintainability
- Faster development
- Clear ownership
- Easier CI/CD

---

# Challenges

- Distributed debugging
- Network latency
- Data consistency
- Service discovery
- Monitoring complexity
- Distributed transactions
- Increased operational complexity

Microservices require mature operational practices.

---

# Production Architecture

```text
                    Client

                       │

                       ▼

                 Amazon Route 53

                       │

                       ▼

                  CloudFront

                       │

                       ▼

                    AWS WAF

                       │

                       ▼

               Amazon API Gateway

                       │

      ┌────────────────┼────────────────┐

      ▼                ▼                ▼

 User Service    Order Service    Payment Service

      │                │                │

      ▼                ▼                ▼

 DynamoDB         Aurora         External Payment API

                       │

                       ▼

             CloudWatch & X-Ray
```

This represents a common production microservices architecture.

---

# API Gateway vs Service Mesh

| API Gateway | Service Mesh |
|--------------|--------------|
| Client-to-Service | Service-to-Service |
| Public APIs | Internal Communication |
| Authentication | mTLS |
| Rate Limiting | Traffic Management |
| Request Validation | Retry & Circuit Breaking |
| API Management | Service Networking |

They solve different problems and are often used together.

---

# Best Practices

- Use API Gateway as the single public entry point.
- Keep microservices independently deployable.
- Follow the database-per-service pattern.
- Avoid direct client access to backend services.
- Keep services stateless whenever possible.
- Use asynchronous messaging where appropriate.
- Enable CloudWatch Metrics, Logs, and AWS X-Ray.
- Implement retries, timeouts, and circuit breakers for service-to-service communication.
- Version APIs without breaking existing clients.

---

# Common Interview Questions

### Why place API Gateway in front of microservices?

API Gateway centralizes authentication, authorization, routing, request validation, throttling, monitoring, and API management while exposing a single endpoint to clients.

---

### Should microservices communicate through API Gateway?

No.

API Gateway is designed for client-to-service communication. Internal services should communicate directly using REST, gRPC, messaging systems, or event-driven architectures.

---

### Why should each microservice have its own database?

A database-per-service architecture reduces coupling, allows independent deployment, and enables each service to evolve without affecting others.

---

### What are the biggest challenges in a microservices architecture?

Common challenges include distributed debugging, network latency, data consistency, monitoring, service discovery, and operational complexity.

---

### Can different microservices use different programming languages?

Yes.

Microservices are technology-agnostic. API Gateway provides a unified API regardless of whether services are written in Python, Java, Go, .NET, or Node.js.

---

# Key Takeaways

- API Gateway serves as the single entry point for client requests in a microservices architecture.
- It centralizes cross-cutting concerns such as authentication, authorization, request validation, routing, throttling, and monitoring.
- Microservices remain independently deployable, scalable, and technology-agnostic while owning their own data stores.
- Service-to-service communication should bypass API Gateway and use protocols such as REST, gRPC, or asynchronous messaging.
- Combining API Gateway with independently scalable microservices, robust observability, and resilient communication patterns results in a maintainable and production-ready architecture.