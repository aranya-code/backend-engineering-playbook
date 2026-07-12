# AWS VPC CLI

> A comprehensive, production-focused guide to designing, managing, securing, and troubleshooting Amazon Virtual Private Cloud (VPC) using the AWS Command Line Interface (AWS CLI). Learn VPC architecture, subnets, routing, gateways, network security, VPC Peering, PrivateLink, VPC Endpoints, and production networking best practices.

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to VPC CLI](./01-%20Introduction%20to%20VPC%20CLI.md) | Learn Amazon VPC architecture, networking fundamentals, CIDR blocks, subnets, and AWS CLI basics |
| [02 - VPCs, CIDR Blocks & Subnets](./02-%20VPCs,%20CIDR%20Blocks%20%26%20Subnets.md) | Create VPCs, plan CIDR ranges, configure IPv4/IPv6, design public and private subnets |
| [03 - Route Tables, Internet Gateway & NAT Gateway](./03-%20Route%20Tables,%20Internet%20Gateway%20%26%20NAT%20Gateway.md) | Configure routing, Internet Gateway, NAT Gateway, Elastic IPs, and internet connectivity |
| [04 - Security Groups & Network ACLs](./04-%20Security%20Groups%20%26%20Network%20ACLs.md) | Secure VPC resources using Security Groups, Network ACLs, inbound/outbound rules, and firewall best practices |
| [05 - VPC Peering, Endpoints & PrivateLink](./05-%20VPC%20Peering,%20Endpoints%20%26%20PrivateLink.md) | Connect VPCs privately using Peering, Gateway Endpoints, Interface Endpoints, and AWS PrivateLink |
| [06 - Troubleshooting & Best Practices](./06-%20Troubleshooting%20%26%20Best%20Practices.md) | Troubleshoot networking, routing, gateways, security, DNS, connectivity, and production networking issues |
| [07 - Cheat Sheet & Interview Guide](./07-%20Cheat%20Sheet%20%26%20Interview%20Guide.md) | Frequently used VPC CLI commands, troubleshooting reference, interview questions, and operational workflows |

---

# Overview

Amazon Virtual Private Cloud (Amazon VPC) is the **networking foundation of AWS**.

Nearly every AWS service—including EC2, RDS, ECS, EKS, Lambda, ElastiCache, OpenSearch, and Redshift—runs inside or connects to a VPC.

Amazon VPC gives you complete control over:

- IP addressing
- Subnet design
- Routing
- Internet connectivity
- Private networking
- Network security
- Hybrid cloud connectivity

This guide focuses on how experienced engineers use the **Amazon VPC CLI** to build secure, scalable, highly available, and production-ready cloud networks.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand Amazon VPC architecture
- Design scalable VPC networks
- Plan IPv4 and IPv6 CIDR blocks
- Build public and private subnet architectures
- Configure Route Tables and Gateways
- Secure networks using Security Groups and Network ACLs
- Configure VPC Peering and PrivateLink
- Access AWS services privately using VPC Endpoints
- Troubleshoot production networking issues
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
AWS VPC CLI/
│
├── 01- Introduction to VPC CLI.md
├── 02- VPCs, CIDR Blocks & Subnets.md
├── 03- Route Tables, Internet Gateway & NAT Gateway.md
├── 04- Security Groups & Network ACLs.md
├── 05- VPC Peering, Endpoints & PrivateLink.md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to VPC CLI

Build a strong networking foundation by learning:

- Amazon VPC architecture
- Networking fundamentals
- CIDR notation
- Public vs Private networking
- Availability Zones
- VPC components
- AWS CLI networking commands

---

## 02. VPCs, CIDR Blocks & Subnets

Learn how to:

- Create VPCs
- Plan IPv4 and IPv6 CIDR ranges
- Configure Subnets
- Design Public and Private networks
- Build highly available subnet layouts
- Plan enterprise IP addressing

---

## 03. Route Tables, Internet Gateway & NAT Gateway

Master:

- Route Tables
- Local routing
- Internet Gateway
- NAT Gateway
- Elastic IPs
- Public internet connectivity
- Private outbound connectivity

