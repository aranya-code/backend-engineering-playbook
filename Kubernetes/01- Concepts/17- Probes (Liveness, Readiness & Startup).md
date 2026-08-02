# Probes (Liveness, Readiness & Startup)

## Overview

Kubernetes uses **Probes** to monitor the health and availability of containers running inside a Pod. Probes allow Kubernetes to determine whether an application is running correctly, ready to receive traffic, or still starting up.

Without probes, Kubernetes only knows whether a container process is running—it cannot determine if the application inside the container is actually healthy.

Properly configured probes improve application reliability, reduce downtime, and enable self-healing.

---

## Why Probes Matter

Probes help Kubernetes:

- Detect unhealthy applications
- Automatically restart failed containers
- Prevent traffic from reaching unready applications
- Handle slow-starting applications
- Improve zero-downtime deployments

---

## Types of Probes

Kubernetes provides three types of probes:

| Probe | Purpose |
|--------|---------|
| Liveness Probe | Checks if the application is still alive |
| Readiness Probe | Checks if the application is ready to receive traffic |
| Startup Probe | Checks whether the application has finished starting |

Each probe serves a different purpose and should be configured based on application requirements.

---

## Probe Lifecycle

```text
Container Starts
       │
       ▼
Startup Probe
       │
       ▼
Readiness Probe
       │
       ▼
Service Begins Sending Traffic
       │
       ▼
Liveness Probe Runs Continuously
```

---

# Liveness Probe

## Overview

A **Liveness Probe** determines whether an application is still functioning correctly.

If the probe fails repeatedly, Kubernetes restarts the container.

It answers the question:

> "Is the application alive?"

---

## When to Use

Use a Liveness Probe when your application may:

- Deadlock
- Freeze
- Stop responding
- Enter an unrecoverable state

Instead of manual intervention, Kubernetes automatically restarts the container.

---

## Example

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Workflow

```text
Container Running
        │
        ▼
Liveness Check
        │
   ┌────┴────┐
   │         │
Success    Failure
   │         │
Continue  Restart Container
```

---

# Readiness Probe

## Overview

A **Readiness Probe** determines whether an application is ready to accept client requests.

If the readiness probe fails:

- The container keeps running.
- Kubernetes removes the Pod from the Service endpoints.
- No traffic is sent to the Pod until it becomes ready again.

It answers the question:

> "Can this application receive traffic?"

---

## Common Scenarios

A container may not be ready because:

- Database connection is not established
- Cache is warming up
- Initial data loading is in progress
- External API dependency is unavailable

---

## Example

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Workflow

```text
Pod Starts
      │
      ▼
Readiness Check
      │
 ┌────┴─────┐
 │          │
Ready    Not Ready
 │          │
Traffic   No Traffic
```

---

# Startup Probe

## Overview

A **Startup Probe** is designed for applications that take a long time to start.

Without a Startup Probe, Kubernetes may think the application has failed and repeatedly restart it before it finishes initializing.

It answers the question:

> "Has the application finished starting?"

---

## Common Use Cases

Startup Probes are useful for:

- Spring Boot applications
- Large Django applications
- Machine Learning services
- Java applications
- Applications performing database migrations
- Services loading large datasets

---

## Example

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10
```

---

## Workflow

```text
Application Starting
        │
        ▼
Startup Probe
        │
   ┌────┴────┐
   │         │
Pass      Fail
   │         │
Readiness  Restart
```

---

# Probe Methods

Kubernetes supports three methods for checking application health.

---

## HTTP Probe

Makes an HTTP request.

```yaml
httpGet:
  path: /health
  port: 8080
```

Common endpoints:

```text
/health

/ready

/live

/status
```

Most commonly used for REST APIs.

---

## TCP Probe

Checks whether a TCP connection can be established.

Example:

```yaml
tcpSocket:
  port: 5432
```

Useful for:

- Databases
- Message queues
- TCP services

---

## Exec Probe

Runs a command inside the container.

Example:

```yaml
exec:
  command:
    - cat
    - /tmp/healthy
```

Useful when application health cannot be determined via HTTP.

---

# Common Probe Configuration

| Property | Description |
|-----------|-------------|
| initialDelaySeconds | Delay before first probe |
| periodSeconds | Time between probes |
| timeoutSeconds | Probe timeout |
| successThreshold | Consecutive successes required |
| failureThreshold | Consecutive failures before action |

---

## Example Configuration

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

---

# Liveness vs Readiness

| Feature | Liveness | Readiness |
|----------|----------|-----------|
| Detects application failure | ✅ | ❌ |
| Restarts container | ✅ | ❌ |
| Removes Pod from Service | ❌ | ✅ |
| Prevents client traffic | ❌ | ✅ |
| Runs continuously | ✅ | ✅ |

---

# Startup vs Liveness

| Startup | Liveness |
|----------|-----------|
| Runs only during startup | Runs throughout container life |
| Prevents premature restarts | Detects runtime failures |
| Ideal for slow applications | Ideal for hung applications |

---

# Example: All Three Probes

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  periodSeconds: 5

livenessProbe:
  httpGet:
    path: /health
    port: 8000
  periodSeconds: 10
```

---

# Common Mistakes

### Using only a Liveness Probe

Without a Readiness Probe, traffic may reach an application before it is ready.

---

### Aggressive Probe Intervals

Checking too frequently increases unnecessary load.

---

### Short Timeouts

Slow applications may be incorrectly marked as failed.

---

### Missing Startup Probe

Long startup times can cause endless restart loops.

---

### Returning HTTP 200 for Every Request

Health endpoints should accurately reflect application state.

---

# Best Practices

- Implement dedicated `/health` and `/ready` endpoints.
- Use Readiness Probes for all production services.
- Configure Startup Probes for slow-starting applications.
- Keep probe handlers lightweight.
- Avoid expensive database queries in health checks.
- Tune delays and thresholds based on application startup time.
- Test probe behavior during deployments and failures.

---

# Interview Tips

- Liveness checks whether the application is alive.
- Readiness determines whether traffic should be routed to the Pod.
- Startup Probes prevent premature restarts during initialization.
- Readiness failures do **not** restart containers.
- Liveness failures **do** restart containers.
- Startup Probes disable Liveness and Readiness checks until startup completes.
- HTTP, TCP, and Exec are the three supported probe types.

---

## Key Takeaways

- Kubernetes Probes help monitor application health and improve reliability.
- Liveness Probes detect failed applications and trigger container restarts.
- Readiness Probes control whether a Pod receives network traffic.
- Startup Probes protect slow-starting applications from premature restarts.
- HTTP, TCP, and Exec probes provide flexible health-check mechanisms.
- Properly configured probes are essential for self-healing, rolling updates, and production-grade Kubernetes deployments.