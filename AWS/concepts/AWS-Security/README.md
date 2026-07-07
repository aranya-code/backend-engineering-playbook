# AWS Security

A comprehensive deep-dive study guide into **AWS Security** — covering the shared responsibility model, encryption, key management, network security, threat detection, compliance, and production hardening best practices for senior DevOps engineers and solutions architects.

---

## 📚 Table of Contents

- [What is AWS Security?](#what-is-aws-security)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Security Architecture Overview](#security-architecture-overview)
- [Navigation](#navigation)

---

## What is AWS Security?

AWS Security is the practice of protecting cloud workloads, data, applications, and infrastructure from unauthorized access, vulnerabilities, and threats. It operates on a **shared responsibility model** — AWS secures the cloud infrastructure, while customers secure their data, configurations, and applications running inside it.

This module covers the full spectrum of AWS security: from identity and encryption fundamentals to advanced threat detection, compliance automation, and production hardening checklists.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | Security pillars, defense in depth, AWS security services landscape, common threats |
| 02 | [AWS Shared Responsibility Model](./02-%20AWS%20Shared%20Responsibility%20Model.md) | AWS vs customer responsibilities, IaaS/PaaS/Serverless comparison, misconceptions |
| 03 | [API Authentication and SigV4](./03-%20API%20Authentication%20and%20SigV4.md) | SigV4 signing process, canonical requests, presigned URLs, temporary credentials, debugging |
| 04 | [Encryption at Rest and In Transit](./04-%20Encryption%20at%20Rest%20and%20In%20Transit.md) | SSE types, KMS integration, TLS, ACM, enforcement patterns per service |
| 05 | [AWS KMS Deep Dive](./05-%20AWS%20KMS%20Deep%20Dive.md) | Key types, key policies, rotation, envelope encryption, quotas, cross-account sharing |
| 06 | [Secrets Manager and Parameter Store](./06-%20AWS%20Secrets%20Manager%20and%20Parameter%20Store.md) | Automatic rotation, hierarchical config, comparison table, when to use which |
| 07 | [AWS WAF and Shield](./07-%20AWS%20WAF%20and%20Shield.md) | WAF rules, managed rule groups, Shield tiers, DDoS architecture, Firewall Manager |
| 08 | [VPC Security](./08-%20VPC%20Security.md) | Security groups, NACLs, VPC endpoints, Flow Logs, bastion vs SSM, network architecture |
| 09 | [GuardDuty and Security Hub](./09-%20AWS%20GuardDuty%20and%20Security%20Hub.md) | Threat detection, finding types, automated remediation, compliance standards, cross-account |
| 10 | [Compliance and Auditing](./10-%20Compliance%20and%20Auditing.md) | Config rules, conformance packs, CloudTrail auditing, Audit Manager, continuous compliance |
| 11 | [Security Best Practices](./11-%20Security%20Best%20Practices.md) | Root account, IAM, network, encryption checklists, monitoring stack, incident response |
| 12 | [Common Interview Questions](./12-%20Common%20Interview%20Questions.md) | 17 senior-level Q&A covering all security domains |

---

## Module Structure

```
AWS-Security/
│
├── Foundations (01–02)
│   └── Introduction, Shared Responsibility Model
│
├── Authentication & Encryption (03–06)
│   └── SigV4, Encryption (At Rest & In Transit),
│       KMS Deep Dive, Secrets Management
│
├── Network & Application Security (07–08)
│   └── WAF & Shield, VPC Security
│
├── Detection & Compliance (09–10)
│   └── GuardDuty & Security Hub,
│       Compliance & Auditing
│
└── Production & Interview Prep (11–12)
    └── Security Best Practices,
        Common Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Shared Responsibility** | AWS secures infrastructure; customers secure their workloads |
| **Defense in Depth** | Multiple security layers — edge, network, compute, application, data, identity |
| **SigV4** | HMAC-SHA256 signing process for authenticating AWS API requests |
| **Envelope Encryption** | Data key encrypts data locally; KMS key encrypts the data key |
| **SSE-S3 / SSE-KMS / SSE-C** | Server-side encryption with varying levels of key control |
| **Security Groups** | Stateful, instance-level firewalls (allow rules only) |
| **NACLs** | Stateless, subnet-level firewalls (allow + deny rules) |
| **VPC Endpoints** | Private connectivity to AWS services without internet |
| **GuardDuty** | ML-based threat detection from CloudTrail, Flow Logs, DNS |
| **Security Hub** | Centralized findings aggregation and compliance scoring |
| **Config Rules** | Continuous compliance evaluation of resource configurations |
| **WAF** | Application-layer firewall (SQL injection, XSS, rate limiting) |
| **Shield** | DDoS protection (Standard: free L3/L4; Advanced: paid L3/L4/L7) |

---

## Security Architecture Overview

```text
┌──────────────────────────────────────────────────┐
│               Defense in Depth                    │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  Edge: CloudFront + WAF + Shield + Route 53 │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Network: VPC + SGs + NACLs + Endpoints     │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Compute: SSM + Inspector + Patching        │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Application: WAF Rules + Input Validation  │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Data: KMS + SSE + ACM + Macie             │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Identity: IAM + STS + Organizations + SCPs │ │
│  ├─────────────────────────────────────────────┤ │
│  │  Detection: GuardDuty + Security Hub +      │ │
│  │            CloudTrail + Config              │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
