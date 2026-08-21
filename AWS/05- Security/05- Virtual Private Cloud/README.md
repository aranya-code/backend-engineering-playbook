# README

## Overview

This section covers the security architecture of Amazon VPCs, with emphasis on controlling network reachability, enforcing least privilege, protecting workloads, and maintaining visibility into network activity.

The material progresses from core VPC security controls to production security practices:

```text
VPC Security
    |
    +-- Security Architecture
    |     +-- VPC Security Overview
    |
    +-- Workload-Level Controls
    |     +-- Security Groups
    |     +-- Security Group Rules and Chaining
    |
    +-- Subnet-Level Controls
    |     +-- Network ACLs
    |     +-- Ephemeral Ports and NACLs
    |
    +-- Control Comparison
    |     +-- Security Groups vs Network ACLs
    |
    +-- AWS Service Access
    |     +-- VPC Endpoint Policies
    |
    +-- Visibility and Detection
    |     +-- VPC Flow Logs and Security Analysis
    |
    +-- Production Hardening
          +-- VPC Security Best Practices
```

## Topics

| File | Topic | Primary Focus |
|---|---|---|
| [01- VPC Security Overview](./01-%20VPC%20Security%20Overview.md) | VPC Security Overview | Security architecture, segmentation, least privilege, defense in depth, and production VPC security |
| [02- Security Groups](./02-%20Security%20Groups.md) | Security Groups | Stateful workload-level network access control |
| [03- Security Group Rules and Chaining](./03-%20Security%20Group%20Rules%20and%20Chaining.md) | Security Group Rules and Chaining | Rule design, Security Group references, service-to-service authorization, and chaining |
| [04- Network ACLs](./04-%20Network%20ACLs.md) | Network ACLs | Stateless subnet-level filtering, rule ordering, and NACL design |
| [05- Ephemeral Ports and Network ACLs](./05-%20Ephemeral%20Ports%20and%20Network%20ACLs.md) | Ephemeral Ports and NACLs | Return traffic, ephemeral ports, stateless filtering, and troubleshooting |
| [06- Security Groups vs Network ACLs](./06-%20Security%20Groups%20vs%20Network%20ACLs.md) | Security Groups vs NACLs | Architectural differences, appropriate use cases, and layered network security |
| [07- VPC Endpoint Policies](./07-%20VPC%20Endpoint%20Policies.md) | VPC Endpoint Policies | Restricting access to AWS services through VPC endpoints |
| [08- VPC Flow Logs and Security Analysis](./08-%20VPC%20Flow%20Logs%20and%20Security%20Analysis.md) | VPC Flow Logs | Network visibility, traffic analysis, investigation, and security monitoring |
| [09- VPC Security Best Practices](./09-%20VPC%20Security%20Best%20Practices.md) | VPC Security Best Practices | Production hardening, observability, IAM, encryption, egress, IaC, and operational security |

## Recommended Reading Order

The files are intentionally ordered so that each topic builds on the previous one.

### Security Architecture

Start with [01- VPC Security Overview](./01-%20VPC%20Security%20Overview.md).

This establishes the security model used throughout the section:

```text
Least Privilege
      +
Network Segmentation
      +
Controlled Routing
      +
Defense in Depth
      +
Encryption
      +
Observability
```

### Security Groups

Continue with [02- Security Groups](./02-%20Security%20Groups.md).

Security Groups are the primary workload-level network control used to define which traffic can reach resources such as:

- EC2 instances
- ECS workloads
- Load balancers
- RDS
- ElastiCache
- Other supported VPC resources

### Security Group Relationships

Then study [03- Security Group Rules and Chaining](./03-%20Security%20Group%20Rules%20and%20Chaining.md).

The focus moves from individual rules to architectural relationships:

```text
ALB SG
  |
  | HTTPS
  v
API SG
  |
  | PostgreSQL
  v
Database SG
```

This is particularly important for dynamic backend architectures using ECS, EKS, Auto Scaling, and microservices.

### Network ACLs

Study [04- Network ACLs](./04-%20Network%20ACLs.md) after Security Groups.

This introduces subnet-level, stateless filtering and explains how NACLs complement Security Groups.

### Ephemeral Ports

