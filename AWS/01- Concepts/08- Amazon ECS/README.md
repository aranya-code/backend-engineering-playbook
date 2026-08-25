# Amazon ECS Concepts

The **Concepts** section provides a strong foundation in Amazon Elastic Container Service (ECS). It introduces the core building blocks, architecture, networking, security, storage, and service management required to understand how ECS runs containerized applications at scale.

Whether you're completely new to ECS or preparing for production deployments, these notes are designed to build your knowledge progressively—from basic concepts to advanced architectural components.

---

# Topics Covered

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Introduction](01-%20Introduction.md) | Introduction to Amazon ECS. |
| 02 | [Architecture](02-%20Architecture.md) | Architectural overview of ECS. |
| 03 | [Core Components](03-%20Core%20Components.md) | Core components of ECS. |
| 04 | [Launch Types](04-%20Launch%20Types.md) | Fargate and EC2 launch types. |
| 05 | [Task Definitions](05-%20Task%20Definitions.md) | Defining tasks and containers. |
| 06 | [Services](06-%20Services.md) | Managing long-running services. |
| 07 | [Networking](07-%20Networking.md) | Network configurations for ECS tasks. |
| 08 | [IAM Roles and Security](08-%20IAM%20Roles%20and%20Security.md) | Identity and Access Management in ECS. |
| 09 | [Load Balancing](09-%20Load%20Balancing.md) | Integrating ALB and NLB with ECS. |
| 10 | [Service Discovery](10-%20Service%20Discovery.md) | Cloud Map and DNS service discovery. |
| 11 | [Storage](11-%20Storage.md) | Persistent and ephemeral storage. |

---

# Learning Path

It is recommended to study the topics in the following order:

```
Introduction
      │
      ▼
Architecture
      │
      ▼
Core Components
      │
      ▼
Launch Types
      │
      ▼
Task Definitions
      │
      ▼
Services
      │
      ▼
Networking
      │
      ▼
IAM & Security
      │
      ▼
Load Balancing
      │
      ▼
Service Discovery
      │
      ▼
Storage
```

Each topic builds upon the previous one, so following the sequence will provide the best learning experience.

---

# Prerequisites

Before studying this section, it is helpful to have a basic understanding of:

- Docker fundamentals
- Containers and container images
- AWS IAM
- Amazon VPC
- EC2 basics
- Basic networking concepts (IP addresses, ports, DNS)
- Load balancers

---

# After Completing This Section

You will be able to:

- Explain the ECS architecture confidently.
- Understand every major ECS component.
- Choose between EC2 and Fargate launch types.
- Design ECS networking correctly.
- Configure IAM roles securely.
- Deploy services behind load balancers.
- Configure service discovery.
- Select appropriate storage options.
- Read production ECS architectures with confidence.

---
