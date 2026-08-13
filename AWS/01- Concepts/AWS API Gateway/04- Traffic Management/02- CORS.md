# CORS (Cross-Origin Resource Sharing)

## Overview

**Cross-Origin Resource Sharing (CORS)** is a browser security mechanism that allows a web application running on one origin to access resources hosted on another origin.

By default, web browsers enforce the **Same-Origin Policy (SOP)**, which prevents JavaScript from making requests to a different origin unless the server explicitly allows it.

Amazon API Gateway provides built-in support for configuring CORS, enabling secure cross-origin communication between frontend applications and backend APIs.

Without CORS, browsers block cross-origin requests even if the API itself is functioning correctly.

---

# What is an Origin?

An origin consists of:

- Protocol
- Domain
- Port

Example:

```text
https://app.example.com:443
```

Origin Components:

```text
https

↓

Protocol

----------------------

app.example.com

↓

Domain

----------------------

443

↓

Port
```

If any one of these components differs, the browser considers it a different origin.

---

# Same-Origin Policy

Suppose your frontend is hosted at:

```text
https://app.example.com
```

and your API is hosted at:

```text
https://api.example.com
```

Even though they belong to the same company, they are different origins.

Browser:

```text
Frontend

↓

API Request

↓

Different Origin

↓

Blocked
```

The request reaches the browser but JavaScript cannot access the response unless CORS is enabled.

---

# Why CORS Exists

Without the Same-Origin Policy:

```text
Malicious Website

↓

Reads Your Banking Session

↓

Steals Sensitive Data
```

The Same-Origin Policy prevents websites from accessing resources belonging to another origin without permission.

CORS provides a controlled way to relax this restriction.

---

# How CORS Works

```text
Browser

↓

API Request

↓

API Gateway

↓

CORS Headers

↓

Browser

↓

Allow or Block
```

The browser decides whether JavaScript can access the response based on the CORS headers returned by the server.

---

# Simple Requests

A request is considered **simple** when it:

- Uses GET, HEAD, or POST
- Uses standard headers
- Uses supported content types

Example:

```http
GET /products
```

Flow:

```text
Browser

↓

GET Request

↓

API Gateway

↓

Access-Control-Allow-Origin

↓

Response Allowed
```

No preflight request is required.

---

# Preflight Requests

More complex requests require a **preflight** request.

Examples include:

- PUT
- PATCH
- DELETE
- Custom Headers
- Authorization Header
- application/json with certain configurations

The browser first sends:

```http
OPTIONS /products
```

This request asks:

> "Is this cross-origin request allowed?"

---

# Preflight Flow

```text
Browser

↓

OPTIONS Request

↓

API Gateway

↓

CORS Response

↓

Allowed?

│

├── Yes

│      │

│      ▼

│ Actual Request

│

└── No

       │

       ▼

Browser Blocks Request
```

---

# OPTIONS Method

The OPTIONS method is automatically used for preflight requests.

Example:

```http
OPTIONS /users
```

API Gateway responds with CORS headers instead of invoking the backend.

---

# Required CORS Headers

Several HTTP headers control CORS behavior.

| Header | Purpose |
|----------|----------|
| Access-Control-Allow-Origin | Allowed origins |
| Access-Control-Allow-Methods | Allowed HTTP methods |
| Access-Control-Allow-Headers | Allowed request headers |
| Access-Control-Allow-Credentials | Allows cookies or credentials |
| Access-Control-Max-Age | How long the browser caches the preflight response |

---

# Access-Control-Allow-Origin

This header specifies which origins may access the API.

Example:

```http
Access-Control-Allow-Origin:

https://app.example.com
```

Only that frontend can access the response.

Allowing every origin:

```http
Access-Control-Allow-Origin: *
```

This is suitable only for public APIs.

---

# Access-Control-Allow-Methods

Specifies permitted HTTP methods.

Example:

```http
Access-Control-Allow-Methods:

GET,POST,PUT,DELETE
```

The browser blocks methods not listed.

---

# Access-Control-Allow-Headers

Defines which request headers the client may send.

