# Dockerfile

## Overview

A Dockerfile is a text file containing a series of instructions used to build a Docker image. It defines the application's environment, dependencies, configuration, and startup commands in a reproducible and automated manner.

Dockerfiles are among the most frequently discussed topics in Docker interviews because they directly impact image size, build speed, security, and production readiness.

This section contains beginner to advanced Dockerfile interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. What is a Dockerfile?

**Answer**

A Dockerfile is a text file containing instructions that Docker follows to build an image.

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

---

## 2. Why is a Dockerfile used?

**Answer**

A Dockerfile allows you to:

- Automate image creation
- Standardize application environments
- Version-control infrastructure
- Build reproducible images
- Simplify deployments

---

## 3. What command builds a Docker image?

**Answer**

```bash
docker build -t my-app .
```

---

## 4. What is the purpose of the `FROM` instruction?

**Answer**

`FROM` specifies the base image.

Example:

```dockerfile
FROM python:3.12-slim
```

Every Dockerfile begins with a `FROM` instruction unless using advanced multi-stage techniques that reference previous stages.

---

## 5. What is `WORKDIR`?

**Answer**

`WORKDIR` sets the working directory for subsequent instructions.

Example:

```dockerfile
WORKDIR /app
```

---

## 6. What is `COPY`?

**Answer**

`COPY` copies files from the build context into the image.

Example:

```dockerfile
COPY . .
```

---

## 7. What is `ADD`?

**Answer**

`ADD` copies files like `COPY` but also supports:

- Extracting local tar archives
- Fetching remote URLs (although downloading with `curl` or `wget` in a `RUN` instruction is generally preferred for clarity)

---

## 8. What is the difference between `COPY` and `ADD`?

**Answer**

| COPY | ADD |
|------|-----|
| Copies files only | Copies files and supports additional features |
| Simple and predictable | More functionality |
| Preferred in most cases | Use only when required |

---

## 9. What is `RUN`?

**Answer**

`RUN` executes commands during image build.

Example:

```dockerfile
RUN apt-get update
```

---

## 10. What is `CMD`?

**Answer**

`CMD` specifies the default command executed when the container starts.

Example:

```dockerfile
CMD ["python", "app.py"]
```

---

# Intermediate Interview Questions

## 11. What is `ENTRYPOINT`?

**Answer**

`ENTRYPOINT` defines the main executable for the container.

Unlike `CMD`, it is intended to remain fixed while allowing additional arguments to be appended at runtime.

Example:

```dockerfile
ENTRYPOINT ["python"]
```

---

## 12. What is the difference between `CMD` and `ENTRYPOINT`?

**Answer**

| CMD | ENTRYPOINT |
|------|------------|
| Default command | Main executable |
| Easily overridden | Intended to remain fixed |
| Provides default arguments | Defines container behavior |

---

## 13. What is `EXPOSE`?

**Answer**

`EXPOSE` documents the network ports the application listens on.

Example:

```dockerfile
EXPOSE 8000
```

It does **not** publish the port.

---

## 14. What is `ENV`?

**Answer**

`ENV` defines environment variables.

Example:

```dockerfile
ENV DEBUG=False
```

---

## 15. What is `ARG`?

**Answer**

`ARG` defines build-time variables.

Example:

```dockerfile
ARG PYTHON_VERSION=3.12
```

Unlike `ENV`, `ARG` is not automatically available at runtime.

---

## 16. What is `USER`?

**Answer**

`USER` specifies the user that executes subsequent instructions and the application.

Example:

```dockerfile
USER appuser
```

Using a non-root user is a production best practice.

---

## 17. What is `LABEL`?

**Answer**

`LABEL` stores metadata.

Example:

```dockerfile
LABEL maintainer="backend@example.com"
```

---

## 18. What is `.dockerignore`?

**Answer**

`.dockerignore` excludes unnecessary files from the build context.

Example:

```text
.git
venv/
__pycache__/
*.log
```

Benefits:

- Faster builds
- Smaller images
- Improved security

---

## 19. How do you view Docker image layers?

**Answer**

```bash
docker history image_name
```

---

## 20. What creates a Docker image layer?

