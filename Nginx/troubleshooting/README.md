# Nginx Troubleshooting Guide

A production-focused collection of troubleshooting guides for diagnosing, investigating, and resolving common Nginx issues.

These guides are designed for **Backend Developers, DevOps Engineers, Platform Engineers, Site Reliability Engineers (SREs), and System Administrators** who work with Nginx in production environments.

Unlike the **Concepts** section, which explains how Nginx works, this section focuses on identifying symptoms, understanding root causes, and applying proven production-ready solutions.

---

# What You'll Learn

This troubleshooting guide covers:

- Startup failures
- Configuration errors
- HTTP status code troubleshooting
- SSL/TLS issues
- Docker & Kubernetes problems
- Performance bottlenecks
- File permission issues
- DNS failures
- Static content problems
- Browser caching
- Rate limiting
- Production diagnostics
- Performance validation

---

# Quick Navigation

## 🚀 Startup & Configuration

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Nginx Won't Start](01-%20Nginx%20Won't%20Start.md) | Diagnose why Nginx fails to start and recover the service |
| 02 | [Configuration Syntax Errors](02-%20Configuration%20Syntax%20Errors.md) | Resolve configuration syntax and validation errors |
| 03 | [Worker Process Directive Error](03-%20Worker%20Process%20Directive%20Error.md) | Fix invalid `worker_processes` directive placement |
| 04 | [Duplicate Location Block](04-%20Duplicate%20Location%20Block.md) | Resolve conflicting location block definitions |
| 05 | [Unknown Directive](05-%20Unknown%20Directive.md) | Troubleshoot unsupported or misspelled directives |

---

## 🌐 HTTP Status Code Errors

| # | Topic | Description |
|---|-------|-------------|
| 06 | [403 Forbidden](06-%20403%20Forbidden.md) | Diagnose permission and access issues |
| 07 | [404 Not Found](07-%20404%20Not%20Found.md) | Troubleshoot missing resources and incorrect paths |
| 08 | [500 Internal Server Error](08-%20500%20Internal%20Server%20Error.md) | Investigate server-side failures |
| 09 | [502 Bad Gateway](09-%20502%20Bad%20Gateway.md) | Resolve upstream communication failures |
| 10 | [503 Service Unavailable](10-%20503%20Service%20Unavailable.md) | Diagnose unavailable backend services |
| 11 | [504 Gateway Timeout](11-%20504%20Gateway%20Timeout.md) | Troubleshoot backend timeout issues |

---

## 🔒 SSL & HTTPS

| # | Topic | Description |
|---|-------|-------------|
| 12 | [SSL Certificate Problems](12-%20SSL%20Certificate%20Problems.md) | Resolve certificate installation and validation issues |
| 13 | [SSL Handshake Failure](13-%20SSL%20Handshake%20Failure.md) | Troubleshoot TLS negotiation failures |
| 14 | [HTTPS Mixed Content](14-%20HTTPS%20Mixed%20Content.md) | Fix insecure resources on HTTPS websites |

---

## 🐳 Docker & Kubernetes

| # | Topic | Description |
|---|-------|-------------|
| 15 | [Docker Networking Issues](15-%20Docker%20Networking%20Issues.md) | Diagnose Docker networking and reverse proxy issues |
| 16 | [Docker Volume Problems](16-%20Docker%20Volume%20Problems.md) | Resolve bind mount and volume mapping problems |
| 17 | [Kubernetes Ingress Issues](17-%20Kubernetes%20Ingress%20Issues.md) | Troubleshoot NGINX Ingress Controller deployments |

---

## ⚡ Performance & System Resources

| # | Topic | Description |
|---|-------|-------------|
| 18 | [High CPU Usage](18-%20High%20CPU%20Usage.md) | Identify excessive CPU utilization and optimize performance |
| 19 | [High Memory Usage](19-%20High%20Memory%20Usage.md) | Diagnose memory leaks and high RAM consumption |
| 20 | [Too Many Open Files](20-%20Too%20Many%20Open%20Files.md) | Resolve file descriptor exhaustion and limit issues |
| 21 | [Permission Denied](21-%20Permission%20Denied.md) | Fix filesystem permission and ownership problems |

---

## 🌍 Networking & Content Delivery

| # | Topic | Description |
|---|-------|-------------|
| 22 | [DNS Resolution Failure](22-%20DNS%20Resolution%20Failure.md) | Diagnose hostname resolution and DNS lookup failures |
| 23 | [Static Files Not Loading](23-%20Static%20Files%20Not%20Loading.md) | Resolve CSS, JavaScript, image, and font loading issues |
| 24 | [Browser Cache Problems](24-%20Browser%20Cache%20Problems.md) | Troubleshoot stale browser cache and asset versioning |
| 25 | [Rate Limiting Issues](25-%20Rate%20Limiting%20Issues.md) | Diagnose request throttling and `limit_req` configuration |

---

## 🛠 Production Operations

| # | Topic | Description |
|---|-------|-------------|
| 26 | [Performance Checklist](26-%20Performance%20Checklist.md) | Pre-deployment optimization and production readiness checklist |
| 27 | [Diagnostic Commands](27-%20Diagnostic%20Commands.md) | Essential Linux, Docker, Kubernetes, and Nginx diagnostic commands |

---

# Recommended Reading Order

If you're new to troubleshooting Nginx, follow this progression:

1. 🚀 Startup & Configuration
2. 🌐 HTTP Status Code Errors
3. 🔒 SSL & HTTPS
4. 🐳 Docker & Kubernetes
5. ⚡ Performance & System Resources
6. 🌍 Networking & Content Delivery
7. 🛠 Production Operations

---

# Production Troubleshooting Workflow

Most production incidents can be diagnosed using the following workflow:

```text
                User Reports Problem
                         │
                         ▼
              Is Nginx Running?
                         │
               ┌─────────┴─────────┐
               │                   │
              No                  Yes
               │                   │
               ▼                   ▼
       Check Service Status   Validate Configuration
               │                   │
               ▼                   ▼
       Review Startup Logs    Review Error Logs
               │                   │
               ▼                   ▼
      Test Backend Service    Check Network/DNS
               │                   │
               ▼                   ▼
       Verify SSL & Cache   Check CPU/Memory
               │                   │
               └─────────┬─────────┘
                         ▼
                    Apply the Fix
                         │
                         ▼
                  Validate Configuration
                         │
                         ▼
                     Reload Nginx
                         │
                         ▼
                  Verify Application
```

---

# Best Practices

- Always validate configuration using `nginx -t` before reloading.
- Prefer `reload` over `restart` whenever possible.
- Investigate logs before modifying configuration.
- Test backend services independently of Nginx.
- Monitor CPU, memory, network, and disk usage.
- Keep backups of production configurations.
- Document every production issue and its resolution.

---

# Related Sections

| Folder | Description |
|---------|-------------|
| **Concepts** | Learn Nginx architecture, request processing, directives, reverse proxy, caching, SSL, and performance tuning |
| **Docker** | Running Nginx inside Docker containers |
| **Kubernetes** | Deploying NGINX Ingress Controller |
| **Interview Guide** | Frequently asked Nginx interview questions |
| **Cheat Sheet** | Quick reference for directives, commands, and configuration snippets |

---