Example:

```http
Access-Control-Allow-Headers:

Authorization,Content-Type
```

Without this header, browsers reject requests containing custom headers.

---

# Access-Control-Allow-Credentials

Allows browsers to send:

- Cookies
- Client Certificates
- Authorization credentials

Example:

```http
Access-Control-Allow-Credentials:

true
```

> **Important:** This cannot be used together with `Access-Control-Allow-Origin: *`.

---

# Access-Control-Max-Age

The browser can cache the preflight response.

Example:

```http
Access-Control-Max-Age:

3600
```

Meaning:

```text
Cache

↓

1 Hour
```

Subsequent requests avoid another OPTIONS call until the cache expires.

---

# Example Request

Frontend:

```text
https://app.example.com
```

Request:

```http
GET /orders

Authorization: Bearer token
```

Browser sends:

```http
OPTIONS /orders
```

API Gateway replies:

```http
Access-Control-Allow-Origin:
https://app.example.com

Access-Control-Allow-Methods:
GET

Access-Control-Allow-Headers:
Authorization
```

Browser then sends the actual GET request.

---

# CORS Configuration in API Gateway

REST APIs allow CORS to be configured per resource or method.

HTTP APIs provide a simplified CORS configuration where you specify:

- Allowed Origins
- Allowed Methods
- Allowed Headers
- Exposed Headers
- Credentials
- Max Age

API Gateway automatically handles OPTIONS requests.

---

# Common CORS Errors

Browser Console:

```text
Access to fetch at

https://api.example.com

has been blocked by CORS policy
```

Possible causes:

- Missing Access-Control-Allow-Origin
- Missing OPTIONS method
- Incorrect allowed methods
- Incorrect allowed headers
- Credentials used with wildcard origin

---

# CORS vs Authentication

These concepts are unrelated.

| CORS | Authentication |
|-------|----------------|
| Browser security feature | User identity verification |
| Controls browser access | Controls API access |
| Enforced by browsers | Enforced by API Gateway |
| Does not identify users | Identifies users |

Enabling CORS does **not** secure an API.

Authentication is still required.

---

# Real-World Example

Architecture:

```text
React Application

↓

https://app.company.com

↓

API Gateway

↓

Lambda

↓

Amazon DynamoDB
```

API Gateway returns:

```http
Access-Control-Allow-Origin:

https://app.company.com
```

The browser allows JavaScript to access the response.

---

# Best Practices

- Allow only trusted origins whenever possible.
- Avoid using `Access-Control-Allow-Origin: *` for authenticated APIs.
- Enable only the HTTP methods your API requires.
- Limit allowed headers to the minimum necessary.
- Configure OPTIONS correctly for REST APIs.
- Cache preflight responses using `Access-Control-Max-Age`.
- Remember that CORS is **not** an authentication or authorization mechanism.

---

# Common Interview Questions

### What is CORS?

CORS (Cross-Origin Resource Sharing) is a browser security mechanism that allows servers to specify which origins are permitted to access their resources.

---

### Why is the OPTIONS method used?

Browsers send an OPTIONS request as a **preflight request** to determine whether a cross-origin request is permitted before sending the actual request.

---

### What is the purpose of Access-Control-Allow-Origin?

It specifies which origins are allowed to access the API response.

---

### Can Access-Control-Allow-Origin be `*` when using credentials?

No.

When `Access-Control-Allow-Credentials: true` is enabled, the origin must be explicitly specified. A wildcard (`*`) is not allowed.

---

### Does enabling CORS make an API secure?

No.

CORS only controls whether browsers allow JavaScript to access responses. Authentication and authorization are still required to secure the API.

---

# Key Takeaways

- CORS enables secure cross-origin communication between web browsers and APIs.
- Browsers enforce the Same-Origin Policy, and CORS selectively relaxes this restriction.
- Preflight OPTIONS requests are used for non-simple cross-origin requests.
- API Gateway simplifies CORS configuration for both REST APIs and HTTP APIs.
- CORS is a browser security feature and should not be confused with authentication or authorization.