---

## 04. Security Groups & Network ACLs

Learn:

- Security Groups
- Network ACLs
- Stateful vs Stateless firewalls
- Inbound rules
- Outbound rules
- Security Group references
- Production network security

---

## 05. VPC Peering, Endpoints & PrivateLink

Topics include:

- VPC Peering
- Gateway Endpoints
- Interface Endpoints
- AWS PrivateLink
- Private DNS
- Cross-VPC communication
- Private AWS service access

---

## 06. Troubleshooting & Best Practices

Master:

- Connectivity troubleshooting
- Routing failures
- Security Group debugging
- Network ACL troubleshooting
- Internet Gateway issues
- NAT Gateway issues
- DNS troubleshooting
- Production networking best practices

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used Amazon VPC CLI commands
- Routing commands
- Security commands
- Endpoint commands
- Peering commands
- Troubleshooting reference
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Design secure Amazon VPC architectures
- Build highly available network topologies
- Configure public and private networking
- Implement secure routing strategies
- Protect workloads using layered network security
- Connect AWS services privately
- Build enterprise networking solutions
- Troubleshoot production networking issues

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Understand AWS IAM fundamentals.
- Be familiar with Amazon EC2.
- Have AWS CLI Version 2 installed.
- Have permissions to create VPC resources.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Use custom VPCs instead of the default VPC.
- Plan CIDR ranges before deployment.
- Separate public and private workloads.
- Use multiple Availability Zones.
- Follow the Principle of Least Privilege.
- Prefer Security Group references over IP-based rules.
- Keep databases in private subnets.
- Use VPC Endpoints instead of unnecessary internet traffic.
- Enable VPC Flow Logs for production monitoring.
- Tag every networking resource consistently.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
VPC Design
      │
      ▼
Subnets
      │
      ▼
Routing
      │
      ▼
Network Security
      │
      ▼
Private Connectivity
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this sequence builds a strong networking foundation before introducing advanced connectivity and production operations.

---

# Real-World Use Cases

The skills in this guide apply to:

- Multi-tier web applications
- Microservices architectures
- Serverless networking
- Hybrid cloud networking
- Multi-account AWS environments
- High availability deployments
- Disaster recovery
- Secure enterprise networking
- Private service communication
- Cloud infrastructure automation

---

# What's Next?

After mastering Amazon VPC CLI, continue with:

- Route 53 CLI
- Elastic Load Balancing (ELB) CLI
- ECS CLI
- ECR CLI
- RDS CLI
- Systems Manager (SSM) CLI
- API Gateway CLI
- DynamoDB CLI
- SQS CLI
- SNS CLI
- Step Functions CLI

Each guide follows the same structure, allowing you to build consistent knowledge across AWS services.

---

# Who Should Read This?

This guide is designed for:

- Backend Engineers
- DevOps Engineers
- Cloud Engineers
- Platform Engineers
- Site Reliability Engineers (SREs)
- AWS Solutions Architects
- Infrastructure Engineers
- Students preparing for AWS certifications
- Engineers preparing for backend and cloud interviews

---

# Learning Outcomes

By the end of this guide, you will be able to:

- ✅ Design and deploy production-ready Amazon VPC architectures.
- ✅ Plan scalable IPv4 and IPv6 network layouts.
- ✅ Configure Route Tables, Internet Gateways, and NAT Gateways.
- ✅ Secure workloads using Security Groups and Network ACLs.
- ✅ Connect VPCs using Peering and AWS PrivateLink.
- ✅ Access AWS services privately using VPC Endpoints.
- ✅ Troubleshoot networking issues in production environments.
- ✅ Build highly available and secure cloud networks.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

Amazon VPC is the networking backbone of AWS. Mastering the Amazon VPC CLI enables you to build secure, scalable, and highly available cloud infrastructure by controlling IP addressing, routing, security, and private connectivity. Combined with Internet Gateways, NAT Gateways, Security Groups, Network ACLs, VPC Endpoints, and PrivateLink, Amazon VPC provides the foundation for nearly every production workload running on AWS.

---

## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **AWS VPC CLI** |

---