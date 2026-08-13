# Amazon ECS

A comprehensive, production-focused guide to Amazon Elastic Container Service — covering architecture, core components, networking, security, scaling, deployment strategies, monitoring, CI/CD, disaster recovery, infrastructure as code, and real-world production design.

These notes are written for **Senior Backend Engineers**, **DevOps Engineers**, **Platform Engineers**, and **Solutions Architects** who need to design, deploy, and operate containerized workloads on AWS at production scale.

---

## Why ECS?

Amazon ECS is AWS's fully managed container orchestration service. It runs Docker containers without requiring you to install, operate, or scale your own cluster management infrastructure.

```text
┌──────────────────────────────────────────────────────────────────┐
│                       ECS Architecture                           │
│                                                                  │
│   Client Request                                                 │
│        │                                                         │
│        ▼                                                         │
│   ┌──────────┐     ┌──────────────────┐     ┌────────────────┐  │
│   │   ALB /  │────▶│   ECS Service    │────▶│  Task (Docker  │  │
│   │   NLB    │     │  (desired count, │     │  containers)   │  │
│   │          │     │   scaling rules) │     │                │  │
│   └──────────┘     └──────────────────┘     └───────┬────────┘  │
│                                                     │            │
│                    ┌────────────────────────────────┘            │
│                    │                                             │
│          ┌─────────┴──────────┐                                  │
│          │                    │                                   │
│   ┌──────▼──────┐    ┌───────▼──────┐                           │
│   │  Fargate    │    │    EC2       │                            │
│   │ (Serverless │    │ (Self-      │                             │
│   │  compute)   │    │  managed    │                             │
│   │             │    │  instances) │                             │
│   └─────────────┘    └─────────────┘                            │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Supporting Services:                                     │  │
│   │  ECR (images) · IAM (security) · CloudWatch (monitoring) │  │
│   │  Cloud Map (discovery) · Secrets Manager · EFS/EBS       │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**ECS vs EKS — when to choose ECS:**
- You want a simpler operational model (no Kubernetes cluster management)
- Your team is already invested in the AWS ecosystem
- You prefer AWS-native integrations (ALB, IAM, CloudWatch, CodeDeploy)
- You want Fargate for fully serverless containers with zero EC2 management

**When ECS is NOT the right choice:**
- You need multi-cloud portability → use EKS / Kubernetes
- Your team already has deep Kubernetes expertise
- You need advanced scheduling (CronJobs, DaemonSets, StatefulSets) → use EKS

---

## Module Index

This playbook contains **27 content files** across **4 modules**, organized from foundational concepts to hands-on production deployment.

| # | Module | Files | Focus |
|---|--------|-------|-------|
| 01 | [Concepts](./01-%20Concepts/) | 11 | Architecture, core components, launch types, task definitions, services, networking, IAM, load balancing, service discovery, storage |
| 02 | [Production](./02-%20Production/) | 12 | Auto scaling, capacity providers, deployment strategies, placement, monitoring, EventBridge, CI/CD, cost optimization, security, DR, production architectures |
| 03 | [Infrastructure](./03-%20Infrastructure/) | 1 | Terraform-based ECS deployment |
| 04 | [Hands On](./04-%20Hands%20On/) | 3 | Labs, end-to-end production project, real-world case studies |

---

## Learning Path

```text
Phase 1 — Foundations                  Phase 2 — Production Operations
┌────────────────────────┐            ┌──────────────────────────────┐
│  01- Concepts          │            │  02- Production              │
│                        │            │                              │
│  Introduction          │            │  Auto Scaling                │
│       ↓                │            │       ↓                      │
│  Architecture          │            │  Capacity Providers          │
│       ↓                │            │       ↓                      │
│  Core Components       │            │  Deployment Strategies       │
│       ↓                │    ────▶   │       ↓                      │
│  Launch Types          │            │  Monitoring & Logging        │
│       ↓                │            │       ↓                      │
│  Task Definitions      │            │  CI/CD & GitHub Actions      │
│       ↓                │            │       ↓                      │
│  Services, Networking  │            │  Security, Cost, DR          │
│       ↓                │            │       ↓                      │
│  IAM, LB, Discovery   │            │  Production Architectures    │
└────────────────────────┘            └──────────────┬───────────────┘
                                                     │
                                                     ▼
                              ┌──────────────────────────────────────┐
                              │  03- Infrastructure                  │
                              │  Terraform Deployment                │
                              └──────────────┬───────────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────────────┐
                              │  04- Hands On                        │
                              │  Labs → Production Project → Cases   │
                              └──────────────────────────────────────┘
