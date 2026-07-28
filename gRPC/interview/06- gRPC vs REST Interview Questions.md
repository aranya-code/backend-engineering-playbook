# Overview

One of the most common topics in backend engineering interviews is the comparison between gRPC and REST. Interviewers rarely want a simple list of differences—they want to understand whether you can evaluate trade-offs and choose the right technology for the right problem.

A common mistake candidates make is claiming that gRPC is always better than REST. In reality, both technologies solve different problems and often coexist within the same architecture.

This chapter covers the most frequently asked gRPC vs REST interview questions, along with model answers, architectural considerations, and practical trade-offs.

---

# Question 1

## What is the primary difference between gRPC and REST?

### What the Interviewer is Testing

- Understanding of communication paradigms.
- Basic architectural knowledge.

### Model Answer

REST is an architectural style built around resources identified by URLs and typically communicates using JSON over HTTP.

gRPC is a Remote Procedure Call (RPC) framework that allows applications to invoke remote methods as if they were local functions. It uses Protocol Buffers for serialization and HTTP/2 for transport.

Example:

REST:

```http
GET /users/123
```

gRPC:

```text
UserService.GetUser(UserRequest)
```

REST focuses on resources, while gRPC focuses on remote procedures.

### Follow-up Questions

- Is REST a protocol?
- Is gRPC tied to HTTP/2?

---

# Question 2

## Why is gRPC generally faster than REST?

### What the Interviewer is Testing

- Performance knowledge.
- Understanding of Protocol Buffers and HTTP/2.

### Model Answer

gRPC achieves better performance because it uses:

- Binary serialization (Protocol Buffers)
- Smaller payload sizes
- HTTP/2 multiplexing
- Header compression (HPACK)
- Persistent TCP connections

REST commonly uses:

- JSON
- HTTP/1.1
- Larger payloads
- More parsing overhead

The performance difference becomes significant in high-throughput microservice environments.

### Follow-up Questions

- Is gRPC always faster?
- Does HTTP/2 contribute to lower latency?

---

# Question 3

## When would you choose REST instead of gRPC?

### What the Interviewer is Testing

- Decision-making.
- Technology selection.

### Model Answer

REST is often the better choice when:

- Building public APIs.
- Supporting browsers directly.
- Integrating with third-party systems.
- Human-readable payloads are valuable.
- Simplicity is preferred over maximum performance.

REST has excellent ecosystem support and is universally understood by HTTP clients.

### Follow-up Questions

- Can REST and gRPC coexist?
- Why do many public APIs still use REST?

---

# Question 4

## When would you choose gRPC instead of REST?

### What the Interviewer is Testing

- Architectural reasoning.

### Model Answer

I prefer gRPC when:

- Services communicate internally.
- Low latency is important.
- High request volume is expected.
- Streaming is required.
- Strong API contracts are beneficial.
- Multiple programming languages are involved.

Typical examples include:

- Payment systems
- Recommendation engines
- Internal microservices
- Machine learning inference
- Real-time analytics

### Follow-up Questions

- Would you expose gRPC directly to customers?
- What if browser support is required?

---

# Question 5

## Can REST and gRPC be used together?

### What the Interviewer is Testing

- Understanding of hybrid architectures.

### Model Answer

Yes.

Many production systems expose REST APIs externally while using gRPC for internal service-to-service communication.

Typical architecture:

```text
Client

↓

REST API Gateway

↓

gRPC Microservices

↓

Database
```

This approach combines REST's compatibility with gRPC's performance.

### Follow-up Questions

- What role does an API Gateway play?
- What is gRPC-Web?

---

# Question 6

## Which is easier to debug?

### What the Interviewer is Testing

- Operational awareness.

### Model Answer

REST is generally easier to debug because:

- JSON is human-readable.
- Standard HTTP tools are widely available.
- Requests can be inspected directly.

gRPC requires specialized tools such as:

- grpcurl
- Evans
- BloomRPC
- Postman (gRPC support)

Although debugging gRPC requires different tooling, these tools provide rich introspection capabilities.

### Follow-up Questions

- What is Reflection?
- How does grpcurl work?

---

# Question 7

## Which is better for browser applications?

### What the Interviewer is Testing

- Browser compatibility.

### Model Answer

REST is generally better because browsers natively support HTTP/1.1 and standard HTTP APIs.

