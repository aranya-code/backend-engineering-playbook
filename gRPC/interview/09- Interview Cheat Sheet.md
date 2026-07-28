# Overview

This chapter serves as a quick revision guide for gRPC interviews. It summarizes the most important concepts, commands, best practices, status codes, Protocol Buffer rules, HTTP/2 features, deployment considerations, and production troubleshooting techniques.

Use this chapter before interviews, technical discussions, or system design rounds to quickly refresh your knowledge without reading the complete playbook.

---

# gRPC at a Glance

| Topic | Summary |
|-------|---------|
| Full Form | Google Remote Procedure Call |
| Developed By | Google |
| Transport Protocol | HTTP/2 |
| Serialization | Protocol Buffers |
| Interface Definition | `.proto` |
| Code Generator | `protoc` |
| Browser Support | Via gRPC-Web |
| Streaming | Native Support |
| Best Use Case | Internal Service-to-Service Communication |

---

# Four RPC Types

| RPC Type | Communication Pattern | Typical Use Case |
|----------|-----------------------|------------------|
| Unary | One Request → One Response | CRUD APIs |
| Server Streaming | One Request → Many Responses | Notifications |
| Client Streaming | Many Requests → One Response | File Uploads |
| Bidirectional Streaming | Many Requests ↔ Many Responses | Chat Applications |

---

# Protocol Buffer Rules

## Always Remember

✅ Never reuse field numbers.

✅ Reserve deleted fields.

✅ Prefer adding new optional fields.

✅ Keep messages backward compatible.

✅ Use meaningful package names.

✅ Organize services logically.

---

## Avoid

❌ Changing field numbers

❌ Removing fields without reserving them

❌ Renaming packages carelessly

❌ Breaking existing clients

---

# Frequently Used Status Codes

| Code | Meaning |
|------|---------|
| OK | Request successful |
| CANCELLED | Request cancelled |
| UNKNOWN | Unknown error |
| INVALID_ARGUMENT | Invalid request |
| DEADLINE_EXCEEDED | Request timeout |
| NOT_FOUND | Resource not found |
| ALREADY_EXISTS | Resource already exists |
| PERMISSION_DENIED | Authorization failed |
| UNAUTHENTICATED | Authentication failed |
| RESOURCE_EXHAUSTED | Rate limit or quota exceeded |
| FAILED_PRECONDITION | Operation cannot proceed |
| ABORTED | Operation aborted |
| OUT_OF_RANGE | Value outside valid range |
| UNIMPLEMENTED | Method not implemented |
| INTERNAL | Internal server error |
| UNAVAILABLE | Service temporarily unavailable |
| DATA_LOSS | Unrecoverable data corruption |

---

# HTTP/2 Features

- Binary framing
- Multiplexing
- Header compression (HPACK)
- Persistent TCP connections
- Flow control
- Stream prioritization
- Lower latency
- Better bandwidth utilization

---

# gRPC Performance Tips

✅ Use Protocol Buffers instead of JSON.

✅ Reuse channels.

✅ Keep messages small.

✅ Use streaming for continuous communication.

✅ Enable compression only when beneficial.

✅ Set deadlines on all client requests.

✅ Avoid unnecessary network hops.

✅ Benchmark before optimizing.

---

# Security Checklist

- TLS enabled
- mTLS for internal communication (when appropriate)
- JWT authentication
- OAuth2 integration
- Authentication interceptors
- Authorization checks
- Certificate rotation
- Secret management
- Encrypted service-to-service traffic

---

# Production Checklist

Before deploying a gRPC service, verify:

- Health checks configured
- Readiness probes
- Liveness probes
- TLS certificates
- Deadlines configured
- Retries configured
- Logging enabled
- Metrics exported
- Distributed tracing enabled
- Reflection disabled (unless required)
- Load balancing configured
- Resource limits defined
- Monitoring dashboards available

---

# Kubernetes Checklist

Ensure:

- Deployment created
- Service created
- Ingress supports HTTP/2
- Horizontal Pod Autoscaler configured
- ConfigMaps used appropriately
- Secrets stored securely
- Proper resource requests and limits
- Rolling updates enabled
- Pod disruption budget configured (if required)

---

# Load Balancing Checklist

Consider:

- Client-side vs Server-side load balancing
- Long-lived HTTP/2 connections
- Health checks
- Connection draining
- Failover strategy
- Retry policies
- Service discovery integration

