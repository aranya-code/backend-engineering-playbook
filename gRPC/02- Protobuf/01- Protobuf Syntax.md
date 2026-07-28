# Overview

Every Protocol Buffer schema begins with a **`.proto` file**.

This file defines the structure of your data, the services your application exposes, and the rules that both clients and servers must follow. It acts as the **single source of truth** for communication in a gRPC application.

Before learning advanced features such as enums, maps, or `oneof`, it is essential to understand the basic syntax of a Protocol Buffer file. This chapter introduces the building blocks of a `.proto` file, explains how each component works, and demonstrates how they fit together to create a complete schema.

By mastering Protobuf syntax, you'll be able to design clean, maintainable, and extensible APIs for distributed systems.

---

# What is a `.proto` File?

A **`.proto` file** is a text file that defines:

- Messages
- Services
- RPC methods
- Enumerations
- Packages
- Imports
- Configuration options

Think of it as the **contract** between the client and the server.

Both sides generate source code from the same `.proto` file, ensuring they communicate using the exact same data structures.

---

# Basic Structure of a `.proto` File

A typical Protocol Buffer file consists of several sections.

```proto
syntax = "proto3";

package employee;

message EmployeeRequest {
    int32 id = 1;
}

message EmployeeResponse {
    int32 id = 1;
    string name = 2;
}

service EmployeeService {
    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);
}
```

Although this file is small, it contains every major component of a Protocol Buffer schema.

---

# The `syntax` Declaration

Every `.proto` file should begin with a syntax declaration.

Example:

```proto
syntax = "proto3";
```

This tells the Protocol Buffer compiler which language specification the file follows.

Today, almost all modern gRPC applications use **Proto3**.

Earlier versions used **Proto2**, which included additional features such as required fields and explicit field presence rules.

Unless you're maintaining an older system, you should always use:

```proto
syntax = "proto3";
```

---

# Comments

Comments improve readability and documentation.

Single-line comments:

```proto
// Employee identifier
int32 id = 1;
```

Multi-line comments:

```proto
/*
Employee information
used by HR services.
*/
```

Comments are ignored by the compiler but are invaluable for developers maintaining the schema.

---

# Message Definitions

Messages define the structure of the data exchanged between applications.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

Each message is similar to a class or data model in an object-oriented programming language.

---

# Field Declarations

A field consists of three parts.

```proto
string name = 2;
```

Breaking it down:

| Component | Meaning |
|----------|---------|
| `string` | Data type |
| `name` | Field name |
| `2` | Unique field number |

Each field number uniquely identifies a field during binary serialization.

---

# Service Definitions

Services define the remote procedures that clients can call.

Example:

```proto
service EmployeeService {

    rpc GetEmployee(EmployeeRequest)
        returns (EmployeeResponse);

}
```

Here:

- `EmployeeService` is the service.
- `GetEmployee` is the RPC method.
- `EmployeeRequest` is the input message.
- `EmployeeResponse` is the output message.

---

# RPC Method Syntax

An RPC method follows this format.

```proto
rpc MethodName(RequestMessage)
    returns (ResponseMessage);
```

Example:

```proto
rpc CreateEmployee(EmployeeRequest)
    returns (EmployeeResponse);
```

This resembles calling a normal function, except the function executes on a remote server.

---

# Naming Conventions

Following consistent naming conventions improves readability.

Recommended conventions:

| Element | Convention | Example |
|----------|------------|---------|
| Message | PascalCase | `EmployeeRequest` |
| Service | PascalCase | `EmployeeService` |
| RPC Method | PascalCase | `GetEmployee` |
| Field | snake_case | `employee_name` |
| Package | lowercase | `employee` |

Consistent naming makes schemas easier to understand and maintain.

---

# Complete Example

The following example demonstrates a complete `.proto` file.

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

This schema defines:

- One package
- Two messages
- One service
- One RPC method

From this single file, the Protocol Buffer compiler can generate client and server code for multiple programming languages.

---

# How the Compiler Uses the Schema

The Protocol Buffer compiler (`protoc`) reads the `.proto` file.

```text
.proto File

      │

      ▼

protoc Compiler

      │

      ▼

Generated Source Code

      │

      ▼

Client & Server Applications
```

Developers work with the generated classes instead of manually handling serialization.

---

# Why Syntax Matters

A `.proto` file is more than just a configuration file.

It defines:

- The API contract
- Data structures
- Communication rules
- Type definitions
- Service interfaces

Any change to the schema affects every client and server that depends on it.

For this reason, `.proto` files should be carefully designed and version controlled.

---

# Best Practices

When writing Protocol Buffer schemas:

- Always begin with `syntax = "proto3";`.
- Use meaningful names for messages and services.
- Follow consistent naming conventions.
- Add comments to explain complex messages.
- Keep related messages together.
- Treat the `.proto` file as the official API contract.

---

# Common Mistakes

Avoid the following mistakes:

- Omitting the `syntax` declaration.
- Using inconsistent naming conventions.
- Choosing unclear message or field names.
- Treating `.proto` files as temporary implementation details.
- Editing generated source code instead of the `.proto` file.

---

# Key Takeaways

- Every Protocol Buffer schema is defined inside a `.proto` file.
- The `syntax = "proto3";` declaration specifies the language version.
- A `.proto` file contains messages, services, RPC methods, and other schema definitions.
- Messages define the structure of transmitted data, while services define the available RPC methods.
- The Protocol Buffer compiler generates strongly typed source code from the schema.
- A well-designed `.proto` file serves as the single source of truth for communication between gRPC clients and servers.