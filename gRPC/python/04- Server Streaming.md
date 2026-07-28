# Overview

While Unary RPC is ideal for request-response communication, many real-world applications require a server to send **multiple pieces of data** in response to a single client request.

For example:

- Streaming live stock prices
- Sending application logs
- Returning thousands of database records
- Streaming chat history
- Monitoring server metrics
- Delivering video or audio chunks

Sending all this data as one large response is inefficient because the client must wait until the server finishes preparing the entire dataset.

To solve this problem, gRPC provides **Server Streaming RPC**.

In a Server Streaming RPC, the client sends **one request**, and the server responds with **a stream of multiple messages**. The client processes each message as soon as it arrives, reducing latency and memory usage while providing a smoother user experience.

This chapter explains how Server Streaming works, how it is implemented in Python, and when it should be used in production applications.

---

# What is Server Streaming?

Server Streaming is an RPC pattern where:

- The client sends **one request**.
- The server sends **zero or more responses**.
- The server decides when the stream ends.

Communication flow:

```text
Client

      │

One Request

      ▼

Server

      │

Response 1

      ▼

Response 2

      ▼

Response 3

      ▼

...

      ▼

Response N

      ▼

Stream Ends
```

Unlike Unary RPC, multiple responses are returned over a single connection.

---

# When Should You Use Server Streaming?

Server Streaming is useful whenever the server needs to return a sequence of data instead of a single object.

Common examples include:

- Live dashboards
- Stock market feeds
- Weather updates
- Log streaming
- Database exports
- File downloads
- Sensor monitoring
- Analytics reports
- Event notifications

Instead of waiting for all results, the client receives data continuously.

---

# Server Streaming Definition

A Server Streaming RPC is declared using the `stream` keyword before the response type.

Example:

```proto
syntax = "proto3";

package employee;

service EmployeeService {

    rpc ListEmployees(EmployeeRequest)
        returns (stream Employee);

}

message EmployeeRequest {

    string department = 1;

}

message Employee {

    int32 id = 1;

    string name = 2;

}
```

Notice that only the response is marked as a stream.

---

# Understanding the RPC Definition

Consider:

```proto
rpc ListEmployees(EmployeeRequest)
    returns (stream Employee);
```

Breaking it down:

| Component | Description |
|-----------|-------------|
| ListEmployees | RPC method |
| EmployeeRequest | Single request |
| stream Employee | Multiple responses |

The client sends one request, while the server sends multiple `Employee` messages.

---

# Communication Lifecycle

A Server Streaming RPC follows this sequence.

```text
Client

        │

Create Request

        │

────────────►

        │

Server

        │

Process Request

        │

Generate Item

        │

Send Response

        │

Generate Next Item

        │

Send Response

        │

...

        │

Close Stream

        │

◄────────────
```

The client receives data as it becomes available.

---

# Generated Python Classes

Given the previous `.proto` file, Python generates:

```text
employee_pb2.py

employee_pb2_grpc.py
```

The generated classes are similar to those used for Unary RPCs.

The main difference lies in how the server and client handle responses.

---

# Implementing the Server

A Server Streaming RPC returns multiple messages using the Python `yield` statement.

Example:

```python
import employee_pb2
import employee_pb2_grpc


class EmployeeService(employee_pb2_grpc.EmployeeServiceServicer):

    def ListEmployees(self, request, context):

        employees = [
            (1, "Alice"),
            (2, "Bob"),
            (3, "Charlie"),
        ]

        for emp_id, name in employees:

            yield employee_pb2.Employee(
                id=emp_id,
                name=name
            )
```

Instead of returning a single response, the method yields one response at a time.

---

# Why Use `yield`?

Unlike Unary RPCs, Server Streaming produces multiple responses.

```python
yield response
```

Each `yield` immediately sends one message to the client.

```text
Server

↓

Yield Employee 1

↓

Yield Employee 2

↓

Yield Employee 3
```

