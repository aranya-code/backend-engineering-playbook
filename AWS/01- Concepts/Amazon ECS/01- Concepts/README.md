# Amazon ECS Concepts

The **Concepts** section provides a strong foundation in Amazon Elastic Container Service (ECS). It introduces the core building blocks, architecture, networking, security, storage, and service management required to understand how ECS runs containerized applications at scale.

Whether you're completely new to ECS or preparing for production deployments, these notes are designed to build your knowledge progressively—from basic concepts to advanced architectural components.

---

# Topics Covered

# Quick Navigation

| Topic | Description |
|--------|-------------|
| [01- Introduction](01-%20Introduction.md) | Learn what Amazon ECS is, its use cases, benefits, and when to use it. |
| [02- Architecture](02-%20Architecture.md) | Understand the overall ECS architecture and how components interact. |
| [03- Core Components](03-%20Core%20Components.md) | Explore clusters, services, tasks, task definitions, and container instances. |
| [04- Launch Types](04-%20Launch%20Types.md) | Compare EC2, Fargate, and External launch types. |
| [05- Task Definitions](05-%20Task%20Definitions.md) | Learn how containers are configured using task definitions. |
| [06- Services](06-%20Services.md) | Understand how ECS services manage task lifecycle and deployments. |
| [07- Networking](07-%20Networking.md) | Explore VPC integration, awsvpc mode, ENIs, subnets, and security groups. |
| [08- IAM Roles and Security](08-%20IAM%20Roles%20and%20Security.md) | Secure ECS workloads using IAM roles, secrets, and least privilege access. |
| [09- Load Balancing](09-%20Load%20Balancing.md) | Configure Application and Network Load Balancers for ECS services. |
| [10- Service Discovery](10-%20Service%20Discovery.md) | Enable service-to-service communication using AWS Cloud Map. |
| [11- Storage](11-%20Storage.md) | Learn persistent and ephemeral storage options for ECS workloads. |

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
