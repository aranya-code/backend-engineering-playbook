# README

## Overview

This section contains interview-focused questions for **AWS CloudFront**, progressing from core concepts to caching, security, signed access, edge computing, monitoring, troubleshooting, architecture, senior-level design, and rapid-fire interview preparation.

The questions are designed for backend engineers working with architectures involving services such as **Django, FastAPI, REST APIs, microservices, Nginx, ALB, S3, AWS WAF, Redis, and PostgreSQL**.

The progression is intentional:

```text
Core Concepts
     ↓
Caching & Policies
     ↓
Security
     ↓
Signed URLs & Cookies
     ↓
Edge Computing
     ↓
Monitoring
     ↓
Scenario-Based Troubleshooting
     ↓
Architecture
     ↓
Senior Engineering
     ↓
Architect-Level Design
     ↓
Rapid-Fire Revision
     ↓
Interview Traps
```

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Beginner Level Questions](01-%20Beginner%20Level%20Questions.md) | Fundamental CloudFront concepts, distributions, origins, behaviors, edge locations, request flow, and core terminology. |
| 02 | [Core CloudFront Questions](02-%20Core%20CloudFront%20Questions.md) | Core interview questions covering CloudFront architecture, request processing, origins, behaviors, and fundamental operational concepts. |
| 03 | [Caching and Policy Questions](03-%20Caching%20and%20Policy%20Questions.md) | Cache behavior, cache keys, cache policies, origin request policies, TTLs, invalidation, headers, cookies, and query strings. |
| 04 | [Security Questions](04-%20Security%20Questions.md) | CloudFront security, TLS, AWS WAF, private origins, S3 Origin Access Control, geographic restrictions, and origin protection. |
| 05 | [Signed URL and Cookie Questions](05-%20Signed%20URL%20and%20Cookie%20Questions.md) | Signed URLs, signed cookies, private content, trusted access, expiration, authorization boundaries, and secure distribution patterns. |
| 06 | [Edge Computing Questions](06-%20Edge%20Computing%20Questions.md) | CloudFront Functions, Lambda@Edge, edge request processing, transformations, routing, and edge-computing trade-offs. |
| 07 | [Monitoring Questions](07-%20Monitoring%20Questions.md) | CloudFront metrics, logs, cache hit ratio, latency, 4xx/5xx errors, origin health, observability, and operational monitoring. |
| 08 | [Scenario Based Questions](08-%20Scenario%20Based%20Questions.md) | Production scenarios involving performance, caching, security, availability, origin failures, deployments, and traffic patterns. |
| 09 | [Troubleshooting Questions](09-%20Troubleshooting%20Questions.md) | Systematic troubleshooting of 4xx/5xx errors, cache issues, origin connectivity, S3 access, DNS, TLS, and configuration problems. |
| 10 | [Architecture Questions](10-%20Architecture%20Questions.md) | CloudFront architecture design, origin patterns, static and dynamic content, APIs, multi-region systems, security, scalability, and HA. |
| 11 | [Senior Level Questions](11-%20Senior%20Level%20Questions.md) | Senior backend engineering questions covering trade-offs, production design, performance, reliability, security, and operational decisions. |
| 12 | [Architect Level Questions](12-%20Architect%20Level%20Questions.md) | Advanced system architecture, global delivery, multi-region strategies, failure domains, security boundaries, cost, and design trade-offs. |
| 13 | [Rapid-Fire Questions](13-%20Rapid-Fire%20Questions.md) | Short-form questions and answers for fast interview revision and last-minute preparation. |
| 14 | [Common Interview Traps](14-%20Common%20Interview%20Traps.md) | Common misconceptions, misleading assumptions, configuration traps, security mistakes, caching mistakes, and interview pitfalls. |

## Recommended Study Order

### Foundation

Start with:

- [01- Core CloudFront Questions.md](./01-%20Core%20CloudFront%20Questions.md)
- [02- Core CloudFront Questions.md](./02-%20Core%20CloudFront%20Questions.md)

Focus on understanding:

