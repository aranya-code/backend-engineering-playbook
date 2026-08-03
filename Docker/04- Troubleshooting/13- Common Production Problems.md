# Common Production Problems

## Overview

Running Docker in production introduces challenges that are rarely encountered during local development. Containers must operate reliably under heavy traffic, resource constraints, network failures, security threats, and infrastructure changes. Poor configuration can lead to downtime, degraded performance, and data loss.

This guide covers the most common production issues encountered in Docker environments, explains how to diagnose them, and provides practical solutions and preventive best practices.

---

## Common Production Problems

| Issue | Severity |
|--------|----------|
| Containers keep restarting | High |
| Out of memory (OOMKilled) | High |
| High CPU usage | High |
| Disk space exhaustion | High |
| Application unavailable after deployment | High |
| Health check failures | High |
| Database connection failures | High |
| Container logs consuming disk space | Medium |
| Image version inconsistencies | Medium |
| Single point of failure | High |

---

# Issue 1: Containers Keep Restarting

## Symptoms

- Container repeatedly restarts.
- Service becomes unavailable.
- Restart count continuously increases.

---

## Possible Causes

- Application crash.
- Invalid configuration.
- Failed health checks.
- Missing environment variables.
- Database unavailable during startup.

---

## How to Diagnose

View running containers:

```bash
docker ps
```

Inspect logs:

```bash
docker logs <container_name>
```

Inspect restart policy:

```bash
docker inspect <container_name>
```

---

## Solutions

- Fix application startup errors.
- Verify environment variables.
- Ensure dependent services are available.
- Correct the restart policy if necessary.

---

## Prevention

- Test startup procedures thoroughly.
- Use health checks.
- Implement retry logic for external dependencies.

---

# Issue 2: Out of Memory (OOMKilled)

## Symptoms

Container exits with:

```text
Exited (137)
```

Application becomes unavailable unexpectedly.

---

## Possible Causes

- Memory leak.
- Memory limits too low.
- Large workloads.

---

## How to Diagnose

Monitor memory usage:

```bash
docker stats
```

Inspect exit status:

```bash
docker inspect <container_name>
```

---

## Solutions

Increase available memory.

Optimize application memory usage.

Configure appropriate memory limits.

---

## Prevention

Monitor memory usage continuously.

Perform load testing before production deployment.

---

# Issue 3: High CPU Usage

## Symptoms

- Slow application response.
- High server load.
- Increased latency.

---

## Possible Causes

- Infinite loops.
- Excessive requests.
- Poor application performance.
- Resource contention.

---

## How to Diagnose

```bash
docker stats
```

View processes:

```bash
docker top <container_name>
```

---

## Solutions

Optimize application code.

Configure CPU limits.

Scale horizontally if required.

---

## Prevention

Perform performance testing.

Monitor CPU usage using observability tools.

---

# Issue 4: Disk Space Exhaustion

## Symptoms

```text
no space left on device
```

Unable to deploy new containers.

---

## Possible Causes

- Large log files.
- Old images.
- Dangling volumes.
- Build cache.

---

## How to Diagnose

View Docker disk usage:

```bash
docker system df
```

Check filesystem:

```bash
df -h
```

---

## Solutions

Clean unused resources:

```bash
docker system prune
```

Remove unused volumes:

```bash
docker volume prune
```

Rotate logs.

---

## Prevention

Schedule automated Docker cleanup.

Enable log rotation.

---

# Issue 5: Application Unavailable After Deployment

## Symptoms

Deployment completes successfully, but users cannot access the application.

---

## Possible Causes

- Wrong port mapping.
- Reverse proxy misconfiguration.
- Application startup failure.
- Firewall restrictions.

---

## How to Diagnose

View container status:

```bash
docker ps
```

Inspect logs:

```bash
docker logs <container_name>
```

Test application locally:

```bash
curl http://localhost:<port>
```

---

## Solutions

Verify published ports.

Review reverse proxy configuration.

Confirm application binds to:

```text
0.0.0.0
```

instead of:

```text
127.0.0.1
```

---

## Prevention

Validate deployments in a staging environment.

Perform post-deployment smoke tests.

---

# Issue 6: Health Check Failures

## Symptoms

Container status:

```text
unhealthy
```

Load balancer removes container from service.

---

## Possible Causes

- Incorrect endpoint.
- Slow startup.
- Application crash.

---

## How to Diagnose

Inspect container:

