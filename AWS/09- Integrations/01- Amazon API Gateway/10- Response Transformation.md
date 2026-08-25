# Response Transformation

## Overview

Response Transformation is a feature of Amazon API Gateway that allows responses returned by backend services to be modified before they are sent back to clients.

Instead of exposing backend responses directly, API Gateway can:

- Rename fields
- Remove sensitive information
- Add new fields
- Convert response formats
- Standardize error responses
- Support API versioning
- Hide backend implementation details

Like Request Transformation, Response Transformation uses **Mapping Templates** written in **Velocity Template Language (VTL)**.

This creates a clean separation between backend services and API consumers.

---

# Why Response Transformation?

Suppose a backend returns:

```json
{
    "employeeId": 101,
    "department": "IT",
    "salary": 120000,
    "internalRemarks": "Promotion Eligible"
}
```

Clients should receive only:

```json
{
    "id": 101,
    "department": "IT"
}
```

Instead of modifying backend code:

```text
Backend

↓

API Gateway

↓

Response Transformation

↓

Client
```

---

# Architecture

```text
             Backend Service

                    │

                    ▼

           Amazon API Gateway

                    │

        Response Transformation

                    │

                    ▼

                 Client
```

API Gateway transforms the response before returning it to the client.

---

# Response Flow

```text
Backend

↓

Original Response

↓

Mapping Template

↓

Transformed Response

↓

Client
```

The client never sees the original backend response.

---

# Mapping Templates

Response Transformation uses **Velocity Template Language (VTL).**

Example:

Backend:

```json
{
    "employeeId":101
}
```

Template:

```vtl
{
    "id":
        "$input.path('$.employeeId')"
}
```

Client receives:

```json
{
    "id":101
}
```

---

# Renaming Fields

Backend:

```json
{
    "customerId":501,
    "customerName":"John"
}
```

Template:

```vtl
{
    "id":
        "$input.path('$.customerId')",

    "name":
        "$input.path('$.customerName')"
}
```

Response:

```json
{
    "id":501,
    "name":"John"
}
```

---

# Removing Sensitive Fields

Backend:

```json
{
    "username":"john",
    "passwordHash":"ABC123",
    "salary":90000
}
```

Template:

```vtl
{
    "username":
        "$input.path('$.username')"
}
```

Sensitive information is never exposed.

---

# Adding New Fields

Backend:

```json
{
    "status":"SUCCESS"
}
```

Template:

```vtl
{
    "status":
        "$input.path('$.status')",

    "apiVersion":"v1"
}
```

Client receives:

```json
{
    "status":"SUCCESS",
    "apiVersion":"v1"
}
```

---

# Response Header Transformation

API Gateway can add or modify HTTP response headers.

Example:

Backend:

```http
200 OK
```

API Gateway adds:

```http
X-API-Version: v1

Cache-Control: no-cache
```

Useful for:

- Versioning
- Security headers
- Caching policies
- Correlation IDs

---

# Error Response Transformation

Backend:

```http
500 Internal Server Error
```

```json
{
    "error":"Database connection failed"
}
```

API Gateway transforms it into:

```http
503 Service Unavailable
```

```json
{
    "message":"Service temporarily unavailable"
}
```

Internal implementation details remain hidden.

---

# Standardizing Responses

Different microservices may return different formats.

Orders Service:

```json
{
    "status":"ok"
}
```

Inventory Service:

```json
{
    "success":true
}
```

API Gateway transforms both into:

```json
{
    "status":"SUCCESS"
}
```

Clients receive a consistent API.

---

# XML to JSON Transformation

Backend:

```xml
<Product>
    <Name>Laptop</Name>
</Product>
```

Client expects:

```json
{
    "name":"Laptop"
}
```

API Gateway converts the response format.

---

# Response Versioning

Version 2 backend:

```json
{
    "firstName":"John",
    "lastName":"Doe"
}
```

Version 1 clients expect:

```json
{
    "name":"John Doe"
}
```

Response Transformation maintains backward compatibility.

---

# Integration Responses

Response Transformation is configured as part of an **Integration Response**.

Flow:

```text
Backend

↓

Integration Response

↓

Mapping Template

↓

Method Response

↓

Client
```

Different mapping templates can be configured for different HTTP status codes.

---

# Status Code Mapping

Backend:

```http
200 OK
```

Client:

```http
201 Created
```

Or:

Backend:

```http
500 Internal Server Error
```

Client:

```http
503 Service Unavailable
```

API Gateway can map backend status codes to different client responses.

---

# Common Use Cases

Response Transformation is commonly used for:

- Hiding sensitive fields
- Standardizing APIs
- Legacy backend integration
- XML to JSON conversion
- API version compatibility
- Error response customization
- Header modification

---

# Response Transformation vs Request Transformation

| Request Transformation | Response Transformation |
|------------------------|--------------------------|
| Client → Backend | Backend → Client |
| Modifies incoming requests | Modifies outgoing responses |
| Uses Request Mapping Templates | Uses Response Mapping Templates |
| Protects backend from client differences | Protects clients from backend changes |

---

# Advantages

## Backend Abstraction

Backend implementation details remain hidden.

---

## Consistent APIs

Multiple backend services can expose a unified response format.

---

## Improved Security

Sensitive fields are removed before responses reach clients.

---

## Easier API Evolution

Backend changes do not necessarily impact clients.

---

## Better Client Experience

Clients receive predictable response structures.

---

# Limitations

Response Transformation:

- Adds processing overhead.
- Requires VTL knowledge.
- Can become difficult to maintain if templates are overly complex.
- Should not contain business logic.

---

# Real-World Example

A banking platform consists of several microservices.

```text
Account Service

↓

Customer Service

↓

Loan Service

↓

API Gateway

↓

Response Transformation

↓

Mobile App
```

Although each service returns different JSON structures, the mobile application receives a consistent API response format.

---

# Best Practices

- Keep Mapping Templates simple and maintainable.
- Remove internal identifiers and sensitive information.
- Standardize error responses across all APIs.
- Add security headers where appropriate.
- Use Response Transformation for presentation logic only.
- Avoid implementing business rules inside mapping templates.

---

# Common Interview Questions

### What is Response Transformation?

Response Transformation modifies backend responses before they are returned to clients using Mapping Templates written in Velocity Template Language (VTL).

---

### Why use Response Transformation?

It hides backend implementation details, removes sensitive fields, standardizes API responses, supports API versioning, and improves client compatibility.

---

### Can Response Transformation modify HTTP status codes?

Yes.

API Gateway can map backend status codes to different client-facing status codes using Integration Responses.

---

### What language is used for Response Transformation?

Velocity Template Language (VTL).

---

### Should business logic be implemented in Response Mapping Templates?

No.

Response Mapping Templates should only transform response data. Business logic belongs in backend services.

---

# Key Takeaways

- Response Transformation modifies backend responses before they reach clients.
- API Gateway uses VTL Mapping Templates to rename fields, remove sensitive data, standardize responses, and convert formats.
- Integration Responses allow different transformations for different HTTP status codes.
- Response Transformation helps decouple clients from backend implementations and simplifies API evolution.
- Keep response transformations focused on presentation and compatibility, leaving business logic in backend services.