# AWS CloudTrail

A deep-dive study guide into **AWS CloudTrail** — AWS's fully managed governance, compliance, and API audit logging service that records every supported API call across your AWS account.

---

## 📚 Table of Contents

- [What is CloudTrail?](#what-is-cloudtrail)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [What Does CloudTrail Record?](#what-does-cloudtrail-record)
- [Navigation](#navigation)

---

## What is CloudTrail?

AWS CloudTrail is a **fully managed governance, compliance, auditing, and operational logging service** that records API activity across your AWS account.

It captures actions performed by users, applications, AWS services, and the AWS Management Console — making it one of the most important security and auditing services in AWS. Every supported API call is recorded as an **event**.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | What CloudTrail is, why it's needed, event types |
| 02 | [CloudTrail Architecture](./02-%20CloudTrail%20Architecture.md) | Internal architecture and data flow |
| 03 | [How CloudTrail Works](./03-%20How%20CloudTrail%20Works.md) | End-to-end event capture pipeline |
| 04 | [Event Types](./04-%20Event%20Types.md) | Overview of all event categories |
| 05 | [Management Events](./05-%20Management%20Events.md) | Control plane operations (create, modify, delete) |
| 06 | [Data Events](./06-%20Data%20Events.md) | Data plane operations (S3, Lambda, DynamoDB) |
| 07 | [Network Activity Events](./07-%20Network%20Activity%20Events.md) | VPC endpoint and private connectivity events |
| 08 | [Trails](./08-%20Trails.md) | Configuring event delivery and storage |
| 09 | [Event History](./09-%20Event%20History.md) | 90-day built-in event viewer |
| 10 | [CloudTrail Insights](./10-%20CloudTrail%20Insights.md) | Anomaly detection for unusual API activity |
| 11 | [Log File Integrity Validation](./11-%20Log%20File%20Integrity%20Validation.md) | Tamper detection with digest files |
| 12 | [CloudTrail Log Files](./12-%20CloudTrail%20Log%20Files.md) | Log file format, structure, and storage |
| 13 | [CloudTrail with Amazon S3](./13-%20CloudTrail%20with%20Amazon%20S3.md) | Long-term log archival in S3 |
| 14 | [CloudTrail with CloudWatch](./14-%20CloudTrail%20with%20CloudWatch.md) | Streaming events to CloudWatch Logs |
| 15 | [CloudTrail with EventBridge](./15-%20CloudTrail%20with%20EventBridge.md) | Triggering automated workflows from API events |
| 16 | [CloudTrail with SNS](./16-%20CloudTrail%20with%20SNS.md) | Sending notifications on log file delivery |
| 17 | [CloudTrail with Lambda](./17-%20CloudTrail%20with%20Lambda.md) | Serverless processing of CloudTrail events |
| 18 | [CloudTrail Organizations](./18-%20CloudTrail%20Organizations.md) | Multi-account trails with AWS Organizations |
| 19 | [IAM & CloudTrail](./19-%20IAM%20%26%20CloudTrail.md) | Permissions, policies, and access control |
| 20 | [CloudTrail Security](./20-%20CloudTrail%20Security.md) | Encryption, access control, and protection |
| 21 | [CloudTrail Pricing](./21-%20CloudTrail%20Pricing.md) | Free tier, costs, and billing details |
| 22 | [Troubleshooting](./22-%20Troubleshooting.md) | Common issues and resolution steps |
| 23 | [Advantages & Limitations](./23-%20Advantages%20%26%20Limitations.md) | Strengths and constraints |
| 24 | [CloudTrail vs CloudWatch vs X-Ray](./24-%20CloudTrail%20vs%20CloudWatch%20vs%20X-Ray.md) | Service comparison guide |
| 25 | [Monitoring & Best Practices](./25-%20Monitoring%20%26%20Best%20Practices.md) | Operational monitoring guidelines |
| 26 | [Cost Optimization](./26-%20Cost%20Optimization.md) | Strategies to reduce CloudTrail costs |
| 27 | [Production Best Practices](./27-%20Production%20Best%20Practices.md) | Enterprise-grade configuration |
| 28 | [Real-World Architectures](./28-%20Real-World%20Architectures.md) | Production architecture patterns |
| 29 | [Common Interview Questions](./29-%20Common%20Interview%20Questions.md) | Interview prep and key takeaways |

---

## Module Structure

This module is organized into progressive learning sections:

```
Cloud Trail/
│
├── Fundamentals (01–04)
│   └── Introduction, Architecture, How It Works, Event Types
│
├── Event Deep-Dive (05–07)
│   └── Management Events, Data Events, Network Activity Events
│
├── Configuration & Storage (08–12)
│   └── Trails, Event History, Insights, Log Integrity, Log Files
│
├── Integrations (13–17)
│   └── S3, CloudWatch, EventBridge, SNS, Lambda
│
├── Security & Governance (18–21)
│   └── Organizations, IAM, Security, Pricing
│
└── Production & Interview Prep (22–29)
    └── Troubleshooting, Comparisons, Best Practices,
        Real-World Architectures, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Management Events** | Control plane API calls — creating, modifying, or deleting resources |
| **Data Events** | Data plane API calls — S3 object operations, Lambda invocations |
| **Network Activity Events** | API activity through VPC endpoints and private connectivity |
| **Trails** | Configuration that delivers events to S3, CloudWatch, or EventBridge |
| **Event History** | Free 90-day searchable history of Management Events |
| **CloudTrail Insights** | Anomaly detection for unusual write API patterns |
| **Log File Integrity** | Digest files to verify logs haven't been tampered with |
| **Organization Trails** | Single trail that captures events across all accounts in an Organization |

---

## Architecture Overview

```
  User / Application / AWS Service
                 │
                 ▼
           AWS API Call
                 │
                 ▼
          AWS CloudTrail
                 │
      ┌──────────┼──────────────┐
      │          │              │
      ▼          ▼              ▼
  ┌────────┐ ┌──────────┐ ┌────────────┐
  │Event   │ │Amazon S3 │ │CloudWatch  │
  │History │ │(Long-Term│ │Logs        │
  │(90 Day)│ │ Storage) │ │            │
  └────────┘ └──────────┘ └────────────┘
                 │
                 ▼
          ┌────────────┐
          │EventBridge │
          │(Automation)│
          └────────────┘
```

---

## What Does CloudTrail Record?

CloudTrail captures activity from:

- **IAM Users & Roles**
- **AWS Management Console**
- **AWS CLI & SDKs**
- **AWS Services** (CloudFormation, Lambda, etc.)
- **Third-party applications** using AWS APIs

Each event records: **who** performed the action, **what** action was performed, **when** it occurred, **where** (region), and the **request/response details**.

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Monitoring](../README.md) |
| ⬅️ Previous | [Amazon CloudWatch](../CloudWatch/README.md) |
| ➡️ Next | [AWS X-Ray](../Amazon%20X-Ray/README.md) |

---

> **Part of the [AWS Monitoring](../README.md) section in the Backend Engineering Playbook.**
