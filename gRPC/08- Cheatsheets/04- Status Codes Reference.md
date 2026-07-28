# Overview

gRPC uses its own set of **standard status codes** to indicate the outcome of every Remote Procedure Call (RPC). Unlike REST, which relies on HTTP status codes such as **200**, **404**, and **500**, gRPC returns language-independent status codes that are understood consistently across all supported programming languages.

Understanding these status codes is essential for implementing proper error handling, retries, monitoring, debugging, and production troubleshooting.

This cheat sheet provides a quick reference to every gRPC status code, when it is returned, common causes, retry recommendations, and best practices.

---

# Status Code Categories

| Category | Status Codes |
|----------|--------------|
| Success | OK |
| Client Errors | INVALID_ARGUMENT, NOT_FOUND, ALREADY_EXISTS, FAILED_PRECONDITION, OUT_OF_RANGE |
| Authentication & Authorization | UNAUTHENTICATED, PERMISSION_DENIED |
| Resource & Capacity | RESOURCE_EXHAUSTED |
| Request Lifecycle | CANCELLED, DEADLINE_EXCEEDED |
| Server Errors | INTERNAL, UNAVAILABLE, DATA_LOSS, UNKNOWN, UNIMPLEMENTED, ABORTED |

---

# Complete Status Code Reference

| Code | Number | Meaning | Retry? |
|------|-------:|---------|:------:|
| OK | 0 | Request completed successfully | ❌ |
| CANCELLED | 1 | Request was cancelled | Depends |
| UNKNOWN | 2 | Unknown error | Depends |
| INVALID_ARGUMENT | 3 | Invalid request data | ❌ |
| DEADLINE_EXCEEDED | 4 | Deadline expired | Sometimes |
| NOT_FOUND | 5 | Resource not found | ❌ |
| ALREADY_EXISTS | 6 | Resource already exists | ❌ |
| PERMISSION_DENIED | 7 | Authorization failed | ❌ |
| RESOURCE_EXHAUSTED | 8 | Resource limit exceeded | Sometimes |
| FAILED_PRECONDITION | 9 | Operation cannot proceed in current state | ❌ |
| ABORTED | 10 | Operation aborted due to concurrency/conflict | Yes |
| OUT_OF_RANGE | 11 | Value outside valid range | ❌ |
| UNIMPLEMENTED | 12 | RPC or feature not implemented | ❌ |
| INTERNAL | 13 | Internal server error | Depends |
| UNAVAILABLE | 14 | Service temporarily unavailable | Yes |
| DATA_LOSS | 15 | Unrecoverable data corruption | ❌ |
| UNAUTHENTICATED | 16 | Authentication required or failed | ❌ |

---

# Success

## OK (0)

### Meaning

The RPC completed successfully.

### Common Causes

- Request processed successfully.
- Response returned correctly.

### Retry

Not required.

---

# Request Lifecycle Errors

## CANCELLED (1)

### Meaning

The operation was cancelled before completion.

### Common Causes

- Client cancelled the request.
- User navigated away.
- Application shutdown.
- Explicit cancellation.

### Retry

Retry only if cancellation was accidental.

---

## DEADLINE_EXCEEDED (4)

### Meaning

The request did not complete before its deadline.

### Common Causes

- Slow database queries.
- Network latency.
- Downstream service delays.
- CPU starvation.
- Long-running business logic.

### Retry

Retry only if the operation is idempotent and the failure is transient.

### Production Checklist

- Check P95/P99 latency.
- Review downstream dependencies.
- Verify deadline configuration.
- Analyze distributed traces.

---

# Client Errors

## INVALID_ARGUMENT (3)

### Meaning

The client sent invalid input.

### Examples

- Invalid email address.
- Negative quantity.
- Missing required value.
- Incorrect data format.

### Retry

No.

The request must be corrected first.

---

## NOT_FOUND (5)

### Meaning

The requested resource does not exist.

### Examples

- User not found.
- Product not found.
- Order not found.

### Retry

No.

---

## ALREADY_EXISTS (6)

### Meaning

The resource already exists.

### Examples

- Duplicate username.
- Existing email address.
- Existing database record.

### Retry

No.

---

## FAILED_PRECONDITION (9)

### Meaning

The system state prevents the operation.

### Examples

- Cannot delete a non-empty folder.
- Payment before order confirmation.
- Inventory unavailable.

### Retry

Only after the precondition changes.

---

## OUT_OF_RANGE (11)

### Meaning

A supplied value is outside the valid range.

### Examples

- Invalid page number.
- Negative index.
- Exceeded maximum value.

### Retry

No.

---

# Authentication & Authorization

## UNAUTHENTICATED (16)

### Meaning

Authentication failed or credentials were missing.

### Common Causes

- Missing JWT.
- Expired token.
- Invalid token.
- Invalid client certificate.

### Retry

Retry only after obtaining valid credentials.

---

## PERMISSION_DENIED (7)

### Meaning

The client is authenticated but not authorized.

### Common Causes

