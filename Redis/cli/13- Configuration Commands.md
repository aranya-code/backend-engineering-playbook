# Configuration Commands

## Overview

Redis Configuration commands allow administrators to inspect and modify the behavior of a running Redis server without restarting it. They are essential for production operations, performance tuning, memory management, security, persistence, replication, and troubleshooting.

Unlike Server commands, which primarily provide information about the running instance, Configuration commands directly affect how Redis operates.

These commands are commonly used by:

- DevOps Engineers
- Site Reliability Engineers (SREs)
- Platform Engineers
- Backend Engineers
- Cloud Infrastructure Teams

Typical production use cases include:

- Memory tuning
- Connection limits
- Persistence configuration
- Replication settings
- Security hardening
- Performance optimization
- Runtime debugging
- Operational maintenance

---

# Configuration Architecture

```
              Administrator

                    │

                    ▼

             CONFIG Commands

                    │

        ┌───────────┼────────────┐

        ▼           ▼            ▼

    Memory      Persistence   Security

        ▼           ▼            ▼

     Runtime Configuration Changes
```

---

# Common Configuration Commands

| Command | Description |
|----------|-------------|
| CONFIG GET | Read configuration values |
| CONFIG SET | Change runtime configuration |
| CONFIG RESETSTAT | Reset statistics |
| CONFIG REWRITE | Persist runtime configuration |
| ACL LIST | View access control lists |
| ACL SETUSER | Create/update users |
| ACL DELUSER | Delete users |
| ACL WHOAMI | Current authenticated user |

---

# CONFIG GET

Retrieves one or more configuration values.

Syntax

```redis
CONFIG GET parameter
```

Example

```redis
CONFIG GET maxmemory
```

Output

```
maxmemory

2147483648
```

Retrieve multiple values

```redis
CONFIG GET max*
```

Useful for:

- Troubleshooting
- Runtime inspection
- Capacity planning

---

# CONFIG SET

Changes runtime configuration.

Syntax

```redis
CONFIG SET parameter value
```

Example

```redis
CONFIG SET maxmemory 4gb
```

Output

```
OK
```

Redis immediately begins using the new value.

---

# Example: Change Eviction Policy

```
Current

↓

noeviction
```

Change

```redis
CONFIG SET maxmemory-policy allkeys-lru
```

Redis immediately switches eviction strategy.

---

# CONFIG RESETSTAT

Resets server statistics.

Example

```redis
CONFIG RESETSTAT
```

Useful during:

- Performance testing
- Benchmarking
- Capacity analysis

---

# CONFIG REWRITE

Writes runtime configuration changes back to the configuration file.

Example

```redis
CONFIG REWRITE
```

Workflow

```
CONFIG SET

↓

Runtime Updated

↓

CONFIG REWRITE

↓

redis.conf Updated
```

Without CONFIG REWRITE:

```
Restart

↓

Changes Lost
```

---

# Viewing Important Configuration

Memory

```redis
CONFIG GET maxmemory
```

Eviction Policy

```redis
CONFIG GET maxmemory-policy
```

Persistence

```redis
CONFIG GET save
```

Append Only File

```redis
CONFIG GET appendonly
```

TCP Port

```redis
CONFIG GET port
```

Timeout

```redis
CONFIG GET timeout
```

Protected Mode

```redis
CONFIG GET protected-mode
```

---

# Memory Configuration

Example

```redis
CONFIG GET maxmemory
```

Output

```
4294967296
```

Meaning

```
4 GB Maximum Memory
```

Update

```redis
CONFIG SET maxmemory 6gb
```

Useful during scaling.

---

# Eviction Policy

View

```redis
CONFIG GET maxmemory-policy
```

Possible values include:

- noeviction
- allkeys-lru
- volatile-lru
- allkeys-lfu
- volatile-lfu
- allkeys-random
- volatile-random
- volatile-ttl

Example

```redis
CONFIG SET

maxmemory-policy

allkeys-lru
```

---

# Persistence Configuration

View

```redis
CONFIG GET save
```

Example Output

```
900 1

300 10

60 10000
```

Meaning

```
After

900 Seconds

1 Change

↓

Create Snapshot
```

---

# AOF Configuration

View

```redis
CONFIG GET appendonly
```

Output

```
yes
```

Disable

```redis
CONFIG SET appendonly no
```

Enable

```redis
CONFIG SET appendonly yes
```

Changing AOF settings should be carefully planned in production.

---

# Network Configuration

View listening port

```redis
CONFIG GET port
```

Connection timeout

```redis
CONFIG GET timeout
```

Maximum clients

```redis
CONFIG GET maxclients
```

Update

```redis
CONFIG SET maxclients 50000
```

---

# Security Configuration

Protected Mode

```redis
CONFIG GET protected-mode
```

Password

```redis
CONFIG GET requirepass
```

Rename Dangerous Commands

```redis
CONFIG GET rename-command
```

---

# ACL LIST

Displays all configured users.

Example

```redis
ACL LIST
```

Output

```
user default

user application

user monitoring
```

Useful for auditing security.

