# HTTP/2 Fundamentals

# Introduction

HTTP/2 is the underlying transport protocol used by gRPC.

Unlike traditional REST APIs, which commonly use HTTP/1.1, gRPC leverages HTTP/2 to provide high-performance, low-latency communication between distributed applications.

HTTP/2 is not a replacement for HTTP—it is a newer version of the same protocol with significant performance improvements.

---

# Why Does gRPC Use HTTP/2?

HTTP/1.1 works well for web applications but has limitations for modern distributed systems.

Some of these limitations include:

- Multiple TCP connections are often required.
- Requests can block each other.
- Headers are repeatedly transmitted.
- Communication is primarily request-response.

HTTP/2 addresses these limitations by introducing:

- Binary communication
- Multiplexing
- Header compression
- Stream prioritization
- Flow control
- Long-lived connections

These features make HTTP/2 an excellent choice for microservices.

---

# HTTP/1.1 vs HTTP/2

| Feature | HTTP/1.1 | HTTP/2 |
|----------|----------|---------|
| Data Format | Text | Binary |
| TCP Connections | Multiple | Usually One |
| Multiplexing | No | Yes |
| Header Compression | No | Yes |
| Streaming | Limited | Native |
| Performance | Good | Excellent |
| Latency | Higher | Lower |

---

# Single TCP Connection

One of the biggest improvements in HTTP/2 is that multiple requests and responses can share a single TCP connection.

Instead of creating a new connection for every request, HTTP/2 keeps one connection open and sends multiple messages through it.

```text
Client
   │
   ├───────────────┐
   │               │
Request A      Request B
   │               │
   └──── One TCP Connection ───► Server
```

Benefits:

- Fewer connection handshakes
- Reduced latency
- Better resource utilization

---

# Binary Protocol

HTTP/1.1 sends text-based messages.

Example:

```http
GET /employees HTTP/1.1
Host: api.company.com
```

HTTP/2 converts all communication into binary frames.

Advantages:

- Faster parsing
- Smaller payloads
- Lower CPU usage
- Less network overhead

This binary format is one reason why gRPC performs better than REST APIs using JSON.

---

# Streams

A **stream** is an independent sequence of messages exchanged between a client and a server over a single connection.

Each RPC call in gRPC is mapped to its own HTTP/2 stream.

```text
Connection

├── Stream 1
├── Stream 2
├── Stream 3
└── Stream 4
```

Each stream operates independently.

---

# Multiplexing

Multiplexing allows multiple streams to be active simultaneously over a single TCP connection.

```text
Client
    │
    ├── Stream 1 ─────────►
    ├── Stream 2 ─────────►
    ├── Stream 3 ─────────►
    └── Stream 4 ─────────►
Server
```

Without multiplexing, requests must often wait for earlier requests to complete.

With multiplexing:

- Multiple requests are processed concurrently.
- No need for multiple TCP connections.
- Better throughput.
- Lower latency.

This feature is one of the primary reasons gRPC is highly efficient.

---

# Header Compression (HPACK)

HTTP requests often contain repetitive headers.

Example:

```text
Authorization
Content-Type
Accept
User-Agent
```

Sending these headers repeatedly wastes bandwidth.

HTTP/2 uses **HPACK**, a compression mechanism that reduces the size of repeated headers.

Benefits:

- Smaller request size
- Lower bandwidth usage
- Faster communication

---

# Flow Control

Flow control prevents one side of the connection from overwhelming the other with data.

If the receiver cannot process data quickly enough, HTTP/2 automatically regulates the transmission rate.

Benefits:

- Prevents buffer overflow
- Improves stability
- Optimizes network performance
- Supports efficient streaming

---

# Server Push

HTTP/2 introduced Server Push, allowing a server to proactively send resources before the client explicitly requests them.

Example:

A browser requests:

```text
index.html
```

The server may also send:

- style.css
- app.js
- logo.png

without waiting for additional requests.

Although Server Push is part of HTTP/2, **gRPC generally does not rely on it**. Instead, gRPC provides its own powerful streaming mechanisms.

---

# Long-Lived Connections

HTTP/2 is designed to maintain persistent connections.

Instead of opening and closing a connection for every request:

```text
Connect

↓

Send Request

↓

Receive Response

↓

Keep Connection Open

↓

Send Next Request

↓

Receive Response
```

Benefits:

- Lower latency
- Reduced connection overhead
- Better performance for microservices

---

# How HTTP/2 Improves gRPC

HTTP/2 enables gRPC to provide:

- Faster communication
- Lower bandwidth consumption
- Native streaming
- Better scalability
- Reduced latency
- Efficient connection reuse
- High throughput

Without HTTP/2, many of gRPC's advanced features would not be possible.

---

# Key Takeaways

- gRPC uses HTTP/2 as its transport protocol.
- HTTP/2 communicates using binary frames instead of plain text.
- Multiple RPC calls can share a single TCP connection.
- Multiplexing allows concurrent communication over one connection.
- HPACK compresses repeated HTTP headers to reduce bandwidth usage.
- Flow control prevents fast senders from overwhelming slower receivers.
- HTTP/2 supports long-lived persistent connections.
- These capabilities make HTTP/2 an ideal transport protocol for high-performance gRPC applications.