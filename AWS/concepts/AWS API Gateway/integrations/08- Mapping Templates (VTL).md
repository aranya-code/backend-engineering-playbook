# Mapping Templates (Velocity Template Language - VTL)

## Overview

One of the most powerful features of Amazon API Gateway is the ability to **transform requests and responses** before they reach backend services or clients.

This transformation is performed using **Mapping Templates**, which are written in **Velocity Template Language (VTL)**.

Mapping Templates allow API Gateway to:

- Modify request bodies
- Modify response bodies
- Rename fields
- Add or remove headers
- Convert data formats
- Extract path parameters
- Extract query parameters
- Generate custom payloads

They are primarily used with:

- REST APIs
- Lambda Non-Proxy Integration
- HTTP Custom Integration
- AWS Service Integrations

> **Note:** HTTP APIs provide only limited transformation capabilities. Mapping Templates are primarily a feature of **REST APIs**.

---

# Why Mapping Templates?

Imagine a client sends:

```json
{
    "firstName": "John",
    "lastName": "Doe"
}
```

Your backend expects:

```json
{
    "name": "John Doe"
}
```

Instead of modifying either the client or the backend, API Gateway transforms the request.

```text
Client

↓

JSON

↓

API Gateway

↓

Mapping Template

↓

Backend
```

---

# Request Transformation

Without Mapping Templates:

```text
Client

↓

Backend
```

Both client and backend must use identical payloads.

With Mapping Templates:

```text
Client

↓

API Gateway

↓

Transformation

↓

Backend
```

The client and backend become independent.

---

# Response Transformation

Backend returns:

```json
{
    "customerId": 101,
    "status": "ACTIVE",
    "internalNotes": "Premium Customer"
}
```

Client should receive:

```json
{
    "id": 101,
    "status": "ACTIVE"
}
```

API Gateway removes unnecessary fields.

---

# Where Are Mapping Templates Used?

```text
Client

↓

API Gateway

↓

Request Mapping

↓

Backend

↓

Response Mapping

↓

Client
```

Templates can be applied to both requests and responses.

---

# What is VTL?

VTL stands for **Velocity Template Language**.

It is a template language originally developed by Apache Velocity.

API Gateway uses VTL to:

- Read incoming data
- Modify payloads
- Build new JSON objects
- Read headers
- Read query parameters
- Read path parameters

---

# Basic Template

Example:

```vtl
{
    "message":"Hello World"
}
```

Every request will produce:

```json
{
    "message":"Hello World"
}
```

---

# Accessing Request Body

Incoming request:

```json
{
    "name":"Laptop",
    "price":50000
}
```

Template:

```vtl
{
    "productName":
        "$input.path('$.name')",

    "productPrice":
        "$input.path('$.price')"
}
```

Generated payload:

```json
{
    "productName":"Laptop",
    "productPrice":50000
}
```

---

# Accessing Path Parameters

Request:

```http
GET /products/100
```

Resource:

```text
/products/{productId}
```

Template:

```vtl
{
    "id":
        "$input.params('productId')"
}
```

Output:

```json
{
    "id":"100"
}
```

---

# Accessing Query Parameters

Request:

```http
GET /products?page=2
```

Template:

```vtl
{
    "page":
        "$input.params('page')"
}
```

Output:

```json
{
    "page":"2"
}
```

---

# Accessing Headers

Request:

```http
Authorization: Bearer abc123
```

Template:

```vtl
{
    "token":
        "$input.params('Authorization')"
}
```

Output:

```json
{
    "token":"Bearer abc123"
}
```

---

# Creating New Fields

Client sends:

```json
{
    "username":"john"
}
```

Template:

```vtl
{
    "username":
        "$input.path('$.username')",

    "createdBy":
        "API Gateway"
}
```

Backend receives:

```json
{
    "username":"john",
    "createdBy":"API Gateway"
}
```

---

# Renaming Fields

Incoming request:

```json
{
    "firstName":"John"
}
```

Template:

```vtl
{
    "givenName":
        "$input.path('$.firstName')"
}
```

Output:

```json
{
    "givenName":"John"
}
```

---

# Removing Fields

Client sends:

```json
{
    "username":"john",
    "password":"secret",
    "rememberMe":true
}
```

Template:

```vtl
{
    "username":
        "$input.path('$.username')"
}
```

Backend receives:

```json
{
    "username":"john"
}
```

Sensitive or unnecessary fields are omitted.

---

# Combining Fields

Incoming request:

```json
{
    "firstName":"John",
    "lastName":"Doe"
}
```

Template:

