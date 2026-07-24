# Connection Refused

## Overview

One of the most common Redis production issues is receiving a **"Connection Refused"** error.

Typical errors include:

```text
Connection refused
```

```text
Error 111 connecting to Redis
```

```text
ECONNREFUSED
```

```text
Could not connect to Redis at 127.0.0.1:6379
```

This error simply means **the client could not establish a TCP connection to Redis.**

The cause could be:

- Redis is not running
- Wrong host or port
- Firewall
- Docker networking
- Kubernetes Service issues
- AWS Security Groups
- Network routing
- Redis binding configuration

This chapter provides a systematic approach for diagnosing and resolving Redis connection failures.

---

# Troubleshooting Workflow

```
Application

↓

Connection Refused

↓

Is Redis Running?

↓

Can Network Reach Redis?

↓

Is Port Correct?

↓

Is Authentication Required?

↓

Connection Established
```

Always work from the lowest layer upward.

---

# What Does Connection Refused Mean?

A connection refusal occurs before Redis processes any commands.

```
Application

↓

TCP Connection

↓

Rejected

↓

Redis Never Receives Request
```

This is different from authentication failures.

---

# Common Causes

| Cause | Typical Symptoms |
|--------|------------------|
| Redis service stopped | Immediate connection failure |
| Wrong host | Cannot reach Redis |
| Wrong port | Connection refused |
| Firewall | Connection timeout/refused |
| Docker networking | Containers cannot communicate |
| Kubernetes Service issue | Pod unreachable |
| Security Group | AWS traffic blocked |
| bind configuration | Redis listening only locally |

---

# Step 1 — Verify Redis is Running

Linux

```bash
sudo systemctl status redis
```

Expected

```text
Active: active (running)
```

If Redis is stopped

```bash
sudo systemctl start redis
```

---

# Step 2 — Test Locally

Run

```bash
redis-cli ping
```

Expected

```text
PONG
```

If this fails

The problem is on the Redis server itself.

---

# Step 3 — Verify Listening Port

Redis normally listens on

```
6379
```

Check

```bash
sudo ss -ltnp | grep 6379
```

or

```bash
sudo netstat -tulpn | grep 6379
```

Expected

```
6379 LISTEN
```

---

# Step 4 — Verify Host

Incorrect

```python
Redis(host="localhost")
```

Correct

```python
Redis(host="redis.internal.company.com")
```

or

```python
Redis(host="redis")
```

inside Docker.

---

# Step 5 — Verify Port

Example

```python
Redis(
    host="redis",
    port=6379
)
```

Incorrect port

```
6380
```

↓

Connection refused.

---

# Localhost Confusion

Inside Docker

```
localhost
```

means

```
Current Container
```

NOT

```
Redis Container
```

Correct

```
Application Container

↓

redis
```

where

```
redis
```

is the Docker service name.

---

# Docker Networking

Correct architecture

```
App Container

↓

Docker Network

↓

Redis Container
```

Check

```bash
docker ps
```

Inspect

```bash
docker network inspect bridge
```

---

# Docker Compose

Correct

```yaml
services:

  redis:
    image: redis:7

  app:
    depends_on:
      - redis
```

Connect using

```
redis
```

not

```
localhost
```

---

# Kubernetes Connectivity

Architecture

```
Application Pod

↓

Redis Service

↓

Redis Pod
```

Applications should connect to

```
redis-service
```

not directly to Pods.

---

# Verify Kubernetes Service

```bash
kubectl get svc
```

Example

```
redis-service
```

Verify endpoints

```bash
kubectl get endpoints redis-service
```

---

# Pod Connectivity

Test

```bash
kubectl exec -it app -- sh
```

Then

```bash
redis-cli -h redis-service
```

---

# DNS Problems

Inside Kubernetes

```
redis.default.svc.cluster.local
```

should resolve correctly.

Verify

```bash
nslookup redis-service
```

---

# Redis bind Configuration

Default

```conf
bind 127.0.0.1
```

Only accepts local connections.

Production

```conf
bind 0.0.0.0
```

or

```conf
bind <private-ip>
```

Use private networking with proper firewall rules.

---

# Protected Mode

Example

```conf
protected-mode yes
```

Protected mode improves security.

Do not disable it unless the deployment is properly secured.

---

# Firewall Issues

Linux

Check

```bash
sudo ufw status
```

or

```bash
sudo firewall-cmd --list-all
```

Firewall may block

```
6379
```

---

# Network Routing

Verify

```bash
ping redis-server
```

