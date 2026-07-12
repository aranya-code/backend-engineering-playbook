# AWS Route 53 CLI

> A comprehensive, production-focused guide to managing domains, DNS, traffic routing, health monitoring, and secure name resolution using Amazon Route 53 and the AWS Command Line Interface (AWS CLI). Learn Hosted Zones, DNS records, Routing Policies, Health Checks, DNSSEC, troubleshooting, and production best practices.

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to Route 53 CLI](./01-%20Introduction%20to%20Route%2053%20CLI.md) | Learn DNS fundamentals, Route 53 architecture, Hosted Zones, and AWS CLI basics |
| [02 - Hosted Zones & DNS Records](./02-%20Hosted%20Zones%20%26%20DNS%20Records.md) | Create and manage Hosted Zones, DNS records, Alias records, TTL, and DNS propagation |
| [03 - Routing Policies](./03-%20Routing%20Policies.md) | Configure Simple, Weighted, Latency, Failover, Geolocation, Geoproximity, and Multi-Value routing |
| [04 - Health Checks & Failover](./04-%20Health%20Checks%20%26%20Failover.md) | Configure Health Checks, CloudWatch integration, DNS Failover, and disaster recovery |
| [05 - Domain Registration & DNSSEC](./05-%20Domain%20Registration%20%26%20DNSSEC.md) | Register domains, manage domain lifecycle, configure DNSSEC, and secure DNS infrastructure |
| [06 - Troubleshooting & Best Practices](./06-%20Troubleshooting%20%26%20Best%20Practices.md) | Troubleshoot DNS resolution, Hosted Zones, Routing Policies, Health Checks, DNSSEC, and production issues |
| [07 - Cheat Sheet & Interview Guide](./07-%20Cheat%20Sheet%20%26%20Interview%20Guide.md) | Frequently used Route 53 CLI commands, troubleshooting reference, interview questions, and operational workflows |

---

# Overview

Amazon Route 53 is AWS's **highly available and scalable Domain Name System (DNS) service**.

It provides:

- Domain registration
- DNS hosting
- Traffic routing
- Health monitoring
- DNS failover
- DNSSEC
- Global name resolution

Route 53 is one of the core networking services in AWS and integrates with services such as EC2, Elastic Load Balancing, CloudFront, API Gateway, S3, Global Accelerator, and VPC.

This guide focuses on how experienced engineers use the **Amazon Route 53 CLI** to build resilient, secure, and globally distributed DNS architectures.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand DNS fundamentals
- Manage Hosted Zones using AWS CLI
- Configure DNS records
- Implement intelligent Routing Policies
- Configure Health Checks and DNS Failover
- Register and manage domains
- Secure DNS using DNSSEC
- Troubleshoot DNS issues
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
AWS Route 53 CLI/
│
├── 01- Introduction to Route 53 CLI.md
├── 02- Hosted Zones & DNS Records.md
├── 03- Routing Policies.md
├── 04- Health Checks & Failover.md
├── 05- Domain Registration & DNSSEC.md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to Route 53 CLI

Build a strong DNS foundation by learning:

- DNS fundamentals
- Route 53 architecture
- Hosted Zones
- DNS resolution
- Public and Private DNS
- AWS CLI basics

---

## 02. Hosted Zones & DNS Records

Learn how to:

- Create Hosted Zones
- Configure Public and Private Hosted Zones
- Manage DNS records
- Configure Alias records
- Understand TTL
- Manage DNS propagation

---

## 03. Routing Policies

Master:

- Simple Routing
- Weighted Routing
- Latency Routing
- Failover Routing
- Geolocation Routing
- Geoproximity Routing
- Multi-Value Answer Routing
- Traffic Flow

---

## 04. Health Checks & Failover

Learn:

- Route 53 Health Checks
- HTTP/HTTPS/TCP monitoring
- CloudWatch Alarm integration
- DNS Failover
- Active-Passive recovery
- Active-Active architectures

---

## 05. Domain Registration & DNSSEC

Topics include:

- Domain registration
- Domain lifecycle
- WHOIS
- Name Servers
- DNSSEC
- Key Signing Keys (KSK)
- Domain security

---

## 06. Troubleshooting & Best Practices

Master:

- DNS troubleshooting
- Hosted Zone issues
- DNS propagation
- Health Check failures
- Routing Policy debugging
- DNSSEC troubleshooting
- Production DNS best practices

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used Route 53 CLI commands
- Hosted Zone commands
- DNS record management
- Health Check commands
- DNSSEC commands
- Domain commands
- Troubleshooting reference
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Build highly available DNS architectures
- Manage domains and Hosted Zones
- Configure intelligent DNS routing
- Implement disaster recovery using DNS
- Secure DNS using DNSSEC
- Monitor application health
- Troubleshoot DNS issues
- Design enterprise-grade global routing solutions

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Understand Amazon VPC fundamentals.
- Be familiar with EC2 and Elastic Load Balancing.
- Have AWS CLI Version 2 installed.
- Have permissions to manage Route 53 resources.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Use Alias Records for AWS resources.
- Separate production and non-production Hosted Zones.
- Keep TTL values appropriate for the workload.
- Configure Health Checks for critical applications.
- Enable DNSSEC for production domains.
- Enable automatic domain renewal.
- Use Routing Policies based on application requirements.
- Manage DNS using Infrastructure as Code.
- Monitor DNS health continuously.
- Audit DNS records regularly.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
Hosted Zones
      │
      ▼
DNS Records
      │
      ▼
Routing Policies
      │
      ▼
Health Checks
      │
      ▼
DNSSEC
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this order builds a solid understanding of DNS before introducing intelligent routing, monitoring, and production security.

---

# Real-World Use Cases

The skills in this guide apply to:

- Website hosting
- REST APIs
- Global applications
- Multi-region deployments
- Disaster recovery
- Blue/Green deployments
- Canary deployments
- Domain management
- Enterprise DNS
- Hybrid cloud networking

---

# What's Next?

After mastering Amazon Route 53 CLI, continue with:

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

- ✅ Manage domains and Hosted Zones using Route 53.
- ✅ Configure DNS records and Alias records.
- ✅ Implement intelligent DNS Routing Policies.
- ✅ Configure Health Checks and DNS Failover.
- ✅ Secure public domains using DNSSEC.
- ✅ Troubleshoot production DNS issues.
- ✅ Build globally distributed, highly available DNS architectures.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

Amazon Route 53 is far more than a managed DNS service. It provides intelligent traffic routing, domain management, health monitoring, disaster recovery, and DNS security for cloud-native applications. Mastering the Route 53 CLI enables you to design resilient, scalable, and globally available systems while integrating seamlessly with the broader AWS networking ecosystem.

---

## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **AWS Route 53 CLI** |

---