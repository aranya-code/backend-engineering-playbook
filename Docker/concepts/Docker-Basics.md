# Docker Basics

## What is Docker?

Docker is an open-source containerization platform that enables developers to build, package, distribute, and run applications inside lightweight, isolated environments called containers.

A container includes everything an application needs to run, such as:
- Application code
- Runtime
- System libraries
- Dependencies
- Configuration files

This ensures the application behaves consistently across different environments.

---

## Why Docker?

Before Docker, applications often worked on one machine but failed on another due to differences in operating systems, software versions, or dependencies.

Docker solves this problem by packaging the application and its dependencies into a portable container that can run anywhere Docker is installed.

---

## Key Benefits of Docker

### 1. Portability
Containers can run consistently across:
- Developer laptops
- Testing environments
- Production servers
- Cloud platforms

**Build once, run anywhere.**

---

### 2. Isolation
Each container runs independently and has:
- Its own filesystem
- Network stack
- Processes

Problems in one container do not affect others.

---

### 3. Lightweight
Containers share the host operating system kernel, making them much smaller and faster than virtual machines.

Benefits:
- Faster startup time
- Lower resource consumption
- Higher application density

---

### 4. Scalability
Applications can be scaled horizontally by running multiple container instances.

This is especially useful for:
- Microservices
- High-traffic applications
- Cloud-native workloads

---

### 5. Consistency
Docker eliminates the classic:

> "It works on my machine."

problem by ensuring the same environment is used throughout development, testing, and production.

---

### 6. Faster Deployments
Containers can be created and started within seconds, enabling:
- Continuous Integration (CI)
- Continuous Deployment (CD)
- Rapid application delivery

---

## Docker vs Virtual Machine

| Feature | Docker Container | Virtual Machine |
|----------|-----------------|----------------|
| Startup Time | Seconds | Minutes |
| Size | MBs | GBs |
| Performance | Near Native | Higher Overhead |
| OS Required | Shares Host Kernel | Full Guest OS |
| Resource Usage | Low | High |

---

## Important Docker Terminology

### Image
A read-only blueprint used to create containers.

Examples:
- nginx
- ubuntu
- mysql

### Container
A running instance of an image.

### Docker Engine
The core service responsible for building and running containers.

### Docker Hub
A public registry used to store and share Docker images.

---

## Docker Workflow

1. Write application code
2. Create a Dockerfile
3. Build a Docker Image
4. Run a Container from the Image
5. Push the Image to Docker Hub (optional)
6. Deploy Containers anywhere

```text
Code
 ↓
Dockerfile
 ↓
Docker Image
 ↓
Docker Container
 ↓
Deployment
```

---

## Real-World Example

Without Docker:

Developer → App Works
Tester → Dependency Missing
Production → Different Environment

Result: Application Failure

With Docker:

Developer → Docker Image
        ↓
Tester → Same Docker Image
        ↓
Production → Same Docker Image

Result: Consistent Behavior Everywhere

---

## One-Line Interview Definition

Docker is an open-source containerization platform that packages applications and their dependencies into lightweight, portable containers, ensuring consistent execution across development, testing, and production environments.