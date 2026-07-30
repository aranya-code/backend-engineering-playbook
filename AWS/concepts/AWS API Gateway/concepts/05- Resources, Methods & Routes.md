# Resources, Methods & Routes

## Overview

Every API in Amazon API Gateway is built using three fundamental building blocks:

- Resources
- Methods
- Routes

These components define **what URLs are available**, **which HTTP operations are supported**, and **how requests are routed to backend services**.

Understanding these concepts is essential because almost every API Gateway configuration starts with defining resources and methods.

---

# Resource

A **Resource** represents a URL path in your API.

For example, consider an e-commerce application.

```text
/products

/orders

/users

/payments
```

Each of these URL paths is a separate resource.

Think of a resource as a **noun** that represents something in your application.

---

## Example Resource Tree

```text
/
├── users
├── products
├── orders
└── payments
```

Each resource can have one or more HTTP methods.

---

# Nested Resources

Resources can be nested to represent relationships.

Example:

```text
/users/{userId}

/users/{userId}/orders

/orders/{orderId}

/products/{productId}/reviews
```

Resource hierarchy:

```text
/
└── users
      │
      └── {userId}
             │
             └── orders
```

Nested resources improve API organization and readability.

---

# Path Parameters

Resources often contain dynamic values.

Example:

```text
/users/100

/users/250

/users/500
```

Instead of creating separate resources, API Gateway uses **path parameters**.

```text
/users/{userId}
```

Here,

```text
{userId}
```

is a path parameter.

---

## Multiple Path Parameters

Example:

```text
/users/{userId}/orders/{orderId}
```

Incoming request:

```text
/users/42/orders/1001
```

API Gateway extracts:

```text
userId = 42

orderId = 1001
```

These values are forwarded to the backend.

---

# HTTP Methods

A resource alone does nothing.

A resource becomes useful only after attaching one or more **HTTP methods**.

Common HTTP methods:

| Method | Purpose |
|----------|----------|
| GET | Retrieve data |
| POST | Create new data |
| PUT | Replace existing data |
| PATCH | Partially update data |
| DELETE | Remove data |
| OPTIONS | CORS Preflight |
| HEAD | Metadata only |

---

# GET Method

Used to retrieve data.

Example:

```http
GET /products
```

Returns:

```json
[
    {
        "id": 1,
        "name": "Laptop"
    }
]
```

Another example:

```http
GET /products/10
```

Returns one product.

---

# POST Method

Creates a new resource.

Example:

```http
POST /products
```

Request:

```json
{
    "name": "Keyboard",
    "price": 2500
}
```

Response:

```json
{
    "id": 101,
    "name": "Keyboard"
}
```

---

# PUT Method

Replaces an existing resource.

Example:

```http
PUT /products/101
```

Request:

```json
{
    "name": "Gaming Keyboard",
    "price": 4500
}
```

Entire resource is replaced.

---

# PATCH Method

Updates only selected fields.

Example:

```http
PATCH /products/101
```

Request:

```json
{
    "price": 3999
}
```

Only the price changes.

---

# DELETE Method

Deletes a resource.

Example:

```http
DELETE /products/101
```

Response:

```text
204 No Content
```

---

# OPTIONS Method

OPTIONS is mainly used for **CORS preflight requests**.

Browser sends:

```http
OPTIONS /products
```

API Gateway responds with:

```text
Access-Control-Allow-Origin

Access-Control-Allow-Methods

Access-Control-Allow-Headers
```

We'll cover CORS in detail later.

---

# HEAD Method

Similar to GET, except it returns **headers only**.

Example:

```http
HEAD /products
```

Useful for:

- Checking resource availability
- Reading metadata
- Verifying cache information

---

# Resources and Methods Together

Example API:

```text
/products
```

Supports:

| Method | Action |
|----------|---------|
| GET | List products |
| POST | Create product |

---

Another resource:

```text
/products/{productId}
```

Supports:

| Method | Action |
|----------|---------|
| GET | Get one product |
| PUT | Replace product |
| PATCH | Update product |
| DELETE | Delete product |

---

# API Resource Tree

Example:

```text
/
├── users
│     ├── GET
│     ├── POST
│     └── {userId}
│            ├── GET
│            ├── PUT
│            └── DELETE
│
├── products
│     ├── GET
│     ├── POST
│     └── {productId}
│            ├── GET
│            ├── PATCH
│            └── DELETE
│
└── orders
      ├── GET
      └── POST
```

This is how most REST APIs are organized.

---

# Routes

The term **Route** depends on the API type.

- **REST APIs** use **Resources + Methods**.
- **HTTP APIs** use **Routes**.
- **WebSocket APIs** use **Route Keys**.

---

## REST API Routing

A request is matched using:

```text
HTTP Method

+

Resource Path
```

Example:

```http
GET /products
```

Another example:

```http
DELETE /products/10
```

---

## HTTP API Routing

HTTP APIs define routes directly.

Example:

```text
GET /products

POST /products

GET /users/{id}
```

Although internally similar to REST APIs, AWS presents these as routes rather than separate resources and methods.

---

## WebSocket Route Keys

WebSocket APIs don't use HTTP methods.

Instead, they define route keys.

Example:

```text
$connect

$disconnect

$default

sendMessage

joinRoom
```

When a client sends:

```json
{
    "action": "sendMessage"
}
```

API Gateway routes the request to the **sendMessage** backend.

---

# Route Matching

Suppose the following routes exist:

```text
GET /products

GET /products/{id}

POST /products
```

Incoming request:

```http
GET /products/25
```

Matched route:

```text
GET /products/{id}
```

Incoming request:

```http
POST /products
```

Matched route:

```text
POST /products
```

---

# Resource Naming Best Practices

Use plural nouns.

Good:

```text
/users

/products

/orders

/payments
```

Avoid verbs.

Bad:

```text
/getUsers

/createOrder

/deleteProduct
```

HTTP methods already describe the action.

---

# RESTful URL Design

Well-designed REST APIs are resource-oriented.

Good examples:

```text
GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}
```

Avoid:

```text
/createUser

/updateUser

/deleteUser

/getAllUsers
```

---

# Common Interview Questions

### What is a Resource?

A resource is a URL path that represents an entity in the API, such as `/users` or `/orders`.

---

### What is the difference between a Resource and a Method?

A **Resource** defines the URL path, while a **Method** defines the HTTP operation (GET, POST, PUT, DELETE, etc.) that can be performed on that resource.

---

### What is a Route?

A route defines how API Gateway matches incoming requests to backend integrations. In REST APIs, a route is determined by the combination of **HTTP Method + Resource Path**. In HTTP APIs, routes are defined directly, while WebSocket APIs use **Route Keys**.

---

### Why should REST APIs use nouns instead of verbs?

Resources represent entities, while HTTP methods represent actions. This separation makes APIs intuitive, consistent, and aligned with REST principles.

---

# Best Practices

- Use plural nouns for resource names.
- Keep URLs hierarchical and meaningful.
- Use path parameters for dynamic values.
- Avoid embedding actions in URLs.
- Use the correct HTTP method for each operation.
- Keep resource hierarchies shallow whenever possible to improve readability.

---

# Key Takeaways

- Resources represent URL paths in an API.
- Methods define the operations that can be performed on a resource.
- Path parameters allow dynamic resource identification.
- REST APIs organize endpoints using **Resources + Methods**, while HTTP APIs define **Routes**, and WebSocket APIs use **Route Keys**.
- Following RESTful naming conventions leads to APIs that are easier to understand, maintain, and consume.