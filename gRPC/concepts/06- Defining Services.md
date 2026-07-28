# Defining Services

# What is a Service?

A **service** defines the operations that a gRPC server provides to its clients.

Think of a service as a collection of related remote functions.

For example, an Employee Management System may provide operations such as:

- Get Employee
- Create Employee
- Update Employee
- Delete Employee

Instead of exposing HTTP endpoints, gRPC exposes **RPC methods** inside a service.

---

# Service Definition

A service is defined using the `service` keyword.

Example:

```proto
service EmployeeService {

}
```

This creates a service named **EmployeeService**.

At this stage, the service doesn't perform any operations because no RPC methods have been defined.

---

# What is an RPC Method?

An **RPC (Remote Procedure Call)** method is a function that can be called remotely by a client.

It behaves like a normal function call, even though it executes on another machine.

Example:

```python
employee = client.GetEmployee(request)
```

Although it appears to be a local function call, the request is actually sent over the network to a remote server.

---

# Defining an RPC Method

RPC methods are declared using the `rpc` keyword.

Example:

```proto
service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

}
```

This defines a remote function named **GetEmployee**.

---

# Understanding the Syntax

Consider the following example:

```proto
service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

}
```

Let's break it down.

| Part | Description |
|------|-------------|
| `service` | Declares a service |
| `EmployeeService` | Name of the service |
| `rpc` | Declares a remote method |
| `GetEmployee` | Method name |
| `EmployeeRequest` | Request message |
| `EmployeeResponse` | Response message |
| `returns` | Specifies the response type |

---

# Request Message

Every RPC method receives a request message.

Example:

```proto
message EmployeeRequest {

    int32 id = 1;

}
```

The client sends this message to the server.

Example:

```text
Request

Employee ID = 101
```

The server receives the request and processes it.

---

# Response Message

After processing the request, the server returns a response message.

Example:

```proto
message EmployeeResponse {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

The client receives this message as the result of the RPC call.

---

# Complete Example

```proto
syntax = "proto3";

package employee;

message EmployeeRequest {

    int32 id = 1;

}

message EmployeeResponse {

    int32 id = 1;

    string name = 2;

    string email = 3;

}

service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

}
```

This `.proto` file defines:

- Two messages
- One service
- One RPC method

---

# How the Client Uses a Service

After generating code with `protoc`, the client interacts with the service through a generated stub.

Example:

```python
response = stub.GetEmployee(request)
```

The developer writes only one line of code.

Behind the scenes, gRPC:

- Serializes the request
- Sends it over HTTP/2
- Invokes the server
- Receives the response
- Deserializes the response
- Returns the final object

---

# How the Server Uses a Service

The server implements the methods defined in the `.proto` file.

Example:

```python
class EmployeeService(EmployeeServiceServicer):

    def GetEmployee(self, request, context):

        return EmployeeResponse(
            id=1,
            name="Alice",
            email="alice@example.com"
        )
```

The server only implements the business logic.

gRPC automatically handles:

- Networking
- Serialization
- Deserialization
- Request routing
- Response transmission

---

# Multiple RPC Methods

A service can expose multiple remote methods.

Example:

```proto
service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

    rpc CreateEmployee(CreateEmployeeRequest)
        returns (EmployeeResponse);

    rpc UpdateEmployee(UpdateEmployeeRequest)
        returns (EmployeeResponse);

    rpc DeleteEmployee(DeleteEmployeeRequest)
        returns (DeleteEmployeeResponse);

}
```

Grouping related operations into a single service improves organization and maintainability.

---

# Service as an API Contract

The `.proto` file acts as a contract between the client and the server.

Both sides generate code from the same service definition.

```text
          employee.proto

        ┌──────────────┐
        │ Service      │
        │ Messages     │
        │ RPC Methods  │
        └──────────────┘
              │
              │
      ┌───────┴────────┐
      ▼                ▼

 Client Code      Server Code
 (Generated)      (Generated)
```

Because both sides use the same contract:

- Method names remain consistent.
- Message structures remain identical.
- Type mismatches are eliminated.
- Integration becomes much simpler.

---

# Best Practices

When designing services:

- Group related RPC methods together.
- Use descriptive service names.
- Use clear and consistent method names.
- Keep each RPC focused on a single responsibility.
- Reuse request and response messages whenever appropriate.
- Avoid creating overly large services with unrelated operations.

---

# Real-World Example

An e-commerce application might define several services.

```text
UserService

ProductService

OrderService

PaymentService

InventoryService
```

Each service is responsible for a specific business domain.

This aligns well with a microservices architecture, where each service owns its own data and business logic.

---

# Common Mistakes

Avoid the following mistakes:

- Putting unrelated RPC methods into the same service.
- Using vague method names such as `DoWork` or `Execute`.
- Creating one service for the entire application.
- Returning overly complex response messages.
- Breaking backward compatibility by changing existing RPC definitions.

---

# Key Takeaways

- A service defines the operations that a gRPC server exposes to clients.
- Services are declared using the `service` keyword.
- Remote functions are declared using the `rpc` keyword.
- Every RPC method accepts a request message and returns a response message.
- The `.proto` file acts as the contract between clients and servers.
- gRPC generates client stubs and server interfaces directly from the service definition.
- The server implements business logic, while gRPC handles networking and message serialization automatically.