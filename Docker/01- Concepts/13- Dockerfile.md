# Dockerfile

## Overview

A Dockerfile is a plain text file that contains a series of instructions used to build a Docker Image. It provides a repeatable and automated way to package an application together with its runtime, dependencies, configuration, and startup commands.

Instead of manually installing software and configuring environments, developers define every step in a Dockerfile. Docker then executes these instructions sequentially to create an immutable image.

Dockerfiles are one of the most important concepts in Docker because they enable reproducible builds, version-controlled infrastructure, automated deployments, and consistent application environments.

---

# What is a Dockerfile?

A Dockerfile is a build specification for creating Docker Images.

It describes:

- Base image
- Application code
- Dependencies
- Configuration
- Environment variables
- Startup commands

Docker reads the file from top to bottom and creates image layers as it processes each instruction.

---

# Dockerfile Build Process

```text
Application Source Code
          │
          ▼
      Dockerfile
          │
          ▼
     docker build
          │
          ▼
      Docker Image
          │
          ▼
   Docker Container
```

The Dockerfile serves as the blueprint for creating Docker Images.

---

# Dockerfile Architecture

A typical Dockerfile follows this structure.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

Each instruction performs a specific task during image creation.

---

# Common Dockerfile Instructions

| Instruction | Purpose |
|-------------|----------|
| FROM | Base image |
| WORKDIR | Working directory |
| COPY | Copy files |
| ADD | Copy files with additional features |
| RUN | Execute build commands |
| ENV | Environment variables |
| ARG | Build-time variables |
| EXPOSE | Document application ports |
| USER | Specify runtime user |
| CMD | Default startup command |
| ENTRYPOINT | Main executable |
| LABEL | Image metadata |

---

# FROM

The `FROM` instruction specifies the base image.

Example:

```dockerfile
FROM python:3.12-slim
```

Every Dockerfile starts with a base image unless using advanced multi-stage techniques.

---

# WORKDIR

Sets the working directory for subsequent instructions.

Example:

```dockerfile
WORKDIR /app
```

Instead of repeatedly changing directories, Docker executes future instructions inside this directory.

---

# COPY

Copies files from the build context into the image.

Example:

```dockerfile
COPY . .
```

COPY is the preferred instruction for copying local files.

---

# ADD

ADD performs everything COPY does but also supports:

- Extracting local tar archives
- Downloading remote URLs

Example:

```dockerfile
ADD archive.tar.gz /app
```

In most cases, COPY is recommended because it is simpler and more predictable.

---

# RUN

RUN executes commands during image creation.

Example:

```dockerfile
RUN pip install -r requirements.txt
```

The command executes while building the image, not when running the container.

---

# ENV

Defines environment variables.

Example:

```dockerfile
ENV DEBUG=False
```

These variables become available inside running containers.

---

# ARG

Defines variables available only during image build.

Example:

```dockerfile
ARG PYTHON_VERSION=3.12
```

Unlike ENV variables, ARG values are not automatically available at runtime.

---

# EXPOSE

Documents which ports the application listens on.

Example:

```dockerfile
EXPOSE 8000
```

EXPOSE does not publish ports.

It simply documents intended network usage.

---

# USER

Specifies which user runs the application.

Example:

```dockerfile
RUN useradd appuser

USER appuser
```

Running as a non-root user improves container security.

---

# CMD

Defines the default command executed when the container starts.

Example:

```dockerfile
CMD ["python", "app.py"]
```

Only one CMD instruction should exist in a Dockerfile.

---

# ENTRYPOINT

Defines the primary executable.

Example:

```dockerfile
ENTRYPOINT ["python"]
```

Arguments supplied during container startup are appended to ENTRYPOINT.

---

# CMD vs ENTRYPOINT

| CMD | ENTRYPOINT |
|------|------------|
| Default command | Main executable |
| Easily overridden | Usually remains fixed |
| Optional | Defines application behavior |

Both instructions can be combined.

---

# Dockerfile Layers

Each Dockerfile instruction creates an image layer.

```text
+---------------------------+
| Application Code          |
+---------------------------+
| Installed Dependencies    |
+---------------------------+
| Python Runtime            |
+---------------------------+
| Base Operating System     |
+---------------------------+
```

Docker reuses unchanged layers during future builds.

---

# Layer Caching

Docker caches layers to speed up builds.

Example:

```text
FROM python
      │
      ▼
Install Dependencies
      │
      ▼
Copy Application Code
```

If only the application code changes, Docker rebuilds only the final layer.

---

# Multi-Stage Builds

Multi-stage builds use multiple FROM instructions.

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
Final Image
```

Benefits:

- Smaller images
- Better security
- Faster deployments
- Reduced attack surface

---

# Build Context

The build context is the directory sent to Docker during image creation.

```text
Project Folder
│
├── Dockerfile
├── app.py
├── requirements.txt
└── src/
```

Everything inside the build context can be copied into the image.

---

# .dockerignore

`.dockerignore` excludes unnecessary files from the build context.

Example:

```text
.git
venv/
__pycache__/
*.log
.env
```

Benefits:

- Faster builds
- Smaller build context
- Improved security
- Better caching

---

# Dockerfile Build Workflow

```text
Dockerfile
     │
     ▼
Read Instructions
     │
     ▼
Execute Instructions
     │
     ▼
Create Image Layers
     │
     ▼
Store Docker Image
```

Docker executes instructions sequentially.

---

# Image Optimization

A well-designed Dockerfile should:

- Use slim base images
- Use multi-stage builds
- Combine related RUN instructions
- Remove temporary files
- Pin dependency versions
- Use `.dockerignore`
- Copy dependency files before application code
- Minimize unnecessary layers

These practices reduce image size and improve build performance.

---

# Dockerfile Security

Security recommendations include:

- Use official base images
- Avoid running as root
- Do not hardcode secrets
- Keep dependencies updated
- Scan images regularly
- Remove unnecessary tools
- Use minimal base images

A secure Dockerfile contributes to a secure production environment.

---

# Common Mistakes

Avoid:

- Using `latest` for production images
- Hardcoding credentials
- Installing unnecessary packages
- Running applications as root
- Large build contexts
- Ignoring `.dockerignore`
- Poor layer ordering

These mistakes increase image size, reduce security, and slow builds.

---

# Real-World Example

Typical Django application Dockerfile:

```text
Base Image
      │
      ▼
Install System Packages
      │
      ▼
Install Python Dependencies
      │
      ▼
Copy Django Project
      │
      ▼
Collect Static Files
      │
      ▼
Run Gunicorn
```

Every deployment follows the same reproducible process.

---

# Best Practices

- Use official base images.
- Prefer slim or distroless images.
- Keep images immutable.
- Use multi-stage builds.
- Minimize image size.
- Pin dependency versions.
- Run applications as non-root users.
- Keep Dockerfiles readable and maintainable.
- Store secrets outside the image.
- Optimize build cache usage.

---

# Related Topics

- Docker Images
- Docker Containers
- Docker Registries
- Docker Engine
- Docker Security
- Docker Best Practices

---

## Key Takeaways

- A Dockerfile defines the complete process for building a Docker Image.
- Docker executes Dockerfile instructions sequentially, creating reusable image layers.
- Proper Dockerfile design improves reproducibility, build performance, security, and image size.
- Features such as layer caching, multi-stage builds, and `.dockerignore` significantly optimize container builds.
- Writing efficient and secure Dockerfiles is a fundamental skill for modern backend development, DevOps, and cloud-native application deployment.