# HTTP Custom Integration

## Overview

**HTTP Custom Integration** allows Amazon API Gateway to communicate with an HTTP backend while **transforming requests and responses** using **Mapping Templates (Velocity Template Language - VTL).**

Unlike **HTTP Proxy Integration**, where requests are forwarded unchanged, HTTP Custom Integration gives API Gateway complete control over the data sent to and received from the backend.

This integration is useful when:

- Existing backends expect a different payload format.
- Clients and backends use different data models.
- Legacy systems require XML instead of JSON.
- Sensitive information should be removed before returning responses.
- APIs need to maintain backward compatibility.

For most modern APIs, **HTTP Proxy Integration** is preferred because it is simpler. HTTP Custom Integration is mainly used when request or response transformation is necessary.

---

# Architecture

```text
                  Client
                     │
                     ▼
            Amazon API Gateway
                     │
          Request Mapping (VTL)
                     │
                     ▼
              HTTP Backend
                     │
          Business Processing
                     │
                     ▼
         Response Mapping (VTL)
                     │
                     ▼
                  Client
```

API Gateway acts as a transformation layer between clients and backend services.

---

# Request Flow

```text
Client

↓

HTTP Request

↓

API Gateway

↓

Mapping Template

↓

Custom HTTP Request

↓

Backend

↓

HTTP Response

↓

Mapping Template

↓

Client
```

Both requests and responses can be modified.

---

# Why Use HTTP Custom Integration?

Imagine you have a legacy backend.

Client sends:

```json
{
    "firstName": "John",
    "lastName": "Doe"
}
```

But the backend expects:

```json
{
    "full_name": "John Doe"
}
```

Instead of modifying the backend application, API Gateway performs the transformation.

---

# Request Transformation

Incoming request:

```http
POST /users
```

```json
{
    "firstName":"John",
    "lastName":"Doe"
}
```

Mapping Template:

```vtl
{
    "full_name":
        "$input.path('$.firstName') $input.path('$.lastName')"
}
```

Backend receives:

```json
{
    "full_name":"John Doe"
}
```

The client and backend remain completely independent.

---

# Response Transformation

Backend returns:

```json
{
    "customerId":101,
    "internalStatus":"ACTIVE",
    "createdBy":"SYSTEM"
}
```

Mapping Template:

```vtl
{
    "id":"$input.path('$.customerId')",
    "status":"$input.path('$.internalStatus')"
}
```

Client receives:

```json
{
    "id":101,
    "status":"ACTIVE"
}
```

Internal implementation details remain hidden.

---

# Transforming Query Parameters

Client request:

```http
GET /products?page=3
```

Mapping Template:

```vtl
{
    "pageNumber":
        "$input.params('page')"
}
```

Backend receives:

```json
{
    "pageNumber":"3"
}
```

---

# Transforming Headers

Client sends:

```http
Authorization: Bearer abc123
```

Mapping Template:

```vtl
{
    "token":
        "$input.params('Authorization')"
}
```

Backend receives:

```json
{
    "token":"Bearer abc123"
}
```

---

# Transforming Path Parameters

Client request:

```http
GET /users/200
```

Mapping Template:

```vtl
{
    "customerId":
        "$input.params('userId')"
}
```

Backend receives:

```json
{
    "customerId":"200"
}
```

---

# XML Transformation Example

Suppose a client sends JSON.

```json
{
    "name":"Laptop",
    "price":50000
}
```

The backend expects XML.

```xml
<Product>
    <Name>Laptop</Name>
    <Price>50000</Price>
</Product>
```

API Gateway can convert JSON into XML before forwarding the request.

This is a common scenario when integrating with older enterprise systems.

---

# Error Response Mapping

Backend returns:

```http
500 Internal Server Error
```

```json
{
    "error":"Database Failure"
}
```

API Gateway can transform this into:

```http
503 Service Unavailable
```

```json
{
    "message":"Service temporarily unavailable"
}
```

This prevents exposing internal implementation details.

---

# Common Use Cases

