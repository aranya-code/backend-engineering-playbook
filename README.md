# README

## Overview

This is a structured, hands-on backend engineering knowledge base built for real-world engineering reference, interview preparation, and continuous learning.

Each section covers a distinct technology or engineering discipline from foundational concepts through production-grade patterns, CLI operations, troubleshooting, architecture, and senior-level interview preparation.

The material is built around practical backend engineering skills:

```text
Language and Data Tooling
        ↓
Infrastructure and Containerization
        ↓
Data Stores and Messaging
        ↓
Cloud and Deployment
        ↓
CI/CD and Automation
        ↓
System Design and Architecture
```

Every section and most subfolders have their own `README.md` indexing what is inside, so you can navigate from here to any specific note.

## Navigation

| # | Section | Description |
|---|---|---|
| 01 | [Python](./Python/) | Production-oriented Python for backend engineers: OOP, concurrency, memory, type system, testing, and backend patterns. |
| 02 | [SQL](./SQL/) | Relational database fundamentals, query writing, schema design, performance, transactions, and PostgreSQL operations. |
| 03 | [Numpy](./Numpy/) | NumPy for backend and data-processing workloads: arrays, numerical operations, performance, and applied projects. |
| 04 | [Pandas](./Pandas/) | Production-focused Pandas reference: data wrangling, transformation, grouping, performance, and backend data engineering. |
| 05 | [Docker](./Docker/) | Container fundamentals, images, volumes, networking, Compose, production Dockerfiles, and troubleshooting. |
| 06 | [Kubernetes](./Kubernetes/) | Core objects, networking, storage, Helm, RBAC, cluster orchestration, CLI reference, and sample manifests. |
| 07 | [AWS](./AWS/) | EC2, IAM, S3, VPC, Lambda, ECS, RDS, ELB, CloudFormation, and production cloud infrastructure across 13 service areas. |
| 08 | [CI-CD](./CI-CD/) | GitHub Actions CI/CD: workflows, security, Docker, AWS deployment, reusable workflows, runners, and production pipelines. |
| 09 | [Redis](./Redis/) | Data structures, caching patterns, pub/sub, persistence, clustering, Django/FastAPI integration, and production operations. |
| 10 | [MongoDB](./MongoDB/) | MongoDB engineering from concepts and architecture through operations, performance, security, backup, and integration. |
| 11 | [Nginx](./Nginx/) | Reverse proxy, load balancing, SSL/TLS, caching, rate limiting, security headers, and troubleshooting. |
| 12 | [Kafka](./Kafka/) | Apache Kafka for backend engineers: producers, consumers, topics, architecture, security, production, and troubleshooting. |
| 13 | [gRPC](./gRPC/) | Protocol Buffers, HTTP/2, all four RPC types, Python implementation, production deployment, and sample projects. |
| 14 | [System Design](./System%20Design/) | Distributed systems, networking, data storage, caching, messaging, scalability patterns, microservices, and architecture case studies. |

---

## Section Overview

| Section | Folders | Key Areas |
|---|---|---|
| Python | 13 | Fundamentals, OOP, Concurrency, Memory, Testing, Backend Python, Interview Preparation, Projects |
| SQL | 21 | Query Fundamentals, Advanced Queries, Schema Design, Performance, Transactions, Security, Interview Questions, Projects |
| Numpy | 8 | Fundamentals, Array Manipulation, Numerical Operations, Data Processing, Performance, Interview Preparation, Projects |
| Pandas | 13 | Data Wrangling, Transformation, Grouping, Strings and Datetime, Performance, Backend Engineering, Interview Preparation, Projects |
| Docker | 6 | Concepts, CLI, Production, Troubleshooting, Interview, Examples |
| Kubernetes | 5 | Concepts, CLI, Troubleshooting, Interview Questions, Sample Files |
| AWS | 13 | Concepts, Architecture, CLI, Operations, Security, Deployment, Troubleshooting, Interview Questions, Hands On, Best Practices |
| CI-CD | 13 | Fundamentals, Workflow Configuration, Security, Containers, Docker, AWS Deployment, Runners, Architecture, Interview Questions, Projects |
| Redis | 9 | Concepts, CLI, Caching, Django/FastAPI Integration, Production, Troubleshooting, Cheatsheets, Interview, Sample Projects |
| MongoDB | 12 | Concepts, Architecture, CLI, Operations, Security, Deployment, Backup and Recovery, Integration, Performance, Interview Questions, Projects |
| Nginx | 5 | Concepts, CLI, Troubleshooting, Interview, Sample Files |
| Kafka | 12 | Concepts, Producers, Consumers, Topics, Docker, CLI, Architecture, Security, Production, Troubleshooting, Interview, Sample Files |
| gRPC | 8 | Concepts, Protobuf, Python, Sample Projects, Production, Troubleshooting, Interview, Cheatsheets |
| System Design | 12 | Fundamentals, Distributed Systems, Networking, Data Storage, Caching, Messaging, Scalability, Microservices, Case Studies, Cloud Architecture, Interview Preparation |