- Missing permissions.
- Incorrect role.
- Access policy violation.

### Retry

No.

Permissions must change first.

---

# Resource & Capacity

## RESOURCE_EXHAUSTED (8)

### Meaning

A resource limit has been exceeded.

### Examples

- Rate limiting.
- Memory exhaustion.
- Disk full.
- Maximum concurrent streams reached.

### Retry

Yes, preferably with exponential backoff.

---

# Server Errors

## UNKNOWN (2)

### Meaning

An unknown or unexpected error occurred.

### Common Causes

- Unhandled exceptions.
- Proxy issues.
- Unexpected runtime failures.

### Retry

Depends on the root cause.

---

## ABORTED (10)

### Meaning

The operation was aborted due to concurrency or transaction conflicts.

### Examples

- Optimistic locking failure.
- Transaction conflict.
- Concurrent update.

### Retry

Usually yes.

---

## UNIMPLEMENTED (12)

### Meaning

The RPC method or feature is not implemented.

### Common Causes

- Method missing.
- Incorrect service version.
- Server does not support the RPC.

### Retry

No.

---

## INTERNAL (13)

### Meaning

An unexpected internal server error occurred.

### Common Causes

- Application bugs.
- Database failures.
- Null pointer exceptions.
- Serialization failures.

### Retry

Only if the error is believed to be transient.

---

## UNAVAILABLE (14)

### Meaning

The service is temporarily unavailable.

### Common Causes

- Service down.
- Network failure.
- DNS issues.
- Load balancer failure.
- Kubernetes pod restart.
- Service discovery issues.

### Retry

Yes.

Use exponential backoff and retry limits.

### Production Checklist

- Verify service health.
- Check Kubernetes pods.
- Inspect load balancer.
- Verify DNS resolution.
- Review server logs.

---

## DATA_LOSS (15)

### Meaning

Unrecoverable data corruption has occurred.

### Examples

- Corrupted storage.
- Corrupted messages.
- Storage integrity failures.

### Retry

No.

Immediate investigation is required.

---

# Retry Strategy

| Status Code | Retry Recommendation |
|-------------|----------------------|
| OK | No |
| CANCELLED | Sometimes |
| DEADLINE_EXCEEDED | Sometimes |
| RESOURCE_EXHAUSTED | Yes |
| ABORTED | Yes |
| INTERNAL | Depends |
| UNAVAILABLE | Yes |
| UNKNOWN | Depends |
| All Others | No |

---

# Mapping to HTTP Status Codes

| gRPC | Approximate HTTP Equivalent |
|------|-----------------------------|
| OK | 200 OK |
| INVALID_ARGUMENT | 400 Bad Request |
| UNAUTHENTICATED | 401 Unauthorized |
| PERMISSION_DENIED | 403 Forbidden |
| NOT_FOUND | 404 Not Found |
| ALREADY_EXISTS | 409 Conflict |
| RESOURCE_EXHAUSTED | 429 Too Many Requests |
| DEADLINE_EXCEEDED | 504 Gateway Timeout |
| INTERNAL | 500 Internal Server Error |
| UNAVAILABLE | 503 Service Unavailable |
| UNIMPLEMENTED | 501 Not Implemented |

> **Note:** These mappings are approximate. gRPC applications should always handle native gRPC status codes rather than relying on HTTP equivalents.

---

# Common Production Issues

| Symptom | Likely Status Code |
|---------|--------------------|
| Authentication failure | UNAUTHENTICATED |
| Permission error | PERMISSION_DENIED |
| Invalid request payload | INVALID_ARGUMENT |
| Slow dependency | DEADLINE_EXCEEDED |
| Service outage | UNAVAILABLE |
| Duplicate resource | ALREADY_EXISTS |
| Missing record | NOT_FOUND |
| Database conflict | ABORTED |
| Rate limiting | RESOURCE_EXHAUSTED |
| Unexpected server exception | INTERNAL |

---

# Best Practices

- Return the most specific status code possible.
- Avoid using `INTERNAL` for validation or business logic errors.
- Configure sensible deadlines for all client requests.
- Retry only transient failures such as `UNAVAILABLE` and `RESOURCE_EXHAUSTED`.
- Use exponential backoff with retry limits.
- Log status codes with correlation IDs for easier troubleshooting.
- Monitor status code trends to detect production issues early.

---

# Common Mistakes

- Returning `INTERNAL` for every exception.
- Retrying validation or authorization failures.
- Ignoring `DEADLINE_EXCEEDED` errors without investigating latency.
- Treating `UNAUTHENTICATED` and `PERMISSION_DENIED` as the same error.
- Failing to distinguish transient failures from permanent failures.

---

# Key Takeaways

- gRPC status codes provide a consistent, language-independent mechanism for reporting RPC outcomes.
- Correct use of status codes improves client behavior, observability, and production reliability.
- Understanding which errors are retryable and which require user intervention is essential for building resilient distributed systems.
- Monitoring status code distributions can quickly reveal authentication issues, latency problems, service outages, and application bugs.