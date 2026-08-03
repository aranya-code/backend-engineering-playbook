# Docker Registries

## Overview

A Docker Registry is a centralized repository used to store, manage, distribute, and version Docker Images. Instead of manually copying images between machines, developers build an image once, push it to a registry, and allow any authorized system to pull the same image.

Docker Registries play a critical role in modern software development by enabling collaboration, CI/CD automation, cloud deployments, and production releases. They serve as the bridge between image creation and container deployment.

This chapter explains how Docker Registries work, their architecture, types, workflows, security considerations, and production best practices.

---

# What is a Docker Registry?

A Docker Registry is a service that stores Docker Images.

It enables developers to:

- Store images
- Share images
- Version images
- Distribute applications
- Deploy applications consistently

Without a registry, every server would need images copied manually.

---

# Why Do We Need Registries?

Imagine a development team with multiple environments.

```text
Developer Laptop

Docker Image
      │
      ▼
Production Server ?
```

Without a registry, images must be copied manually.

With a registry:

```text
Developer
     │
     ▼
Docker Registry
     │
     ▼
Development
Testing
Staging
Production
```

Every environment uses exactly the same image.

---

# Registry Architecture

```text
                   Docker Registry

            +----------------------+
            | Docker Registry      |
            +----------+-----------+
                       ▲
            Push       │      Pull
                       │
      +----------------+----------------+
      |                                 |
      ▼                                 ▼
Developer                      Production Server
      │                                 │
 Build Image                     Run Container
```

The registry acts as the central distribution point for Docker Images.

---

# Image Workflow

The complete image workflow looks like this.

```text
Application Code
        │
        ▼
Dockerfile
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
Docker Pull
        │
        ▼
Docker Container
```

Every production deployment follows this general workflow.

---

# Public Registries

Public registries are accessible over the Internet.

Examples include:

- Docker Hub
- GitHub Container Registry
- Microsoft Artifact Registry
- Quay.io

Public registries are commonly used for:

- Open-source software
- Community images
- Learning
- Development

---

# Private Registries

Organizations often use private registries.

Private registries store:

- Internal applications
- Proprietary software
- Enterprise services
- Production images

Access is restricted through authentication and authorization.

---

# Popular Docker Registries

| Registry | Typical Use Case |
|-----------|------------------|
| Docker Hub | Public & Private Images |
| Amazon Elastic Container Registry (ECR) | AWS Deployments |
| Azure Container Registry (ACR) | Azure Deployments |
| Google Artifact Registry | Google Cloud |
| GitHub Container Registry (GHCR) | GitHub Projects |
| Harbor | Self-hosted Enterprise Registry |
| Quay.io | Enterprise & Open Source |

---

# Docker Hub

Docker Hub is Docker's official registry.

Features:

- Public repositories
- Private repositories
- Official images
- Automated builds
- Image tags
- Team collaboration

Many developers use Docker Hub as their default registry.

---

# Repository Structure

A registry organizes images into repositories.

Example:

```text
backend-api

├── 1.0
├── 1.1
├── 1.2
├── 2.0
└── latest
```

Each repository stores multiple image versions.

---

# Image Tags

Tags identify specific image versions.

Example:

```text
backend-api:1.0

backend-api:1.1

backend-api:2.0
```

Tags allow applications to deploy predictable image versions.

---

# Why Versioning Matters

Versioning allows teams to:

- Roll back releases
- Track deployments
- Reproduce builds
- Maintain compatibility

Production deployments should use immutable version tags.

---

# Push Workflow

Publishing an image follows this process.

```text
Docker Image
      │
      ▼
Authentication
      │
      ▼
Push Image
      │
      ▼
Docker Registry
```

Once uploaded, the image becomes available to authorized users.

---

# Pull Workflow

Deployments retrieve images using this workflow.

```text
Production Server
        │
        ▼
Authenticate
        │
        ▼
Docker Registry
        │
        ▼
Download Image
        │
        ▼
Run Container
```

Only missing layers are downloaded, improving efficiency.

---

# Layer Storage

Registries store image layers separately.

```text
Docker Registry

├── Base Layer
├── Python Layer
├── Dependency Layer
└── Application Layer
```

If two images share identical layers, the registry stores them only once.

This saves storage and reduces network usage.

---

# Registry Authentication

Private registries require authentication.

Authentication protects:

- Images
- Repositories
- Organizations
- Deployment pipelines

Production environments should never allow anonymous access to private images.

---

# Registry Security

A secure registry should provide:

- Authentication
- Authorization
- TLS encryption
- Vulnerability scanning
- Image signing
- Access logging
- Role-based permissions

Security becomes increasingly important as organizations grow.

---

# Registry in CI/CD

Registries are central to modern deployment pipelines.

```text
Developer
     │
     ▼
Git Push
     │
     ▼
CI/CD Pipeline
     │
     ▼
Build Docker Image
     │
     ▼
Push Registry
     │
     ▼
Deploy Production
```

Every deployment uses the same tested image.

---

# Registry in Production

A production architecture typically looks like this.

```text
                 Git Repository
                        │
                        ▼
                 CI/CD Pipeline
                        │
                        ▼
                 Docker Registry
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 Development       Staging        Production
```

The registry becomes the single source of truth for application images.

---

# Common Misconceptions

### Docker Hub is required.

Incorrect.

Docker can use any OCI-compatible registry.

---

### Registries store containers.

Incorrect.

Registries store **Docker Images**, not running containers.

---

### Every image must be public.

Incorrect.

Many enterprise applications use private registries.

---

# Best Practices

- Use private registries for production applications.
- Tag images with immutable versions.
- Avoid relying on the `latest` tag in production.
- Enable vulnerability scanning.
- Sign images where appropriate.
- Remove unused image versions regularly.
- Restrict registry access using least-privilege principles.
- Integrate registry operations into CI/CD pipelines.

---

# Related Topics

- Docker Images
- Docker Containers
- Docker Engine
- Docker Security
- Dockerfile
- Docker Best Practices

---

## Key Takeaways

- Docker Registries provide centralized storage and distribution for Docker Images.
- Images are built once, stored in a registry, and pulled consistently across development, testing, and production environments.
- Registries support image versioning, authentication, access control, and integration with CI/CD pipelines.
- Public registries are useful for open-source software, while private registries protect enterprise applications.
- A secure, well-managed registry is a critical component of modern containerized application delivery.