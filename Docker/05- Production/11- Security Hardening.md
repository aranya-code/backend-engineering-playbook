# Security Hardening

## Overview

Containers provide process isolation, but they are **not security boundaries** by themselves. A poorly configured container can expose sensitive data, consume excessive system resources, or provide an attacker with unnecessary privileges.

Security hardening is the process of reducing the attack surface of a Docker deployment by following secure configuration practices.

A secure Docker deployment focuses on:

- Least privilege
- Minimal attack surface
- Secure image management
- Secure networking
- Secret protection
- Runtime protection
- Continuous updates

---

# Security Layers

```text
Application

↓

Docker Image

↓

Container

↓

Docker Engine

↓

Host Operating System

↓

Cloud / Physical Server
```

Every layer should be secured.

---

# Principle of Least Privilege

Containers should receive only the permissions they actually require.

Avoid:

```text
Full Host Access
```

Prefer:

```text
Only Required Permissions
```

Limiting permissions reduces the impact of compromised containers.

---

# Run Containers as Non-root

Avoid

```dockerfile
USER root
```

Use

```dockerfile
RUN groupadd --system appgroup \
 && useradd --system \
    --gid appgroup \
    appuser

USER appuser
```

Benefits

- Reduced privilege escalation
- Better filesystem protection
- Lower attack surface

---

# Use Official Images

Always prefer trusted images.

Good examples

```text
python:3.12-slim

nginx:1.28-alpine

postgres:17-alpine

redis:7.4-alpine
```

Avoid downloading random community images without reviewing their source and maintenance status.

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

Pinned versions provide reproducible deployments and reduce unexpected changes.

---

# Use Minimal Images

Smaller images contain:

- Fewer packages
- Fewer vulnerabilities
- Smaller attack surface

Example

```text
Ubuntu

↓

Many Packages

↓

Larger Attack Surface

--------------------------

Python Slim

↓

Fewer Packages

↓

Smaller Attack Surface
```

---

# Use Multi-Stage Builds

Builder

```text
Compiler

↓

Dependencies

↓

Application
```

Runtime

```text
Application

↓

Runtime Libraries
```

Development tools should never remain in the runtime image.

---

# Protect Secrets

Never include:

- API keys
- Passwords
- SSH keys
- Certificates
- Tokens

inside:

```text
Dockerfile

Git Repository

Docker Image
```

Use:

- Environment variables
- Docker Secrets
- Secret management systems

---

# Secure Environment Files

Example

```text
.env.production
```

Do not commit:

```text
.env

.env.production
```

Only commit:

```text
.env.example
```

---

# Limit Container Capabilities

Linux containers receive capabilities.

Remove unnecessary ones.

Example

```yaml
cap_drop:

  - ALL
```

Add back only required capabilities.

This follows the principle of least privilege.

---

# Prevent Privilege Escalation

Example

```yaml
security_opt:

  - no-new-privileges:true
```

This prevents processes from gaining additional privileges after startup.

---

# Use Read-Only Filesystems

When possible

```yaml
read_only: true
```

Benefits

- Protects application files
- Prevents unauthorized modifications
- Reduces persistence opportunities for attackers

Writable storage should be limited to mounted volumes.

---

# Restrict Published Ports

Avoid

```yaml
ports:

  - "5432:5432"
```

Preferred

```yaml
expose:

  - "5432"
```

Only publish ports that external users must access.

---

# Use Private Networks

```text
Internet

↓

Nginx

↓

Application

↓

Database
```

Database containers should remain inaccessible from the public internet.

---

# Enable Health Checks

Healthy containers are easier to monitor.

Example

```dockerfile
HEALTHCHECK \
CMD curl --fail http://localhost:8000/health || exit 1
```

Health checks improve operational reliability.

---

# Keep Images Updated

Regularly rebuild images using updated base images.

Workflow

```text
Security Update

↓

Rebuild Image

↓

Deploy New Version
```

Avoid using outdated images for long periods.

---

# Scan Images

Image scanning identifies known vulnerabilities.

```text
Docker Image

↓

Security Scanner

↓

Report

↓

Fix

↓

Rebuild
```

Scanning should be integrated into CI/CD.

---

# Secure Volume Mounts

Prefer

```yaml
volumes:

  - app_data:/data
```

Avoid mounting sensitive host directories unless absolutely necessary.

Example to avoid

```yaml
volumes:

  - /:/host
```

---

# Restrict Container Resources

Example

```yaml
mem_limit: 512m

cpus: 1.0

pids_limit: 200
```

Resource limits reduce denial-of-service risks caused by runaway processes.

---

# Log Security Events

Monitor:

- Authentication failures
- Unexpected restarts
- Permission errors
- Failed health checks
- Container crashes

Logs should be forwarded to a centralized logging system whenever possible.

---

# Secure Docker Socket

Avoid mounting:

```text
/var/run/docker.sock
```

inside containers unless there is a well-understood operational requirement.

A container with unrestricted access to the Docker socket can often control other containers on the host.

---

# Security Workflow

```text
Build

↓

Scan

↓

Deploy

↓

Monitor

↓

Patch

↓

Rebuild
```

Security is a continuous process rather than a one-time task.

---

# Common Mistakes

## Running as Root

Root containers increase the potential impact of security vulnerabilities.

---

## Hardcoding Secrets

Secrets should never appear in source code or Docker images.

---

## Using Latest Tags

Pinned versions provide predictable and auditable deployments.

---

## Publishing Every Port

Only expose services that require external access.

---

## Ignoring Updates

Outdated base images may contain publicly known vulnerabilities.

---

## Mounting the Docker Socket

Containers should not receive unrestricted Docker Engine access unless absolutely necessary.

---

# Production Security Checklist

Before deployment:

- Official base image used
- Image version pinned
- Multi-stage build implemented
- Non-root user configured
- Secrets externalized
- Environment files protected
- Health checks enabled
- Published ports minimized
- Private Docker network configured
- Resource limits configured
- Image vulnerability scan completed
- Base image updated
- Docker socket not exposed

---

# Best Practices

- Follow the principle of least privilege.
- Run containers as non-root users.
- Use minimal, official base images.
- Remove unnecessary Linux capabilities.
- Keep secrets outside images.
- Enable `no-new-privileges`.
- Restrict published ports.
- Scan images regularly for vulnerabilities.
- Keep base images updated.
- Review container permissions periodically.

---

# Key Takeaways

- Docker security is achieved through multiple layers rather than a single configuration setting.
- Running containers as non-root users, minimizing capabilities, and using trusted images significantly reduce the attack surface.
- Secrets should always be managed outside Docker images and source code.
- Secure networking, resource limits, and regular vulnerability scanning are essential components of a production deployment.
- Security hardening is an ongoing process that includes continuous monitoring, patching, rebuilding, and reviewing container configurations.