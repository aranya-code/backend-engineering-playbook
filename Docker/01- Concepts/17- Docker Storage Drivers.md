# Docker Storage Drivers

## Overview

Docker Storage Drivers are responsible for managing how Docker Images and Containers are stored on disk. Every Docker Image consists of multiple read-only layers, while every running container receives an additional writable layer. Storage drivers efficiently combine these layers into a single unified filesystem that applications can use.

Storage drivers are one of Docker's core internal technologies. Although most developers rarely configure them directly, understanding how they work helps explain Docker's layered architecture, image caching, build performance, disk usage, and container filesystem behavior.

This chapter explains Docker Storage Drivers, Copy-on-Write (CoW), layered filesystems, supported storage drivers, and production best practices.

---

# What is a Storage Driver?

A Docker Storage Driver is the component responsible for:

- Managing image layers
- Managing container writable layers
- Combining multiple layers into one filesystem
- Handling file modifications
- Optimizing disk usage
- Supporting Copy-on-Write

Without a storage driver, Docker could not efficiently build or run containers.

---

# Why Storage Drivers Exist

Imagine three containers created from the same image.

Without storage drivers:

```text
Container A
└── Complete Image

Container B
└── Complete Image

Container C
└── Complete Image
```

Each container would require a complete copy of the image.

This wastes:

- Disk space
- Memory
- Build time

Storage drivers eliminate this duplication.

---

# Layered Filesystem

Docker Images are built using layers.

```text
+---------------------------+
| Application Layer         |
+---------------------------+
| Python Dependencies       |
+---------------------------+
| Python Runtime            |
+---------------------------+
| Ubuntu Base Image         |
+---------------------------+
```

Each layer is stored only once.

Containers reuse these shared layers.

---

# Storage Driver Architecture

```text
                  Docker Engine

                       │
                       ▼

              Docker Storage Driver

                       │
      ┌────────────────┼────────────────┐
      ▼                ▼                ▼
 Image Layers    Writable Layer     Filesystem
```

The storage driver presents all layers as one unified filesystem.

---

# Image Layers

Image layers are:

- Read-only
- Immutable
- Shared
- Cached
- Reusable

Multiple containers can safely share the same image layers.

---

# Writable Layer

When Docker starts a container, it creates a writable layer.

```text
Container

Writable Layer
-----------------------
Image Layer 3
-----------------------
Image Layer 2
-----------------------
Image Layer 1
```

Only the writable layer changes during execution.

The image layers remain unchanged.

---

# Copy-on-Write (CoW)

Docker Storage Drivers use **Copy-on-Write (CoW)**.

Instead of copying entire files:

```text
Image File
      │
      ▼
Modify File
      │
      ▼
Copy Only Modified File
```

Unmodified files continue to be shared.

This dramatically reduces storage usage.

---

# Copy-on-Write Example

Suppose three containers use the same image.

```text
Base Image

app.py
config.yml
requirements.txt
```

If only `config.yml` changes in one container:

```text
Container

Writable Layer

config.yml (modified)
```

The remaining files continue using the shared image layers.

---

# Benefits of Copy-on-Write

Copy-on-Write provides:

- Faster container creation
- Lower storage usage
- Faster image downloads
- Efficient image sharing
- Reduced memory consumption

This is one reason Docker containers start much faster than virtual machines.

---

# Common Storage Drivers

Docker supports several storage drivers.

| Storage Driver | Status | Typical Use |
|----------------|--------|-------------|
| overlay2 | Recommended | Modern Linux systems |
| overlay | Legacy | Older kernels |
| aufs | Deprecated | Historical Docker installations |
| btrfs | Supported | Btrfs filesystems |
| zfs | Supported | ZFS environments |
| devicemapper | Legacy | Older enterprise deployments |
| vfs | Testing | Development and debugging |

Today, **overlay2** is the recommended storage driver for almost all Linux deployments.

