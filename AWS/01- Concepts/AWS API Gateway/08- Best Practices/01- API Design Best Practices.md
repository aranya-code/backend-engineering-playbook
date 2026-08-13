# API Design Best Practices

## Overview

Designing a good API is about much more than making it functional. A well-designed API should be:

- Easy to understand
- Consistent
- Secure
- Scalable
- Versionable
- Performant
- Maintainable

Poor API design leads to:

- Difficult integrations
- Breaking client applications
- Higher maintenance costs
- Security issues
- Performance bottlenecks

This chapter covers the best practices followed by experienced backend engineers when designing production-grade REST APIs with Amazon API Gateway.

---

# Design APIs Around Resources

REST APIs should represent resources rather than actions.

Good:

```http
GET /users

GET /users/123

POST /orders

DELETE /orders/456
```

Poor:

```http
GET /getUsers

POST /createOrder

POST /deleteOrder
```

Resources should be nouns, not verbs.

---

# Use Proper HTTP Methods

Each HTTP method has a specific purpose.

| Method | Purpose |
|----------|---------|
| GET | Retrieve data |
| POST | Create a resource |
| PUT | Replace a resource |
| PATCH | Partially update a resource |
| DELETE | Remove a resource |

Example:

```http
GET /products

POST /products

PUT /products/15

PATCH /products/15

DELETE /products/15
```

---

# Use Meaningful Resource Names

Good:

```http
/users

/orders

/products

/payments
```

Avoid:

```http
/data

/info

/list

/items
```

Resource names should clearly represent business entities.

---

# Keep URLs Simple

Good:

```http
/users/123/orders
```

Avoid:

```http
/getUserOrdersByCustomerId/123
```

URLs should be intuitive and readable.

---

# Use Plural Resource Names

Preferred:

```http
/users

/orders

/products
```

Instead of:

```http
/user

/order

/product
```

Plural naming provides consistency across APIs.

---

# Use Nested Resources Carefully

Good:

```http
/users/15/orders
```

Avoid excessive nesting:

```http
/users/15/orders/22/items/7/payments/5
```

Deep URLs become difficult to understand and maintain.

---

# Use Query Parameters for Filtering

Instead of:

```http
/products/electronics
```

Use:

```http
GET /products?category=electronics
```

Additional examples:

```http
GET /orders?status=completed

GET /users?country=India
```

---

# Use Query Parameters for Sorting

Example:

```http
GET /products?sort=price
```

Descending:

```http
GET /products?sort=-price
```

Sorting should not require separate endpoints.

---

# Implement Pagination

Avoid:

```http
GET /products
```

Returning:

```text
1 Million Records
```

Instead:

```http
GET /products?page=1&limit=100
```

Benefits:

- Lower latency
- Smaller payloads
- Better scalability

---

# Support Searching

Example:

```http
GET /products?search=laptop
```

Instead of creating dedicated search endpoints.

---

# Return Appropriate HTTP Status Codes

Examples:

```http
200 OK
```

```http
201 Created
```

```http
204 No Content
```

```http
400 Bad Request
```

```http
401 Unauthorized
```

```http
403 Forbidden
```

```http
404 Not Found
```

```http
409 Conflict
```

```http
500 Internal Server Error
```

Never return:

```http
200 OK
```

for every request.

---

# Design Consistent Responses

Example:

```json
{
    "id": 101,
    "name": "Laptop",
    "price": 89999
}
```

Avoid changing response formats across endpoints.

---

# Standardize Error Responses

Good:

```json
{
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User does not exist."
    }
}
```

Avoid:

```json
{
    "status": "failed"
}
```

Consistent errors simplify client development.

---

# Validate Requests

Validate:

- Request body
- Path parameters
- Query parameters
- Headers

Invalid requests should be rejected before reaching business logic.

---

# Make APIs Idempotent

Safe operations:

```http
PUT

DELETE
```

Multiple identical requests should produce the same result.

For POST operations such as payments:

```text
Idempotency-Key
```

prevents duplicate processing.

