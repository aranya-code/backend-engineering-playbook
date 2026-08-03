# Docker Installation

## Overview

Before building and running containers, Docker must be installed and configured correctly. While installation is straightforward, the process differs across operating systems because Docker relies on Linux kernel features such as namespaces and cgroups. On Windows and macOS, Docker uses lightweight virtualization to provide a Linux environment.

This chapter explains Docker's installation architecture, system requirements, installation methods, verification steps, and best practices. It focuses on understanding **how Docker is installed and configured**, rather than troubleshooting installation issues.

---

# Docker Installation Options

Docker can be installed on several operating systems.

| Platform | Installation Method |
|----------|----------------------|
| Windows | Docker Desktop |
| macOS | Docker Desktop |
| Ubuntu | Docker Engine |
| Debian | Docker Engine |
| CentOS / RHEL | Docker Engine |
| Amazon Linux | Docker Engine |
| Fedora | Docker Engine |

---

# Docker Desktop vs Docker Engine

Docker provides two primary installation options.

| Docker Desktop | Docker Engine |
|----------------|---------------|
| Windows & macOS | Linux |
| Includes GUI | CLI only |
| Includes Docker Compose | Docker Compose installed separately or bundled |
| Includes Kubernetes (optional) | Kubernetes installed separately |
| Uses virtualization | Uses native Linux kernel |

---

# System Requirements

Minimum requirements vary slightly by operating system.

### Windows

- Windows 10/11 (64-bit)
- WSL 2 or Hyper-V
- Hardware virtualization enabled
- Minimum 4 GB RAM (8 GB recommended)

---

### macOS

- macOS 12 or later
- Apple Silicon or Intel processor
- Minimum 4 GB RAM (8 GB recommended)

---

### Linux

- 64-bit operating system
- Linux kernel 3.10 or newer
- Root or sudo access
- Supported package manager

---

# Installation Architecture

Docker uses different architectures depending on the operating system.

## Linux

```text
+--------------------------+
| Docker CLI               |
+------------+-------------+
             |
             ▼
+--------------------------+
| Docker Daemon            |
+------------+-------------+
             |
             ▼
+--------------------------+
| Linux Kernel             |
+------------+-------------+
             |
             ▼
      Physical Hardware
```

Docker runs directly on the Linux kernel.

---

## Windows

```text
+--------------------------+
| Docker Desktop           |
+------------+-------------+
             |
             ▼
+--------------------------+
| WSL 2 / Hyper-V          |
+------------+-------------+
             |
             ▼
+--------------------------+
| Linux VM                 |
+------------+-------------+
             |
             ▼
| Docker Engine            |
```

Docker Desktop provides a lightweight Linux environment using WSL 2 (recommended) or Hyper-V.

---

## macOS

```text
+--------------------------+
| Docker Desktop           |
+------------+-------------+
             |
             ▼
+--------------------------+
| Lightweight Linux VM     |
+------------+-------------+
             |
             ▼
| Docker Engine            |
```

Since macOS does not use the Linux kernel, Docker Desktop runs Docker Engine inside a lightweight virtual machine.

---

# Docker Desktop Components

Docker Desktop includes several integrated tools.

- Docker Engine
- Docker CLI
- Docker Compose
- Docker Dashboard
- Docker Extensions
- Docker Scout
- Kubernetes (optional)

This provides a complete container development environment.

---

# Docker Engine Components

A Linux installation typically includes:

```text
Docker Engine
│
├── Docker Daemon (dockerd)
├── Docker CLI
├── containerd
├── runc
└── Docker API
```

Each component plays a specific role in container management.

---

# Installation Workflow

A typical installation process is:

```text
Download Docker
        │
        ▼
Install Docker
        │
        ▼
Start Docker Service
        │
        ▼
Verify Installation
        │
        ▼
Run First Container
```

---

# Docker Service

After installation, the Docker service manages containers in the background.

Responsibilities include:

- Building images
- Starting containers
- Managing networks
- Managing volumes
- Pulling images
- Communicating with registries

---

# Verifying the Installation

After installation, verify that Docker is working correctly.

Check the Docker version:

```bash
docker --version
```

View Docker system information:

```bash
docker info
```

Run a test container:

```bash
docker run hello-world
```

If the container runs successfully, Docker has been installed correctly.

---

# First Container Workflow

Running your first container follows this sequence.

```text
docker run hello-world
         │
         ▼
Check Local Image
         │
         ▼
Download Image (if needed)
         │
         ▼
Create Container
         │
         ▼
Run Application
         │
         ▼
Display Output
```

This demonstrates Docker's complete image-to-container workflow.

---

# Docker Installation Directory

Common installation locations include:

### Linux

```text
/usr/bin/docker
```

Docker data:

```text
/var/lib/docker/
```

---

### Windows

Docker Desktop stores application data within the user's profile and WSL 2 virtual disks.

---

### macOS

Docker Desktop stores configuration and VM data under the user's Library directory.

---

# Docker Desktop Dashboard

Docker Desktop provides a graphical interface for:

- Viewing containers
- Managing images
- Managing volumes
- Managing networks
- Viewing logs
- Monitoring resource usage
- Managing extensions

Although convenient, most production environments rely on the Docker CLI.

---

# Docker Installation Best Practices

When installing Docker:

- Use the latest stable release.
- Enable virtualization in the BIOS/UEFI if required.
- Prefer WSL 2 over Hyper-V on modern Windows systems.
- Keep Docker Desktop or Docker Engine updated.
- Allocate sufficient CPU, memory, and disk space.
- Verify the installation before starting development.

---

# Common Installation Mistakes

Avoid these common mistakes:

- Installing outdated Docker versions.
- Running unsupported operating systems.
- Disabling hardware virtualization.
- Ignoring Docker updates.
- Allocating insufficient memory.
- Assuming Docker Desktop and Docker Engine are identical.

---

# Production Considerations

For production servers:

- Prefer Docker Engine over Docker Desktop.
- Install only required components.
- Secure access to the Docker daemon.
- Restrict Docker API exposure.
- Monitor Docker services.
- Keep the host operating system updated.

Docker Desktop is intended for local development rather than production deployments.

---

# Related Topics

- Introduction to Docker
- Docker Architecture
- Docker Engine
- Docker Images
- Docker Containers
- Docker Security

---

## Key Takeaways

- Docker installation differs across operating systems because Docker relies on Linux kernel features.
- Docker Desktop provides an integrated development environment for Windows and macOS, while Docker Engine is the preferred choice for Linux servers.
- A successful installation includes Docker Engine, the Docker Daemon, the Docker CLI, and supporting runtime components.
- Verifying the installation with commands such as `docker --version`, `docker info`, and `docker run hello-world` confirms that Docker is functioning correctly.
- Understanding the installation architecture helps explain how Docker operates on different platforms and prepares you for later topics such as Docker Engine, images, and containers.