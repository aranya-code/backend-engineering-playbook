# Overview

While Server Streaming allows a server to send multiple responses for a single client request, there are situations where the opposite is needed—the client needs to send **multiple messages** to the server before receiving a response.

Examples include:

- Uploading a large file in chunks
- Sending batches of sensor data
- Uploading application logs
- Streaming telemetry data
- Batch database inserts
- Sending multiple images for processing

Sending all of this data in a single request can be inefficient or even impossible due to size limitations.

To address this scenario, gRPC provides **Client Streaming RPC**.

In a Client Streaming RPC, the client sends a stream of multiple request messages to the server. Once the client has finished sending all requests, the server processes the complete stream and returns a single response.

This chapter explains how Client Streaming works, how it is implemented in Python, and the scenarios where it provides significant advantages over Unary RPCs.

---

# What is Client Streaming?

Client Streaming is an RPC pattern where:

- The client sends multiple requests.
- The server receives the requests as a stream.
- The server returns one response after processing the entire stream.

Communication flow:

```text
Client

Request 1

      │

Request 2

      │

Request 3

      │

...

      │

Request N

      ▼

Server

      │

One Response

      ▼

Client
```

The connection remains open while the client streams requests.

---

# When Should You Use Client Streaming?

Client Streaming is useful whenever the client generates data gradually or needs to send a large volume of information.

Common examples include:

- File uploads
- Video uploads
- Audio uploads
- IoT sensor readings
- Log aggregation
- Bulk record insertion
- Data synchronization
- Batch analytics

Instead of sending one massive request, data is transmitted incrementally.

---

# Client Streaming Definition

A Client Streaming RPC is declared using the `stream` keyword before the request type.

Example:

```proto
syntax = "proto3";

package employee;

service EmployeeService {

    rpc UploadEmployees(stream Employee)
        returns (UploadSummary);

}

message Employee {

    int32 id = 1;

    string name = 2;

}

message UploadSummary {

    int32 total = 1;

}
```

Notice that only the request is marked as a stream.

---

# Understanding the RPC Definition

Consider:

```proto
rpc UploadEmployees(stream Employee)
    returns (UploadSummary);
```

Breaking it down:

| Component | Description |
|-----------|-------------|
| UploadEmployees | RPC method |
| stream Employee | Multiple requests |
| UploadSummary | Single response |

The client streams many `Employee` messages, and the server returns one summary.

---

# Communication Lifecycle

A Client Streaming RPC follows this sequence.

```text
Client

        │

Employee 1

────────────►

Employee 2

────────────►

Employee 3

────────────►

...

Employee N

────────────►

        │

Stream Ends

────────────►

        │

Server Processes Data

        │

One Response

◄────────────
```

The server waits until the client finishes sending messages before responding.

---

# Generated Python Classes

Python generates the same files as other RPC types.

```text
employee_pb2.py

employee_pb2_grpc.py
```

The difference lies in how the server processes incoming requests.

---

# Implementing the Server

The server receives an iterator containing all incoming requests.

```python
import employee_pb2
import employee_pb2_grpc


class EmployeeService(employee_pb2_grpc.EmployeeServiceServicer):

    def UploadEmployees(self, request_iterator, context):

        total = 0

        for employee in request_iterator:

            print(employee.name)

            total += 1

        return employee_pb2.UploadSummary(
            total=total
        )
```

The server processes each incoming message one at a time.

---

# Understanding `request_iterator`

Unlike Unary RPCs, the server does not receive a single request object.

Instead, it receives an iterator.

```python
for employee in request_iterator:

    ...
```

Each iteration retrieves the next streamed message from the client.

This allows the server to process data without loading the entire stream into memory.

---

# Registering the Service

Service registration remains unchanged.

```python
employee_pb2_grpc.add_EmployeeServiceServicer_to_server(
    EmployeeService(),
    server
)
```

---

# Implementing the Client

The client generates a stream of request messages.

```python
def employee_generator():

    employees = [

        (1, "Alice"),

        (2, "Bob"),

        (3, "Charlie")

    ]

    for emp_id, name in employees:

        yield employee_pb2.Employee(
            id=emp_id,
            name=name
        )
```

The generator produces one message at a time.

---

# Sending the Stream

Create the stub.

```python
channel = grpc.insecure_channel("localhost:50051")

stub = employee_pb2_grpc.EmployeeServiceStub(channel)
```

Send the stream.

```python
response = stub.UploadEmployees(
    employee_generator()
)
```

The client streams each generated message to the server.

---

# Receiving the Response

After all requests have been sent, the server returns a single response.

```python
print(response.total)
```

Example output:

```text
3
```

The response is received only after the client completes the stream.

---

# Streaming Timeline

```text
Client

Employee 1

────────────►

Employee 2

────────────►

Employee 3

────────────►

End Stream

────────────►

        │

Server

        │

Process Data

        │

Summary

◄────────────
```

The server waits until the client finishes streaming before responding.

---

# Client Streaming vs Unary RPC

| Feature | Unary RPC | Client Streaming |
|----------|-----------|------------------|
| Requests | 1 | Many |
| Responses | 1 | 1 |
| Request Type | Single message | Stream |
| Response Type | Single message | Single message |
| Typical Use Case | CRUD operations | Uploads and batch processing |

---

# Handling Errors

Errors can occur while the client is still streaming.

Example:

```text
Client

Employee 1

────────────►

Employee 2

────────────►

Invalid Record

────────────►

        │

Server

        │

INVALID_ARGUMENT

◄────────────
```

When an unrecoverable error occurs, the stream is terminated and the client receives a gRPC error.

Applications should handle these exceptions appropriately.

---

# Real-World Example

Consider a file upload service.

```proto
service FileService {

    rpc Upload(stream FileChunk)
        returns (UploadResult);

}
```

Each request contains one chunk of the file.

```text
Chunk 1

Chunk 2

Chunk 3

...

Chunk N
```

After the last chunk is received, the server reconstructs the file and returns the upload status.

This approach avoids transmitting very large payloads in a single request.

---

# Advantages of Client Streaming

Client Streaming offers several benefits.

- Efficient large data uploads
- Reduced memory consumption
- Continuous request transmission
- Better scalability
- Lower network overhead
- Suitable for batch operations
- Supports incremental processing

---

# When Should You Avoid Client Streaming?

Client Streaming may not be appropriate when:

- Only one request is required.
- The server must continuously send updates.
- Both client and server need simultaneous communication.
- Immediate responses are required after every request.

Unary, Server Streaming, or Bidirectional Streaming may be more appropriate in these cases.

---

# Best Practices

- Stream data in manageable chunks.
- Validate each incoming message.
- Avoid buffering the entire stream in memory.
- Handle client cancellations gracefully.
- Return meaningful status codes for failures.
- Design request messages to be small and focused.
- Use generators to produce streamed requests efficiently.

---

# Common Mistakes

Avoid the following mistakes:

- Reading the entire stream into memory before processing.
- Forgetting to iterate over `request_iterator`.
- Sending oversized request messages.
- Returning responses before processing the complete stream.
- Ignoring client disconnections.
- Using Client Streaming for simple request-response operations.

---

# Key Takeaways

- Client Streaming allows multiple client requests followed by a single server response.
- The `stream` keyword before the request type defines a Client Streaming RPC.
- Python servers receive streamed requests through an iterator.
- Clients commonly use generators to stream request messages efficiently.
- Client Streaming is ideal for uploads, batch processing, telemetry, and large data transfers.
- Processing streamed requests incrementally improves scalability and reduces memory usage.