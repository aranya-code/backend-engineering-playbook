# Redis CLI Basics

## Overview

The **Redis Command Line Interface (`redis-cli`)** is the official command-line utility provided by Redis for interacting directly with Redis servers. It is one of the most essential tools for backend developers, DevOps engineers, SREs, and database administrators.

Although most applications communicate with Redis using language-specific client libraries (such as `redis-py`, `Jedis`, or `node-redis`), every experienced backend engineer should be comfortable using the CLI because it provides direct access to every Redis command without writing application code.

The Redis CLI is commonly used for:

- Learning Redis
- Testing commands
- Debugging applications
- Monitoring Redis servers
- Performance analysis
- Server administration
- Configuration management
- Automation and scripting
- Troubleshooting production incidents

This chapter introduces the Redis CLI, explains how to connect to Redis, demonstrates common command-line options, and establishes the foundation for the command-specific chapters that follow.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand the purpose of `redis-cli`
- Connect to local and remote Redis instances
- Authenticate with Redis servers
- Execute commands interactively and non-interactively
- Understand Redis CLI syntax
- Navigate multiple Redis databases
- Format command output
- Use Redis CLI for automation
- Follow production best practices

---

# What is redis-cli?

`redis-cli` is the official Redis client distributed with every Redis installation.

It communicates directly with a Redis server using the **RESP (Redis Serialization Protocol)** over a TCP connection.

```
             Redis CLI

        +-------------+
        |  redis-cli  |
        +------+------+
               |
               | TCP
               |
        +------+------+
        | Redis Server|
        +-------------+
```

Unlike GUI tools, `redis-cli` exposes **every Redis feature**, making it the preferred interface for administration and troubleshooting.

---

# Why Backend Engineers Should Learn Redis CLI

During production incidents, engineers rarely have access to application code or graphical interfaces.

Instead, they connect directly to Redis.

Typical workflow:

```
Application Error

        ↓

Connect using redis-cli

        ↓

Inspect Data

        ↓

Identify Problem

        ↓

Fix Issue
```

Because of this, Redis CLI is considered an essential operational skill.

---

# Installing Redis CLI

The CLI is bundled with Redis.

When Redis is installed, the `redis-cli` executable is installed automatically.

Verify installation:

```bash
redis-cli --version
```

Example:

```text
redis-cli 8.0.0
```

---

# Starting Redis CLI

To connect to a locally running Redis server:

```bash
redis-cli
```

Default connection:

```
127.0.0.1:6379>
```

You are now connected and can execute Redis commands.

---

# Interactive Mode

Interactive mode allows continuous execution of commands.

```
redis-cli

↓

Redis Prompt

↓

Execute Commands

↓

Immediate Response
```

Example:

```text
127.0.0.1:6379>
```

This is the preferred mode for:

- Learning Redis
- Testing commands
- Debugging
- Manual administration

---

# Non-Interactive Mode

Individual commands can also be executed directly.

```bash
redis-cli PING
```

Output:

```text
PONG
```

This approach is commonly used in:

- Shell scripts
- Automation
- CI/CD pipelines
- Health checks
- Monitoring systems

---

# Connecting to a Remote Redis Server

Specify the host and port.

```bash
redis-cli -h <host> -p <port>
```

Example:

```bash
redis-cli -h redis.example.com -p 6379
```

---

# Authentication

If authentication is enabled:

```bash
redis-cli -a <password>
```

Example:

```bash
redis-cli -a myStrongPassword
```

For ACL users:

```bash
redis-cli --user app_user --pass password
```

---

# Using TLS

Many managed Redis services require encrypted connections.

```bash
redis-cli \
--tls \
-h redis.example.com \
-p 6380
```

TLS encrypts all communication between the client and Redis.

---

# Selecting a Database

Redis supports multiple logical databases (except Redis Cluster).

Switch databases:

```text
SELECT 1
```

Example:

```
127.0.0.1:6379> SELECT 1

OK
```

Verify current database by storing or retrieving keys.

Production environments typically use **Database 0** and separate workloads using independent Redis instances.

---

# Redis CLI Prompt

Typical prompt:

```
127.0.0.1:6379>
```

The prompt shows:

- Connected host
- Connected port
- Current database

Example:

```
127.0.0.1:6379[2]>
```

Database 2 is currently selected.

---

# Redis Command Syntax

Most Redis commands follow this format:

```
COMMAND key value
```