The stream ends automatically when the function completes.

---

# Registering the Service

Service registration is identical to Unary RPC.

```python
employee_pb2_grpc.add_EmployeeServiceServicer_to_server(
    EmployeeService(),
    server
)
```

No additional configuration is required.

---

# Implementing the Client

The client creates a stub.

```python
channel = grpc.insecure_channel("localhost:50051")

stub = employee_pb2_grpc.EmployeeServiceStub(channel)
```

Create the request.

```python
request = employee_pb2.EmployeeRequest(
    department="Engineering"
)
```

Call the RPC.

```python
responses = stub.ListEmployees(request)
```

Unlike Unary RPCs, the result is an iterator rather than a single object.

---

# Reading the Stream

The client processes each message as it arrives.

```python
for employee in responses:

    print(employee.id)

    print(employee.name)
```

Output:

```text
1 Alice

2 Bob

3 Charlie
```

Each message is received independently.

---

# Streaming Timeline

```text
Client

        │

Request

        │

────────────►

        │

Server

        │

Employee 1

◄────────────

Employee 2

◄────────────

Employee 3

◄────────────

End Stream

◄────────────
```

The connection remains open until all responses are sent.

---

# Server Streaming vs Unary RPC

| Feature | Unary RPC | Server Streaming |
|----------|-----------|------------------|
| Requests | 1 | 1 |
| Responses | 1 | Many |
| Connection | Short-lived | Open until stream ends |
| Response Type | Single message | Stream of messages |
| Typical Use Case | CRUD operations | Continuous or large datasets |

---

# Handling Errors

Errors may occur before or during streaming.

Example:

```text
Client

        │

Request

────────────►

        │

Server

        │

Employee 1

◄────────────

Employee 2

◄────────────

Database Error

        │

INTERNAL

◄────────────
```

The stream terminates immediately when an error occurs.

Clients should handle exceptions while consuming the stream.

---

# Real-World Example

Consider a log monitoring service.

```proto
service LogService {

    rpc StreamLogs(LogRequest)
        returns (stream LogEntry);

}
```

The client sends one request.

```text
Server Name
```

The server continuously returns:

```text
10:01 INFO

10:02 INFO

10:03 WARNING

10:04 ERROR
```

This allows administrators to monitor logs in real time.

---

# Advantages of Server Streaming

Server Streaming offers several benefits.

- Reduced memory usage
- Lower response latency
- Efficient handling of large datasets
- Better user experience
- Continuous delivery of data
- Supports real-time applications
- Eliminates the need for polling

---

# When Should You Avoid Server Streaming?

Server Streaming is not appropriate when:

- Only one response is required.
- The client needs to send multiple requests.
- Bidirectional communication is required.
- Responses must be aggregated before processing.

Unary or Bidirectional Streaming may be better choices in these situations.

---

# Best Practices

- Stream data as soon as it becomes available.
- Keep each streamed message reasonably small.
- Handle client cancellations using the gRPC context.
- Return meaningful status codes when errors occur.
- Avoid loading the entire dataset into memory before streaming.
- Use streaming for large datasets instead of oversized Unary responses.
- Monitor long-running streams for resource usage.

---

# Common Mistakes

Avoid the following mistakes:

- Returning a list instead of yielding individual messages.
- Loading an entire dataset into memory before streaming.
- Forgetting that the client receives an iterator.
- Ignoring client disconnections or cancellations.
- Using Server Streaming for simple request-response operations.
- Sending excessively large individual messages.

---

# Key Takeaways

- Server Streaming allows one client request to receive multiple server responses.
- The `stream` keyword before the response type defines a Server Streaming RPC.
- Python servers implement Server Streaming by yielding response messages.
- Clients consume streamed responses using an iterator.
- Server Streaming is ideal for large datasets, live updates, monitoring systems, and real-time data delivery.
- Streaming reduces latency and memory usage while providing a more responsive communication model.