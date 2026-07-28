# RPC Types


# Introduction

Unlike traditional REST APIs, which primarily follow a request-response model, gRPC supports multiple communication patterns.

gRPC provides **four types of Remote Procedure Calls (RPCs)**:

1. Unary RPC
2. Server Streaming RPC
3. Client Streaming RPC
4. Bidirectional Streaming RPC

Each type is designed for a different communication scenario.

---

# Overview of RPC Types

| RPC Type | Client Sends | Server Sends | Streaming |
|----------|--------------|--------------|------------|
| Unary RPC | One Request | One Response | No |
| Server Streaming RPC | One Request | Multiple Responses | Server |
| Client Streaming RPC | Multiple Requests | One Response | Client |
| Bidirectional Streaming RPC | Multiple Requests | Multiple Responses | Both |

---

# 1. Unary RPC

Unary RPC is the simplest and most common type of RPC.

The client sends one request, and the server returns one response.

```text
Client
   │
   │ Request
   ▼
Server
   │
   │ Response
   ▼
Client
```

Example:

```proto
rpc GetEmployee(EmployeeRequest)
    returns (EmployeeResponse);
```

Client:

```python
response = stub.GetEmployee(request)
```

This communication pattern is very similar to a REST API.

---

# When to Use Unary RPC

Unary RPC is suitable when:

- Fetching a user
- Creating an order
- Updating a record
- Deleting data
- Authentication
- Payment processing

In most business applications, Unary RPC is the most frequently used communication pattern.

---

# Advantages of Unary RPC

- Simple to implement
- Easy to understand
- Low complexity
- Ideal for request-response operations
- Similar to REST APIs

---

# 2. Server Streaming RPC

In Server Streaming RPC, the client sends a single request, but the server returns multiple responses over time.

```text
Client
   │
   │ Request
   ▼
Server
   │
   ├── Response 1
   ├── Response 2
   ├── Response 3
   └── Response 4
```

The connection remains open until the server has finished sending all responses.

Example:

```proto
rpc ListEmployees(EmployeeRequest)
    returns (stream EmployeeResponse);
```

Notice the `stream` keyword before the response type.

---

# Client Code

Example:

```python
responses = stub.ListEmployees(request)

for employee in responses:
    print(employee.name)
```

The client processes each response as it arrives.

---

# When to Use Server Streaming

Server Streaming is useful when:

- Downloading large datasets
- Log streaming
- Live notifications
- Stock market updates
- Sensor data
- Video metadata
- Report generation

Instead of waiting for all data to be available, the server streams it continuously.

---

# Advantages of Server Streaming

- Lower memory usage
- Faster response to the client
- Better user experience
- Efficient handling of large datasets

---

# 3. Client Streaming RPC

Client Streaming is the opposite of Server Streaming.

The client sends multiple requests, and the server returns a single response after processing them all.

```text
Client

Request 1
Request 2
Request 3
Request 4
     │
     ▼
Server
     │
Single Response
     ▼
Client
```

Example:

```proto
rpc UploadLogs(stream LogMessage)
    returns (UploadResponse);
```

Here, the request is marked with the `stream` keyword.

---

# Client Code

Example:

```python
response = stub.UploadLogs(log_generator())
```

The client continuously sends log messages.

After all messages have been received, the server returns a single response.

---

# When to Use Client Streaming

Common use cases include:

- File uploads
- Image uploads
- Log collection
- Telemetry data
- IoT sensor readings
- Batch processing

---

# Advantages of Client Streaming

- Efficient for large uploads
- Reduced network overhead
- Lower latency than multiple unary calls
- Better bandwidth utilization

---

# 4. Bidirectional Streaming RPC

Bidirectional Streaming allows both the client and server to send messages independently.

Neither side has to wait for the other.

```text
Client                     Server

Request 1  ───────────────►

             ◄──────────── Response 1

Request 2  ───────────────►

             ◄──────────── Response 2

Request 3  ───────────────►

             ◄──────────── Response 3
```

Both sides can continue sending messages until the stream is closed.

Example:

```proto
rpc Chat(stream ChatMessage)
    returns (stream ChatMessage);
```

Notice that both the request and response use the `stream` keyword.

---

# When to Use Bidirectional Streaming

This communication pattern is ideal for:

- Chat applications
- Multiplayer games
- Live collaboration tools
- Real-time dashboards
- Video conferencing
- Financial trading systems
- Interactive AI applications

---

# Advantages of Bidirectional Streaming

- Full-duplex communication
- Extremely low latency
- Efficient use of network resources
- Supports real-time communication

---

# Understanding the `stream` Keyword

The `stream` keyword determines whether messages are streamed.

Unary RPC:

```proto
rpc GetEmployee(EmployeeRequest)
    returns (EmployeeResponse);
```

Server Streaming:

```proto
rpc ListEmployees(EmployeeRequest)
    returns (stream EmployeeResponse);
```

Client Streaming:

```proto
rpc UploadLogs(stream LogMessage)
    returns (UploadResponse);
```

Bidirectional Streaming:

```proto
rpc Chat(stream ChatMessage)
    returns (stream ChatMessage);
```

The position of the `stream` keyword determines which side streams data.

---

# Choosing the Right RPC Type

| Scenario | Recommended RPC Type |
|----------|----------------------|
| Get a single employee | Unary RPC |
| Download a report | Server Streaming |
| Upload a large file | Client Streaming |
| Chat application | Bidirectional Streaming |
| Live stock prices | Server Streaming |
| Telemetry collection | Client Streaming |
| Real-time collaboration | Bidirectional Streaming |
| Authentication | Unary RPC |

---

# Comparison of RPC Types

| Feature | Unary | Server Streaming | Client Streaming | Bidirectional |
|---------|--------|-----------------|-----------------|---------------|
| Requests | One | One | Many | Many |
| Responses | One | Many | One | Many |
| Streaming | None | Server | Client | Both |
| Complexity | Low | Medium | Medium | High |
| Common Use | CRUD APIs | Notifications | Uploads | Real-time Systems |

---

# Best Practices

When choosing an RPC type:

- Use Unary RPC for standard request-response operations.
- Use Server Streaming when returning large datasets or continuous updates.
- Use Client Streaming when clients need to upload multiple pieces of data.
- Use Bidirectional Streaming only when both client and server need to exchange messages continuously.
- Avoid using streaming unless it provides a clear performance or usability benefit.

---

# Key Takeaways

- gRPC supports four communication patterns: Unary, Server Streaming, Client Streaming, and Bidirectional Streaming.
- Unary RPC is the simplest and most commonly used pattern.
- Server Streaming allows one request to receive multiple responses.
- Client Streaming allows multiple requests to produce a single response.
- Bidirectional Streaming enables both client and server to exchange messages independently over the same connection.
- The `stream` keyword determines whether requests or responses are streamed.
- Choosing the appropriate RPC type improves performance, scalability, and application design.