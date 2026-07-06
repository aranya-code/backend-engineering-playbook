# Amazon S3 (Simple Storage Service)

A comprehensive deep-dive study guide into **Amazon S3** — AWS's fully managed, infinitely scalable object storage service. This module covers **19 topic areas** with **190+ structured notes** spanning fundamentals, security, encryption, storage classes, replication, performance, and exam/interview preparation.

---

## 📚 Table of Contents

- [What is Amazon S3?](#what-is-amazon-s3)
- [Module Overview](#module-overview)
- [Topics Covered](#topics-covered)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Suggested Learning Path](#suggested-learning-path)
- [Storage Classes Quick Reference](#storage-classes-quick-reference)
- [Navigation](#navigation)

---

## What is Amazon S3?

Amazon S3 is AWS's **object storage service** designed to store and retrieve virtually unlimited amounts of data with **99.999999999% (11 nines) durability** and **99.99% availability**.

Files are stored as **objects** (consisting of data, metadata, and a unique key) inside **buckets**. S3 is a regional service with a globally unique bucket namespace, and it underpins countless AWS architectures — from static websites and data lakes to backup storage and disaster recovery.

---

## Module Overview

| Metric | Value |
|--------|-------|
| **Topic Areas** | 19 subdirectories |
| **Total Notes** | 190+ files |
| **Coverage** | Fundamentals → Advanced → Exam & Interview Prep |
| **Key Themes** | Storage, Security, Encryption, Replication, Performance, Cost Optimization |

---

## Topics Covered

### 🏗️ Core Concepts

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 1 | [S3 Fundamentals](./S3%20Fundamentals/) | 5 | What is S3, Buckets, Objects, Keys & Prefixes, Limits |
| 2 | [S3 Storage Classes](./S3%20Storage%20Classes/) | 12 | Standard, Standard-IA, One Zone-IA, Intelligent-Tiering, Glacier (Instant, Flexible, Deep Archive), Cost Comparison |
| 3 | [S3 Versioning & Data Protection](./S3%20Versioning-Data-Protection/) | 8 | Versioning, Delete Markers, MFA Delete, Object Lock, Legal Hold, Retention, Recovery |

---

### 🔒 Security & Encryption

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 4 | [S3 Security](./S3%20Security/) | 9 | IAM vs Bucket Policies, ACLs, Block Public Access, Access Points, Policy Evaluation Logic |
| 5 | [S3 Encryption](./S3%20Encryption/) | 12 | SSE-S3, SSE-KMS, SSE-C, Client-Side Encryption, KMS Deep Dive, Envelope Encryption, In-Transit |
| 6 | [S3 Access Points](./S3%20Access%20Points/) | 10 | Access Point Architecture, Policies, VPC Access Points, Multi-Team Design |
| 7 | [S3 Presigned URLs](./S3%20Presigned%20URLs/) | 10 | How Presigned URLs Work, Upload/Download, Security, Expiration |

---

### 🔄 Data Management & Replication

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 8 | [S3 Replication](./S3%20Replication/) | 10 | CRR, SRR, Requirements, Delete Marker Replication, RTC, Multi-Account, DR Scenarios |
| 9 | [S3 Lifecycle Policies](./S3%20Lifecycle%20Policies/) | 10 | Transition Actions, Expiration Actions, Versioned Objects, Storage Class Transitions, Cost Optimization |
| 10 | [S3 Object Lock Advanced](./S3%20Object%20Lock%20Advanced/) | 11 | Governance Mode, Compliance Mode, Legal Hold, Retention, WORM Storage, Regulatory Compliance |

---

### ⚡ Performance & Delivery

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 11 | [S3 Performance](./S3%20Performance/) | 1 | Multipart Upload, Transfer Acceleration, Byte-Range Fetches, Metadata, Tags, Event Notifications |
| 12 | [S3 Transfer Acceleration](./S3%20Transfer%20Acceleration/) | 10 | How It Works, Edge Locations, Performance Benefits, Cost, Global Upload Architectures |
| 13 | [S3 Event Notifications](./S3%20Event%20Notifications/) | 10 | Supported Events, SQS/SNS/Lambda Integration, Event-Driven Architectures |
| 14 | [S3 Static Website Hosting](./S3%20Static%20Website%20Hosting/) | 11 | Bucket Config, Index/Error Docs, Public Access, Custom Domains, Route 53, CloudFront Integration |

---

### 🌍 Advanced & Multi-Region

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 15 | [S3 Multi Region Access Points](./S3%20Multi%20Region%20Access%20Points/) | 10 | Global Endpoints, Traffic Routing, Failover, Active-Active, Replication Integration |
| 16 | [S3 Storage Lens & Inventory](./S3%20Storage%20Lens%20and%20Inventory/) | 10 | Metrics & Dashboards, Organization Visibility, Inventory Reports, Cost Optimization Insights |

---

### 📝 Exam & Interview Preparation

| # | Module | Files | Key Topics |
|---|--------|-------|------------|
| 17 | [S3 Cheat Sheets](./S3%20Cheat%20Sheets/) | 10 | One-Page S3 Cheat Sheet, Quick References (Storage Classes, Security, Encryption, Lifecycle), Architecture Patterns, Troubleshooting, Last-Minute Revision |
| 18 | [S3 Exam Guide](./S3%20Exam%20Guide/) | 10 | Exam Strategy, Frequently Tested Concepts, Decision Guides, Common Traps, Memory Tricks |
| 19 | [S3 Interview Questions](./S3%20Interview%20Questions/) | 10 | Beginner → Advanced Questions, Scenario-Based, Architecture, Security, Cost Optimization, Model Answers |

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Bucket** | A container for objects — globally unique name, created in a specific region |
| **Object** | A file stored in S3 (data + metadata + unique key), up to 5 TB |
| **Key** | The unique identifier (path) for an object within a bucket |
| **Durability** | 99.999999999% (11 nines) — data survives failures |
| **Availability** | 99.99% — data is accessible when needed |
| **Versioning** | Keep multiple variants of an object in the same bucket |
| **Bucket Policy** | JSON-based resource policy for access control |
| **SSE** | Server-Side Encryption (S3-managed, KMS, or customer-provided keys) |
| **Replication** | CRR (Cross-Region) or SRR (Same-Region) automatic object copying |
| **Lifecycle Rules** | Automatically transition or expire objects based on age |
| **Object Lock** | WORM (Write Once Read Many) protection for compliance |
| **Presigned URLs** | Time-limited URLs granting temporary access to private objects |
| **Transfer Acceleration** | Faster uploads via AWS Edge Locations and backbone network |
| **Access Points** | Named network endpoints with dedicated policies for shared buckets |
| **Storage Lens** | Organization-wide visibility into S3 usage and activity metrics |

---

## Architecture Overview

```
                        ┌─────────────────────┐
                        │    Amazon S3 Bucket  │
                        │                     │
                        │  ┌───────────────┐  │
                        │  │   Objects      │  │
  Users / Applications  │  │  (up to 5 TB)  │  │
         │              │  └───────────────┘  │
         │              │                     │
         ▼              │  ┌───────────────┐  │
  ┌──────────────┐      │  │  Versioning   │  │
  │ Access Layer │      │  │  Object Lock  │  │
  │              │      │  └───────────────┘  │
  │ • IAM Policies│──▶  │                     │
  │ • Bucket Policy│    │  ┌───────────────┐  │
  │ • Access Points│    │  │  Encryption   │  │
  │ • Presigned URL│    │  │  (SSE-S3/KMS) │  │
  │ • OAC / OAI   │    │  └───────────────┘  │
  └──────────────┘      │                     │
                        │  ┌───────────────┐  │
                        │  │  Lifecycle     │  │
                        │  │  Replication   │  │
                        │  └───────────────┘  │
                        └─────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Event     │ │ Replica  │ │ Glacier  │
             │Notification│ │ Bucket   │ │ Archive  │
             │(Lambda/   │ │(CRR/SRR) │ │          │
             │ SQS/SNS)  │ │          │ │          │
             └──────────┘ └──────────┘ └──────────┘
```

---

## Suggested Learning Path

```
 START
   │
   ▼
 ① S3 Fundamentals ──────────── Buckets, Objects, Keys, Limits
   │
   ▼
 ② Storage Classes ──────────── Standard, IA, Glacier tiers
   │
   ▼
 ③ Versioning & Data Protection  MFA Delete, Object Lock
   │
   ▼
 ④ Security ──────────────────── IAM, Bucket Policies, ACLs
   │
   ▼
 ⑤ Encryption ────────────────── SSE-S3, SSE-KMS, SSE-C
   │
   ▼
 ⑥ Replication ───────────────── CRR, SRR, DR scenarios
   │
   ▼
 ⑦ Lifecycle Policies ────────── Transitions, Expirations
   │
   ▼
 ⑧ Performance ───────────────── Multipart, Transfer Acceleration
   │
   ▼
 ⑨ Advanced Features ─────────── Access Points, Presigned URLs,
   │                               MRAP, Storage Lens, Static Hosting
   │
   ▼
 ⑩ Exam & Interview Prep ─────── Cheat Sheets, Exam Guide, Q&A
   │
  END
```

---

## Storage Classes Quick Reference

| Storage Class | Use Case | Min Duration | Retrieval |
|--------------|----------|-------------|-----------|
| **S3 Standard** | Frequently accessed data | None | Instant |
| **S3 Standard-IA** | Infrequent access, rapid retrieval | 30 days | Instant |
| **S3 One Zone-IA** | Reproducible infrequent data | 30 days | Instant |
| **S3 Intelligent-Tiering** | Unknown/changing access patterns | None | Instant |
| **Glacier Instant Retrieval** | Archive with instant access | 90 days | Milliseconds |
| **Glacier Flexible Retrieval** | Archive, minutes-to-hours retrieval | 90 days | 1 min – 12 hrs |
| **Glacier Deep Archive** | Long-term archive, rare access | 180 days | 12 – 48 hrs |

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
