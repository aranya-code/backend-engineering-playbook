# Overview

This document is a last-minute revision guide for gRPC interviews. It summarizes the most important concepts, terminology, architecture, production practices, and common interview questions in a concise format that can be reviewed in 5–10 minutes.

---

# gRPC in One Minute

- Developed by Google
- Open-source RPC framework
- Uses HTTP/2
- Uses Protocol Buffers (Protobuf)
- Supports multiple programming languages
- Strongly typed APIs
- Excellent for microservices
- High-performance communication
- Native streaming support

---

# gRPC Architecture

```text
Client

↓

Client Stub

↓

Protocol Buffers

↓

HTTP/2

↓

Network

↓

gRPC Server

↓

Business Logic

↓

Database
```

Remember:

- Stub is generated automatically.
- HTTP/2 transports messages.
- Protobuf serializes data.
- Business logic resides only on the server.

---

# Why gRPC?

- Faster than REST
- Smaller payloads
- Binary serialization
- Code generation
- Strong contracts
- Built-in streaming
- Multiplexed connections
- Cross-language support

---

# Why is gRPC Faster than REST?

| REST | gRPC |
|------|------|
| JSON | Binary Protobuf |
| HTTP/1.1 | HTTP/2 |
| Larger payloads | Smaller payloads |
| Text parsing | Binary parsing |
| Multiple TCP connections | Multiplexed streams |

Interview answer:

> gRPC achieves higher performance by combining HTTP/2 multiplexing with compact Protocol Buffer serialization, reducing both network overhead and serialization costs.

---

# HTTP/2 Features

Remember these keywords:

- Binary framing
- Multiplexing
- Header compression (HPACK)
- Flow control
- Stream prioritization
- Persistent TCP connection

---

# Protocol Buffers

Remember:

- `.proto` defines APIs.
- `protoc` generates code.
- Binary serialization.
- Language independent.
- Backward compatible.

Generated Python files:

```text
employee_pb2.py

employee_pb2_grpc.py
```

---

# Four RPC Types

## Unary

```text
Client

↓

Server

↓

Response
```

Example:

- Get User

---

## Server Streaming

```text
Client

↓

Server

↓

Item

↓

Item

↓

Item
```

Example:

- Notifications

---

## Client Streaming

```text
Item

↓

Item

↓

Item

↓

Server Response
```

Example:

- File upload

---

## Bidirectional Streaming

```text
Client

↕︎

Server

↕︎

Continuous Messages
```

Example:

- Chat application

---

# gRPC Components

| Component | Purpose |
|-----------|---------|
| Service | RPC definitions |
| Message | Data structure |
| Stub | Client proxy |
| Channel | Connection |
| Metadata | Headers |
| Interceptor | Middleware |
| Reflection | Runtime discovery |

---

# Metadata

Common examples:

```text
Authorization

Bearer JWT
```

Other metadata:

- Correlation ID
- Trace ID
- Tenant ID
- Locale

---

# Interceptors

Used for:

- Authentication
- Authorization
- Logging
- Metrics
- Tracing
- Retry
- Rate limiting

Think:

> Middleware for gRPC

---

# Security

Know these:

- TLS
- mTLS
- JWT
- OAuth2
- API Keys

Production:

Always enable TLS.

---

# Deadlines

Never leave requests unlimited.

Always configure deadlines.

Benefits:

- Prevent hanging requests
- Improve resiliency
- Reduce cascading failures

---

# Reflection

Allows tools to discover:

- Services
- Methods
- Messages

Useful tools:

- grpcurl
- Postman
- Evans

Production:

Usually disable Reflection unless operationally required.

---

# Common Status Codes

| Code | Meaning |
|------|---------|
| OK | Success |
| INVALID_ARGUMENT | Bad request |
| NOT_FOUND | Missing resource |
| UNAUTHENTICATED | Invalid credentials |
| PERMISSION_DENIED | Access denied |
| DEADLINE_EXCEEDED | Timeout |
| RESOURCE_EXHAUSTED | Rate limit/resource exhaustion |
| INTERNAL | Server error |
| UNAVAILABLE | Service unavailable |

