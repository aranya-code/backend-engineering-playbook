# Volumes in Docker Compose

## Overview

Containers are designed to be ephemeral.

This means:

```text
Container Deleted

      ▼

Data Lost
```

To persist data beyond the life of a container, Docker provides **Volumes**.

Docker Compose makes volume management simple and declarative through the Compose file.

---

# What is a Volume?

## Definition

A Docker Volume is a persistent storage mechanism managed by Docker that allows data to survive container recreation and deletion.

Volumes are stored outside the container filesystem.

---

# Why Do We Need Volumes?

Without volumes:

```text
MySQL Container

      ▼

Database Created

      ▼

Container Deleted

      ▼

Database Lost
```

---

# With Volumes

```text
Volume

   │

   ▼

Container

   │

   ▼

Container Deleted

   │

   ▼

Data Remains
```

---

# Volume Architecture

```text
Docker Volume

       │

       ▼

Container

       │

       ▼

Application Data
```

---

# Types of Storage in Docker

Docker supports:

```text
Volumes

Bind Mounts

tmpfs Mounts
```

---

# Volumes

Managed by Docker.

Recommended for most use cases.

---

# Bind Mounts

Directly map host directories.

Example:

```text
Host Folder

      │

      ▼

Container Folder
```

---

# tmpfs Mounts

Stored only in memory.

Data disappears after container stops.

---

# Defining Volumes in Compose

Example:

```yaml
volumes:

  db-data:
```

---

# Using a Volume

```yaml
services:

  mysql:

    volumes:

      - db-data:/var/lib/mysql

volumes:

  db-data:
```

---

# Volume Workflow

```text
Volume Created

      │

      ▼

Mounted Into Container

      │

      ▼

Application Writes Data

      │

      ▼

Container Removed

      │

      ▼

Data Still Exists
```

---

# Named Volumes

Most common type.

Example:

```yaml
volumes:

  db-data:
```

Docker manages the storage location.

---

# Verify Volumes

List volumes:

```bash
docker volume ls
```

Example:

```text
DRIVER    VOLUME NAME

local     myapp_db-data
```

---

# Inspect Volume

```bash
docker volume inspect myapp_db-data
```

Displays:

- Mount Point
- Driver
- Labels

---

# Bind Mount Example

```yaml
services:

  web:

    volumes:

      - ./app:/app
```

---

# Architecture

```text
Host Directory

      │

      ▼

Container Directory
```

Changes are reflected immediately.

---

# Bind Mount Use Cases

Useful for:

```text
Development

Source Code

Configuration Files
```

---

# Named Volume vs Bind Mount

| Feature | Named Volume | Bind Mount |
|----------|-------------|------------|
| Managed By Docker | Yes | No |
| Portable | Yes | Limited |
| Host Dependency | No | Yes |
| Production Usage | Recommended | Limited |
| Development Usage | Good | Excellent |

---

# Multiple Volumes

Example:

```yaml
services:

  app:

    volumes:

      - app-data:/data

      - logs-data:/logs

volumes:

  app-data:

  logs-data:
```

---

# Read-Only Volumes

Prevent writes.

Example:

```yaml
volumes:

  - ./config:/config:ro
```

Meaning:

```text
Read Only
```

---

# Anonymous Volumes

Example:

```yaml
services:

  app:

    volumes:

      - /data
```

Docker automatically creates a volume.

---

# Persistent Database Example

```yaml
services:

  mysql:

    image: mysql

    volumes:

      - mysql-data:/var/lib/mysql

volumes:

  mysql-data:
```

---

# Data Flow

```text
MySQL

   │

   ▼

/var/lib/mysql

   │

   ▼

Docker Volume
```

---

# Sharing Volumes

Multiple containers can use the same volume.

Example:

```yaml
services:

  app1:

    volumes:

      - shared-data:/data

  app2:

    volumes:

      - shared-data:/data

volumes:

  shared-data:
```

---

# Volume Creation

Automatic:

```bash
docker compose up
```

Docker creates missing volumes automatically.

---

# Volume Removal

Stop containers:

```bash
docker compose down
```

---

Remove volumes:

```bash
docker compose down -v
```

Warning:

```text
Data Deleted
```

---

# Volume Commands

## List Volumes

```bash
docker volume ls
```

---

## Inspect Volume

```bash
docker volume inspect <volume-name>
```

---

## Remove Volume

```bash
docker volume rm <volume-name>
```

---

## Remove Unused Volumes

```bash
docker volume prune
```

---

# Backup Volume

Example:

```bash
docker run --rm -v myvolume:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```

---

# Restore Volume

Example:

```bash
docker run --rm -v myvolume:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

---

# Best Practices

## Use Named Volumes for Databases

Examples:

```text
MySQL

PostgreSQL

MongoDB
```

---

## Use Bind Mounts for Development

Source code synchronization.

---

## Avoid Storing Important Data in Containers

Containers are temporary.

---

## Backup Production Volumes

Protect critical data.

---

## Use Read-Only Mounts When Possible

Improves security.

---

# Common Volume Problems

## Data Missing After Restart

Check:

```text
Volume Mounted?
```

---

## Permission Issues

Verify:

```text
Container User

Host Permissions
```

---

## Wrong Mount Path

Inspect:

```yaml
volumes:
```

configuration.

---

# Common Interview Questions

## What is a Docker Volume?

A Docker Volume is a persistent storage mechanism that survives container deletion and recreation.

---

## Why Are Volumes Required?

To preserve data outside container filesystems.

---

## Difference Between Volume and Bind Mount?

Volumes are managed by Docker, while bind mounts directly map host directories into containers.

---

## Which Command Lists Volumes?

```bash
docker volume ls
```

---

## Which Command Removes Volumes During Compose Cleanup?

```bash
docker compose down -v
```

---

## Can Multiple Containers Share a Volume?

Yes.

Multiple containers can mount the same volume.

---

# Interview One-Liner

Docker Compose volumes provide persistent storage for containers by mounting Docker-managed volumes or host directories, ensuring application data survives container recreation and enabling reliable stateful workloads.