Standard gRPC cannot be called directly from most browsers because of HTTP/2 framing requirements.

When browser communication with gRPC services is required, gRPC-Web is commonly used.

### Follow-up Questions

- Why can't browsers communicate with standard gRPC?
- What does gRPC-Web solve?

---

# Question 8

## Which is better for microservices?

### What the Interviewer is Testing

- Service architecture knowledge.

### Model Answer

For internal microservice communication, gRPC is often preferred because of:

- Lower latency
- Strong typing
- Efficient serialization
- Streaming support
- Automatic client generation

REST remains appropriate when interoperability and simplicity are more important than raw performance.

### Follow-up Questions

- Would every service use gRPC?
- Where would Kafka fit?

---

# Question 9

## Which technology provides better API contracts?

### What the Interviewer is Testing

- API design knowledge.

### Model Answer

gRPC provides stronger contracts because every API is defined using a `.proto` file.

The schema defines:

- Services
- Messages
- Field types
- RPC methods

Client and server code are generated directly from this contract.

REST often relies on documentation standards such as OpenAPI, but the contract is not inherently enforced by the protocol.

### Follow-up Questions

- What happens when the `.proto` changes?
- How is backward compatibility maintained?

---

# Question 10

## Which technology is more suitable for streaming?

### What the Interviewer is Testing

- Streaming concepts.

### Model Answer

gRPC is specifically designed for streaming and supports:

- Server Streaming
- Client Streaming
- Bidirectional Streaming

REST typically requires:

- Polling
- Long polling
- Server-Sent Events (SSE)
- WebSockets

For continuous, low-latency communication, gRPC streaming is generally the better option.

### Follow-up Questions

- When would WebSockets still be preferable?
- Which RPC type is used for chat applications?

---

# Common Comparison Questions

Senior interviewers frequently ask:

- Is REST stateless?
- Is gRPC stateless?
- Which protocol consumes less bandwidth?
- Which technology has lower latency?
- Which scales better?
- Which is easier to cache?
- Which is easier to monitor?
- Which has better browser support?
- Which is easier to version?
- Which is easier for third-party developers?
- Can REST support streaming?
- Can gRPC support file uploads?
- Which is better for mobile applications?
- Which performs better over slow networks?
- Which technology is more secure?
- Which has better tooling?
- Can GraphQL replace REST?
- Can GraphQL work with gRPC?
- Would you migrate an existing REST API to gRPC?
- What are the disadvantages of gRPC?
- What are the disadvantages of REST?
- How does gRPC compare with WebSockets?
- How does gRPC compare with GraphQL?
- How would you expose a gRPC service to external partners?
- Would you recommend gRPC for a startup's first API?

---

# Comparison Summary

| Feature | REST | gRPC |
|---------|------|------|
| Communication Style | Resource-based | RPC |
| Payload Format | JSON (typically) | Protocol Buffers |
| Transport | HTTP/1.1 or HTTP/2 | HTTP/2 |
| Serialization | Text | Binary |
| Performance | Good | Excellent |
| Browser Support | Excellent | Limited (gRPC-Web) |
| Streaming | Limited | Native |
| API Contract | OpenAPI (optional) | `.proto` (required) |
| Code Generation | Optional | Built-in |
| Human Readability | Excellent | Poor |
| Best Use Case | Public APIs | Internal Microservices |

---

# Best Practices

- Avoid presenting REST and gRPC as competitors; they are often complementary.
- Base your recommendation on business and technical requirements.
- Discuss trade-offs rather than absolute advantages.
- Consider browser compatibility, performance, tooling, and interoperability.
- Support answers with real-world architecture examples.
- Explain why a technology fits a specific use case.

---

# Common Mistakes

- Saying gRPC completely replaces REST.
- Claiming gRPC is always faster in every scenario.
- Ignoring browser compatibility limitations.
- Forgetting that gRPC requires HTTP/2.
- Recommending gRPC for every external API.
- Comparing only performance while ignoring ecosystem and usability.

---

# Key Takeaways

- REST and gRPC solve different problems and frequently coexist within modern backend architectures.
- gRPC excels in high-performance, strongly typed, service-to-service communication, while REST remains the preferred choice for public APIs and browser-based clients.
- Successful interview answers focus on architectural trade-offs rather than declaring one technology universally superior.
- Demonstrating an understanding of performance, compatibility, maintainability, and operational considerations is essential for senior backend engineering interviews.