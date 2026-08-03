# Docker Images

## Overview

A Docker Image is a lightweight, read-only, immutable template used to create Docker containers. It contains everything required to run an application, including the application code, runtime, system libraries, dependencies, configuration files, and startup instructions.

Docker Images are one of the most fundamental concepts in Docker. Every container is created from an image, making images the building blocks of containerized applications.

Understanding how Docker Images work is essential for building efficient, secure, and production-ready applications.

---

# What is a Docker Image?

A Docker Image is a packaged application template.

It typically contains:

- Application source code
- Runtime (Python, Java, Node.js, etc.)
- Required libraries
- Application dependencies
- Configuration
- Environment variables
- Startup command

An image itself does **not** execute.

Instead, Docker creates one or more containers from the image.

---

# Docker Image Architecture

```text
                Docker Image

+-----------------------------------+
| Application Code                  |
+-----------------------------------+
| Runtime                           |
+-----------------------------------+
| Libraries                         |
+-----------------------------------+
| Dependencies                      |
+-----------------------------------+
| Configuration                     |
+-----------------------------------+
| Startup Command                   |
+-----------------------------------+

        │
        ▼

Docker Container
```

One image can create multiple independent containers.

---

# Image vs Container

A common analogy is:

| Docker Image | Docker Container |
|--------------|------------------|
| Blueprint | House |
| Class | Object |
| Read-only | Running instance |
| Immutable | Mutable |
| Template | Execution |

Think of an image as a blueprint and a container as the building constructed from it.

---

# Image Lifecycle

Docker Images follow a predictable lifecycle.

```text
Dockerfile
      │
      ▼
docker build
      │
      ▼
Docker Image
      │
      ▼
Docker Registry
      │
      ▼
docker pull
      │
      ▼
Docker Container
```

Images can be built locally or downloaded from a registry.

---

# How Images Are Built

Images are built using a Dockerfile.

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

Each Dockerfile instruction contributes to the final image.

---

# Docker Image Layers

One of Docker's most powerful features is its layered architecture.

```text
+-----------------------------+
| Application Code            |
+-----------------------------+
| Installed Dependencies      |
+-----------------------------+
| Python Runtime              |
+-----------------------------+
| Debian Slim Base Image      |
+-----------------------------+
```

Each instruction creates a separate image layer.

---

# Why Layers Are Important

Layers provide several benefits.

- Faster builds
- Smaller downloads
- Layer caching
- Efficient storage
- Layer reuse
- Faster deployments

If only the application code changes, Docker reuses previously built layers whenever possible.

---

# Layer Caching

Docker caches image layers during builds.

Example workflow:

```text
FROM python:3.12
        │
        ▼
Install Dependencies
        │
        ▼
Copy Application Code
```

If only the application code changes:

✔ Base image reused

✔ Dependency layer reused

✔ Only application layer rebuilt

This significantly reduces build times.

---

# Image IDs

Every image has a unique identifier.

Example:

```text
sha256:4f7c2b1d...
```

The Image ID uniquely identifies an image regardless of its name or tag.

---

# Image Tags

Tags identify different versions of an image.

Example:

```text
python:3.12

python:3.11

python:3.10

python:latest
```

A tag points to a specific image version.

---

# Why Tags Matter

Tags help developers:

- Version applications
- Roll back deployments
- Track releases
- Maintain reproducible builds

Production systems should use immutable version tags rather than relying on `latest`.

---

# Base Images

Every Docker image begins with a base image.

Example:

```dockerfile
FROM ubuntu:24.04
```

or

```dockerfile
FROM python:3.12-slim
```

The base image provides the starting filesystem for the new image.

---

# Parent and Child Images

Images inherit from other images.

Example:

```text
Ubuntu
    │
    ▼
Python
    │
    ▼
Django Application
```

Each child image builds upon its parent.

---

# Image Storage

Images are stored locally by Docker Engine.

```text
Docker Engine

├── Image A
├── Image B
├── Image C
```

Multiple containers can share the same image.

---

# Image Distribution

Images are distributed using container registries.

```text
Developer
     │
     ▼
Docker Build
     │
     ▼
Docker Image
     │
     ▼
Docker Registry
     │
     ▼
Production Server
     │
     ▼
docker pull
```

This enables consistent deployments across environments.

---

# Public vs Private Images

## Public Images

Examples:

- nginx
- redis
- postgres
- python

Available to everyone.

---

## Private Images

Used by organizations for:

- Internal applications
- Proprietary software
- Enterprise deployments

Private images require authentication.

---

# Image Size

Smaller images provide several advantages.

- Faster downloads
- Faster deployments
- Lower storage usage
- Reduced attack surface
- Improved CI/CD performance

Large images increase deployment time and consume additional storage.

---

# Image Optimization

Common optimization techniques include:

- Use slim base images
- Use distroless images where appropriate
- Multi-stage builds
- Remove unnecessary packages
- Clean package caches
- Minimize layers
- Use `.dockerignore`

---

# Image Security

Images should be treated as software artifacts.

Production recommendations include:

- Use official images
- Scan images regularly
- Keep dependencies updated
- Avoid hardcoded secrets
- Sign images where appropriate
- Remove unnecessary tools

---

# Common Misconceptions

### Images are Containers.

Incorrect.

Images are templates.

Containers are running instances.

---

### Images can change after creation.

Incorrect.

Docker Images are immutable.

Changes create a new image rather than modifying the existing one.

---

### Every container stores its own image.

Incorrect.

Multiple containers can share the same image layers.

---

# Best Practices

- Use official base images.
- Pin image versions instead of using `latest`.
- Keep images as small as possible.
- Scan images for vulnerabilities.
- Remove unnecessary packages.
- Use multi-stage builds.
- Version images consistently.
- Store images in a trusted registry.

---

# Related Topics

- Docker Engine
- Docker Containers
- Docker Registries
- Dockerfile
- Docker Storage Drivers
- Docker Security

---

## Key Takeaways

- Docker Images are immutable, read-only templates used to create containers.
- Images contain everything an application needs to run, including code, runtime, dependencies, and configuration.
- Docker Images are built from Dockerfiles and organized into reusable layers that improve build performance and storage efficiency.
- Tags enable versioning, while registries provide centralized storage and distribution of images.
- Building small, secure, and well-versioned images is a fundamental best practice for reliable containerized applications.