---

# Version APIs

Example:

```http
/v1/users

/v2/users
```

Versioning prevents breaking existing clients.

---

# Keep APIs Stateless

Good:

```text
Request

↓

Response
```

Avoid:

```text
Server Memory

↓

Session State
```

Store session information in:

- JWT
- Redis
- DynamoDB

---

# Minimize Payload Size

Instead of:

```json
{
    "id": 1,
    "name": "Laptop",
    "description": "...",
    "supplier": "...",
    "warehouse": "...",
    "internalNotes": "..."
}
```

Return:

```json
{
    "id": 1,
    "name": "Laptop"
}
```

Only expose fields required by clients.

---

# Support Compression

Enable:

```text
Gzip
```

Benefits:

- Lower bandwidth
- Faster responses
- Better mobile performance

---

# Secure Sensitive Data

Never expose:

- Passwords
- Internal IDs
- Secrets
- API Keys
- Database details

Always sanitize responses.

---

# Design for Caching

Suitable endpoints:

```http
GET /products

GET /categories

GET /countries
```

Poor candidates:

```http
POST /payments

POST /login
```

Read-heavy APIs benefit from caching.

---

# Use HTTPS Everywhere

Always expose APIs through:

```text
HTTPS
```

Never send sensitive information over HTTP.

---

# Document Every Endpoint

Include:

- URL
- HTTP Method
- Parameters
- Request Example
- Response Example
- Error Responses

Use:

- OpenAPI
- Swagger
- ReDoc

---

# Keep APIs Backward Compatible

Instead of changing:

```http
/v1/orders
```

Create:

```http
/v2/orders
```

Existing clients continue functioning.

---

# Rate Limit Public APIs

Protect APIs using:

- API Keys
- Usage Plans
- Throttling
- AWS WAF

Rate limiting prevents abuse.

---

# Design for Observability

Every request should be traceable.

Include:

- Request ID
- Correlation ID
- Logs
- Metrics
- Traces

Use:

- CloudWatch
- AWS X-Ray

---

# Production API Example

```text
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Authentication

↓

Validation

↓

Lambda / ECS

↓

Database
```

Each layer has a clearly defined responsibility.

---

# Common API Design Mistakes

Avoid:

- Using verbs in URLs
- Ignoring HTTP semantics
- Returning inconsistent responses
- Exposing internal implementation details
- Large payloads
- No pagination
- No versioning
- Generic error messages
- Hardcoded URLs
- Breaking backward compatibility

---

# Best Practices Checklist

Before releasing an API:

- Resource-oriented URLs
- Correct HTTP methods
- Consistent naming
- Pagination implemented
- Filtering and sorting supported
- Request validation enabled
- HTTPS enforced
- Proper status codes returned
- Consistent error format
- API versioning strategy defined
- Authentication enabled
- Logging and monitoring configured
- Documentation published

---

# Common Interview Questions

### Why should REST APIs use nouns instead of verbs?

REST represents resources. HTTP methods already describe the action, so URLs should identify the resource rather than the operation.

---

### Why is pagination important?

Pagination improves performance, reduces payload sizes, lowers memory usage, and prevents clients from requesting excessively large datasets.

---

### Why are idempotent APIs important?

Idempotent APIs allow clients to safely retry requests without causing duplicate updates or unintended side effects, improving reliability in distributed systems.

---

### Why should APIs be stateless?

Stateless APIs scale horizontally because each request contains all the information required for processing, eliminating dependency on server-side session state.

---

### Why is API versioning necessary?

Versioning enables new functionality and breaking changes to be introduced without disrupting existing clients that depend on earlier API contracts.

---

# Key Takeaways

- Design APIs around resources using clear, consistent, and predictable URLs.
- Follow HTTP semantics by using appropriate methods and status codes.
- Keep APIs stateless, versioned, secure, and backward compatible.
- Implement pagination, filtering, sorting, validation, and standardized error responses for better usability.
- Well-designed APIs are easier to consume, maintain, scale, and operate in production.