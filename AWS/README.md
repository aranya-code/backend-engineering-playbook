# ☁️ AWS Knowledge Base

A structured personal knowledge base covering Amazon Web Services (AWS) from fundamental cloud concepts to production-grade architecture. Built as a hands-on study reference with concept deep-dives, CLI cheat sheets, infrastructure blueprints, and documented troubleshooting war stories.

---

## 📁 Repository Structure

```text
AWS/
├── concepts/               # In-depth concept notes
│   ├── AWS-Global-Infrastructure.md
│   ├── IAM-and-Security.md
│   ├── Shared-Responsibility-Model.md
│   ├── Well-Architected-Framework.md
│   ├── Compute/            # 8-part Compute series
│   ├── Storage/            # 6-part Storage series
│   ├── Networking/         # 7-part VPC & Networking series
│   └── Databases/          # 5-part Database series
├── cli/                    # Quick-reference command sheets
│   ├── README.md
│   ├── AWS-CLI-Basics.md
│   ├── IAM-Commands.md
│   ├── EC2-Commands.md
│   ├── S3-Commands.md
│   └── CloudFormation-Snippets.md
├── troubleshooting/
│   └── AWS-Troubleshooting.md
├── architecture/           # Reference blueprints and IaC
│   └── Production-VPC-Architecture.md
└── images/                 # Architecture diagrams and screenshots
```

---

## 📚 Topics Covered

### Core Concepts

| Topic | Description |
|-------|-------------|
| [AWS Global Infrastructure](concepts/AWS-Global-Infrastructure.md) | Regions, Availability Zones (AZs), Edge Locations, and latency considerations |
| [IAM & Security](concepts/IAM-and-Security.md) | Users, Groups, Roles, Policies, and the Principle of Least Privilege |
| [Shared Responsibility](concepts/Shared-Responsibility-Model.md) | Security *of* the cloud (AWS) vs. Security *in* the cloud (Customer) |
| [Well-Architected Framework](concepts/Well-Architected-Framework.md) | Operational Excellence, Security, Reliability, Performance, Cost, Sustainability |

---

### Compute & Scaling (8-part series)

| # | Topic |
|---|-------|
| 01 | [EC2 Fundamentals & Instance Types](concepts/Compute/01-%20EC2%20Fundamentals.md) |
| 02 | [AMIs and User Data Bootstrapping](concepts/Compute/02-%20AMIs%20and%20User%20Data.md) |
| 03 | [Security Groups vs NACLs](concepts/Compute/03-%20Security%20Groups%20vs%20NACLs.md) |
| 04 | [Elastic Load Balancing (ALB, NLB, GLB)](concepts/Compute/04-%20Elastic%20Load%20Balancing.md) |
| 05 | [Auto Scaling Groups (ASG)](concepts/Compute/05-%20Auto%20Scaling%20Groups.md) |
| 06 | [AWS Lambda & Serverless Compute](concepts/Compute/06-%20AWS%20Lambda.md) |
| 07 | [Elastic Container Service (ECS) & Fargate](concepts/Compute/07-%20ECS%20and%20Fargate.md) |
| 08 | [Compute Interview Questions](concepts/Compute/08-%20Interview%20Questions.md) |

---

### Storage (6-part series)

| # | Topic |
|---|-------|
| 01 | [S3 Fundamentals and Storage Classes](concepts/Storage/01-%20S3%20Fundamentals.md) |
| 02 | [S3 Security (Bucket Policies & Block Public Access)](concepts/Storage/02-%20S3%20Security.md) |
| 03 | [Elastic Block Store (EBS) & Snapshots](concepts/Storage/03-%20EBS%20and%20Snapshots.md) |
| 04 | [Elastic File System (EFS)](concepts/Storage/04-%20EFS.md) |
| 05 | [Storage Comparison: EBS vs EFS vs S3](concepts/Storage/05-%20Storage%20Comparison.md) |
| 06 | [Storage Interview Questions](concepts/Storage/06-%20Interview%20Questions.md) |

---

### Networking & Content Delivery (7-part series)

| # | Topic |
|---|-------|
| 01 | [VPC Basics (CIDR, Subnets, Route Tables)](concepts/Networking/01-%20VPC%20Basics.md) |
| 02 | [Internet Gateways & NAT Gateways](concepts/Networking/02-%20IGW%20and%20NAT.md) |
| 03 | [VPC Peering & Transit Gateway](concepts/Networking/03-%20VPC%20Peering.md) |
| 04 | [Route 53 DNS Routing Policies](concepts/Networking/04-%20Route%2053.md) |
| 05 | [CloudFront CDN Fundamentals](concepts/Networking/05-%20CloudFront.md) |
| 06 | [AWS WAF & Shield](concepts/Networking/06-%20WAF%20and%20Shield.md) |
| 07 | [Networking Interview Questions](concepts/Networking/07-%20Interview%20Questions.md) |

---

### CLI Reference

Quick-reference command sheets organized by topic:

- [AWS CLI Basics](cli/AWS-CLI-Basics.md) — profiles, configure, sts get-caller-identity
- [IAM Commands](cli/IAM-Commands.md) — create-user, attach-user-policy, assume-role
- [EC2 Commands](cli/EC2-Commands.md) — run-instances, describe-instances, create-key-pair
- [S3 Commands](cli/S3-Commands.md) — mb, cp, sync, presign, rm
- [CloudFormation Snippets](cli/CloudFormation-Snippets.md) — deploy, delete-stack, describe-stacks

---

### Troubleshooting

Real problems encountered and solved, with screenshots:

| # | Problem | Fix |
|---|---------|-----|
| 1 | EC2 Instance Connect Timeout / SSH fails | Verify Security Group inbound rules allow Port 22 from your IP and ensure the subnet has an attached Internet Gateway. |
| 2 | S3 Access Denied (403) on public objects | Check if "Block Public Access" is enabled at the bucket/account level and verify the Bucket Policy allows `s3:GetObject`. |
| 3 | Lambda function timing out | Increase the execution timeout limit in the configuration; if in a VPC, ensure private subnets route internet traffic through a NAT Gateway. |
| 4 | Cannot connect to RDS from local machine | Ensure RDS is set to `Publicly Accessible: Yes` (for dev), verify the SG allows inbound Port 5432/3306, or use a Bastion Host. |
| 5 | Auto Scaling Group not terminating unhealthy instances | Check the ASG health check type. If using an ALB, switch the ASG health check from `EC2` to `ELB`. |

---

## 🏗️ Production Architecture Blueprint

A production-ready AWS VPC architecture guide is included at [`architecture/Production-VPC-Architecture.md`](architecture/Production-VPC-Architecture.md).

**Key practices applied:**
- High Availability across 2+ Availability Zones (AZs).
- Public subnets for Application Load Balancers and Bastion Hosts.
- Private subnets for application servers (EC2/ECS) to block direct internet access.
- Secure database subnets isolated from application tiers.
- Principle of Least Privilege applied to all IAM roles attached to instances.
- Egress internet access handled strictly via NAT Gateways.

---

## 🎯 Purpose

This repository is a personal AWS study reference built to:

- Consolidate cloud infrastructure learning into searchable, structured notes.
- Prepare for backend engineering and cloud architecture interviews (concept explanations + scenario-based Q&A included).
- Document real-world deployment issues, IAM permission conflicts, and fixes encountered during hands-on practice.

---

*Created by Aranya Majumdar*