- Distribution
- Origin
- Origin group
- Behavior
- Edge location
- Viewer request
- Origin request
- Cache
- TTL
- Cache hit and miss
- CloudFront-to-origin communication

### Caching and Performance

Continue with:

- [03- Caching and Policy Questions.md](./03-%20Caching%20and%20Policy%20Questions.md)

Pay particular attention to:

```text
Cache Policy
     ↓
Cache Key
     ↓
Cache Hit / Miss
     ↓
Origin Request
     ↓
TTL / Freshness
     ↓
Invalidation
```

This section is particularly important for backend interviews because CloudFront performance problems are frequently caused by incorrect cache-key design rather than insufficient infrastructure.

### Security

Then study:

- [04- Security Questions.md](./04-%20Security%20Questions.md)
- [05- Signed URL and Cookie Questions.md](./05-%20Signed%20URL%20and%20Cookie%20Questions.md)

Understand the distinction between:

```text
TLS
  ↓
CloudFront
  ↓
WAF
  ↓
Origin Access Control
  ↓
Origin Authorization
  ↓
Application Authorization
```

Do not treat CloudFront as a replacement for application-level authentication or authorization.

### Edge Computing

Study:

- [06- Edge Computing Questions.md](./06-%20Edge%20Computing%20Questions.md)

Focus on understanding when edge execution is appropriate and when business logic should remain inside the application layer.

### Operations

Then study:

- [07- Monitoring Questions.md](./07-%20Monitoring%20Questions.md)
- [09- Troubleshooting Questions.md](./09-%20Troubleshooting%20Questions.md)

The goal is to move beyond configuration knowledge and understand how to diagnose production failures.

### Architecture and Senior-Level Design

Finish the deeper architecture material with:

- [08- Scenario Based Questions.md](./08-%20Scenario%20Based%20Questions.md)
- [10- Architecture Questions.md](./10-%20Architecture%20Questions.md)
- [11- Senior Level Questions.md](./11-%20Senior%20Level Questions.md)
- [12- Architect Level Questions.md](./12-%20Architect%20Level%20Questions.md)

These sections should be approached as system-design exercises rather than memorization material.

### Final Revision

Use:

- [13- Rapid-Fire Questions.md](./13-%20Rapid-Fire%20Questions.md)
- [14- Common Interview Traps.md](./14-%20Common%20Interview%20Traps.md)

These are best used after completing the deeper sections.

## What Interviewers Commonly Test

CloudFront interviews typically evaluate whether you understand the interaction between several layers rather than whether you can recite individual features.

### Request Flow

Be able to explain:

```text
Client
  ↓
DNS
  ↓
CloudFront
  ↓
WAF
  ↓
Cache Lookup
  │
  ├── Hit ──→ Response
  │
  └── Miss
         ↓
       Origin
         ↓
     Application
         ↓
       Response
         ↓
   CloudFront Cache
         ↓
       Client
```

### Caching

Be prepared to explain:

- What determines the cache key
- How query strings affect caching
- How headers affect caching
- How cookies affect caching
- Cache policies
- Origin request policies
- TTL behavior
- Cache invalidation
- Cache-control headers
- Cache fragmentation
- Personalized content
- Cache correctness

### Security

Be able to distinguish:

| Concern | Typical Responsibility |
|---|---|
| TLS termination | CloudFront |
| HTTP filtering | AWS WAF |
| Private S3 access | CloudFront OAC + S3 policy |
| Private content access | Signed URLs / signed cookies |
| Business authorization | Application |
| Database authorization | Database/application layer |
| Origin protection | Network and application architecture |

### Architecture

Be prepared to design CloudFront in front of:

- S3
- ALB
- EC2
- ECS
- EKS
- API services
- Django
- FastAPI
- Microservices
- Multi-region applications

## Core Mental Model

A useful CloudFront mental model is:

