# Error Handling & Status Codes


# Introduction

In any distributed system, requests do not always succeed.

A request may fail because:

- The requested resource does not exist.
- The client sends invalid data.
- The user is not authenticated.
- The server is unavailable.
- The network connection is interrupted.
- The request takes too long.

Instead of returning arbitrary error messages, gRPC uses **standardized status codes** to describe the outcome of every RPC.

This allows clients written in different programming languages to interpret errors consistently.

---

# What is a Status Code?

A **status code** indicates whether an RPC succeeded or failed.

Every RPC returns one status code.

```text
RPC Request

        │

        ▼

Server

        │

        ▼

Status Code

        │

        ▼

Client
```

The client examines the status code to determine what happened.

---

# Successful RPC

If the RPC completes successfully, gRPC returns:

```text
OK
```

This indicates:

- The request was processed successfully.
- The response is valid.
- No errors occurred.

---

# Failed RPC

If something goes wrong, gRPC returns an appropriate error status.

Example:

```text
NOT_FOUND
```

or

```text
UNAUTHENTICATED
```

or

```text
DEADLINE_EXCEEDED
```

The status code provides a standardized description of the failure.

---

# Common gRPC Status Codes

| Status Code | Meaning |
|-------------|---------|
| OK | Request completed successfully |
| CANCELLED | Request was cancelled |
| UNKNOWN | Unknown error occurred |
| INVALID_ARGUMENT | Client sent invalid input |
| DEADLINE_EXCEEDED | Request exceeded its deadline |
| NOT_FOUND | Requested resource does not exist |
| ALREADY_EXISTS | Resource already exists |
| PERMISSION_DENIED | Client lacks permission |
| UNAUTHENTICATED | Client is not authenticated |
| RESOURCE_EXHAUSTED | Resource limit exceeded |
| FAILED_PRECONDITION | System state prevents operation |
| ABORTED | Operation was aborted |
| OUT_OF_RANGE | Value is outside valid range |
| UNIMPLEMENTED | RPC method is not implemented |
| INTERNAL | Internal server error |
| UNAVAILABLE | Service is temporarily unavailable |
| DATA_LOSS | Unrecoverable data corruption |
| UNAUTHENTICATED | Authentication failed |

---

# OK

The request completed successfully.

```text
Client

↓

Get Employee

↓

Server

↓

Employee Returned

↓

Status: OK
```

This is the most common status returned by successful RPCs.

---

# INVALID_ARGUMENT

The client sends invalid input.

Example:

```text
Employee ID = -10
```

Since employee IDs cannot be negative, the server returns:

```text
INVALID_ARGUMENT
```

This tells the client that the request itself is incorrect.

---

# NOT_FOUND

The requested resource does not exist.

Example:

```text
Employee ID = 9999
```

If no employee exists with that ID:

```text
Status

NOT_FOUND
```

---

# ALREADY_EXISTS

The client attempts to create a resource that already exists.

Example:

```text
Create User

Email:

alice@example.com
```

If that email already exists:

```text
ALREADY_EXISTS
```

---

# UNAUTHENTICATED

The client has not provided valid authentication credentials.

Example:

```text
Missing JWT Token
```

Result:

```text
UNAUTHENTICATED
```

The client must authenticate before retrying.

---

# PERMISSION_DENIED

The client is authenticated but does not have permission to perform the requested operation.

Example:

```text
Employee

Attempts to Delete User
```

Result:

```text
PERMISSION_DENIED
```

Authentication and authorization are different concepts.

---

# DEADLINE_EXCEEDED

The server did not finish processing before the client's deadline expired.

Example:

```text
Client

↓

Wait 5 Seconds

↓

No Response

↓

DEADLINE_EXCEEDED
```

This status was discussed in the previous chapter.

---

# UNAVAILABLE

The service is temporarily unavailable.

Possible reasons include:

- Server restart
- Network outage
- Load balancer failure
- Temporary maintenance

Unlike `INTERNAL`, this error is often temporary and clients may retry the request.

---

# INTERNAL

An unexpected error occurred inside the server.

Examples include:

- Unexpected exception
- Database failure
- Null reference
- Programming bug

Clients should not depend on the exact cause of an `INTERNAL` error.

---

# How Clients Handle Errors

When an RPC fails, the client receives an exception.

Example:

```python
try:
    response = stub.GetEmployee(request)

except grpc.RpcError as error:
    print(error.code())
    print(error.details())
```

The client can inspect:

- Status code
- Error message
- Additional error information

and decide how to respond.

---

# Choosing the Right Status Code

Selecting the correct status code makes APIs easier to understand.

Examples:

| Scenario | Status Code |
|----------|-------------|
| Employee not found | NOT_FOUND |
| Invalid email | INVALID_ARGUMENT |
| Missing login token | UNAUTHENTICATED |
| User lacks permission | PERMISSION_DENIED |
| Request timeout | DEADLINE_EXCEEDED |
| Duplicate email | ALREADY_EXISTS |
| Server crashed | INTERNAL |
| Temporary outage | UNAVAILABLE |

---

# Why Standardized Status Codes Matter

Without standardized status codes:

- Every service would invent its own error messages.
- Clients would require custom parsing logic.
- Cross-language interoperability would become difficult.

Standardized status codes provide:

- Consistency
- Predictability
- Better debugging
- Easier client implementation
- Improved interoperability

---

# Best Practices

When handling errors:

- Return the most appropriate status code.
- Do not expose sensitive internal implementation details.
- Include clear, human-readable error messages.
- Handle expected failures gracefully.
- Retry only transient failures such as `UNAVAILABLE`.
- Log server-side exceptions for troubleshooting.

---

# Common Mistakes

Avoid the following mistakes:

- Returning `INTERNAL` for every failure.
- Using `UNKNOWN` instead of specific status codes.
- Exposing stack traces to clients.
- Returning success when an operation actually failed.
- Ignoring `DEADLINE_EXCEEDED` or `UNAVAILABLE` errors.

---

# Key Takeaways

- Every gRPC RPC returns a standardized status code.
- `OK` indicates a successful operation.
- Common error codes include `INVALID_ARGUMENT`, `NOT_FOUND`, `UNAUTHENTICATED`, `PERMISSION_DENIED`, `DEADLINE_EXCEEDED`, `UNAVAILABLE`, and `INTERNAL`.
- Clients use status codes to determine how to respond to failures.
- Choosing the correct status code improves API consistency, debugging, and interoperability.
- Well-designed error handling is essential for building reliable distributed systems.