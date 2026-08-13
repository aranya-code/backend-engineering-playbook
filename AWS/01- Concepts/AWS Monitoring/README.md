# AWS Monitoring

A comprehensive deep-dive into the four core AWS monitoring and observability services. This section covers architecture, internals, integrations, best practices, cost optimization, and interview preparation for each service.

---

## 📚 Table of Contents

- [Overview](#overview)
- [Services Covered](#services-covered)
  - [Amazon CloudWatch](#amazon-cloudwatch)
  - [AWS CloudTrail](#aws-cloudtrail)
  - [AWS X-Ray](#aws-x-ray)
  - [Amazon EventBridge](#amazon-eventbridge)
- [How These Services Work Together](#how-these-services-work-together)
- [Quick Comparison](#quick-comparison)
- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)

---

## Overview

Monitoring is a foundational pillar of any well-architected AWS workload. AWS provides a suite of fully managed services that, together, deliver **metrics collection**, **log aggregation**, **API audit trails**, **distributed tracing**, and **event-driven automation**.

This section of the playbook provides **117 structured notes** organized into four service-specific modules, each progressing from introductory concepts through architecture, integrations, security, cost optimization, production best practices, and common interview questions.

---

## Services Covered

### Amazon CloudWatch

> **Fully managed monitoring and observability service** — metrics, logs, alarms, dashboards, and insights.

| # | Topic |
|---|-------|
| 01 | Introduction |
| 02 | CloudWatch Architecture |
| 03 | Core Components |
| 04 | CloudWatch Metrics |
| 05 | AWS Service Metrics |
| 06 | Custom Metrics |
| 07 | Namespaces |
| 08 | Dimensions |
| 09 | Metric Statistics |
| 10 | Metric Resolution |
| 11 | Basic vs Detailed Monitoring |
| 12 | CloudWatch Logs |
| 14 | Log Streams |
| 15 | Log Retention Policies |
| 16 | Metric Filters |
| 17 | Subscription Filters |
| 18 | CloudWatch Logs Insights |
| 19 | Export Logs to Amazon S3 |
| 20 | CloudWatch Agent & Unified CloudWatch Agent |
| 21 | CloudWatch Dashboards |
| 22 | CloudWatch Alarms |
| 23 | Composite Alarms |
| 24 | Contributor Insights |
| 25 | Container Insights |
| 26 | CloudWatch Synthetics |
| 27 | ServiceLens |
| 28 | Cross-Account Observability |
| 29 | Best Practices & Cost Optimization |
| 30 | Interview Questions & Summary |

📂 **Path:** [`CloudWatch/`](./CloudWatch)

---

### AWS CloudTrail

> **Fully managed governance, compliance, and API audit logging service** — records every supported API call across your AWS account.

| # | Topic |
|---|-------|
| 01 | Introduction |
| 02 | CloudTrail Architecture |
| 03 | How CloudTrail Works |
| 04 | Event Types |
| 05 | Management Events |
| 06 | Data Events |
| 07 | Network Activity Events |
| 08 | Trails |
| 09 | Event History |
| 10 | CloudTrail Insights |
| 11 | Log File Integrity Validation |
| 12 | CloudTrail Log Files |
| 13 | CloudTrail with Amazon S3 |
| 14 | CloudTrail with CloudWatch |
| 15 | CloudTrail with EventBridge |
| 16 | CloudTrail with SNS |
| 17 | CloudTrail with Lambda |
| 18 | CloudTrail Organizations |
| 19 | IAM & CloudTrail |
| 20 | CloudTrail Security |
| 21 | CloudTrail Pricing |
| 22 | Troubleshooting |
| 23 | Advantages & Limitations |
| 24 | CloudTrail vs CloudWatch vs X-Ray |
| 25 | Monitoring & Best Practices |
| 26 | Cost Optimization |
| 27 | Production Best Practices |
| 28 | Real-World Architectures |
| 29 | Common Interview Questions |

📂 **Path:** [`Cloud Trail/`](./Cloud%20Trail)

---

### AWS X-Ray

> **Fully managed distributed tracing service** — end-to-end request tracing, service maps, and latency analysis for microservices and serverless applications.

| # | Topic |
|---|-------|
| 01 | Introduction |
| 02 | X-Ray Architecture |
| 03 | Distributed Tracing |
| 04 | Traces |
| 05 | Segments |
| 06 | Subsegments |
| 07 | Service Map |
| 08 | Sampling |
| 09 | Annotations & Metadata |
| 10 | Trace Analysis |
| 11 | X-Ray SDK |
| 12 | X-Ray Daemon |
| 13 | X-Ray Write APIs |
| 14 | X-Ray Read APIs |
| 15 | X-Ray with Lambda |
| 16 | X-Ray with API Gateway |
| 17 | X-Ray with EC2 |
| 18 | X-Ray with ECS & Fargate |
| 19 | X-Ray with Elastic Beanstalk |
| 20 | X-Ray with EKS & Kubernetes |
| 21 | X-Ray Security |
| 22 | Troubleshooting |
| 23 | Advantages & Limitations |
| 24 | CloudWatch vs CloudTrail vs X-Ray |
| 25 | Monitoring & Best Practices |
| 26 | Cost Optimization |
| 27 | Production Best Practices |
| 28 | Real-World Architectures |
| 29 | Common Interview Questions |

📂 **Path:** [`Amazon X-Ray/`](./Amazon%20X-Ray)

---

### Amazon EventBridge

> **Fully managed serverless event bus** — event-driven architectures with routing, filtering, scheduling, replay, and SaaS integrations.

| # | Topic |
|---|-------|
| 01 | Introduction |
| 02 | Event-Driven Architecture |
| 03 | Core Components |
| 04 | Events |
| 05 | Event Buses |
| 06 | Event Patterns |
| 07 | Rules |
| 08 | Targets |
| 09 | Scheduler |
| 10 | Cron Expressions |
| 11 | EventBridge Pipes |
| 12 | EventBridge Archives |
| 13 | Event Replay |
| 14 | Schema Registry |
| 15 | Resource Policies |
| 16 | EventBridge Integrations |
| 17 | API Destinations |
| 18 | Partner Event Sources |
| 19 | Custom Events |
| 20 | Dead-Letter Queues (DLQ) |
| 21 | Retry Policies |
| 22 | EventBridge Security |
| 23 | Monitoring EventBridge |
| 24 | EventBridge Best Practices |
| 25 | Cost Optimization |
| 26 | Real-World Architectures |
| 27 | Common Mistakes |
| 28 | EventBridge vs SNS vs SQS |
| 29 | Production Best Practices |
| 30 | Interview Questions & Summary |

📂 **Path:** [`EventBridge/`](./EventBridge)

---

## How These Services Work Together

```
                          ┌─────────────────┐
                          │   Application    │
                          └────────┬────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
              ▼                    ▼                     ▼
     ┌────────────────┐  ┌────────────────┐   ┌────────────────┐
     │  CloudWatch    │  │   X-Ray        │   │  CloudTrail    │
     │  (Metrics &    │  │  (Distributed  │   │  (API Audit    │
     │   Logs)        │  │   Tracing)     │   │   Logging)     │
     └───────┬────────┘  └───────┬────────┘   └───────┬────────┘
             │                   │                     │
             └───────────────────┼─────────────────────┘
                                 │
                                 ▼
                       ┌────────────────┐
                       │  EventBridge   │
                       │  (Event-Driven │
                       │  Automation)   │
                       └────────────────┘
```

- **CloudWatch** collects metrics and logs from your resources and applications.
- **X-Ray** traces individual requests as they travel across distributed services.
- **CloudTrail** records every API call for governance, compliance, and auditing.
- **EventBridge** reacts to events from all three services (and more) to trigger automated workflows.

---

## Quick Comparison

| Aspect | CloudWatch | CloudTrail | X-Ray | EventBridge |
|--------|-----------|------------|-------|-------------|
| **Primary Purpose** | Monitoring & Observability | API Auditing & Compliance | Distributed Tracing | Event-Driven Automation |
| **Data Collected** | Metrics, Logs, Alarms | API Events (Management, Data, Network) | Traces, Segments, Service Maps | Events from AWS, SaaS, Custom |
| **Key Question Answered** | *"How is my system performing?"* | *"Who did what and when?"* | *"Where is the bottleneck in this request?"* | *"What happened, and what should react?"* |
| **Real-Time** | Near real-time | ~15 min delivery | Real-time traces | Near real-time |
| **Retention** | Configurable (1 day – indefinite) | 90 days (Event History) / S3 (indefinite) | 30 days (default) | Archives (configurable) |

---

## Getting Started

Each subdirectory is structured as a sequential learning path — start from **`01- Introduction.md`** and progress through the numbered files. Topics build upon each other, culminating in best practices, real-world architectures, and interview questions.

**Suggested reading order:**

1. **CloudWatch** — Understand metrics, logs, and alarms first as the foundation of AWS observability.
2. **CloudTrail** — Learn API-level auditing and how it complements CloudWatch.
3. **X-Ray** — Add distributed tracing to understand request flows across services.
4. **EventBridge** — Tie everything together with event-driven automation and integration.

---

## Prerequisites

- Basic understanding of AWS core services (EC2, Lambda, S3, IAM)
- Familiarity with cloud architecture concepts
- An AWS account (for hands-on practice)

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
