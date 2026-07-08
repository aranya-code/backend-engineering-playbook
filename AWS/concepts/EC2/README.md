# AWS EC2 (Elastic Compute Cloud)

A comprehensive, production-focused playbook on Amazon EC2 — AWS's core Infrastructure-as-a-Service offering that provides resizable virtual servers in the cloud. This module covers EC2 fundamentals, instance types, purchasing options, networking, storage, load balancing, auto scaling, security, troubleshooting, and senior-level interview preparation.

---

# What You Will Learn

By completing this module, you will understand:

- EC2 Architecture and Core Components
- Instance Types and Selection Criteria
- Purchasing Options and Cost Optimization
- Instance Access (SSH, Key Pairs, User Data, Instance Metadata)
- Networking (Security Groups, NACLs, Elastic IPs, Ports)
- Storage (EBS Volumes, Instance Store, EFS, Snapshots, IOPS)
- Elastic Load Balancing (ALB, NLB, GWLB, SSL, Sticky Sessions)
- Auto Scaling Groups and Scaling Policies
- Production Troubleshooting
- Senior-Level Interview Preparation

---

# Module Structure

```text
EC2/
│
├── README.md                          ← You are here
├── EC2 Basics.md                      Core architecture and components
├── Instance Types.md                  Instance families and selection guide
├── Purchasing Options.md              On-Demand, Reserved, Spot, Savings Plans
├── EC2-Instance-Metadata.md           IMDS v1 vs v2, security implications
│
├── Access/                            Instance access and bootstrapping
│   ├── Key Pairs.md
│   ├── SSH.md
│   └── User Data.md
│
├── Networking/                        Network security and addressing
│   ├── Security Groups.md
│   ├── NACL vs SG.md
│   ├── Elastic IP.md
│   └── Ports.md
│
├── Storage/                           Block, instance, and file storage
│   ├── EBS.md
│   ├── EBS Snapshot.md
│   ├── EBS Multi-Attach.md
│   ├── IOPS.md
│   ├── Instance Store.md
│   ├── EFS.md
│   └── Amazon EFS.md
│
├── Load Balancing/                    Traffic distribution and SSL
│   ├── Elastic Load Balancer.md
│   ├── Load Balancer Types.md
│   ├── SSL Certificates.md
│   ├── SNI.md
│   └── Sticky Sessions.md
│
├── AutoScaling/                       Capacity management
│   └── Auto_Scaling_Groups.md
│
├── Interview/                         Interview preparation
│   ├── EC2 Interview Questions.md
│   └── Quick Revision.md
│
└── Troubleshooting/                   Production debugging
    ├── Connection Timeout.md
    └── Connection Refused.md
```

---

# Architecture Overview

```text
Internet
    │
    ▼
Route 53 (DNS)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                 │
│                                                       │
│  ┌────────────────────────────────────────────┐      │
│  │  Public Subnets (Multi-AZ)                 │      │
│  │  ┌───────────────────────────────────┐     │      │
│  │  │  Application Load Balancer (ALB)  │     │      │
│  │  │  - SSL Termination                │     │      │
│  │  │  - Path/Host-Based Routing        │     │      │
│  │  └──────────────┬────────────────────┘     │      │
│  └─────────────────┼─────────────────────────┘      │
│                    │                                  │
│  ┌─────────────────┼─────────────────────────┐      │
│  │  Private Subnets (Multi-AZ)               │      │
│  │  ┌──────────────▼────────────────────┐    │      │
│  │  │  Auto Scaling Group               │    │      │
│  │  │  ┌─────────┐  ┌─────────┐        │    │      │
│  │  │  │ EC2 (1) │  │ EC2 (2) │  ...   │    │      │
│  │  │  │ (AZ-1)  │  │ (AZ-2)  │        │    │      │
│  │  │  └────┬────┘  └────┬────┘        │    │      │
│  │  └───────┼────────────┼──────────────┘    │      │
│  └──────────┼────────────┼───────────────────┘      │
│             │            │                           │
│  ┌──────────▼────────────▼───────────────────┐      │
│  │  Private Data Subnets                     │      │
│  │  ┌─────────┐  ┌───────────┐               │      │
│  │  │   RDS   │  │ElastiCache│               │      │
│  │  └─────────┘  └───────────┘               │      │
│  └───────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
