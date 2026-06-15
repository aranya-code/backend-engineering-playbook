# Introduction to Docker Stacks

## Overview

Docker Stacks provide a way to deploy and manage multi-service applications in a Docker Swarm cluster using a single declarative configuration file.

A Stack allows administrators to deploy an entire application ecosystem consisting of:

- Frontend Services
- Backend APIs
- Databases
- Networks
- Volumes
- Secrets
- Configurations

as a single unit.

---

# What is a Docker Stack?

## Definition

A Docker Stack is a collection of related services deployed together into a Docker Swarm cluster using a Compose file.

Think of a Stack as:

```text
Application Package
```

that contains everything required to run an application.

---

# Why Docker Stacks Exist

Imagine deploying an application manually.

Frontend:

```bash
docker service create frontend
```

Backend:

```bash
docker service create backend
```

Database:

```bash
docker service create mysql
```

Managing large applications this way quickly becomes difficult.

---

# Docker Stack Solution

Instead of creating everything manually:

```text
Application Definition
       │
       ▼
docker stack deploy
       │
       ▼
Entire Application Created
```

Everything is deployed together.

---

# Stack Components

A stack may contain:

- Services
- Networks
- Volumes
- Secrets
- Configs

---

# Relationship with Docker Swarm

Important:

```text
Docker Stack Requires Docker Swarm
```

Stacks cannot run on standalone Docker Engine.

Verify:

```bash
docker info
```

Look for:

```text
Swarm: active
```

---

# Stack Lifecycle

```text
Create Stack File
        │
        ▼
Deploy Stack
        │
        ▼
Create Services
        │
        ▼
Run Tasks
        │
        ▼
Update Stack
        │
        ▼
Remove Stack
```

---

# Common Commands

Deploy:

```bash
docker stack deploy
```

List stacks:

```bash
docker stack ls
```

View services:

```bash
docker stack services
```

View tasks:

```bash
docker stack ps
```

Remove stack:

```bash
docker stack rm
```

---

# Common Interview Questions

## What is a Docker Stack?

A Docker Stack is a collection of services deployed and managed together in a Docker Swarm cluster using a Compose file.

## Can Docker Stacks Run Without Swarm?

No. Docker Stacks require Docker Swarm mode to be enabled.

## What File Format Does Docker Stack Use?

Docker Compose YAML format.

---

# Interview One-Liner

Docker Stacks provide a declarative and production-ready way to deploy, manage, and scale multi-service applications in Docker Swarm using a single Compose-based configuration file.
