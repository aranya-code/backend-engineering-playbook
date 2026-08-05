# Image Optimization

## Overview

Docker images are downloaded, stored, transferred, and deployed every time an application is built or released. Large images consume more storage, take longer to build, increase deployment times, and expose a larger attack surface.

Image optimization is the process of creating Docker images that are small, secure, efficient, and reproducible without sacrificing functionality.

Optimizing images leads to:

- Faster builds
- Faster deployments
- Lower bandwidth usage
- Better security
- Lower storage costs
- Improved CI/CD performance

---

# Why Image Optimization Matters

Without optimization:

```text
Large Image

↓

Slow Build

↓

Slow Push

↓

Slow Pull

↓

Slow Deployment
```

With optimization:

```text
Small Image

↓

Fast Build

↓

Fast Push

↓

Fast Pull

↓

Fast Deployment
```

---

# Goals of Image Optimization

A production Docker image should be:

- Small
- Secure
- Reproducible
- Efficient
- Easy to maintain

---

# Image Optimization Workflow

```text
Application

↓

Dockerfile

↓

Optimization

↓

Smaller Image

↓

Registry

↓

Production
```

---

# Choose the Right Base Image

The base image has the greatest impact on image size.

Recommended:

```dockerfile
FROM python:3.12-slim
```

or

```dockerfile
FROM python:3.12-alpine
```

Avoid

```dockerfile
FROM ubuntu

FROM debian
```

unless the application genuinely requires them.

---

# Official Images

Always prefer official Docker images.

Examples

```text
python:3.12-slim

nginx:1.28-alpine

redis:7.4-alpine

postgres:17-alpine
```

Benefits include:

- Security updates
- Community support
- Smaller size
- Regular maintenance

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

Pinned versions make builds predictable and reproducible.

---

# Use Multi-Stage Builds

Without multi-stage builds

```text
Builder

↓

Compiler

↓

Dependencies

↓

Final Image
```

Final image contains unnecessary tools.

With multi-stage builds

```text
Builder Stage

↓

Compile

↓

Copy Runtime Files

↓

Runtime Image
```

Only runtime files remain.

---

# Install Only Required Packages

Good

```dockerfile
RUN apt-get update \
 && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*
```

Avoid installing:

- Editors
- Debuggers
- Build tools
- Documentation packages

inside the runtime image.

---

# Clean Package Cache

Bad

```dockerfile
RUN apt-get update

RUN apt-get install -y curl
```

Better

```dockerfile
RUN apt-get update \
 && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*
```

Removing package metadata reduces image size.

---

# Optimize Docker Layers

Docker caches layers.

Good order

```text
Base Image

↓

System Packages

↓

Dependencies

↓

Application Code
```

Benefits:

- Faster rebuilds
- Better cache reuse
- Reduced CI build times

---

# Copy Requirements First

Instead of

```dockerfile
COPY . .

RUN pip install -r requirements.txt
```

Use

```dockerfile
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
```

Application changes no longer invalidate dependency layers.

---

# Use .dockerignore

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

- Smaller build context
- Faster builds
- Better security

---

# Remove Temporary Files

Temporary build files increase image size.

Example

```dockerfile
RUN rm -rf /tmp/*
```

Remove:

- Package cache
- Temporary files
- Build artifacts
- Download archives

---

# Avoid Duplicate Files

Avoid copying the same files multiple times.

Bad

```dockerfile
COPY . .

COPY app/ .
```

Only copy what the application needs.

---

# Keep Images Immutable

Do not modify running containers.

Instead

```text
Code Change

↓

New Image

↓

New Container
```

Immutable images simplify deployments and rollbacks.

---

# Run as Non-root

Avoid

```dockerfile
USER root
```

Use

```dockerfile
USER appuser
```

Smaller attack surface.

Better security.

---

# Remove Build Dependencies

Builder image

```text
Compiler

Build Tools

Libraries
```

Runtime image

```text
Application

Runtime Libraries
```

Build dependencies should never remain in the final image.

---

# Inspect Image Size

View images

```bash
docker images
```

Example

```text
REPOSITORY

TAG

SIZE

myapp

1.0.0

158MB
```

---

# Inspect Image Layers

Command

```bash
docker history myapp:1.0.0
```

Output shows:

- Layer size
- Build instructions
- Image history

Useful for identifying unnecessary layers.

---

# Scan Images

Regularly scan images for vulnerabilities.

Typical workflow

```text
Docker Image

↓

Security Scan

↓

Known Vulnerabilities

↓

Update Dependencies

↓

Rebuild
```

Scanning should be part of the CI/CD pipeline.

---

# Compare Image Sizes

| Image | Approximate Size |
|---------|----------------:|
| Ubuntu | Large |
| Debian Slim | Medium |
| Python Slim | Small |
| Alpine | Very Small |

Smaller is not always better.

Choose an image that balances compatibility, security, and size.

---

# Build Optimization Flow

```text
Source Code

↓

Dockerfile

↓

Multi-stage Build

↓

Small Runtime Image

↓

Registry

↓

Production
```

---

# Common Mistakes

## Using Large Base Images

Large base images increase:

- Download time
- Storage usage
- Attack surface

---

## Installing Everything

Only install packages required by the application.

---

## Keeping Build Tools

Compilers belong in the builder stage.

Not the runtime image.

---

## Missing .dockerignore

Large build contexts slow every Docker build.

---

## Using Latest Tags

Avoid

```dockerfile
FROM python:latest
```

Always pin versions.

---

## Not Cleaning Package Cache

Leaving package metadata inside images wastes storage.

---

# Image Optimization Checklist

Before production:

- Official base image
- Version pinned
- Multi-stage build
- Runtime image only
- Package cache removed
- Temporary files removed
- Non-root user
- `.dockerignore` configured
- Dependencies optimized
- Image scanned
- Image size reviewed

---

# Best Practices

- Use official, minimal base images.
- Pin image versions.
- Build runtime images with multi-stage builds.
- Remove unnecessary packages and caches.
- Optimize Docker layer ordering.
- Exclude unnecessary files using `.dockerignore`.
- Scan images for vulnerabilities regularly.
- Review image size as part of every release.
- Rebuild images when base images receive security updates.

---

# Key Takeaways

- Smaller Docker images build faster, deploy faster, and reduce storage and bandwidth requirements.
- Multi-stage builds are one of the most effective techniques for optimizing production images.
- Proper layer ordering and a well-configured `.dockerignore` significantly improve build performance.
- Image optimization is not only about size—it also improves security by reducing unnecessary software and attack surface.
- Regular image reviews, vulnerability scanning, and dependency updates are essential parts of maintaining production-ready Docker images.