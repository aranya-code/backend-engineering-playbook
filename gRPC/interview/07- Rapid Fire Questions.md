# Overview

Rapid-fire interview rounds are commonly used by interviewers to quickly assess the breadth of a candidate's knowledge. These rounds consist of short, direct questions that require concise, accurate answers. The goal is not to provide lengthy explanations but to demonstrate confidence and a solid understanding of core concepts.

This chapter contains over 100 frequently asked rapid-fire questions covering gRPC fundamentals, Protocol Buffers, HTTP/2, streaming, security, production deployments, performance optimization, Kubernetes integration, observability, and troubleshooting.

Practice answering each question in **10–30 seconds**. If the interviewer wants more detail, they will ask follow-up questions.

---

# gRPC Fundamentals

### 1. What does gRPC stand for?

Google Remote Procedure Call.

---

### 2. Who developed gRPC?

Google.

---

### 3. Is gRPC open source?

Yes.

---

### 4. What transport protocol does gRPC use?

HTTP/2.

---

### 5. Which serialization format does gRPC use?

Protocol Buffers.

---

### 6. Is JSON mandatory in gRPC?

No.

---

### 7. What is an RPC?

A function call executed on a remote machine.

---

### 8. Is gRPC synchronous?

It supports both synchronous and asynchronous communication.

---

### 9. Can gRPC stream data?

Yes.

---

### 10. Is gRPC language-independent?

Yes.

---

# Protocol Buffers

### 11. What is a `.proto` file?

The schema definition file.

---

### 12. What compiler generates code?

`protoc`

---

### 13. Why are field numbers important?

They uniquely identify serialized fields.

---

### 14. Can field numbers change?

No.

---

### 15. Should deleted field numbers be reused?

No.

---

### 16. Which keyword prevents field reuse?

`reserved`

---

### 17. What is `oneof`?

It allows only one field to be set.

---

### 18. What is a repeated field?

A list or array.

---

### 19. What is a map field?

A key-value collection.

---

### 20. Are Protocol Buffers human-readable?

No.

---

# HTTP/2

### 21. Which HTTP version does gRPC require?

HTTP/2.

---

### 22. What is multiplexing?

Multiple streams over one connection.

---

### 23. What is HPACK?

HTTP/2 header compression.

---

### 24. Does HTTP/2 reduce latency?

Yes.

---

### 25. Does HTTP/2 reuse connections?

Yes.

---

# RPC Types

### 26. How many RPC types exist?

Four.

---

### 27. Which RPC resembles REST?

Unary RPC.

---

### 28. Which RPC supports live notifications?

Server Streaming.

---

### 29. Which RPC uploads multiple messages?

Client Streaming.

---

### 30. Which RPC supports chat applications?

Bidirectional Streaming.

---

# Client & Server

### 31. What is a Stub?

The generated client proxy.

---

### 32. What is a Channel?

A communication connection.

---

### 33. What is Reflection?

Service discovery for tools.

---

### 34. What tool tests gRPC services?

grpcurl.

---

### 35. Can Postman test gRPC?

Yes.

---

# Metadata

### 36. What is Metadata?

Key-value request information.

---

### 37. Where is JWT usually sent?

Metadata.

---

### 38. Can Metadata contain tracing information?

Yes.

---

### 39. Is Metadata encrypted with TLS?

Yes.

---

### 40. Can Metadata be modified by interceptors?

Yes.

---

# Security

### 41. What protocol encrypts gRPC traffic?

TLS.

---

### 42. What is mTLS?

Mutual TLS.

---

### 43. Does gRPC support JWT?

Yes.

---

### 44. Does gRPC support OAuth2?

Yes.

---

### 45. Should internal traffic be encrypted?

Yes.

---

# Error Handling

### 46. Which status indicates success?

OK.

---

### 47. Which status indicates timeout?

DEADLINE_EXCEEDED.

---

### 48. Which status indicates authentication failure?

UNAUTHENTICATED.

---

### 49. Which status indicates authorization failure?

PERMISSION_DENIED.

---

### 50. Which status indicates service unavailable?

UNAVAILABLE.

---

# Performance

### 51. Why is gRPC faster than REST?

Binary serialization and HTTP/2.

---

### 52. Does Protocol Buffers reduce payload size?

Yes.

---

### 53. Can compression improve performance?

Sometimes.

---

### 54. Should everything be compressed?

No.

---

### 55. Does connection reuse improve throughput?

Yes.

---

# Versioning

