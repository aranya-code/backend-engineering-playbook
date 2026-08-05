# Persistent Storage

## Overview

Containers are designed to be **ephemeral**, meaning they can be created, stopped, destroyed, and recreated at any time. While this behavior is ideal for application containers, it creates a challenge for data that must survive container replacement.

Persistent storage ensures that important data remains available even when containers are removed or recreated.

Examples include:

- Database data
- User uploads
- Application-generated files
- SSL certificates
- Configuration files
- Backup archives

Without persistent storage, deleting a container also deletes its writable filesystem.

---

# Why Persistent Storage Matters

Without persistent storage:

```text
Container

↓

Database Writes Data

↓

Container Removed

↓

Data Lost
```

With persistent storage:

```text
Container

↓

Docker Volume

↓

Persistent Storage

↓

Container Recreated

↓

Data Still Exists
```

---

# Container Filesystem

Every container has a writable layer.

```text
Docker Image

↓

Read-Only Layers

↓

Writable Container Layer
```

The writable layer exists only while the container exists.

When the container is removed:

```text
Container Removed

↓

Writable Layer Deleted

↓

Data Lost
```

---

# Storage Options

Docker supports several storage mechanisms.

| Storage Type | Use Case |
|--------------|----------|
| Named Volume | Production applications |
| Bind Mount | Development |
| tmpfs Mount | Temporary in-memory storage |

---

# Named Volumes

Named volumes are managed by Docker.

Example

```yaml
services:

  postgres:

    image: postgres:17-alpine

    volumes:

      - postgres_data:/var/lib/postgresql/data

volumes:

  postgres_data:
```

Workflow

```text
Application

↓

Docker Volume

↓

Host Storage
```

Docker manages the storage location automatically.

---

# Bind Mounts

Bind mounts connect a host directory to a container.

Example

```yaml
volumes:

  - ./uploads:/app/uploads
```

Workflow

```text
Host Directory

↓

Docker

↓

Container
```

Bind mounts are useful during development.

---

# tmpfs Mounts

Temporary storage held entirely in memory.

```yaml
tmpfs:

  - /tmp
```

Workflow

```text
RAM

↓

Container

↓

Temporary Files
```

Data disappears when the container stops.

---

# Named Volume vs Bind Mount

| Named Volume | Bind Mount |
|---------------|------------|
| Docker managed | Host managed |
| Production | Development |
| Portable | Host dependent |
| Better isolation | Direct host access |
| Recommended for databases | Useful for source code |

---

# Production Architecture

```text
Internet

↓

Nginx

↓

Application

↓

Database

↓

Docker Volume

↓

Disk
```

Application containers remain stateless while persistent data is stored in volumes.

---

# Database Storage

Databases should always use persistent volumes.

Example

```yaml
services:

  db:

    image: postgres:17-alpine

    volumes:

      - postgres_data:/var/lib/postgresql/data
```

Without the volume:

```text
Container Deleted

↓

Database Deleted
```

---

# User Uploads

Uploaded files should also use persistent storage.

Example

```yaml
volumes:

  - uploads:/app/media
```

This prevents uploaded files from disappearing after deployments.

---

# Configuration Storage

Configuration files can be mounted separately.

```yaml
volumes:

  - ./config:/config:ro
```

Using read-only mounts protects configuration from accidental modification.

---

# Viewing Volumes

List volumes

```bash
docker volume ls
```

Example

```text
DRIVER    VOLUME NAME

local     postgres_data

local     uploads
```

---

# Inspecting Volumes

```bash
docker volume inspect postgres_data
```

Displays:

- Mountpoint
- Driver
- Labels
- Creation time

---

# Removing Volumes

Remove a volume

```bash
docker volume rm postgres_data
```

Remove unused volumes

```bash
docker volume prune
```

Be careful:

Removing a volume permanently deletes its stored data.

---

# Volume Backup

Example workflow

```text
Docker Volume

↓

Backup

↓

Compressed Archive

↓

Secure Storage
```

Regular backups are essential for production systems.

---

# Volume Restore

```text
Backup Archive

↓

Restore

↓

Docker Volume

↓

Application
```

A backup strategy should always include tested restoration procedures.

---

# Shared Volumes

Multiple containers can use the same volume.

```text
Container A

↓

Shared Volume

↑

Container B
```

Typical examples include:

- Shared uploads
- Static assets
- Log files

Care should be taken to avoid concurrent write conflicts.

---

# Read-Only Mounts

Example

```yaml
volumes:

  - ./config:/config:ro
```

Benefits:

- Prevents accidental changes
- Improves security
- Protects configuration files

---

# Storage Lifecycle

```text
Create Volume

↓

Attach Volume

↓

Write Data

↓

Remove Container

↓

Volume Remains

↓

Attach to New Container
```

Volumes outlive containers.

---

# Common Mistakes

## Storing Database Data Inside Containers

Incorrect

```text
Container

↓

Database

↓

Container Deleted

↓

Data Lost
```

Always use persistent volumes.

---

## Using Bind Mounts in Production

Bind mounts tightly couple containers to host directories.

Prefer named volumes unless host access is specifically required.

---

## Forgetting Backups

Persistent storage is **not** a backup strategy.

Volumes should still be backed up regularly.

---

## Removing Volumes Accidentally

Commands like

```bash
docker volume prune
```

can permanently remove unused volumes.

Review before executing cleanup commands.

---

## Mixing Application Code with Persistent Data

Keep application code immutable.

Persist only data that must survive deployments.

---

# Production Checklist

Before deployment:

- Database stored in a named volume
- User uploads persisted
- Configuration mounted appropriately
- Read-only mounts used where possible
- Backup strategy documented
- Restore process tested
- Volumes monitored
- Storage capacity planned

---

# Best Practices

- Use named volumes for production data.
- Keep application containers stateless.
- Back up persistent volumes regularly.
- Test backup restoration procedures.
- Use read-only mounts for configuration.
- Avoid unnecessary bind mounts in production.
- Monitor storage utilization.
- Separate application code from persistent data.

---

# Key Takeaways

- Containers are ephemeral, but application data often needs to persist across deployments.
- Named Docker volumes are the preferred storage mechanism for production workloads because they are portable, isolated, and managed by Docker.
- Databases, uploaded files, and other critical data should always reside on persistent storage rather than inside the container's writable layer.
- Persistent storage must be complemented by regular backups and tested recovery procedures.
- Treat containers as replaceable and data as durable by designing applications around stateless services and persistent volumes.