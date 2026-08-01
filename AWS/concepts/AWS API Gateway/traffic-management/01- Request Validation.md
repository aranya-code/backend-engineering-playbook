# Request Validation

## Overview

One of the first responsibilities of Amazon API Gateway is ensuring that incoming requests are **valid** before they reach backend services.

Without request validation:

- Invalid JSON payloads
- Missing required parameters
- Incorrect data types
- Malformed requests

can all reach your backend, increasing application complexity and unnecessary compute costs.

API Gateway provides **Request Validation**, allowing invalid requests to be rejected immediately without invoking Lambda, ECS, EC2, or any other backend.

Request Validation improves:

- API reliability
- Security
- Performance
- Backend efficiency
- Client experience

---

# Why Request Validation?

Consider a customer creation API.

```http
POST /customers
```

Expected payload:

```json
{
    "name": "John",
    "email": "john@example.com"
}
```

Instead, the client sends:

```json
{
    "username": 123,
    "age": "twenty"
}
```

Without validation:

```text
Client

↓

API Gateway

↓

Lambda

↓

Validation Logic

↓

400 Bad Request
```

The backend is invoked unnecessarily.

With Request Validation:

```text
Client

↓

API Gateway

↓

Validation

↓

400 Bad Request
```

The backend is never executed.

---

# Architecture

```text
             Client

                │

                ▼

        Amazon API Gateway

                │

       Request Validation

                │

      ┌─────────┴─────────┐

      ▼                   ▼

 Valid Request      Invalid Request

      │                   │

      ▼                   ▼

 Backend          HTTP 400 Response
```

Validation occurs before integration with the backend.

---

# What Can Be Validated?

API Gateway can validate:

- Request body
- Query string parameters
- Path parameters
- Headers

These checks ensure requests conform to the expected API contract.

---

# Request Body Validation

Suppose the API expects:

```json
{
    "productName": "Laptop",
    "price": 50000
}
```

If the client sends:

```json
{
    "productName": 123,
    "price": "high"
}
```

API Gateway rejects the request before it reaches the backend.

---

# Parameter Validation

API Gateway can ensure required parameters are present.

Example:

```http
GET /orders?customerId=123
```

If `customerId` is missing:

```http
GET /orders
```

Response:

```http
400 Bad Request
```

---

# Header Validation

Example:

```http
X-Request-ID: abc123
```

If the API requires this header and it is missing:

```http
400 Bad Request
```

---

# Path Parameter Validation

Resource:

```text
/orders/{orderId}
```

API Gateway verifies required path parameters exist before forwarding the request.

---

# JSON Schema Models

Request validation uses **Models** based on JSON Schema.

Example:

```json
{
  "type": "object",
  "required": [
    "name",
    "email"
  ]
}
```

The incoming request must match the schema.

---

# Validation Flow

```text
Client

↓

API Gateway

↓

JSON Schema Validation

↓

Valid?

│

├── Yes

│      │

│      ▼

│  Backend

│

└── No

       │

       ▼

400 Bad Request
```

---

# Validation Types

API Gateway supports different validation options.

| Validation | Description |
|------------|-------------|
| Body Only | Validate JSON body |
| Parameters Only | Validate headers, path, and query parameters |
| Body + Parameters | Validate everything |

Choose the validator based on the API's requirements.

---

# Example

Schema:

```json
{
  "required": [
    "username"
  ]
}
```

Incoming request:

```json
{}
```

Response:

```http
400 Bad Request
```

---

# Advantages

## Reduced Backend Load

Invalid requests never reach backend services.

---

## Lower Cost

Lambda invocations and compute resources are not consumed by malformed requests.

---

## Consistent API Contract

Clients receive immediate feedback when requests do not conform to the API specification.

---

## Improved Security

Rejecting malformed input early reduces the attack surface.

---

# Limitations

Request Validation checks only:

- Structure
- Required fields
- Data types

It does **not** validate:

- Business rules
- Database constraints
- User permissions

Backend applications must still perform application-level validation.

---

# Real-World Example

An online banking API expects:

```json
{
  "accountNumber": "1234567890",
  "amount": 1000
}
```

A request missing the `amount` field is rejected immediately by API Gateway, preventing unnecessary Lambda execution and database access.

---

# Best Practices

- Enable Request Validation for all public APIs.
- Define JSON Schema models for every request body.
- Validate required query and path parameters.
- Continue validating business rules in backend services.
- Return meaningful error responses to help API consumers fix requests.

---

# Common Interview Questions

### What is Request Validation in API Gateway?

Request Validation checks incoming requests against configured models and required parameters before invoking backend services.

---

### Does Request Validation replace backend validation?

No.

API Gateway validates request structure, while backend services must still validate business logic, permissions, and database constraints.

---

### What response is returned when validation fails?

```http
400 Bad Request
```

The backend service is never invoked.

---

# Key Takeaways

- Request Validation ensures incoming requests conform to the expected API contract before reaching backend services.
- API Gateway can validate request bodies, query parameters, path parameters, and headers.
- JSON Schema models define the expected request structure.
- Early validation reduces backend load, lowers costs, and improves API reliability.
- Backend applications should always perform additional business-level validation even when API Gateway Request Validation is enabled.