# Request & Response Lifecycle

## Overview

Every request sent to Amazon API Gateway follows a well-defined lifecycle before reaching the backend service and returning a response to the client.

Understanding this lifecycle is essential for designing secure, scalable, and maintainable APIs. It also helps identify where features such as authentication, request validation, throttling, logging, and response transformation occur.

A typical request passes through several stages before reaching the backend and then follows a similar path on the way back.

---

# High-Level Request Lifecycle

```text
                 Client
                    │
                    ▼
            Amazon API Gateway
                    │
          Authentication
                    │
          Authorization
                    │
         Request Validation
                    │
            Request Mapping
                    │
             Backend Service
                    │
           Business Logic
                    │
          Response Mapping
                    │
            API Gateway
                    │
                    ▼
                 Client
```

Every incoming request moves through this pipeline.

---

# Step 1 – Client Sends Request

A client sends an HTTP request to an API Gateway endpoint.

Example:

```http
GET /products/101 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhb...
```

The request contains:

- HTTP Method
- URL
- Headers
- Query Parameters
- Path Parameters
- Request Body (if applicable)

---

# Step 2 – Route Matching

API Gateway determines which API resource and method should handle the request.

Example:

```http
GET /products/101
```

Matches:

```text
GET /products/{productId}
```

If no matching route exists:

```http
404 Not Found
```

is returned.

---

# Step 3 – Authentication

If authentication is configured, API Gateway verifies the client's identity.

Supported authentication methods include:

- IAM Authentication
- Amazon Cognito
- JWT Authorizer
- Lambda Authorizer

Example:

```text
Authorization:
Bearer eyJhbGci...
```

If authentication fails:

```http
401 Unauthorized
```

---

# Step 4 – Authorization

Authentication answers:

> Who are you?

Authorization answers:

> Are you allowed to perform this action?

Example:

```text
User

↓

Authenticated

↓

Allowed to access

GET /orders

↓

Allowed

------------------------

User

↓

Authenticated

↓

DELETE /orders

↓

Denied
```

If authorization fails:

```http
403 Forbidden
```

---

# Step 5 – Request Validation

API Gateway can validate:

- Request body
- Headers
- Query parameters
- Path parameters

Example JSON Schema:

```json
{
    "name": "Laptop",
    "price": 50000
}
```

If the request doesn't match the expected schema:

```http
400 Bad Request
```

is returned before the backend is invoked.

---

# Step 6 – Throttling

Before forwarding the request, API Gateway checks whether the client has exceeded configured rate limits.

Example:

```
Rate Limit

100 requests/sec

Burst

200 requests
```

If exceeded:

```http
429 Too Many Requests
```

This protects backend services from traffic spikes.

---

# Step 7 – Request Transformation (Optional)

For REST APIs, API Gateway can transform incoming requests using **Mapping Templates (VTL)**.

Example:

Incoming request:

```json
{
    "username": "john"
}
```

Transformed request:

```json
{
    "user_name": "john",
    "createdBy": "API Gateway"
}
```

This allows backend services to receive data in the required format.

> **Note:** Request transformation using VTL is primarily available for **REST APIs**. HTTP APIs provide more limited transformation capabilities.

---

# Step 8 – Backend Integration

API Gateway forwards the request to the configured backend.

Possible integrations include:

- AWS Lambda
- ECS
- EC2
- Application Load Balancer
- External HTTP API
- AWS Services
- Mock Integration

Example:

```text
API Gateway

↓

Lambda Function

↓

Business Logic

↓

Database
```

---

# Step 9 – Backend Processing

The backend performs application-specific work.

Example:

```text
Receive Request

↓

Validate Business Rules

↓

Read Database

↓

Generate Response

↓

Return Response
```

This is where your application code executes.

---

# Step 10 – Response Transformation (Optional)

REST APIs can modify backend responses before returning them to clients.

Backend response:

```json
{
    "id": 10,
    "internalStatus": "ACTIVE",
    "createdBy": "admin"
}
```

API Gateway transforms it into:

```json
{
    "id": 10,
    "status": "ACTIVE"
}
```

Sensitive fields can be removed before sending data to clients.

---

# Step 11 – Return Response

Finally, API Gateway returns the response to the client.

Example:

```http
HTTP/1.1 200 OK

Content-Type: application/json
```

```json
{
    "id": 10,
    "name": "Laptop"
}
```

---

# Complete Request Flow

```text
Client
   │
   ▼
DNS Resolution
   │
   ▼
API Gateway
   │
   ▼
Route Matching
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
Request Mapping
   │
   ▼
Backend Integration
   │
   ▼
Business Logic
   │
   ▼
Response Mapping
   │
   ▼
API Gateway
   │
   ▼
Client
```

---

# Error Responses During the Lifecycle

| Stage | Common Error |
|---------|--------------|
| Route Matching | 404 Not Found |
| Authentication | 401 Unauthorized |
| Authorization | 403 Forbidden |
| Request Validation | 400 Bad Request |
| Throttling | 429 Too Many Requests |
| Backend Failure | 500 Internal Server Error |
| Backend Timeout | 504 Gateway Timeout |

Understanding where these errors originate is important when troubleshooting API Gateway applications.

---

# Lifecycle with Lambda Proxy Integration

With Lambda Proxy Integration, API Gateway performs minimal request transformation.

```text
Client
    │
    ▼
API Gateway
    │
    ▼
Entire HTTP Request
    │
    ▼
Lambda
    │
    ▼
Entire HTTP Response
    │
    ▼
Client
```

The Lambda function is responsible for processing the complete request and generating the response.

---

# Lifecycle with HTTP Proxy Integration

```text
Client
    │
    ▼
API Gateway
    │
    ▼
HTTP Backend
    │
    ▼
Response
    │
    ▼
Client
```

API Gateway simply forwards the request and returns the backend response with minimal processing.

---

# Why This Lifecycle Matters

Each stage provides important capabilities:

- Authentication secures the API.
- Authorization controls access.
- Validation prevents invalid requests.
- Throttling protects backend services.
- Transformations decouple clients from backend implementations.
- Logging and monitoring improve observability.

Because these concerns are handled centrally, backend services can focus primarily on business logic.

---

# Common Interview Questions

### What happens when a client sends a request to API Gateway?

The request is matched to a route, authenticated, authorized, validated, checked against throttling limits, optionally transformed, forwarded to the backend, and then the response follows the reverse path back to the client.

---

### At which stage is request validation performed?

After route matching and before the backend integration. Invalid requests are rejected by API Gateway without invoking the backend.

---

### Does API Gateway always transform requests?

No. Request and response transformations are optional. They are commonly used in REST APIs and are limited in HTTP APIs. Lambda Proxy Integration typically forwards the request without transformation.

---

### Why is request validation useful?

It prevents malformed requests from reaching backend services, reducing unnecessary processing and improving API reliability.

---

# Best Practices

- Authenticate requests as early as possible.
- Validate requests before invoking backend services.
- Apply throttling to protect downstream systems.
- Use response transformations to hide internal implementation details when needed.
- Log requests and responses for monitoring and troubleshooting.
- Prefer Lambda Proxy Integration unless request or response transformation is required.

---

# Key Takeaways

- Every API Gateway request follows a structured lifecycle from the client to the backend and back.
- API Gateway performs route matching, authentication, authorization, request validation, throttling, optional transformations, backend integration, and response handling.
- Invalid or unauthorized requests are rejected before reaching backend services.
- Understanding the request lifecycle is essential for designing secure, reliable, and scalable APIs.
- Knowing where each feature is applied helps simplify debugging and architecture decisions.