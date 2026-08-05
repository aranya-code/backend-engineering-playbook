# Production Best Practices

## Overview

Building a Docker image is only one part of running applications successfully in production. Long-term reliability depends on following proven operational practices that improve security, stability, scalability, and maintainability.

This chapter summarizes the most important best practices discussed throughout the Docker production section and serves as a practical reference for deploying containerized applications.

---

# Production Mindset

Development focuses on building features.

Production focuses on keeping services available.

```text
Development

↓

Testing

↓

Deployment

↓

Monitoring

↓

Maintenance

↓

Continuous Improvement
```

Production is an ongoing operational process rather than a one-time deployment.

---

# Build Once, Deploy Everywhere

Build the Docker image a single time.

```text
Source Code

↓

Docker Build

↓

Docker Image

↓

Container Registry

↓

Development

↓

Staging

↓

Production
```

The same image should move through every environment without rebuilding.

---

# Use Immutable Images

Never modify running containers.

Avoid

```text
Running Container

↓

SSH

↓

Manual Changes
```

Instead

```text
Code Change

↓

New Image

↓

Deploy New Container
```

Immutable deployments are easier to reproduce, test, and roll back.

---

# Use Official Images

Prefer trusted images maintained by official publishers.

Examples

```text
python:3.12-slim

nginx:1.28-alpine

postgres:17-alpine

redis:7.4-alpine
```

Benefits include:

- Security updates
- Better documentation
- Community support
- Predictable behavior

---

# Pin Image Versions

Good

```dockerfile
FROM python:3.12-slim
```

Avoid

```dockerfile
FROM python:latest
```

Pinned versions produce reproducible deployments and simplify rollbacks.

---

# Keep Images Small

Smaller images provide:

- Faster builds
- Faster deployments
- Reduced storage usage
- Smaller attack surface

Use:

- Multi-stage builds
- Minimal base images
- `.dockerignore`

---

# Run as a Non-root User

Avoid

```dockerfile
USER root
```

Use

```dockerfile
USER appuser
```

Running as a non-root user reduces the impact of security vulnerabilities.

---

# Keep Applications Stateless

Containers should never store important application state.

Good

```text
Application

↓

Database

↓

Persistent Storage
```

Avoid storing:

- Sessions
- Uploaded files
- Database files

inside application containers.

---

# Externalize Configuration

Configuration belongs outside the Docker image.

Examples

```text
Environment Variables

↓

Secret Manager

↓

Application
```

Never hardcode:

- Passwords
- API keys
- Database credentials

---

# Protect Secrets

Store secrets securely.

Good options include:

- Environment variables
- Docker Secrets
- Cloud secret managers

Never commit:

```text
.env.production

Private Keys

Certificates
```

to version control.

---

# Configure Health Checks

Every production service should expose a lightweight health endpoint.

```text
GET /health
```

Health checks allow Docker and deployment systems to verify that applications are functioning correctly.

---

# Configure Restart Policies

Recommended

```yaml
restart: unless-stopped
```

Restart policies improve application availability after unexpected failures.

---

# Limit Resource Usage

Configure resource limits.

Example

```yaml
mem_limit: 512m

cpus: 1.0

pids_limit: 200
```

Resource limits prevent a single container from affecting the stability of the host.

---

# Use Persistent Storage

Store persistent data in Docker volumes.

```text
Container

↓

Docker Volume

↓

Disk
```

Application containers should remain disposable.

---

# Secure Networking

Expose only required services.

Recommended architecture

```text
Internet

↓

Nginx

↓

Application

↓

Database
```

Databases and internal services should remain on private Docker networks.

---

# Centralize Logging

Applications should write logs to:

```text
stdout

stderr
```

Forward logs to a centralized logging platform for analysis and retention.

---

# Monitor Everything

Monitor:

- CPU usage
- Memory usage
- Response time
- Error rate
- Restart count
- Health checks
- Disk usage

Monitoring should be proactive rather than reactive.

---

# Automate Deployments

Manual deployments increase the risk of errors.

Preferred workflow

```text
Git Push

↓

CI Pipeline

↓

Build Image

↓

Deploy

↓

Health Check

↓

Production
```

Automation improves consistency and reliability.

---

# Implement Backup Strategies

Regularly back up:

- Databases
- Docker volumes
- Uploaded files
- Configuration

Test restoration procedures on a regular basis.

---

# Prepare Rollback Procedures

Every deployment should have a rollback plan.

```text
Deploy

↓

Health Check

↓

Failure

↓

Rollback

↓

Previous Version
```

Rollback should be fast and well documented.

---

# Continuously Update Images

Security vulnerabilities are discovered regularly.

Maintenance workflow

```text
Base Image Updated

↓

Rebuild

↓

Test

↓

Deploy
```

Keeping images current reduces security risk.

---

# Scan Images

Scan Docker images during the CI pipeline.

```text
Build Image

↓

Security Scan

↓

Deploy
```

Fix known vulnerabilities before deployment.

---

# Validate Before Deployment

Verify:

- Dockerfile
- Docker Compose
- Health checks
- Environment variables
- Secrets
- Resource limits
- Volumes
- Networks

Validation prevents configuration-related failures.

---

# Production Deployment Lifecycle

```text
Plan

↓

Develop

↓

Build

↓

Test

↓

Scan

↓

Deploy

↓

Monitor

↓

Backup

↓

Maintain
```

---

# Production Best Practices Checklist

| Category | Recommendation |
|----------|----------------|
| Docker Images | Official, minimal, version pinned |
| Dockerfile | Multi-stage build |
| User | Non-root |
| Configuration | Environment variables |
| Secrets | External secret management |
| Health Checks | Enabled |
| Restart Policies | `unless-stopped` |
| Storage | Docker volumes |
| Networking | Private Docker networks |
| Reverse Proxy | Nginx |
| Logging | stdout/stderr + centralized logging |
| Monitoring | Metrics and alerts |
| Resource Limits | CPU, memory, PID limits |
| Deployment | Automated CI/CD |
| Backup | Automated and tested |
| Rollback | Documented and tested |

---

# Common Mistakes

## Using Development Configurations

Development settings should never be deployed directly to production.

---

## Manual Container Changes

Production containers should always be replaced through deployments rather than modified manually.

---

## Ignoring Monitoring

Without monitoring, production issues are often discovered by users first.

---

## Keeping Secrets in Source Code

Secrets should always be stored outside the application and Docker image.

---

## No Disaster Recovery Plan

Every production system should have documented backup and recovery procedures.

---

# Production Readiness Workflow

```text
Secure

↓

Optimize

↓

Deploy

↓

Verify

↓

Monitor

↓

Scale

↓

Backup

↓

Recover

↓

Maintain
```

---

# Best Practices Summary

- Build once and deploy the same image everywhere.
- Use immutable, versioned Docker images.
- Keep images small and secure.
- Run containers as non-root users.
- Keep applications stateless.
- Store persistent data in Docker volumes.
- Protect secrets using external management.
- Configure health checks and restart policies.
- Limit CPU and memory usage.
- Expose only necessary ports.
- Centralize logging and monitoring.
- Automate deployments through CI/CD.
- Test backups and rollback procedures regularly.
- Continuously update and scan Docker images.

---

# Key Takeaways

- Production success depends as much on operational practices as it does on application code.
- Immutable images, stateless services, and automated deployments create predictable and reliable systems.
- Security, monitoring, logging, backups, and recovery should be built into every production deployment from the beginning.
- Following established best practices improves reliability, simplifies maintenance, and reduces operational risk.
- Together, these practices form the foundation of modern, production-ready Docker deployments used across real-world backend systems.