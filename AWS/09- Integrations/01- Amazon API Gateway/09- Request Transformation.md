# Request Transformation

## Overview

Request Transformation is a feature of Amazon API Gateway that allows incoming client requests to be modified before they are forwarded to the backend service.

Different clients often send requests in different formats, while backend services may expect a completely different request structure.

Instead of modifying every client or changing backend services, API Gateway can transform requests using **Mapping Templates** written in **Velocity Template Language (VTL)**.

Request Transformation enables you to:

- Rename fields
- Add new fields
- Remove unwanted fields
- Transform headers
- Transform query parameters
- Transform path parameters
- Convert payload formats
- Support legacy backend systems

API Gateway acts as a translation layer between clients and backend services.

---

# Why Request Transformation?

Suppose a mobile application sends:

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

Without transformation:

```text
Mobile App

↓

Backend Modification Required
```

With API Gateway:

```text
Mobile App

↓

API Gateway

↓

Request Transformation

↓

Backend
```

The backend receives exactly the format it expects.

---

# Architecture

```text
               Client

                  │

                  ▼

          Amazon API Gateway

                  │

        Request Transformation

                  │

                  ▼

      Lambda / ECS / EC2 Backend
```

Transformation occurs before the backend integration.

---

# Request Flow

```text
Incoming Request

↓

API Gateway

↓

Mapping Template

↓

Transformed Request

↓

Backend
```

The client never sees the transformed payload.

---

# Mapping Templates

API Gateway uses **Velocity Template Language (VTL)** to perform request transformations.

Example:

```vtl
{
    "name":
        "$input.path('$.firstName')"
}
```

The template extracts values from the incoming request and creates a new payload.

---

# Request Body Transformation

Incoming request:

```json
{
    "productName": "Laptop",
    "price": 50000
}
```

Backend expects:

```json
{
    "name": "Laptop",
    "cost": 50000
}
```

Mapping Template:

```vtl
{
    "name":
        "$input.path('$.productName'),

    "cost":
        "$input.path('$.price')
}
```

Backend receives the transformed payload.

---

# Header Transformation

Client request:

```http
Authorization: Bearer abc123
```

Backend expects:

```json
{
    "token":"Bearer abc123"
}
```

Template:

```vtl
{
    "token":
        "$input.params('Authorization')"
}
```

---

# Query Parameter Transformation

Client request:

```http
GET /products?page=2
```

Template:

```vtl
{
    "pageNumber":
        "$input.params('page')
}
```

Backend receives:

```json
{
    "pageNumber":"2"
}
```

---

# Path Parameter Transformation

Resource:

```text
/orders/{orderId}
```

Request:

```http
GET /orders/100
```

Template:

```vtl
{
    "id":
        "$input.params('orderId')
}
```

Backend receives:

```json
{
    "id":"100"
}
```

---

# Adding New Fields

Incoming request:

```json
{
    "username":"john"
}
```

Template:

```vtl
{
    "username":
        "$input.path('$.username'),

    "source":
        "API Gateway"
}
```

Backend receives:

```json
{
    "username":"john",
    "source":"API Gateway"
}
```

---

# Removing Fields

Client sends:

```json
{
    "username":"john",
    "password":"secret"
}
```

Template:

```vtl
{
    "username":
        "$input.path('$.username')
}
```

The password field is never forwarded to the backend.

---

# Setting Default Values

Suppose a client omits a field.

Template:

```vtl
{
    "country":"India"
}
```

Backend always receives:

```json
{
    "country":"India"
}
```

This is useful for applying default configuration values.

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
        "$input.path('$.firstName')
        $input.path('$.lastName')"
}
```

Backend receives:

```json
{
    "fullName":"John Doe"
}
```

---

# Content-Type Transformation

Client:

```text
application/json
```

Backend:

```text
application/xml
```

API Gateway can transform payloads into the required format using Mapping Templates.

---

# Legacy System Integration

Modern application:

```json
{
    "customerId":100
}
```

Legacy backend expects:

```xml
<Customer>
    <Id>100</Id>
</Customer>
```

API Gateway performs the conversion without changing either system.

---

# API Version Compatibility

Version 1 clients send:

```json
{
    "name":"John"
}
```

Version 2 backend expects:

```json
{
    "firstName":"John"
}
```

Request Transformation bridges the gap between API versions.

---

# Common Use Cases

Request Transformation is commonly used for:

- Legacy application integration
- SOAP to REST migration
- API version compatibility
- Payload normalization
- Field renaming
- Header mapping
- Query parameter mapping
- XML ↔ JSON conversion

---

# Advantages

## Backend Independence

Clients and backend services evolve independently.

---

## Simplified Client Development

Clients can use their preferred payload format.

---

## Legacy Integration

Supports older systems without backend modifications.

---

## Standardized Requests

Different client payloads can be converted into a common backend format.

---

## Easier API Evolution

Changes in request formats do not necessarily require backend changes.

---

# Limitations

Request Transformation:

- Uses Velocity Template Language (VTL), which has a learning curve.
- Adds slight processing overhead.
- Should not contain business logic.
- Can become difficult to maintain if templates are overly complex.

---

# Real-World Example

A logistics company has:

```text
React Application

↓

API Gateway

↓

Request Transformation

↓

Legacy SOAP Service

↓

ERP System
```

The React application sends JSON, while the ERP system expects XML.

API Gateway performs the translation transparently.

---

# Best Practices

- Keep Mapping Templates simple and readable.
- Use Request Transformation only for payload conversion.
- Avoid implementing business logic inside VTL templates.
- Document every transformation clearly.
- Validate requests before applying transformations.
- Prefer Lambda Proxy Integration when transformation is unnecessary.

---

# Common Interview Questions

### What is Request Transformation?

Request Transformation modifies incoming client requests before forwarding them to the backend using Mapping Templates written in Velocity Template Language (VTL).

---

### What language is used for Request Transformation?

Amazon API Gateway uses **Velocity Template Language (VTL)** for request mapping templates.

---

### Why use Request Transformation?

It enables payload restructuring, field renaming, parameter mapping, legacy integration, API version compatibility, and backend abstraction without modifying clients or backend services.

---

### Does Request Transformation replace backend validation?

No.

It only changes the request format. Backend services must still validate business rules, permissions, and application logic.

---

### Should business logic be implemented in Mapping Templates?

No.

Mapping Templates should focus only on request transformation. Business logic belongs in backend applications.

---

# Key Takeaways

- Request Transformation modifies client requests before they reach backend services.
- API Gateway performs transformations using Mapping Templates written in Velocity Template Language (VTL).
- Common transformations include field renaming, parameter mapping, payload restructuring, and format conversion.
- Request Transformation simplifies API evolution, legacy integration, and backend abstraction.
- Keep Mapping Templates simple and use them only for data transformation, not business logic.