# Mock Integrations

## Overview

A **Mock Integration** is an integration type in Amazon API Gateway where **no backend service is invoked**.

Instead of forwarding requests to AWS Lambda, an HTTP endpoint, or another AWS service, API Gateway generates and returns the response itself.

Mock Integrations are useful for:

- API prototyping
- Frontend development
- Testing
- Health check endpoints
- Returning static responses
- Simulating backend behavior

Since no backend is involved, Mock Integrations are extremely fast and inexpensive.

---

# Architecture

```text
              Client
                 │
                 ▼
        Amazon API Gateway
                 │
                 ▼
          Mock Integration
                 │
                 ▼
        Static Response
                 │
                 ▼
              Client
```

Notice that there is:

- No Lambda
- No EC2
- No ECS
- No Database

API Gateway itself generates the response.

---

# Request Flow

```text
Client

↓

API Gateway

↓

Mock Integration

↓

Response Generated

↓

Client
```

The request never reaches any backend service.

---

# How It Works

Suppose a client sends:

```http
GET /status
```

API Gateway immediately returns:

```json
{
    "status": "Healthy"
}
```

No backend processing occurs.

---

# Simple Example

Request:

```http
GET /health
```

Response:

```json
{
    "status":"UP"
}
```

Execution flow:

```text
Client

↓

API Gateway

↓

Mock Response

↓

Client
```

---

# Why Use Mock Integrations?

During development, backend services may not yet exist.

For example:

```text
Frontend Team

Ready

↓

Backend Team

Still Developing
```

Instead of waiting for the backend, API Gateway can return predefined responses.

Frontend developers can continue building the application.

---

# Example: Login API

Suppose the frontend requires:

```http
POST /login
```

Expected response:

```json
{
    "token":"abc123",
    "username":"John"
}
```

Even if authentication has not been implemented, API Gateway can return this static response.

---

# Example: Feature Flags

Request:

```http
GET /feature-flags
```

Response:

```json
{
    "newCheckout": true,
    "darkMode": false
}
```

No backend is required.

---

# Example: Maintenance Page

Request:

```http
GET /maintenance
```

Response:

```json
{
    "status":"Scheduled Maintenance",
    "start":"10:00 PM",
    "duration":"30 minutes"
}
```

---

# Example: API Documentation

Request:

```http
GET /
```

Response:

```json
{
    "version":"1.0",
    "service":"Customer API"
}
```

Useful for returning static metadata.

---

# Configuring a Mock Integration

The configuration typically consists of:

```text
Method

↓

Mock Integration

↓

Integration Response

↓

Method Response
```

Since no backend exists, API Gateway uses Mapping Templates to generate the response.

---

# Request Mapping

Even though there is no backend, API Gateway still executes a request mapping template.

Example:

```vtl
{
    "statusCode": 200
}
```

This tells API Gateway which integration response should be used.

---

# Integration Response

The Integration Response defines what API Gateway should return.

Example:

```json
{
    "message":"API is running"
}
```

---

# Method Response

The Method Response defines:

- HTTP Status Code
- Headers
- Response Models

Example:

```http
HTTP/1.1 200 OK
```

```json
{
    "message":"Success"
}
```

---

# Returning Different Status Codes

Mock Integrations can return different HTTP status codes.

Example:

```http
200 OK
```

```json
{
    "status":"Healthy"
}
```

---

```http
404 Not Found
```

```json
{
    "message":"Resource not found"
}
```

---

```http
503 Service Unavailable
```

```json
{
    "message":"Maintenance in progress"
}
```

No backend service is required.

---

# Mock Integration Architecture

```text
                  Client
                     │
                     ▼
             Amazon API Gateway
                     │
             Mock Integration
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    200 OK       404 Error     503 Error
```

API Gateway chooses the configured response.

---

# Advantages

## No Backend Required

Perfect for early development.

---

## Very Fast

No network calls.

No Lambda invocation.

No database queries.

---

## Low Cost

Since no compute resources are used, Mock Integrations are extremely inexpensive.

---

## Frontend Development

Frontend teams can develop independently.

---

## API Testing

Allows API consumers to test endpoints before backend implementation.

---

# Disadvantages

## Static Responses

Responses are predefined.

No business logic is executed.

---

## No Dynamic Data

Cannot query databases.

Cannot call AWS services.

Cannot process user input.

---

## Limited Use Cases

Not suitable for production business workflows.

---

# Common Use Cases

Mock Integrations are commonly used for:

- Health endpoints
- API prototypes
- Frontend development
- Integration testing
- Demo APIs
- Maintenance endpoints
- API documentation
- Static configuration endpoints

---

# Mock Integration vs Lambda

| Feature | Mock Integration | Lambda |
|----------|------------------|---------|
| Backend | None | Lambda |
| Dynamic Logic | ❌ | ✅ |
| Database Access | ❌ | ✅ |
| Performance | Excellent | Very Good |
| Cost | Lowest | Higher |
| Use Case | Static Responses | Business Logic |

---

# Mock Integration vs AWS Service Integration

| Feature | Mock | AWS Service |
|----------|------|-------------|
| Backend | None | AWS Service |
| Business Logic | ❌ | Limited |
| Dynamic Data | ❌ | Yes |
| Cost | Lowest | Low |
| Typical Use | Testing | Production Workflows |

---

# Real-World Example

A mobile development team is building an application while the backend team is still implementing APIs.

Instead of delaying development:

```text
Mobile App

↓

API Gateway

↓

Mock Integration

↓

Sample JSON
```

The mobile application can be fully developed and tested using realistic API responses.

Once the backend is ready, the Mock Integration is replaced with a Lambda or HTTP integration without changing the API contract.

---

# Common Interview Questions

### What is a Mock Integration?

A Mock Integration is an API Gateway integration where API Gateway generates the response itself without invoking any backend service.

---

### When should you use Mock Integrations?

Use Mock Integrations for:

- API prototyping
- Frontend development
- Testing
- Static responses
- Health check endpoints

---

### Can Mock Integrations access a database?

No.

Mock Integrations do not invoke any backend service and therefore cannot access databases or execute business logic.

---

### Why are Mock Integrations useful during development?

They allow frontend and API consumers to continue development before backend services are implemented, reducing dependencies between teams.

---

# Best Practices

- Use Mock Integrations only for static or temporary endpoints.
- Replace Mock Integrations with real backend integrations before production if dynamic behavior is required.
- Keep response payloads consistent with the final API contract to avoid frontend changes later.
- Use Mock Integrations for health checks, API documentation, and demonstrations where appropriate.
- Avoid implementing business logic using Mock Integrations.

---

# Key Takeaways

- Mock Integration allows API Gateway to return responses without calling any backend service.
- It is ideal for API prototyping, frontend development, testing, and static endpoints.
- Mock Integrations provide excellent performance and the lowest operational cost.
- Responses are predefined and cannot include dynamic business logic.
- Mock Integrations help decouple frontend and backend development while maintaining a stable API contract.