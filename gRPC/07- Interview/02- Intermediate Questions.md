# Overview

Intermediate-level gRPC interviews move beyond basic concepts and focus on implementation, application development, debugging, and production readiness.

At this stage, interviewers expect candidates to have hands-on experience building gRPC applications rather than simply understanding the theory. Questions often involve Protocol Buffers, code generation, streaming, authentication, deadlines, metadata, error handling, asynchronous programming, and deployment.

The goal is to determine whether a candidate can independently develop, debug, and maintain production-quality gRPC services.

This chapter contains common intermediate interview questions, model answers, follow-up questions, and practical explanations based on real-world backend engineering scenarios.

---

# Question 1

## Explain the complete lifecycle of a gRPC request.

### What the Interviewer is Testing

The interviewer wants to evaluate whether you understand the end-to-end communication process inside gRPC.

### Model Answer

A typical gRPC request follows these steps:

1. The client invokes a stub method.
2. The request object is serialized using Protocol Buffers.
3. The message is transmitted over an HTTP/2 connection.
4. The server receives and deserializes the request.
5. The corresponding RPC handler executes.
6. The response is serialized.
7. The response is sent back over HTTP/2.
8. The client deserializes the response into an object.

```text
Client

↓

Stub

↓

Protocol Buffers

↓

HTTP/2

↓

Server

↓

Business Logic

↓

Protocol Buffers

↓

HTTP/2

↓

Client
```

### Follow-up Questions

- Where does serialization happen?
- Which layer uses HTTP/2?
- When are interceptors executed?

---

# Question 2

## What files are generated from a .proto file in Python?

### What the Interviewer is Testing

Understanding of Protocol Buffer code generation.

### Model Answer

Running `protoc` with the Python gRPC plugin generates two files.

```text
employee_pb2.py
```

Contains:

- Message classes
- Enum definitions
- Serialization logic

```text
employee_pb2_grpc.py
```

Contains:

- Client stubs
- Server interfaces
- Registration helpers

Together these files allow Python applications to communicate without manually implementing the networking layer.

### Follow-up Questions

- Can these files be modified manually?
- What happens if the `.proto` changes?

---

# Question 3

## What is the purpose of a stub?

### What the Interviewer is Testing

Whether you understand how clients communicate with servers.

### Model Answer

A stub is a client-side proxy generated from the `.proto` file.

Instead of constructing HTTP requests manually, the application calls methods on the stub.

Example:

```python
employee = stub.GetEmployee(request)
```

Internally the stub:

- Serializes the request
- Sends it over HTTP/2
- Waits for the response
- Deserializes the response

To the developer, it behaves like a normal function call.

### Follow-up Questions

- Is the stub generated automatically?
- Does every language have stubs?

---

# Question 4

## What are gRPC Metadata?

### What the Interviewer is Testing

Understanding of request metadata.

### Model Answer

Metadata consists of key-value pairs sent alongside an RPC request.

Typical use cases include:

- Authentication tokens
- Request IDs
- Correlation IDs
- Tenant IDs
- Language preferences
- Trace identifiers

Metadata is similar to HTTP headers but is designed specifically for gRPC.

### Example

```text
authorization

Bearer <JWT>
```

### Follow-up Questions

- Is metadata encrypted?
- Can metadata be modified by interceptors?

---

# Question 5

## What are Interceptors?

### What the Interviewer is Testing

Knowledge of middleware concepts.

### Model Answer

Interceptors are middleware components that execute before or after an RPC.

Common responsibilities include:

- Authentication
- Authorization
- Logging
- Metrics
- Distributed tracing
- Retry handling

Instead of duplicating this logic inside every RPC handler, it is implemented once inside an interceptor.

### Follow-up Questions

- What is the difference between client and server interceptors?
- Can multiple interceptors be chained?

---

# Question 6

## What is the difference between Deadlines and Timeouts?

### What the Interviewer is Testing

Understanding of request lifetime management.

### Model Answer

A timeout specifies how long the client is willing to wait.

A deadline specifies the exact point in time when the request expires.

Example:

```text
Current Time

10:00

↓

Deadline

10:05
```

If the server has not completed processing by 10:05, the request is cancelled.

Deadlines help prevent indefinitely hanging RPCs.

