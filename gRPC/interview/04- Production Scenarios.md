# Overview

Production scenario questions are among the most important parts of a Senior Backend Engineer interview. Unlike theoretical questions, these scenarios evaluate how you think under pressure, identify root causes, analyze trade-offs, and resolve real production incidents.

Interviewers are less interested in whether you immediately know the answer and more interested in your troubleshooting methodology. A structured, logical approach often carries more weight than jumping to conclusions.

For each scenario in this chapter, focus on:

- Gathering evidence before making assumptions.
- Identifying the scope of the problem.
- Isolating the affected components.
- Using logs, metrics, and traces effectively.
- Explaining both immediate mitigation and long-term prevention.

These scenarios are representative of issues encountered in production microservice environments using gRPC.

---

# Scenario 1

## A client suddenly starts receiving `UNAVAILABLE` errors. How would you troubleshoot the issue?

### What the Interviewer is Testing

- Understanding of gRPC status codes.
- Production troubleshooting methodology.
- Networking knowledge.

### Model Answer

I would investigate the problem layer by layer instead of assuming the application is at fault.

My troubleshooting process would be:

1. Verify whether all clients are affected or only a subset.
2. Check whether the server is healthy.
3. Verify Kubernetes pods are running.
4. Check service discovery.
5. Inspect load balancer health.
6. Review server logs.
7. Examine network connectivity.
8. Review recent deployments.
9. Check TLS certificates.
10. Validate DNS resolution.

If the issue started immediately after deployment, I would consider rolling back while continuing the investigation.

### Follow-up Questions

- Which logs would you inspect first?
- Can DNS issues cause `UNAVAILABLE`?
- Can TLS failures return the same status?

---

# Scenario 2

## API latency suddenly increases from 30 ms to 800 ms. What would you do?

### What the Interviewer is Testing

- Performance troubleshooting.
- Monitoring experience.
- Root cause analysis.

### Model Answer

I would avoid guessing and instead use observability tools.

My investigation would include:

- Request latency dashboards.
- CPU utilization.
- Memory usage.
- Network latency.
- Database query performance.
- Downstream service latency.
- Recent deployments.
- Distributed traces.
- Error rates.

If only one dependency is slow, I would isolate that service before investigating application code.

### Follow-up Questions

- Which metric would you check first?
- Would you restart the service immediately?

---

# Scenario 3

## One service cannot communicate with another after a Kubernetes deployment.

### What the Interviewer is Testing

- Kubernetes knowledge.
- Networking fundamentals.
- Service discovery.

### Model Answer

Possible causes include:

- Service selector mismatch.
- Incorrect namespace.
- Failed readiness probes.
- Network policies.
- Incorrect DNS configuration.
- TLS configuration issues.
- Container startup failures.

I would verify:

```text
Pods

↓

Services

↓

Endpoints

↓

DNS

↓

Network

↓

Application Logs
```

This helps identify where communication is breaking.

### Follow-up Questions

- How would you verify service discovery?
- What kubectl commands would you use?

---

# Scenario 4

## A streaming RPC disconnects after several minutes.

### What the Interviewer is Testing

- Streaming knowledge.
- HTTP/2 understanding.
- Infrastructure awareness.

### Model Answer

Common causes include:

- Idle timeout.
- Load balancer timeout.
- Proxy timeout.
- Client deadline.
- Server deadline.
- Network interruption.
- Keepalive configuration.

I would inspect:

- Keepalive settings.
- Ingress configuration.
- Load balancer idle timeout.
- HTTP/2 configuration.
- Client logs.
- Server logs.

### Follow-up Questions

- How does Keepalive solve this?
- Which component usually closes the connection?

---

# Scenario 5

## A new version of a service breaks older clients.

### What the Interviewer is Testing

- API versioning.
- Protocol Buffer compatibility.

### Model Answer

This usually indicates a backward compatibility issue.

Possible causes include:

- Field numbers changed.
- Required fields introduced.
- Services renamed.
- Fields removed without reserving them.
- Breaking schema changes.

To prevent this:

- Never reuse field numbers.
- Reserve deleted fields.
- Prefer adding optional fields.
- Maintain compatibility during migrations.

### Follow-up Questions

- Can field names change?
- Can field numbers change?

---

# Scenario 6

## CPU usage suddenly reaches 95% after a deployment.

### What the Interviewer is Testing

- Production diagnostics.
- Performance optimization.

### Model Answer

I would investigate:

