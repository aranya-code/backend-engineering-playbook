# Deadlines & Timeouts

# Introduction

In distributed systems, network communication is not always reliable.

A server may become:

- Slow
- Busy
- Unavailable
- Overloaded

If a client waits indefinitely for a response, it can lead to:

- Poor user experience
- Wasted resources
- Thread starvation
- Cascading failures across services

To prevent this, gRPC provides **Deadlines**.

---

# What is a Deadline?

A **Deadline** specifies the maximum amount of time the client is willing to wait for an RPC to complete.

If the server does not respond before the deadline expires, the RPC is automatically cancelled.

Instead of waiting forever, the client receives an error indicating that the deadline has been exceeded.

---

# Why Are Deadlines Important?

Imagine an application where one service depends on another.

```text
Frontend
    │
    ▼
User Service
    │
    ▼
Payment Service
    │
    ▼
Database
```

Suppose the database becomes very slow.

Without deadlines:

```text
Frontend

↓

Waiting...

↓

Waiting...

↓

Waiting...
```

Every service continues waiting.

Eventually:

- Connections remain occupied.
- Threads become blocked.
- Response times increase.
- The entire application may become unresponsive.

---

# Using Deadlines

With deadlines:

```text
Client

↓

Wait 5 Seconds

↓

No Response

↓

Cancel RPC

↓

Return Error
```

Instead of waiting indefinitely, the client quickly detects the problem and can take appropriate action.

---

# Deadline vs Timeout

Although the terms are often used interchangeably, they are slightly different.

| Deadline | Timeout |
|----------|----------|
| Absolute point in time | Relative duration |
| "Finish before this time" | "Wait this long" |
| Preferred term in gRPC | Common networking term |

Example:

Current time:

```text
10:00:00
```

Deadline:

```text
10:00:05
```

Timeout:

```text
5 seconds
```

Both represent the same waiting period but are expressed differently.

---

# Setting a Deadline

In Python, a deadline is commonly specified using the `timeout` parameter.

Example:

```python
response = stub.GetEmployee(
    request,
    timeout=5
)
```

This means:

- Wait up to **5 seconds**.
- If the server responds sooner, return immediately.
- If not, cancel the RPC.

---

# Request Timeline

```text
Client

    │

    │ Send Request

    ▼

Server

    │

    │ Processing...

    │

    │ Processing...

    │

    ▼

Response
```

If the response arrives before the deadline:

```text
RPC Success
```

Otherwise:

```text
Deadline Exceeded
```

---

# Deadline Exceeded

If the server does not complete processing before the deadline, gRPC returns an error.

Example:

```text
Status Code:

DEADLINE_EXCEEDED
```

The client knows:

- The request was not completed within the allowed time.
- It may retry the operation if appropriate.
- It can inform the user about the delay.

---

# What Happens on the Server?

When a deadline expires:

1. The client cancels the RPC.
2. The server receives a cancellation notification.
3. The server can stop unnecessary processing.
4. Resources are released.

This helps improve overall system efficiency.

---

# Choosing an Appropriate Deadline

The deadline should depend on the operation being performed.

Examples:

| Operation | Example Deadline |
|-----------|------------------|
| User Login | 2–5 seconds |
| Fetch User Profile | 2–5 seconds |
| Database Query | 3–10 seconds |
| File Upload | 30–120 seconds |
| Machine Learning Inference | 30–60 seconds |
| Report Generation | 60 seconds or more |

There is no universal value.

Choose a deadline based on the expected execution time and user experience requirements.

---

# Deadlines in Microservices

Consider the following architecture.

```text
Frontend

↓

API Gateway

↓

User Service

↓

Payment Service

↓

Inventory Service
```

Suppose the frontend sets a deadline of **10 seconds**.

Each downstream service should reserve enough time for the remaining services.

Example:

| Service | Deadline |
|----------|----------|
| Frontend → API Gateway | 10 seconds |
| API Gateway → User Service | 8 seconds |
| User Service → Payment Service | 6 seconds |
| Payment Service → Inventory Service | 4 seconds |

This ensures that each service has time to process its work without exceeding the client's overall deadline.

---

# Benefits of Deadlines

Using deadlines provides several advantages.

- Prevents clients from waiting forever.
- Improves application responsiveness.
- Frees resources quickly.
- Prevents cascading failures.
- Helps detect slow services.
- Improves system reliability.
- Encourages efficient service design.

---

# Common Mistakes

Avoid the following mistakes:

- Not setting deadlines at all.
- Using the same deadline for every RPC.
- Setting deadlines that are too short.
- Setting deadlines that are excessively long.
- Ignoring deadline exceeded errors.
- Continuing expensive processing after the client has cancelled the request.

---

# Best Practices

When working with deadlines:

- Set a deadline for every external RPC.
- Choose realistic values based on the operation.
- Handle `DEADLINE_EXCEEDED` errors gracefully.
- Release resources promptly when a request is cancelled.
- Propagate deadlines to downstream services when appropriate.
- Monitor slow RPCs to identify performance bottlenecks.

---

# Key Takeaways

- A deadline specifies how long a client is willing to wait for an RPC to complete.
- Deadlines prevent clients from waiting indefinitely for slow or unavailable services.
- If a deadline expires, gRPC returns the `DEADLINE_EXCEEDED` status code.
- Deadlines improve responsiveness, resource utilization, and overall system reliability.
- Every production gRPC application should configure appropriate deadlines for remote procedure calls.
- Well-designed deadline strategies help prevent cascading failures in distributed systems.