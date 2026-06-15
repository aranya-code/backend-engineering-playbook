# Docker Compose Interview Questions

## Overview

This file contains the most commonly asked Docker Compose interview questions from beginner to advanced levels.

Use this file as a final revision guide before interviews, certifications, and practical assessments.

---

# Beginner Questions

## What is Docker Compose?

Docker Compose is a tool used to define and run multi-container Docker applications using a YAML configuration file.

---

## Why Do We Use Docker Compose?

Docker Compose simplifies deployment and management of applications that require multiple containers.

Instead of:

```bash
docker run
docker run
docker run
```

we use:

```bash
docker compose up
```

---

## Which File Does Docker Compose Use?

Default files:

```text
compose.yaml
```

or

```text
docker-compose.yml
```

---

## Which Command Starts a Compose Application?

```bash
docker compose up
```

---

## Which Command Starts Containers in the Background?

```bash
docker compose up -d
```

---

## Which Command Stops a Compose Application?

```bash
docker compose down
```

---

# Core Concepts

## What is a Service?

A service is a configuration that defines how a container should be created and run.

Example:

```yaml
services:

  web:

    image: nginx
```

---

## What is a Volume?

A volume provides persistent storage that survives container recreation and deletion.

---

## What is a Network?

A network allows services to communicate with each other.

Docker Compose automatically creates a default network.

---

## What is Depends On?

The `depends_on` directive controls startup order between services.

---

## What are Profiles?

Profiles allow selective startup of services based on environment or use case.

---

# Service Questions

## Which Section Defines Services?

```yaml
services:
```

---

## Can One Compose File Contain Multiple Services?

Yes.

Example:

```text
Frontend

Backend

Database
```

can all be defined in one file.

---

## How Do Services Communicate?

Using built-in DNS and service names.

Example:

```text
backend

mysql
```

instead of IP addresses.

---

## Can Services Be Scaled?

Yes.

Example:

```bash
docker compose up --scale web=3
```

---

# Networking Questions

## Does Docker Compose Create Networks Automatically?

Yes.

A default network is created automatically.

---

## Which Network Driver Is Used By Default?

```text
Bridge
```

---

## Can a Service Join Multiple Networks?

Yes.

A service can be attached to multiple networks simultaneously.

---

## How Do Containers Discover Each Other?

Using Docker's built-in DNS service discovery.

---

# Storage Questions

## Difference Between Volume and Bind Mount?

Volume:

```text
Managed By Docker
```

Bind Mount:

```text
Managed By Host Filesystem
```

---

## Which Is Recommended for Databases?

Named Volumes.

---

## Which Command Lists Volumes?

```bash
docker volume ls
```

---

## Which Command Removes Volumes During Cleanup?

```bash
docker compose down -v
```

---

# Environment Variable Questions

## Which Section Defines Environment Variables?

```yaml
environment:
```

---

## What is the Purpose of the .env File?

To store reusable configuration values loaded automatically by Docker Compose.

---

## How Do You Reference Variables?

```yaml
${VARIABLE_NAME}
```

---

## How Do You Provide Default Values?

```yaml
${VARIABLE:-default}
```

---

# Depends On Questions

## Does Depends On Guarantee Readiness?

No.

It guarantees startup order, not application readiness.

---

## How Do You Ensure a Database Is Ready?

Use:

```yaml
healthcheck:
```

and:

```yaml
condition: service_healthy
```

---

## Why Is This Important?

A container can be running while the application inside it is still initializing.

---

# Profile Questions

## Why Use Profiles?

To selectively start environment-specific services.

Example:

```text
Development

Testing

Debugging

Monitoring
```

---

## How Do You Activate a Profile?

```bash
docker compose --profile dev up
```

---

## Can a Service Belong to Multiple Profiles?

Yes.

---

# Commands Questions

## View Running Services

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs
```

---

## Follow Logs

```bash
docker compose logs -f
```

---

## Execute Shell

```bash
docker compose exec web sh
```

---

## Validate Compose File

```bash
docker compose config
```

---

# Intermediate Questions

## Difference Between Docker Run and Docker Compose?

Docker Run:

```text
Single Container
```

Docker Compose:

```text
Multi-Container Applications
```

---

## Difference Between Compose and Swarm?

Compose:

```text
Single Host
Development
```

Swarm:

```text
Multi-Node
Production
```

---

## Can Docker Compose Be Used in Production?

Yes, but it is primarily designed for development and testing.

Docker Swarm and Kubernetes provide additional production orchestration features.

---

## What Happens During docker compose up?

Workflow:

```text
Read Compose File

      ▼

Create Network

      ▼

Create Volumes

      ▼

Create Containers

      ▼

Start Services
```

---

# Advanced Questions

## How Does Service Discovery Work?

Docker provides built-in DNS.

Services communicate using service names.

---

## What Happens If a Container Fails?

Behavior depends on:

```yaml
restart:
```

policy.

---

## What Are Common Restart Policies?

```text
no

always

on-failure

unless-stopped
```

---

## Why Use Health Checks?

To monitor application health rather than only container status.

---

## How Do You Share Data Between Containers?

Using shared volumes.

---

# Scenario-Based Questions

## Your Application Cannot Connect to MySQL. What Do You Check?

1. Service Name
2. Network Configuration
3. Health Check Status
4. Logs
5. Environment Variables

---

## Containers Start But Application Fails. Why?

Most common cause:

```text
Database Not Ready
```

Use:

```yaml
healthcheck:
```

and:

```yaml
depends_on:
```

with conditions.

---

## How Would You Deploy a Three-Tier Application?

Compose file containing:

```text
Frontend

Backend

Database
```

services.

---

## How Would You Persist Database Data?

Use:

```yaml
volumes:
```

with a named volume.

---

# Rapid-Fire Questions

## Start Application

```bash
docker compose up
```

---

## Stop Application

```bash
docker compose down
```

---

## View Logs

```bash
docker compose logs
```

---

## Execute Shell

```bash
docker compose exec
```

---

## Validate Configuration

```bash
docker compose config
```

---

## Scale Services

```bash
docker compose up --scale
```

---

# Top 20 Most Asked Questions

1. What is Docker Compose?
2. Why use Docker Compose?
3. What file does Compose use?
4. What is a service?
5. What is a volume?
6. What is a network?
7. What is depends_on?
8. What are profiles?
9. How do services communicate?
10. What is service discovery?
11. Difference between volume and bind mount?
12. Difference between Compose and Docker Run?
13. Difference between Compose and Swarm?
14. How do environment variables work?
15. What is the .env file?
16. What is a health check?
17. Which command validates a Compose file?
18. How do you scale services?
19. How do you view logs?
20. Can Compose be used in production?

---

# One-Line Revision Answers

## Docker Compose

Multi-container application management tool.

---

## Service

Container definition.

---

## Volume

Persistent storage.

---

## Network

Container communication layer.

---

## Depends On

Controls startup order.

---

## Profiles

Conditional service startup.

---

## Environment Variables

Runtime configuration.

---

## Health Checks

Application health monitoring.

---

## Compose File

```text
compose.yaml
```

---

## Start Application

```bash
docker compose up
```

---

# Final Interview One-Liner

Docker Compose is a YAML-based tool for defining, deploying, networking, configuring, and managing multi-container applications on a single Docker host, making it one of the most important tools for modern containerized development workflows.
