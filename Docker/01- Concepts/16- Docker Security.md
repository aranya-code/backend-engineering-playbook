# Docker Security

## Overview

Docker Security is the practice of protecting containerized applications, Docker images, container runtimes, hosts, networks, and registries from vulnerabilities and unauthorized access. Although containers provide process isolation, they share the host operating system's kernel, making security a shared responsibility between the application, the container runtime, and the underlying infrastructure.

A secure Docker environment requires more than simply running containers. It involves building trusted images, minimizing attack surfaces, managing secrets securely, restricting privileges, scanning for vulnerabilities, monitoring runtime behavior, and applying the principle of least privilege.

This chapter explains Docker's security architecture, common threats, security mechanisms, best practices, and production recommendations.

---

# Why Docker Security Matters

Containers often run:

- Production APIs
- Databases
- Authentication services
- Payment systems
- Internal applications
- Cloud-native workloads

A compromised container can potentially expose sensitive data or affect the host system if security best practices are not followed.

Security should therefore be considered throughout the container lifecycle.

---

# Docker Security Architecture

```text
                    Docker Security

+------------------------------------------+
|          Application Security            |
+------------------------------------------+
|          Docker Image Security           |
+------------------------------------------+
|       Container Runtime Security         |
+------------------------------------------+
|         Docker Engine Security           |
+------------------------------------------+
|          Linux Kernel Security           |
+------------------------------------------+
|          Host Operating System           |
+------------------------------------------+
|            Physical Hardware             |
+------------------------------------------+
```

Security is implemented in multiple layers.

---

# Docker Security Layers

A secure Docker deployment consists of several layers.

| Layer | Responsibility |
|--------|----------------|
| Application | Secure code |
| Docker Image | Trusted images |
| Container | Runtime isolation |
| Docker Engine | Secure runtime |
| Host OS | Operating system hardening |
| Infrastructure | Network and cloud security |

Each layer contributes to the overall security posture.

---

# Docker Isolation

Docker isolates containers using Linux kernel features.

These include:

- Namespaces
- cgroups
- Seccomp
- Capabilities
- AppArmor
- SELinux

Together, these mechanisms prevent containers from interfering with one another.

---

# Linux Namespaces

Namespaces isolate resources between containers.

Types include:

- Process namespace
- Network namespace
- Mount namespace
- IPC namespace
- UTS namespace
- User namespace

Each container receives its own isolated view of these resources.

---

# cgroups

Control Groups (cgroups) limit resource usage.

They manage:

- CPU
- Memory
- Disk I/O
- Network resources
- Process counts

This prevents one container from exhausting host resources.

---

# Linux Capabilities

Linux capabilities divide root privileges into smaller permissions.

Instead of granting full root access, containers receive only the capabilities they require.

Examples include:

- Network administration
- Time management
- File ownership
- System administration

Reducing capabilities significantly improves security.

---

# Seccomp

Seccomp filters Linux system calls.

```text
Application
      │
      ▼
Allowed System Calls
      │
      ▼
Linux Kernel
```

Dangerous system calls can be blocked before reaching the kernel.

---

# AppArmor and SELinux

These Linux security frameworks enforce mandatory access controls.

They restrict:

- File access
- Network access
- Process permissions
- Device access

Many production environments enable AppArmor or SELinux by default.

---

# Image Security

Every Docker deployment begins with an image.

Secure images should:

- Come from trusted sources
- Be regularly updated
- Be vulnerability scanned
- Be digitally signed where appropriate
- Minimize installed software

Smaller images generally reduce the attack surface.

---

# Image Scanning

Images should be scanned before deployment.

Scanners identify:

- Vulnerable packages
- Outdated libraries
- Known CVEs
- Security misconfigurations

Image scanning should be integrated into CI/CD pipelines.

---

# Trusted Images

Prefer:

- Official Docker images
- Verified publisher images
- Organization-approved base images

Avoid downloading random community images without verification.

---

# Running as Non-Root

Containers should avoid running as the root user.

```text
Bad Practice

Container
     │
     ▼
Root User
```

Preferred:

```text
Recommended

Container
     │
     ▼
Application User
```

Running as a non-root user limits the impact of a container compromise.

---

# Secret Management

Sensitive information should never be stored inside images.

Avoid embedding:

- Passwords
- API keys
- Database credentials
- Access tokens
- Certificates

Instead use:

- Docker Secrets
- Environment variables (carefully)
- Cloud Secret Managers
- External secret management solutions

---

# Docker Socket Security

The Docker socket provides administrative access to Docker Engine.

```text
/var/run/docker.sock
```

Anyone with access to this socket can effectively control Docker on the host.

Access should therefore be tightly restricted.

---

# Network Security

Protect container networking by:

- Using private Docker networks
- Exposing only required ports
- Encrypting external traffic
- Segmenting frontend and backend services
- Applying firewall rules

Containers should not communicate over public networks unless necessary.

---

# Registry Security

Protect Docker registries using:

- Authentication
- Authorization
- TLS encryption
- Image signing
- Access logging
- Vulnerability scanning

Private registries should require authenticated access.

---

# Runtime Security

Monitor running containers for:

- Unexpected processes
- Privilege escalation
- File modifications
- Network anomalies
- Resource abuse
- Suspicious system calls

Runtime monitoring complements image scanning by detecting threats after deployment.

---

# Docker Security in CI/CD

A secure deployment pipeline typically follows this workflow.

```text
Source Code
      │
      ▼
Build Image
      │
      ▼
Vulnerability Scan
      │
      ▼
Push Registry
      │
      ▼
Deploy Container
      │
      ▼
Runtime Monitoring
```

Security checks should occur throughout the pipeline rather than only at deployment time.

---

# Common Security Risks

Some common risks include:

- Running containers as root
- Using outdated base images
- Hardcoding secrets
- Exposing unnecessary ports
- Using the `latest` image tag
- Mounting sensitive host directories
- Granting excessive privileges
- Ignoring security updates

---

# Security Best Practices

- Use official or trusted base images.
- Keep images minimal.
- Scan images regularly.
- Run containers as non-root users.
- Apply the principle of least privilege.
- Protect the Docker socket.
- Use read-only filesystems where appropriate.
- Store secrets outside images.
- Keep Docker Engine updated.
- Monitor running containers continuously.
- Use immutable image versions.
- Restrict network access between services.

---

# Common Misconceptions

### Containers are completely isolated.

Incorrect.

Containers share the host operating system's kernel.

---

### Docker is insecure by default.

Incorrect.

Docker provides strong security features, but they must be configured properly.

---

### Image scanning alone is enough.

Incorrect.

Security also requires runtime monitoring, secure configuration, host hardening, and regular updates.

---

# Related Topics

- Docker Engine
- Docker Images
- Docker Networking
- Docker Volumes
- Docker Best Practices
- Docker Limitations

---

## Key Takeaways

- Docker Security protects applications, images, containers, runtimes, and hosts through multiple layers of defense.
- Linux namespaces, cgroups, capabilities, Seccomp, AppArmor, and SELinux provide the foundation for container isolation.
- Secure Docker deployments rely on trusted images, least privilege, proper secret management, restricted network access, and continuous vulnerability scanning.
- Security should be integrated throughout the software delivery lifecycle, from image creation to runtime monitoring.
- Following Docker security best practices significantly reduces the risk of vulnerabilities and strengthens production container deployments.