### 56. Can fields be added?

Yes.

---

### 57. Can field numbers change?

No.

---

### 58. Should removed fields be reserved?

Yes.

---

### 59. Is backward compatibility important?

Yes.

---

### 60. Should clients and servers evolve independently?

Ideally, yes.

---

# Kubernetes

### 61. Can Kubernetes run gRPC services?

Yes.

---

### 62. What distributes traffic across Pods?

A Service or Load Balancer.

---

### 63. What checks application health?

Liveness and Readiness probes.

---

### 64. Does gRPC work with Ingress?

Yes.

---

### 65. Which Ingress controllers support gRPC?

NGINX, Envoy, Traefik, HAProxy, and others with HTTP/2 support.

---

# Production

### 66. Should Reflection be enabled in production?

Usually no.

---

### 67. Should retries be unlimited?

No.

---

### 68. What retry strategy is recommended?

Exponential backoff.

---

### 69. What prevents retry storms?

Retry limits and backoff.

---

### 70. Should every error be retried?

No.

---

# Observability

### 71. Name the three pillars of observability.

Metrics, Logs, Traces.

---

### 72. What enables distributed tracing?

OpenTelemetry.

---

### 73. What is a Correlation ID?

An identifier used to trace a request across services.

---

### 74. Which metric measures latency?

Response time (for example, P95 or P99 latency).

---

### 75. Why monitor error rates?

To detect service degradation.

---

# Architecture

### 76. Is gRPC suitable for internal microservices?

Yes.

---

### 77. Is REST suitable for public APIs?

Yes.

---

### 78. Can REST and gRPC coexist?

Yes.

---

### 79. Should Kafka replace gRPC?

No.

---

### 80. Should gRPC replace Kafka?

No.

---

# Streaming

### 81. Which RPC supports continuous server updates?

Server Streaming.

---

### 82. Which RPC supports continuous client uploads?

Client Streaming.

---

### 83. Which RPC supports full-duplex communication?

Bidirectional Streaming.

---

### 84. Does streaming reduce repeated network requests?

Yes.

---

### 85. Can streaming connections remain open?

Yes.

---

# Deployment

### 86. What is service discovery?

Finding available service instances dynamically.

---

### 87. What performs TLS termination?

Often an API Gateway or Ingress Controller.

---

### 88. Why are health checks important?

To avoid routing traffic to unhealthy instances.

---

### 89. What is horizontal scaling?

Adding more service instances.

---

### 90. What is vertical scaling?

Increasing resources on an existing instance.

---

# Troubleshooting

### 91. What tool inspects services without local `.proto` files?

grpcurl (with Reflection enabled).

---

### 92. What commonly causes `UNAVAILABLE`?

Network issues, unhealthy services, or load balancer failures.

---

### 93. What commonly causes `DEADLINE_EXCEEDED`?

Slow processing or network latency.

---

### 94. What is the first step in troubleshooting?

Gather evidence before making assumptions.

---

### 95. Which observability tool usually finds the bottleneck fastest?

Distributed tracing.

---

# Senior Backend

### 96. Is gRPC always better than REST?

No.

---

### 97. What is the biggest advantage of gRPC?

Efficient service-to-service communication.

---

### 98. What is the biggest limitation of gRPC?

Limited native browser support.

---

### 99. Should APIs be designed for today's requirements only?

No, they should allow for future evolution and backward compatibility.

---

### 100. What matters most in a senior interview?

Clear reasoning, sound architectural decisions, and understanding trade-offs.

---

# Best Practices

- Keep answers concise and technically accurate.
- Avoid memorized definitions without understanding.
- Support answers with practical examples when asked.
- Explain trade-offs rather than absolute rules.
- Practice answering within 10–30 seconds per question.
- Be prepared for follow-up questions on any topic.

---

# Common Mistakes

- Rushing through answers without understanding the question.
- Claiming one technology is always better than another.
- Confusing Protocol Buffers with gRPC itself.
- Forgetting key concepts such as HTTP/2, streaming, or status codes.
- Giving overly detailed answers during rapid-fire rounds unless requested.

---

# Key Takeaways

- Rapid-fire rounds test the breadth of your knowledge rather than deep implementation details.
- Strong candidates answer confidently, accurately, and concisely while demonstrating a clear understanding of core concepts.
- Mastering these questions improves recall and prepares you for technical interviews ranging from junior to senior backend engineering roles.
- Use this chapter as a quick revision guide before interviews to reinforce key gRPC concepts and terminology.