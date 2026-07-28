# Overview

This chapter contains beginner-level gRPC interview questions commonly asked for Junior Backend Developer, Software Engineer I, Graduate Engineer, and early-career Backend Developer roles.

The primary objective of these interviews is to evaluate whether a candidate understands the core concepts of gRPC rather than simply memorizing definitions or APIs.

Most beginner interviews focus on:

- What gRPC is
- Why it exists
- How it differs from REST
- Protocol Buffers
- HTTP/2 fundamentals
- RPC communication
- Basic client-server architecture
- Security fundamentals
- Common gRPC terminology

Although these are considered "beginner" questions, interviewers often expect clear explanations with practical examples instead of one-line definitions.

This chapter presents commonly asked interview questions along with model answers, explanations, follow-up questions, and common mistakes to help you build strong conceptual foundations.

---

# Question 1

## What is gRPC?

### What the Interviewer is Testing

The interviewer wants to know whether you understand:

- What gRPC is
- Why it exists
- Its communication model
- Whether you can explain it in simple terms

### Model Answer

gRPC is a high-performance Remote Procedure Call (RPC) framework developed by Google.

It allows applications running on different machines to communicate with each other as if they were calling local functions. Instead of exchanging JSON over HTTP like REST APIs, gRPC uses Protocol Buffers for serialization and HTTP/2 for transport, making communication faster, more compact, and more efficient.

It is commonly used for:

- Microservices
- Internal APIs
- Distributed systems
- Real-time communication
- Cloud-native applications

### Example

Instead of sending:

```json
GET /employees/101
```

A gRPC client simply calls:

```python
employee = client.GetEmployee(request)
```

The network communication is handled automatically.

### Follow-up Questions

- What does RPC mean?
- Why is gRPC faster than REST?
- Who developed gRPC?
- Does gRPC only work with microservices?

---

# Question 2

## What does RPC mean?

### What the Interviewer is Testing

Whether you understand the fundamental concept behind gRPC.

### Model Answer

RPC stands for **Remote Procedure Call**.

It allows one application to execute a function that actually runs on another machine.

From the developer's perspective, calling a remote function looks almost identical to calling a local function.

Instead of manually creating HTTP requests, parsing JSON, and handling networking, the RPC framework performs these operations automatically.

### Example

Local function:

```python
calculate_salary(employee)
```

Remote function:

```python
employee_service.CalculateSalary(request)
```

The second function executes on another server but appears like a normal function call.

### Follow-up Questions

- Is RPC synchronous?
- What is the difference between local and remote function calls?
- What challenges does RPC solve?

---

# Question 3

## Why was gRPC created?

### What the Interviewer is Testing

Whether you understand the limitations of traditional REST communication.

### Model Answer

Google created gRPC to enable efficient communication between distributed systems.

As applications became increasingly service-oriented, REST APIs introduced several challenges:

- Larger JSON payloads
- Higher latency
- Manual client implementation
- Lack of strongly typed contracts
- Limited streaming capabilities

gRPC addresses these problems by providing:

- Binary serialization
- Code generation
- HTTP/2 support
- Streaming
- Strongly typed APIs

This makes communication faster, more reliable, and easier to maintain.

### Follow-up Questions

- What problems does JSON introduce?
- Why is binary serialization faster?
- Can REST solve the same problems?

---

# Question 4

## Who developed gRPC?

### What the Interviewer is Testing

Basic awareness of the technology.

### Model Answer

gRPC was developed by Google.

It is the modern open-source implementation of Google's internal RPC framework called Stubby, which has been used internally for many years to power Google's distributed infrastructure.

Today, gRPC is maintained by the Cloud Native Computing Foundation (CNCF) community and is widely adopted across the software industry.

### Follow-up Questions

- What is Stubby?
- Is gRPC open source?

---

# Question 5

## What is a Protocol Buffer?

### What the Interviewer is Testing

Understanding of the serialization format used by gRPC.

### Model Answer

Protocol Buffers (Protobuf) are Google's language-neutral, platform-neutral mechanism for serializing structured data.

Instead of transmitting human-readable JSON or XML, Protocol Buffers encode data into a compact binary format.

Benefits include:

- Smaller messages
- Faster serialization
- Faster deserialization
- Strong schema definition
- Automatic code generation

Protocol Buffers are defined using `.proto` files.

### Example

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

The compiler automatically generates classes for multiple programming languages.

### Follow-up Questions

- Why are Protocol Buffers faster than JSON?
- What generates the code?
- Can Protocol Buffers work without gRPC?

---

# Question 6

## What is a .proto file?

### What the Interviewer is Testing

Whether you understand how gRPC APIs are defined.

### Model Answer

