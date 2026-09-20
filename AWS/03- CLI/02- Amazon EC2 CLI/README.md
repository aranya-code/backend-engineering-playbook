# Amazon EC2 CLI

> A comprehensive, production-focused guide to managing Amazon EC2 using the AWS Command Line Interface (AWS CLI). Learn instance management, storage, networking, monitoring, Auto Scaling, troubleshooting, and operational best practices through real-world examples.

---

## Quick Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- AWS CLI Setup and Configuration](./01-%20AWS%20CLI%20Setup%20and%20Configuration.md) | AWS CLI installation, configuration, credentials, profiles, and EC2 command structure |
| 02 | [02- EC2 Instance Inspection](./02-%20EC2%20Instance%20Inspection.md) | Inspecting instance metadata, state, configuration, and connected resources |
| 03 | [03- EC2 Instance Management](./03-%20EC2%20Instance%20Management.md) | Launch, start, stop, reboot, terminate, modify, and manage EC2 instance lifecycle |
| 04 | [04- AMI Management](./04-%20AMI%20Management.md) | Creating, registering, copying, sharing, and deregistering Amazon Machine Images |
| 05 | [05- EBS Volume Management](./05-%20EBS%20Volume%20Management.md) | Creating, attaching, detaching, resizing, and managing persistent EBS volumes |
| 06 | [06- EBS Snapshot Management](./06-%20EBS%20Snapshot%20Management.md) | Point-in-time EBS backups, snapshot lifecycle, copy, restore, and disaster recovery |
| 07 | [07- Security Group Management](./07-%20Security%20Group%20Management.md) | Creating, modifying, and managing stateful virtual firewall rules for EC2 instances |
| 08 | [08- Key Pair Management](./08-%20Key%20Pair%20Management.md) | EC2 key pair creation, import, rotation, and public-key authentication for SSH access |
| 09 | [09- Elastic IP Management](./09-%20Elastic%20IP%20Management.md) | Allocating, associating, disassociating, and releasing static public IPv4 addresses |
| 10 | [10- Auto Scaling CLI](./10-%20Auto%20Scaling%20CLI.md) | Auto Scaling Groups, Launch Templates, scaling policies, health checks, and capacity management |
| 11 | [11- Load Balancer CLI](./11-%20Load%20Balancer%20CLI.md) | Elastic Load Balancing, listeners, target groups, health checks, and traffic routing |
| 12 | [12- Querying and Filtering](./12-%20Querying%20and%20Filtering.md) | JMESPath queries, --filter flags, and extracting focused data from AWS CLI responses |
| 13 | [13- Output Formatting](./13-%20Output%20Formatting.md) | JSON, table, text, and YAML output formats for human consumption and shell automation |
| 14 | [14- Operational CLI Workflows](./14-%20Operational%20CLI%20Workflows.md) | Production-grade multi-command workflows for incident investigation and operations |

---

# Overview

Amazon Elastic Compute Cloud (Amazon EC2) is the core Infrastructure as a Service (IaaS) offering in AWS.

Although the AWS Management Console is useful for learning and occasional administration, production environments rely heavily on the AWS CLI for automation, deployments, infrastructure management, monitoring, and operational workflows.

This guide focuses on how experienced Backend Engineers, DevOps Engineers, and Cloud Engineers use the EC2 CLI in real-world production environments.

---

# Learning Objectives

After completing this section, you will be able to:

- Launch and manage EC2 instances
- Work with Amazon Machine Images (AMIs)
- Manage EBS volumes and snapshots
- Configure networking and security
- Monitor EC2 instances using CloudWatch
- Implement Auto Scaling
- Troubleshoot production issues
- Apply production-ready operational practices
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
Amazon EC2 CLI/
│
├── 01- Introduction to EC2 CLI.md
├── 02- Instance Management.md
├── 03- AMIs, Volumes & Snapshots.md
├── 04- Networking & Security.md
├── 05- Monitoring & Auto Scaling.md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to EC2 CLI

Build a solid foundation by learning:

- EC2 CLI architecture
- EC2 resources
- Instance identifiers
- Describe operations
- Common CLI patterns
- Querying EC2 resources

---