Then study [05- Ephemeral Ports and Network ACLs](./05-%20Ephemeral%20Ports%20and%20Network%20ACLs.md).

This topic is important when designing restrictive NACLs because return traffic commonly uses dynamically allocated client-side ports.

```text
Client
10.0.1.10:49152
      |
      | TCP
      v
Server
10.0.2.20:443
      |
      | Response
      v
10.0.1.10:49152
```

Because NACLs are stateless, both directions must be evaluated.

### Security Groups vs NACLs

Use [06- Security Groups vs Network ACLs](./06-%20Security%20Groups%20vs%20Network%20ACLs.md) to consolidate the distinction between the two controls.

The core comparison is:

| Property | Security Group | Network ACL |
|---|---|---|
| Scope | Resource / network interface | Subnet |
| State | Stateful | Stateless |
| Rules | Allow rules | Allow and deny rules |
| Rule ordering | Not based on numeric priority | Lowest rule number evaluated first |
| Return traffic | Automatically tracked | Must be explicitly permitted |
| Typical role | Primary workload control | Subnet-level defense in depth |

### VPC Endpoint Policies

Study [07- VPC Endpoint Policies](./07-%20VPC%20Endpoint%20Policies.md) to understand how private workloads can access supported AWS services through VPC endpoints with additional policy controls.

Conceptually:

```text
Private Workload
      |
      v
VPC Endpoint
      |
      v
Endpoint Policy
      |
      v
AWS Service
```

This becomes especially relevant when reducing public internet dependency and controlling access to AWS services.

### Flow Logs and Security Analysis

Study [08- VPC Flow Logs and Security Analysis](./08-%20VPC%20Flow%20Logs%20and%20Security%20Analysis.md) after understanding the network controls.

The focus changes from:

```text
"Can traffic flow?"
```

to:

```text
"What traffic actually occurred?"
```

Flow Logs provide valuable telemetry for:

- Connectivity troubleshooting
- Security investigations
- Rejected traffic analysis
- Unexpected network paths
- Traffic baselining
- Incident response

### Production Security

Finish with [09- VPC Security Best Practices](./09-%20VPC%20Security%20Best%20Practices.md).

This consolidates the preceding concepts into a production-oriented security model covering:

- Least privilege
- Network segmentation
- Egress control
- IAM
- Encryption
- VPC endpoints
- Flow Logs
- GuardDuty
- Security Hub
- Infrastructure as Code
- CI/CD security validation
- High availability
- Disaster recovery
- Multi-account architecture
- Security monitoring

## Security Model

