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
│   ├── README.md
│   ├── 01- Key Pairs.md
│   ├── 02- SSH.md
│   └── 03- User Data.md
│
├── Networking/                        Network security and addressing
│   ├── README.md
│   ├── 01- Security Groups.md
│   ├── 02- NACL vs SG.md
│   ├── 03- Elastic IP.md
│   └── 04- Ports.md
│
├── Storage/                           Block, instance, and file storage
│   ├── README.md
│   ├── 01- EBS.md
│   ├── 02- EBS Volume Types.md
│   ├── 03- EBS Snapshot.md
│   ├── 04- EBS Multi-Attach.md
│   ├── 05- Instance Store.md
│   ├── 06- EFS.md
│   └── 07- IOPS.md
│
├── Load Balancing/                    Traffic distribution and SSL
│   ├── README.md
│   ├── 01- Elastic Load Balancer.md
│   ├── 02- Load Balancer Types.md
│   ├── 03- SSL Certificates.md
│   ├── 04- SNI.md
│   └── 05- Sticky Sessions.md
│
├── AutoScaling/                       Capacity management
│   ├── README.md
│   └── 01- Auto Scaling Groups.md
│
├── Interview/                         Interview preparation
│   ├── README.md
│   ├── 01- Quick Revision.md
│   └── 02- EC2 Interview Questions.md
│
└── Troubleshooting/                   Production debugging
    ├── README.md
    ├── 01- Connection Refused.md
    ├── 02- Connection Timeout.md
    ├── 03- Instance Failing Health Checks.md
    └── 04- High CPU and T-Series Throttling.md
```

---

# 📚 Topics Covered

### Fundamentals

| Topic | Description |
|-------|-------------|
| [EC2 Basics](EC2%20Basics.md) | Architecture (Nitro System), core components, AMIs, Placement Groups, instance lifecycle, Hibernate vs. Stop |
| [Instance Types](Instance%20Types.md) | Naming convention, every instance family, Graviton, the T3 credit model, and a selection decision tree |
| [Purchasing Options](Purchasing%20Options.md) | On-Demand, Reserved Instances, Savings Plans, Spot, Dedicated Hosts, Capacity Reservations |
| [EC2 Instance Metadata](EC2-Instance-Metadata.md) | IMDSv1 vs. IMDSv2, SSRF protection, and the Instance Identity Document |

### [Access](Access/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Key Pairs](Access/01-%20Key%20Pairs.md) | Asymmetric SSH authentication and how the challenge-response works |
| 02 | [SSH](Access/02-%20SSH.md) | Connecting to instances, and default usernames by AMI |
| 03 | [User Data](Access/03-%20User%20Data.md) | The cloud-init bootstrap flow, and why secrets don't belong here |

### [Networking](Networking/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Security Groups](Networking/01-%20Security%20Groups.md) | Stateful, instance-level firewall — allow rules only |
| 02 | [NACL vs SG](Networking/02-%20NACL%20vs%20SG.md) | Stateless subnet-level filtering vs. stateful instance-level filtering |
| 03 | [Elastic IP](Networking/03-%20Elastic%20IP.md) | Static public IPs, and why unattached ones quietly cost money |
| 04 | [Ports](Networking/04-%20Ports.md) | Common service ports, and why database ports shouldn't be open broadly |

### [Storage](Storage/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [EBS](Storage/01-%20EBS.md) | Persistent, network-attached block storage — AZ-scoped, single-instance by default |
| 02 | [EBS Volume Types](Storage/02-%20EBS%20Volume%20Types.md) | gp3, io2, st1/sc1 — choosing by IOPS, throughput, and cost |
| 03 | [EBS Snapshot](Storage/03-%20EBS%20Snapshot.md) | Incremental backups, cross-region copy, and automating lifecycle with DLM |
| 04 | [EBS Multi-Attach](Storage/04-%20EBS%20Multi-Attach.md) | Shared block access for already-clustered software — attachment only, not write coordination |
| 05 | [Instance Store](Storage/05-%20Instance%20Store.md) | Physically local, ephemeral storage — fastest, but lost on stop/terminate |
| 06 | [EFS](Storage/06-%20EFS.md) | A real distributed filesystem for concurrent multi-instance, multi-AZ access |
| 07 | [IOPS](Storage/07-%20IOPS.md) | IOPS vs. throughput vs. latency, and diagnosing a storage bottleneck |

### [Load Balancing](Load%20Balancing/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Elastic Load Balancer](Load%20Balancing/01-%20Elastic%20Load%20Balancer.md) | What ELB is, and what it improves |
| 02 | [Load Balancer Types](Load%20Balancing/02-%20Load%20Balancer%20Types.md) | CLB, ALB, NLB, and GWLB compared |
| 03 | [SSL Certificates](Load%20Balancing/03-%20SSL%20Certificates.md) | TLS termination at the load balancer |
| 04 | [SNI](Load%20Balancing/04-%20SNI.md) | Hosting multiple SSL certificates on one IP |
| 05 | [Sticky Sessions](Load%20Balancing/05-%20Sticky%20Sessions.md) | Binding a client to a specific target instance |

### [AutoScaling](AutoScaling/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Auto Scaling Groups](AutoScaling/01-%20Auto%20Scaling%20Groups.md) | Goals, scaling policies, and how ASGs maintain availability |

### [Troubleshooting](Troubleshooting/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Connection Refused](Troubleshooting/01-%20Connection%20Refused.md) | The network layer is fine — the app itself isn't listening correctly |
| 02 | [Connection Timeout](Troubleshooting/02-%20Connection%20Timeout.md) | Security Group, NACL (both directions), or routing — in that order |
| 03 | [Instance Failing Health Checks](Troubleshooting/03-%20Instance%20Failing%20Health%20Checks.md) | Target Group vs. ASG health checks, and why they can disagree |
| 04 | [High CPU and T-Series Throttling](Troubleshooting/04-%20High%20CPU%20and%20T-Series%20Throttling.md) | Diagnosing CPU credit exhaustion before it looks like a mystery slowdown |

### [Interview](Interview/)

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Quick Revision](Interview/01-%20Quick%20Revision.md) | A condensed cheat sheet of every major fact across this folder |
| 02 | [EC2 Interview Questions](Interview/02-%20EC2%20Interview%20Questions.md) | 15 questions across beginner, intermediate, and senior/advanced tiers |

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