Examples:

```
SET user:1 John

GET user:1

DEL user:1
```

Commands are:

- Case-insensitive
- Space-separated
- Executed immediately

---

# Getting Help

Redis CLI provides command help.

```bash
redis-cli --help
```

Individual command help:

```text
HELP SET
```

or

```text
COMMAND INFO SET
```

Useful for quickly understanding command usage.

---

# Output Formats

Redis CLI supports multiple output styles.

Default:

```text
"John"
```

Raw output:

```bash
redis-cli --raw GET user:1
```

CSV output:

```bash
redis-cli --csv
```

Useful for automation and scripting.

---

# Running Commands from Files

Redis CLI can execute batches of commands.

```bash
redis-cli < commands.txt
```

Example file:

```
SET user:1 John
SET user:2 Alice
SET user:3 Bob
```

This technique is commonly used for:

- Initial data loading
- Bulk operations
- Automated deployments

---

# Piping Commands

Commands can be piped into Redis.

Example:

```bash
echo "PING" | redis-cli
```

Output:

```
PONG
```

Useful in shell scripts and CI/CD pipelines.

---

# Executing Commands in Scripts

Example:

```bash
#!/bin/bash

redis-cli SET status running

redis-cli GET status
```

Automation frequently uses this pattern.

---

# Redis CLI Workflow

Typical development workflow:

```
Application

↓

redis-cli

↓

Inspect Keys

↓

Modify Data

↓

Verify Results
```

---

Production workflow:

```
Incident

↓

Connect

↓

Inspect

↓

Monitor

↓

Resolve

↓

Disconnect
```

---

# Useful CLI Options

| Option | Description |
|---------|-------------|
| `-h` | Host |
| `-p` | Port |
| `-a` | Password |
| `--user` | ACL Username |
| `--pass` | ACL Password |
| `--tls` | Enable TLS |
| `--raw` | Raw output |
| `--csv` | CSV output |
| `--pipe` | Pipe mode |
| `--help` | Help |

---

# Redis CLI in Production

The CLI is commonly used for:

- Server health verification
- Memory inspection
- Replication validation
- Configuration changes
- Performance monitoring
- Cache debugging
- Security validation
- Cluster management
- Backup verification
- Emergency troubleshooting

---

# Common Mistakes

## Connecting to the Wrong Environment

Always verify whether you are connected to:

- Development
- Testing
- Staging
- Production

Mistaken changes in production can have serious consequences.

---

## Using Administrative Commands Without Verification

Commands that modify server state should always be reviewed before execution.

---

## Exposing Passwords

Avoid placing passwords directly in shell history.

Prefer:

- Environment variables
- Secret managers
- Configuration management systems

---

## Forgetting TLS

Production Redis deployments should encrypt client-server communication whenever supported.

---

## Assuming Database Selection Persists

Applications often reconnect automatically.

Never assume a previously selected database remains active across new sessions.

---

# Best Practices

- Learn Redis CLI before relying on GUI tools.
- Use non-interactive mode for automation.
- Prefer private network connectivity.
- Enable TLS for production.
- Authenticate using ACL users.
- Verify your target environment before executing commands.
- Keep administrative sessions short.
- Store credentials securely.
- Use scripting for repetitive operational tasks.

---

# Production Considerations

For enterprise environments:

- Restrict CLI access using firewalls.
- Use VPNs or private VPC networking.
- Audit administrative access.
- Enable TLS.
- Disable anonymous access.
- Rotate credentials regularly.
- Use least-privilege ACL users.
- Avoid executing dangerous commands during peak traffic.

---

# Summary

The Redis CLI is the primary interface for interacting with Redis servers. It enables developers and operators to execute commands, inspect data, automate workflows, and troubleshoot production systems efficiently. Mastering the CLI is an essential skill for anyone building or maintaining Redis-backed applications. The following chapters build upon this foundation by exploring the complete set of Redis commands for managing keys, data structures, transactions, server administration, and configuration.

---

# Key Takeaways

- `redis-cli` is the official Redis command-line client.
- It supports both interactive and non-interactive execution.
- Connections can be local, remote, authenticated, and encrypted using TLS.
- The CLI is indispensable for debugging, automation, and production operations.
- Understanding command syntax and common CLI options is fundamental before exploring Redis command categories.
- The remaining CLI chapters will provide a deep dive into the commands used to manage keys, data structures, server operations, and administration.