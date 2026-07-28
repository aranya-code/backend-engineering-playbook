# Overview

This production checklist serves as a quick reference for deploying and operating gRPC services in production. It summarizes the most important considerations across security, networking, reliability, observability, scalability, deployment, and maintenance.

Use this checklist before every production release and during architecture reviews to ensure your gRPC services are reliable, secure, and scalable.

---

# Architecture Checklist

## Service Design

- ☐ Define clear service boundaries.
- ☐ Follow single responsibility principle.
- ☐ Keep services loosely coupled.
- ☐ Design idempotent operations where applicable.
- ☐ Separate read and write operations when appropriate.
- ☐ Use meaningful package and service names.

---

## API Design

- ☐ Use Protocol Buffers for all contracts.
- ☐ Keep messages focused and concise.
- ☐ Use appropriate scalar types.
- ☐ Avoid deeply nested message structures.
- ☐ Use `oneof` for mutually exclusive fields.
- ☐ Organize reusable messages into shared packages.

---

## Versioning

- ☐ Never change field numbers.
- ☐ Reserve removed fields.
- ☐ Add new optional fields only.
- ☐ Maintain backward compatibility.
- ☐ Version APIs carefully.

---

# Security Checklist

## Transport Security

- ☐ Enable TLS.
- ☐ Use modern TLS versions.
- ☐ Rotate certificates regularly.
- ☐ Validate server certificates.
- ☐ Encrypt all production traffic.

---

## Authentication

- ☐ Use JWT or OAuth2.
- ☐ Validate tokens.
- ☐ Check token expiration.
- ☐ Reject invalid credentials.
- ☐ Protect internal services.

---

## Authorization

- ☐ Implement role-based access control.
- ☐ Enforce least privilege.
- ☐ Validate permissions for every request.
- ☐ Audit privileged operations.

---

## Secrets Management

- ☐ Never hardcode secrets.
- ☐ Store secrets securely.
- ☐ Rotate credentials periodically.
- ☐ Limit secret access.
- ☐ Audit secret usage.

---

# Networking Checklist

## HTTP/2

- ☐ Enable HTTP/2.
- ☐ Reuse channels.
- ☐ Configure keepalive.
- ☐ Monitor connection health.
- ☐ Optimize multiplexing.

---

## Load Balancing

- ☐ Configure client-side or proxy load balancing.
- ☐ Distribute traffic evenly.
- ☐ Remove unhealthy instances.
- ☐ Verify failover behavior.

---

## Service Discovery

- ☐ Register services automatically.
- ☐ Remove stale registrations.
- ☐ Verify DNS resolution.
- ☐ Test discovery during deployments.

---

# Reliability Checklist

## Deadlines

- ☐ Configure deadlines for every RPC.
- ☐ Avoid unlimited requests.
- ☐ Tune deadlines per operation.

---

## Retries

- ☐ Retry only transient failures.
- ☐ Use exponential backoff.
- ☐ Add retry limits.
- ☐ Avoid retry storms.

---

## Circuit Breakers

- ☐ Protect downstream services.
- ☐ Prevent cascading failures.
- ☐ Configure recovery thresholds.

---

## Health Checks

- ☐ Implement gRPC health service.
- ☐ Verify readiness.
- ☐ Verify liveness.
- ☐ Remove unhealthy instances automatically.

---

# Performance Checklist

## Protocol Buffers

- ☐ Keep payloads small.
- ☐ Remove unused fields.
- ☐ Avoid unnecessary nesting.
- ☐ Optimize frequently used messages.

---

## Streaming

- ☐ Use streaming where appropriate.
- ☐ Avoid unnecessary Unary RPCs.
- ☐ Handle stream termination correctly.

---

## Compression

- ☐ Compress only large payloads.
- ☐ Measure CPU overhead.
- ☐ Benchmark performance before enabling.

---

## Resource Usage

- ☐ Monitor CPU.
- ☐ Monitor memory.
- ☐ Monitor network throughput.
- ☐ Monitor disk usage.

---

# Observability Checklist

## Logging

- ☐ Structured logging.
- ☐ Include request IDs.
- ☐ Include correlation IDs.
- ☐ Log failures clearly.
- ☐ Avoid logging sensitive data.

---

## Metrics

Monitor:

- ☐ Request count
- ☐ Error rate
- ☐ Latency
- ☐ Throughput
- ☐ Active connections
- ☐ Resource utilization

---

## Distributed Tracing

- ☐ Enable tracing.
- ☐ Propagate trace IDs.
- ☐ Trace downstream services.
- ☐ Analyze latency bottlenecks.

