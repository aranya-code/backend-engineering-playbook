# Installing Redis

## Overview

Before Redis can be used as a cache, message broker, or in-memory database, it must be installed and configured. Redis is lightweight, easy to install, and available on all major operating systems.

In production environments, Redis is commonly deployed using:

- Linux packages
- Docker containers
- Kubernetes
- Cloud-managed Redis services (AWS ElastiCache, Azure Cache for Redis, Google Cloud Memorystore)

For development, Docker is the most popular option because it provides a consistent environment across different operating systems.

This chapter covers multiple installation methods and explains when to use each one.

---

# Installation Options

There are several ways to install Redis.

| Method | Recommended For |
|----------|-----------------|
| Docker | Development, Learning, Testing |
| Native Linux | Production Servers |
| Windows (WSL) | Development |
| macOS (Homebrew) | Development |
| Cloud Managed Services | Production |

---

# Installing Redis Using Docker (Recommended)

Docker is the easiest and most portable way to run Redis.

Pull the latest Redis image:

```bash
docker pull redis
```

Run a Redis container:

```bash
docker run -d \
  --name redis-server \
  -p 6379:6379 \
  redis
```

Verify that the container is running:

```bash
docker ps
```

Example output:

```text
CONTAINER ID   IMAGE   STATUS
a31df12345     redis   Up 10 seconds
```

---

# Connecting to Redis CLI

Open an interactive Redis shell:

```bash
docker exec -it redis-server redis-cli
```

You should see:

```text
127.0.0.1:6379>
```

This indicates that you are connected to the Redis server.

---

# Verify the Installation

Run:

```redis
PING
```

Expected output:

```text
PONG
```

This is the standard health check command used to verify that Redis is operational.

---

# Basic Test

Store a value:

```redis
SET username "Aranya"
```

Output:

```text
OK
```

Retrieve the value:

```redis
GET username
```

Output:

```text
"Aranya"
```

Delete the key:

```redis
DEL username
```

Output:

```text
(integer) 1
```

---

# Installing Redis on Ubuntu

Update package lists:

```bash
sudo apt update
```

Install Redis:

```bash
sudo apt install redis-server -y
```

Verify installation:

```bash
redis-server --version
```

Example:

```text
Redis server v=8.x.x
```

Start Redis:

```bash
sudo systemctl start redis-server
```

Enable Redis during system boot:

```bash
sudo systemctl enable redis-server
```

Check service status:

```bash
sudo systemctl status redis-server
```

---

# Installing Redis on macOS

Using Homebrew:

```bash
brew install redis
```

Start Redis:

```bash
brew services start redis
```

Connect:

```bash
redis-cli
```

---

# Installing Redis on Windows

Redis is not officially supported on Windows.

The recommended approach is to use:

- Windows Subsystem for Linux (WSL)
- Docker Desktop

Example:

```bash
docker run -d \
  --name redis-server \
  -p 6379:6379 \
  redis
```

Avoid using unofficial Windows Redis binaries for production or long-term development.

---

# Redis Default Port

By default Redis listens on:

```text
6379
```

Example connection:

```text
localhost:6379
```

Most Redis client libraries use this port by default.

---

# Redis Configuration File

The Redis configuration file is named:

```text
redis.conf
```

Common Linux location:

```text
/etc/redis/redis.conf
```

Some important configuration options include:

```text
bind
port
requirepass
maxmemory
appendonly
save
```

These settings control networking, security, persistence, and memory usage.

---

# Running Redis in the Background

Start Redis as a daemon:

```bash
redis-server --daemonize yes
```

Stop Redis:

```bash
redis-cli shutdown
```

---

# Checking Redis Version

Using the CLI:

```bash
redis-server --version
```

Example:

```text
Redis server v=8.x.x
```

Inside Redis:

```redis
INFO server
```

This command displays detailed server information, including version, operating system, uptime, and process details.

---

# Testing Client Connectivity

Connect using the Redis CLI:

```bash
redis-cli
```

Test the connection:

```redis
PING
```

Expected response:

```text
PONG
```

If you receive `PONG`, the client can communicate successfully with the Redis server.

---

# Common Installation Issues

## Port Already in Use

Error:

```text
Could not bind to port 6379
```

Solution:

- Stop the process using port 6379.
- Change the Redis port in `redis.conf`.
- Run Redis on a different port.

---

## Connection Refused

Error:

```text
Could not connect to Redis
```

Possible causes:

- Redis service is not running.
- Incorrect host or port.
- Firewall restrictions.

Verify:

```bash
redis-cli ping
```

---

## Docker Container Stops Immediately

Possible causes:

- Incorrect command
- Port conflicts
- Existing Redis container with the same name

Inspect logs:

```bash
docker logs redis-server
```

---

# Installation Best Practices

- Use Docker for local development.
- Use Linux packages for dedicated servers.
- Use managed Redis services in cloud environments.
- Keep Redis updated to the latest stable version.
- Secure Redis before exposing it to a network.
- Avoid running Redis as the root user.
- Monitor memory usage from the beginning.

---

# Summary

Redis can be installed in multiple ways depending on the environment. Docker provides the simplest setup for development, while Linux packages and managed cloud services are preferred for production deployments. After installation, always verify connectivity using the `PING` command and familiarize yourself with the default configuration file and service management commands.

---

# Key Takeaways

- Redis can be installed using Docker, Linux packages, Homebrew, or cloud-managed services.
- Docker is the recommended installation method for development.
- Redis listens on port **6379** by default.
- The `PING` command is the simplest way to verify a successful installation.
- The primary configuration file is `redis.conf`.
- Use `redis-cli` to interact with the Redis server.
- Always validate the installation before integrating Redis into your application.
- Production deployments should include proper security, persistence, and monitoring configurations.