# Scenario Based Questions

## Overview

Scenario-based questions are commonly used in backend, DevOps, platform engineering, and cloud interviews to evaluate practical problem-solving skills. Instead of asking about Docker commands, interviewers present real-world production issues and expect you to explain how you would investigate, troubleshoot, and resolve them.

The goal is not to memorize commands but to demonstrate a structured troubleshooting process, sound engineering judgment, and familiarity with Docker best practices.

This section contains practical Docker scenarios along with interview-ready answers.

---

# Beginner Scenarios

## 1. A Docker container exits immediately after starting. What would you do?

**Expected Answer**

First, determine why the container exited.

Investigation steps:

1. Check the container status.

```bash
docker ps -a
```

2. Review container logs.

```bash
docker logs container_name
```

3. Inspect the container.

```bash
docker inspect container_name
```

4. Verify:

- CMD
- ENTRYPOINT
- Environment variables
- Application startup
- Missing dependencies

---

## 2. The application works locally but not inside Docker. How would you troubleshoot it?

**Expected Answer**

Check:

- Dockerfile
- Build logs
- Environment variables
- Mounted volumes
- Published ports
- Working directory
- Installed dependencies

Use:

```bash
docker exec -it container_name sh
```

to inspect the running container.

---

## 3. Your web application is running, but the browser cannot access it.

**Expected Answer**

Possible causes:

- Port not published
- Wrong host port
- Firewall
- Application listening on:

```text
127.0.0.1
```

instead of

```text
0.0.0.0
```

Verify:

```bash
docker ps
```

Check published ports.

---

## 4. A Docker image takes 15 minutes to build. How would you optimize it?

**Expected Answer**

Investigate:

- Layer ordering
- Large dependencies
- Build cache usage
- Base image size
- `.dockerignore`

Apply:

- Multi-stage builds
- Smaller base images
- Better COPY ordering
- Layer caching

---

## 5. A container cannot connect to PostgreSQL.

**Expected Answer**

Verify:

- Database container is running
- Service names
- Network configuration
- Credentials
- Database port
- Firewall

Never use:

```text
localhost
```

Use:

```text
database
```

(or the Docker Compose service name).

---

# Intermediate Scenarios

## 6. A production container keeps restarting every few seconds.

**Expected Answer**

Investigate:

- Application logs
- Health checks
- Restart policy
- Environment variables
- Resource usage

Commands:

```bash
docker logs container_name
```

```bash
docker inspect container_name
```

```bash
docker stats
```

---

## 7. Your PostgreSQL database loses all data after recreating the container.

**Expected Answer**

The database is likely storing data inside the container's writable layer.

Solution:

- Use a named Docker volume.
- Verify the volume is mounted correctly.
- Keep database files outside the container lifecycle.

---

## 8. Developers complain that Docker builds are always slow.

**Expected Answer**

Review:

- Dockerfile order
- Build context
- Cache usage
- Base image
- Dependency installation

Optimize by:

- Copying dependency files first
- Using `.dockerignore`
- Multi-stage builds
- Lightweight base images

---

## 9. One container cannot communicate with another.

**Expected Answer**

Check:

- Docker network
- Service names
- DNS resolution
- Firewall
- Container status

Commands:

```bash
docker network ls
```

```bash
docker network inspect network_name
```

---

## 10. Disk space on the Docker host is almost full.

**Expected Answer**

Inspect Docker storage.

Commands:

```bash
docker system df
```

Remove unused resources:

```bash
docker system prune
```

Also review:

- Volumes
- Build cache
- Images
- Logs

---

# Advanced Scenarios

## 11. Your application suddenly consumes 100% CPU.

**Expected Answer**

Investigate:

- Infinite loops
- High request volume
- Background processes
- Resource limits

Commands:

```bash
docker stats
```

```bash
docker top container_name
```

---

## 12. Containers are frequently being OOMKilled.

**Expected Answer**

Review:

- Memory limits
- Application memory leaks
- Large caches
- Traffic spikes

Use:

```bash
docker stats
```

Increase memory only after understanding the root cause.

---

## 13. Your CI/CD pipeline downloads the same Docker image every build.

**Expected Answer**

Implement:

- Layer caching
- Registry mirrors
- Cached dependencies
- Immutable image tags

---

## 14. Developers hardcoded passwords inside the Dockerfile.

**Expected Answer**

Immediately:

- Remove secrets
- Rotate credentials
- Rebuild images
- Store secrets in a secret manager

Never commit credentials to source control.

---

## 15. Containers cannot access external APIs.

**Expected Answer**

Investigate:

- DNS
- Firewall
- Proxy
- Docker networking
- Internet connectivity

Test:

```bash
docker exec -it container_name ping google.com
```

---

# Production Scenarios

## 16. A deployment introduces downtime. How would you prevent this?

**Expected Answer**

Use:

- Rolling deployments
- Health checks
- Multiple replicas
- Load balancing
- Staging validation
- Automated rollback strategy

---

## 17. One Docker Swarm worker fails.

**Expected Answer**

Swarm automatically schedules replacement tasks on healthy workers if sufficient resources are available.

Verify:

```bash
docker node ls
```

---

## 18. Your application behaves differently on two servers using the same image.

**Expected Answer**

Compare:

- Environment variables
- Mounted volumes
- Configuration files
- Runtime arguments
- Secrets
- Docker versions

The image may be identical while the runtime environment differs.

---

## 19. A security scan reports critical vulnerabilities.

**Expected Answer**

- Update the base image
- Upgrade dependencies
- Rebuild the image
- Re-scan
- Deploy only after validation

---

## 20. Your production logs fill the entire disk.

**Expected Answer**

Enable log rotation.

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

Restart Docker after updating the configuration.

---

# Senior-Level Design Scenarios

## 21. How would you deploy a highly available Docker application?

**Expected Answer**

Use:

- Multiple application replicas
- Load balancer
- Health checks
- Persistent storage
- Automated monitoring
- Rolling deployments
- Reverse proxy
- TLS
- Backup strategy

---

## 22. How would you secure Docker in production?

**Expected Answer**

- Run as non-root
- Use trusted images
- Scan images regularly
- Store secrets externally
- Drop unnecessary Linux capabilities
- Enable monitoring
- Restrict exposed ports

---

## 23. How would you optimize a slow Dockerized application?

**Expected Answer**

Review:

- CPU
- Memory
- Disk I/O
- Dockerfile
- Network latency
- Database queries
- Image size
- Container startup

Use metrics before making changes.

---

## 24. Your company wants zero-downtime deployments. How would you achieve this?

**Expected Answer**

Implement:

- Rolling updates
- Health checks
- Blue-Green or Canary deployments
- Load balancing
- Automated rollback
- Monitoring and alerting

---

## 25. A production container is compromised. What are your immediate actions?

**Expected Answer**

1. Isolate the affected container.
2. Preserve logs and evidence.
3. Revoke exposed credentials.
4. Stop or replace the compromised container.
5. Deploy a clean image.
6. Investigate the root cause.
7. Patch vulnerabilities.
8. Monitor for further suspicious activity.

---

# Interview Tips

- Follow a structured troubleshooting process instead of jumping directly to solutions.
- Explain **how you would investigate** before explaining **how you would fix** the problem.
- Mention relevant Docker commands where appropriate.
- Consider security, scalability, monitoring, and production impact in your answers.
- Communicate your reasoning clearly and prioritize root-cause analysis over quick fixes.

---

## Key Takeaways

- Scenario-based questions evaluate practical Docker experience rather than command memorization.
- A systematic troubleshooting approach—inspect, diagnose, resolve, and validate—is highly valued in interviews.
- Many production issues involve networking, storage, resource limits, configuration, or deployment strategies.
- Strong answers balance technical knowledge with operational best practices such as monitoring, security, and automation.
- Demonstrating structured thinking and real-world troubleshooting skills is often more important than recalling specific commands.