```bash
docker inspect <container_name>
```

Review logs:

```bash
docker logs <container_name>
```

---

## Solutions

Correct health check configuration.

Increase startup timeout.

Verify application readiness.

---

## Prevention

Implement lightweight and reliable health endpoints.

---

# Issue 7: Database Connection Failures

## Symptoms

```text
Connection refused
```

or

```text
Timeout expired
```

---

## Possible Causes

- Database unavailable.
- Incorrect credentials.
- Network issues.
- Service startup order.

---

## How to Diagnose

Inspect environment variables:

```bash
docker exec <container_name> env
```

Verify database connectivity:

```bash
docker exec -it <container_name> ping database
```

Review database logs.

---

## Solutions

Use service names instead of IP addresses.

Implement retry mechanisms.

Verify credentials.

---

## Prevention

Use health checks and connection retries.

---

# Issue 8: Container Logs Consuming Disk Space

## Symptoms

Disk usage continuously increases.

---

## Possible Causes

- Verbose logging.
- Missing log rotation.

---

## How to Diagnose

View log directory size:

```bash
du -sh /var/lib/docker/containers
```

---

## Solutions

Configure log rotation.

Example:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
```

Restart Docker after applying changes.

---

## Prevention

Always configure log rotation in production.

---

# Issue 9: Image Version Inconsistencies

## Symptoms

Different servers run different application versions.

Unexpected application behavior.

---

## Possible Causes

- Using `latest`.
- Missing image versioning.
- Failed deployment.

---

## How to Diagnose

Inspect images:

```bash
docker images
```

Inspect running container:

```bash
docker inspect <container_name>
```

---

## Solutions

Use immutable version tags.

Deploy identical images across environments.

---

## Prevention

Never use `latest` in production deployments.

---

# Issue 10: Single Point of Failure

## Symptoms

Entire application becomes unavailable after one server fails.

---

## Possible Causes

- Single Docker host.
- No redundancy.
- No load balancing.

---

## How to Diagnose

Review deployment architecture.

Identify critical components without redundancy.

---

## Solutions

Deploy multiple application instances.

Use load balancers.

Use orchestration platforms such as Docker Swarm or Kubernetes.

---

## Prevention

Design for high availability.

Avoid single points of failure.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| List containers | `docker ps` |
| View logs | `docker logs <container>` |
| Monitor resources | `docker stats` |
| Inspect container | `docker inspect <container>` |
| View disk usage | `docker system df` |
| Remove unused resources | `docker system prune` |
| View processes | `docker top <container>` |
| Execute shell | `docker exec -it <container> sh` |
| Inspect networks | `docker network inspect` |
| Inspect volumes | `docker volume inspect` |

---

# Production Readiness Checklist

- ✅ Configure CPU and memory limits.
- ✅ Run containers as a non-root user.
- ✅ Enable health checks.
- ✅ Configure restart policies.
- ✅ Enable log rotation.
- ✅ Use named volumes for persistent data.
- ✅ Store secrets outside Docker images.
- ✅ Pin image versions (avoid `latest`).
- ✅ Monitor containers using Prometheus and Grafana.
- ✅ Perform regular backups.
- ✅ Scan images for vulnerabilities.
- ✅ Test deployments in a staging environment.
- ✅ Implement rolling deployments where possible.
- ✅ Configure reverse proxies and TLS.
- ✅ Keep Docker Engine and images updated.

---

# Best Practices

- Treat containers as immutable.
- Keep Docker images small and optimized.
- Automate deployments using CI/CD pipelines.
- Use infrastructure as code for reproducible deployments.
- Implement centralized logging and monitoring.
- Configure proper resource limits.
- Regularly clean unused Docker resources.
- Continuously monitor production workloads and infrastructure health.

---

# Related Topics

- Docker Security
- Docker Compose
- Docker Swarm
- Docker Networking
- Docker Volumes
- Performance and Resource Issues
- Registry and Image Pull Issues

---

## Key Takeaways

- Production Docker environments require careful planning around reliability, scalability, security, and observability.
- Most production incidents stem from resource exhaustion, configuration errors, deployment inconsistencies, or inadequate monitoring.
- Health checks, resource limits, centralized logging, and automated deployments significantly improve production stability.
- Avoid using mutable image tags like `latest`, and ensure deployments are tested in staging before production.
- Proactive monitoring, regular maintenance, and adherence to container best practices help minimize downtime and simplify troubleshooting.