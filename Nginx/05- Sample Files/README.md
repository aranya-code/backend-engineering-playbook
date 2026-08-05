# Nginx Sample Files

## Overview

This folder contains production-oriented Nginx configuration examples for common deployment scenarios. Each sample demonstrates a specific use case and follows recommended configuration practices that can be adapted for real-world applications.

These files are intended to complement the Concepts, CLI, Troubleshooting, and Interview sections of this playbook by providing practical, copyable configurations that illustrate how Nginx is used in production.

> **Note:** These are reference configurations. Adjust domain names, file paths, SSL certificates, upstream servers, and other settings to match your environment before deploying them.

---

# Folder Structure

```text
05-Sample Files/

├── README.md
├── 01- Basic Web Server.conf
├── 02- Reverse Proxy.conf
├── 03- Load Balancer.conf
├── 04- SSL HTTPS.conf
├── 05- Static Files.conf
├── 06- Gzip Compression.conf
├── 07- Caching.conf
├── 08- Rate Limiting.conf
├── 09- Multiple Virtual Hosts.conf
├── 10- Docker Reverse Proxy.conf
├── 11- Django Deployment.conf
├── 12- FastAPI Deployment.conf
├── 13- React SPA.conf
├── 14- Microservices API Gateway.conf
└── 15- Production nginx.conf
```

---

## Quick Navigation

| Configuration | Description |
|--------------|-------------|
| [01. Basic Web Server](01-%20Basic%20Web%20Server.conf) | Minimal Nginx configuration for serving static websites. |
| [02. Reverse Proxy](02-%20Reverse%20Proxy.conf) | Forward requests from Nginx to backend applications. |
| [03. Load Balancer](03-%20Load%20Balancer.conf) | Distribute traffic across multiple backend servers. |
| [04. SSL HTTPS](04-%20SSL%20HTTPS.conf) | Configure HTTPS, TLS, and automatic HTTP to HTTPS redirection. |
| [05. Static Files](05-%20Static%20Files.conf) | Efficiently serve static assets with browser caching. |
| [06. Gzip Compression](06-%20Gzip%20Compression.conf) | Compress responses to reduce bandwidth and improve performance. |
| [07. Caching](07-%20Caching.conf) | Configure proxy caching to reduce backend load. |
| [08. Rate Limiting](08-%20Rate%20Limiting.conf) | Protect applications from abuse and excessive requests. |
| [09. Multiple Virtual Hosts](09-%20Multiple%20Virtual%20Hosts.conf) | Host multiple domains using a single Nginx instance. |
| [10. Docker Reverse Proxy](10-%20Docker%20Reverse%20Proxy.conf) | Reverse proxy configuration for Dockerized applications. |
| [11. Django Deployment](11-%20Django%20Deployment.conf) | Production-ready configuration for Django with Gunicorn. |
| [12. FastAPI Deployment](12-%20FastAPI%20Deployment.conf) | Production-ready configuration for FastAPI with Uvicorn. |
| [13. React SPA](13-%20React%20SPA.conf) | Serve React, Vue, or Angular Single Page Applications. |
| [14. Microservices API Gateway](14-%20Microservices%20API%20Gateway.conf) | API Gateway configuration for routing requests to multiple services. |
| [15. Production Nginx.conf](15-%20Production%20Nginx.conf) | Complete production-ready global Nginx configuration. |

---

# Configuration Categories

| Category | Sample Files |
|----------|--------------|
| Basic Web Hosting | 01, 05 |
| Reverse Proxy | 02, 10, 11, 12 |
| Load Balancing | 03 |
| Security & HTTPS | 04, 08 |
| Performance Optimization | 06, 07, 15 |
| Multi-Site Hosting | 09 |
| Containerized Deployments | 10, 12, 13, 14 |
| Production Configuration | 15 |

---

# Recommended Learning Order

Follow this order to gradually build your understanding of production Nginx configurations.

```text
Basic Web Server
        │
        ▼
Reverse Proxy
        │
        ▼
Load Balancer
        │
        ▼
HTTPS
        │
        ▼
Static Files
        │
        ▼
Compression
        │
        ▼
Caching
        │
        ▼
Rate Limiting
        │
        ▼
Virtual Hosts
        │
        ▼
Docker
        │
        ▼
Django
        │
        ▼
FastAPI
        │
        ▼
React SPA
        │
        ▼
Microservices
        │
        ▼
Production Configuration
```

---

# How to Use These Samples

Before using any configuration:

1. Replace example domain names.
2. Update file system paths.
3. Configure SSL certificates.
4. Modify backend server addresses.
5. Validate the configuration.

```bash
nginx -t
```

Reload Nginx after validation.

```bash
nginx -s reload
```

---

# Best Practices

- Validate every configuration before deployment.
- Keep configurations modular.
- Store reusable configurations in separate files.
- Use HTTPS in production.
- Enable logging and monitoring.
- Optimize static content delivery.
- Configure rate limiting for public APIs.
- Never expose backend services directly to the internet.
- Test configurations in a staging environment before production.

---

# Related Sections

- **01- Concepts** — Learn how Nginx works internally.
- **02- CLI** — Essential commands for managing Nginx.
- **03- Troubleshooting** — Diagnose and resolve common issues.
- **04- Interview** — Prepare for backend and DevOps interviews.

---

# Key Takeaways

- This folder provides practical, production-oriented Nginx configuration examples.
- Each sample focuses on a specific deployment scenario and demonstrates recommended configuration patterns.
- The examples progress from basic web hosting to production-ready architectures involving Docker, FastAPI, Django, and microservices.
- Use these configurations as reference templates and adapt them to your own infrastructure and deployment requirements.
- Combining these sample files with the Concepts, CLI, Troubleshooting, and Interview sections provides a comprehensive understanding of Nginx in real-world environments.