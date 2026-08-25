# Lambda Non-Proxy Integration

## Overview

**Lambda Non-Proxy Integration** is an API Gateway integration where API Gateway performs **request and response transformations** before communicating with an AWS Lambda function.

Unlike Lambda Proxy Integration, the Lambda function **does not receive the complete HTTP request**. Instead, API Gateway uses **Mapping Templates (Velocity Template Language - VTL)** to construct a custom request payload for Lambda.

Similarly, Lambda's response can be transformed before being returned to the client.

Although this integration offers greater flexibility, it is more complex to configure and is generally used only when request or response transformation is required.

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
             AWS Lambda
                    │
          Business Logic
                    │
                    ▼
       Response Mapping (VTL)
                    │
                    ▼
                 Client
```

Unlike Proxy Integration, API Gateway actively participates in request and response processing.

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

Custom JSON

↓

Lambda

↓

Response

↓

Mapping Template

↓

HTTP Response

↓

Client
```

Notice that both the incoming request and outgoing response can be modified.

---

# Why Use Non-Proxy Integration?

Sometimes backend applications should not receive the raw HTTP request.

Examples:

- Legacy systems
- XML backends
- Older Lambda functions
- Standardized payloads
- Hiding HTTP-specific details

Instead of forwarding the complete request, API Gateway constructs a payload that exactly matches what the backend expects.

---

# Example

Incoming HTTP request:

```http
POST /users

Content-Type: application/json
```

```json
{
    "firstName": "John",
    "lastName": "Doe"
}
```

Instead of forwarding the entire request, API Gateway can transform it into:

```json
{
    "name": "John Doe"
}
```

Lambda receives only:

```json
{
    "name": "John Doe"
}
```

---

# Mapping Templates

The transformation is performed using **Velocity Template Language (VTL).**

Example:

```vtl
{
    "name": "$input.path('$.firstName') $input.path('$.lastName')"
}
```

Incoming JSON:

```json
{
    "firstName":"John",
    "lastName":"Doe"
}
```

Generated payload:

```json
{
    "name":"John Doe"
}
```

---

# Lambda Event

Unlike Proxy Integration, the Lambda event is completely controlled by the mapping template.

Example:

```json
{
    "customerId": 10,
    "amount": 500
}
```

Only these fields reach Lambda.

HTTP headers, query parameters, and path parameters are not included unless explicitly mapped.

---

# Mapping Headers

Request:

```http
Authorization: Bearer abc123
```

Mapping Template:

```vtl
{
    "token":"$input.params('Authorization')"
}
```

Lambda receives:

```json
{
    "token":"Bearer abc123"
}
```

---

# Mapping Path Parameters

Request:

```http
GET /users/101
```

Mapping Template:

```vtl
{
    "userId":"$input.params('userId')"
}
```

Lambda receives:

```json
{
    "userId":"101"
}
```

---

# Mapping Query Parameters

Request:

```http
GET /products?page=3
```

Mapping Template:

```vtl
{
    "page":"$input.params('page')"
}
```

Lambda receives:

```json
{
    "page":"3"
}
```

---

# Response Mapping

Lambda response:

```json
{
    "id":100,
    "status":"SUCCESS",
    "internalId":"XYZ123"
}
```

Mapping Template:

```vtl
{
    "id":"$input.path('$.id')",
    "status":"$input.path('$.status')"
}
```

Client receives:

```json
{
    "id":100,
    "status":"SUCCESS"
}
```

Internal fields are hidden.

---

# Error Mapping

Lambda may return:

```json
{
    "error":"Invalid Customer"
}
```

API Gateway can map this to:

```http
400 Bad Request
```

with a custom error message.

Different Lambda errors can be mapped to different HTTP status codes.

---

# Common Use Cases

Lambda Non-Proxy Integration is useful when:

- Request transformation is required
- Response transformation is required
- Legacy payload formats must be supported
- XML-to-JSON conversion is needed
- Internal fields should be hidden
- Multiple client formats must be supported

---

# Advantages

## Fine-Grained Control

Every request can be customized.

---

## Hide Backend Details

Backend implementation remains private.

---

## Standardized Payloads

Different clients can produce a common request format.

---

## Response Customization

Responses can be filtered before reaching clients.

---

## Legacy Integration

Older applications can continue using existing payload structures.

---

# Disadvantages

## More Configuration

Every endpoint requires mapping templates.

---

## VTL Learning Curve

Developers must understand Velocity Template Language.

---

## Harder Debugging

Errors may occur in mapping templates instead of application code.

---

## Additional Maintenance

Changes to request formats require updating templates.

---

# Lambda Proxy vs Non-Proxy

| Feature | Proxy | Non-Proxy |
|----------|--------|-----------|
| Entire HTTP Request | ✅ | ❌ |
| Mapping Templates | ❌ | ✅ |
| Request Transformation | ❌ | ✅ |
| Response Transformation | ❌ | ✅ |
| Configuration | Simple | Complex |
| Recommended for New APIs | ✅ | Only if Needed |

---

# When Should You Use It?

Choose Lambda Non-Proxy Integration when:

- Backend expects a specific payload
- Clients send different request formats
- Response transformation is required
- Migrating legacy APIs
- Hiding backend implementation details

Otherwise, Lambda Proxy Integration is generally the better choice.

---

# Real-World Example

A banking application exposes:

```http
POST /transfer
```

Clients send:

```json
{
    "sender":"123",
    "receiver":"456",
    "amount":5000
}
```

The existing Lambda expects:

```json
{
    "fromAccount":"123",
    "toAccount":"456",
    "value":5000
}
```

API Gateway transforms the request before invoking Lambda.

No application changes are required.

---

# Common Interview Questions

### What is Lambda Non-Proxy Integration?

It is an integration where API Gateway transforms requests and responses using Mapping Templates before communicating with Lambda.

---

### Does Lambda receive the full HTTP request?

No.

Lambda receives only the payload generated by the mapping template.

---

### When should you choose Non-Proxy Integration?

When request or response transformation is required, or when integrating with legacy applications that expect a specific payload format.

---

### Which integration is recommended for new serverless applications?

Lambda Proxy Integration, because it is simpler, requires less configuration, and allows Lambda to handle request processing directly.

---

# Best Practices

- Prefer **Lambda Proxy Integration** unless transformation is required.
- Keep mapping templates as simple as possible.
- Avoid placing business logic inside VTL templates.
- Use response mapping to remove sensitive or internal fields before returning data to clients.
- Document mapping templates thoroughly, as they can become difficult to maintain over time.

---

# Key Takeaways

- Lambda Non-Proxy Integration uses **Mapping Templates (VTL)** to transform requests and responses.
- Lambda receives a custom payload rather than the full HTTP request.
- Response mapping allows API Gateway to modify backend responses before sending them to clients.
- This integration is ideal for legacy systems, payload transformations, and response customization.
- For most modern serverless applications, Lambda Proxy Integration remains the preferred option due to its simplicity and maintainability.