# Profiles in Docker Compose

## Overview

Docker Compose Profiles allow you to selectively start services based on the environment or use case.

Profiles are useful when some services should only run:

- During Development
- During Testing
- During Debugging
- In Specific Environments

Instead of maintaining multiple Compose files, profiles let you control service activation from a single file.

---

# What are Profiles?

## Definition

Profiles are a Docker Compose feature that enables conditional service startup.

A service assigned to a profile starts only when that profile is activated.

---

# Why Use Profiles?

Consider an application:

```text
Frontend

Backend

Database

Redis

Admin Tool

Debug Tool
```

Not every service is needed all the time.

---

# Without Profiles

```bash
docker compose up
```

Starts:

```text
Frontend

Backend

Database

Redis

Admin Tool

Debug Tool
```

Everything runs.

---

# With Profiles

```bash
docker compose --profile dev up
```

Starts only services assigned to:

```text
dev
```

profile.

---

# Profile Architecture

```text
Compose File

       │

       ▼

Profiles

 ┌─────┼─────┐

 ▼     ▼     ▼

dev   test  debug
```

---

# Basic Example

```yaml
services:

  app:

    image: myapp

  admin:

    image: admin-tool

    profiles:

      - dev
```

---

# Behavior

Default:

```bash
docker compose up
```

Starts:

```text
app
```

Only.

---

Activate Profile:

```bash
docker compose --profile dev up
```

Starts:

```text
app

admin
```

---

# Multiple Services

```yaml
services:

  app:

    image: myapp

  redis:

    image: redis

    profiles:

      - dev

  admin:

    image: admin-tool

    profiles:

      - dev
```

---

# Workflow

```text
Default Startup

      ▼

Application Only
```

---

```text
Dev Profile

      ▼

Application

Redis

Admin Tool
```

---

# Multiple Profiles

A service can belong to multiple profiles.

Example:

```yaml
services:

  redis:

    profiles:

      - dev

      - test
```

---

# Result

Profile:

```text
dev
```

starts Redis.

Profile:

```text
test
```

also starts Redis.

---

# Activating Profiles

## Single Profile

```bash
docker compose --profile dev up
```

---

## Multiple Profiles

```bash
docker compose --profile dev --profile debug up
```

---

# Environment-Specific Example

```yaml
services:

  app:

    image: myapp

  debug:

    image: busybox

    profiles:

      - debug
```

---

# Development Workflow

```text
Production

     ▼

Application
```

---

```text
Development

     ▼

Application

Debug Tools
```

---

# Testing Example

```yaml
services:

  app:

    image: myapp

  test-runner:

    image: test-tool

    profiles:

      - test
```

---

# Run Tests

```bash
docker compose --profile test up
```

---

# Debugging Example

```yaml
services:

  debugger:

    image: debugger

    profiles:

      - debug
```

---

# Start Debug Environment

```bash
docker compose --profile debug up
```

---

# Profile Naming

Common profile names:

```text
dev

test

debug

staging

monitoring
```

---

# Monitoring Example

```yaml
services:

  prometheus:

    image: prometheus

    profiles:

      - monitoring

  grafana:

    image: grafana

    profiles:

      - monitoring
```

---

# Start Monitoring Stack

```bash
docker compose --profile monitoring up
```

---

# Combining Profiles

Example:

```bash
docker compose --profile dev --profile monitoring up
```

Starts:

```text
Development Services

Monitoring Services
```

Together.

---

# View Active Services

```bash
docker compose ps
```

Displays currently running services.

---

# Profiles and Dependencies

Example:

```yaml
services:

  app:

    depends_on:

      - redis

  redis:

    profiles:

      - dev
```

---

# Potential Problem

Default startup:

```bash
docker compose up
```

may fail because:

```text
Redis Not Started
```

Always verify profile dependencies.

---

# Best Practice

Keep dependent services within the same profile when necessary.

---

# Complete Example

```yaml
services:

  app:

    image: myapp

  mysql:

    image: mysql

  redis:

    image: redis

    profiles:

      - dev

  admin:

    image: admin-tool

    profiles:

      - dev

  test-runner:

    image: tester

    profiles:

      - test
```

---

# Startup Results

Default:

```bash
docker compose up
```

Starts:

```text
app

mysql
```

---

Development:

```bash
docker compose --profile dev up
```

Starts:

```text
app

mysql

redis

admin
```

---

Testing:

```bash
docker compose --profile test up
```

Starts:

```text
app

mysql

test-runner
```

---

# Benefits of Profiles

## Single Compose File

Avoid maintaining multiple files.

---

## Cleaner Environments

Run only required services.

---

## Faster Startup

Fewer containers.

---

## Better Resource Usage

Unused services remain stopped.

---

## Easier Development

Activate tools only when needed.

---

# Common Commands

## Default Startup

```bash
docker compose up
```

---

## Start Dev Profile

```bash
docker compose --profile dev up
```

---

## Start Test Profile

```bash
docker compose --profile test up
```

---

## Multiple Profiles

```bash
docker compose --profile dev --profile monitoring up
```

---

# Common Interview Questions

## What are Docker Compose Profiles?

Profiles allow selective startup of services based on environment or use case.

---

## Why Use Profiles?

To avoid running unnecessary services and reduce the need for multiple Compose files.

---

## How Do You Activate a Profile?

```bash
docker compose --profile dev up
```

---

## Can a Service Belong to Multiple Profiles?

Yes.

A service can be assigned to multiple profiles.

---

## Are Profiles Useful for Development?

Yes.

Profiles are commonly used for development, testing, debugging, and monitoring services.

---

# Interview One-Liner

Docker Compose Profiles enable conditional service startup, allowing developers to selectively run environment-specific services such as debugging, testing, monitoring, and development tools from a single Compose configuration file.