## 02. Instance Management

Learn how to:

- Launch EC2 instances
- Start, stop, reboot, and terminate instances
- Tag resources
- Filter instances
- Wait for state transitions
- Manage the EC2 instance lifecycle

---

## 03. AMIs, Volumes & Snapshots

Learn:

- Amazon Machine Images (AMIs)
- Creating custom AMIs
- Amazon EBS
- Volume management
- Snapshots
- Backup strategies
- Disaster recovery

---

## 04. Networking & Security

Topics include:

- Security Groups
- Key Pairs
- Elastic IPs
- Elastic Network Interfaces
- Public and Private Instances
- Bastion Hosts
- EC2 networking architecture
- Connectivity troubleshooting

---

## 05. Monitoring & Auto Scaling

Learn:

- Amazon CloudWatch
- EC2 metrics
- CloudWatch alarms
- Launch Templates
- Auto Scaling Groups
- Scaling policies
- Health checks
- Capacity planning

---

## 06. Troubleshooting & Best Practices

Master:

- Common EC2 CLI errors
- SSH troubleshooting
- Instance launch failures
- EBS troubleshooting
- Security Group debugging
- Performance optimization
- Production operational checklists

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used EC2 CLI commands
- Common AWS CLI queries
- Daily operational workflows
- Troubleshooting commands
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Automate EC2 administration
- Deploy production servers
- Manage storage and backups
- Secure EC2 infrastructure
- Configure monitoring and Auto Scaling
- Troubleshoot production environments
- Build scalable compute infrastructure

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Have AWS CLI Version 2 installed.
- Understand basic IAM concepts.
- Have an AWS account with EC2 permissions.
- Be familiar with basic networking concepts.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Verify the AWS account before making changes.
- Always confirm the target Region.
- Use IAM Roles instead of Access Keys.
- Tag every resource consistently.
- Prefer Launch Templates over Launch Configurations.
- Enable CloudWatch monitoring.
- Restrict Security Group access.
- Automate backups using EBS snapshots.
- Test Auto Scaling policies before production deployment.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
Instance Management
      │
      ▼
AMIs & Storage
      │
      ▼
Networking & Security
      │
      ▼
Monitoring
      │
      ▼
Auto Scaling
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this order builds a strong understanding of EC2 operations before moving into automation and optimization.

---

# Real-World Use Cases

The skills in this guide apply to:

- Web application hosting
- Backend API deployment
- CI/CD infrastructure
- Database servers
- Batch processing
- High Availability architectures
- Disaster recovery
- Monitoring and alerting
- Auto Scaling applications
- Production infrastructure management

---

# What's Next?

After mastering Amazon EC2 CLI, continue with:

- IAM CLI
- CloudFormation CLI
- CloudWatch CLI
- Lambda CLI
- ECS CLI
- ECR CLI
- RDS CLI
- DynamoDB CLI
- SQS CLI
- SNS CLI
- Route 53 CLI
- VPC CLI

Each guide follows the same structure, making it easy to learn additional AWS services.

---

# Who Should Read This?

This guide is designed for:

- Backend Engineers
- DevOps Engineers
- Cloud Engineers
- Platform Engineers
- Site Reliability Engineers (SREs)
- AWS Solutions Architects
- Students preparing for AWS certifications
- Engineers preparing for backend and cloud interviews

---

# Learning Outcomes

By the end of this guide, you will be able to:

- ✅ Launch and manage EC2 instances confidently.
- ✅ Create and manage AMIs and EBS snapshots.
- ✅ Configure secure networking for EC2.
- ✅ Monitor infrastructure using CloudWatch.
- ✅ Implement Auto Scaling for high availability.
- ✅ Troubleshoot common EC2 production issues.
- ✅ Follow operational best practices used by experienced cloud engineers.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

Amazon EC2 is the foundation of compute services in AWS. Mastering the EC2 CLI enables you to automate infrastructure provisioning, storage management, networking, monitoring, and scaling. Combined with IAM, CloudWatch, Auto Scaling, and EBS, the EC2 CLI becomes an indispensable tool for building secure, scalable, and production-ready cloud infrastructure.


## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **Amazon EC2 CLI** |

---