# ECS Networking

# Why Networking Matters

Most ECS production issues are networking issues.

Examples:

- Task cannot reach database
- ALB cannot reach tasks
- Tasks cannot pull images
- Services cannot communicate
- Internet access failures

Understanding ECS networking is essential for production environments.

---

# ECS Networking Overview

When a container runs, it must communicate with:

```text
Users
Databases
Other Services
AWS APIs
Internet
```

Networking enables this communication.

---

# ECS Network Modes

ECS supports three primary network modes:

```text
awsvpc
bridge
host
```

---

# awsvpc Mode

Recommended mode.

Required for:

```text
Fargate
```

Each task receives:

- Private IP Address
- Elastic Network Interface (ENI)
- Security Group

---

# Architecture

```text
Task A
 ↓
10.0.1.10

Task B
 ↓
10.0.1.11
```

Each task behaves like a virtual machine.

---

# Benefits

## Network Isolation

Each task has dedicated networking.

---

## Security Group Per Task

Granular access control.

---

## Simpler Networking

No port conflicts.

---

## Better Security

Independent network boundaries.

---

# awsvpc Example

```text
ALB
 ↓
Task A (10.0.1.10)
 ↓
Port 8000

Task B (10.0.1.11)
 ↓
Port 8000
```

No conflicts.

---

# bridge Mode

Traditional Docker networking.

Architecture:

```text
EC2 Instance
       ↓
Docker Bridge
       ↓
Containers
```

Containers share the host network.

---

# Example

```text
Container A
Port 8000

Container B
Port 8001
```

Ports must be unique.

---

# Advantages

- Lower networking overhead
- Mature Docker model

---

# Disadvantages

- Port conflicts
- Shared networking
- More complex configuration

---

# host Mode

Containers use the host network directly.

Architecture:

```text
EC2 Instance
      ↓
Container
```

No network abstraction.

---

# Advantages

- Lowest latency
- Maximum performance

---

# Disadvantages

- Port conflicts
- Reduced isolation
- Limited scalability

---

# Network Mode Comparison

| Feature | awsvpc | bridge | host |
|----------|---------|---------|------|
| Fargate Support | Yes | No | No |
| Security Group Per Task | Yes | No | No |
| Port Conflicts | No | Possible | Common |
| Isolation | High | Medium | Low |
| Complexity | Low | Medium | Medium |

---

# Elastic Network Interfaces (ENI)

## What is an ENI?

Elastic Network Interface = Virtual Network Card.

In awsvpc mode:

```text
Task
 ↓
ENI
 ↓
Private IP
```

Each task gets its own ENI.

---

# Why ENIs Matter

Provide:

- Private IP Address
- Security Group Attachment
- VPC Connectivity

---

# Security Groups

Think of Security Groups as:

```text
Virtual Firewall
```

Controls:

- Inbound Traffic
- Outbound Traffic

---

# Example

ALB Security Group:

```text
Allow:
80
443
```

---

Task Security Group:

```text
Allow:
8000
From ALB Only
```

---

Database Security Group:

```text
Allow:
5432
From ECS Tasks
```

---

# Security Group Flow

```text
Internet
 ↓
ALB SG
 ↓
ECS SG
 ↓
RDS SG
```

Layered security.

---

# Public and Private Subnets

## Public Subnet

Has route to:

```text
Internet Gateway
```

Resources can receive internet traffic.

---

Examples

- ALB
- Bastion Host

---

# Private Subnet

No direct internet access.

Recommended location for:

```text
ECS Tasks
Databases
Redis
```

---

# Production Architecture

```text
Public Subnet
 ↓
ALB

Private Subnet
 ↓
ECS Tasks

Private Subnet
 ↓
RDS
```

---

# Internet Gateway

Provides internet connectivity.

Architecture:

```text
VPC
 ↓
Internet Gateway
 ↓
Internet
```

---

# NAT Gateway

Private subnets often need outbound internet access.

Examples:

- Pull Docker images
- Access AWS APIs
- Download updates

---

Architecture

```text
Private ECS Task
       ↓
NAT Gateway
       ↓
Internet
```

---

# Why ECS Tasks Need NAT

Examples:

```text
Pull Image From ECR
Call External API
Download Packages
```

Without NAT:

```text
Connection Failure
```

---

# Service-to-Service Communication

Microservices often communicate internally.

Example:

```text
Order Service
      ↓
Payment Service
```

---

# Communication Methods

## Internal Load Balancer

```text
Order Service
      ↓
Internal ALB
      ↓
Payment Service
```

---

## Cloud Map

DNS-based service discovery.

Example:

```text
payment.internal
```

instead of:

```text
10.0.1.20
```

---

# DNS Resolution

AWS provides:

```text
Route53 Resolver
```

Handles:

- Internal DNS
- External DNS

---

# ECS + ALB Networking Flow

```text
User
 ↓
Route53
 ↓
ALB
 ↓
Target Group
 ↓
ECS Task
```

---

# Target Groups

ALB forwards traffic to:

```text
Target Group
```

Targets:

```text
ECS Tasks
```

---

# Health Check Flow

```text
ALB
 ↓
/health
 ↓
Task
```

Healthy:

```text
Traffic Allowed
```

Unhealthy:

```text
Traffic Blocked
```

---

# Common Networking Problems

## ALB Cannot Reach Task

Possible causes:

- Wrong Security Group
- Wrong Port Mapping
- Failed Health Checks

---

## Task Cannot Reach Database

Possible causes:

- Security Group Misconfiguration
- Wrong Endpoint
- Wrong Port

---

## Task Cannot Pull Images

Possible causes:

- Missing NAT Gateway
- Missing ECR Permissions

---

## Service Communication Failure

Possible causes:

- DNS Issues
- Security Group Rules
- Network ACLs

---

# Troubleshooting Checklist

Check:

```text
Security Groups
Route Tables
Subnets
ENIs
Target Groups
Health Checks
```

---

# Production Best Practices

## Use awsvpc Mode

Recommended for modern deployments.

---

## Deploy Tasks in Private Subnets

Reduce attack surface.

---

## Restrict Security Groups

Allow only required traffic.

---

## Use Internal DNS

Avoid hardcoded IPs.

---

## Monitor Networking Metrics

Use CloudWatch.

---

# Common Interview Questions

## Why Does Fargate Require awsvpc?

Because every task receives its own ENI.

---

## What is an ENI?

Virtual network interface attached to tasks.

---

## Difference Between Public and Private Subnets?

Public:

Direct internet access.

Private:

No direct internet access.

---

## Why Use NAT Gateway?

Allows outbound internet access from private subnets.

---

## Why Use Security Groups?

Control network traffic.

---

# Senior Engineer Perspective

Most ECS outages are not container problems.

They are:

- Security Group Issues
- Route Table Issues
- Health Check Failures
- DNS Problems

A senior engineer always validates networking before debugging application code.

---

# Key Takeaways

- ECS supports awsvpc, bridge, and host modes.
- awsvpc is the recommended networking mode.
- Fargate requires awsvpc.
- Security Groups control traffic.
- Private subnets are preferred for ECS tasks.
- NAT Gateway enables outbound internet access.
- Cloud Map provides service discovery.
- Networking is often the root cause of ECS production issues.
