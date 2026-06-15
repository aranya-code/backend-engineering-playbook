# Depends On in Docker Compose

## Overview

In a multi-container application, some services depend on others.

Examples:

```text
Frontend → Backend

Backend → Database

Application → Redis
```

Docker Compose provides the `depends_on` directive to control service startup order.

---

# What is Depends On?

## Definition

`depends_on` is a Docker Compose directive that specifies service dependencies and startup order.

It tells Docker Compose:

```text
Start Service A

Before

Start Service B
```

---

# Why Do We Need Depends On?

Consider:

```text
Application

Database
```

If the application starts before the database:

```text
Application ❌ Database Connection
```

The application may fail.

---

# Solution

Use:

```yaml
depends_on:
```

to ensure services start in the correct order.

---

# Basic Example

```yaml
services:

  app:

    image: myapp

    depends_on:

      - mysql

  mysql:

    image: mysql
```

---

# Startup Workflow

```text
MySQL Starts

      │

      ▼

Application Starts
```

---

# Architecture

```text
Application

      │

depends_on

      │

      ▼

Database
```

---

# Multiple Dependencies

Example:

```yaml
services:

  app:

    depends_on:

      - mysql

      - redis
```

---

# Workflow

```text
MySQL

Redis

   │

   ▼

Application
```

---

# Common Use Cases

## Application and Database

```yaml
depends_on:

  - mysql
```

---

## Application and Redis

```yaml
depends_on:

  - redis
```

---

## API and Message Queue

```yaml
depends_on:

  - rabbitmq
```

---

# Important Limitation

Many beginners misunderstand `depends_on`.

It only guarantees:

```text
Container Started
```

It does NOT guarantee:

```text
Application Ready
```

---

# Example Problem

Database container starts.

```text
MySQL Container Running
```

But:

```text
Database Still Initializing
```

Application may fail.

---

# Startup vs Readiness

```text
Container Started

≠

Application Ready
```

This is a very important interview concept.

---

# Example Scenario

```text
MySQL Startup Time

30 Seconds
```

Application:

```text
Starts in 2 Seconds
```

Result:

```text
Connection Failure
```

even though `depends_on` exists.

---

# Health Checks

To solve readiness issues, use:

```yaml
healthcheck:
```

---

# Health Check Example

```yaml
services:

  mysql:

    image: mysql

    healthcheck:

      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]

      interval: 10s

      retries: 5
```

---

# Service Health States

```text
Starting

Healthy

Unhealthy
```

---

# Depends On with Conditions

Modern Compose supports conditions.

Example:

```yaml
services:

  app:

    depends_on:

      mysql:

        condition: service_healthy
```

---

# Workflow

```text
MySQL Starts

      │

      ▼

MySQL Healthy

      │

      ▼

Application Starts
```

---

# Available Conditions

## service_started

```text
Container Started
```

---

## service_healthy

```text
Container Healthy
```

---

## service_completed_successfully

```text
Task Completed Successfully
```

Useful for initialization jobs.

---

# Example

```yaml
services:

  app:

    depends_on:

      mysql:

        condition: service_healthy
```

---

# Complete Example

```yaml
services:

  mysql:

    image: mysql

    healthcheck:

      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]

      interval: 10s

      retries: 5

  app:

    image: myapp

    depends_on:

      mysql:

        condition: service_healthy
```

---

# Database Initialization Pattern

```text
Database Starts

      │

      ▼

Database Healthy

      │

      ▼

Application Starts
```

Recommended pattern.

---

# Redis Example

```yaml
services:

  app:

    depends_on:

      redis:

        condition: service_healthy

  redis:

    image: redis
```

---

# Multi-Tier Example

```yaml
services:

  frontend:

    depends_on:

      backend:

        condition: service_healthy

  backend:

    depends_on:

      mysql:

        condition: service_healthy

  mysql:

    image: mysql
```

---

# Architecture

```text
Frontend

    │

    ▼

Backend

    │

    ▼

Database
```

---

# Viewing Service Status

```bash
docker compose ps
```

Displays:

```text
Running

Healthy

Unhealthy
```

---

# View Logs

```bash
docker compose logs
```

Useful when dependencies fail.

---

# Troubleshooting

## Application Starts Too Early

Cause:

```text
depends_on

Without

Health Check
```

---

Solution:

```yaml
healthcheck:
```

plus:

```yaml
condition: service_healthy
```

---

# Service Never Becomes Healthy

Check:

```bash
docker compose logs
```

---

# Dependency Loop

Avoid:

```text
A depends_on B

B depends_on A
```

Creates circular dependency.

---

# Best Practices

## Use Health Checks

Do not rely only on startup order.

---

## Avoid Circular Dependencies

Keep dependency chains simple.

---

## Keep Services Independent

Reduce unnecessary dependencies.

---

## Test Startup Sequences

Verify service initialization order.

---

## Use service_healthy

Preferred for databases and caches.

---

# Common Commands

## Start Application

```bash
docker compose up
```

---

## View Status

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs
```

---

## Restart Services

```bash
docker compose restart
```

---

# Common Interview Questions

## What is Depends On?

A Docker Compose directive that controls startup order between services.

---

## Does Depends On Guarantee Application Readiness?

No.

It guarantees container startup, not application readiness.

---

## How Do You Wait for a Database to Become Ready?

Use:

```yaml
healthcheck:
```

and:

```yaml
condition: service_healthy
```

---

## Can One Service Depend on Multiple Services?

Yes.

Example:

```yaml
depends_on:

  - mysql

  - redis
```

---

## What Problem Does Depends On Solve?

It prevents dependent services from starting before required services have started.

---

# Interview One-Liner

The `depends_on` directive in Docker Compose controls service startup order, and when combined with health checks, ensures applications start only after their required dependencies are healthy and ready to accept connections.