### Follow-up Questions

- What happens when a deadline expires?
- Which gRPC status code is returned?

---

# Question 7

## Explain Unary vs Streaming RPC.

### What the Interviewer is Testing

Knowledge of communication models.

### Model Answer

Unary RPC:

```text
Client

↓

Request

↓

Server

↓

Response
```

Streaming RPC:

```text
Client

↓

Message

↓

Message

↓

Message
```

or

```text
Server

↓

Message

↓

Message

↓

Message
```

Streaming is ideal for:

- Live notifications
- Chat applications
- Video streaming
- Telemetry
- Real-time dashboards

### Follow-up Questions

- Which streaming type resembles REST?
- When would you use Bidirectional Streaming?

---

# Question 8

## Why does gRPC use HTTP/2?

### What the Interviewer is Testing

Understanding of transport-layer improvements.

### Model Answer

HTTP/2 provides features required by gRPC.

These include:

- Multiplexing
- Header compression
- Persistent connections
- Binary framing
- Flow control

These capabilities reduce latency and improve throughput compared to HTTP/1.1.

### Follow-up Questions

- Can gRPC use HTTP/1.1?
- What is multiplexing?

---

# Question 9

## How does gRPC handle errors?

### What the Interviewer is Testing

Knowledge of error handling.

### Model Answer

gRPC uses predefined status codes instead of HTTP status codes.

Examples include:

- OK
- NOT_FOUND
- INVALID_ARGUMENT
- UNAUTHENTICATED
- PERMISSION_DENIED
- DEADLINE_EXCEEDED
- INTERNAL
- UNAVAILABLE

These codes are available across every supported programming language.

### Follow-up Questions

- What is the difference between UNAVAILABLE and INTERNAL?
- Should application errors use INTERNAL?

---

# Question 10

## What is Reflection?

### What the Interviewer is Testing

Understanding of service discovery.

### Model Answer

Reflection allows clients to discover:

- Services
- RPC methods
- Messages

without requiring local `.proto` files.

Reflection is commonly used by:

- grpcurl
- BloomRPC
- Postman
- Evans

It is typically enabled in development and restricted or disabled in production.

### Follow-up Questions

- Does Reflection affect performance?
- Should Reflection be enabled in production?

---

# Additional Intermediate Questions

A backend interview may also include:

- What is grpcurl?
- How does gRPC perform authentication?
- What is Mutual TLS (mTLS)?
- What are Protocol Buffer field numbers?
- What is `oneof`?
- What are repeated fields?
- What are maps in Protocol Buffers?
- What is backward compatibility?
- What happens when fields are removed?
- What are reserved fields?
- What is asynchronous gRPC?
- What are server interceptors?
- What are client interceptors?
- How do retries work?
- What is flow control?
- What is message compression?
- How are large messages handled?
- How do you debug a gRPC application?
- What happens if a client disconnects during streaming?
- What causes `DEADLINE_EXCEEDED`?
- What causes `UNAVAILABLE`?
- How does gRPC communicate through NGINX?
- How does Docker networking affect gRPC?
- How would you deploy a Python gRPC application?

---

# Best Practices

- Explain concepts using production examples.
- Demonstrate understanding of the complete request lifecycle.
- Discuss trade-offs instead of memorizing definitions.
- Mention HTTP/2 features when discussing performance.
- Explain why a feature exists, not just what it does.
- Relate answers to real backend systems whenever possible.

---

# Common Mistakes

- Confusing metadata with Protocol Buffer messages.
- Assuming REST and gRPC use identical communication models.
- Forgetting that HTTP/2 is mandatory for gRPC.
- Editing generated Protocol Buffer files manually.
- Confusing deadlines with retries.
- Believing Reflection is required in production.
- Ignoring streaming use cases.

---

# Key Takeaways

- Intermediate interviews focus on practical implementation rather than basic definitions.
- Candidates should understand the full gRPC request lifecycle, Protocol Buffer code generation, metadata, interceptors, deadlines, streaming, and error handling.
- Interviewers expect familiarity with debugging tools such as grpcurl and an understanding of how gRPC behaves in real production environments.
- Providing architecture diagrams, practical examples, and implementation trade-offs demonstrates hands-on experience and significantly strengthens interview performance.