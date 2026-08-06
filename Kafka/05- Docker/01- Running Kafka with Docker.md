# Running Kafka with Docker

## Overview

Installing Apache Kafka manually requires downloading binaries, configuring brokers, installing Java, and managing dependencies. While this approach is useful for understanding Kafka internals, it is not the preferred method for local development.

Today, most developers run Kafka using **Docker**, allowing a complete Kafka environment to be started with a few commands. Docker provides:

- Quick setup
- Easy cleanup
- Consistent environments
- Isolation from the host machine
- Support for multi-broker clusters

Whether you're learning Kafka, developing microservices, or testing distributed systems, Docker is the fastest and most convenient way to get started.

---

# Why Run Kafka with Docker?

Without Docker:

```text
Install Java

↓

Download Kafka

↓

Configure Broker

↓

Start ZooKeeper/KRaft

↓

Start Kafka

↓

Configure Networking
```

With Docker:

```text
docker run

↓

Kafka Ready
```

Docker dramatically simplifies local development.

---

# Benefits of Docker

Running Kafka in Docker offers several advantages:

- No manual installation
- Platform independent
- Easy version switching
- Fast environment setup
- Easy cleanup
- Consistent development environment
- Ideal for CI/CD pipelines

---

# Docker Architecture

```text
Host Machine

│

├── Docker Engine
│
├── Kafka Container
│
└── Kafka UI Container
```

Kafka runs as an isolated container while still exposing ports to the host.

---

# Prerequisites

Before running Kafka with Docker, install:

- Docker Desktop (Windows/macOS)
- Docker Engine (Linux)

Verify installation:

```bash
docker --version
```

Example:

```text
Docker version 28.x.x
```

---

Verify Docker Compose:

```bash
docker compose version
```

Example:

```text
Docker Compose version v2.x.x
```

---

# Choosing a Kafka Docker Image

Several Kafka images are available.

Popular options:

| Image | Recommended | Notes |
|---------|:-----------:|------|
| Apache Kafka Official | ✅ | Official image from Apache |
| Confluent Platform | ✅ | Most widely used in enterprise |
| Bitnami Kafka | ✅ | Beginner-friendly |
| wurstmeister/kafka | ❌ | Legacy image |

For learning and production-like environments, prefer:

- Apache Official
- Confluent
- Bitnami

---

# Running a Single Kafka Container

A simple example:

```bash
docker run \
-d \
--name kafka \
-p 9092:9092 \
apache/kafka:latest
```

Docker will:

- Download the image
- Create a container
- Start Kafka
- Expose port **9092**

---

# Verify the Container

List running containers:

```bash
docker ps
```

Example:

```text
CONTAINER ID

NAME

STATUS

PORTS

kafka
```

Kafka should appear in the list.

---

# View Logs

To monitor Kafka startup:

```bash
docker logs kafka
```

Follow logs continuously:

```bash
docker logs -f kafka
```

Useful during troubleshooting.

---

# Stopping Kafka

Stop the container:

```bash
docker stop kafka
```

Container:

```text
Running

↓

Stopped
```

The container still exists.

---

# Starting Kafka Again

Restart:

```bash
docker start kafka
```

Kafka resumes from its previous state.

---

# Removing the Container

Delete the stopped container:

```bash
docker rm kafka
```

To stop and remove:

```bash
docker rm -f kafka
```

---

# Pulling a Specific Kafka Version

Instead of using `latest`, pull a specific version.

Example:

```bash
docker pull apache/kafka:4.1.0
```

Using explicit versions improves reproducibility.

---

# Exposed Ports

Typical Kafka ports:

| Port | Purpose |
|------:|---------|
| 9092 | Kafka Broker |
| 9093 | Internal / SSL (optional) |

Different Docker images may expose additional ports.

---

# Container Networking

Docker provides networking between containers.

Example:

```text
Application Container

↓

Kafka Container

↓

Docker Network
```

Applications communicate using the container name.

Example:

```text
kafka:9092
```

instead of

```text
localhost:9092
```

when running inside the same Docker network.

---

# Running Kafka in Detached Mode

Detached mode keeps Kafka running in the background.

```bash
docker run -d ...
```

Without `-d`:

```text
Terminal

↓

Occupied
```

Detached mode is recommended.

---

# Checking Resource Usage

View CPU and memory usage:

```bash
docker stats
```

Example:

```text
Kafka

CPU

Memory

Network
```

Useful when running multiple containers.

---

# Inspecting the Container

View container details:

```bash
docker inspect kafka
```

Information includes:

- Network
- Volumes
- Ports
- Environment variables

---

# Executing Commands Inside Kafka

Open a shell inside the container:

```bash
docker exec -it kafka bash
```

Or:

```bash
docker exec -it kafka sh
```

You can now execute Kafka CLI commands inside the container.

---

# Persistent Data

Without volumes:

```text
Stop Container

↓

Delete Container

↓

All Data Lost
```

For persistence:

```text
Kafka Container

↓

Docker Volume

↓

Disk
```

Volumes are discussed in the next chapter.

---

# Common Startup Workflow

```text
Start Docker

↓

Pull Kafka Image

↓

Run Container

↓

Verify Logs

↓

Verify Port

↓

Kafka Ready
```

---

# Common Problems

### Port Already in Use

Error:

```text
9092 already allocated
```

Solution:

- Stop the existing process
- Change the mapped port

---

### Docker Not Running

Error:

```text
Cannot connect to Docker daemon
```

Solution:

Start Docker Desktop or Docker Engine.

---

### Container Stops Immediately

Possible causes:

- Invalid configuration
- Missing environment variables
- Incorrect image

Check:

```bash
docker logs kafka
```

---

### Cannot Connect to Kafka

Verify:

- Container is running
- Port mapping is correct
- Firewall allows connections
- Broker listener configuration

---

# Best Practices

- Use official or well-maintained Docker images.
- Prefer explicit image versions instead of `latest`.
- Run Kafka in detached mode.
- Monitor startup logs after launching.
- Persist Kafka data using Docker volumes.
- Keep Docker Desktop updated.
- Stop unused containers to conserve resources.

---

# Common Mistakes

- Using outdated Kafka images.
- Forgetting to expose port **9092**.
- Running multiple brokers on the same port.
- Ignoring container logs when startup fails.
- Assuming data persists without volumes.
- Using `latest` in production environments.

---

# Summary

Docker provides the fastest and simplest way to run Apache Kafka for local development and testing. Instead of manually installing Kafka and its dependencies, developers can start a fully functional broker with a single Docker command. Docker also offers portability, environment consistency, and easy cleanup, making it the preferred choice for development, experimentation, and CI/CD workflows. As Kafka deployments grow, Docker Compose and multi-container environments provide an even more powerful approach, which will be covered in the next chapter.

---

# Key Takeaways

- Docker is the preferred way to run Kafka locally.
- Kafka can be started in minutes using a Docker image.
- Official, Confluent, and Bitnami images are recommended.
- Always verify container status and logs after startup.
- Use Docker volumes to persist Kafka data.
- Use explicit image versions for reproducible environments.
- Docker networking enables communication between Kafka and other containers.
- Docker Compose is the recommended approach for managing multi-container Kafka environments.