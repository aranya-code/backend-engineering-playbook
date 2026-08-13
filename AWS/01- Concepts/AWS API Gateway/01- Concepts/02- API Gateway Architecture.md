# API Gateway Architecture

## Overview

Amazon API Gateway acts as the **front door** for your backend services. Instead of exposing multiple backend services directly to clients, API Gateway provides a **single, secure, and scalable entry point**.

It receives client requests, performs authentication, authorization, validation, throttling, logging, and monitoring, then forwards the request to the appropriate backend service.

This architecture simplifies application development and improves security, scalability, and maintainability.

---

# High-Level Architecture

```text
                   Client Applications
        ┌──────────────┬──────────────┐
        │              │              │
        ▼              ▼              ▼
   Web Browser    Mobile App     Third-Party Client
                      │
                      ▼
              Amazon API Gateway
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
   AWS Lambda      ECS/Fargate      EC2 Instance
      │               │                │
      ├───────────────┼────────────────┤
      ▼               ▼                ▼
 DynamoDB         Amazon RDS      External APIs
```

API Gateway hides the complexity of the backend infrastructure from clients.

---

# Why Use API Gateway?

Without API Gateway, every client must know where each backend service is hosted.

Example:

```text
Web App
   │
   ├────────► User Service
   │
   ├────────► Product Service
   │
   ├────────► Payment Service
   │
   └────────► Notification Service
```

Problems:

- Multiple endpoints
- Duplicate authentication logic
- Difficult API versioning
- No centralized monitoring
- Backend changes affect clients
- Harder to secure APIs

---

With API Gateway:

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
User Service  Product Service  Payment Service
```

The client only knows one endpoint.

---

# API Gateway Request Lifecycle

A request typically passes through the following stages.

```text
Client
   │
   ▼
DNS Resolution
   │
   ▼
API Gateway Endpoint
   │
   ▼
Authentication
   │
   ▼
Authorization
   │
   ▼
Request Validation
   │
   ▼
Throttling
   │
   ▼
Request Transformation (Optional)
   │
   ▼
Backend Integration
   │
   ▼
Backend Response
   │
   ▼
Response Transformation (Optional)
   │
   ▼
Client
```

Each stage can be configured independently.

---

# Core Components

## 1. API

An API is the top-level container that groups resources, methods, integrations, deployments, and stages.

Example:

```text
Shopping API
```

---

## 2. Resources

Resources represent URL paths.

Example:

```text
/users

/products

/orders

/payments
```

Resources can also be nested.

```text
/users/{userId}

/orders/{orderId}
```

---

## 3. Methods

Methods define the HTTP operations supported by a resource.

Common methods include:

- GET
- POST
- PUT
- PATCH
- DELETE
- OPTIONS
- HEAD

Example:

```text
GET /products

POST /products

DELETE /products/{id}
```

---

## 4. Integration

After receiving a request, API Gateway forwards it to a backend integration.

Supported integrations include:

- AWS Lambda
- HTTP APIs
- Application Load Balancer
- Network Load Balancer
- AWS Services
- Mock Integration

---

## 5. Deployment

API configuration changes are not immediately available.

You must create a deployment.

```text
Modify API

↓

Deploy API

↓

Stage

↓

Users
```

---

## 6. Stage

A stage represents a deployed version of the API.

Typical stages include:

```text
dev

test

staging

production
```

Each stage has its own endpoint.

Example:

```text
https://abc.execute-api.us-east-1.amazonaws.com/dev

https://abc.execute-api.us-east-1.amazonaws.com/prod
```

---

# Architecture with AWS Lambda

One of the most common architectures.

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
             AWS Lambda
                   │
                   ▼
             Amazon DynamoDB
```

Advantages:

- Fully serverless
- Auto-scaling
- Pay per request
- No infrastructure management

---

# Architecture with ECS

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
             ECS Service
                   │
                   ▼
             Amazon RDS
```

Suitable for containerized applications.

---

# Architecture with EC2

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
           EC2 Application
                   │
                   ▼
             Amazon RDS
```

Common for legacy applications.

---

# Microservices Architecture

API Gateway acts as the entry point for multiple independent services.

```text
                    Client
                       │
                       ▼
               Amazon API Gateway
      ┌────────────┼────────────┬────────────┐
      ▼            ▼            ▼            ▼
 User Service  Order Service Product Service Payment Service
      │            │            │            │
      ▼            ▼            ▼            ▼
    Database    Database     Database    Database
```

Benefits:

- Loose coupling
- Independent deployments
- Better scalability
- Easier maintenance

---

# Cross-Cutting Responsibilities

API Gateway handles many concerns that would otherwise need to be implemented in every backend service.

These include:

- Authentication
- Authorization
- Rate limiting
- API keys
- Usage plans
- Logging
- Monitoring
- Metrics
- Request validation
- Response transformation
- Caching
- CORS

This allows backend services to focus only on business logic.

---

# Example Request Flow

Suppose a customer requests product information.

```http
GET /products/100
```

Request flow:

```text
Client

↓

API Gateway

↓

JWT Authentication

↓

Request Validation

↓

Lambda Function

↓

DynamoDB

↓

Lambda Response

↓

API Gateway

↓

Client
```

The client never communicates directly with Lambda or DynamoDB.

---

# Benefits of API Gateway Architecture

- Single entry point for all APIs
- Improved security
- Reduced client complexity
- Automatic scaling
- Backend abstraction
- Centralized logging
- Request validation
- Traffic throttling
- Better monitoring
- Easier API versioning
- Support for multiple backend technologies

---

# Common Interview Questions

### Why is API Gateway considered the front door of serverless applications?

Because it receives all incoming client requests, applies security and traffic management policies, and routes requests to backend services such as AWS Lambda, ECS, EC2, or other HTTP endpoints.

---

### Why should clients never call Lambda functions directly?

Because API Gateway provides:

- Authentication
- Authorization
- Request validation
- Throttling
- Logging
- Monitoring
- API versioning
- Custom domains

Without API Gateway, these capabilities would need to be implemented separately.

---

# Key Takeaways

- API Gateway is the central entry point for backend services.
- It abstracts backend infrastructure from clients.
- Resources define URL paths, while methods define supported HTTP operations.
- API changes become available only after deployment to a stage.
- API Gateway integrates with Lambda, ECS, EC2, ALB, AWS services, and external HTTP APIs.
- It centralizes authentication, authorization, validation, monitoring, throttling, and request routing.
- API Gateway is a key building block for scalable microservices and serverless architectures.