---

# ACL SETUSER

Creates or modifies users.

Example

```redis
ACL SETUSER appuser

on

>StrongPassword

+@all
```

Permissions can include:

- Commands
- Key patterns
- Passwords
- Categories

---

# ACL DELUSER

Deletes a Redis user.

Example

```redis
ACL DELUSER olduser
```

---

# ACL WHOAMI

Displays the currently authenticated user.

Example

```redis
ACL WHOAMI
```

Output

```
application
```

Useful during debugging.

---

# Runtime Configuration Workflow

```
Administrator

↓

CONFIG GET

↓

Review Current Settings

↓

CONFIG SET

↓

Runtime Updated

↓

CONFIG REWRITE

↓

Persistent Configuration
```

---

# Memory Tuning Example

```
Application

↓

Memory Increasing

↓

CONFIG GET maxmemory

↓

Increase Limit

↓

Monitor
```

---

# Performance Optimization

```
High Latency

↓

Review Configuration

↓

Adjust Memory

↓

Adjust Clients

↓

Monitor Performance
```

---

# Security Hardening

```
Review ACL

↓

Disable Default User

↓

Create Application Users

↓

Restrict Commands
```

---

# Production Migration

```
New Hardware

↓

Increase Memory

↓

Increase Clients

↓

Rewrite Configuration
```

---

# Common Production Use Cases

Configuration commands are commonly used for:

- Memory tuning
- Connection scaling
- Security hardening
- Runtime diagnostics
- Replication configuration
- Persistence management
- Performance optimization
- Cloud migration
- Capacity planning
- Operational maintenance

---

# Common Mistakes

## Forgetting CONFIG REWRITE

```
CONFIG SET

↓

Restart Server

↓

Old Configuration Restored
```

Always rewrite persistent changes.

---

## Changing Production Configuration Without Testing

Configuration changes may impact:

- Memory
- Performance
- Replication
- Persistence

Always validate in staging first.

---

## Disabling Protected Mode Improperly

Avoid exposing Redis directly to the internet.

Always combine:

- Firewall
- TLS
- ACL
- Authentication

---

## Setting Unlimited Memory

```
maxmemory = 0
```

May cause:

- Memory exhaustion
- OOM killer
- Server crashes

Always define memory limits.

---

## Giving Full ACL Permissions

Avoid

```
+@all
```

unless absolutely necessary.

Grant least privilege.

---

# Best Practices

- Version-control your Redis configuration.
- Monitor configuration drift across environments.
- Use ACLs instead of a shared password.
- Define `maxmemory` explicitly.
- Select an eviction policy appropriate for your workload.
- Test configuration changes before production rollout.
- Persist runtime changes with `CONFIG REWRITE`.
- Restrict administrative commands to trusted users.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| CONFIG GET | O(N) |
| CONFIG SET | O(1) |
| CONFIG RESETSTAT | O(1) |
| CONFIG REWRITE | O(N) |
| ACL LIST | O(N) |
| ACL SETUSER | O(1) |
| ACL DELUSER | O(1) |
| ACL WHOAMI | O(1) |

*N = number of configuration parameters or ACL entries.*

---

# Production Considerations

For production deployments:

- Automate Redis configuration using Infrastructure as Code (Terraform, Ansible, Kubernetes ConfigMaps, Helm charts).
- Avoid making manual configuration changes directly on production servers whenever possible.
- Secure Redis with ACLs, authentication, TLS, and network isolation.
- Monitor memory usage, client connections, and eviction metrics after configuration changes.
- Apply configuration updates during maintenance windows if they could affect performance.
- Keep configuration files synchronized across primary and replica nodes.
- Regularly audit ACLs and remove unused accounts.

---

# Configuration Commands vs Server Commands

| Configuration Commands | Server Commands |
|------------------------|-----------------|
| Modify Redis behavior | Inspect Redis state |
| Runtime tuning | Monitoring |
| Memory configuration | Memory statistics |
| Security configuration | Client inspection |
| Persistence settings | Backup execution |
| ACL management | Server diagnostics |

---

# Summary

Redis Configuration commands provide administrators with the ability to inspect, modify, and persist runtime settings without restarting the server. They play a critical role in memory management, performance tuning, security, persistence, and operational maintenance. Commands such as `CONFIG GET`, `CONFIG SET`, `CONFIG REWRITE`, and the ACL management commands enable production teams to manage Redis safely and efficiently. Careful planning, testing, and monitoring are essential when applying configuration changes in production environments.

---

# Key Takeaways

- `CONFIG GET` retrieves current runtime configuration values.
- `CONFIG SET` updates Redis configuration without restarting the server.
- `CONFIG REWRITE` persists runtime changes to the configuration file.
- Use ACL commands (`ACL LIST`, `ACL SETUSER`, `ACL DELUSER`) to implement fine-grained access control.
- Always define `maxmemory` and choose an appropriate eviction policy.
- Test configuration changes in staging before applying them to production.
- Protect Redis using ACLs, TLS, authentication, and network isolation.
- Automate configuration management to ensure consistency across environments.