---

# overlay2

overlay2 is Docker's default storage driver on most modern Linux distributions.

Advantages:

- Excellent performance
- Efficient layer management
- Low disk usage
- Stable
- Production ready

It is the preferred storage driver for:

- Ubuntu
- Debian
- Fedora
- Amazon Linux
- RHEL
- CentOS

---

# AUFS

AUFS (Another Union File System) was one of Docker's earliest storage drivers.

Characteristics:

- Layered filesystem
- Copy-on-Write support
- Historical importance

Today, AUFS is largely replaced by overlay2.

---

# Btrfs

Btrfs provides advanced filesystem features.

Advantages:

- Snapshots
- Compression
- Checksums
- Native Copy-on-Write

Useful when Docker runs on Btrfs filesystems.

---

# ZFS

ZFS is commonly used in enterprise storage environments.

Advantages:

- High reliability
- Data integrity
- Snapshots
- Compression
- Cloning

Requires a ZFS-backed host filesystem.

---

# Device Mapper

Device Mapper was widely used before overlay2 became standard.

Characteristics:

- Block-level storage
- Enterprise support
- More complex configuration

Modern deployments typically use overlay2 instead.

---

# VFS

The VFS driver performs full file copies instead of using Copy-on-Write.

Advantages:

- Very simple
- Useful for testing

Disadvantages:

- Slow
- High disk usage
- Not suitable for production

---

# Storage Driver Workflow

```text
Docker Image
      │
      ▼
Image Layers
      │
      ▼
Storage Driver
      │
      ▼
Writable Layer
      │
      ▼
Running Container
```

The storage driver combines image layers with the writable layer.

---

# Storage Drivers and Docker Build

During image builds:

```text
Dockerfile
      │
      ▼
Instruction
      │
      ▼
New Layer
      │
      ▼
Storage Driver
      │
      ▼
Docker Image
```

Each instruction creates a new cached layer.

---

# Performance Considerations

Storage driver performance affects:

- Image builds
- Container startup
- Disk usage
- Layer caching
- File operations

For most workloads, overlay2 provides the best balance of performance and stability.

---

# Choosing a Storage Driver

| Scenario | Recommended Driver |
|----------|--------------------|
| General Linux | overlay2 |
| Enterprise ZFS | zfs |
| Btrfs Filesystem | btrfs |
| Testing | vfs |
| Legacy Systems | devicemapper (if required) |

For nearly all modern Docker installations, no manual selection is necessary because Docker automatically uses overlay2 when supported.

---

# Common Misconceptions

### Storage Drivers store Docker Volumes.

Incorrect.

Storage drivers manage **image layers** and **container writable layers**.

Docker Volumes are managed separately.

---

### Every container stores a complete copy of the image.

Incorrect.

Containers share read-only image layers and create only a small writable layer.

---

### Changing a file modifies the Docker Image.

Incorrect.

Changes are written only to the container's writable layer.

The image remains immutable.

---

# Best Practices

- Use **overlay2** whenever possible.
- Keep images small to reduce layer size.
- Use multi-stage builds.
- Minimize unnecessary image layers.
- Store persistent application data in Docker Volumes rather than the writable layer.
- Regularly remove unused images and build cache.
- Monitor disk utilization on Docker hosts.

---

# Related Topics

- Docker Images
- Docker Containers
- Docker Volumes
- Docker Engine
- Docker Best Practices

---

## Key Takeaways

- Docker Storage Drivers manage image layers, container writable layers, and the unified filesystem presented to containers.
- Copy-on-Write (CoW) allows containers to share immutable image layers while storing only modified files in a writable layer.
- The layered filesystem architecture improves build performance, reduces storage usage, and accelerates container startup.
- **overlay2** is the recommended storage driver for most modern Linux deployments because of its performance and stability.
- Understanding storage drivers helps explain Docker's internal filesystem behavior and supports better image optimization and storage management.