# AWS Elastic Load Balancing (ELB) CLI

> A comprehensive, production-focused guide to deploying, managing, securing, and troubleshooting AWS Elastic Load Balancing (ELB) using the AWS Command Line Interface (AWS CLI). Learn Application Load Balancers (ALB), Network Load Balancers (NLB), Target Groups, Health Checks, HTTPS, Auto Scaling integration, AWS WAF, and production traffic management.

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to ELB CLI](./01-%20Introduction%20to%20ELB%20CLI.md) | Learn Elastic Load Balancing architecture, Load Balancer types, Target Groups, and AWS CLI fundamentals |
| [02 - Load Balancers, Listeners & Target Groups](./02-%20Load%20Balancers,%20Listeners%20%26%20Target%20Groups.md) | Create Load Balancers, configure Listeners, Target Groups, Listener Rules, and traffic routing |
| [03 - Health Checks, SSL & Routing](./03-%20Health%20Checks,%20SSL%20%26%20Routing.md) | Configure Health Checks, HTTPS, SSL termination, ACM certificates, and advanced routing |
| [04 - Auto Scaling Integration & High Availability](./04-%20Auto%20Scaling%20Integration%20%26%20High%20Availability.md) | Integrate ELB with Auto Scaling Groups, Cross-Zone Load Balancing, Multi-AZ deployments, and scaling strategies |
| [05 - Stickiness, WAF & Logging](./05-%20Stickiness,%20WAF%20%26%20Logging.md) | Configure Sticky Sessions, AWS WAF, Access Logs, HTTP/2, WebSockets, gRPC, and advanced ELB features |
| [06 - Troubleshooting & Best Practices](./06-%20Troubleshooting%20%26%20Best%20Practices.md) | Troubleshoot Load Balancers, Health Checks, SSL, routing, scaling, and production deployment issues |
| [07 - Cheat Sheet & Interview Guide](./07-%20Cheat%20Sheet%20%26%20Interview%20Guide.md) | Frequently used ELB CLI commands, troubleshooting reference, interview questions, and operational workflows |

---

# Overview

AWS Elastic Load Balancing (ELB) is a fully managed traffic distribution service that automatically distributes incoming requests across multiple backend resources.

It enables applications to become:

- Highly Available
- Fault Tolerant
- Scalable
- Secure
- Resilient

Elastic Load Balancing integrates with many AWS services including:

- Amazon EC2
- Amazon ECS
- AWS Lambda
- Auto Scaling
- Amazon Route 53
- AWS Certificate Manager (ACM)
- AWS WAF
- Amazon CloudWatch

This guide focuses on how experienced engineers use the **Elastic Load Balancing CLI** to deploy and manage production-grade applications.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand Elastic Load Balancing architecture
- Configure Application and Network Load Balancers
- Create and manage Target Groups
- Configure HTTPS using ACM
- Implement Health Checks
- Integrate with Auto Scaling Groups
- Configure AWS WAF and Access Logs
- Troubleshoot production traffic issues
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
AWS Elastic Load Balancing CLI/
│
├── 01- Introduction to ELB CLI.md
├── 02- Load Balancers, Listeners & Target Groups.md
├── 03- Health Checks, SSL & Routing.md
├── 04- Auto Scaling Integration & High Availability.md
├── 05- Stickiness, WAF & Logging.md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to ELB CLI

Build a strong foundation by learning:

- Elastic Load Balancing
- ALB vs NLB vs GWLB
- Load Balancer architecture
- Listeners
- Target Groups
- Health Checks
- AWS CLI basics

---

## 02. Load Balancers, Listeners & Target Groups

Learn how to:

- Create Load Balancers
- Configure Listeners
- Configure Listener Rules
- Create Target Groups
- Register Targets
- Implement Host-based Routing
- Implement Path-based Routing

---

## 03. Health Checks, SSL & Routing

Master:

