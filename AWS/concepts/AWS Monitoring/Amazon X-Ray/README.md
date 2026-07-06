# AWS X-Ray

A deep-dive study guide into **AWS X-Ray** — AWS's fully managed distributed tracing service for analyzing, monitoring, and debugging requests as they travel across microservices, serverless functions, and distributed applications.

---

## 📚 Table of Contents

- [What is X-Ray?](#what-is-x-ray)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Supported AWS Services](#supported-aws-services)
- [Navigation](#navigation)

---

## What is X-Ray?

AWS X-Ray is a **fully managed distributed tracing service** that helps developers analyze, monitor, and debug applications running on AWS and on-premises environments.

It enables end-to-end request tracing across distributed systems, allowing you to identify **performance bottlenecks**, **application errors**, **latency issues**, and **service dependencies** — providing a complete picture of how a request travels through your application instead of viewing logs from individual services.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | What X-Ray is, why it's needed, core features |
| 02 | [X-Ray Architecture](./02-%20X-Ray%20Architecture.md) | Internal architecture and components |
| 03 | [Distributed Tracing](./03-%20Distributed%20Tracing.md) | Tracing concepts and how X-Ray implements them |
| 04 | [Traces](./04-%20Traces.md) | End-to-end request traces |
| 05 | [Segments](./05-%20Segments.md) | Work done by a single service |
| 06 | [Subsegments](./06-%20Subsegments.md) | Granular breakdown of downstream calls |
| 07 | [Service Map](./07-%20Service%20Map.md) | Visual dependency graph of your application |
| 08 | [Sampling](./08-%20Sampling.md) | Controlling which requests are traced |
| 09 | [Annotations & Metadata](./09-%20Annotations%20%26%20Metadata.md) | Adding searchable and non-searchable data to traces |
| 10 | [Trace Analysis](./10-%20Trace%20Analysis.md) | Querying and filtering traces |
| 11 | [X-Ray SDK](./11-%20X-Ray%20SDK.md) | Instrumenting applications with the SDK |
| 12 | [X-Ray Daemon](./12-%20X-Ray%20Daemon.md) | Background process that sends trace data |
| 13 | [X-Ray Write APIs](./13-%20X-Ray%20Write%20APIs.md) | PutTraceSegments, PutTelemetryRecords |
| 14 | [X-Ray Read APIs](./14-%20X-Ray%20Read%20APIs.md) | GetTraceSummaries, BatchGetTraces, GetServiceGraph |
| 15 | [X-Ray with Lambda](./15-%20X-Ray%20with%20Lambda.md) | Serverless tracing with AWS Lambda |
| 16 | [X-Ray with API Gateway](./16-%20X-Ray%20with%20API%20Gateway.md) | Tracing API requests end-to-end |
| 17 | [X-Ray with EC2](./17-%20X-Ray%20with%20EC2.md) | EC2-based application tracing |
| 18 | [X-Ray with ECS & Fargate](./18-%20X-Ray%20with%20ECS%20%26%20Fargate.md) | Container-based tracing patterns |
| 19 | [X-Ray with Elastic Beanstalk](./19-%20X-Ray%20with%20Elastic%20Beanstalk.md) | Beanstalk integration and configuration |
| 20 | [X-Ray with EKS & Kubernetes](./20-%20X-Ray%20with%20EKS%20%26%20Kubernetes.md) | Kubernetes-native tracing with DaemonSets |
| 21 | [X-Ray Security](./21-%20X-Ray%20Security.md) | IAM policies, encryption, and access control |
| 22 | [Troubleshooting](./22-%20Troubleshooting.md) | Common issues and debugging steps |
| 23 | [Advantages & Limitations](./23-%20Advantages%20%26%20Limitations.md) | Strengths and constraints |
| 24 | [CloudWatch vs CloudTrail vs X-Ray](./24-%20CloudWatch%20vs%20CloudTrail%20vs%20X-Ray.md) | Service comparison guide |
| 25 | [Monitoring & Best Practices](./25-%20Monitoring%20%26%20Best%20Practices.md) | Operational monitoring guidelines |
| 26 | [Cost Optimization](./26-%20Cost%20Optimization.md) | Strategies to reduce X-Ray costs |
| 27 | [Production Best Practices](./27-%20Production%20Best%20Practices.md) | Enterprise-grade tracing configuration |
| 28 | [Real-World Architectures](./28-%20Real-World%20Architectures.md) | Production architecture patterns |
| 29 | [Common Interview Questions](./29-%20Common%20Interview%20Questions.md) | Interview prep and key takeaways |

---

## Module Structure

This module is organized into progressive learning sections:

```
Amazon X-Ray/
│
├── Fundamentals (01–03)
│   └── Introduction, Architecture, Distributed Tracing
│
├── Tracing Concepts (04–10)
│   └── Traces, Segments, Subsegments, Service Map,
│       Sampling, Annotations & Metadata, Trace Analysis
│
├── SDK & Daemon (11–14)
│   └── X-Ray SDK, X-Ray Daemon, Write APIs, Read APIs
│
├── AWS Integrations (15–20)
│   └── Lambda, API Gateway, EC2, ECS & Fargate,
│       Elastic Beanstalk, EKS & Kubernetes
│
└── Production & Interview Prep (21–29)
    └── Security, Troubleshooting, Comparisons,
        Best Practices, Cost Optimization,
        Real-World Architectures, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Trace** | An end-to-end record of a request as it travels across services |
| **Segment** | A block of data representing work done by a single service |
| **Subsegment** | A granular breakdown of downstream calls within a segment |
| **Service Map** | A visual, real-time dependency graph of your application |
| **Sampling** | Rules that control which requests are traced (to manage costs) |
| **Annotations** | Indexed key-value pairs that can be used to filter traces |
| **Metadata** | Non-indexed key-value pairs for additional trace context |
| **X-Ray SDK** | Client library for instrumenting application code |
| **X-Ray Daemon** | Background process that buffers and sends trace data to the X-Ray API |
| **Trace ID** | Unique identifier that links all segments of a single request |

---

## Architecture Overview

```
  Client Request
       │
       ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │API Gateway│──▶│  Lambda  │──▶│ DynamoDB │
  └──────────┘    └──────────┘    └──────────┘
       │               │               │
       ▼               ▼               ▼
  ┌─────────────────────────────────────────┐
  │           X-Ray SDK / Daemon            │
  │      (Collects Segments & Traces)       │
  └─────────────────┬───────────────────────┘
                    │
                    ▼
            ┌──────────────┐
            │  AWS X-Ray   │
            │   Console    │
            ├──────────────┤
            │ Service Map  │
            │ Trace List   │
            │ Trace Detail │
            │ Analytics    │
            └──────────────┘
```

---

## Supported AWS Services

X-Ray integrates natively with:

EC2 · Lambda · ECS · Fargate · Elastic Beanstalk · API Gateway · Step Functions · EKS · ELB · App Runner

It also supports instrumentation via the **X-Ray SDK** for Java, Python, Node.js, .NET, Go, and Ruby.

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Monitoring](../README.md) |
| ⬅️ Previous | [AWS CloudTrail](../Cloud%20Trail/README.md) |
| ➡️ Next | [Amazon EventBridge](../EventBridge/README.md) |

---

> **Part of the [AWS Monitoring](../README.md) section in the Backend Engineering Playbook.**
