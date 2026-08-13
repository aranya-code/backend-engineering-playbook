# Request Lifecycle

## Overview

Every request sent to Amazon API Gateway passes through a well-defined processing pipeline before reaching the backend service and returning a response to the client.

Understanding this lifecycle is critical because it explains:

- Where authentication occurs
- When authorization is checked
- How request validation works
- When caching is evaluated
- How throttling is enforced
- When Lambda or HTTP integrations are invoked
- How responses are transformed before reaching clients

Many production issues can be diagnosed simply by understanding where a request fails within this lifecycle.

---

# Complete Request Lifecycle

```text
                Client

                   │

                   ▼

             DNS Resolution

                   │

                   ▼

             TLS Handshake

                   │

                   ▼

          Amazon API Gateway

                   │

                   ▼

         Resource & Method Match

                   │

                   ▼

     Authentication & Authorization

                   │

                   ▼

          Resource Policy Check

                   │

                   ▼

          Request Validation

                   │

                   ▼

          API Key Validation

                   │

                   ▼

             Throttling

                   │

                   ▼

            Cache Lookup

         ┌─────────┴─────────┐

         ▼                   ▼

    Cache Hit           Cache Miss

         │                   │

         │                   ▼

         │        Request Transformation

         │                   │

         │                   ▼

         │        Backend Integration

         │                   │

         └──────────┬────────┘

                    ▼

         Response Transformation

                    ▼

            Response Compression

                    ▼

          CloudWatch Logs

                    ▼

             Client Response
```

Every request follows this sequence.

---

# Step 1 – DNS Resolution

Client:

```text
https://api.example.com
```

DNS resolves:

```text
api.example.com

↓

API Gateway Endpoint
```

Only after DNS resolution can the client establish a connection.

---

# Step 2 – TLS Handshake

API Gateway supports HTTPS.

```text
Client

↓

TLS Handshake

↓

Encrypted Connection
```

If Mutual TLS is enabled:

```text
Client Certificate

↓

Validation

↓

Connection Established
```

---

# Step 3 – Resource Matching

API Gateway determines:

```text
/users/123

↓

Resource

↓

/users/{id}
```

If no matching resource exists:

```http
404 Not Found
```

is returned immediately.

---

# Step 4 – Method Matching

API Gateway verifies:

```http
GET

POST

PUT

DELETE
```

Example:

```http
DELETE /users/123
```

If DELETE is not configured:

```http
405 Method Not Allowed
```

---

# Step 5 – Authentication

Authentication verifies:

```text
Who is calling?
```

Possible mechanisms:

- IAM
- Cognito
- JWT
- Lambda Authorizer
- Mutual TLS

If authentication fails:

```http
401 Unauthorized
```

Backend is never invoked.

---

# Step 6 – Authorization

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
What can you do?
```

Example:

```text
Authenticated User

↓

Delete Customer

↓

Not Allowed

↓

403 Forbidden
```

---

# Step 7 – Resource Policy Evaluation

Resource Policies determine whether the caller is allowed.

Example:

```text
Corporate IP

↓

Allowed

--------------------

Unknown IP

↓

Denied
```

Rejected requests stop here.

---

# Step 8 – Request Validation

API Gateway validates:

- Request body
- Query parameters
- Headers
- Path parameters

Example:

```json
{}
```

Expected:

```json
{
    "email":"abc@test.com"
}
```

Response:

```http
400 Bad Request
```

---

# Step 9 – API Key Validation

If the API requires an API Key:

```text
Client

↓

API Key

↓

Usage Plan

↓

Continue
```

Otherwise:

```http
403 Forbidden
```

---

# Step 10 – Throttling

API Gateway evaluates request limits.

Example:

```text
100 Requests/sec
```

If exceeded:

```http
429 Too Many Requests
```

Backend is protected.

---

# Step 11 – Cache Lookup

If API caching is enabled:

```text
Request

↓