**Answer**

Most Dockerfile instructions create a new read-only image layer.

Examples include:

- RUN
- COPY
- ADD

Docker reuses cached layers whenever possible.

---

# Advanced Interview Questions

## 21. What are multi-stage builds?

**Answer**

Multi-stage builds use multiple `FROM` instructions to separate build and runtime environments.

Benefits:

- Smaller images
- Better security
- Faster deployments
- Reduced attack surface

---

## 22. Why should frequently changing files be copied last?

**Answer**

Docker caches image layers.

Copying frequently changing files near the end of the Dockerfile maximizes cache reuse and speeds up builds.

---

## 23. How do you optimize a Dockerfile?

**Answer**

Common techniques include:

- Use slim or distroless base images.
- Use multi-stage builds.
- Combine related `RUN` commands.
- Remove temporary files.
- Use `.dockerignore`.
- Pin dependency versions.
- Copy dependency files before application source code to improve cache efficiency.

---

## 24. Why shouldn't secrets be stored in a Dockerfile?

**Answer**

Secrets become part of the image history and can potentially be extracted.

Instead, use:

- Environment variables
- Secret management services
- Docker Secrets (Swarm)

---

## 25. Why should Dockerfiles use official images?

**Answer**

Official images are generally:

- Better maintained
- Frequently patched
- Well documented
- More secure

---

# Scenario-Based Interview Questions

## 26. Your Docker image is 2 GB. How would you reduce it?

**Expected Answer**

- Use multi-stage builds.
- Switch to slim or distroless images.
- Remove unnecessary packages.
- Clean package caches.
- Use `.dockerignore`.
- Minimize dependencies.

---

## 27. Docker builds are taking too long. What would you investigate?

**Expected Answer**

- Layer ordering
- Build cache usage
- Large build context
- Dockerfile optimization
- Dependency installation
- Large base images

---

## 28. A rebuild installs every dependency again even though nothing changed. Why?

**Expected Answer**

The Dockerfile likely copies the entire application before installing dependencies.

A better approach is:

```dockerfile
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
```

This allows Docker to reuse the dependency installation layer when only application code changes.

---

## 29. A developer hardcoded database credentials into a Dockerfile. What would you recommend?

**Expected Answer**

Remove the credentials immediately.

Use:

- Environment variables
- Docker Secrets
- Secret management platforms

Rebuild and redeploy the image after rotating the credentials.

---

## 30. Your production container is running as the root user. How would you fix it?

**Expected Answer**

Create a dedicated application user and add:

```dockerfile
USER appuser
```

Test the application and redeploy the updated image.

---

# Production-Level Questions

## 31. What Dockerfile best practices do you follow?

**Answer**

- Use official base images.
- Use slim or distroless images.
- Use multi-stage builds.
- Minimize image layers where appropriate.
- Pin dependency versions.
- Run as a non-root user.
- Avoid embedding secrets.
- Keep images small and reproducible.

---

## 32. Why should Dockerfiles be deterministic?

**Answer**

Deterministic builds ensure that the same Dockerfile consistently produces the same image, improving reproducibility, testing, and deployment reliability.

---

## 33. What are common Dockerfile mistakes?

**Answer**

- Using `latest`
- Running as root
- Large base images
- Poor layer ordering
- Missing `.dockerignore`
- Hardcoded secrets
- Unnecessary packages
- Excessive image size

---

# Interview Tips

- Understand every commonly used Dockerfile instruction.
- Be able to explain Docker layer caching.
- Expect questions about image optimization and multi-stage builds.
- Know the differences between `CMD`, `ENTRYPOINT`, `COPY`, `ADD`, `ARG`, and `ENV`.
- Be prepared for scenario-based questions involving build performance, security, and production readiness.

---

## Key Takeaways

- Dockerfiles define reproducible instructions for building Docker images.
- Proper Dockerfile design improves build speed, reduces image size, and enhances security.
- Multi-stage builds, layer caching, and `.dockerignore` are key optimization techniques.
- Running containers as non-root users and avoiding embedded secrets are essential production practices.
- Mastering Dockerfile concepts is critical for backend engineering, DevOps, and cloud engineering interviews.