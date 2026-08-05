# Production Dockerfile

## Overview

A Dockerfile that works during development is not necessarily suitable for production.

Production Dockerfiles should produce images that are:

- Small
- Secure
- Reproducible
- Fast to build
- Easy to maintain

The Dockerfile is one of the most important components of a production deployment because it defines exactly how the application is packaged and executed.

---

# Goals of a Production Dockerfile

A production Dockerfile should:

- Minimize image size
- Reduce attack surface
- Build quickly
- Use official images
- Run as a non-root user
- Support health checks
- Produce reproducible builds
- Avoid unnecessary files

---

# Development vs Production

| Development | Production |
|-------------|------------|
| Convenience | Security |
| Debugging | Performance |
| Large images | Small images |
| Frequent rebuilds | Stable releases |
| Root user (sometimes) | Non-root user |
| Source code mounts | Immutable images |

---

# Production Build Process

```text
Source Code

↓

Dockerfile

↓

Build

↓

Docker Image

↓

Registry

↓

Production Server

↓

Running Container
```

---

# Example Production Dockerfile

```dockerfile
# ==========================================
# Stage 1 - Builder
# ==========================================

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


# ==========================================
# Stage 2 - Runtime
# ==========================================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN groupadd --system appgroup \
 && useradd \
    --system \
    --gid appgroup \
    --create-home \
    appuser

COPY app/ .

COPY scripts/start.sh /start.sh

RUN chmod +x /start.sh \
 && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["/start.sh"]
```

---

# Why Multi-Stage Builds?

Without multi-stage builds:

```text
Application

↓

Compiler

↓

Development Tools

↓

Final Image
```

The final image contains unnecessary software.

With multi-stage builds:

```text
Builder Image

↓

Install Dependencies

↓

Copy Runtime Files

↓

Small Runtime Image
```

Benefits:

- Smaller images
- Faster downloads
- Better security
- Lower storage requirements

---

# Choose the Right Base Image

Good choices:

```dockerfile
python:3.12-slim

nginx:1.28-alpine

redis:7.4-alpine

postgres:17-alpine
```

Avoid:

```dockerfile
python:latest
```

Always pin image versions to ensure reproducible builds.

---

# Keep Images Small

Only install required packages.

Good

```dockerfile
RUN apt-get update \
 && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*
```

Avoid installing development tools unless they are needed during the build stage.

---

# Layer Optimization

Docker builds images layer by layer.

Efficient order:

```text
Base Image

↓

System Packages

↓

Python Dependencies

↓

Application Code
```

This improves build caching because application code changes more frequently than dependencies.

---

# Copy Dependencies First

Instead of:

```dockerfile
COPY . .

RUN pip install -r requirements.txt
```

Prefer:

```dockerfile
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
```

This allows Docker to reuse cached dependency layers when only the application code changes.

---

# Use .dockerignore

Exclude unnecessary files from the build context.

Example

```text
.git

.env

venv/

__pycache__/

.pytest_cache/

README.md

screenshots/
```

Benefits:

- Faster builds
- Smaller build context
- Improved security

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

Benefits:

- Reduced attack surface
- Better isolation
- Improved security

---

# Environment Variables

Store configuration outside the image.

Example

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1
```

Application configuration should come from environment variables at runtime rather than being hardcoded into the image.

---

# Use Exec Form for CMD

Good

```dockerfile
CMD ["gunicorn","main:app"]
```

Avoid

```dockerfile
CMD gunicorn main:app
```

The exec form ensures proper signal handling and graceful container shutdown.

---

# Expose Required Ports

Example

```dockerfile
EXPOSE 8000
```

`EXPOSE` documents the intended listening port but does not publish it to the host.

---

# Keep Secrets Out of Images

Never copy:

- `.env`
- SSH keys
- API keys
- Passwords
- Certificates

Instead, provide them at runtime through environment variables or secret management systems.

---

# Minimize Installed Packages

Only install what the application requires.

Avoid:

- Editors
- Compilers (runtime stage)
- Debugging utilities
- Package managers not needed at runtime

Smaller images have fewer vulnerabilities and download faster.

---

# Image Build Workflow

```text
Source Code

↓

Dockerfile

↓

Build

↓

Image

↓

Registry

↓

Production
```

---

# Common Mistakes

## Using Latest Tags

Bad

```dockerfile
FROM python:latest
```

Good

```dockerfile
FROM python:3.12-slim
```

---

## Running as Root

Avoid

```dockerfile
USER root
```

---

## Copying Everything

Bad

```dockerfile
COPY . .
```

without a proper `.dockerignore` file.

---

## Keeping Build Tools

Build tools belong in the builder stage, not the runtime image.

---

## Hardcoding Secrets

Never include credentials inside the Docker image.

---

# Production Dockerfile Checklist

Before building:

- Official base image
- Version pinned
- Multi-stage build
- Minimal packages
- Non-root user
- `.dockerignore` configured
- Exec form CMD
- No secrets
- Runtime dependencies only
- Health check supported

---

# Best Practices

- Use multi-stage builds.
- Keep runtime images minimal.
- Pin image versions.
- Run containers as non-root users.
- Optimize Docker layer caching.
- Exclude unnecessary files with `.dockerignore`.
- Use the exec form for `CMD`.
- Keep secrets outside the image.
- Rebuild images instead of modifying running containers.

---

# Key Takeaways

- A production Dockerfile should prioritize security, efficiency, and reproducibility over development convenience.
- Multi-stage builds create smaller, cleaner runtime images by excluding build-time tools.
- Layer optimization and a well-configured `.dockerignore` significantly improve build performance.
- Running containers as non-root users and avoiding embedded secrets are fundamental security practices.
- A well-designed Dockerfile is the foundation of reliable production deployments and efficient CI/CD pipelines.