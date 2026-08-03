# Image Build Failures

## Overview

Building Docker images is a fundamental part of containerized application development. Image build failures can occur due to syntax errors, missing files, network issues, incorrect build contexts, dependency problems, or misconfigured Dockerfiles.

This guide covers the most common Docker image build failures, explains how to diagnose them, and provides practical solutions and preventive best practices.

---

## Common Image Build Issues

| Issue | Severity |
|--------|----------|
| Dockerfile not found | High |
| COPY/ADD file not found | High |
| Build context problems | High |
| Package installation failures | Medium |
| Permission denied during build | Medium |
| Invalid Dockerfile syntax | High |
| Base image cannot be pulled | High |
| Build cache issues | Medium |
| Out of disk space | High |
| Build hangs indefinitely | Medium |

---

# Issue 1: Dockerfile Not Found

## Symptoms

```text
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory
```

---

## Possible Causes

- Dockerfile does not exist.
- Wrong working directory.
- Incorrect filename.
- Incorrect `-f` option.

---

## How to Diagnose

Check current directory:

```bash
pwd
```

List files:

```bash
ls -la
```

Verify Dockerfile exists:

```bash
find . -name Dockerfile
```

---

## Solutions

Build from the correct directory:

```bash
docker build .
```

Specify Dockerfile manually:

```bash
docker build -f Dockerfile.dev .
```

---

## Prevention

- Keep Dockerfile in the project root.
- Use consistent naming.
- Verify the build context before building.

---

# Issue 2: COPY or ADD File Not Found

## Symptoms

```text
COPY failed: file not found
```

---

## Possible Causes

- File does not exist.
- Wrong path.
- File excluded by `.dockerignore`.
- Incorrect build context.

---

## How to Diagnose

Check project files:

```bash
ls -R
```

Review `.dockerignore`:

```bash
cat .dockerignore
```

---

## Solutions

Correct the file path:

```dockerfile
COPY requirements.txt .
```

Ensure the file is inside the build context.

---

## Prevention

- Keep paths relative to the build context.
- Regularly review `.dockerignore`.

---

# Issue 3: Build Context Problems

## Symptoms

```text
failed to compute cache key
```

or

```text
file not found in build context
```

---

## Possible Causes

- Building from the wrong directory.
- Files located outside the build context.

---

## How to Diagnose

Check current directory:

```bash
pwd
```

Verify build command:

```bash
docker build .
```

---

## Solutions

Run the build from the project root.

Avoid referencing files outside the build context.

---

## Prevention

Organize project files so that everything required is inside the build context.

---

# Issue 4: Package Installation Failures

## Symptoms

```text
Unable to locate package
```

or

```text
ERROR: Could not find a version that satisfies the requirement
```

---

## Possible Causes

- Invalid package name.
- Missing repositories.
- Network issues.
- Unsupported package version.

---

## How to Diagnose

Test package installation manually.

Verify internet connectivity.

---

## Solutions

Update package index:

```dockerfile
RUN apt-get update
```

Use valid package versions.

Verify package names.

---

## Prevention

- Pin dependency versions.
- Use official package repositories.
- Keep base images updated.

---

# Issue 5: Permission Denied During Build

## Symptoms

```text
permission denied
```

---

## Possible Causes

- Incorrect file permissions.
- Root-only files.
- Read-only directories.

---

## How to Diagnose

Check permissions:

```bash
ls -l
```

---

## Solutions

Modify permissions:

```bash
chmod +r filename
```

Use appropriate ownership:

```dockerfile
COPY --chown=app:app . .
```

---

## Prevention

Maintain proper project permissions.

---

# Issue 6: Invalid Dockerfile Syntax

## Symptoms

```text
unknown instruction
```

or

```text
parse error
```

---

## Possible Causes

- Typographical errors.
- Unsupported instruction.
- Incorrect formatting.

---

## How to Diagnose

Review the Dockerfile carefully.

Validate instructions against Docker documentation.

---

## Solutions

Correct syntax.

Ensure every instruction is valid.

---

## Prevention

Use syntax highlighting in your editor.

Review Dockerfile changes before committing.

---

# Issue 7: Base Image Cannot Be Pulled

## Symptoms

```text
pull access denied
```

or

```text
manifest unknown
```

---

## Possible Causes

- Incorrect image name.
- Incorrect tag.
- Private registry authentication.
- Network issues.

---

## How to Diagnose

Pull image manually:

```bash
docker pull python:3.12
```

---

## Solutions

Verify image name.

Login to registry:

```bash
docker login
```

---

## Prevention

Use official images whenever possible.

Pin image tags.

---

# Issue 8: Build Cache Problems

## Symptoms

Application changes are not reflected after rebuilding.

---

## Possible Causes

- Cached build layers.
- Incorrect Dockerfile order.

---

## How to Diagnose

Build without cache:

```bash
docker build --no-cache .
```

---

## Solutions

Rebuild without cache.

Optimize Dockerfile layer ordering.

---

## Prevention

Copy dependency files before application files to maximize cache efficiency.

---

# Issue 9: Out of Disk Space

## Symptoms

```text
no space left on device
```

---

## Possible Causes

- Old images.
- Dangling layers.
- Large build cache.

---

## How to Diagnose

Check Docker disk usage:

```bash
docker system df
```

---

## Solutions

Remove unused resources:

```bash
docker system prune
```

Remove unused images:

```bash
docker image prune
```

---

## Prevention

Regularly clean unused Docker resources.

---

# Issue 10: Build Hangs Indefinitely

## Symptoms

The build process never completes.

---

## Possible Causes

- Network timeout.
- Waiting for package manager.
- Infinite script execution.

---

## How to Diagnose

Build with detailed logs:

```bash
docker build --progress=plain .
```

---

## Solutions

Check internet connectivity.

Verify Dockerfile commands.

Avoid interactive commands during builds.

---

## Prevention

- Keep Dockerfiles deterministic.
- Avoid unnecessary downloads.
- Use reliable package mirrors.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| Build image | `docker build .` |
| Build without cache | `docker build --no-cache .` |
| Specify Dockerfile | `docker build -f Dockerfile.dev .` |
| View disk usage | `docker system df` |
| Remove unused resources | `docker system prune` |
| Pull base image | `docker pull <image>` |
| List images | `docker images` |
| Build with detailed logs | `docker build --progress=plain .` |

---

# Best Practices

- Use official base images.
- Keep Dockerfiles simple and readable.
- Minimize image layers where appropriate.
- Pin dependency versions.
- Use multi-stage builds for production images.
- Keep `.dockerignore` up to date.
- Regularly clean unused Docker resources.
- Test builds in a clean environment before deployment.

---

# Related Topics

- Docker Installation
- Dockerfile
- Docker Images
- Docker CLI
- Docker Compose
- Multi-stage Builds
- Docker Registry

---

## Key Takeaways

- Most image build failures are caused by incorrect Dockerfiles, missing files, dependency issues, or build context problems.
- Always verify the build context before running `docker build`.
- Use `--no-cache` when troubleshooting unexpected build behavior.
- Keep Dockerfiles clean, deterministic, and optimized for caching.
- Regular maintenance of images and build cache helps prevent disk space and performance issues.