---

## Monitoring

- ☐ Create dashboards.
- ☐ Configure alerts.
- ☐ Monitor SLOs.
- ☐ Monitor SLIs.
- ☐ Review trends regularly.

---

# Kubernetes Checklist

## Deployment

- ☐ Configure Deployments.
- ☐ Use rolling updates.
- ☐ Set resource requests.
- ☐ Set resource limits.

---

## Networking

- ☐ Configure Services.
- ☐ Verify ingress configuration.
- ☐ Configure Network Policies.
- ☐ Test internal communication.

---

## Availability

- ☐ Multiple replicas.
- ☐ Pod disruption budget.
- ☐ Anti-affinity rules.
- ☐ Automatic restarts.

---

# Production Debugging Checklist

When problems occur:

- ☐ Check application logs.
- ☐ Verify pod health.
- ☐ Inspect metrics.
- ☐ Review traces.
- ☐ Check deadlines.
- ☐ Verify TLS certificates.
- ☐ Test connectivity.
- ☐ Check DNS resolution.
- ☐ Verify service discovery.
- ☐ Review recent deployments.

---

# Deployment Checklist

Before deployment:

- ☐ All tests passed.
- ☐ Contracts validated.
- ☐ API compatibility verified.
- ☐ Secrets configured.
- ☐ Certificates installed.
- ☐ Monitoring enabled.
- ☐ Dashboards updated.
- ☐ Alerts configured.
- ☐ Rollback plan prepared.

---

# Post-Deployment Checklist

Immediately after deployment:

- ☐ Verify service health.
- ☐ Test critical RPCs.
- ☐ Check logs.
- ☐ Review latency.
- ☐ Review error rates.
- ☐ Validate metrics.
- ☐ Confirm traffic routing.
- ☐ Verify authentication.
- ☐ Verify authorization.

---

# Incident Response Checklist

If production fails:

1. Verify service availability.
2. Check recent deployments.
3. Review logs and traces.
4. Identify affected dependencies.
5. Roll back if necessary.
6. Restore service.
7. Perform root cause analysis.
8. Document lessons learned.

---

# Common Production Mistakes

- Deploying without TLS.
- Forgetting request deadlines.
- Returning generic `INTERNAL` errors for all failures.
- Ignoring health checks.
- Logging sensitive information.
- Using unlimited retries.
- Breaking Protocol Buffer compatibility.
- Enabling Reflection unnecessarily in production.
- Skipping monitoring and alerting.
- Not testing rollback procedures.

---

# Golden Rules

1. Always use TLS.
2. Always configure deadlines.
3. Keep Protocol Buffers backward compatible.
4. Reuse channels whenever possible.
5. Implement health checks.
6. Retry only transient failures.
7. Monitor everything.
8. Use structured logging.
9. Enable distributed tracing.
10. Test disaster recovery and rollback procedures.

---

# Production Readiness Scorecard

| Area | Ready? |
|------|:------:|
| API Design | ☐ |
| Protocol Buffers | ☐ |
| Versioning | ☐ |
| Authentication | ☐ |
| Authorization | ☐ |
| TLS | ☐ |
| Deadlines | ☐ |
| Retries | ☐ |
| Health Checks | ☐ |
| Load Balancing | ☐ |
| Service Discovery | ☐ |
| Monitoring | ☐ |
| Logging | ☐ |
| Metrics | ☐ |
| Tracing | ☐ |
| Kubernetes | ☐ |
| Deployment Strategy | ☐ |
| Rollback Plan | ☐ |

---

# Best Practices

- Treat Protocol Buffer definitions as stable API contracts and evolve them carefully.
- Automate deployment validation with health checks, monitoring, and rollback procedures.
- Design for failure by implementing deadlines, retries, circuit breakers, and redundancy.
- Build observability into every service through logs, metrics, and distributed tracing.
- Regularly review production configurations to maintain security, performance, and reliability.

---

# Common Mistakes

- Deploying without adequate monitoring or alerting.
- Ignoring backward compatibility during schema evolution.
- Configuring aggressive retries that amplify outages.
- Treating observability as an afterthought.
- Neglecting rollback testing and disaster recovery planning.

---

# Key Takeaways

- Production-ready gRPC services require much more than correct application code—they depend on secure communication, resilient networking, careful API evolution, comprehensive observability, and reliable deployment practices.
- A structured production checklist helps prevent common operational failures and promotes consistent, high-quality deployments across environments.
- Regularly using this checklist before releases can significantly improve the stability, security, and maintainability of distributed systems.