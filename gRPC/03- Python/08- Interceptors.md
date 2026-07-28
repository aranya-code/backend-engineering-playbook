# Overview

As applications grow, certain functionality needs to be executed for **every RPC call**, regardless of the specific business logic being invoked.

Examples include:

- Authentication
- Authorization
- Logging
- Metrics collection
- Request validation
- Tracing
- Rate limiting
- Auditing

Implementing this logic inside every RPC method quickly leads to duplicated code and makes services difficult to maintain.

To solve this problem, gRPC provides **Interceptors**.

An interceptor sits between the client and the server, allowing developers to inspect, modify, or reject RPC requests and responses before they reach the application logic.

Interceptors are conceptually similar to:

- Middleware in Django
- Middleware in FastAPI
- Filters in Spring Boot
- Express.js middleware

They provide a clean mechanism for implementing cross-cutting concerns without cluttering business logic.

This chapter explains how interceptors work, the different types of interceptors available in Python gRPC, and the best practices for using them in production systems.

---

# What is an Interceptor?

An interceptor is a component that executes automatically before or after an RPC.

Communication flow:

```text
Client

    │

    ▼

Interceptor

    │

    ▼

gRPC Service

    │

    ▼

Business Logic

    │

    ▼

Response

    │

    ▼

Interceptor

    │

    ▼

Client
```

The interceptor can inspect, modify, or terminate the request before it reaches the service.

---

# Why Use Interceptors?

Without interceptors, every RPC might contain duplicated logic.

Example:

```python
def GetEmployee(...):

    authenticate()

    log_request()

    validate_request()

    ...
```

The same code would need to be repeated in every method.

Using interceptors:

```text
Authentication

↓

Logging

↓

Validation

↓

Business Logic
```

The business logic remains clean and focused.

---

# Common Use Cases

Interceptors are commonly used for:

- Authentication
- Authorization
- Request logging
- Response logging
- Performance monitoring
- Distributed tracing
- Request validation
- Metrics collection
- Rate limiting
- Audit logging

These concerns apply across many or all RPC methods.

---

# Types of Interceptors

Python gRPC supports two primary categories.

## Client Interceptors

Execute before a request leaves the client and after a response is received.

Typical responsibilities:

- Add authentication tokens
- Retry failed requests
- Log outgoing calls
- Collect client-side metrics

---

## Server Interceptors

Execute before the request reaches the service implementation.

Typical responsibilities:

- Authentication
- Authorization
- Logging
- Metrics
- Validation
- Tracing

Server interceptors are commonly used in production services.

---

# Request Lifecycle

The following illustrates a typical server-side request flow.

```text
Client

    │

    ▼

Authentication

    │

    ▼

Authorization

    │

    ▼

Logging

    │

    ▼

Validation

    │

    ▼

Business Logic

    │

    ▼

Response
```

Each interceptor performs one specific responsibility before passing control to the next stage.

---

# Server Interceptor Example

A server interceptor typically extends the gRPC interceptor interface.

Example:

```python
import grpc


class LoggingInterceptor(grpc.ServerInterceptor):

    def intercept_service(
        self,
        continuation,
        handler_call_details,
    ):

        print(
            f"RPC: {handler_call_details.method}"
        )

        return continuation(handler_call_details)
```

This interceptor logs every incoming RPC.

---

# Registering Server Interceptors

Interceptors are registered when creating the server.

Example:

```python
server = grpc.server(

    executor,

    interceptors=[

        LoggingInterceptor(),

    ]

)
```

Every incoming RPC passes through the interceptor before reaching the service.

---

# Client Interceptor Example

A client interceptor executes before outgoing RPC calls.

Example:

```python
class ClientLoggingInterceptor(
    grpc.UnaryUnaryClientInterceptor
):

    ...

```

Typical responsibilities include:

- Logging
- Retry logic
- Metadata injection
- Request timing

---

# Adding Authentication Metadata

