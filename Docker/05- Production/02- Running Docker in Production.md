# Running Docker in Production

## Overview

Running Docker in production is fundamentally different from running containers during development.

Development environments prioritize convenience, rapid iteration, and debugging. Production environments prioritize reliability, security, scalability, performance, and maintainability.

This guide explains the key considerations and best practices for deploying Docker applications into production.

---

# Development vs Production

| Development | Production |
|-------------|------------|
| Rapid development | Stability |
| Frequent code changes | Controlled releases |
| Debugging enabled | Debugging disabled |
| Source code mounted | Immutable images |
| Local environment | Production infrastructure |
| Minimal security | Hardened security |

---

# Production Deployment Lifecycle

```text
Develop

↓

Build

↓

Test

↓

Create Docker Image

↓

Deploy

↓

Health Check

↓

Monitor

↓

Maintain
```

---

# Goals of Production Deployment

A production deployment should achieve the following:

- High availability
- Security
- Fault tolerance
- Scalability
- Easy maintenance
- Fast recovery
- Predictable deployments

---

# Immutable Infrastructure

Production containers should be immutable.

Instead of modifying a running container:

```text
Application Bug

↓

Edit Container

↓

Restart
```

Use this approach:

```text
Fix Code

↓

Build New Image

↓

Deploy New Container
```

Containers should never be manually modified after deployment.

---

# Use Versioned Images

Always deploy a specific version.

Good

```dockerfile
myapp:1.0.0
```

Better

```dockerfile
myapp:1.2.5
```

Avoid

```dockerfile
myapp:latest
```

Versioned images ensure deployments are reproducible and simplify rollbacks.

---

# Build Images Once

Build the Docker image a single time.

```text
Source Code

↓

Docker Build

↓

Docker Image

↓

Registry

↓

Production
```

Do **not** rebuild the application separately on each server.

---

# Use Official Base Images

Choose trusted and maintained images.

Examples:

- python:3.12-slim
- nginx:1.28-alpine
- postgres:17-alpine
- redis:7.4-alpine

Benefits include:

- Security updates
- Smaller images
- Better community support

---

# Run Containers as Non-root

Avoid running applications as the root user.

Bad

```dockerfile
USER root
```

Good

```dockerfile
USER appuser
```

Running as a non-root user limits the impact of potential security vulnerabilities.

---

# Keep Containers Stateless

Containers should not store important application data.

Good

```text
Application

↓

Database Volume

↓

Persistent Storage
```

Bad

```text
Application

↓

Container Filesystem

↓

Data Lost
```

Use volumes for persistent data.

---

# Externalize Configuration

Do not hardcode configuration values.

Use:

- Environment variables
- Configuration files
- Secret managers

Example

```text
APP_ENV=production

DATABASE_HOST=db

REDIS_HOST=redis
```

---

# Secure Secrets

Never store secrets inside:

- Docker images
- Git repositories
- Source code

Store secrets securely using:

- Environment variables
- Secret management tools
- CI/CD secret stores

---

# Add Health Checks

Every production application should expose:

```text
GET /health
```

Example response

```json
{
    "status": "healthy"
}
```

Health checks allow Docker and orchestrators to detect unhealthy containers.

---

# Configure Restart Policies

Containers should recover automatically from unexpected failures.

Example

```yaml
restart: unless-stopped
```

Common options:

| Policy | Description |
|---------|-------------|
| no | Never restart |
| on-failure | Restart only after failures |
| always | Always restart |
| unless-stopped | Restart unless manually stopped |

---

# Use Reverse Proxies

Production applications are rarely exposed directly.

Typical architecture

```text
Internet

↓

Nginx

↓

Application
```

Benefits:

- SSL termination
- Compression
- Request routing
- Security headers
- Load balancing

---

# Enable Logging

Write logs to:

```text
stdout

stderr
```

Container platforms can collect these logs automatically.

Avoid writing logs exclusively inside the container filesystem.

---

# Monitor Applications

Track:

- CPU usage
- Memory usage
- Disk usage
- Response time
- Error rate
- Container restarts

Monitoring provides early warning before failures affect users.

---

# Resource Limits

Protect the host system.

Example

```yaml
mem_limit: 512m

cpus: 1.0

pids_limit: 200
```

Resource limits prevent one container from monopolizing system resources.

---

# Backup Critical Data

Regularly back up:

- Databases
- Uploaded files
- Configuration
- SSL certificates

Test restoration procedures to ensure backups are usable.

---

# Prepare Rollback Procedures

Every deployment should have a rollback plan.

```text
Deploy

↓

Verify

↓

Failure

↓

Rollback

↓

Previous Version
```

Rollback should be fast and well documented.

---

# Production Deployment Workflow

```text
Code

↓

Docker Image

↓

Registry

↓

Production Server

↓

Health Check

↓

Users
```

---

# Common Mistakes

## Using Development Images

Development images often contain unnecessary tools and increase image size.

---

## Editing Running Containers

Containers should be replaced, not modified.

---

## Ignoring Logs

Without logs, troubleshooting production issues becomes much more difficult.

---

## No Resource Limits

Unlimited containers can exhaust host resources and affect other services.

---

## Skipping Monitoring

A healthy deployment requires continuous visibility into application performance.

---

# Production Deployment Checklist

Before deploying:

- Build succeeds
- Image version is tagged
- Health checks configured
- Environment variables verified
- Secrets available
- Volumes mounted
- Logs accessible
- Resource limits configured
- Monitoring enabled
- Backup verified
- Rollback documented

---

# Best Practices

- Build images once and deploy the same artifact everywhere.
- Use immutable, versioned Docker images.
- Run containers as non-root users.
- Keep containers stateless.
- Store configuration outside the image.
- Enable health checks and restart policies.
- Monitor application health continuously.
- Limit resource usage.
- Test rollback procedures before production deployments.

---

# Key Takeaways

- Production deployments prioritize reliability, security, and repeatability over development convenience.
- Immutable, versioned Docker images make deployments predictable and simplify rollbacks.
- Containers should remain stateless, with persistent data stored in external volumes or databases.
- Health checks, logging, monitoring, and restart policies are essential for maintaining application availability.
- Successful production Docker deployments combine secure configuration, operational best practices, and continuous monitoring to ensure long-term stability.