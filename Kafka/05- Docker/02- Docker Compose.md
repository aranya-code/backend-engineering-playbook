# Docker Compose

## Overview

Running a single Kafka container is useful for basic experimentation, but real-world Kafka deployments usually require multiple services working together.

A typical local Kafka environment includes:

- Kafka Broker
- Kafka UI
- Optional Schema Registry
- Optional Kafka Connect
- Optional Multiple Brokers

Managing these containers individually using `docker run` quickly becomes difficult. Docker Compose solves this problem by allowing all services to be defined in a single YAML file and started with one command.

Docker Compose is the standard way to run Kafka locally for development and testing.

---

# Why Docker Compose?

Without Docker Compose:

```text
Start Kafka

↓

Start Kafka UI

↓

Create Network

↓

Configure Ports

↓

Configure Volumes

↓

Manage Containers
```

Everything must be managed manually.

With Docker Compose:

```text
docker compose up

↓

Entire Kafka Environment Ready
```

---

# What is Docker Compose?

Docker Compose is a tool for defining and running multi-container applications.

Everything is described inside:

```text
docker-compose.yml
```

The file contains:

- Services
- Networks
- Volumes
- Environment Variables
- Port Mappings

---

# Compose Architecture

```text
docker-compose.yml

        │

        ▼

Docker Compose

        │

 ┌──────┴─────────┐
 ▼                ▼

Kafka         Kafka UI

        │

        ▼

Docker Network
```

Every container communicates through an isolated Docker network.

---

# Basic Docker Compose File

A minimal Compose file looks like:

```yaml
services:
  kafka:
    image: apache/kafka:latest
```

In production-like environments, additional configuration is required.

---

# Compose File Structure

A typical Compose file contains:

```yaml
services:

volumes:

networks:
```

Each section has a specific purpose.

---

# Services

Services define containers.

Example:

```yaml
services:
  kafka:
    image: apache/kafka:latest

  kafka-ui:
    image: provectuslabs/kafka-ui
```

Each service becomes a Docker container.

---

# Environment Variables

Kafka uses environment variables for configuration.

Example:

```yaml
environment:
  KAFKA_NODE_ID: 1
```

Environment variables eliminate the need to modify configuration files inside the container.

---

# Port Mapping

Expose Kafka to the host machine.

Example:

```yaml
ports:
  - "9092:9092"
```

Format:

```text
Host Port

↓

Container Port
```

---

# Container Names

Assign meaningful names.

Example:

```yaml
container_name: kafka
```

Benefits:

- Easier debugging
- Simpler CLI commands
- Clearer logs

---

# Restart Policy

Automatically restart containers.

Example:

```yaml
restart: unless-stopped
```

Common options:

- no
- always
- on-failure
- unless-stopped

---

# Volumes

Volumes preserve Kafka data.

Example:

```yaml
volumes:
  - kafka-data:/var/lib/kafka/data
```

Without volumes:

```text
Delete Container

↓

Delete Data
```

With volumes:

```text
Delete Container

↓

Data Remains
```

---

# Docker Networks

Compose automatically creates a network.

Example:

```text
Kafka

↓

Kafka UI

↓

Same Docker Network
```

Containers communicate using service names.

Example:

```text
kafka:9092
```

instead of

```text
localhost:9092
```

---

# Starting the Environment

Start all services:

```bash
docker compose up
```

Compose will:

- Create network
- Create volumes
- Pull images
- Start containers

---

# Detached Mode

Run everything in the background.

```bash
docker compose up -d
```

Recommended for development.

---

# Viewing Running Containers

```bash
docker compose ps
```

Example:

```text
NAME

kafka

kafka-ui
```

---

# Viewing Logs

View logs from every service:

```bash
docker compose logs
```

Follow logs:

```bash
docker compose logs -f
```

Logs from a specific service:

```bash
docker compose logs kafka
```

---

# Stopping Containers

Stop the environment:

```bash
docker compose stop
```

Containers remain available.

---

# Starting Again

Restart:

```bash
docker compose start
```

---

# Removing Everything

Stop and remove containers:

```bash
docker compose down
```

Containers disappear.

Volumes remain.

---

# Removing Everything Including Volumes

```bash
docker compose down -v
```

Removes:

- Containers
- Networks
- Volumes

All Kafka data is lost.

---

# Rebuilding Containers

Suppose the Compose file changes.

Rebuild:

```bash
docker compose up --build
```

Useful after modifying Dockerfiles.

---

# Scaling Services

Compose supports multiple container instances.

Example:

```bash
docker compose up --scale consumer=3
```

Three consumer containers are created.

This is commonly used for application containers rather than Kafka brokers.

---

# Compose Lifecycle

```text
docker compose up

↓

Create Network

↓

Create Volumes

↓

Start Containers

↓

Application Ready

↓

docker compose down
```

---

# Directory Structure

A common project layout:

```text
project/

├── docker-compose.yml
├── .env
├── kafka/
├── producer/
└── consumer/
```

Keeping Compose files at the project root simplifies management.

---

# Common Problems

### Port Conflict

Error:

```text
9092 already in use
```

Solution:

- Stop existing Kafka
- Change port mapping

---

### Container Cannot Communicate

Cause:

```text
Wrong Host Name
```

Correct:

```text
kafka:9092
```

Incorrect:

```text
localhost:9092
```

inside another container.

---

### Changes Not Applied

If configuration changes are ignored:

```bash
docker compose down

docker compose up --build
```

---

### Volume Issues

Unexpected old data?

Existing Docker volumes may still contain previous Kafka logs.

Remove them:

```bash
docker compose down -v
```

---

# Development Workflow

```text
Write Compose File

↓

docker compose up -d

↓

Verify Logs

↓

Develop Applications

↓

docker compose down
```

---

# Advantages

- Single command startup
- Automatic networking
- Persistent storage
- Easy environment sharing
- Consistent development setup
- Supports multiple services
- Easy cleanup

---

# Limitations

- Intended for development and testing.
- Not a replacement for Kubernetes.
- Large clusters become difficult to manage using Compose alone.

---

# Best Practices

- Store the Compose file in version control.
- Use explicit image versions.
- Use named volumes for Kafka data.
- Keep environment variables in a `.env` file.
- Use meaningful container names.
- Run containers in detached mode during development.
- Verify logs after startup.
- Keep Docker Compose files simple and well documented.

---

# Common Mistakes

- Using `localhost` between containers.
- Forgetting persistent volumes.
- Running everything as the root user.
- Using `latest` images.
- Editing containers manually instead of updating the Compose file.
- Deleting volumes unintentionally with `down -v`.

---

# Summary

Docker Compose is the preferred way to run Kafka locally because it simplifies the management of multiple containers, networks, and persistent storage. By defining the entire Kafka environment in a single `docker-compose.yml` file, developers can start, stop, and recreate complex environments with a single command. Docker Compose provides consistency across development machines and forms the foundation for local Kafka development before moving to container orchestration platforms such as Kubernetes.

---

# Key Takeaways

- Docker Compose manages multi-container Kafka environments.
- A `docker-compose.yml` file defines services, networks, and volumes.
- `docker compose up` starts the complete environment.
- Named volumes preserve Kafka data across container restarts.
- Containers communicate using service names rather than `localhost`.
- `docker compose down` removes containers, while `down -v` also removes volumes.
- Docker Compose provides a reproducible development environment.
- It is ideal for local development but not intended for large-scale production orchestration.