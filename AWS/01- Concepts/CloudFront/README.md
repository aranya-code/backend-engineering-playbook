# Amazon CloudFront

A deep-dive study guide into **Amazon CloudFront** — AWS's fully managed Content Delivery Network (CDN) service that securely delivers content to users worldwide through a global network of Edge Locations.

---

## 📚 Table of Contents

- [What is CloudFront?](#what-is-cloudfront)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Use Cases](#use-cases)
- [Navigation](#navigation)

---

## What is CloudFront?

Amazon CloudFront is AWS's fully managed **Content Delivery Network (CDN)** that caches content at **Edge Locations** around the world, serving requests from the location nearest to the user.

It delivers **static content**, **dynamic content**, **APIs**, **video streams**, **software downloads**, and **web applications** — significantly reducing latency and improving performance while integrating with AWS security services like **Shield**, **WAF**, and **ACM**.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | CDN concepts, CloudFront components, use cases, benefits |
| 02 | [Architecture](./02-%20Architecture.md) | Edge Locations, Regional Edge Caches, request flow |
| 03 | [Origins](./03-%20Origins.md) | S3, ALB, EC2, API Gateway, custom origins, Origin Groups |
| 04 | [Caching](./04-%20Caching.md) | Cache behavior, TTL, cache hit/miss, invalidations |
| 05 | [Cache Keys and Policies](./05-%20Cache%20Keys%20and%20Policies.md) | Cache key components, cache policies, origin request policies |
| 06 | [Security](./06-%20Security.md) | HTTPS/TLS, AWS Shield, WAF, OAC, Geo Restriction, Field-Level Encryption |
| 07 | [Signed URLs and Signed Cookies](./07-%20Signed%20URLs%20and%20Signed%20Cookies.md) | Private content delivery, trusted signers, URL vs Cookie signing |
| 08 | [Edge Computing](./08-%20Edge%20Computing.md) | CloudFront Functions, Lambda@Edge, edge-side logic |
| 09 | [Monitoring and Logging](./09-%20Monitoring%20and%20Logging.md) | Access logs, real-time logs, CloudWatch metrics, reporting |
| 10 | [Best Practices](./10-%20Best%20Practices.md) | Performance, caching, security, and cost optimization guidelines |
| 11 | [Troubleshooting](./11-%20Troubleshooting.md) | Common errors, cache issues, origin failures, debugging |
| 12 | [Real-World Scenarios](./12-%20Real-World%20Scenarios.md) | Production architecture patterns and case studies |
| 13 | [Interview Questions and Answers](./13-%20Interview%20Questions%20and%20Answers.md) | Comprehensive interview prep with detailed answers |

---

## Module Structure

This module is organized into progressive learning sections:

```
CloudFront/
│
├── Fundamentals (01–02)
│   └── Introduction, Architecture
│
├── Content Delivery (03–05)
│   └── Origins, Caching, Cache Keys & Policies
│
├── Security (06–07)
│   └── Security Layers (HTTPS, Shield, WAF, OAC,
│       Geo Restriction), Signed URLs & Cookies
│
├── Edge Computing (08)
│   └── CloudFront Functions, Lambda@Edge
│
├── Observability (09)
│   └── Monitoring, Access Logs, Real-Time Logs
│
└── Production & Interview Prep (10–13)
    └── Best Practices, Troubleshooting,
        Real-World Scenarios, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Distribution** | The CloudFront configuration object — defines origins, cache behavior, and security |
| **Edge Location** | A physical AWS location where content is cached close to users |
| **Regional Edge Cache** | An intermediate cache layer between Edge Locations and the origin |
| **Origin** | The backend source of content (S3, ALB, EC2, API Gateway, custom) |
| **Cache Behavior** | Rules that match URL path patterns to specific origins and cache settings |
| **TTL (Time To Live)** | How long CloudFront keeps cached content before revalidating with the origin |
| **Cache Hit / Miss** | Whether content was served from cache (hit) or fetched from origin (miss) |
| **Invalidation** | Force-removing cached content before TTL expiry |
| **OAC** | Origin Access Control — restricts S3 access to CloudFront only |
| **Signed URLs/Cookies** | Restrict access to private content with time-limited, authenticated URLs |
| **CloudFront Functions** | Lightweight JavaScript functions running at Edge Locations |
| **Lambda@Edge** | Full Lambda functions running at Regional Edge Caches |
| **Geo Restriction** | Allow or block access based on the viewer's geographic location |

---

## Architecture Overview

```
  Users (Global)
       │
       ▼
  ┌──────────────┐
  │ Edge Location │  ◄── Cache Hit → Content served immediately
  └──────┬───────┘
         │ Cache Miss
         ▼
  ┌──────────────────┐
  │ Regional Edge    │  ◄── Second-level cache
  │ Cache            │
  └──────┬───────────┘
         │ Cache Miss
         ▼
  ┌──────────────┐
  │   Origin     │
  │ (S3 / ALB /  │
  │  EC2 / API   │
  │  Gateway)    │
  └──────────────┘
```

### Security Layers

```
Layer 1: HTTPS / TLS Encryption
Layer 2: AWS Shield (DDoS Protection)
Layer 3: AWS WAF (Request Filtering)
Layer 4: OAC (Origin Access Control)
Layer 5: Signed URLs / Cookies
Layer 6: Geo Restriction
Layer 7: Field-Level Encryption
```

---

## Use Cases

| Use Case | Architecture |
|----------|-------------|
| **Static Website** | Users → CloudFront → S3 Bucket |
| **Dynamic Application** | Users → CloudFront → ALB → EC2/ECS/EKS |
| **API Acceleration** | Users → CloudFront → API Gateway |
| **Video Streaming** | Users → CloudFront → S3 (HLS/DASH segments) |
| **Software Distribution** | Users → CloudFront → S3 (binaries, patches) |
| **Private Content** | Users → CloudFront (Signed URL) → S3 |

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