One common use case is attaching authentication tokens.

Example:

```text
Authorization

Bearer <token>
```

The interceptor automatically adds the metadata to every outgoing request.

Without an interceptor, every RPC would need to attach the token manually.

---

# Logging Requests

Logging is one of the most common interceptor use cases.

Example log:

```text
RPC Method:
/employee.EmployeeService/GetEmployee

Execution Time:
18 ms

Status:
OK
```

Centralized logging improves observability and troubleshooting.

---

# Authentication

Authentication verifies the identity of the caller.

Example workflow:

```text
Client

    │

JWT Token

    ▼

Authentication Interceptor

    │

Valid?

 ┌──┴───┐

 │      │

Yes     No

 │      │

 ▼      ▼

Service  UNAUTHENTICATED
```

The request reaches the service only if authentication succeeds.

---

# Authorization

After authentication, authorization determines whether the caller has permission to perform the requested operation.

Example:

```text
Role = Admin

↓

Allowed

↓

Continue
```

If authorization fails:

```text
PERMISSION_DENIED
```

The business logic is never executed.

---

# Metrics Collection

Interceptors are commonly used to collect metrics.

Typical metrics include:

- Request count
- Response count
- Error count
- Request latency
- Active RPCs
- Success rate

These metrics can be exported to monitoring systems such as Prometheus.

---

# Distributed Tracing

Modern microservices often use distributed tracing.

Example flow:

```text
Gateway

↓

User Service

↓

Order Service

↓

Payment Service
```

An interceptor can propagate trace identifiers through every RPC, enabling end-to-end request tracking.

---

# Rate Limiting

Interceptors can enforce request limits.

Example:

```text
100 Requests

↓

Interceptor

↓

Allowed

or

RESOURCE_EXHAUSTED
```

This helps protect services from abuse or excessive traffic.

---

# Validation

Basic request validation can also be centralized.

Example:

```text
Incoming Request

↓

Required Fields Present?

↓

Valid Format?

↓

Business Logic
```

Centralizing validation reduces duplicate code across services.

---

# Interceptor Chain

Multiple interceptors can be combined.

```text
Client

    │

Authentication

    │

Authorization

    │

Logging

    │

Metrics

    │

Tracing

    │

Business Logic
```

Each interceptor performs a single responsibility.

---

# Advantages of Interceptors

Interceptors provide several benefits.

- Separation of concerns
- Cleaner service implementations
- Code reuse
- Centralized logging
- Easier monitoring
- Simplified authentication
- Better maintainability
- Consistent behavior across services

---

# When Should You Avoid Interceptors?

Interceptors should not contain business logic.

Avoid using interceptors for:

- Database operations unrelated to request processing
- Business rules
- Domain-specific workflows
- Complex application logic

Their purpose is to implement infrastructure-level concerns.

---

# Best Practices

- Keep interceptors lightweight.
- Implement one responsibility per interceptor.
- Avoid performing expensive computations.
- Return appropriate gRPC status codes for failures.
- Use interceptors for cross-cutting concerns only.
- Register interceptors in a consistent order.
- Log useful information without exposing sensitive data.

---

# Common Mistakes

Avoid the following mistakes:

- Placing business logic inside interceptors.
- Combining multiple responsibilities into one interceptor.
- Logging sensitive information such as passwords or tokens.
- Performing long-running blocking operations.
- Ignoring authentication failures.
- Creating complex dependency chains between interceptors.

---

# Key Takeaways

- Interceptors allow developers to execute logic before or after RPC processing.
- They are commonly used for authentication, authorization, logging, metrics, tracing, and validation.
- Client interceptors operate on outgoing requests, while server interceptors process incoming requests.
- Interceptors help separate infrastructure concerns from business logic, resulting in cleaner and more maintainable services.
- Multiple interceptors can be chained together to build a robust request-processing pipeline.
- Properly designed interceptors improve security, observability, and consistency across gRPC applications.