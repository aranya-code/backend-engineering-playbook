# CloudFront

## Overview

Amazon CloudFront is AWS's globally distributed Content Delivery Network (CDN) service. It accelerates the delivery of static assets, dynamic API responses, and streaming media by caching content at edge locations close to end users, reducing latency and offloading traffic from origin servers.

This folder provides a comprehensive technical reference covering CloudFront's architecture, caching mechanics, security model, and edge compute capabilities. The material progresses from foundational CDN concepts through advanced topics like cache key engineering, invalidation strategies, and Lambda@Edge.

CloudFront integrates tightly with other AWS services including S3, ALB, WAF, Shield, and ACM, making it a critical component in production-grade AWS architectures.

---

## Folder Structure

```text
CloudFront/

├── 01- Introduction.md
├── 02- Global Infrastructure and Components.md
├── 03- Origins.md
├── 04- Distributions and Cache Behaviors.md
├── 05- Request Lifecycle.md
├── 06- Caching.md
├── 07- Cache Keys and Policies.md
├── 08- Cache Invalidation and Versioning.md
├── 09- Security.md
├── 10- Edge Computing.md
└── README.md
```

---

## Quick Navigation

| #  | Topic                                | Coverage                                                                              |
| -- | ------------------------------------ | ------------------------------------------------------------------------------------- |
| 01 | [Introduction](01-%20Introduction.md) | CDN fundamentals, why CloudFront exists, supported content types and origins.         |
| 02 | [Global Infrastructure and Components](02-%20Global%20Infrastructure%20and%20Components.md) | Edge Locations, Regional Edge Caches, Points of Presence, Origin Shield.              |
| 03 | [Origins](03-%20Origins.md)          | S3 buckets, custom HTTP origins, VPC origins, OAC, origin groups, and failover.       |
| 04 | [Distributions and Cache Behaviors](04-%20Distributions%20and%20Cache%20Behaviors.md) | Distribution configuration, path-based routing, and per-behavior policies.            |
| 05 | [Request Lifecycle](05-%20Request%20Lifecycle.md) | End-to-end request flow through edge, cache evaluation, and origin infrastructure.    |
| 06 | [Caching](06-%20Caching.md)          | Cache hit/miss mechanics, TTL controls, cache hit ratio optimization.                 |
| 07 | [Cache Keys and Policies](07-%20Cache%20Keys%20and%20Policies.md) | Cache key construction, cache policies vs. origin request policies, fragmentation.    |
| 08 | [Cache Invalidation and Versioning](08-%20Cache%20Invalidation%20and%20Versioning.md) | Invalidation vs. URL versioning, content-hashed immutable assets.                     |
| 09 | [Security](09-%20Security.md)        | HTTPS/TLS, AWS Shield, WAF, OAC, Geo Restrictions, Signed URLs/Cookies.              |
| 10 | [Edge Computing](10-%20Edge%20Computing.md) | CloudFront Functions, Lambda@Edge, event triggers, and execution limits.              |

---

## Learning Path

```text
Introduction
     │
     ▼
Global Infrastructure
     │
     ▼
Origins
     │
     ▼
Distributions & Behaviors
     │
     ▼
Request Lifecycle
     │
     ▼
Caching
     │
     ▼
Cache Keys & Policies
     │
     ▼
Invalidation & Versioning
     │
     ▼
Security
     │
     ▼
Edge Computing
```

---

## Key Areas

### Fundamentals & Architecture

Covers what CloudFront is, its global infrastructure of edge locations and regional caches, and how origins connect backend resources to the CDN. Files 01–03 establish the foundation.

### Request Flow & Caching

Explains how distributions route requests via cache behaviors, the complete request lifecycle through the edge network, and the mechanics of caching including TTLs, cache keys, policies, and invalidation strategies. Files 04–08 form the core operational knowledge.

### Security & Edge Compute

Addresses CloudFront's layered security model (TLS, WAF, Shield, signed URLs, OAC) and programmable edge computing with CloudFront Functions and Lambda@Edge. Files 09–10 cover advanced production concerns.

---

## Recommended Study Order

Follow the files in numerical order. Each topic builds on concepts introduced previously.

```text
01 → CDN Fundamentals
02 → Global Infrastructure
03 → Origins
04 → Distributions & Behaviors
05 → Request Lifecycle
06 → Caching Mechanics
07 → Cache Keys & Policies
08 → Invalidation & Versioning
09 → Security
10 → Edge Computing
```

---

## Key Takeaways

* CloudFront's multi-tier edge architecture (Edge Locations → Regional Edge Caches → Origin Shield) maximizes cache hit ratios and minimizes origin load.
* Cache behaviors provide path-based routing with independent caching, security, and origin policies per URL pattern.
* Cache key engineering and policy separation (cache policy vs. origin request policy) are critical for avoiding cache fragmentation.
* Content-hashed URL versioning is preferred over invalidation for immutable static assets in production deployments.
* CloudFront Functions and Lambda@Edge enable request/response manipulation at the edge without modifying origin infrastructure.