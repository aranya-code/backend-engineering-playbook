# Hello World Container

## Overview

A minimal sample project that walks through the complete Docker workflow — writing a Dockerfile, building an image, and running a container. The application is a simple Python script that prints system information to the console.

This project is intentionally simple. The goal is to understand the **image → container** lifecycle, not to build a complex application.

---

## Project Structure

```text
01- Hello World Container/
├── Dockerfile          # Instructions to build the Docker image
├── .dockerignore       # Files excluded from the Docker build context
├── .env.example        # Sample environment variables
├── .gitignore          # Files excluded from version control
├── app/
│   └── app.py          # The Python application (entry point)
├── screenshots/        # (Optional) Output screenshots for the README
└── README.md           # This file
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running.

Verify with:

```bash
docker --version
```

---

## Quick Start

### 1. Build the Image

```bash
docker build -t hello-docker .
```

| Flag | Purpose |
|------|---------|
| `-t hello-docker` | Tags (names) the image so you can reference it easily |
| `.` | Sets the build context to the current directory |

### 2. Run the Container

```bash
docker run hello-docker
```

### 3. Expected Output

```text
============================================================
  Hello Docker
============================================================
  Current Time      : 2026-08-05 17:15:42
  Operating System  : Linux 6.5.0-44-generic
  Python Version    : 3.12.4
  Hostname          : f92a34493393
------------------------------------------------------------
  Congratulations!
  Your first Docker container is running successfully.
============================================================
```

> **Note:** The `Hostname` is the container's short ID — proof that the script is running inside Docker, not on your host machine.

---

## Passing Environment Variables

Override the app name using the `-e` flag:

```bash
docker run -e APP_NAME="My First Docker App" hello-docker
```

Or use an env file:

```bash
cp .env.example .env
docker run --env-file .env hello-docker
```

---

## Useful Commands

```bash
# List all local images (verify the build)
docker images | grep hello-docker

# List all containers (including stopped ones)
docker ps -a

# Remove the container after it exits automatically
docker run --rm hello-docker

# Remove the image when you no longer need it
docker rmi hello-docker
```

---

## What You Learn

| Concept | Where It Appears |
|---------|-----------------|
| Choosing a base image (`FROM`) | `Dockerfile` |
| Setting a working directory (`WORKDIR`) | `Dockerfile` |
| Copying files into the image (`COPY`) | `Dockerfile` |
| Defining the startup command (`CMD`) | `Dockerfile` |
| Excluding files from the build (`.dockerignore`) | `.dockerignore` |
| Passing environment variables (`-e`, `--env-file`) | `docker run` |
| The image → container lifecycle | `docker build` → `docker run` |

---

## Key Takeaways

- A Dockerfile is a recipe — `docker build` bakes it into an image, `docker run` starts a container from that image.
- Always use a `.dockerignore` to keep your build context small and avoid leaking secrets.
- Use `-e` or `--env-file` to inject configuration at runtime instead of hardcoding values.
- The container has its own hostname, filesystem, and network — it is an isolated environment.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*