Cache
```

Two outcomes:

```text
Cache Hit

↓

Immediate Response
```

or

```text
Cache Miss

↓

Backend Invocation
```

---

# Step 12 – Request Transformation

API Gateway applies Mapping Templates.

Example:

Client:

```json
{
    "name":"John"
}
```

Backend:

```json
{
    "fullName":"John"
}
```

Transformation occurs automatically.

---

# Step 13 – Backend Integration

API Gateway invokes:

```text
Lambda

↓

HTTP

↓

AWS Service

↓

VPC Link
```

The backend processes the request.

---

# Step 14 – Backend Response

Example:

```json
{
    "status":"SUCCESS"
}
```

Response returns to API Gateway.

---

# Step 15 – Response Transformation

API Gateway modifies the response.

Example:

Backend:

```json
{
    "employeeId":101
}
```

Client:

```json
{
    "id":101
}
```

---

# Step 16 – Response Compression

If enabled:

```text
Large JSON

↓

Gzip Compression

↓

Client
```

Bandwidth usage decreases.

---

# Step 17 – Logging & Monitoring

During request processing:

```text
CloudWatch Metrics

↓

CloudWatch Logs

↓

Access Logs

↓

AWS X-Ray
```

Telemetry is generated automatically.

---

# Step 18 – Response Returned

Finally:

```text
API Gateway

↓

HTTPS

↓

Client
```

The request lifecycle completes.

---

# Failure Points

A request can fail at multiple stages.

```text
Authentication

↓

401

---------------------

Authorization

↓

403

---------------------

Validation

↓

400

---------------------

Method

↓

405

---------------------

Resource

↓

404

---------------------

Throttling

↓

429

---------------------

Backend Failure

↓

500
```

Knowing the stage helps identify the root cause quickly.

---

# Successful Request Flow

```text
Client

↓

Authentication

↓

Authorization

↓

Validation

↓

Throttle Check

↓

Cache

↓

Backend

↓

Transformation

↓

Compression

↓

Client
```

Every component contributes to the final response.

---

# Lifecycle in a Microservices Architecture

```text
Client

↓

API Gateway

↓

Authentication

↓

Order Service

↓

Inventory Service

↓

Payment Service

↓

Response
```

API Gateway performs common concerns only once before routing requests.

---

# Observability Throughout the Lifecycle

```text
Every Request

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

Access Logs

↓

X-Ray Trace
```

Every stage can be monitored and analyzed.

---

# Best Practices

- Understand where authentication, authorization, and validation occur.
- Reject invalid requests as early as possible.
- Enable caching for read-heavy endpoints.
- Use Mapping Templates only for payload transformation.
- Monitor every stage using CloudWatch and X-Ray.
- Design backends assuming API Gateway has already handled common concerns.
- Document the request lifecycle for development teams.

---

# Common Interview Questions

### What happens first when a request reaches API Gateway?

After DNS resolution and the TLS handshake, API Gateway matches the request to the appropriate resource and HTTP method.

---

### At what stage is authentication performed?

Authentication occurs before request validation and backend integration.

---

### When does API Gateway check the cache?

After authentication, authorization, validation, API key verification, and throttling, but before invoking the backend.

---

### When is the backend invoked?

Only after all security, validation, throttling, and caching checks have completed successfully.

---

### When are CloudWatch Logs and X-Ray generated?

Telemetry is generated throughout the request lifecycle, allowing complete visibility into request processing and backend execution.

---

# Key Takeaways

- Every API Gateway request follows a predictable processing pipeline from DNS resolution to the final client response.
- Security checks, request validation, throttling, and cache evaluation occur before backend invocation.
- Request and Response Transformations allow API Gateway to adapt payloads without changing clients or backend services.
- CloudWatch Metrics, Logs, Access Logs, and AWS X-Ray provide observability throughout the request lifecycle.
- Understanding the request lifecycle is essential for designing, debugging, and operating production-grade APIs.