# Nginx

A comprehensive, production-oriented playbook for mastering Nginx — from web server fundamentals to reverse proxying, load balancing, caching, SSL/TLS, Docker, Kubernetes Ingress, performance tuning, CLI operations, and production troubleshooting.

---

# What You Will Learn

By completing this playbook, you will understand:

- Nginx Architecture (event-driven, master/worker model)
- Configuration Contexts, Directives, and Inheritance
- Request Processing and Location Block Matching
- Static File Serving and HTTP Headers
- Gzip Compression and HTTP/2
- Reverse Proxy and Backend Communication
- FastCGI and Proxy Caching
- SSL/TLS Termination and HTTPS Redirection
- Security Headers and Hardening
- Load Balancing Algorithms and Upstream Configuration
- Logging, Monitoring, and Observability
- Performance Tuning (workers, buffers, keepalive, sendfile)
- Browser Caching (Cache-Control, ETag, Expires)
- Docker Deployment and Docker Compose
- Kubernetes Ingress Controller
- CLI Commands and Daily Operations
- Production Troubleshooting (27 scenarios)
- Interview Preparation

---

# Module Structure

```text
Nginx/
│
├── README.md                          ← You are here
│
├── concepts/                          28 files — Core knowledge
│   ├── README.md                      Detailed module index with learning path
│   ├── 01- Introduction.md
│   ├── 02- Nginx Architecture.md
│   ├── 03- Configuration Contexts.md
│   ├── 04- Directives.md
│   ├── 05- Request Processing.md
│   ├── 06- Location Blocks.md
│   ├── 07- Variables.md
│   ├── 08- Directive Inheritance.md
│   ├── 09- Static File Serving.md
│   ├── 10- HTTP Headers.md
│   ├── 11- Gzip Compression.md
│   ├── 12- HTTP2.md
│   ├── 13- Reverse Proxy.md
│   ├── 14- FastCGI Cache.md
│   ├── 15- Proxy Cache.md
│   ├── 16- SSL TLS.md
│   ├── 17- HTTPS Redirection.md
│   ├── 18- Nginx Security Headers.md
│   ├── 19- Load Balancing.md
│   ├── 20- Logging.md
│   ├── 21- Performance Tuning.md
│   ├── 22- Browser Caching.md
│   ├── 23- Security Best Practices.md
│   ├── 24- Docker Deployment.md
│   ├── 25- Kubernetes Ingress.md
│   ├── 26- Troubleshooting.md
│   ├── 27- Interview Guide.md
│   └── 28- Nginx Cheat Sheet.md
│
├── cli/                               5 files — Command-line operations
│   ├── README.md
│   ├── 01- Essential Commands.md
│   ├── 02- Configuration Management.md
│   ├── 03- Log Analysis.md
│   ├── 04- Performance Debugging.md
│   └── 05- SSL Certificate Management.md
│
├── troubleshooting/                   28 files — Production incident guides
│   ├── README.md
│   ├── 01- Nginx Won't Start.md
│   ├── ...
│   └── 27- Diagnostic Commands.md
│
└── sample files/                      Reference configurations
    └── conf/nginx.conf
```

---

# Module Directory

| # | Directory | Files | Description |
|---|-----------|-------|-------------|
| 01 | [Concepts](./concepts/) | 28 | Core Nginx knowledge — architecture, configuration, proxying, caching, SSL, load balancing, Docker, K8s, interviews |
| 02 | [CLI](./cli/) | 5 | Command-line operations — essential commands, config management, log analysis, performance debugging, SSL management |
| 03 | [Troubleshooting](./troubleshooting/) | 28 | Production incident guides — startup failures, HTTP errors, SSL issues, Docker/K8s problems, performance bottlenecks |
| 04 | [Sample Files](./sample%20files/) | 1 | Reference nginx.conf configuration |

---

# Architecture Overview

```text
                        Internet (Clients)
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                      Nginx Server                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Master Process (root)                │   │
│  │  - Reads configuration                            │   │
│  │  - Manages worker processes                       │   │
│  │  - Binds to ports 80/443                          │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                        │
│     ┌───────────┼───────────┐                           │
│     ▼           ▼           ▼                           │
│  ┌──────┐  ┌──────┐  ┌──────┐                          │
│  │Worker│  │Worker│  │Worker│  (event-driven,           │
│  │  #1  │  │  #2  │  │  #3  │   non-blocking I/O)      │
│  └──┬───┘  └──┬───┘  └──┬───┘                          │
│     │         │         │                               │
│     └─────────┼─────────┘                               │
│               │                                          │
│   ┌───────────┼───────────────────────────┐             │
│   │           │           │               │             │
│   ▼           ▼           ▼               ▼             │
│ Static     Reverse     Load           SSL/TLS           │
│ Files      Proxy     Balancer       Termination         │
│            │           │                                 │
└────────────┼───────────┼─────────────────────────────────┘
             │           │
             ▼           ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ Django   │  │ FastAPI  │  │ Node.js  │
     │ Gunicorn │  │ Uvicorn  │  │ Express  │
     └──────────┘  └──────────┘  └──────────┘
         Backend Application Servers
```

---

# Learning Path

```text
Phase 1: Foundations
  Introduction → Architecture → Configuration Contexts →
  Directives → Request Processing → Location Blocks

Phase 2: Serving Content
  Variables → Directive Inheritance → Static File Serving →
  HTTP Headers → Gzip Compression → HTTP/2

Phase 3: Proxying & Caching
  Reverse Proxy → FastCGI Cache → Proxy Cache

Phase 4: Security
  SSL/TLS → HTTPS Redirection → Security Headers →
  Security Best Practices

Phase 5: Scaling & Performance
  Load Balancing → Logging → Performance Tuning → Browser Caching

Phase 6: Containers & Orchestration
  Docker Deployment → Kubernetes Ingress

Phase 7: Operations
  CLI Commands → Troubleshooting (27 guides) →
  Interview Guide → Cheat Sheet
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Backend Engineering Playbook](../) |

---

> **Part of the [Backend Engineering Playbook](../) — a structured learning resource for backend engineers.**

*Created by Aranya Majumdar*