---

# Observability Checklist

Monitor:

### Metrics

- Request rate
- Error rate
- Success rate
- Active streams
- CPU usage
- Memory usage
- Network throughput
- P95 latency
- P99 latency

### Logs

- Structured logs
- Correlation IDs
- Request IDs
- Error details

### Traces

- Distributed tracing
- Service latency
- Dependency calls
- End-to-end request flow

---

# Common grpcurl Commands

List services:

```bash
grpcurl localhost:50051 list
```

Describe a service:

```bash
grpcurl localhost:50051 describe UserService
```

Call a method:

```bash
grpcurl \
-d '{"id":1}' \
localhost:50051 \
UserService/GetUser
```

Use Reflection:

```bash
grpcurl localhost:50051 list
```

Call with TLS:

```bash
grpcurl \
-cert client.crt \
-key client.key \
-cacert ca.crt \
host:443 \
service/method
```

---

# Common Interview Questions

Be prepared to answer:

- What is gRPC?
- Why HTTP/2?
- Why Protocol Buffers?
- Why is gRPC faster than REST?
- Explain the four RPC types.
- Unary vs Streaming?
- What is Metadata?
- What are Interceptors?
- What are Deadlines?
- What is Reflection?
- What is grpcurl?
- Explain API versioning.
- Explain service discovery.
- Explain load balancing.
- Explain retries.
- Explain circuit breakers.
- Explain observability.
- Explain mTLS.
- Explain gRPC-Web.
- When would you choose REST instead?

---

# Common Production Problems

| Problem | Possible Cause |
|----------|----------------|
| UNAVAILABLE | Service unavailable, network issue, load balancer |
| DEADLINE_EXCEEDED | Slow service, slow database, network latency |
| Authentication failures | Expired JWT, invalid certificate |
| Streaming disconnects | Idle timeout, Keepalive misconfiguration |
| High latency | Slow dependencies, serialization, network |
| Uneven traffic | Sticky sessions, connection reuse |
| Connection refused | Service not running, incorrect endpoint |
| Proto mismatch | Version incompatibility |

---

# REST vs gRPC

| REST | gRPC |
|------|------|
| JSON | Protocol Buffers |
| HTTP/1.1 (typically) | HTTP/2 |
| Resource-based | RPC-based |
| Human-readable | Binary |
| Public APIs | Internal Services |
| Limited Streaming | Native Streaming |

---

# Architecture Decision Guide

| Scenario | Recommended Technology |
|----------|------------------------|
| Public API | REST |
| Browser Application | REST / gRPC-Web |
| Internal Microservices | gRPC |
| High Throughput | gRPC |
| Low Latency | gRPC |
| Third-party Integration | REST |
| Real-time Chat | gRPC Streaming |
| Event Processing | Kafka (with gRPC where synchronous communication is required) |
| File Upload | Client Streaming or REST (depending on requirements) |
| Notifications | Server Streaming |

---

# Senior Interview Tips

- Clarify requirements before proposing a solution.
- Discuss trade-offs rather than absolute answers.
- Think in terms of scalability, reliability, and maintainability.
- Consider failure scenarios and recovery strategies.
- Mention observability, security, and performance throughout your design.
- Use real production examples whenever possible.
- Communicate your reasoning clearly and systematically.

---

# Best Practices

- Keep this chapter bookmarked for quick revision.
- Revisit the checklists before interviews and production deployments.
- Practice explaining concepts in your own words rather than memorizing definitions.
- Use architecture diagrams to support technical discussions.
- Stay updated with evolving gRPC features and ecosystem tools.

---

# Common Mistakes

- Memorizing answers without understanding the underlying concepts.
- Ignoring production concerns such as monitoring and resilience.
- Assuming gRPC is always the best choice regardless of context.
- Overlooking backward compatibility when evolving APIs.
- Forgetting to explain trade-offs during interview discussions.

---

# Key Takeaways

- This cheat sheet consolidates the most important gRPC concepts, commands, and best practices into a single reference.
- Strong interview performance comes from understanding how individual concepts connect within real-world distributed systems.
- Reviewing these summaries before interviews helps reinforce key topics such as Protocol Buffers, HTTP/2, streaming, security, observability, deployment, and troubleshooting.
- Use this chapter as a final revision resource alongside the detailed chapters in this playbook to build confidence for backend engineering and system design interviews.