Then

```bash
telnet redis-server 6379
```

or

```bash
nc -zv redis-server 6379
```

Successful connection

```
Connected
```

---

# AWS Security Groups

Architecture

```
EC2

↓

Security Group

↓

ElastiCache
```

Verify

- Inbound rules
- Outbound rules
- VPC
- Subnet

---

# VPC Problems

Applications and Redis must exist inside compatible VPC networking.

```
EC2

↓

VPC A
```

```
Redis

↓

VPC B
```

↓

Cannot connect without routing.

---

# Redis AUTH vs Connection Refused

Connection refused

```
TCP Failed
```

Authentication failure

```
TCP Success

↓

AUTH Failed
```

These are different problems.

---

# Client Configuration

Python example

```python
import redis

client = redis.Redis(
    host="redis",
    port=6379,
    socket_timeout=5
)
```

Verify

```python
client.ping()
```

---

# Connection Pool

Poor

```
Every Request

↓

New Connection
```

Better

```
Connection Pool

↓

Redis
```

Pooling reduces connection overhead.

---

# Network Latency

High latency may resemble connection problems.

Monitor

- Packet loss
- RTT
- DNS resolution
- Routing

---

# Redis Logs

Review

```bash
journalctl -u redis-server
```

or

```bash
cat /var/log/redis/redis-server.log
```

Look for

- Binding failures
- Startup errors
- Port conflicts

---

# Client Logs

Applications often log

```
ECONNREFUSED

Retrying...

Timeout...
```

Client logs help identify intermittent failures.

---

# Health Check

Verify

```bash
redis-cli ping
```

Then

```bash
redis-cli INFO server
```

Confirm

- Redis version
- Uptime
- Listening port

---

# Diagnostic Flow

```
Connection Refused

        │

        ▼

Redis Running?

        │

 ┌──────┴──────┐

 │             │

No            Yes

 │             │

Start      Check Port

                │

                ▼

         Check Network

                │

                ▼

         Check Firewall

                │

                ▼

        Check bind Setting

                │

                ▼

        Verify Application Host

                │

                ▼

          Connection Success
```

---

# Common Mistakes

## Using localhost in Docker

```
localhost

≠

Redis Container
```

Use the container or service name.

---

## Wrong Port

Redis listens on

```
6379
```

unless configured otherwise.

---

## Ignoring Firewalls

Redis may be running but unreachable.

---

## Public Redis

Never expose Redis directly to the Internet.

Always use private networking.

---

## Hardcoding IP Addresses

Prefer

- DNS
- Kubernetes Services
- Service Discovery

instead of static IPs.

---

# Best Practices

- Verify Redis is running before investigating networking.
- Use DNS names instead of hardcoded IP addresses.
- Validate host and port configuration in every environment.
- Keep Redis inside private networks protected by firewalls or Security Groups.
- Use connection pooling in client applications.
- Monitor connection failures and retry rates.
- Test connectivity after infrastructure changes.
- Document network architecture and connection paths.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| DNS | Use stable service discovery |
| Connection Pooling | Reuse TCP connections |
| Networking | Minimize latency |
| Firewall | Allow only required traffic |
| Kubernetes | Connect through Services |
| AWS | Verify Security Groups and VPC |

---

# Production Considerations

For production environments:

- Configure health checks that validate Redis connectivity.
- Alert on increasing connection failures or refused connections.
- Use infrastructure-as-code to standardize networking rules.
- Review firewall, Network Policy, and Security Group changes before deployment.
- Verify connectivity after failover or infrastructure maintenance.
- Maintain runbooks for diagnosing networking issues across VMs, Docker, Kubernetes, and cloud platforms.

---

# Summary

A "Connection Refused" error indicates that a Redis client could not establish a TCP connection to the server. The root cause is typically related to the Redis service, network configuration, firewalls, container networking, or cloud infrastructure rather than Redis itself. A structured troubleshooting process—starting with service health, then validating ports, networking, DNS, and infrastructure configuration—allows engineers to restore connectivity quickly and safely.

---

# Key Takeaways

- "Connection Refused" occurs before Redis processes any commands.
- Verify that Redis is running and listening on the expected port.
- Check hostnames, ports, DNS resolution, and network routing.
- In Docker and Kubernetes, use service names instead of `localhost`.
- Keep Redis on private networks protected by firewalls or Security Groups.
- Distinguish connection failures from authentication failures.
- Use connection pooling to improve client efficiency.
- Follow a systematic troubleshooting workflow to identify the root cause efficiently.