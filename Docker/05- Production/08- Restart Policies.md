# Restart Policies

## Overview

Containers can stop unexpectedly due to application crashes, system failures, resource exhaustion, or host reboots. Without a restart policy, these containers remain stopped until someone manually starts them again.

Docker restart policies automatically restart containers under specific conditions, improving application availability and reducing manual intervention.

Restart policies are one of the simplest yet most effective reliability features available in Docker.

---

# Why Restart Policies Matter

Without restart policies:

```text
Application Crash

↓

Container Stops

↓

Manual Restart Required

↓

Application Offline
```

With restart policies:

```text
Application Crash

↓

Container Stops

↓

Docker Restart Policy

↓

Container Restarted

↓

Application Available
```

---

# What Causes Containers to Stop?

Containers may stop because of:

- Application crashes
- Unhandled exceptions
- Out of memory errors
- Host reboot
- Docker daemon restart
- Manual stop
- Dependency failures

Restart policies help recover automatically from many of these situations.

---

# Available Restart Policies

Docker provides four restart policies.

| Policy | Description |
|---------|-------------|
| `no` | Never restart the container |
| `on-failure` | Restart only if the container exits with a non-zero exit code |
| `always` | Always restart the container |
| `unless-stopped` | Restart unless the container was explicitly stopped |

---

# Restart Policy Workflow

```text
Container

↓

Application Stops

↓

Docker Checks Policy

↓

Restart?

↓

Container Running
```

---

# Policy: no

Default behavior.

```yaml
restart: "no"
```

Workflow

```text
Application Crash

↓

Container Stops

↓

No Restart
```

Use when:

- Temporary containers
- One-time scripts
- Database migrations
- Batch jobs

---

# Policy: on-failure

Docker restarts only after an unexpected failure.

```yaml
restart: on-failure
```

Workflow

```text
Exit Code 1

↓

Restart

↓

Application Running
```

Normal exit

```text
Exit Code 0

↓

No Restart
```

Useful for:

- Worker containers
- Scheduled jobs
- Processing pipelines

---

# Limiting Restart Attempts

Example

```yaml
restart: on-failure:5
```

Docker attempts:

```text
Crash

↓

Restart #1

↓

Crash

↓

Restart #2

↓

...

↓

Restart #5

↓

Stop
```

This prevents endless restart loops.

---

# Policy: always

```yaml
restart: always
```

Workflow

```text
Container Stops

↓

Restart

↓

Running
```

Docker also restarts the container after:

- Docker daemon restart
- Host reboot

Use carefully.

---

# Policy: unless-stopped

Recommended for most production services.

```yaml
restart: unless-stopped
```

Workflow

```text
Unexpected Stop

↓

Restart

↓

Running
```

Manual stop

```text
docker stop

↓

Remain Stopped
```

Unlike `always`, Docker respects manual stops.

---

# Compose Example

```yaml
services:

  app:

    image: myapp:1.0.0

    restart: unless-stopped
```

---

# Docker CLI Example

Run with restart policy.

```bash
docker run \
    --restart unless-stopped \
    myapp:1.0.0
```

Update an existing container.

```bash
docker update \
    --restart unless-stopped \
    mycontainer
```

---

# Production Architecture

```text
Internet

↓

Nginx

↓

Application

↓

Database
```

Recommended restart policies

| Service | Policy |
|----------|--------|
| Nginx | unless-stopped |
| FastAPI | unless-stopped |
| Django | unless-stopped |
| Redis | unless-stopped |
| PostgreSQL | unless-stopped |
| Celery Worker | unless-stopped |

---

# Restart After Host Reboot

```text
Server Reboot

↓

Docker Starts

↓

Restart Policy

↓

Containers Start

↓

Application Online
```

---

# Restart Loops

Sometimes an application crashes immediately after starting.

```text
Start

↓

Crash

↓

Restart

↓

Crash

↓

Restart

↓

Crash
```

Possible causes:

- Invalid environment variables
- Missing database
- Missing volumes
- Invalid configuration
- Application bugs

Restart policies do **not** solve underlying problems.

---

# Restart Policies and Health Checks

Restart policies and health checks complement each other.

```text
Container Starts

↓

Health Check

↓

Healthy

↓

Running
```

If the application repeatedly exits:

```text
Crash

↓

Restart Policy

↓

Restart
```

Health checks detect unhealthy applications.

Restart policies recover stopped containers.

---

# Restart Policy Decision Guide

```text
One-Time Task

↓

no

-------------------

Background Worker

↓

on-failure

-------------------

Production API

↓

unless-stopped

-------------------

Development

↓

unless-stopped
```

---

# Monitoring Restart Counts

View restart count.

```bash
docker inspect mycontainer
```

Example

```text
RestartCount

↓

4
```

A high restart count often indicates an application issue.

---

# Common Mistakes

## No Restart Policy

Without one, production services remain offline after crashes.

---

## Using always Everywhere

`always` may restart containers that administrators intentionally stopped.

Prefer:

```yaml
restart: unless-stopped
```

for long-running services.

---

## Ignoring Restart Loops

Repeated restarts usually indicate a configuration or application problem.

Investigate logs rather than relying on automatic restarts.

---

## Assuming Restart Policies Replace Monitoring

Restart policies recover containers.

Monitoring identifies why failures occur.

Both are necessary.

---

# Production Checklist

Before deployment:

- Restart policy configured
- Correct policy selected
- Health checks enabled
- Logs monitored
- Restart count monitored
- Startup dependencies verified
- Crash scenarios tested

---

# Best Practices

- Use `unless-stopped` for long-running production services.
- Use `on-failure` for batch jobs and workers.
- Monitor restart counts regularly.
- Combine restart policies with health checks.
- Investigate repeated restarts instead of masking failures.
- Test container recovery after host reboots.
- Document restart behavior for each service.

---

# Key Takeaways

- Restart policies automatically recover containers from many common failures.
- `unless-stopped` is the preferred restart policy for most production services because it balances resilience with administrator control.
- Restart policies improve availability but do not replace monitoring or proper error handling.
- High restart counts usually indicate deeper application or configuration issues that require investigation.
- Combining restart policies with health checks creates a more reliable and resilient Docker deployment.