The section should ultimately be understood as a layered security architecture rather than a collection of independent AWS features.

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph VPC["Amazon VPC"]
        Routing["Route Tables"]

        subgraph Public["Public Subnets"]
            ALB["Public Load Balancer"]
            NAT["NAT Gateway"]
        end

        subgraph App["Private Application Subnets"]
            API["Django / FastAPI"]
            Worker["Celery Workers"]
            Services["Microservices"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL / RDS"]
            Redis["Redis"]
            Kafka["Kafka"]
        end

        SG["Security Groups"]
        NACL["Network ACLs"]
        Endpoint["VPC Endpoints"]
        Flow["VPC Flow Logs"]
    end

    Internet --> ALB
    ALB --> API
    API --> DB
    API --> Redis
    Worker --> Kafka
    Worker --> DB

    API --> NAT
    Worker --> Endpoint

    Routing --> Public
    Routing --> App
    Routing --> Data

    NACL --> Public
    NACL --> App
    NACL --> Data

    SG --> API
    SG --> Worker
    SG --> DB
    SG --> Redis
    SG --> Kafka

    App --> Flow
    Data --> Flow
```

The key architectural relationship is:

```text
Routing
   |
   v
Network Reachability
   |
   v
NACL
   |
   v
Security Group
   |
   v
Workload
   |
   v
Application Authentication
   |
   v
Application Authorization
```

Each layer solves a different problem.

## Backend Engineering Relevance

VPC security directly affects the architecture of modern backend systems.

### Django and FastAPI

A typical production deployment should look conceptually like:

```text
Internet
   |
   v
ALB
   |
   v
Private Django / FastAPI
   |
   +---- PostgreSQL
   +---- Redis
   +---- Celery
   +---- Kafka
   +---- AWS Services
```

The API should not need direct public exposure simply because it serves internet-facing clients.

### Microservices

Microservices require explicit service-to-service communication rules.

```text
API
 |
 +--> User Service
 |
 +--> Payment Service
 |
 +--> Inventory Service
```

Security Groups and application-level authorization should work together to enforce these relationships.

### Kubernetes

For EKS environments, VPC-level controls are complemented by Kubernetes-level controls:

```text
VPC Security Groups
        +
Network ACLs
        +
Kubernetes Network Policies
        +
IAM / Pod Identity
        +
Application Authentication
```

### Redis, PostgreSQL, and Kafka

Stateful services should generally remain private and should only accept traffic from workloads that require them.

```text
API SG
  |
  +----> PostgreSQL SG :5432
  |
  +----> Redis SG :6379

Worker SG
  |
  +----> Kafka SG :9092
```

This prevents broad internal network access from becoming implicit authorization.

## Production Security Checklist

Use this checklist when reviewing a production VPC:

- [ ] Workloads that do not require public connectivity are private.
- [ ] Public IP addresses are intentional.
- [ ] Public load balancers are the intended internet entry point.
- [ ] Database resources are not publicly accessible.
- [ ] Redis is not publicly accessible.
- [ ] Kafka brokers are not broadly exposed.
- [ ] Security Groups follow least privilege.
- [ ] Security Group references are preferred over broad CIDRs where appropriate.
- [ ] `0.0.0.0/0` ingress rules are justified.
- [ ] IPv6 exposure has been reviewed.
- [ ] Egress requirements are documented.
- [ ] NACL rules are intentionally designed.
- [ ] NACL return traffic and ephemeral ports are understood.
- [ ] Route tables do not provide unnecessary reachability.
- [ ] VPC endpoints are used where appropriate.
- [ ] Flow Logs are enabled where required.
- [ ] CloudTrail is enabled.
- [ ] Threat detection is configured where required.
- [ ] Administrative access does not depend on publicly exposed SSH where avoidable.
- [ ] Secrets are stored in managed secret systems.
- [ ] Encryption is enabled for sensitive data and traffic where appropriate.
- [ ] VPC configuration is managed through Infrastructure as Code.
- [ ] CI/CD validates security-sensitive infrastructure changes.
- [ ] Configuration drift is detected.
- [ ] Security controls are included in disaster recovery planning.

## Navigation

| Section | Files |
|---|---|
| Security Architecture | [01- VPC Security Overview](./01-%20VPC%20Security%20Overview.md) |
| Security Groups | [02- Security Groups](./02-%20Security%20Groups.md) |
| Security Group Chaining | [03- Security Group Rules and Chaining](./03-%20Security%20Group%20Rules%20and%20Chaining.md) |
| Network ACLs | [04- Network ACLs](./04-%20Network%20ACLs.md) |
| Ephemeral Ports | [05- Ephemeral Ports and Network ACLs](./05-%20Ephemeral%20Ports%20and%20Network%20ACLs.md) |
| Comparison | [06- Security Groups vs Network ACLs](./06-%20Security%20Groups%20vs%20Network%20ACLs.md) |
| VPC Endpoints | [07- VPC Endpoint Policies](./07-%20VPC%20Endpoint%20Policies.md) |
| Network Visibility | [08- VPC Flow Logs and Security Analysis](./08-%20VPC%20Flow%20Logs%20and%20Security%20Analysis.md) |
| Production Hardening | [09- VPC Security Best Practices](./09-%20VPC%20Security%20Best%20Practices.md) |

## Key Takeaways

- **VPC security is layered**: routing, Security Groups, NACLs, IAM, encryption, endpoints, and observability solve different security problems.
- **Security Groups are the primary workload-level control**: use explicit service relationships and least-privilege rules instead of broad network access.
- **NACLs require stateless networking knowledge**: rule ordering, return traffic, and ephemeral ports are critical when restrictive subnet-level filtering is used.
- **Visibility is part of security**: Flow Logs, CloudTrail, threat detection, and centralized analysis make security controls operationally useful.
- **Production security must be reproducible**: manage VPC security through Infrastructure as Code, validate changes through CI/CD, monitor drift, and include security controls in HA and disaster-recovery designs.