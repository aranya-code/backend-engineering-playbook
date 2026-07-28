# 🧭 Backend Engineering Playbook

A structured, hands-on knowledge base for backend engineering — built one technology at a time, with concept notes, CLI references, real troubleshooting write-ups, interview preparation, and working sample projects.

> **1,350+ notes · 9.9 MB of documentation · 6 technologies**

---

## 📚 Topics

| Technology | Covers | Scale |
|------------|--------|-------|
| [Docker](Docker/) | Container fundamentals, images, volumes, networking, Compose, Swarm, production Dockerfiles | 9 concepts · 10 CLI refs · 6 troubleshooting |
| [Kubernetes](Kubernetes/) | Core objects, networking, storage, Helm, RBAC, cluster orchestration, sample manifests | 17 concepts · 17 CLI refs · sample files |
| [AWS](AWS/) | EC2, S3, IAM, VPC, Lambda, DynamoDB, ECS, ELB, Route 53, CloudFront, CloudFormation, Monitoring, Messaging, Security | 16 service areas · 812 notes |
| [Nginx](Nginx/) | Reverse proxy, load balancing, SSL/TLS, caching, rate limiting, security headers, troubleshooting | 29 concepts · 6 CLI refs · 28 troubleshooting |
| [Redis](Redis/) | Data structures, caching, pub/sub, persistence, clustering, Django/FastAPI integration, production, interview prep | 136 notes across 9 sections |
| [gRPC](gRPC/) | Protocol Buffers, HTTP/2, all 4 RPC types, Python implementation, production deployment, troubleshooting, interview prep | 8 sections · 98 notes · 6 sample projects |

---

## 🗂️ How Topics Are Organized

Each topic follows a consistent structure, though the exact folders vary by technology:

| Folder | Contains |
|--------|----------|
| `concepts/` | Theory notes, architecture deep dives, and explained examples |
| `cli/` | Quick-reference command sheets |
| `troubleshooting/` | Real problems encountered during hands-on practice, with root cause and fix |
| `interview/` | Interview Q&A organized by difficulty level |
| `cheatsheets/` | Condensed revision sheets and production checklists |
| `sample projects/` | Working code examples and starter projects |
| `production/` | Deployment, security, scaling, and operational best practices |
| `images/` | Supporting screenshots and diagrams |

Every topic — and most of its subfolders — has its own `README.md` indexing what's inside, so you can drill down from here to any specific note.

---

## 🎯 Purpose

This repository exists to:

- **Consolidate learning** into searchable, structured notes rather than scattered files
- **Prepare for backend engineering interviews** — concept explanations and interview Q&A are built into most topics
- **Document real issues** hit during hands-on practice, not just textbook theory
- **Provide working code** — sample projects and config files you can run immediately

---

## 🗺️ Learning Roadmap

```
Docker                ← Containerize anything
   │
   ▼
Kubernetes            ← Orchestrate containers at scale
   │
   ▼
AWS                   ← Cloud infrastructure & services
   │
   ▼
Nginx                 ← Reverse proxy & load balancing
   │
   ▼
Redis                 ← Caching, pub/sub & data structures
   │
   ▼
gRPC                  ← High-performance service communication
```

Each topic is self-contained — you can start with any one that matches your current needs.

---

## 🚀 Quick Links

| I want to... | Go to |
|--------------|-------|
| Learn Docker from scratch | [Docker/concepts/](Docker/concepts/) |
| Look up a kubectl command | [Kubernetes/cli/](Kubernetes/cli/) |
| Understand AWS IAM | [AWS/concepts/IAM/](AWS/concepts/IAM/) |
| Fix an Nginx error | [Nginx/troubleshooting/](Nginx/troubleshooting/) |
| Set up Redis caching with Django | [Redis/Django-FastAPI integration/](Redis/Django-FastAPI%20integration/) |
| Build a Python gRPC service | [gRPC/03- Python/](gRPC/03-%20Python/) |
| Practice gRPC with sample projects | [gRPC/04- Sample Projects/](gRPC/04-%20Sample%20Projects/) |
| Prepare for backend interviews | [gRPC/07- Interview/](gRPC/07-%20Interview/) · [Redis/interview/](Redis/interview/) |

---

*Aranya Majumdar — [github.com/aranya-code](https://github.com/aranya-code)*