```vtl
{
    "fullName":
        "$input.path('$.firstName') $input.path('$.lastName')"
}
```

Output:

```json
{
    "fullName":"John Doe"
}
```

---

# Response Mapping Example

Backend returns:

```json
{
    "employeeId":101,
    "status":"ACTIVE",
    "salary":90000
}
```

Template:

```vtl
{
    "id":
        "$input.path('$.employeeId')",

    "status":
        "$input.path('$.status')"
}
```

Client receives:

```json
{
    "id":101,
    "status":"ACTIVE"
}
```

Salary is hidden.

---

# Mapping XML

Legacy systems often expect XML.

Client:

```json
{
    "name":"Laptop",
    "price":50000
}
```

API Gateway converts:

```xml
<Product>
    <Name>Laptop</Name>
    <Price>50000</Price>
</Product>
```

This is common when integrating with enterprise systems.

---

# Error Mapping

Backend returns:

```json
{
    "error":"Database Failure"
}
```

Template:

```json
{
    "message":"Temporary Service Error"
}
```

Client receives a cleaner response.

---

# Common Variables

| Variable | Description |
|----------|-------------|
| `$input.body` | Entire request body |
| `$input.path()` | Extract JSON values |
| `$input.params()` | Read path, query, or header parameters |
| `$context` | Request context |
| `$stageVariables` | Stage variables |
| `$util` | Utility functions |

These variables are commonly used in Mapping Templates.

---

# Common Use Cases

Mapping Templates are useful for:

- Request transformation
- Response transformation
- API version compatibility
- Legacy system integration
- XML conversion
- Field renaming
- Removing sensitive information
- Building standardized payloads

---

# Advantages

## Client Independence

Clients and backend services can evolve independently.

---

## Legacy Integration

Supports older applications without code changes.

---

## Response Filtering

Hide internal implementation details.

---

## Payload Standardization

Multiple clients can produce a common backend request format.

---

## API Version Compatibility

Support old and new clients simultaneously.

---

# Disadvantages

## Learning Curve

VTL syntax is unfamiliar to many developers.

---

## Difficult Debugging

Template errors can be difficult to identify.

---

## More Maintenance

Templates require updates whenever payload formats change.

---

## Performance Overhead

Request transformation introduces a small amount of processing compared to Proxy Integrations.

---

# When Should You Use Mapping Templates?

Use Mapping Templates when:

- Request transformation is required.
- Response transformation is required.
- Legacy systems expect different payloads.
- Sensitive response fields should be removed.
- API version compatibility is needed.

Avoid them when:

- Client and backend already use the same format.
- Using Lambda Proxy Integration.
- Using HTTP Proxy Integration.

---

# Real-World Example

A banking system still uses XML internally.

Modern mobile applications communicate using JSON.

Architecture:

```text
Mobile App

↓

API Gateway

↓

JSON → XML

↓

Legacy Banking System

↓

XML → JSON

↓

Mobile App
```

Neither the mobile app nor the backend requires modification.

---

# Common Interview Questions

### What are Mapping Templates?

Mapping Templates are VTL scripts that transform requests and responses in API Gateway before they reach backend services or clients.

---

### Which API Gateway integrations commonly use Mapping Templates?

- Lambda Non-Proxy Integration
- HTTP Custom Integration
- AWS Service Integrations
- REST APIs

---

### Do Lambda Proxy Integrations use Mapping Templates?

Generally, no.

Lambda Proxy Integration forwards the complete HTTP request directly to Lambda without requiring request or response transformations.

---

### Why would you use Mapping Templates?

To transform payloads, support legacy systems, hide backend details, standardize request formats, and maintain API compatibility across different client versions.

---

# Best Practices

- Prefer Proxy Integrations whenever transformations are unnecessary.
- Keep Mapping Templates focused on data transformation, not business logic.
- Document templates thoroughly for easier maintenance.
- Use response mappings to prevent exposing sensitive backend fields.
- Avoid overly complex VTL expressions that become difficult to debug.
- Test Mapping Templates independently before deploying to production.

---

# Key Takeaways

- Mapping Templates allow API Gateway to transform requests and responses using **Velocity Template Language (VTL)**.
- They are primarily used with REST APIs, Lambda Non-Proxy Integrations, HTTP Custom Integrations, and AWS Service Integrations.
- Mapping Templates enable payload transformation, field renaming, response filtering, XML conversion, and API version compatibility.
- They provide powerful flexibility but increase configuration complexity and maintenance effort.
- For modern applications where transformation is unnecessary, Proxy Integrations remain the preferred architectural choice.