- Target Health Checks
- HTTPS
- SSL Termination
- End-to-End Encryption
- AWS Certificate Manager (ACM)
- Redirect Rules
- Advanced Routing

---

## 04. Auto Scaling Integration & High Availability

Learn:

- Auto Scaling integration
- Target registration
- Cross-Zone Load Balancing
- Multi-AZ deployments
- Scaling policies
- Rolling deployments
- Blue-Green deployments
- Canary deployments

---

## 05. Stickiness, WAF & Logging

Topics include:

- Sticky Sessions
- AWS WAF
- Access Logs
- HTTP/2
- WebSockets
- gRPC
- Idle Timeout
- Deletion Protection

---

## 06. Troubleshooting & Best Practices

Master:

- Health Check failures
- SSL troubleshooting
- Target registration issues
- Listener debugging
- Routing problems
- CloudWatch monitoring
- Production deployment strategies

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used ELB CLI commands
- Load Balancer commands
- Listener commands
- Target Group commands
- ACM commands
- WAF commands
- Troubleshooting reference
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Deploy highly available Load Balancers
- Configure intelligent traffic routing
- Secure applications using HTTPS
- Manage SSL certificates with ACM
- Configure Auto Scaling integration
- Protect applications using AWS WAF
- Monitor and troubleshoot production traffic
- Design scalable AWS architectures

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Understand Amazon VPC networking.
- Understand Amazon EC2 fundamentals.
- Be familiar with Amazon Route 53.
- Have AWS CLI Version 2 installed.
- Have permissions to manage ELB resources.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Prefer Application Load Balancers for HTTP/HTTPS workloads.
- Deploy Load Balancers across multiple Availability Zones.
- Use HTTPS for all internet-facing applications.
- Store certificates in AWS Certificate Manager.
- Configure Health Checks for every Target Group.
- Enable AWS WAF for public applications.
- Enable Access Logs for production environments.
- Integrate with Auto Scaling Groups.
- Keep backend applications stateless.
- Monitor ELB metrics continuously.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
Load Balancers
      │
      ▼
Listeners
      │
      ▼
Target Groups
      │
      ▼
Health Checks
      │
      ▼
Auto Scaling
      │
      ▼
Security
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this order builds a strong understanding of traffic management before moving into scaling, security, and production operations.

---

# Real-World Use Cases

The skills in this guide apply to:

- High-traffic web applications
- REST APIs
- Microservices architectures
- Kubernetes ingress
- Blue-Green deployments
- Canary releases
- Multi-AZ deployments
- Auto Scaling environments
- Enterprise web applications
- Cloud-native architectures

---

# What's Next?

After mastering AWS Elastic Load Balancing CLI, continue with:

- ECS CLI
- ECR CLI
- RDS CLI
- Systems Manager (SSM) CLI
- API Gateway CLI
- DynamoDB CLI
- SQS CLI
- SNS CLI
- Step Functions CLI
- EventBridge CLI

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

- ✅ Deploy and manage Application and Network Load Balancers.
- ✅ Configure Listeners and Target Groups.
- ✅ Implement secure HTTPS using AWS Certificate Manager.
- ✅ Configure Health Checks and advanced routing.
- ✅ Integrate ELB with Auto Scaling Groups.
- ✅ Protect applications using AWS WAF.
- ✅ Monitor and troubleshoot production traffic.
- ✅ Design scalable, highly available AWS architectures.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

Elastic Load Balancing is one of the core building blocks of AWS architectures. Mastering the ELB CLI enables you to build highly available, scalable, and secure applications by intelligently distributing traffic, integrating with Auto Scaling, terminating TLS, monitoring application health, and protecting workloads using AWS WAF. Together with Route 53, VPC, CloudWatch, and Auto Scaling, ELB forms the foundation of modern production-ready cloud infrastructure.

---

## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **AWS Elastic Load Balancing (ELB) CLI** |

---