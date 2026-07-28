# Overview

A **Unary RPC** is the simplest and most commonly used communication pattern in gRPC. It follows the traditional **request-response** model, where a client sends a single request to the server and receives exactly one response.

If you have previously worked with REST APIs, a Unary RPC behaves very similarly to a REST endpoint. The primary difference is that instead of exchanging JSON over HTTP, gRPC exchanges Protocol Buffer messages over HTTP/2.

Most CRUD operations—such as creating a user, retrieving an employee, updating a profile, or deleting a record—can be implemented using Unary RPCs.

This chapter explains how Unary RPCs work, how they are defined in Protocol Buffers, how they are implemented in Python, and the best practices for building production-ready Unary gRPC services.

---

# What is a Unary RPC?

A Unary RPC consists of:

- One request
- One response

Communication flow:

```text
Client

    │

    │  One Request

    ▼

Server

    │

    │  One Response

    ▼

Client
```

The communication ends once the response is returned.

---

# Unary RPC Characteristics

A Unary RPC has the following characteristics:

- Single request
- Single response
- Synchronous communication model
- Easy to implement
- Ideal for CRUD operations
- Similar to traditional REST APIs

Because of its simplicity, Unary RPC is the most widely used RPC type.

---

# Unary RPC Definition

A Unary RPC is defined inside a service.

Example:

```proto
syntax = "proto3";

package employee;

service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

}

message EmployeeRequest {

    int32 id = 1;

}

message EmployeeResponse {

    int32 id = 1;

    string name = 2;

    string department = 3;

}
```

Notice that the RPC accepts one request message and returns one response message.

---

# Understanding the RPC Definition

Consider:

```proto
rpc GetEmployee(EmployeeRequest)
    returns (EmployeeResponse);
```

Breaking it down:

| Component | Description |
|-----------|-------------|
| GetEmployee | RPC method name |
| EmployeeRequest | Request message |
| EmployeeResponse | Response message |

This definition becomes the contract between the client and server.

---

# Communication Lifecycle

A Unary RPC follows a straightforward sequence.

```text
Client

        │

        ▼

Create Request

        │

        ▼

Serialize Request

        │

        ▼

Send over HTTP/2

        │

        ▼

Server Receives Request

        │

        ▼

Business Logic

        │

        ▼

Create Response

        │

        ▼

Serialize Response

        │

        ▼

Return Response

        │

        ▼

Client Receives Response
```

All serialization and network communication are handled automatically by gRPC.

---

# Generated Python Classes

Given the previous `.proto` file, Python generates:

```text
employee_pb2.py

employee_pb2_grpc.py
```

Important generated classes include:

```text
EmployeeRequest

EmployeeResponse

EmployeeServiceStub

EmployeeServiceServicer
```

These classes are used by both the client and the server.

---

# Implementing the Server

The server implementation extends the generated service base class.

```python
import employee_pb2
import employee_pb2_grpc


class EmployeeService(employee_pb2_grpc.EmployeeServiceServicer):

    def GetEmployee(self, request, context):

        return employee_pb2.EmployeeResponse(
            id=request.id,
            name="Alice",
            department="Engineering"
        )
```

The server receives an `EmployeeRequest` object and returns an `EmployeeResponse` object.

---

# Registering the Service

The service must be registered with the gRPC server.

```python
employee_pb2_grpc.add_EmployeeServiceServicer_to_server(
    EmployeeService(),
    server
)
```

Without registration, incoming requests cannot be routed to the service implementation.

---

# Starting the Server

A basic server typically follows this sequence.

```text
Create Server

        │

Register Services

        │

Bind Address

        │

Start Server

        │

Wait for Requests
```

Once started, the server listens for incoming Unary RPC calls.

---

# Implementing the Client

The client creates a channel and a stub.

```python
import grpc

import employee_pb2
import employee_pb2_grpc


channel = grpc.insecure_channel("localhost:50051")

stub = employee_pb2_grpc.EmployeeServiceStub(channel)
```

The stub acts as a local proxy for the remote service.

---

# Sending a Request

Create the request.

```python
request = employee_pb2.EmployeeRequest(id=1)
```

Invoke the RPC.

```python
response = stub.GetEmployee(request)
```

Although the service executes remotely, it appears as a normal Python method call.

---

# Reading the Response

The returned object contains the response message.

```python
print(response.id)

print(response.name)

print(response.department)
```

Output:

```text
1

Alice

Engineering
```

The client never needs to parse Protocol Buffers manually.

---

# Unary RPC Flow

Complete communication:

```text
Client

        │

EmployeeRequest

        │

──────────────►

        │

Server

        │

Business Logic

        │

EmployeeResponse

        │

◄──────────────

        │

Client
```

Exactly one request and one response are exchanged.

---

# Error Handling

If an error occurs, the server returns a gRPC status code instead of a normal response.

Example:

```text
Client

        │

Employee ID = 999

        │

────────────►

        │

Server

        │

Employee Not Found

        │

NOT_FOUND

        │

◄────────────
```

The client receives an exception rather than a successful response.

Common status codes include:

- OK
- INVALID_ARGUMENT
- NOT_FOUND
- PERMISSION_DENIED
- UNAUTHENTICATED
- INTERNAL
- UNAVAILABLE

Error handling will be covered in more detail in later chapters.

---

# Common Use Cases

Unary RPCs are commonly used for:

- Login
- User registration
- Fetching user details
- Creating resources
- Updating records
- Deleting records
- Authentication
- Authorization
- Configuration retrieval
- Search requests returning a single response

Most enterprise gRPC services use Unary RPCs for the majority of their endpoints.

---

# Unary RPC vs REST

| Feature | Unary gRPC | REST |
|----------|------------|------|
| Transport | HTTP/2 | HTTP/1.1 or HTTP/2 |
| Payload | Protocol Buffers | JSON |
| Response | One | One |
| Performance | High | Moderate |
| Serialization | Binary | Text |
| Type Safety | Strong | Weaker |

Although both use a request-response model, Unary gRPC provides better performance and stronger contracts through Protocol Buffers.

---

# Advantages of Unary RPC

Unary RPC offers several benefits:

- Simple programming model
- Efficient binary serialization
- Strongly typed APIs
- Automatic code generation
- Low latency
- Easy debugging
- Excellent IDE support
- Suitable for most business operations

It is usually the first RPC type developers learn because it closely resembles traditional API development.

---

# Best Practices

- Keep request and response messages focused.
- Return meaningful gRPC status codes for errors.
- Validate requests before processing.
- Design request and response messages for future extensibility.
- Avoid placing unrelated data in a single RPC.
- Keep business logic separate from transport logic.
- Use Unary RPCs for operations that naturally involve one request and one response.

---

# Common Mistakes

Avoid the following mistakes:

- Returning `None` instead of a valid response message.
- Placing business logic inside generated files.
- Using Unary RPCs for large continuous data transfers.
- Ignoring gRPC status codes and error handling.
- Creating oversized request or response messages.
- Forgetting to register the service with the server.

---

# Key Takeaways

- Unary RPC is the simplest communication pattern in gRPC.
- It consists of one request followed by one response.
- Unary RPCs are ideal for CRUD operations and request-response workflows.
- Python generates client stubs and server base classes from the `.proto` file.
- The client communicates with the server through a generated stub, while the server implements the generated service interface.
- Unary RPCs provide a clean, efficient, and strongly typed alternative to traditional REST APIs.