```

---

## Module Breakdown

### 01 — Concepts (11 files)

Foundational ECS knowledge — from architecture to storage. Read these sequentially before moving to production topics.

| # | File | Topic |
|---|------|-------|
| 01 | [Introduction](./01-%20Concepts/01-%20Introduction.md) | What ECS is, managed vs self-managed orchestration, Fargate vs EC2 |
| 02 | [Architecture](./01-%20Concepts/02-%20Architecture.md) | Control plane, data plane, cluster architecture, request flow |
| 03 | [Core Components](./01-%20Concepts/03-%20Core%20Components.md) | Clusters, tasks, services, task definitions, container definitions |
| 04 | [Launch Types](./01-%20Concepts/04-%20Launch%20Types.md) | Fargate vs EC2 — pricing, control, networking, use cases |
| 05 | [Task Definitions](./01-%20Concepts/05-%20Task%20Definitions.md) | Container definitions, resource limits, environment variables, volumes |
| 06 | [Services](./01-%20Concepts/06-%20Services.md) | Desired count, health checks, deployment configuration, service types |
| 07 | [Networking](./01-%20Concepts/07-%20Networking.md) | awsvpc mode, bridge mode, host mode, security groups, VPC design |
| 08 | [IAM Roles and Security](./01-%20Concepts/08-%20IAM%20Roles%20and%20Security.md) | Task role vs execution role, least privilege, secrets management |
| 09 | [Load Balancing](./01-%20Concepts/09-%20Load%20Balancing.md) | ALB vs NLB, target groups, health checks, path-based routing |
| 10 | [Service Discovery](./01-%20Concepts/10-%20Service%20Discovery.md) | AWS Cloud Map, DNS-based discovery, service-to-service communication |
| 11 | [Storage](./01-%20Concepts/11-%20Storage.md) | EFS, EBS, bind mounts, ephemeral storage, shared volumes |

---

### 02 — Production (12 files)

Everything needed to run ECS in production — scaling, deployment, monitoring, security, and disaster recovery.

| # | File | Topic |
|---|------|-------|
| 01 | [Auto Scaling](./02-%20Production/01-%20Auto%20Scaling.md) | Target tracking, step scaling, scheduled scaling, scaling policies |
| 02 | [Capacity Providers](./02-%20Production/02-%20Capacity%20Providers.md) | Fargate, Fargate Spot, EC2 Auto Scaling Group capacity providers |
| 03 | [Deployment Strategies](./02-%20Production/03-%20Deployment%20Strategies.md) | Rolling update, blue/green (CodeDeploy), canary, circuit breaker |
| 04 | [Placement Strategies and Constraints](./02-%20Production/04-%20Placement%20Strategies%20and%20Constraints.md) | Spread, binpack, random, attribute-based constraints, AZ balancing |
| 05 | [Monitoring and Logging](./02-%20Production/05-%20Monitoring%20and%20Logging.md) | CloudWatch metrics, Container Insights, CloudWatch Logs, X-Ray |
| 06 | [EventBridge Integration](./02-%20Production/06-%20EventBridge%20Integration.md) | Task state change events, automated responses, event-driven scaling |
| 07 | [CI/CD and GitHub Actions](./02-%20Production/07-%20CI-CD%20and%20GitHub%20Actions.md) | Build → push ECR → deploy ECS pipeline, GitHub Actions workflows |
| 08 | [Cost Optimization](./02-%20Production/08-%20Cost%20Optimization.md) | Fargate Spot, right-sizing, Savings Plans, reserved instances |
| 09 | [Security Best Practices](./02-%20Production/09-%20Security%20Best%20Practices.md) | Image scanning, network isolation, secrets, runtime security |
| 10 | [Production Architectures](./02-%20Production/10-%20Production%20Architectures.md) | Multi-AZ, microservices, SaaS platforms, event-driven patterns |
| 11 | [Disaster Recovery and High Availability](./02-%20Production/11-%20Disaster%20Recovery%20and%20High%20Availability.md) | Multi-AZ failover, cross-region DR, service recovery, rollback |
| 12 | [Best Practices Checklist](./02-%20Production/12-%20Best%20Practices%20Checklist.md) | Production readiness checklist across networking, security, scaling, monitoring |

---

### 03 — Infrastructure (1 file)

Infrastructure as Code for ECS deployments.

| # | File | Topic |
|---|------|-------|
| 01 | [Terraform Deployment](./03-%20Infrastructure/01-%20Terraform%20Deployment.md) | Complete Terraform modules for ECS cluster, service, ALB, IAM, ECR |

---

### 04 — Hands On (3 files)

Practical exercises and real-world implementations.

| # | File | Topic |
|---|------|-------|
| 01 | [Hands-On Labs](./04-%20Hands%20On/01-%20Hands-On%20Labs.md) | Step-by-step labs for deploying containers on ECS |
| 02 | [End-to-End Production Project](./04-%20Hands%20On/02-%20End-to-End%20Production%20Project.md) | Full production deployment: ECS Fargate + ALB + RDS + ECR + CI/CD |
| 03 | [Real World Case Studies](./04-%20Hands%20On/03-%20Real%20World%20Case%20Studies.md) | Production architectures from real-world ECS deployments |

---

## Quick Reference

### ECS Core Concepts

```text
Cluster         A logical grouping of tasks and services.
                One cluster per environment (dev, staging, prod).