```text
                    ┌───────────────────┐
                    │      Client       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   CloudFront CDN  │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                 Cache Hit          Cache Miss
                    │                   │
                    │                   ▼
                    │             ┌───────────┐
                    │             │   WAF     │
                    │             └─────┬─────┘
                    │                   │
                    │                   ▼
                    │             ┌───────────┐
                    │             │  Origin   │
                    │             └─────┬─────┘
                    │                   │
                    │                   ▼
                    │             Application
                    │
                    └───────────────┬───────┘
                                    ▼
                                  Client
```

The most important question is not:

> "Can CloudFront cache this?"

It is:

> "Can this response be safely shared, and what request attributes determine its representation?"

That distinction drives correct cache-key, security, and performance decisions.

## Backend Engineering Context

CloudFront becomes particularly valuable when placed in front of a backend architecture:

```text
                         Internet
                            │
                            ▼
                         Route 53
                            │
                            ▼
                       CloudFront
                            │
                         AWS WAF
                            │
                 ┌──────────┴──────────┐
                 │                     │
              Static                 API
                 │                     │
                 ▼                     ▼
                 S3                   ALB
                                       │
                                  Django/FastAPI
                                  /           \
                               Redis       PostgreSQL
```

Typical responsibilities are separated as follows:

| Layer | Responsibility |
|---|---|
| Route 53 | DNS |
| CloudFront | Global HTTP delivery and caching |
| WAF | Web request filtering |
| S3 | Static/object storage |
| ALB | Regional application load balancing |
| Django/FastAPI | Business logic and APIs |
| Redis | Application/data caching |
| PostgreSQL | Persistent relational data |

This separation is important in architecture interviews because replacing one layer with another usually creates incorrect assumptions.

## Interview Preparation Priorities

Prioritize these areas when time is limited:

1. **CloudFront request lifecycle**
2. **Cache keys and cache policies**
3. **Origin request policies**
4. **TTL and cache invalidation**
5. **S3 OAC and private origins**
6. **AWS WAF integration**
7. **Signed URLs and signed cookies**
8. **CloudFront Functions vs Lambda@Edge**
9. **Monitoring and troubleshooting**
10. **Architecture and failure scenarios**
11. **Personalized content and cache safety**
12. **Origin protection and bypass prevention**

## High-Value Interview Questions

Use these questions as checkpoints before considering CloudFront interview preparation complete:

- What happens when CloudFront receives a request?
- How does CloudFront determine whether an object is cached?
- What is a cache key?
- What is the difference between a cache policy and an origin request policy?
- How do cookies affect caching?
- How do query strings affect caching?
- How do headers affect caching?
- What is a cache hit versus a cache miss?
- How does TTL affect CloudFront?
- When should you invalidate a CloudFront cache?
- Why is immutable asset versioning preferable to frequent invalidations?
- How would you safely cache a REST API?
- How would you prevent personalized responses from being shared?
- How do you protect a private S3 bucket behind CloudFront?
- What is Origin Access Control?
- What are signed URLs?
- What are signed cookies?
- When would you use CloudFront Functions?
- When would you use Lambda@Edge?
- How does CloudFront integrate with AWS WAF?
- How would you protect an ALB from direct origin bypass?
- How would you troubleshoot a CloudFront 403?
- How would you troubleshoot a CloudFront 502 or 504?
- Why can origin traffic remain high even when CloudFront is enabled?
- How would you design CloudFront for a global Django API?
- How would you design CloudFront for static assets stored in S3?
- How would you handle CloudFront during an origin outage?
- How would you design a multi-region CloudFront architecture?
- Which CloudFront metrics would you monitor?
- What are the most common CloudFront caching mistakes?

## Key Takeaways

- **Study CloudFront as an edge architecture component, not merely as a CDN cache.**
- **Caching correctness, cache-key design, and security boundaries are more important than simply maximizing cache hit ratio.**
- **Understand the responsibilities of CloudFront, WAF, S3, ALB, Route 53, Redis, and the application layer independently.**
- **Senior-level CloudFront interviews focus on trade-offs involving performance, security, availability, cost, and operational complexity.**
- **Use scenario-based and troubleshooting questions to demonstrate engineering reasoning rather than feature memorization.**