HTTP Custom Integration is useful for:

- Legacy REST APIs
- SOAP/XML systems
- Enterprise middleware
- Mainframe applications
- Third-party APIs
- Payload normalization
- API version compatibility

---

# Advantages

## Request Transformation

Convert incoming requests into backend-specific formats.

---

## Response Transformation

Hide unnecessary or sensitive backend fields.

---

## Backend Independence

Backend services remain unchanged even when client requirements evolve.

---

## API Versioning

Support multiple client versions without modifying backend services.

---

## Legacy Integration

Allows modern clients to communicate with older systems.

---

# Disadvantages

## More Configuration

Every endpoint requires Mapping Templates.

---

## Learning VTL

Velocity Template Language introduces additional complexity.

---

## Harder Debugging

Errors may originate from mapping templates rather than backend code.

---

## Increased Maintenance

Template changes are required whenever request or response formats change.

---

# HTTP Proxy vs HTTP Custom

| Feature | HTTP Proxy | HTTP Custom |
|----------|------------|-------------|
| Request Transformation | ❌ | ✅ |
| Response Transformation | ❌ | ✅ |
| Mapping Templates | ❌ | ✅ |
| Simplicity | High | Medium |
| Performance | Higher | Slightly Lower |
| Legacy Support | Limited | Excellent |

---

# HTTP Custom vs Lambda Non-Proxy

| Feature | HTTP Custom | Lambda Non-Proxy |
|----------|-------------|------------------|
| Backend | HTTP Service | Lambda |
| Request Mapping | ✅ | ✅ |
| Response Mapping | ✅ | ✅ |
| Uses VTL | ✅ | ✅ |
| Typical Use | Existing REST APIs | Lambda Functions |

The concepts are similar—the primary difference is the backend target.

---

# Real-World Example

A bank has a legacy Java application that expects XML requests.

Modern mobile applications send JSON.

Architecture:

```text
Mobile App

↓

API Gateway

↓

Request Mapping

↓

Legacy Java Service

↓

Response Mapping

↓

Mobile App
```

The mobile application never needs to know the backend uses XML.

---

# When Should You Use HTTP Custom Integration?

Choose HTTP Custom Integration when:

- Request transformation is required.
- Response transformation is required.
- Legacy applications expect different payloads.
- Sensitive response fields should be removed.
- Multiple client versions must be supported.

Otherwise, choose **HTTP Proxy Integration**.

---

# Common Interview Questions

### What is HTTP Custom Integration?

HTTP Custom Integration allows API Gateway to transform HTTP requests and responses using Mapping Templates before communicating with an HTTP backend.

---

### What is the main difference between HTTP Proxy and HTTP Custom Integration?

HTTP Proxy forwards requests directly with minimal processing, while HTTP Custom Integration uses Mapping Templates to transform requests and responses.

---

### When would you choose HTTP Custom Integration?

When integrating with legacy systems, converting request formats, hiding backend details, or supporting multiple client payload formats.

---

### Does HTTP Custom Integration require VTL?

Yes.

Request and response transformations are implemented using **Velocity Template Language (VTL)**.

---

# Best Practices

- Prefer **HTTP Proxy Integration** for modern REST services.
- Use **HTTP Custom Integration** only when request or response transformation is necessary.
- Keep Mapping Templates simple and avoid embedding business logic in VTL.
- Document all transformations clearly to simplify maintenance.
- Use response mapping to prevent exposing internal implementation details.
- Minimize transformations where possible to reduce latency and complexity.

---

# Key Takeaways

- HTTP Custom Integration enables API Gateway to transform requests and responses before communicating with HTTP backends.
- It relies on **Mapping Templates (VTL)** for request and response customization.
- It is particularly useful for legacy systems, payload normalization, XML integrations, and API version compatibility.
- Compared to HTTP Proxy Integration, it offers greater flexibility at the cost of additional configuration and maintenance.
- For most modern applications, HTTP Proxy Integration remains the preferred choice unless transformation capabilities are required.