# Amazon VPC (Virtual Private Cloud)

A comprehensive deep-dive study guide into **Amazon VPC** — AWS's foundational networking service that provides a logically isolated virtual network where you deploy and run AWS resources with complete control over IP addressing, subnets, routing, gateways, and security controls.

---

## 📚 Table of Contents

- [What is Amazon VPC?](#what-is-amazon-vpc)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Quick Reference Tables](#quick-reference-tables)
- [Navigation](#navigation)

---

## What is Amazon VPC?

Amazon VPC lets you provision a **logically isolated section of the AWS cloud** where you launch resources in a virtual network that you define. You have complete control over the network configuration — IP address ranges, subnets, route tables, gateways, and security settings.

VPC is the foundation of all AWS networking. Every EC2 instance, RDS database, Lambda function (VPC-attached), ECS task, and EKS pod runs inside a VPC. Getting the VPC design right is critical — these decisions are difficult to change after deployment.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | VPC fundamentals, CIDR blocks, reserved IPs, default vs custom VPC |
| 02 | [Subnets and Route Tables](./02-%20Subnets%20and%20Route%20Tables.md) | Public vs private subnets, three-tier design, Multi-AZ, subnet sizing, route table association |
| 03 | [Internet Gateway and NAT Gateway](./03-%20Internet%20Gateway%20and%20NAT%20Gateway.md) | IGW mechanics, NAT Gateway HA, NAT GW vs NAT Instance, pricing |
| 04 | [Security Groups and NACLs](./04-%20Security%20Groups%20and%20NACLs.md) | Stateful vs stateless, SG chaining, NACL rule ordering, ephemeral ports, traffic flow |
| 05 | [VPC Endpoints](./05-%20VPC%20Endpoints.md) | Gateway vs Interface endpoints, PrivateLink, endpoint policies, cost savings |
| 06 | [VPC Peering and Transit Gateway](./06-%20VPC%20Peering%20and%20Transit%20Gateway.md) | Point-to-point vs hub-and-spoke, transitive routing, TGW route tables, when to use each |
| 07 | [VPN and Direct Connect](./07-%20VPN%20and%20Direct%20Connect.md) | Site-to-Site VPN, Direct Connect, VIFs, DX Gateway, hybrid architecture patterns |
| 08 | [VPC Flow Logs](./08-%20VPC%20Flow%20Logs.md) | Log format, capture levels, destinations, security analysis, Athena queries |
| 09 | [VPC Design Patterns and Best Practices](./09-%20VPC%20Design%20Patterns%20and%20Best%20Practices.md) | CIDR planning, three-tier pattern, multi-account, private-only VPC, cost optimization |
| 10 | [Common Interview Questions](./10-%20Common%20Interview%20Questions.md) | 17 senior-level Q&A across all VPC domains |

---

## Module Structure

```
Virtual_Private_Cloud/
│
├── Fundamentals (01–03)
│   └── Introduction, Subnets & Route Tables,
│       Internet Gateway & NAT Gateway
│
├── Security (04)
│   └── Security Groups, NACLs, Traffic Flow
│
├── Connectivity (05–07)
│   └── VPC Endpoints, VPC Peering &
│       Transit Gateway, VPN & Direct Connect
│
├── Monitoring (08)
│   └── VPC Flow Logs
│
└── Production & Interview Prep (09–10)
    └── Design Patterns & Best Practices,
        Common Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **VPC** | Logically isolated virtual network defined by a CIDR block |
| **Subnet** | A subdivision of a VPC, scoped to a single AZ |
| **Route Table** | Rules determining where network traffic is directed |
| **Internet Gateway** | Enables bidirectional internet access for public subnets (free) |
| **NAT Gateway** | Enables outbound-only internet for private subnets (paid, AZ-scoped) |
| **Security Group** | Stateful, instance-level firewall — allow rules only |
| **NACL** | Stateless, subnet-level firewall — allow and deny rules |
| **VPC Endpoint** | Private connectivity to AWS services without internet |
| **VPC Peering** | Direct, non-transitive connection between two VPCs |
| **Transit Gateway** | Central hub connecting multiple VPCs, VPN, and Direct Connect |
| **Site-to-Site VPN** | Encrypted tunnel over public internet to on-premises |
| **Direct Connect** | Dedicated private fiber connection to on-premises |
| **Flow Logs** | Network traffic metadata capture for monitoring and auditing |

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────┐
│                     VPC (10.0.0.0/16)                │
│                                                       │
│   Internet ◄──► Internet Gateway                     │
│                       │                               │
│   ┌───────────────────┼───────────────────┐          │
│   │  Public Subnets   │                   │          │
│   │  ┌─────┐  ┌──────┐│  ┌─────┐         │          │
│   │  │ ALB │  │NAT GW││  │ ALB │  (AZ-2) │          │
│   │  └──┬──┘  └──┬───┘│  └──┬──┘         │          │
│   └─────┼────────┼────┘─────┼─────────────┘          │
│         │        │          │                         │
│   ┌─────┼────────┼──────────┼─────────────┐          │
│   │  Private App Subnets    │             │          │
│   │  ┌──────┐  ┌──────┐  ┌──────┐        │          │
│   │  │ EC2  │  │ ECS  │  │ EC2  │ (AZ-2) │          │
│   │  └──┬───┘  └──┬───┘  └──┬───┘        │          │
│   └─────┼────────┼──────────┼─────────────┘          │
│         │        │          │                         │
│   ┌─────┼────────┼──────────┼─────────────┐          │
│   │  Private Data Subnets   │             │          │
│   │  ┌──────┐  ┌──────────┐ │             │          │
│   │  │ RDS  │  │ElastiCache│ │  (AZ-2)    │          │
│   │  │(Pri) │  └──────────┘ │             │          │
│   │  └──────┘               │             │          │
│   └─────────────────────────┘─────────────┘          │
│                                                       │
│   VPC Endpoints: S3, DynamoDB, Secrets Manager, ECR  │
│   Flow Logs: Enabled → S3 + CloudWatch               │
│                                                       │
│   Connectivity: Transit GW / VPN / Direct Connect    │
└──────────────────────────────────────────────────────┘
```

---

## Quick Reference Tables

### Connectivity Options

| Method | Speed | Cost | Setup Time | Use Case |
|--------|-------|------|-----------|----------|
| VPC Peering | AWS backbone | Free | Minutes | 2-3 VPC connections |
| Transit Gateway | AWS backbone | ~$0.05/hr | Minutes | 4+ VPCs, hybrid |
| Site-to-Site VPN | Up to 1.25 Gbps | ~$0.05/hr | Minutes | Quick hybrid |
| Direct Connect | 1-100 Gbps | Higher | Weeks-months | High bandwidth, low latency |

### Security Controls

| Control | Scope | State | Rules |
|---------|-------|-------|-------|
| Security Groups | Instance (ENI) | Stateful | Allow only |
| NACLs | Subnet | Stateless | Allow + Deny |
| VPC Endpoints | Service access | N/A | Endpoint policies |
| Flow Logs | Monitoring | N/A | Capture all/accept/reject |

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
