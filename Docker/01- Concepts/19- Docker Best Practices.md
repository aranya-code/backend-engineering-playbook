# Docker Best Practices

## Overview

Docker makes it easy to package and deploy applications, but simply running containers is not enough to build reliable production systems. Poorly designed images, insecure containers, excessive resource consumption, improper networking, and weak deployment strategies can lead to unstable and vulnerable applications.

Docker Best Practices are a collection of proven guidelines that improve performance, security, maintainability, scalability, and operational reliability. Following these practices helps teams build production-ready containerized applications that are easier to deploy, monitor, and maintain.

This chapter consolidates the most important recommendations for developing and operating Docker applications.

---

# Why Best Practices Matter

Following Docker best practices helps organizations:

- Improve security
- Reduce image size
- Speed up deployments
- Improve build performance
- Increase application reliability
- Simplify maintenance
- Reduce infrastructure costs
- Improve scalability

Good practices become increasingly important as applications grow.

---

# Build Small Images

Smaller images provide several advantages.

Benefits include:

- Faster downloads
- Faster deployments
- Lower storage usage
- Better caching
- Reduced attack surface
- Faster CI/CD pipelines

Prefer lightweight base images whenever possible.

Examples:

- Alpine Linux (where compatible)
- Debian Slim
- Distroless Images

---

# Use Official Base Images

Prefer images maintained by trusted organizations.

Examples include:

- Python Official Image
- Node.js Official Image
- PostgreSQL Official Image
- Redis Official Image
- Nginx Official Image

Official images are regularly updated and receive security patches.

---

# Pin Image Versions

Avoid using:

```text
latest
```

Instead use versioned tags.

Example:

```text
python:3.12-slim

postgres:16

redis:7
```

Version pinning provides predictable deployments and simplifies rollbacks.

---

# Use Multi-Stage Builds

Separate build and runtime environments.

```text
Build Stage
      │
Compile Application
      │
      ▼
Runtime Stage
      │
Copy Artifacts
      │
      ▼
Small Production Image
```

Benefits:

- Smaller images
- Better security
- Faster deployment
- Reduced attack surface

---

# Optimize Dockerfile Layer Order

Docker caches layers.

Place stable instructions first.

Example:

```text
FROM

Install Dependencies

Copy Application Code
```

Application code changes most frequently.

Keeping dependency installation earlier maximizes cache reuse.

---

# Use .dockerignore

Exclude unnecessary files.

Example:

```text
.git
.env
venv/
node_modules/
__pycache__/
*.log
```

Benefits:

- Faster builds
- Smaller build context
- Better security

---

# Run Containers as Non-Root

Avoid:

```text
Root User
```

Prefer:

```text
Application User
```

Running as a non-root user limits the impact of security vulnerabilities.

---

# Keep Containers Stateless

Containers should not permanently store application data.

Instead store data in:

- Docker Volumes
- Databases
- Object Storage
- Shared Network Storage

Stateless containers are easier to replace and scale.

---

# Use Docker Volumes

Store persistent data outside containers.

Examples:

- PostgreSQL data
- Redis persistence
- Uploaded files
- Shared assets

Never rely on a container's writable layer for critical data.

---

# One Responsibility Per Container

Each container should perform one primary responsibility.

Example:

```text
Good

Nginx

API

Redis

PostgreSQL
```

Avoid:

```text
Bad

One Container

Nginx

API

Database

Redis
```

This improves scalability, maintainability, and fault isolation.

---

# Use Environment Variables

Avoid hardcoding configuration.

Instead configure:

- Database credentials
- API URLs
- Feature flags
- Debug settings

This allows the same image to run across different environments.

---

# Never Store Secrets in Images

Do not embed:

- Passwords
- API keys
- Access tokens
- Certificates

Use:

- Docker Secrets
- Cloud Secret Managers
- External secret management solutions

---

# Configure Health Checks

Health checks allow Docker and orchestration platforms to detect unhealthy containers.

Typical workflow:

```text
Running
     │
Health Check
     │
Healthy?
 │         │
 ▼         ▼
Yes       Restart
```

Health checks improve application reliability.

---

# Configure Restart Policies

Restart policies improve availability.

Examples:

- on-failure
- unless-stopped
- always

Production applications should rarely use the default behavior.

---

# Limit Resource Usage

Set limits for:

- CPU
- Memory
- Process count

Benefits:

- Prevent noisy neighbors
- Improve cluster stability
- Protect the host system

---

# Use Private Networks

Only expose required services.

Example:

```text
Internet
     │
     ▼
Nginx
     │
     ▼
API
     │
     ▼
Database
```

Databases should remain on private networks whenever possible.

---

# Log to stdout and stderr

Applications should write logs to:

```text
stdout

stderr
```

Docker automatically collects these streams.

Avoid writing application logs directly inside containers.

---

# Scan Images Regularly

Use vulnerability scanning during CI/CD.

Scanning detects:

- Known CVEs
- Outdated packages
- Vulnerable dependencies
- Security issues

Security scanning should occur before deployment.

---

# Monitor Containers

Production monitoring should include:

- CPU usage
- Memory usage
- Disk usage
- Network traffic
- Restart count
- Health checks
- Log volume

Monitoring improves operational visibility.

---

# Remove Unused Resources

Unused resources consume disk space.

Regularly remove:

- Unused images
- Dangling images
- Stopped containers
- Unused volumes
- Unused networks
- Build cache

Routine cleanup keeps Docker hosts healthy.

---

# Use CI/CD Pipelines

Automate:

```text
Source Code
      │
      ▼
Build Image
      │
      ▼
Run Tests
      │
      ▼
Scan Image
      │
      ▼
Push Registry
      │
      ▼
Deploy
```

Automation improves consistency and reduces manual errors.

---

# Version Everything

Version:

- Images
- Compose files
- Infrastructure
- Configuration

Immutable versioning enables safe rollbacks and reproducible deployments.

---

# Production Architecture

```text
                  Internet
                       │
                       ▼
                Load Balancer
                       │
                       ▼
                 Reverse Proxy
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      API 1       API 2       API 3
          │            │            │
          └────────────┼────────────┘
                       ▼
          Private Docker Network
             │               │
             ▼               ▼
       PostgreSQL        Redis
             │
             ▼
      Docker Volumes
```

This architecture demonstrates several best practices:

- One service per container
- Private backend network
- Persistent storage
- Horizontal scaling
- Reverse proxy
- Load balancing

---

# Common Mistakes

Avoid:

- Using latest tags
- Running as root
- Hardcoding secrets
- Storing database files inside containers
- Large images
- Ignoring health checks
- Ignoring resource limits
- Exposing unnecessary ports
- Manual production deployments

---

# Production Checklist

Before deploying:

- Use official images
- Use versioned tags
- Scan images
- Configure health checks
- Configure restart policies
- Store secrets securely
- Enable monitoring
- Enable centralized logging
- Back up persistent data
- Keep images small
- Keep containers stateless

---

# Related Topics

- Docker Security
- Docker Images
- Docker Volumes
- Docker Networking
- Docker Compose
- Docker Swarm
- Docker Logging Drivers

---

## Key Takeaways

- Docker best practices improve security, performance, scalability, maintainability, and operational reliability.
- Small, versioned, immutable images combined with multi-stage builds produce faster and more secure deployments.
- Containers should remain stateless, run as non-root users, and store persistent data in Docker Volumes.
- Health checks, restart policies, centralized logging, monitoring, and automated CI/CD pipelines are essential for production environments.
- Consistently applying these practices results in robust, maintainable, and production-ready containerized applications.