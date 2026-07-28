# What is gRPC?

# What is gRPC?

**gRPC (Google Remote Procedure Call)** is a high-performance, open-source Remote Procedure Call (RPC) framework developed by Google.

It allows applications running on different machines—or even written in different programming languages—to communicate with each other as if they were calling a local function.

Instead of manually creating HTTP requests and parsing JSON responses, developers simply call a method, and gRPC handles the communication behind the scenes.

---

# Official Definition

> gRPC is a modern, open-source, high-performance RPC framework that can run in any environment. It enables efficient communication between distributed applications using HTTP/2 and Protocol Buffers.

---

# What Problem Does gRPC Solve?

Imagine you have two microservices.

- User Service
- Order Service

The User Service needs customer information from the Order Service.

### Without gRPC

The User Service must:

1. Create an HTTP request.
2. Convert data into JSON.
3. Send the request over the network.
4. Wait for the response.
5. Parse the JSON response.
6. Handle HTTP errors.

This requires a lot of boilerplate code.

---

### With gRPC

The User Service simply calls a method.

```python
order = order_client.GetOrder(request)
```

It looks like a normal Python function call.

gRPC automatically:

- Serializes the request
- Sends it over the network
- Receives the response
- Deserializes the response
- Returns the result

The networking details are hidden from the developer.

---

# What is an RPC?

RPC stands for **Remote Procedure Call**.

It allows a program to execute a function on another computer as though it were a local function.

Instead of writing:

```
Send HTTP Request
Receive JSON
Parse JSON
```

You simply write:

```python
customer = client.GetCustomer(request)
```

The actual function executes on another server.

---

# Real-World Example

Imagine using an ATM.

You press:

```
Withdraw ₹5,000
```

You do **not** care:

- Which bank server processed the request
- Which database was queried
- Which network protocol was used

You simply call a service and receive the result.

gRPC works in the same way.

---

# Why Was gRPC Created?

As systems evolved into microservices, traditional REST APIs began to show limitations.

Large-scale distributed systems require:

- Faster communication
- Lower network usage
- Better performance
- Multiple programming language support
- Streaming support
- Strongly typed contracts

Google developed gRPC to address these requirements.

---

# Key Features of gRPC

- High-performance communication
- Built on HTTP/2
- Uses Protocol Buffers (Protobuf)
- Strongly typed APIs
- Code generation
- Streaming support
- Cross-platform
- Cross-language
- Secure communication with TLS
- Efficient binary serialization

---

# How gRPC Works

```
Client

    │
    │ Calls a remote method
    ▼

Generated Client Stub

    │
    │ Serializes request
    ▼

HTTP/2

    │
    ▼

Generated Server Stub

    │
    │ Deserializes request
    ▼

Server Implementation

    │
    ▼

Business Logic

    │
    ▼

Database / Cache / Other Services
```

The client never directly communicates with the server implementation.

Instead, generated client and server stubs handle the communication automatically.

---

# REST vs gRPC (High-Level)

| Feature | REST | gRPC |
|---------|------|------|
| Protocol | HTTP/1.1 (commonly) | HTTP/2 |
| Data Format | JSON | Protocol Buffers |
| Performance | Good | Excellent |
| Payload Size | Larger | Smaller |
| Streaming | Limited | Native |
| Code Generation | No | Yes |
| Strong Typing | No | Yes |
| Browser Friendly | Excellent | Limited (requires gRPC-Web for browsers) |

---

# Common Use Cases

gRPC is commonly used for:

- Microservices communication
- Backend-to-backend APIs
- Internal enterprise systems
- Real-time messaging
- Chat applications
- Machine learning inference
- Financial systems
- IoT platforms
- Distributed systems
- Cloud-native applications

---

# Advantages of gRPC

- Very fast communication
- Compact binary payloads
- Lower bandwidth usage
- Strong API contracts
- Automatic client/server code generation
- Excellent scalability
- Supports streaming
- Multiple language support
- Built-in authentication support
- Works well with Kubernetes and microservices

---

# Limitations of gRPC

- Not human-readable (binary data)
- Harder to debug than JSON APIs
- Browser support requires gRPC-Web
- Less suitable for public APIs compared to REST
- Learning Protocol Buffers adds some complexity

---

# Where is gRPC Used?

Many large technology companies use gRPC for internal service communication.

Examples include:

- Google
- Netflix
- Square
- Cisco
- Dropbox
- Cloud-native applications running on Kubernetes

---

# Key Takeaways

- gRPC is an RPC framework developed by Google.
- It enables applications to communicate by calling remote methods as if they were local functions.
- It uses HTTP/2 for transport.
- It uses Protocol Buffers for efficient binary serialization.
- It is significantly faster than traditional REST APIs for service-to-service communication.
- It is widely used in microservices and distributed systems.
- gRPC provides automatic code generation, strong typing, and built-in streaming support.

---