---

## How Topics Are Organized

Each section follows a consistent internal structure, though the exact folder names vary by technology:

| Folder Pattern | Contains |
|---|---|
| `Concepts` / `Fundamentals` | Theory notes, architecture deep dives, and explained examples |
| `CLI` | Quick-reference command sheets |
| `Troubleshooting` | Real problems with root cause and resolution |
| `Interview` / `Interview Questions` | Q&A organized by topic and difficulty |
| `Production` | Deployment, security, scaling, and operational best practices |
| `Projects` | Working code examples and runnable starter projects |
| `Architecture` | System-level design patterns and decisions |
| `Cheatsheets` | Condensed revision sheets and production checklists |

---

## Learning Paths

### Backend Python Stack

```text
Python
    ↓
SQL (PostgreSQL)
    ↓
Redis
    ↓
MongoDB
    ↓
Docker
    ↓
Kubernetes
    ↓
AWS
    ↓
CI-CD (GitHub Actions)
```

### Data Engineering Stack

```text
Python
    ↓
Numpy
    ↓
Pandas
    ↓
SQL
    ↓
MongoDB
    ↓
Kafka
    ↓
Docker
    ↓
AWS
```

### Infrastructure and Systems Stack

```text
Docker
    ↓
Kubernetes
    ↓
Nginx
    ↓
AWS
    ↓
CI-CD
    ↓
System Design
```

Each section is self-contained — start with any technology that matches your current focus.

---

## Interview Preparation

Each section contains dedicated interview preparation material:

| Section | Interview Coverage |
|---|---|
| Python | OOP, concurrency, memory, type system, testing, backend patterns |
| SQL | Query design, schema, performance, transactions, PostgreSQL internals |
| Numpy | Array operations, performance, numerical computing |
| Pandas | Data wrangling, transformation, performance, backend integration |
| Docker | Container architecture, images, networking, Compose, production |
| Kubernetes | Objects, scheduling, networking, storage, RBAC, operations |
| AWS | 13 service areas including EC2, IAM, S3, ECS, Lambda, CloudFormation |
| CI-CD | GitHub Actions architecture, security, deployment strategies, troubleshooting |
| Redis | Data structures, caching, pub/sub, clustering, persistence |
| MongoDB | Schema design, aggregation, indexing, replication, sharding |
| Nginx | Reverse proxy, load balancing, SSL/TLS, performance, security |
| Kafka | Producers, consumers, partitions, replication, delivery guarantees |
| gRPC | Protocol Buffers, RPC types, streaming, production deployment |
| System Design | Scalability, distributed systems, CAP, databases, caching, messaging |

---

## Key Takeaways

- Every section is built around practical backend engineering skills — not just theory.
- The material covers the full engineering lifecycle: concepts, implementation, operations, troubleshooting, and interview preparation.
- Each section and most subfolders have their own README so the repository can be navigated from any entry point.
- The CI-CD section documents GitHub Actions as a complete production engineering platform across 13 structured folders and 14 hands-on projects.
- The AWS section is the largest, covering 13 service areas across 1,400+ notes.
- The SQL section is the most comprehensive relational database reference, covering 21 structured areas from query fundamentals through production operations.