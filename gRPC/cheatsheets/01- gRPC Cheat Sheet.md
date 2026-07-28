# Overview

This cheat sheet provides a concise reference to the most important gRPC concepts, architecture, communication patterns, status codes, security, and best practices. It is intended for quick revision before interviews, debugging production issues, or refreshing your understanding while developing gRPC applications.

---

# What is gRPC?

- **Full Form:** Google Remote Procedure Call
- **Developed By:** Google
- **Current Status:** Open Source
- **Transport Protocol:** HTTP/2
- **Serialization Format:** Protocol Buffers (Protobuf)
- **Communication Model:** Remote Procedure Call (RPC)

Best suited for:

- Internal Microservices
- Distributed Systems
- Service-to-Service Communication
- High-Performance APIs
- Cloud-Native Applications

---

# gRPC Architecture

```text
        Client
           │
        Stub (Generated)
           │
   Protocol Buffers
           │
        HTTP/2
           │
      Network
           │
      gRPC Server
           │
 Business Logic
           │
   Protocol Buffers
           │
        HTTP/2
           │
        Client
```

---

# Core Components

| Component | Purpose |
|-----------|---------|
| `.proto` File | Defines services and messages |
| Protocol Buffers | Binary serialization format |
| `protoc` | Generates client and server code |
| Stub | Client-side proxy |
| Channel | Communication connection |
| Service | Server implementation |
| Metadata | Request/Response headers |
| Interceptor | Middleware |
| Reflection | Runtime service discovery |

---

# Communication Flow

```text
Client

↓

Stub

↓

Serialize Request

↓

HTTP/2

↓

Server

↓

Business Logic

↓

Serialize Response

↓

HTTP/2

↓

Client
```

---

# Four RPC Types

| RPC Type | Request | Response | Typical Use Case |
|----------|---------|----------|------------------|
| Unary | One | One | CRUD APIs |
| Server Streaming | One | Many | Notifications |
| Client Streaming | Many | One | File Uploads |
| Bidirectional Streaming | Many | Many | Chat Applications |

---

# Unary RPC

```text
Client

↓

Request

↓

Server

↓

Response
```

Examples:

- Get User
- Create Product
- Update Order
- Delete Customer

---

# Server Streaming

```text
Client

↓

Request

↓

Message

↓

Message

↓

Message
```

Examples:

- Notifications
- Live Scores
- Stock Prices
- Event Streams

---

# Client Streaming

```text
Client

↓

Message

↓

Message

↓

Message

↓

Server Response
```

Examples:

- File Upload
- Log Collection
- Sensor Data

---

# Bidirectional Streaming

```text
Client

↓

Message

↑↓

Message

↑↓

Message
```

Examples:

- Chat Systems
- Multiplayer Games
- Live Collaboration
- IoT Devices

---

# Why gRPC is Fast

- Binary serialization
- Protocol Buffers
- HTTP/2
- Multiplexing
- Header compression
- Persistent TCP connections
- Smaller payloads
- Automatic code generation

---

# HTTP/2 Features

- Binary framing
- Multiplexing
- HPACK header compression
- Flow control
- Stream prioritization
- Persistent connections
- Lower latency
- Better bandwidth utilization

---

# Protocol Buffers

Advantages:

- Compact
- Fast
- Strongly typed
- Language independent
- Version friendly
- Code generation

Generated files (Python):

```text
employee_pb2.py

employee_pb2_grpc.py
```

---

# Metadata

Common metadata includes:

```text
authorization

Bearer <JWT>
```

Other examples:

- Request ID
- Correlation ID
- Trace ID
- Tenant ID
- Locale

---

# Interceptors

Common responsibilities:

- Authentication
- Authorization
- Logging
- Metrics
- Distributed Tracing
- Retry Logic
- Rate Limiting

---

# Security

Supported mechanisms:

- TLS
- Mutual TLS (mTLS)
- JWT
- OAuth2
- API Keys
- Metadata Authentication

---

# Common Status Codes