---

# Safe Versioning Rules

✅ Add fields

✅ Reserve deleted fields

✅ Add new RPC methods

✅ Maintain backward compatibility

Never:

❌ Change field numbers

❌ Reuse field numbers

---

# Production Best Practices

- Reuse channels.
- Enable TLS.
- Configure deadlines.
- Use retries carefully.
- Implement health checks.
- Enable observability.
- Use distributed tracing.
- Monitor latency.
- Monitor error rates.
- Keep payloads small.

---

# When to Use gRPC

Choose gRPC for:

- Internal APIs
- Microservices
- Cloud-native systems
- Real-time communication
- Streaming workloads
- High-throughput services

---

# When REST is Better

Choose REST for:

- Public APIs
- Browser applications
- Third-party integrations
- Human-readable APIs
- Simple CRUD systems

---

# Frequently Asked Interview Questions

## Beginner

- What is gRPC?
- What is RPC?
- Why use Protocol Buffers?
- Why HTTP/2?
- What is a Stub?
- What is a Channel?

---

## Intermediate

- Explain all four RPC types.
- What is Metadata?
- What are Interceptors?
- Explain Reflection.
- How do deadlines work?
- How does streaming work?

---

## Senior

- How would you migrate REST to gRPC?
- How do you version APIs?
- How do you secure gRPC?
- How do you load balance gRPC?
- How do you troubleshoot latency?
- How do you observe gRPC services?
- When would you choose REST over gRPC?

---

# Common Production Problems

| Problem | Likely Cause |
|---------|--------------|
| Deadline exceeded | Slow dependency |
| Unavailable | Service outage |
| Internal | Application bug |
| Unauthenticated | Invalid JWT |
| Permission denied | Authorization failure |
| Connection refused | Server not running |
| Proto mismatch | Version incompatibility |

---

# One-Line Definitions

| Term | Definition |
|------|------------|
| RPC | Remote Procedure Call |
| Stub | Client proxy generated from `.proto` |
| Channel | Connection between client and server |
| Protobuf | Binary serialization format |
| Metadata | Request/response headers |
| Reflection | Runtime API discovery |
| Interceptor | Middleware for RPC calls |
| Deadline | Maximum time allowed for an RPC |
| Streaming | Sending multiple messages in one RPC |

---

# 60-Second Revision

Remember these keywords:

- Google
- HTTP/2
- Protocol Buffers
- Binary
- Multiplexing
- Streaming
- Stub
- Channel
- Metadata
- Interceptor
- Reflection
- TLS
- Deadlines
- Health Checks
- Load Balancing
- Service Discovery
- Observability
- Retries
- Versioning
- Backward Compatibility

---

# Best Practices

- Understand the complete request lifecycle from client stub to server response.
- Be prepared to explain trade-offs between gRPC and REST rather than simply listing advantages.
- Relate concepts such as streaming, deadlines, retries, and security to real production scenarios.
- Use precise terminology when discussing Protocol Buffers, HTTP/2, and RPC communication.
- Support interview answers with practical examples from distributed systems and microservices.

---

# Common Mistakes

- Claiming that gRPC should replace every REST API.
- Confusing deadlines with retries or timeouts.
- Assuming HTTP/2 alone is responsible for gRPC's performance.
- Forgetting the importance of backward-compatible schema evolution.
- Ignoring production concerns such as observability, authentication, and service resilience.

---

# Key Takeaways

- gRPC combines HTTP/2, Protocol Buffers, and RPC semantics to provide fast, strongly typed service-to-service communication.
- Mastering the core concepts, production practices, and trade-offs is more important than memorizing definitions.
- This revision guide serves as a rapid refresher before interviews, helping you recall the most important topics and confidently discuss real-world gRPC systems.