A `.proto` file is the Interface Definition Language (IDL) used by Protocol Buffers.

It defines:

- Messages
- Services
- RPC methods
- Enums
- Packages

The Protocol Buffer compiler reads this file and generates client and server code.

Example:

```proto
service EmployeeService {

    rpc GetEmployee(EmployeeRequest)

    returns (EmployeeResponse);

}
```

Every gRPC service begins with a `.proto` definition.

### Follow-up Questions

- What information does a `.proto` file contain?
- Can one project contain multiple `.proto` files?

---

# Question 7

## What is protoc?

### What the Interviewer is Testing

Whether you understand code generation.

### Model Answer

`protoc` is the Protocol Buffer compiler.

It reads `.proto` files and generates source code for supported programming languages.

For Python, it generates files such as:

- employee_pb2.py
- employee_pb2_grpc.py

This eliminates the need to manually implement serialization or networking code.

### Follow-up Questions

- What files does protoc generate?
- Does protoc generate server code?

---

# Question 8

## Why is gRPC faster than REST?

### What the Interviewer is Testing

Whether you understand the performance advantages.

### Model Answer

gRPC is generally faster than REST because it uses:

- Protocol Buffers instead of JSON
- Binary serialization
- HTTP/2 instead of HTTP/1.1
- Multiplexing
- Header compression
- Persistent connections

These features reduce bandwidth usage and network overhead.

However, REST may still be a better choice for public APIs and browser compatibility.

### Follow-up Questions

- Is gRPC always faster?
- Why is binary serialization smaller?
- Does HTTP/2 improve latency?

---

# Question 9

## What is HTTP/2?

### What the Interviewer is Testing

Basic networking knowledge.

### Model Answer

HTTP/2 is the transport protocol used by gRPC.

It introduces several improvements over HTTP/1.1, including:

- Multiplexing
- Binary framing
- Header compression (HPACK)
- Stream prioritization
- Server push

These improvements significantly increase communication efficiency for distributed systems.

### Follow-up Questions

- Can gRPC work over HTTP/1.1?
- What is multiplexing?

---

# Question 10

## What are the four types of RPC supported by gRPC?

### What the Interviewer is Testing

Understanding of communication patterns.

### Model Answer

gRPC supports four communication models:

1. Unary RPC
2. Server Streaming RPC
3. Client Streaming RPC
4. Bidirectional Streaming RPC

Unary communication is similar to REST.

Streaming allows multiple messages to be exchanged over a single connection.

### Follow-up Questions

- Which RPC resembles REST?
- When would you use Bidirectional Streaming?

---

# Additional Beginner Questions

A beginner interviewer may also ask:

- What is Unary RPC?
- What is Server Streaming?
- What is Client Streaming?
- What is Bidirectional Streaming?
- What is serialization?
- What is deserialization?
- What is a channel?
- What is a stub?
- What is metadata?
- What is a deadline?
- What is a timeout?
- What is TLS?
- How does gRPC secure communication?
- What is Reflection?
- What is grpcurl?
- What is gRPC-Web?
- Can browsers communicate directly with gRPC?
- Which programming languages support gRPC?
- Can Protocol Buffers be used without gRPC?
- What is the difference between HTTP and RPC?
- What is the difference between REST and gRPC?
- What are status codes in gRPC?
- What is code generation?
- Why are field numbers important in Protocol Buffers?
- Can a client written in Python communicate with a server written in Go?
- What is backward compatibility in Protocol Buffers?
- What happens if a server is unavailable?

---

# Best Practices

- Explain concepts before discussing implementation details.
- Use simple real-world examples whenever possible.
- Compare gRPC with REST when appropriate.
- Focus on understanding rather than memorization.
- Keep answers concise but technically accurate.
- Mention production use cases when relevant.
- Be prepared for follow-up questions after every answer.

---

# Common Mistakes

- Defining gRPC only as an API framework.
- Confusing gRPC with REST.
- Saying Protocol Buffers are databases or data formats like JSON.
- Forgetting that gRPC requires HTTP/2.
- Mixing up the four RPC communication patterns.
- Claiming gRPC is always better than REST in every scenario.
- Giving memorized definitions without explaining practical applications.

---

# Key Takeaways

- Beginner interviews focus on evaluating your understanding of gRPC fundamentals rather than deep implementation details.
- You should be able to clearly explain RPC, Protocol Buffers, HTTP/2, and the four RPC communication models.
- Interviewers often ask follow-up questions, so understanding the reasoning behind concepts is more valuable than memorizing definitions.
- Supporting your answers with simple real-world examples demonstrates confidence and practical understanding.
- A strong grasp of these foundational topics prepares you for intermediate and senior-level gRPC interview discussions.