# Kafka with Docker

Running Apache Kafka with Docker is the fastest and most practical way to create a local Kafka environment for development, learning, and testing. Instead of manually installing Java, Kafka binaries, and configuring brokers, Docker allows developers to launch a fully functional Kafka cluster with just a few commands.

In modern development environments, Kafka is almost always executed inside containers, often alongside supporting services such as Kafka UI, Schema Registry, Kafka Connect, and application services. Docker Compose further simplifies this process by managing multiple containers, networks, and persistent storage from a single configuration file.

This section introduces Docker-based Kafka deployments, covering everything from running a single broker to creating a multi-broker cluster suitable for simulating production environments.

---

# Folder Structure

```text
05-Docker/
│
├── 01- Running Kafka with Docker.md
├── 02- Docker Compose.md
├── 03- Kafka UI.md
├── 04- Multi Broker Cluster.md
└── README.md
```

---

# Navigation

## Getting Started

- [01- Running Kafka with Docker](./01-%20Running%20Kafka%20with%20Docker.md)
- [02- Docker Compose](./02-%20Docker%20Compose.md)

---

## Development Tools

- [03- Kafka UI](./03-%20Kafka%20UI.md)

---

## Production-Like Environment

- [04- Multi Broker Cluster](./04-%20Multi%20Broker%20Cluster.md)

---

# Learning Path

Study the chapters in the following order:

```text
Running Kafka with Docker
            │
            ▼
Docker Compose
            │
            ▼
Kafka UI
            │
            ▼
Multi Broker Cluster
```

This progression starts with a single broker, introduces container orchestration, adds visualization tools, and finally moves to a distributed Kafka cluster.

---

# Topics Covered

This section explains:

- Running Kafka using Docker
- Kafka Docker images
- Docker Compose
- Container networking
- Port mapping
- Docker volumes
- Kafka UI tools
- Broker visualization
- Multi-broker clusters
- Cluster networking
- Replication testing
- Local production-like environments

---

# Prerequisites

Before studying this section, you should understand:

- Kafka Basics
- Topics
- Partitions
- Producers
- Consumers
- Basic Docker concepts
- Docker installation

---

# Skills You'll Gain

After completing this section, you will be able to:

- Run Kafka using Docker containers.
- Build reproducible Kafka development environments.
- Configure Docker Compose for Kafka projects.
- Use Kafka UI to inspect clusters and messages.
- Deploy and manage a multi-broker Kafka cluster locally.
- Understand Docker networking for Kafka services.
- Persist Kafka data using Docker volumes.
- Simulate production-like Kafka deployments on a local machine.

---

# Real-World Applications

The concepts in this section are commonly used in:

- Local Development
- Backend API Development
- Microservices Testing
- Event-Driven Systems
- CI/CD Pipelines
- Integration Testing
- Distributed Systems Training
- Development Sandboxes
- Kafka Proof of Concepts
- Local Production Simulations

---

# Best Practices

- Use Docker Compose instead of multiple `docker run` commands.
- Pin Docker images to specific Kafka versions.
- Store Kafka data in Docker volumes.
- Use Kafka UI for development and troubleshooting.
- Keep Docker Compose files under version control.
- Test broker failures using a multi-broker setup.
- Use service names instead of `localhost` for container-to-container communication.
- Monitor container logs during startup and debugging.

---

# Common Mistakes

- Using the `latest` Docker image in long-running environments.
- Forgetting to expose Kafka ports correctly.
- Using `localhost` between Docker containers.
- Running Kafka without persistent volumes.
- Ignoring container logs when troubleshooting.
- Assuming a single broker behaves like a production cluster.
- Removing Docker volumes accidentally with `docker compose down -v`.
- Hardcoding broker addresses instead of using service names.

---

# Summary

Docker has become the standard way to run Apache Kafka for development and testing. It eliminates complex installation steps, provides consistent environments across machines, and enables developers to launch complete Kafka ecosystems with minimal effort. By combining Docker Compose, Kafka UI, and multi-broker clusters, developers can closely replicate production deployments, making it easier to build, test, debug, and understand distributed event-driven systems before deploying them to real infrastructure.