Task Definition A blueprint (like a Dockerfile for ECS) that describes:
                - Container image, CPU, memory
                - Port mappings, environment variables
                - IAM roles, log configuration
                Versioned — each revision is immutable.

Task            A running instance of a task definition.
                One task = one or more Docker containers running together.

Service         Maintains a desired count of tasks.
                Handles rolling deployments, health checks, and scaling.
                Integrates with ALB/NLB for traffic distribution.

Container       A Docker container running inside a task.
                One task can run multiple containers (sidecar pattern).
```

### ECS Limits

| Resource | Limit |
|----------|-------|
| Clusters per region | 10,000 |
| Services per cluster | 5,000 |
| Tasks per service | 5,000 |
| Containers per task definition | 10 |
| Task definition revisions | Unlimited |
| Max task CPU (Fargate) | 16 vCPU |
| Max task memory (Fargate) | 120 GB |
| Max ephemeral storage (Fargate) | 200 GB |

### Fargate vs EC2 at a Glance

```text
                    Fargate                     EC2
                    ─────────────────           ─────────────────
Infra Management    None (serverless)           You manage instances
Pricing             Per-task (vCPU + GB/hr)     Per-instance (EC2 pricing)
Scaling             Instant task launch         ASG + Capacity Provider
Networking          awsvpc only (ENI per task)  awsvpc, bridge, host
GPU Support         No                          Yes
Spot Pricing        Fargate Spot (70% off)      EC2 Spot Instances
Best For            Most workloads              GPU, large batch, cost control
```

### Key Design Principles

```text
1. Use Fargate unless you need GPU, custom AMI, or extreme cost optimization
2. One service per microservice — don't colocate unrelated containers
3. Use awsvpc networking mode for task-level security group isolation
4. Separate Task Role (app permissions) from Execution Role (ECS permissions)
5. Store secrets in Secrets Manager, never in environment variables or images
6. Enable Container Insights from day one for CPU, memory, and network metrics
7. Use blue/green deployments (CodeDeploy) for zero-downtime production releases
8. Set deployment circuit breaker to auto-rollback failed deployments
9. Right-size tasks: start small, monitor CloudWatch, adjust CPU/memory
10. Use Fargate Spot for non-critical workloads to save up to 70%
```

---

## Prerequisites

- Docker fundamentals (images, containers, Dockerfile)
- AWS core services (VPC, IAM, EC2, ALB)
- Basic networking (subnets, security groups, DNS)
- CI/CD concepts (pipelines, build/test/deploy)
- Linux command line basics
- Python / Django / FastAPI experience (optional, for hands-on labs)

---

## Who These Notes Are For

- **Senior Backend Engineers** deploying containerized applications
- **DevOps / Platform Engineers** building container platforms on AWS
- **Cloud Engineers** designing ECS infrastructure
- **Solutions Architects** evaluating ECS vs EKS
- **SREs** operating and troubleshooting ECS in production
- **Interview candidates** preparing for AWS and system design interviews

---

## AWS Services Covered

```text
Core ECS                  Networking               Security
────────────              ──────────               ────────
Amazon ECS                Amazon VPC               AWS IAM
AWS Fargate               ALB / NLB                Secrets Manager
Amazon ECR                Security Groups          Systems Manager
AWS Cloud Map             Route 53                 KMS

Monitoring                CI/CD                    Storage
──────────                ─────                    ───────
CloudWatch Metrics        GitHub Actions           Amazon EFS
CloudWatch Logs           AWS CodePipeline         Amazon EBS
Container Insights        AWS CodeBuild            Ephemeral Storage
AWS X-Ray                 AWS CodeDeploy
EventBridge               Terraform
```

---