- Infinite loops.
- High request volume.
- Thread contention.
- Serialization overhead.
- Memory pressure.
- Database retries.
- Inefficient algorithms.
- Logging overhead.

I would compare metrics before and after deployment to identify regressions.

### Follow-up Questions

- Would you immediately scale the deployment?
- How would you identify the offending endpoint?

---

# Scenario 7

## Authentication suddenly fails for every request.

### What the Interviewer is Testing

- Security knowledge.
- Authentication flow.

### Model Answer

I would verify:

- JWT expiration.
- Token issuer.
- Token audience.
- Authentication interceptors.
- Certificate validity.
- Secret rotation.
- Identity provider availability.

Authentication failures are often caused by expired certificates or configuration changes rather than application bugs.

### Follow-up Questions

- How would you validate a JWT?
- Can clock skew cause authentication failures?

---

# Scenario 8

## A single pod receives significantly more traffic than the others.

### What the Interviewer is Testing

- Load balancing.
- Kubernetes networking.

### Model Answer

Possible causes include:

- Sticky sessions.
- Client-side connection reuse.
- Improper load balancing policy.
- Uneven endpoint registration.
- Long-lived HTTP/2 connections.

I would examine:

- Connection distribution.
- Endpoint health.
- Load balancer configuration.
- Client connection behavior.

### Follow-up Questions

- Why can HTTP/2 affect load balancing?
- How would you rebalance connections?

---

# Scenario 9

## Memory usage continuously increases until the service crashes.

### What the Interviewer is Testing

- Memory leak diagnosis.

### Model Answer

I would investigate:

- Memory profiling.
- Object retention.
- Long-lived streams.
- Unclosed resources.
- Cache growth.
- Goroutine/thread leaks.
- Large message buffering.

I would compare heap usage over time and inspect garbage collection behavior.

### Follow-up Questions

- Which profiling tools would you use?
- How do long-lived streams affect memory?

---

# Scenario 10

## A customer reports intermittent failures, but monitoring shows the service is healthy.

### What the Interviewer is Testing

- Advanced troubleshooting.
- Distributed systems thinking.

### Model Answer

Intermittent failures often indicate problems outside the application itself.

I would investigate:

- Network instability.
- DNS resolution.
- Load balancer behavior.
- Packet loss.
- Retry storms.
- Downstream dependencies.
- Time synchronization.
- Client configuration.

Distributed tracing is particularly valuable because it reveals failures that may not appear in application logs.

### Follow-up Questions

- Why are intermittent failures difficult to reproduce?
- Which observability tool would provide the most useful information?

---

# Additional Production Scenarios

Senior backend interviews frequently include scenarios such as:

- A rolling deployment causes intermittent request failures.
- Clients receive `DEADLINE_EXCEEDED` during peak traffic.
- gRPC traffic fails after introducing an API Gateway.
- TLS certificate rotation causes service outages.
- One Kubernetes node experiences significantly higher latency.
- A streaming service experiences backpressure.
- Distributed tracing suddenly disappears after a deployment.
- Message compression increases CPU utilization.
- Large Protocol Buffer messages cause request failures.
- Cross-region gRPC communication experiences high latency.
- One microservice becomes a bottleneck during traffic spikes.
- Health checks pass, but requests still fail.
- A retry storm overwhelms downstream services.
- Connection pools become exhausted during peak traffic.
- Observability dashboards show normal metrics, yet customers report failures.

---

# Best Practices

- Follow a structured troubleshooting methodology.
- Validate assumptions with metrics and logs.
- Investigate one layer at a time.
- Use distributed tracing to correlate requests across services.
- Differentiate between mitigation and permanent fixes.
- Explain trade-offs when proposing solutions.
- Document lessons learned after resolving incidents.

---

# Common Mistakes

- Jumping directly to conclusions without evidence.
- Restarting services before collecting diagnostics.
- Ignoring infrastructure components such as load balancers and DNS.
- Focusing solely on application code.
- Assuming every issue is caused by the latest deployment.
- Neglecting observability tools during investigations.
- Treating symptoms instead of identifying root causes.

---

# Key Takeaways

- Production scenario interviews evaluate your troubleshooting process more than your ability to recall facts.
- A systematic approach that considers networking, infrastructure, application logic, and dependencies is essential for diagnosing distributed systems.
- Strong candidates explain both immediate mitigation steps and long-term preventive measures.
- Demonstrating familiarity with observability, Kubernetes, networking, and production operations is a key differentiator for senior backend engineering roles.