| Status Code | Meaning |
|-------------|---------|
| OK | Success |
| INVALID_ARGUMENT | Invalid request |
| NOT_FOUND | Resource missing |
| ALREADY_EXISTS | Resource already exists |
| UNAUTHENTICATED | Authentication failed |
| PERMISSION_DENIED | Authorization failed |
| DEADLINE_EXCEEDED | Request timed out |
| INTERNAL | Internal server error |
| UNAVAILABLE | Service unavailable |
| RESOURCE_EXHAUSTED | Resource limit exceeded |

---

# Deadlines vs Timeouts

**Timeout**

Maximum duration a client is willing to wait.

```text
Wait 5 seconds
```

**Deadline**

Exact point in time when the request expires.

```text
Current Time

↓

Deadline

↓

Cancel Request
```

---

# Reflection

Reflection allows tools to discover:

- Services
- RPC methods
- Messages

Useful tools:

- grpcurl
- Postman
- BloomRPC
- Evans

---

# Performance Best Practices

✅ Reuse channels.

✅ Keep messages small.

✅ Use streaming when appropriate.

✅ Compress large payloads only.

✅ Set deadlines.

✅ Monitor latency.

✅ Benchmark before optimizing.

---

# Versioning Rules

✅ Add new optional fields.

✅ Reserve removed field numbers.

✅ Never reuse field numbers.

✅ Maintain backward compatibility.

❌ Don't change existing field numbers.

❌ Don't remove fields without reserving them.

---

# Production Checklist

- TLS enabled
- Authentication configured
- Health checks implemented
- Deadlines configured
- Retries configured
- Logging enabled
- Metrics exported
- Tracing enabled
- Reflection disabled (unless required)
- Compression configured
- Load balancing enabled
- Monitoring dashboards available

---

# Common Use Cases

| Application | Recommended RPC |
|-------------|-----------------|
| CRUD API | Unary |
| Notifications | Server Streaming |
| File Upload | Client Streaming |
| Chat | Bidirectional Streaming |
| IoT | Bidirectional Streaming |
| Live Dashboard | Server Streaming |

---

# gRPC vs REST

| REST | gRPC |
|------|------|
| JSON | Protocol Buffers |
| HTTP/1.1 | HTTP/2 |
| Human-readable | Binary |
| Resource-based | RPC-based |
| Browser Friendly | gRPC-Web Required |
| Limited Streaming | Native Streaming |

---

# Common Interview Questions

- What is gRPC?
- Why HTTP/2?
- Why Protocol Buffers?
- Explain the four RPC types.
- What is Metadata?
- What is a Stub?
- What is a Channel?
- What is Reflection?
- What is grpcurl?
- Why is gRPC faster than REST?
- How do you secure gRPC?
- How do you version APIs?
- How do you scale gRPC services?
- How do you debug production issues?

---

# Best Practices

- Use gRPC primarily for internal service-to-service communication.
- Design Protocol Buffer schemas for backward compatibility.
- Configure deadlines and retries thoughtfully.
- Secure communication with TLS and strong authentication.
- Monitor services using logs, metrics, and distributed traces.
- Keep message payloads efficient and avoid unnecessary network calls.
- Choose the appropriate RPC type based on communication requirements.

---

# Common Mistakes

- Treating gRPC as a replacement for every REST API.
- Reusing Protocol Buffer field numbers.
- Forgetting to configure deadlines.
- Enabling Reflection unnecessarily in production.
- Sending excessively large messages.
- Ignoring observability and monitoring.
- Assuming gRPC is always the best choice regardless of context.

---

# Key Takeaways

- gRPC is a high-performance RPC framework built on HTTP/2 and Protocol Buffers.
- It provides efficient, strongly typed, service-to-service communication with native support for streaming.
- Understanding RPC types, Protocol Buffers, HTTP/2, security, and production best practices is essential for building reliable distributed systems.
- This cheat sheet serves as a quick reference for development, production troubleshooting, and interview preparation.